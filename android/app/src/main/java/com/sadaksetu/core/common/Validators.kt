package com.sadaksetu.core.common

object Validators {
    fun email(value: String): String? = when {
        value.isBlank() -> "Email address is required"
        !value.contains('@') || !value.contains('.') -> "Enter a valid email address (e.g. name@example.com)"
        else -> null
    }

    fun phone(value: String): String? {
        val digits = value.filter { it.isDigit() }
        return when {
            digits.isBlank() -> "Mobile number is required"
            digits.length != 10 -> "Mobile number must be exactly 10 digits"
            else -> null
        }
    }

    fun password(value: String, registration: Boolean = false): String? {
        if (value.isBlank()) return "Password is required"
        if (value.length < 6) return "Password must be at least 6 characters"
        return null
    }

    fun name(value: String): String? = when {
        value.trim().length < 2 -> "Please enter your full name (minimum 2 characters)"
        else -> null
    }

    fun complaint(title: String, description: String): String? = when {
        title.trim().length < 5 -> "Title must be at least 5 characters"
        description.trim().length < 10 -> "Description must be at least 10 characters"
        else -> null
    }

    private val EMAIL_REGEX = Regex("^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$")
}
