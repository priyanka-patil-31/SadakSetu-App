package com.sadaksetu.data.repository

import android.content.Context
import android.net.Uri
import com.sadaksetu.data.remote.ApiService
import com.sadaksetu.data.remote.model.OptionalNoteDto
import com.sadaksetu.data.remote.model.TeamMemberCreateDto
import com.sadaksetu.data.remote.model.WorkOrderCompletionDto
import com.sadaksetu.data.remote.model.WorkOrderDelayDto
import com.sadaksetu.data.remote.model.WorkOrderMembersDto
import com.sadaksetu.data.remote.model.WorkOrderPhotoDto
import com.sadaksetu.data.remote.model.WorkOrderProgressDto
import com.sadaksetu.domain.models.TeamMember
import com.sadaksetu.domain.models.WorkOrder
import com.sadaksetu.domain.repositories.WorkOrderRepository
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.toRequestBody
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class WorkOrderRepositoryImpl @Inject constructor(
    private val api: ApiService,
    @ApplicationContext private val context: Context,
) : WorkOrderRepository {

    override suspend fun getMyWork(): Result<List<WorkOrder>> = withContext(Dispatchers.IO) {
        runCatching {
            api.getMyWork().map { it.toDomain() }
        }
    }

    override suspend fun acceptWorkOrder(id: String, note: String?): Result<WorkOrder> = withContext(Dispatchers.IO) {
        runCatching {
            api.acceptWorkOrder(id, OptionalNoteDto(note)).toDomain()
        }
    }

    override suspend fun startWorkOrder(id: String, note: String?): Result<WorkOrder> = withContext(Dispatchers.IO) {
        runCatching {
            api.startWorkOrder(id, OptionalNoteDto(note)).toDomain()
        }
    }

    override suspend fun updateProgress(id: String, percentage: Int, notes: String?): Result<WorkOrder> = withContext(Dispatchers.IO) {
        runCatching {
            api.updateWorkProgress(id, WorkOrderProgressDto(percentage, notes)).toDomain()
        }
    }

    override suspend fun reportDelay(id: String, reason: String): Result<WorkOrder> = withContext(Dispatchers.IO) {
        runCatching {
            api.reportWorkDelay(id, WorkOrderDelayDto(reason)).toDomain()
        }
    }

    override suspend fun updateMembers(id: String, memberIds: List<String>): Result<WorkOrder> = withContext(Dispatchers.IO) {
        runCatching {
            api.updateWorkMembers(id, WorkOrderMembersDto(memberIds)).toDomain()
        }
    }

    override suspend fun uploadWorkPhoto(
        workOrderId: String,
        complaintId: String,
        photoType: String,
        uri: Uri,
        latitude: Double,
        longitude: Double,
    ): Result<WorkOrder> = withContext(Dispatchers.IO) {
        runCatching {
            val bytes = context.contentResolver.openInputStream(uri)?.use { input -> input.readBytes() }
                ?: error("Photo could not be read")
            require(bytes.size <= 10 * 1024 * 1024) { "Photo must be 10 MB or smaller" }
            val mediaType = (context.contentResolver.getType(uri) ?: "image/jpeg").toMediaType()
            val body = bytes.toRequestBody(mediaType)
            val text = "text/plain".toMediaType()

            val uploaded = api.uploadImage(
                complaintId = complaintId,
                image = MultipartBody.Part.createFormData("image", "work-evidence.jpg", body),
                latitude = latitude.toString().toRequestBody(text),
                longitude = longitude.toString().toRequestBody(text),
            )

            val photoUrl = "/api/v1/complaints/$complaintId/images/${uploaded.id}"
            api.addWorkPhoto(
                id = workOrderId,
                body = WorkOrderPhotoDto(
                    photoType = photoType.uppercase(),
                    photoUrl = photoUrl,
                ),
            ).toDomain()
        }
    }

    override suspend fun submitCompletion(id: String, notes: String?): Result<WorkOrder> = withContext(Dispatchers.IO) {
        runCatching {
            api.submitWorkCompletion(id, WorkOrderCompletionDto(notes)).toDomain()
        }
    }

    override suspend fun getMyTeamMembers(): Result<List<TeamMember>> = withContext(Dispatchers.IO) {
        runCatching {
            api.getMyTeamMembers().map { it.toDomain() }
        }
    }

    override suspend fun createTeamMember(
        name: String,
        employeeId: String,
        phone: String?,
        skills: List<String>,
    ): Result<TeamMember> = withContext(Dispatchers.IO) {
        runCatching {
            api.createMyTeamMember(
                TeamMemberCreateDto(
                    name = name,
                    employeeId = employeeId,
                    phone = phone,
                    skills = skills,
                )
            ).toDomain()
        }
    }
}
