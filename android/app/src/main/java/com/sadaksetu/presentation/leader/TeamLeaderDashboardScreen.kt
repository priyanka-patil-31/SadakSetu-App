@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.sadaksetu.presentation.leader

import android.widget.Toast
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Add
import androidx.compose.material.icons.filled.Assignment
import androidx.compose.material.icons.filled.Engineering
import androidx.compose.material.icons.filled.ExitToApp
import androidx.compose.material.icons.filled.Group
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Notifications
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material.icons.outlined.Assignment
import androidx.compose.material.icons.outlined.Group
import androidx.compose.material.icons.outlined.Notifications
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.FloatingActionButton
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.NavigationBar
import androidx.compose.material3.NavigationBarItem
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.sadaksetu.core.common.UiState
import com.sadaksetu.domain.models.User
import com.sadaksetu.domain.models.WorkOrder

@Composable
fun TeamLeaderApp(
    user: User,
    onSignOut: () -> Unit,
    viewModel: WorkOrderViewModel = hiltViewModel(),
) {
    val workOrdersState by viewModel.workOrdersState.collectAsState()
    val teamMembersState by viewModel.teamMembersState.collectAsState()
    val selectedFilter by viewModel.selectedFilter.collectAsState()
    val message by viewModel.message.collectAsState()
    val context = LocalContext.current

    var currentTab by remember { mutableIntStateOf(0) }
    var selectedWorkOrderId by remember { mutableStateOf<String?>(null) }
    var showSignOutDialog by remember { mutableStateOf(false) }
    var showAddMemberDialog by remember { mutableStateOf(false) }

    LaunchedEffect(message) {
        message?.let {
            Toast.makeText(context, it, Toast.LENGTH_SHORT).show()
            viewModel.clearMessage()
        }
    }

    // If viewing work order details
    if (selectedWorkOrderId != null) {
        val activeOrder = when (val s = workOrdersState) {
            is UiState.Data -> s.value.find { it.id == selectedWorkOrderId }
            else -> null
        }
        if (activeOrder != null) {
            WorkOrderDetailScreen(
                workOrder = activeOrder,
                viewModel = viewModel,
                onBack = { selectedWorkOrderId = null },
            )
            return
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Surface(
                                shape = CircleShape,
                                color = Color(0xFFEA580C),
                                modifier = Modifier.size(8.dp),
                            ) {}
                            Text(
                                text = "SadakSetu Field Portal",
                                fontWeight = FontWeight.ExtraBold,
                                fontSize = 17.sp,
                                color = Color(0xFF0F172A),
                            )
                        }
                        Text(
                            text = "${user.fullName} · Team Leader",
                            fontSize = 11.sp,
                            fontWeight = FontWeight.Medium,
                            color = Color(0xFF64748B),
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.loadMyWork(); viewModel.loadTeamMembers() }) {
                        Icon(Icons.Default.Refresh, contentDescription = "Refresh")
                    }
                    IconButton(onClick = { showSignOutDialog = true }) {
                        Icon(Icons.Default.ExitToApp, contentDescription = "Sign Out", tint = Color(0xFFDC2626))
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = Color.White),
            )
        },
        bottomBar = {
            NavigationBar(containerColor = Color.White, tonalElevation = 8.dp) {
                NavigationBarItem(
                    selected = currentTab == 0,
                    onClick = { currentTab = 0 },
                    icon = {
                        Icon(
                            if (currentTab == 0) Icons.Filled.Assignment else Icons.Outlined.Assignment,
                            contentDescription = "My Work",
                        )
                    },
                    label = { Text("My Work", fontSize = 11.sp, fontWeight = if (currentTab == 0) FontWeight.Bold else FontWeight.Normal) },
                )
                NavigationBarItem(
                    selected = currentTab == 1,
                    onClick = { currentTab = 1 },
                    icon = {
                        Icon(
                            if (currentTab == 1) Icons.Filled.Group else Icons.Outlined.Group,
                            contentDescription = "Team Members",
                        )
                    },
                    label = { Text("Team Members", fontSize = 11.sp, fontWeight = if (currentTab == 1) FontWeight.Bold else FontWeight.Normal) },
                )
            }
        },
        floatingActionButton = {
            if (currentTab == 1) {
                FloatingActionButton(
                    onClick = { showAddMemberDialog = true },
                    containerColor = Color(0xFFEA580C),
                    contentColor = Color.White,
                ) {
                    Icon(Icons.Default.Add, contentDescription = "Add Member")
                }
            }
        }
    ) { padding ->
        Box(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .background(Color(0xFFF8FAFC)),
        ) {
            when (currentTab) {
                // TAB 0: MY ASSIGNED WORK
                0 -> {
                    Column(modifier = Modifier.fillMaxSize()) {
                        // Filter Pills Bar
                        LazyRow(
                            modifier = Modifier
                                .fillMaxWidth()
                                .background(Color.White)
                                .padding(horizontal = 16.dp, vertical = 10.dp),
                            horizontalArrangement = Arrangement.spacedBy(8.dp),
                        ) {
                            val filters = listOf(
                                "ALL" to "All Work",
                                "PENDING" to "Pending",
                                "IN_PROGRESS" to "In Progress",
                                "DELAYED" to "Delayed",
                                "COMPLETED" to "Completed",
                            )
                            items(filters) { (key, label) ->
                                val isSelected = selectedFilter == key
                                Surface(
                                    shape = RoundedCornerShape(20.dp),
                                    color = if (isSelected) Color(0xFFEA580C) else Color(0xFFF1F5F9),
                                    modifier = Modifier.clickable { viewModel.setFilter(key) },
                                ) {
                                    Text(
                                        text = label,
                                        modifier = Modifier.padding(horizontal = 14.dp, vertical = 6.dp),
                                        fontSize = 12.sp,
                                        fontWeight = if (isSelected) FontWeight.Bold else FontWeight.Medium,
                                        color = if (isSelected) Color.White else Color(0xFF475569),
                                    )
                                }
                            }
                        }

                        // Work Orders List
                        when (val state = workOrdersState) {
                            UiState.Loading -> {
                                Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                    CircularProgressIndicator(color = Color(0xFFEA580C))
                                }
                            }
                            is UiState.Error -> {
                                Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                                    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                        Text(text = "Failed to load assignments", fontWeight = FontWeight.Bold, color = Color(0xFFDC2626))
                                        Text(text = state.message, fontSize = 12.sp, color = Color(0xFF64748B))
                                        Button(onClick = { viewModel.loadMyWork() }) { Text("Retry") }
                                    }
                                }
                            }
                            is UiState.Data -> {
                                val filteredList = state.value.filter { wo ->
                                    when (selectedFilter) {
                                        "PENDING" -> wo.workStatus == "PENDING"
                                        "IN_PROGRESS" -> wo.workStatus == "IN_PROGRESS" || wo.workStatus == "ACCEPTED"
                                        "DELAYED" -> wo.workStatus == "DELAYED"
                                        "COMPLETED" -> wo.workStatus == "COMPLETED" || wo.workStatus == "COMPLETION_SUBMITTED"
                                        else -> true
                                    }
                                }

                                if (filteredList.isEmpty()) {
                                    Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                                        Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                            Icon(Icons.Default.Engineering, contentDescription = "Empty", tint = Color(0xFFCBD5E1), modifier = Modifier.size(54.dp))
                                            Text(text = "No work orders in this category", fontWeight = FontWeight.SemiBold, fontSize = 14.sp, color = Color(0xFF64748B))
                                            Text(text = "New assignments dispatched by Admin will appear here.", fontSize = 12.sp, color = Color(0xFF94A3B8))
                                        }
                                    }
                                } else {
                                    LazyColumn(
                                        modifier = Modifier.fillMaxSize().padding(horizontal = 16.dp, vertical = 12.dp),
                                        verticalArrangement = Arrangement.spacedBy(12.dp),
                                    ) {
                                        items(filteredList) { wo ->
                                            WorkOrderCard(
                                                workOrder = wo,
                                                onClick = { selectedWorkOrderId = wo.id },
                                            )
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                // TAB 1: TEAM MEMBERS
                1 -> {
                    when (val state = teamMembersState) {
                        UiState.Loading -> {
                            Box(modifier = Modifier.fillMaxSize(), contentAlignment = Alignment.Center) {
                                CircularProgressIndicator(color = Color(0xFFEA580C))
                            }
                        }
                        is UiState.Error -> {
                            Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                                Text(text = "Error: ${state.message}", color = Color.Red)
                            }
                        }
                        is UiState.Data -> {
                            if (state.value.isEmpty()) {
                                Box(modifier = Modifier.fillMaxSize().padding(24.dp), contentAlignment = Alignment.Center) {
                                    Column(horizontalAlignment = Alignment.CenterHorizontally, verticalArrangement = Arrangement.spacedBy(8.dp)) {
                                        Icon(Icons.Default.Group, contentDescription = "No members", tint = Color(0xFFCBD5E1), modifier = Modifier.size(54.dp))
                                        Text(text = "No crew members registered", fontWeight = FontWeight.Bold, color = Color(0xFF64748B))
                                        Text(text = "Tap the + button to add workers to your team.", fontSize = 12.sp, color = Color(0xFF94A3B8))
                                    }
                                }
                            } else {
                                LazyColumn(
                                    modifier = Modifier.fillMaxSize().padding(16.dp),
                                    verticalArrangement = Arrangement.spacedBy(10.dp),
                                ) {
                                    items(state.value) { member ->
                                        Card(
                                            colors = CardDefaults.cardColors(containerColor = Color.White),
                                            shape = RoundedCornerShape(12.dp),
                                            modifier = Modifier.fillMaxWidth(),
                                        ) {
                                            Row(
                                                modifier = Modifier.padding(14.dp),
                                                horizontalArrangement = Arrangement.SpaceBetween,
                                                verticalAlignment = Alignment.CenterVertically,
                                            ) {
                                                Column(verticalArrangement = Arrangement.spacedBy(2.dp)) {
                                                    Text(text = member.name, fontWeight = FontWeight.Bold, fontSize = 14.sp)
                                                    Text(text = "Employee ID: ${member.employeeId}", fontSize = 11.sp, color = Color(0xFF64748B))
                                                    if (!member.phone.isNullOrBlank()) {
                                                        Text(text = "Phone: ${member.phone}", fontSize = 11.sp, color = Color(0xFF64748B))
                                                    }
                                                    if (member.skills.isNotEmpty()) {
                                                        Text(text = "Skills: ${member.skills.joinToString(", ")}", fontSize = 11.sp, color = Color(0xFFEA580C))
                                                    }
                                                }

                                                Surface(
                                                    shape = RoundedCornerShape(8.dp),
                                                    color = if (member.isActive) Color(0xFFD1FAE5) else Color(0xFFF1F5F9),
                                                ) {
                                                    Text(
                                                        text = if (member.isActive) "Active" else "Inactive",
                                                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                                        fontSize = 11.sp,
                                                        fontWeight = FontWeight.Bold,
                                                        color = if (member.isActive) Color(0xFF047857) else Color(0xFF64748B),
                                                    )
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    // ADD TEAM MEMBER DIALOG
    if (showAddMemberDialog) {
        var nameText by remember { mutableStateOf("") }
        var empIdText by remember { mutableStateOf("") }
        var phoneText by remember { mutableStateOf("") }
        var skillsText by remember { mutableStateOf("") }

        AlertDialog(
            onDismissRequest = { showAddMemberDialog = false },
            title = { Text("Add Team Member", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    OutlinedTextField(
                        value = nameText,
                        onValueChange = { nameText = it },
                        label = { Text("Full Name *") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = empIdText,
                        onValueChange = { empIdText = it },
                        label = { Text("Employee ID *") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = phoneText,
                        onValueChange = { phoneText = it },
                        label = { Text("Phone (Optional)") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                    OutlinedTextField(
                        value = skillsText,
                        onValueChange = { skillsText = it },
                        label = { Text("Skills (Comma separated)") },
                        placeholder = { Text("e.g. Roller Operator, Asphalt, Masonry") },
                        modifier = Modifier.fillMaxWidth(),
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if (nameText.isNotBlank() && empIdText.isNotBlank()) {
                            val skills = skillsText.split(',').map { it.trim() }.filter { it.isNotEmpty() }
                            viewModel.addTeamMember(
                                name = nameText.trim(),
                                employeeId = empIdText.trim(),
                                phone = phoneText.trim().ifEmpty { null },
                                skills = skills,
                            )
                            showAddMemberDialog = false
                        }
                    },
                    enabled = nameText.isNotBlank() && empIdText.isNotBlank(),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEA580C)),
                ) {
                    Text("Add Member")
                }
            },
            dismissButton = {
                TextButton(onClick = { showAddMemberDialog = false }) { Text("Cancel") }
            },
        )
    }

    // SIGN OUT CONFIRMATION DIALOG
    if (showSignOutDialog) {
        AlertDialog(
            onDismissRequest = { showSignOutDialog = false },
            title = { Text("Sign Out?") },
            text = { Text("Are you sure you want to log out of the Team Leader Portal?") },
            confirmButton = {
                Button(
                    onClick = {
                        showSignOutDialog = false
                        onSignOut()
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFDC2626)),
                ) {
                    Text("Log Out")
                }
            },
            dismissButton = {
                TextButton(onClick = { showSignOutDialog = false }) { Text("Cancel") }
            },
        )
    }
}

@Composable
fun WorkOrderCard(
    workOrder: WorkOrder,
    onClick: () -> Unit,
) {
    Card(
        colors = CardDefaults.cardColors(containerColor = Color.White),
        shape = RoundedCornerShape(16.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
        modifier = Modifier
            .fillMaxWidth()
            .clickable { onClick() },
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(8.dp)) {
            // Badges Row
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Text(
                    text = workOrder.workOrderNumber,
                    fontWeight = FontWeight.ExtraBold,
                    fontSize = 14.sp,
                    color = Color(0xFFEA580C),
                )

                Surface(
                    shape = RoundedCornerShape(8.dp),
                    color = when (workOrder.workStatus) {
                        "PENDING" -> Color(0xFFF1F5F9)
                        "ACCEPTED" -> Color(0xFFE0F2FE)
                        "IN_PROGRESS" -> Color(0xFFDBEAFE)
                        "DELAYED" -> Color(0xFFFEE2E2)
                        "COMPLETION_SUBMITTED" -> Color(0xFFFEF3C7)
                        "COMPLETED" -> Color(0xFFD1FAE5)
                        else -> Color(0xFFF1F5F9)
                    },
                ) {
                    Text(
                        text = workOrder.workStatus.replace('_', ' '),
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 3.dp),
                        fontSize = 10.sp,
                        fontWeight = FontWeight.Bold,
                        color = when (workOrder.workStatus) {
                            "PENDING" -> Color(0xFF475569)
                            "ACCEPTED" -> Color(0xFF0369A1)
                            "IN_PROGRESS" -> Color(0xFF1D4ED8)
                            "DELAYED" -> Color(0xFFB91C1C)
                            "COMPLETION_SUBMITTED" -> Color(0xFFB45309)
                            "COMPLETED" -> Color(0xFF047857)
                            else -> Color(0xFF475569)
                        },
                    )
                }
            }

            Text(
                text = "Complaint #${workOrder.complaintNumber}",
                fontWeight = FontWeight.Medium,
                fontSize = 11.sp,
                color = Color(0xFF64748B),
            )

            // Title
            Text(
                text = workOrder.complaintTitle,
                fontWeight = FontWeight.Bold,
                fontSize = 15.sp,
                color = Color(0xFF0F172A),
                maxLines = 1,
            )

            // Location
            Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                Icon(Icons.Default.LocationOn, contentDescription = "Location", tint = Color(0xFFEA580C), modifier = Modifier.size(14.dp))
                Text(
                    text = workOrder.complaintAddress,
                    fontSize = 12.sp,
                    color = Color(0xFF475569),
                    maxLines = 1,
                )
            }

            // Progress bar
            Column(verticalArrangement = Arrangement.spacedBy(3.dp), modifier = Modifier.padding(top = 4.dp)) {
                Row(
                    modifier = Modifier.fillMaxWidth(),
                    horizontalArrangement = Arrangement.SpaceBetween,
                ) {
                    Text(text = "Progress", fontSize = 11.sp, color = Color(0xFF64748B))
                    Text(text = "${workOrder.progressPercentage}%", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFFEA580C))
                }
                LinearProgressIndicator(
                    progress = { (workOrder.progressPercentage / 100f).coerceIn(0f, 1f) },
                    modifier = Modifier
                        .fillMaxWidth()
                        .height(6.dp)
                        .clip(CircleShape),
                    color = Color(0xFFEA580C),
                    trackColor = Color(0xFFE2E8F0),
                )
            }

            if (!workOrder.delayReason.isNullOrBlank()) {
                Surface(
                    color = Color(0xFFFEF2F2),
                    shape = RoundedCornerShape(6.dp),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Row(modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp), verticalAlignment = Alignment.CenterVertically) {
                        Icon(Icons.Default.Warning, contentDescription = "Delay", tint = Color(0xFFDC2626), modifier = Modifier.size(13.dp))
                        Spacer(modifier = Modifier.width(4.dp))
                        Text(text = "Delay: ${workOrder.delayReason}", fontSize = 11.sp, color = Color(0xFFB91C1C), maxLines = 1)
                    }
                }
            }

            // Target deadline & Tap to open
            Row(
                modifier = Modifier.fillMaxWidth().padding(top = 2.dp),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(4.dp)) {
                    Icon(Icons.Default.Schedule, contentDescription = "Deadline", tint = Color(0xFF94A3B8), modifier = Modifier.size(13.dp))
                    Text(
                        text = if (workOrder.expectedCompletionDate != null) "Due: ${workOrder.expectedCompletionDate.take(10)}" else "No deadline",
                        fontSize = 11.sp,
                        color = Color(0xFF64748B),
                    )
                }

                Text(
                    text = "View details →",
                    fontSize = 11.sp,
                    fontWeight = FontWeight.Bold,
                    color = Color(0xFFEA580C),
                )
            }
        }
    }
}
