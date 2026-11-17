package com.sadaksetu.data.repository

import com.sadaksetu.core.database.ComplaintEntity
import com.sadaksetu.data.remote.model.*
import com.sadaksetu.domain.models.*

fun UserDto.toDomain() = User(id, email, fullName, role, isActive)

fun LocationDto.toDomain() = Location(latitude, longitude, address, area, zone)

fun ComplaintDto.toDomain() = Complaint(id, reporterId, complaintNumber, title, description, status, severity, location.toDomain(), createdAt, updatedAt)

fun ComplaintDto.toEntity() = ComplaintEntity(id, reporterId, complaintNumber, title, status, severity, location.latitude, location.longitude, createdAt, updatedAt)

fun ComplaintUpdateDto.toDomain() = ComplaintUpdate(id, eventType, oldValue, newValue, note, createdAt)

fun WorkOrderDto.toDomain() = WorkOrder(
    id = id,
    complaintId = complaintId,
    teamId = teamId,
    workOrderNumber = workOrderNumber ?: "WO-${id.take(8).uppercase()}",
    priority = priority ?: "MEDIUM",
    expectedCompletionDate = expectedCompletionDate,
    instructions = instructions,
    workStatus = workStatus,
    progressPercentage = progressPercentage,
    progressNotes = progressNotes,
    delayReason = delayReason,
    beforePhotos = beforePhotos,
    afterPhotos = afterPhotos,
    assignedMemberIds = assignedMemberIds,
    completionNotes = completionNotes,
    teamName = teamName ?: "Repair Team",
    teamLeadName = teamLeadName ?: "Team Lead",
    teamPhone = teamPhone ?: "",
    complaintNumber = complaintNumber ?: "Complaint",
    complaintTitle = complaintTitle ?: "Road Issue",
    complaintDescription = complaintDescription ?: "",
    complaintStatus = complaintStatus ?: "ASSIGNED",
    complaintSeverity = complaintSeverity ?: "MEDIUM",
    complaintAddress = complaintAddress ?: "Road Location",
    complaintLatitude = complaintLatitude,
    complaintLongitude = complaintLongitude,
    complaintPhotoUrl = complaintPhotoUrl,
    createdAt = createdAt,
)

fun TeamMemberDto.toDomain() = TeamMember(
    id = id,
    teamId = teamId,
    name = name,
    employeeId = employeeId,
    phone = phone,
    skills = skills,
    isActive = isActive,
)
