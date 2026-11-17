@file:OptIn(androidx.compose.material3.ExperimentalMaterial3Api::class)

package com.sadaksetu.presentation.leader

import android.content.Intent
import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
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
import androidx.compose.foundation.lazy.LazyRow
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AddAPhoto
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.Engineering
import androidx.compose.material.icons.filled.Group
import androidx.compose.material.icons.filled.LocationOn
import androidx.compose.material.icons.filled.Map
import androidx.compose.material.icons.filled.PlayArrow
import androidx.compose.material.icons.filled.Schedule
import androidx.compose.material.icons.filled.Warning
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Button
import androidx.compose.material3.ButtonDefaults
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Checkbox
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.LinearProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Slider
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableFloatStateOf
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.layout.ContentScale
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import coil.compose.AsyncImage
import com.sadaksetu.BuildConfig
import com.sadaksetu.core.common.UiState
import com.sadaksetu.domain.models.WorkOrder

fun resolveImageUrl(url: String?): String? {
    if (url.isNullOrBlank()) return null
    if (url.startsWith("http://") || url.startsWith("https://")) return url
    val base = BuildConfig.API_BASE_URL.trimEnd('/')
    val path = if (url.startsWith("/")) url else "/$url"
    return "$base$path"
}

@Composable
fun WorkOrderDetailScreen(
    workOrder: WorkOrder,
    viewModel: WorkOrderViewModel,
    onBack: () -> Unit,
) {
    val context = LocalContext.current
    val actionInProgress by viewModel.actionInProgress.collectAsState()
    val message by viewModel.message.collectAsState()
    val teamMembersState by viewModel.teamMembersState.collectAsState()

    // Dialog states
    var showProgressDialog by remember { mutableStateOf(false) }
    var progressSliderValue by remember { mutableFloatStateOf(workOrder.progressPercentage.toFloat()) }
    var progressNotesText by remember { mutableStateOf(workOrder.progressNotes ?: "") }

    var showDelayDialog by remember { mutableStateOf(false) }
    var delayReasonText by remember { mutableStateOf(workOrder.delayReason ?: "") }

    var showMembersDialog by remember { mutableStateOf(false) }
    val selectedMemberIds = remember { mutableStateListOf<String>().apply { addAll(workOrder.assignedMemberIds) } }

    var showPhotoTypeDialog by remember { mutableStateOf(false) }
    var pendingPhotoType by remember { mutableStateOf("BEFORE") }

    var showCompletionDialog by remember { mutableStateOf(false) }
    var completionNotesText by remember { mutableStateOf("") }

    val photoPickerLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        uri?.let {
            viewModel.uploadPhoto(
                workOrderId = workOrder.id,
                complaintId = workOrder.complaintId,
                photoType = pendingPhotoType,
                uri = it,
            )
        }
    }

    LaunchedEffect(message) {
        message?.let {
            Toast.makeText(context, it, Toast.LENGTH_SHORT).show()
            viewModel.clearMessage()
        }
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text(
                            text = workOrder.workOrderNumber,
                            fontWeight = FontWeight.Bold,
                            fontSize = 17.sp,
                        )
                        Text(
                            text = "Linked to ${workOrder.complaintNumber}",
                            fontSize = 11.sp,
                            color = Color(0xFF64748B),
                        )
                    }
                },
                navigationIcon = {
                    IconButton(onClick = onBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                },
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .verticalScroll(rememberScrollState())
                .padding(padding)
                .padding(horizontal = 16.dp, vertical = 12.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
        ) {
            // Top Status & Priority Card
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(16.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
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
                                modifier = Modifier.padding(horizontal = 10.dp, vertical = 4.dp),
                                fontSize = 11.sp,
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

                        Surface(
                            shape = RoundedCornerShape(8.dp),
                            color = when (workOrder.priority) {
                                "CRITICAL" -> Color(0xFFFEE2E2)
                                "HIGH" -> Color(0xFFFFEDD5)
                                else -> Color(0xFFF1F5F9)
                            },
                        ) {
                            Text(
                                text = "PRIORITY: ${workOrder.priority}",
                                modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp),
                                fontSize = 10.sp,
                                fontWeight = FontWeight.ExtraBold,
                                color = when (workOrder.priority) {
                                    "CRITICAL" -> Color(0xFFB91C1C)
                                    "HIGH" -> Color(0xFFC2410C)
                                    else -> Color(0xFF475569)
                                },
                            )
                        }
                    }

                    // Progress Section
                    Column(verticalArrangement = Arrangement.spacedBy(4.dp)) {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                        ) {
                            Text(text = "Repair Progress", fontSize = 12.sp, fontWeight = FontWeight.SemiBold)
                            Text(text = "${workOrder.progressPercentage}%", fontSize = 12.sp, fontWeight = FontWeight.Bold, color = Color(0xFFEA580C))
                        }
                        LinearProgressIndicator(
                            progress = { (workOrder.progressPercentage / 100f).coerceIn(0f, 1f) },
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(8.dp)
                                .clip(CircleShape),
                            color = Color(0xFFEA580C),
                            trackColor = Color(0xFFE2E8F0),
                        )
                    }

                    if (!workOrder.progressNotes.isNullOrBlank()) {
                        Text(
                            text = "“${workOrder.progressNotes}”",
                            fontSize = 12.sp,
                            color = Color(0xFF475569),
                            fontFamily = FontFamily.Serif,
                        )
                    }

                    if (!workOrder.delayReason.isNullOrBlank()) {
                        Surface(
                            color = Color(0xFFFEF2F2),
                            shape = RoundedCornerShape(8.dp),
                            border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFECACA)),
                            modifier = Modifier.fillMaxWidth(),
                        ) {
                            Row(modifier = Modifier.padding(10.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                Icon(Icons.Default.Warning, contentDescription = "Delay", tint = Color(0xFFDC2626), modifier = Modifier.size(16.dp))
                                Column {
                                    Text(text = "Delay Reported", fontWeight = FontWeight.Bold, fontSize = 11.sp, color = Color(0xFF991B1B))
                                    Text(text = workOrder.delayReason, fontSize = 11.sp, color = Color(0xFF7F1D1D))
                                }
                            }
                        }
                    }

                    // Target deadline
                    Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                        Icon(Icons.Default.Schedule, contentDescription = "Deadline", tint = Color(0xFF64748B), modifier = Modifier.size(15.dp))
                        Text(
                            text = if (workOrder.expectedCompletionDate != null) "Deadline: ${workOrder.expectedCompletionDate}" else "Target deadline not set",
                            fontSize = 12.sp,
                            color = Color(0xFF475569),
                        )
                    }
                }
            }

            // Citizen Complaint Details Card
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(16.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(
                        text = "CITIZEN COMPLAINT REPORT",
                        fontSize = 11.sp,
                        fontWeight = FontWeight.Bold,
                        color = Color(0xFF94A3B8),
                        letterSpacing = 1.sp,
                    )
                    Text(
                        text = workOrder.complaintTitle,
                        fontWeight = FontWeight.Bold,
                        fontSize = 16.sp,
                        color = Color(0xFF0F172A),
                    )
                    Text(
                        text = workOrder.complaintDescription,
                        fontSize = 13.sp,
                        color = Color(0xFF334155),
                        lineHeight = 18.sp,
                    )

                    // Address with Map Button
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Row(
                            modifier = Modifier.weight(1f),
                            horizontalArrangement = Arrangement.spacedBy(6.dp),
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Icon(Icons.Default.LocationOn, contentDescription = "Location", tint = Color(0xFFEA580C), modifier = Modifier.size(16.dp))
                            Text(
                                text = workOrder.complaintAddress,
                                fontSize = 12.sp,
                                color = Color(0xFF475569),
                                maxLines = 2,
                            )
                        }

                        if (workOrder.complaintLatitude != null && workOrder.complaintLongitude != null) {
                            OutlinedButton(
                                onClick = {
                                    val uri = Uri.parse("geo:${workOrder.complaintLatitude},${workOrder.complaintLongitude}?q=${workOrder.complaintLatitude},${workOrder.complaintLongitude}(Road Issue)")
                                    val mapIntent = Intent(Intent.ACTION_VIEW, uri)
                                    context.startActivity(mapIntent)
                                },
                                shape = RoundedCornerShape(8.dp),
                            ) {
                                Icon(Icons.Default.Map, contentDescription = "Map", modifier = Modifier.size(14.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(text = "Map", fontSize = 11.sp)
                            }
                        }
                    }

                    // Citizen initial uploaded photo
                    resolveImageUrl(workOrder.complaintPhotoUrl)?.let { photoUrl ->
                        Spacer(modifier = Modifier.height(4.dp))
                        Text(text = "Citizen Report Photo", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFF64748B))
                        AsyncImage(
                            model = photoUrl,
                            contentDescription = "Citizen photo",
                            modifier = Modifier
                                .fillMaxWidth()
                                .height(180.dp)
                                .clip(RoundedCornerShape(12.dp)),
                            contentScale = ContentScale.Crop,
                        )
                    }
                }
            }

            // Repair Instructions from Admin
            if (!workOrder.instructions.isNullOrBlank()) {
                Card(
                    colors = CardDefaults.cardColors(containerColor = Color(0xFFFFFBEB)),
                    shape = RoundedCornerShape(16.dp),
                    border = androidx.compose.foundation.BorderStroke(1.dp, Color(0xFFFDE68A)),
                    modifier = Modifier.fillMaxWidth(),
                ) {
                    Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(6.dp)) {
                        Row(verticalAlignment = Alignment.CenterVertically, horizontalArrangement = Arrangement.spacedBy(6.dp)) {
                            Icon(Icons.Default.Engineering, contentDescription = "Instructions", tint = Color(0xFFD97706), modifier = Modifier.size(16.dp))
                            Text(text = "ADMIN REPAIR INSTRUCTIONS", fontWeight = FontWeight.Bold, fontSize = 11.sp, color = Color(0xFFB45309))
                        }
                        Text(
                            text = workOrder.instructions,
                            fontSize = 13.sp,
                            color = Color(0xFF78350F),
                            lineHeight = 18.sp,
                        )
                    }
                }
            }

            // Before & After Photos Gallery
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(16.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically,
                    ) {
                        Text(text = "WORK EVIDENCE PHOTOS", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFF94A3B8))
                        if (workOrder.workStatus != "COMPLETED" && workOrder.workStatus != "PENDING") {
                            TextButton(onClick = { showPhotoTypeDialog = true }) {
                                Icon(Icons.Default.AddAPhoto, contentDescription = "Upload", modifier = Modifier.size(14.dp))
                                Spacer(modifier = Modifier.width(4.dp))
                                Text(text = "Add Photo", fontSize = 11.sp)
                            }
                        }
                    }

                    // Before Photos
                    Text(text = "Before Repair (${workOrder.beforePhotos.size})", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFF475569))
                    if (workOrder.beforePhotos.isEmpty()) {
                        Text(text = "No before photos uploaded yet.", fontSize = 11.sp, color = Color(0xFF94A3B8))
                    } else {
                        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            items(workOrder.beforePhotos) { url ->
                                resolveImageUrl(url)?.let { fullUrl ->
                                    AsyncImage(
                                        model = fullUrl,
                                        contentDescription = "Before repair photo",
                                        modifier = Modifier
                                            .size(90.dp)
                                            .clip(RoundedCornerShape(8.dp))
                                            .border(1.dp, Color(0xFFE2E8F0), RoundedCornerShape(8.dp)),
                                        contentScale = ContentScale.Crop,
                                    )
                                }
                            }
                        }
                    }

                    Spacer(modifier = Modifier.height(4.dp))

                    // After Photos
                    Text(text = "After Repair (${workOrder.afterPhotos.size})", fontSize = 12.sp, fontWeight = FontWeight.SemiBold, color = Color(0xFF475569))
                    if (workOrder.afterPhotos.isEmpty()) {
                        Text(text = "No after photos uploaded yet.", fontSize = 11.sp, color = Color(0xFF94A3B8))
                    } else {
                        LazyRow(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            items(workOrder.afterPhotos) { url ->
                                resolveImageUrl(url)?.let { fullUrl ->
                                    AsyncImage(
                                        model = fullUrl,
                                        contentDescription = "After repair photo",
                                        modifier = Modifier
                                            .size(90.dp)
                                            .clip(RoundedCornerShape(8.dp))
                                            .border(1.dp, Color(0xFFE2E8F0), RoundedCornerShape(8.dp)),
                                        contentScale = ContentScale.Crop,
                                    )
                                }
                            }
                        }
                    }
                }
            }

            // Contextual Action Buttons
            Card(
                colors = CardDefaults.cardColors(containerColor = Color.White),
                shape = RoundedCornerShape(16.dp),
                elevation = CardDefaults.cardElevation(defaultElevation = 2.dp),
                modifier = Modifier.fillMaxWidth(),
            ) {
                Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(text = "TEAM LEADER ACTIONS", fontSize = 11.sp, fontWeight = FontWeight.Bold, color = Color(0xFF94A3B8))

                    if (actionInProgress) {
                        Row(
                            modifier = Modifier.fillMaxWidth().padding(12.dp),
                            horizontalArrangement = Arrangement.Center,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            CircularProgressIndicator(modifier = Modifier.size(20.dp), color = Color(0xFFEA580C))
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(text = "Processing update…", fontSize = 12.sp, color = Color(0xFF64748B))
                        }
                    } else {
                        when (workOrder.workStatus) {
                            "PENDING" -> {
                                Button(
                                    onClick = { viewModel.acceptWork(workOrder.id) },
                                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEA580C)),
                                    modifier = Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(10.dp),
                                ) {
                                    Icon(Icons.Default.Check, contentDescription = "Accept")
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(text = "Accept Work Order")
                                }
                            }
                            "ACCEPTED" -> {
                                Button(
                                    onClick = { viewModel.startWork(workOrder.id) },
                                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF2563EB)),
                                    modifier = Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(10.dp),
                                ) {
                                    Icon(Icons.Default.PlayArrow, contentDescription = "Start")
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(text = "Start Repair Work")
                                }
                            }
                            "IN_PROGRESS", "DELAYED" -> {
                                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    Button(
                                        onClick = { showProgressDialog = true },
                                        colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEA580C)),
                                        modifier = Modifier.weight(1f),
                                        shape = RoundedCornerShape(10.dp),
                                    ) {
                                        Text(text = "Update %", fontSize = 12.sp)
                                    }
                                    OutlinedButton(
                                        onClick = { showDelayDialog = true },
                                        modifier = Modifier.weight(1f),
                                        shape = RoundedCornerShape(10.dp),
                                    ) {
                                        Text(text = "Report Delay", fontSize = 12.sp, color = Color(0xFFDC2626))
                                    }
                                }

                                Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                                    OutlinedButton(
                                        onClick = { showMembersDialog = true },
                                        modifier = Modifier.weight(1f),
                                        shape = RoundedCornerShape(10.dp),
                                    ) {
                                        Icon(Icons.Default.Group, contentDescription = "Members", modifier = Modifier.size(14.dp))
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(text = "Assign Crew", fontSize = 12.sp)
                                    }
                                    OutlinedButton(
                                        onClick = { showPhotoTypeDialog = true },
                                        modifier = Modifier.weight(1f),
                                        shape = RoundedCornerShape(10.dp),
                                    ) {
                                        Icon(Icons.Default.AddAPhoto, contentDescription = "Photo", modifier = Modifier.size(14.dp))
                                        Spacer(modifier = Modifier.width(4.dp))
                                        Text(text = "Add Photo", fontSize = 12.sp)
                                    }
                                }

                                Spacer(modifier = Modifier.height(4.dp))

                                Button(
                                    onClick = { showCompletionDialog = true },
                                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF059669)),
                                    modifier = Modifier.fillMaxWidth(),
                                    shape = RoundedCornerShape(10.dp),
                                ) {
                                    Icon(Icons.Default.CheckCircle, contentDescription = "Submit")
                                    Spacer(modifier = Modifier.width(6.dp))
                                    Text(text = "Submit Completion for Verification")
                                }
                            }
                            "COMPLETION_SUBMITTED" -> {
                                Surface(
                                    color = Color(0xFFFEF3C7),
                                    shape = RoundedCornerShape(10.dp),
                                    modifier = Modifier.fillMaxWidth(),
                                ) {
                                    Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                                        Icon(Icons.Default.Schedule, contentDescription = "Awaiting", tint = Color(0xFFD97706), modifier = Modifier.size(18.dp))
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text(
                                            text = "Completion submitted! Awaiting Admin review & approval.",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.SemiBold,
                                            color = Color(0xFF92400E),
                                        )
                                    }
                                }
                            }
                            "COMPLETED" -> {
                                Surface(
                                    color = Color(0xFFD1FAE5),
                                    shape = RoundedCornerShape(10.dp),
                                    modifier = Modifier.fillMaxWidth(),
                                ) {
                                    Row(modifier = Modifier.padding(12.dp), verticalAlignment = Alignment.CenterVertically) {
                                        Icon(Icons.Default.CheckCircle, contentDescription = "Done", tint = Color(0xFF059669), modifier = Modifier.size(18.dp))
                                        Spacer(modifier = Modifier.width(8.dp))
                                        Text(
                                            text = "Work order verified and completed by Admin.",
                                            fontSize = 12.sp,
                                            fontWeight = FontWeight.Bold,
                                            color = Color(0xFF065F46),
                                        )
                                    }
                                }
                            }
                        }
                    }
                }
            }

            Spacer(modifier = Modifier.height(20.dp))
        }
    }

    // 1. UPDATE PROGRESS DIALOG
    if (showProgressDialog) {
        AlertDialog(
            onDismissRequest = { showProgressDialog = false },
            title = { Text("Update Progress", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(12.dp)) {
                    Text(text = "Progress: ${progressSliderValue.toInt()}%", fontWeight = FontWeight.SemiBold, color = Color(0xFFEA580C))
                    Slider(
                        value = progressSliderValue,
                        onValueChange = { progressSliderValue = it },
                        valueRange = 0f..100f,
                        steps = 19,
                    )
                    OutlinedTextField(
                        value = progressNotesText,
                        onValueChange = { progressNotesText = it },
                        label = { Text("Field Progress Notes") },
                        placeholder = { Text("e.g., Finished subgrade compaction, applying hot mix asphalt...") },
                        modifier = Modifier.fillMaxWidth(),
                        maxLines = 3,
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.updateProgress(
                            id = workOrder.id,
                            percentage = progressSliderValue.toInt(),
                            notes = progressNotesText.trim().ifEmpty { null },
                        )
                        showProgressDialog = false
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEA580C)),
                ) {
                    Text("Save Progress")
                }
            },
            dismissButton = {
                TextButton(onClick = { showProgressDialog = false }) { Text("Cancel") }
            },
        )
    }

    // 2. REPORT DELAY DIALOG
    if (showDelayDialog) {
        AlertDialog(
            onDismissRequest = { showDelayDialog = false },
            title = { Text("Report Work Delay", fontWeight = FontWeight.Bold, color = Color(0xFFDC2626)) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(text = "Explain the cause of delay (e.g., adverse weather, shortage of materials, utility leak):", fontSize = 12.sp)
                    OutlinedTextField(
                        value = delayReasonText,
                        onValueChange = { delayReasonText = it },
                        label = { Text("Reason for Delay *") },
                        modifier = Modifier.fillMaxWidth(),
                        maxLines = 4,
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        if (delayReasonText.isNotBlank()) {
                            viewModel.reportDelay(workOrder.id, delayReasonText.trim())
                            showDelayDialog = false
                        }
                    },
                    enabled = delayReasonText.isNotBlank(),
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFDC2626)),
                ) {
                    Text("Submit Delay Flag")
                }
            },
            dismissButton = {
                TextButton(onClick = { showDelayDialog = false }) { Text("Cancel") }
            },
        )
    }

    // 3. ASSIGN TEAM MEMBERS DIALOG
    if (showMembersDialog) {
        AlertDialog(
            onDismissRequest = { showMembersDialog = false },
            title = { Text("Assign Crew Members", fontWeight = FontWeight.Bold) },
            text = {
                when (val members = teamMembersState) {
                    is UiState.Data -> {
                        if (members.value.isEmpty()) {
                            Text("No team members found. Add members in the Team Members tab.", fontSize = 12.sp)
                        } else {
                            Column(modifier = Modifier.verticalScroll(rememberScrollState())) {
                                members.value.forEach { member ->
                                    val isChecked = selectedMemberIds.contains(member.id)
                                    Row(
                                        verticalAlignment = Alignment.CenterVertically,
                                        modifier = Modifier
                                            .fillMaxWidth()
                                            .clickable {
                                                if (isChecked) selectedMemberIds.remove(member.id)
                                                else selectedMemberIds.add(member.id)
                                            }
                                            .padding(vertical = 4.dp),
                                    ) {
                                        Checkbox(
                                            checked = isChecked,
                                            onCheckedChange = { checked ->
                                                if (checked) selectedMemberIds.add(member.id)
                                                else selectedMemberIds.remove(member.id)
                                            },
                                        )
                                        Column {
                                            Text(text = member.name, fontWeight = FontWeight.SemiBold, fontSize = 13.sp)
                                            Text(text = "ID: ${member.employeeId}", fontSize = 11.sp, color = Color(0xFF64748B))
                                        }
                                    }
                                }
                            }
                        }
                    }
                    UiState.Loading -> CircularProgressIndicator()
                    is UiState.Error -> Text("Failed to load members: ${members.message}", fontSize = 12.sp, color = Color.Red)
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.updateMembers(workOrder.id, selectedMemberIds.toList())
                        showMembersDialog = false
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFFEA580C)),
                ) {
                    Text("Save Crew Assignment")
                }
            },
            dismissButton = {
                TextButton(onClick = { showMembersDialog = false }) { Text("Cancel") }
            },
        )
    }

    // 4. PHOTO TYPE SELECTION DIALOG
    if (showPhotoTypeDialog) {
        AlertDialog(
            onDismissRequest = { showPhotoTypeDialog = false },
            title = { Text("Select Photo Type", fontWeight = FontWeight.Bold) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
                    Text(text = "Which evidence stage is this photo for?", fontSize = 13.sp)
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(
                            onClick = {
                                pendingPhotoType = "BEFORE"
                                showPhotoTypeDialog = false
                                photoPickerLauncher.launch("image/*")
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF0284C7)),
                            modifier = Modifier.weight(1f),
                        ) {
                            Text("Before Repair")
                        }
                        Button(
                            onClick = {
                                pendingPhotoType = "AFTER"
                                showPhotoTypeDialog = false
                                photoPickerLauncher.launch("image/*")
                            },
                            colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF059669)),
                            modifier = Modifier.weight(1f),
                        ) {
                            Text("After Repair")
                        }
                    }
                }
            },
            confirmButton = {},
            dismissButton = {
                TextButton(onClick = { showPhotoTypeDialog = false }) { Text("Cancel") }
            },
        )
    }

    // 5. SUBMIT COMPLETION DIALOG
    if (showCompletionDialog) {
        AlertDialog(
            onDismissRequest = { showCompletionDialog = false },
            title = { Text("Submit Completion", fontWeight = FontWeight.Bold, color = Color(0xFF059669)) },
            text = {
                Column(verticalArrangement = Arrangement.spacedBy(10.dp)) {
                    Text(text = "Ready to submit this repair for Admin inspection? Make sure after-repair photos are uploaded.", fontSize = 12.sp)
                    OutlinedTextField(
                        value = completionNotesText,
                        onValueChange = { completionNotesText = it },
                        label = { Text("Completion Notes (Optional)") },
                        placeholder = { Text("e.g., Pothole filled with dense bituminous macadam, surface leveled and compacted.") },
                        modifier = Modifier.fillMaxWidth(),
                        maxLines = 3,
                    )
                }
            },
            confirmButton = {
                Button(
                    onClick = {
                        viewModel.submitCompletion(workOrder.id, completionNotesText.trim().ifEmpty { null })
                        showCompletionDialog = false
                    },
                    colors = ButtonDefaults.buttonColors(containerColor = Color(0xFF059669)),
                ) {
                    Text("Confirm Submission")
                }
            },
            dismissButton = {
                TextButton(onClick = { showCompletionDialog = false }) { Text("Cancel") }
            },
        )
    }
}
