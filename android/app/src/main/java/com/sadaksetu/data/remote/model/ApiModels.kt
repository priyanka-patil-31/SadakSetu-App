package com.sadaksetu.data.remote.model

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

@Serializable
data class UserDto(
    val id: String,
    val email: String,
    @SerialName("full_name") val fullName: String,
    val role: String,
    @SerialName("is_active") val isActive: Boolean,
)

@Serializable
data class AuthResponseDto(
    val user: UserDto,
    @SerialName("session_id") val sessionId: String? = null,
    @SerialName("expires_at") val expiresAt: String,
)

@Serializable
data class SessionDto(
    val id: String,
    @SerialName("expires_at") val expiresAt: String,
    @SerialName("last_activity_at") val lastActivityAt: String,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class RegisterRequestDto(
    val email: String,
    val password: String,
    @SerialName("full_name") val fullName: String,
    val phone: String? = null,
    val role: String = "CITIZEN",
    @SerialName("client_type") val clientType: String = "android",
)

@Serializable
data class LoginRequestDto(
    val email: String,
    val password: String,
    @SerialName("client_type") val clientType: String = "android",
)

@Serializable
data class ForgotPasswordRequestDto(
    val email: String,
    @SerialName("new_password") val newPassword: String,
)

@Serializable
data class ProfileUpdateRequestDto(
    val email: String? = null,
    @SerialName("full_name") val fullName: String? = null,
)

@Serializable
data class PasswordUpdateRequestDto(
    @SerialName("current_password") val currentPassword: String,
    @SerialName("new_password") val newPassword: String,
)

@Serializable
data class LocationDto(
    val id: String? = null,
    val latitude: Double,
    val longitude: Double,
    val address: String? = null,
    val area: String? = null,
    val zone: String? = null,
)

@Serializable
data class NearbyLocationDto(
    val location: LocationDto,
    @SerialName("distance_meters") val distanceMeters: Double,
)

@Serializable
data class ComplaintDto(
    val id: String,
    @SerialName("complaint_number") val complaintNumber: String,
    @SerialName("reporter_id") val reporterId: String,
    val status: String,
    val severity: String,
    val title: String,
    val description: String,
    val location: LocationDto,
    @SerialName("assigned_team_id") val assignedTeamId: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("updated_at") val updatedAt: String,
)

@Serializable
data class ComplaintListDto(
    val items: List<ComplaintDto>,
    val total: Int,
    val page: Int,
    @SerialName("page_size") val pageSize: Int,
)

@Serializable
data class ComplaintCreateRequestDto(
    val title: String,
    val description: String,
    val location: LocationDto,
)

@Serializable
data class ComplaintDeleteRequestDto(val reason: String)

@Serializable
data class ComplaintUpdateDto(
    val id: String,
    @SerialName("actor_id") val actorId: String? = null,
    @SerialName("event_type") val eventType: String,
    @SerialName("old_value") val oldValue: String? = null,
    @SerialName("new_value") val newValue: String? = null,
    val note: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class ComplaintHistoryDto(val items: List<ComplaintUpdateDto>)

@Serializable
data class ComplaintImageDto(
    val id: String,
    @SerialName("complaint_id") val complaintId: String,
    @SerialName("storage_key") val storageKey: String,
    @SerialName("media_type") val mediaType: String,
    @SerialName("byte_size") val byteSize: Long,
    val checksum: String,
    @SerialName("captured_at") val capturedAt: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class AiDetectionDto(
    val id: String,
    @SerialName("complaint_image_id") val complaintImageId: String,
    @SerialName("model_name") val modelName: String,
    @SerialName("model_version") val modelVersion: String,
    val status: String,
    @SerialName("processing_time_ms") val processingTimeMs: Int? = null,
    @SerialName("detection_count") val detectionCount: Int,
    @SerialName("result_metadata") val resultMetadata: Map<String, kotlinx.serialization.json.JsonElement>? = null,
    @SerialName("error_message") val errorMessage: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class AiDetectionBoxDto(
    val x1: Float,
    val y1: Float,
    val x2: Float,
    val y2: Float,
    val confidence: Float,
    val label: String,
)

@Serializable
data class AiDirectDetectionResponseDto(
    @SerialName("model_name") val modelName: String,
    @SerialName("model_version") val modelVersion: String,
    val status: String,
    @SerialName("processing_time_ms") val processingTimeMs: Int,
    @SerialName("detection_count") val detectionCount: Int,
    @SerialName("image_width") val imageWidth: Int,
    @SerialName("image_height") val imageHeight: Int,
    val boxes: List<AiDetectionBoxDto> = emptyList(),
    @SerialName("error_message") val errorMessage: String? = null,
)

@Serializable
data class NotificationDto(
    val id: String,
    @SerialName("complaint_id") val complaintId: String? = null,
    @SerialName("team_id") val teamId: String? = null,
    @SerialName("notification_type") val notificationType: String,
    val title: String,
    val body: String,
    @SerialName("read_at") val readAt: String? = null,
    @SerialName("created_at") val createdAt: String,
)

@Serializable
data class NotificationListDto(
    val items: List<NotificationDto>,
    val total: Int,
    val unread: Int,
    val page: Int,
    @SerialName("page_size") val pageSize: Int,
)

@Serializable
data class DeviceTokenRequestDto(val platform: String, val token: String)

@Serializable
data class WorkOrderDto(
    val id: String,
    @SerialName("complaint_id") val complaintId: String,
    @SerialName("team_id") val teamId: String,
    @SerialName("assigned_by_id") val assignedById: String,
    val status: String,
    @SerialName("released_at") val releasedAt: String? = null,
    @SerialName("created_at") val createdAt: String,
    @SerialName("updated_at") val updatedAt: String,
    @SerialName("work_order_number") val workOrderNumber: String? = null,
    val priority: String? = null,
    @SerialName("expected_completion_date") val expectedCompletionDate: String? = null,
    val instructions: String? = null,
    @SerialName("work_status") val workStatus: String,
    @SerialName("progress_percentage") val progressPercentage: Int = 0,
    @SerialName("progress_notes") val progressNotes: String? = null,
    @SerialName("delay_reason") val delayReason: String? = null,
    @SerialName("before_photos") val beforePhotos: List<String> = emptyList(),
    @SerialName("after_photos") val afterPhotos: List<String> = emptyList(),
    @SerialName("assigned_member_ids") val assignedMemberIds: List<String> = emptyList(),
    @SerialName("completion_notes") val completionNotes: String? = null,
    @SerialName("completion_submitted_at") val completionSubmittedAt: String? = null,
    @SerialName("verified_at") val verifiedAt: String? = null,
    @SerialName("verified_by_id") val verifiedById: String? = null,
    @SerialName("reassign_reason") val reassignReason: String? = null,
    @SerialName("team_name") val teamName: String? = null,
    @SerialName("team_lead_name") val teamLeadName: String? = null,
    @SerialName("team_phone") val teamPhone: String? = null,
    @SerialName("complaint_number") val complaintNumber: String? = null,
    @SerialName("complaint_title") val complaintTitle: String? = null,
    @SerialName("complaint_description") val complaintDescription: String? = null,
    @SerialName("complaint_status") val complaintStatus: String? = null,
    @SerialName("complaint_severity") val complaintSeverity: String? = null,
    @SerialName("complaint_address") val complaintAddress: String? = null,
    @SerialName("complaint_latitude") val complaintLatitude: Double? = null,
    @SerialName("complaint_longitude") val complaintLongitude: Double? = null,
    @SerialName("complaint_photo_url") val complaintPhotoUrl: String? = null,
)

@Serializable
data class OptionalNoteDto(
    val note: String? = null,
)

@Serializable
data class WorkOrderProgressDto(
    @SerialName("progress_percentage") val progressPercentage: Int,
    @SerialName("progress_notes") val progressNotes: String? = null,
)

@Serializable
data class WorkOrderDelayDto(
    @SerialName("delay_reason") val delayReason: String,
)

@Serializable
data class WorkOrderMembersDto(
    @SerialName("member_ids") val memberIds: List<String>,
)

@Serializable
data class WorkOrderPhotoDto(
    @SerialName("photo_type") val photoType: String,
    @SerialName("photo_url") val photoUrl: String,
)

@Serializable
data class WorkOrderCompletionDto(
    @SerialName("completion_notes") val completionNotes: String? = null,
)

@Serializable
data class TeamMemberDto(
    val id: String,
    @SerialName("team_id") val teamId: String,
    val name: String,
    @SerialName("employee_id") val employeeId: String,
    val phone: String? = null,
    val skills: List<String> = emptyList(),
    @SerialName("is_active") val isActive: Boolean = true,
)

@Serializable
data class TeamMemberCreateDto(
    val name: String,
    @SerialName("employee_id") val employeeId: String,
    val phone: String? = null,
    val skills: List<String> = emptyList(),
)
