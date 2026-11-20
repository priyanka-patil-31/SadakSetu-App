export type TeamAvailability = 'Available' | 'On job' | 'Off duty'

export type RepairTeam = {
  id: string
  name: string
  zone: string
  lead: string
  phone: string
  email: string
  availability: TeamAvailability
  members: number
  specialties: string[]
  assignedComplaints: string[]
  updatedAt: string
  hasAccount?: boolean
  leadUserId?: string | null
  currentLatitude?: number | null
  currentLongitude?: number | null
  lastLocationUpdate?: string | null
  currentLocationAddress?: string | null
}

export type TeamMember = {
  id: string
  teamId: string
  name: string
  employeeId: string
  phone: string | null
  skills: string[]
  isActive: boolean
}
