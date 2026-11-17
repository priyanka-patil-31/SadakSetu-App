package com.sadaksetu.domain.repositories

import android.net.Uri
import com.sadaksetu.domain.models.TeamMember
import com.sadaksetu.domain.models.WorkOrder

interface WorkOrderRepository {
    suspend fun getMyWork(): Result<List<WorkOrder>>
    suspend fun acceptWorkOrder(id: String, note: String? = null): Result<WorkOrder>
    suspend fun startWorkOrder(id: String, note: String? = null): Result<WorkOrder>
    suspend fun updateProgress(id: String, percentage: Int, notes: String? = null): Result<WorkOrder>
    suspend fun reportDelay(id: String, reason: String): Result<WorkOrder>
    suspend fun updateMembers(id: String, memberIds: List<String>): Result<WorkOrder>
    suspend fun uploadWorkPhoto(
        workOrderId: String,
        complaintId: String,
        photoType: String,
        uri: Uri,
        latitude: Double = 0.0,
        longitude: Double = 0.0,
    ): Result<WorkOrder>
    suspend fun submitCompletion(id: String, notes: String? = null): Result<WorkOrder>
    suspend fun getMyTeamMembers(): Result<List<TeamMember>>
    suspend fun createTeamMember(
        name: String,
        employeeId: String,
        phone: String?,
        skills: List<String>,
    ): Result<TeamMember>
}
