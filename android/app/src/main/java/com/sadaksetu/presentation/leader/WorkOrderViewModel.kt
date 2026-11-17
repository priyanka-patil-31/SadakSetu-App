package com.sadaksetu.presentation.leader

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.sadaksetu.core.common.UiState
import com.sadaksetu.domain.models.TeamMember
import com.sadaksetu.domain.models.WorkOrder
import com.sadaksetu.domain.repositories.WorkOrderRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

@HiltViewModel
class WorkOrderViewModel @Inject constructor(
    private val repository: WorkOrderRepository,
) : ViewModel() {

    private val _workOrdersState = MutableStateFlow<UiState<List<WorkOrder>>>(UiState.Loading)
    val workOrdersState: StateFlow<UiState<List<WorkOrder>>> = _workOrdersState.asStateFlow()

    private val _teamMembersState = MutableStateFlow<UiState<List<TeamMember>>>(UiState.Loading)
    val teamMembersState: StateFlow<UiState<List<TeamMember>>> = _teamMembersState.asStateFlow()

    private val _selectedFilter = MutableStateFlow("ALL")
    val selectedFilter: StateFlow<String> = _selectedFilter.asStateFlow()

    private val _actionInProgress = MutableStateFlow(false)
    val actionInProgress: StateFlow<Boolean> = _actionInProgress.asStateFlow()

    private val _message = MutableStateFlow<String?>(null)
    val message: StateFlow<String?> = _message.asStateFlow()

    init {
        loadMyWork()
        loadTeamMembers()
    }

    fun setFilter(filter: String) {
        _selectedFilter.value = filter
    }

    fun clearMessage() {
        _message.value = null
    }

    fun loadMyWork() {
        viewModelScope.launch {
            _workOrdersState.value = UiState.Loading
            repository.getMyWork().fold(
                onSuccess = { _workOrdersState.value = UiState.Data(it) },
                onFailure = { _workOrdersState.value = UiState.Error(it.message ?: "Failed to load work orders") },
            )
        }
    }

    fun loadTeamMembers() {
        viewModelScope.launch {
            _teamMembersState.value = UiState.Loading
            repository.getMyTeamMembers().fold(
                onSuccess = { _teamMembersState.value = UiState.Data(it) },
                onFailure = { _teamMembersState.value = UiState.Error(it.message ?: "Failed to load team members") },
            )
        }
    }

    fun acceptWork(id: String, note: String? = null, onComplete: () -> Unit = {}) {
        viewModelScope.launch {
            _actionInProgress.value = true
            repository.acceptWorkOrder(id, note).fold(
                onSuccess = {
                    _message.value = "Work order accepted successfully"
                    loadMyWork()
                    onComplete()
                },
                onFailure = {
                    _message.value = "Error: ${it.message}"
                },
            )
            _actionInProgress.value = false
        }
    }

    fun startWork(id: String, note: String? = null, onComplete: () -> Unit = {}) {
        viewModelScope.launch {
            _actionInProgress.value = true
            repository.startWorkOrder(id, note).fold(
                onSuccess = {
                    _message.value = "Repair work started"
                    loadMyWork()
                    onComplete()
                },
                onFailure = {
                    _message.value = "Error: ${it.message}"
                },
            )
            _actionInProgress.value = false
        }
    }

    fun updateProgress(id: String, percentage: Int, notes: String? = null, onComplete: () -> Unit = {}) {
        viewModelScope.launch {
            _actionInProgress.value = true
            repository.updateProgress(id, percentage, notes).fold(
                onSuccess = {
                    _message.value = "Progress updated to $percentage%"
                    loadMyWork()
                    onComplete()
                },
                onFailure = {
                    _message.value = "Error: ${it.message}"
                },
            )
            _actionInProgress.value = false
        }
    }

    fun reportDelay(id: String, reason: String, onComplete: () -> Unit = {}) {
        viewModelScope.launch {
            _actionInProgress.value = true
            repository.reportDelay(id, reason).fold(
                onSuccess = {
                    _message.value = "Delay report submitted"
                    loadMyWork()
                    onComplete()
                },
                onFailure = {
                    _message.value = "Error: ${it.message}"
                },
            )
            _actionInProgress.value = false
        }
    }

    fun updateMembers(id: String, memberIds: List<String>, onComplete: () -> Unit = {}) {
        viewModelScope.launch {
            _actionInProgress.value = true
            repository.updateMembers(id, memberIds).fold(
                onSuccess = {
                    _message.value = "Assigned members updated"
                    loadMyWork()
                    onComplete()
                },
                onFailure = {
                    _message.value = "Error: ${it.message}"
                },
            )
            _actionInProgress.value = false
        }
    }

    fun uploadPhoto(
        workOrderId: String,
        complaintId: String,
        photoType: String,
        uri: Uri,
        onComplete: () -> Unit = {},
    ) {
        viewModelScope.launch {
            _actionInProgress.value = true
            repository.uploadWorkPhoto(
                workOrderId = workOrderId,
                complaintId = complaintId,
                photoType = photoType,
                uri = uri,
            ).fold(
                onSuccess = {
                    _message.value = "$photoType photo uploaded successfully"
                    loadMyWork()
                    onComplete()
                },
                onFailure = {
                    _message.value = "Upload failed: ${it.message}"
                },
            )
            _actionInProgress.value = false
        }
    }

    fun submitCompletion(id: String, notes: String? = null, onComplete: () -> Unit = {}) {
        viewModelScope.launch {
            _actionInProgress.value = true
            repository.submitCompletion(id, notes).fold(
                onSuccess = {
                    _message.value = "Completion submitted for Admin verification!"
                    loadMyWork()
                    onComplete()
                },
                onFailure = {
                    _message.value = "Error: ${it.message}"
                },
            )
            _actionInProgress.value = false
        }
    }

    fun addTeamMember(
        name: String,
        employeeId: String,
        phone: String?,
        skills: List<String>,
        onComplete: () -> Unit = {},
    ) {
        viewModelScope.launch {
            _actionInProgress.value = true
            repository.createTeamMember(name, employeeId, phone, skills).fold(
                onSuccess = {
                    _message.value = "Team member added"
                    loadTeamMembers()
                    onComplete()
                },
                onFailure = {
                    _message.value = "Error: ${it.message}"
                },
            )
            _actionInProgress.value = false
        }
    }
}
