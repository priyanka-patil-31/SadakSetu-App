import { apiClient } from '@/lib/http-client'

export type BackendWorkOrder = {
  id: string
  complaint_id: string
  team_id: string
  assigned_by_id: string
  status: string
  released_at: string | null
  created_at: string
  updated_at: string
  work_order_number: string | null
  priority: string | null
  expected_completion_date: string | null
  instructions: string | null
  work_status: string
  progress_percentage: number
  progress_notes: string | null
  delay_reason: string | null
  before_photos: string[]
  after_photos: string[]
  assigned_member_ids: string[]
  completion_notes: string | null
  completion_submitted_at: string | null
  verified_at: string | null
  verified_by_id: string | null
  reassign_reason: string | null
  team_name: string | null
  team_lead_name: string | null
  team_phone: string | null
  complaint_number: string | null
  complaint_title: string | null
  complaint_description: string | null
  complaint_status: string | null
  complaint_severity: string | null
  complaint_address: string | null
  complaint_latitude: number | null
  complaint_longitude: number | null
  complaint_photo_url: string | null
}

export type WorkOrder = {
  id: string
  complaintId: string
  teamId: string
  assignedById: string
  status: string
  releasedAt: string | null
  createdAt: string
  updatedAt: string
  workOrderNumber: string
  priority: string
  expectedCompletionDate: string | null
  instructions: string | null
  workStatus: string
  progressPercentage: number
  progressNotes: string | null
  delayReason: string | null
  beforePhotos: string[]
  afterPhotos: string[]
  assignedMemberIds: string[]
  completionNotes: string | null
  completionSubmittedAt: string | null
  verifiedAt: string | null
  reassignReason: string | null
  teamName: string
  teamLeadName: string
  teamPhone: string
  complaintNumber: string
  complaintTitle: string
  complaintDescription: string
  complaintStatus: string
  complaintSeverity: string
  complaintAddress: string
  complaintCoordinates: [number, number] | null
  complaintPhotoUrl: string | null
}

export type WorkMonitoringStats = {
  total: number
  pending: number
  ongoing: number
  delayed: number
  completion_submitted: number
  completed: number
}

function mapWorkOrder(b: BackendWorkOrder): WorkOrder {
  return {
    id: b.id,
    complaintId: b.complaint_id,
    teamId: b.team_id,
    assignedById: b.assigned_by_id,
    status: b.status,
    releasedAt: b.released_at,
    createdAt: b.created_at,
    updatedAt: b.updated_at,
    workOrderNumber: b.work_order_number || `WO-${b.id.slice(0, 8).toUpperCase()}`,
    priority: b.priority || 'MEDIUM',
    expectedCompletionDate: b.expected_completion_date,
    instructions: b.instructions,
    workStatus: b.work_status || 'PENDING',
    progressPercentage: b.progress_percentage || 0,
    progressNotes: b.progress_notes,
    delayReason: b.delay_reason,
    beforePhotos: b.before_photos || [],
    afterPhotos: b.after_photos || [],
    assignedMemberIds: b.assigned_member_ids || [],
    completionNotes: b.completion_notes,
    completionSubmittedAt: b.completion_submitted_at,
    verifiedAt: b.verified_at,
    reassignReason: b.reassign_reason,
    teamName: b.team_name || 'Assigned Crew',
    teamLeadName: b.team_lead_name || 'Team Lead',
    teamPhone: b.team_phone || '',
    complaintNumber: b.complaint_number || 'Complaint',
    complaintTitle: b.complaint_title || 'Road Issue',
    complaintDescription: b.complaint_description || '',
    complaintStatus: b.complaint_status || 'ASSIGNED',
    complaintSeverity: b.complaint_severity || 'MEDIUM',
    complaintAddress: b.complaint_address || 'Road Location',
    complaintCoordinates:
      b.complaint_latitude !== null && b.complaint_longitude !== null
        ? [b.complaint_latitude, b.complaint_longitude]
        : null,
    complaintPhotoUrl: b.complaint_photo_url,
  }
}

export const assignmentsService = {
  async list(statusFilter?: string, teamId?: string, search?: string): Promise<WorkOrder[]> {
    const params = new URLSearchParams()
    if (statusFilter && statusFilter !== 'ALL') params.set('status', statusFilter)
    if (teamId) params.set('team_id', teamId)
    if (search) params.set('search', search)

    const query = params.toString() ? `?${params.toString()}` : ''
    const response = await apiClient.get<BackendWorkOrder[]>(`/assignments${query}`)
    return response.data.map(mapWorkOrder)
  },

  async getStats(): Promise<WorkMonitoringStats> {
    const response = await apiClient.get<WorkMonitoringStats>('/assignments/stats')
    return response.data
  },

  async assignComplaint(
    complaintId: string,
    payload: {
      team_id: string
      priority?: string
      expected_completion_date?: string
      instructions?: string
      note?: string
    }
  ): Promise<WorkOrder> {
    const response = await apiClient.post<BackendWorkOrder>(
      `/assignments/complaints/${encodeURIComponent(complaintId)}`,
      payload
    )
    return mapWorkOrder(response.data)
  },

  async reassignWorkOrder(
    complaintId: string,
    payload: {
      team_id: string
      reason: string
      priority?: string
      expected_completion_date?: string
      instructions?: string
    }
  ): Promise<WorkOrder> {
    const response = await apiClient.post<BackendWorkOrder>(
      `/assignments/complaints/${encodeURIComponent(complaintId)}/reassign`,
      payload
    )
    return mapWorkOrder(response.data)
  },

  async releaseAssignment(complaintId: string, note?: string): Promise<void> {
    await apiClient.post(`/assignments/complaints/${encodeURIComponent(complaintId)}/release`, { note })
  },

  async getComplaintAssignments(complaintId: string): Promise<WorkOrder[]> {
    const response = await apiClient.get<{ items: BackendWorkOrder[] }>(
      `/assignments/complaints/${encodeURIComponent(complaintId)}`
    )
    return response.data.items.map(mapWorkOrder)
  },

  async verifyCompletion(
    assignmentId: string,
    payload: { approved: boolean; note?: string }
  ): Promise<WorkOrder> {
    const response = await apiClient.post<BackendWorkOrder>(
      `/assignments/${encodeURIComponent(assignmentId)}/verify`,
      payload
    )
    return mapWorkOrder(response.data)
  },
}
