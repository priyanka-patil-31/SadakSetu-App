package com.sadaksetu.core.network

import kotlinx.serialization.Serializable
import kotlinx.serialization.json.Json
import retrofit2.HttpException
import java.io.IOException
import java.net.ConnectException
import java.net.SocketTimeoutException
import java.net.UnknownHostException

@Serializable
private data class ErrorBody(val detail: String? = null)

sealed interface AppError {
    val message: String

    data class Network(override val message: String = "No internet connection. Check your network and try again.") : AppError
    data class BackendUnavailable(override val message: String = "SadakSetu server is unavailable. Please try again shortly.") : AppError
    data class Timeout(override val message: String = "The SadakSetu server took too long to respond. Please try again.") : AppError
    data class Unauthorized(override val message: String = "Your session has expired. Please sign in again.") : AppError
    data class Server(override val message: String) : AppError
    data class Unknown(override val message: String = "Something went wrong. Please try again.") : AppError
}

class AppException(val error: AppError) : RuntimeException(error.message)

fun Throwable.toAppError(): AppError = when (this) {
    is SocketTimeoutException -> AppError.Timeout()
    is ConnectException, is UnknownHostException -> AppError.BackendUnavailable()
    is IOException -> AppError.Network()
    is HttpException -> when {
        code() in 400..499 -> {
            val detailMsg = response()?.errorBody()?.string()?.let(::readDetail)
            if (code() == 401) {
                if (!detailMsg.isNullOrBlank() && !detailMsg.contains("expired", ignoreCase = true)) {
                    AppError.Server(detailMsg)
                } else {
                    AppError.Unauthorized(detailMsg ?: "Your session has expired. Please sign in again.")
                }
            } else {
                AppError.Server(detailMsg ?: "Request could not be completed.")
            }
        }
        else -> AppError.Server("The SadakSetu service is temporarily unavailable.")
    }
    else -> AppError.Unknown(message ?: "Something went wrong. Please try again.")
}

private fun readDetail(raw: String): String = runCatching {
    val element = Json.parseToJsonElement(raw)
    if (element is kotlinx.serialization.json.JsonObject) {
        val detail = element["detail"]
        if (detail is kotlinx.serialization.json.JsonPrimitive) {
            val content = detail.content
            if (content.isNotBlank()) return@runCatching content
        } else if (detail is kotlinx.serialization.json.JsonArray) {
            val msgs = detail.mapNotNull {
                if (it is kotlinx.serialization.json.JsonObject) {
                    val msg = it["msg"]
                    if (msg is kotlinx.serialization.json.JsonPrimitive) msg.content else null
                } else null
            }
            if (msgs.isNotEmpty()) return@runCatching msgs.joinToString(". ")
        }
        val message = element["message"]
        if (message is kotlinx.serialization.json.JsonPrimitive && message.content.isNotBlank()) {
            return@runCatching message.content
        }
    }
    null
}.getOrNull()?.takeIf { it.isNotBlank() } ?: "Request could not be completed."

fun AppError.asException(): AppException = AppException(this)
