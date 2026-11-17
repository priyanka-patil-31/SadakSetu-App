package com.sadaksetu.domain.models

data class User(
    val id: String,
    val email: String,
    val fullName: String,
    val role: String,
    val isActive: Boolean,
)

data class Location(
    val latitude: Double,
    val longitude: Double,
    val address: String? = null,
    val area: String? = null,
    val zone: String? = null,
)

data class Complaint(
    val id: String,
    val reporterId: String,
    val complaintNumber: String,
    val title: String,
    val description: String,
    val status: String,
    val severity: String,
    val location: Location,
    val createdAt: String,
    val updatedAt: String,
)

data class ComplaintUpdate(
    val id: String,
    val eventType: String,
    val oldValue: String?,
    val newValue: String?,
    val note: String?,
    val createdAt: String,
)

data class Notification(
    val id: String,
    val complaintId: String?,
    val title: String,
    val body: String,
    val readAt: String?,
    val createdAt: String,
)

data class WorkOrder(
    val id: String,
    val complaintId: String,
    val teamId: String,
    val workOrderNumber: String,
    val priority: String,
    val expectedCompletionDate: String?,
    val instructions: String?,
    val workStatus: String,
    val progressPercentage: Int,
    val progressNotes: String?,
    val delayReason: String?,
    val beforePhotos: List<String>,
    val afterPhotos: List<String>,
    val assignedMemberIds: List<String>,
    val completionNotes: String?,
    val teamName: String,
    val teamLeadName: String,
    val teamPhone: String,
    val complaintNumber: String,
    val complaintTitle: String,
    val complaintDescription: String,
    val complaintStatus: String,
    val complaintSeverity: String,
    val complaintAddress: String,
    val complaintLatitude: Double?,
    val complaintLongitude: Double?,
    val complaintPhotoUrl: String?,
    val createdAt: String,
)

data class TeamMember(
    val id: String,
    val teamId: String,
    val name: String,
    val employeeId: String,
    val phone: String?,
    val skills: List<String>,
    val isActive: Boolean,
)
