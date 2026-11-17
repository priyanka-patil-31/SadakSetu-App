import { apiClient } from '@/lib/http-client'
import type { RepairTeam, TeamAvailability, TeamMember } from '@/lib/teams-data'

type BackendAvailability = 'AVAILABLE' | 'ON_JOB' | 'OFF_DUTY'
type BackendTeam = {
  id: string
  name: string
  lead_name: string
  phone: string
  email: string
  zone: string
  members: number
  specialties: string[]
  availability: BackendAvailability
  lead_user_id?: string | null
  has_account?: boolean
  is_active: boolean
  created_at: string
  updated_at: string
  assigned_work_count?: number
}
type AssignedWork = { complaint_number: string }
type BackendMember = { id: string; team_id: string; name: string; employee_id: string; phone: string | null; skills: string[]; is_active: boolean }

const availabilityToLabel: Record<BackendAvailability, TeamAvailability> = { AVAILABLE: 'Available', ON_JOB: 'On job', OFF_DUTY: 'Off duty' }
const labelToAvailability: Record<TeamAvailability, BackendAvailability> = { Available: 'AVAILABLE', 'On job': 'ON_JOB', 'Off duty': 'OFF_DUTY' }

function mapTeam(team: BackendTeam, assignedComplaints: string[] = []): RepairTeam {
  return {
    id: team.id,
    name: team.name,
    zone: team.zone,
    lead: team.lead_name,
    phone: team.phone,
    email: team.email,
    availability: availabilityToLabel[team.availability] ?? 'Available',
    members: team.members,
    specialties: team.specialties ?? [],
    assignedComplaints,
    updatedAt: new Date(team.updated_at).toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' }),
    hasAccount: team.has_account ?? !!team.lead_user_id,
    leadUserId: team.lead_user_id ?? null,
  }
}

async function withAssignedWork(team: BackendTeam) {
  try {
    const response = await apiClient.get<AssignedWork[]>(`/teams/${encodeURIComponent(team.id)}/complaints`)
    return mapTeam(team, response.data.map((item) => item.complaint_number))
  } catch {
    return mapTeam(team, [])
  }
}

export const teamsService = {
  async list() {
    const response = await apiClient.get<{ items: BackendTeam[] }>('/teams?page=1&page_size=100')
    return Promise.all(response.data.items.map(withAssignedWork))
  },

  async create(payload: { name: string; lead: string; phone: string; email: string; zone: string; members: number; specialties: string[]; availability: TeamAvailability }) {
    const response = await apiClient.post<BackendTeam>('/teams', { name: payload.name, lead_name: payload.lead, phone: payload.phone, email: payload.email, zone: payload.zone, members: payload.members, specialties: payload.specialties, availability: labelToAvailability[payload.availability] })
    return mapTeam(response.data)
  },

  async update(id: string, payload: { name: string; lead: string; phone: string; email: string; zone: string; members: number; specialties: string[]; availability: TeamAvailability }) {
    const response = await apiClient.patch<BackendTeam>(`/teams/${encodeURIComponent(id)}`, { name: payload.name, lead_name: payload.lead, phone: payload.phone, email: payload.email, zone: payload.zone, members: payload.members, specialties: payload.specialties, availability: labelToAvailability[payload.availability] })
    return mapTeam(response.data)
  },

  async updateAvailability(id: string, availability: TeamAvailability) {
    const response = await apiClient.patch<BackendTeam>(`/teams/${encodeURIComponent(id)}/availability`, { availability: labelToAvailability[availability] })
    return mapTeam(response.data)
  },

  async remove(id: string) {
    await apiClient.delete(`/teams/${encodeURIComponent(id)}`)
  },

  async listMembers(teamId: string): Promise<TeamMember[]> {
    const response = await apiClient.get<BackendMember[]>(`/teams/${encodeURIComponent(teamId)}/members`)
    return response.data.map((member) => ({ id: member.id, teamId: member.team_id, name: member.name, employeeId: member.employee_id, phone: member.phone, skills: member.skills ?? [], isActive: member.is_active }))
  },

  async createMember(teamId: string, payload: { name: string; employeeId: string; phone?: string; skills: string[] }) {
    const response = await apiClient.post<BackendMember>(`/teams/${encodeURIComponent(teamId)}/members`, { name: payload.name, employee_id: payload.employeeId, phone: payload.phone || null, skills: payload.skills })
    const member = response.data
    return { id: member.id, teamId: member.team_id, name: member.name, employeeId: member.employee_id, phone: member.phone, skills: member.skills ?? [], isActive: member.is_active }
  },

  async updateMember(teamId: string, memberId: string, payload: { isActive: boolean }) {
    const response = await apiClient.patch<BackendMember>(`/teams/${encodeURIComponent(teamId)}/members/${encodeURIComponent(memberId)}`, payload)
    const member = response.data
    return { id: member.id, teamId: member.team_id, name: member.name, employeeId: member.employee_id, phone: member.phone, skills: member.skills ?? [], isActive: member.is_active }
  },

  async createLeaderAccount(teamId: string, payload: { full_name: string; email: string; phone: string; password: string }) {
    const response = await apiClient.post<BackendTeam>(`/teams/${encodeURIComponent(teamId)}/leader`, payload)
    return mapTeam(response.data)
  },

  async assignLeader(teamId: string, userId: string) {
    const response = await apiClient.post<BackendTeam>(`/teams/${encodeURIComponent(teamId)}/assign-leader`, { user_id: userId })
    return mapTeam(response.data)
  },

  async listAvailableLeaders(): Promise<{ id: string; email: string; full_name: string; phone: string | null; is_active: boolean }[]> {
    const response = await apiClient.get<{ id: string; email: string; full_name: string; phone: string | null; is_active: boolean }[]>('/teams/available-leaders')
    return response.data
  },

  async getWorkStats(teamId: string): Promise<{ active_assignments: number; completed_assignments: number; delayed_assignments: number; pending_assignments: number }> {
    const response = await apiClient.get<{ active_assignments: number; completed_assignments: number; delayed_assignments: number; pending_assignments: number }>(`/teams/${encodeURIComponent(teamId)}/work-stats`)
    return response.data
  },
}
