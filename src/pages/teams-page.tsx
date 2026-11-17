import { useEffect, useMemo, useState } from 'react'
import {
  AlertTriangle,
  Calendar,
  Check,
  CheckCircle2,
  ChevronRight,
  Clock,
  Eye,
  FileText,
  HardHat,
  KeyRound,
  Loader2,
  Mail,
  MapPin,
  Pencil,
  Phone,
  Plus,
  RefreshCw,
  Search,
  ShieldAlert,
  Trash2,
  UserCheck,
  UserPlus,
  UsersRound,
  X,
} from 'lucide-react'
import { Link, useSearchParams } from 'react-router-dom'
import { PageHeader } from '@/components/page-header'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { type RepairTeam, type TeamAvailability, type TeamMember } from '@/lib/teams-data'
import { cn, formatDate } from '@/lib/utils'
import { teamsService } from '@/services/teams-service'
import {
  assignmentsService,
  type WorkOrder,
  type WorkMonitoringStats,
} from '@/services/assignments-service'

const availabilityClasses: Record<TeamAvailability, string> = {
  Available: 'border-emerald-200 bg-emerald-50 text-emerald-700',
  'On job': 'border-sky-200 bg-sky-50 text-sky-700',
  'Off duty': 'border-slate-200 bg-slate-50 text-slate-600',
}

const workStatusClasses: Record<string, string> = {
  PENDING: 'border-slate-200 bg-slate-50 text-slate-700',
  ACCEPTED: 'border-sky-200 bg-sky-50 text-sky-700',
  IN_PROGRESS: 'border-blue-200 bg-blue-50 text-blue-700',
  DELAYED: 'border-red-200 bg-red-50 text-red-700',
  COMPLETION_SUBMITTED: 'border-amber-200 bg-amber-50 text-amber-700 animate-pulse',
  COMPLETED: 'border-emerald-200 bg-emerald-50 text-emerald-700',
}

const emptyForm = {
  name: '',
  zone: 'West Zone',
  lead: '',
  phone: '',
  email: '',
  availability: 'Available' as TeamAvailability,
  members: '4',
  specialties: '',
}

function AvailabilityBadge({ availability }: { availability: TeamAvailability }) {
  return (
    <Badge variant="outline" className={cn('font-medium', availabilityClasses[availability])}>
      <span className="mr-1.5 h-1.5 w-1.5 rounded-full bg-current" />
      {availability}
    </Badge>
  )
}

export function TeamsPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [activeTab, setActiveTab] = useState<'teams' | 'monitoring'>(
    searchParams.get('tab') === 'monitoring' ? 'monitoring' : 'teams'
  )

  const [teams, setTeams] = useState<RepairTeam[]>([])
  const [search, setSearch] = useState('')
  const [availabilityFilter, setAvailabilityFilter] = useState('All teams')
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [formOpen, setFormOpen] = useState(false)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [form, setForm] = useState(emptyForm)
  const [formError, setFormError] = useState('')
  const [confirmDeleteId, setConfirmDeleteId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [members, setMembers] = useState<TeamMember[]>([])
  const [memberForm, setMemberForm] = useState({ name: '', employeeId: '', phone: '', skills: '' })
  const [memberError, setMemberError] = useState('')
  const [memberSaving, setMemberSaving] = useState(false)

  // Team Leader Account Creation & Linking State
  const [createLeaderOpen, setCreateLeaderOpen] = useState(false)
  const [leaderForm, setLeaderForm] = useState({ fullName: '', email: '', phone: '', password: '' })
  const [leaderSaving, setLeaderSaving] = useState(false)
  const [leaderError, setLeaderError] = useState('')

  const [assignLeaderOpen, setAssignLeaderOpen] = useState(false)
  const [availableLeaders, setAvailableLeaders] = useState<{ id: string; email: string; full_name: string; phone: string | null }[]>([])
  const [selectedLeaderId, setSelectedLeaderId] = useState('')
  const [assignLeaderSaving, setAssignLeaderSaving] = useState(false)
  const [assignLeaderError, setAssignLeaderError] = useState('')

  // Team Work Stats for Selected Team
  const [teamWorkStats, setTeamWorkStats] = useState<{
    active_assignments: number
    completed_assignments: number
    delayed_assignments: number
    pending_assignments: number
  } | null>(null)

  // Work Monitoring State
  const [monitoringStatusFilter, setMonitoringStatusFilter] = useState('ALL')
  const [monitoringSearch, setMonitoringSearch] = useState('')
  const [monitoringTeamFilter, setMonitoringTeamFilter] = useState('ALL')
  const [workOrders, setWorkOrders] = useState<WorkOrder[]>([])
  const [workStats, setWorkStats] = useState<WorkMonitoringStats>({
    total: 0,
    pending: 0,
    ongoing: 0,
    delayed: 0,
    completion_submitted: 0,
    completed: 0,
  })
  const [monitoringLoading, setMonitoringLoading] = useState(false)

  // Inspection & Verification Modal
  const [inspectWorkOrder, setInspectWorkOrder] = useState<WorkOrder | null>(null)
  const [verificationNotes, setVerificationNotes] = useState('')
  const [verificationSaving, setVerificationSaving] = useState(false)
  const [verificationError, setVerificationError] = useState('')

  const selected = teams.find((team) => team.id === selectedId) ?? null

  useEffect(() => {
    if (!selectedId) {
      setMembers([])
      setTeamWorkStats(null)
      return
    }
    teamsService.listMembers(selectedId).then(setMembers).catch(() => setMembers([]))
    teamsService.getWorkStats(selectedId).then(setTeamWorkStats).catch(() => setTeamWorkStats(null))
  }, [selectedId])

  const addMember = async () => {
    if (!selectedId || !memberForm.name.trim() || !memberForm.employeeId.trim()) {
      setMemberError('Name and employee ID are required.')
      return
    }
    if (memberForm.phone && !/^\d{10}$/.test(memberForm.phone)) {
      setMemberError('Phone must contain exactly 10 digits.')
      return
    }
    setMemberSaving(true)
    setMemberError('')
    try {
      const member = await teamsService.createMember(selectedId, {
        name: memberForm.name.trim(),
        employeeId: memberForm.employeeId.trim(),
        phone: memberForm.phone,
        skills: memberForm.skills
          .split(',')
          .map((value) => value.trim())
          .filter(Boolean),
      })
      setMembers((current) => [...current, member].sort((a, b) => a.name.localeCompare(b.name)))
      setMemberForm({ name: '', employeeId: '', phone: '', skills: '' })
    } catch (reason: unknown) {
      setMemberError(reason instanceof Error ? reason.message : 'Unable to add team member.')
    } finally {
      setMemberSaving(false)
    }
  }

  const toggleMember = async (member: TeamMember) => {
    if (!selectedId) return
    setMemberSaving(true)
    try {
      const updated = await teamsService.updateMember(selectedId, member.id, { isActive: !member.isActive })
      setMembers((current) => current.map((item) => (item.id === updated.id ? updated : item)))
    } catch (reason: unknown) {
      setMemberError(reason instanceof Error ? reason.message : 'Unable to update team member.')
    } finally {
      setMemberSaving(false)
    }
  }

  const filtered = useMemo(() => {
    return teams.filter(
      (team) =>
        `${team.name} ${team.lead} ${team.zone}`
          .toLowerCase()
          .includes(search.toLowerCase()) &&
        (availabilityFilter === 'All teams' || team.availability === availabilityFilter)
    )
  }, [availabilityFilter, search, teams])

  useEffect(() => {
    let active = true
    teamsService
      .list()
      .then((items) => {
        if (active) setTeams(items)
      })
      .catch((reason: unknown) => {
        if (active)
          setFormError(
            reason instanceof Error ? reason.message : 'Unable to load repair teams.'
          )
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    // Also prefetch work monitoring stats
    assignmentsService
      .getStats()
      .then((s) => {
        if (active) setWorkStats(s)
      })
      .catch(() => {})

    return () => {
      active = false
    }
  }, [])

  // Load Work Monitoring data
  const loadMonitoringData = async () => {
    setMonitoringLoading(true)
    try {
      const [orders, stats] = await Promise.all([
        assignmentsService.list(
          monitoringStatusFilter !== 'ALL' ? monitoringStatusFilter : undefined,
          monitoringTeamFilter !== 'ALL' ? monitoringTeamFilter : undefined,
          monitoringSearch.trim() || undefined
        ),
        assignmentsService.getStats(),
      ])
      setWorkOrders(orders)
      setWorkStats(stats)
    } catch {
      setWorkOrders([])
    } finally {
      setMonitoringLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === 'monitoring') {
      loadMonitoringData()
    }
  }, [activeTab, monitoringStatusFilter, monitoringTeamFilter, monitoringSearch])

  const openAdd = () => {
    setEditingId(null)
    setForm(emptyForm)
    setFormError('')
    setFormOpen(true)
  }

  const openEdit = (team: RepairTeam) => {
    setEditingId(team.id)
    setForm({
      name: team.name,
      zone: team.zone,
      lead: team.lead,
      phone: team.phone,
      email: team.email,
      availability: team.availability,
      members: String(team.members),
      specialties: team.specialties.join(', '),
    })
    setFormError('')
    setFormOpen(true)
  }

  const updateForm = (key: keyof typeof emptyForm, value: string) =>
    setForm((current) => ({ ...current, [key]: value }))

  const saveTeam = async () => {
    if (
      !form.name.trim() ||
      !form.lead.trim() ||
      !form.phone.trim() ||
      !form.email.trim()
    ) {
      setFormError('Team name, lead, phone, and email are required.')
      return
    }
    if (!/^\d{10}$/.test(form.phone)) {
      setFormError('Team phone must contain exactly 10 digits.')
      return
    }
    const details = {
      name: form.name.trim(),
      zone: form.zone,
      lead: form.lead.trim(),
      phone: form.phone.trim(),
      email: form.email.trim(),
      availability: form.availability,
      members: Math.max(1, Number(form.members) || 1),
      specialties: form.specialties
        .split(',')
        .map((value) => value.trim())
        .filter(Boolean),
    }
    setSaving(true)
    try {
      const saved = editingId
        ? await teamsService.update(editingId, details)
        : await teamsService.create(details)
      if (editingId) {
        setTeams((current) =>
          current.map((team) => (team.id === editingId ? { ...team, ...saved } : team))
        )
      } else {
        setTeams((current) => [...current, saved])
        setSelectedId(saved.id)
      }
      setFormOpen(false)
    } catch (reason: unknown) {
      setFormError(
        reason instanceof Error ? reason.message : 'Unable to save repair team.'
      )
    } finally {
      setSaving(false)
    }
  }

  const deleteTeam = async (id: string) => {
    setSaving(true)
    setFormError('')
    try {
      await teamsService.remove(id)
      setTeams((current) => current.filter((team) => team.id !== id))
      if (selectedId === id) setSelectedId(null)
      setConfirmDeleteId(null)
    } catch (reason: unknown) {
      setFormError(
        reason instanceof Error ? reason.message : 'Unable to delete repair team.'
      )
    } finally {
      setSaving(false)
    }
  }

  const updateAvailability = async (availability: TeamAvailability) => {
    if (!selected) return
    setSaving(true)
    try {
      const saved = await teamsService.updateAvailability(selected.id, availability)
      setTeams((current) =>
        current.map((team) =>
          team.id === selected.id
            ? { ...team, ...saved, assignedComplaints: team.assignedComplaints }
            : team
        )
      )
    } catch (reason: unknown) {
      setFormError(
        reason instanceof Error ? reason.message : 'Unable to update team availability.'
      )
    } finally {
      setSaving(false)
    }
  }

  // Team Leader Account Handlers
  const openCreateLeader = (team: RepairTeam) => {
    setLeaderForm({
      fullName: team.lead,
      email: team.email,
      phone: team.phone,
      password: '',
    })
    setLeaderError('')
    setCreateLeaderOpen(true)
  }

  const handleCreateLeaderSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedId || !leaderForm.email || !leaderForm.password) {
      setLeaderError('Email and password are required.')
      return
    }
    if (leaderForm.password.length < 6) {
      setLeaderError('Password must be at least 6 characters.')
      return
    }
    setLeaderSaving(true)
    setLeaderError('')
    try {
      const updated = await teamsService.createLeaderAccount(selectedId, {
        full_name: leaderForm.fullName.trim(),
        email: leaderForm.email.trim(),
        phone: leaderForm.phone.trim(),
        password: leaderForm.password,
      })
      setTeams((current) => current.map((t) => (t.id === updated.id ? { ...t, ...updated } : t)))
      setCreateLeaderOpen(false)
    } catch (err) {
      setLeaderError(err instanceof Error ? err.message : 'Failed to create team leader account.')
    } finally {
      setLeaderSaving(false)
    }
  }

  const openAssignLeader = async (team: RepairTeam) => {
    setAssignLeaderError('')
    setSelectedLeaderId('')
    try {
      const available = await teamsService.listAvailableLeaders()
      setAvailableLeaders(available)
      if (available.length > 0) setSelectedLeaderId(available[0].id)
    } catch {
      setAvailableLeaders([])
    }
    setAssignLeaderOpen(true)
  }

  const handleAssignLeaderSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!selectedId || !selectedLeaderId) {
      setAssignLeaderError('Please select a team leader.')
      return
    }
    setAssignLeaderSaving(true)
    setAssignLeaderError('')
    try {
      const updated = await teamsService.assignLeader(selectedId, selectedLeaderId)
      setTeams((current) => current.map((t) => (t.id === updated.id ? { ...t, ...updated } : t)))
      setAssignLeaderOpen(false)
    } catch (err) {
      setAssignLeaderError(err instanceof Error ? err.message : 'Failed to assign team leader.')
    } finally {
      setAssignLeaderSaving(false)
    }
  }

  // Work Order Verification Handler
  const handleVerify = async (approved: boolean) => {
    if (!inspectWorkOrder) return
    setVerificationSaving(true)
    setVerificationError('')
    try {
      const updated = await assignmentsService.verifyCompletion(inspectWorkOrder.id, {
        approved,
        note: verificationNotes.trim() || undefined,
      })
      setInspectWorkOrder(updated)
      setVerificationNotes('')
      // refresh monitoring and teams list
      loadMonitoringData()
      const updatedTeams = await teamsService.list()
      setTeams(updatedTeams)
    } catch (err) {
      setVerificationError(err instanceof Error ? err.message : 'Verification action failed')
    } finally {
      setVerificationSaving(false)
    }
  }

  return (
    <div>
      <PageHeader
        eyebrow="Field operations"
        title="Repair teams & work monitoring"
        description="Coordinate repair crews, create leader accounts, dispatch jobs, and audit field completion evidence."
        action={
          <div className="flex items-center gap-2">
            {activeTab === 'teams' ? (
              <Button
                onClick={openAdd}
                className="gap-2 bg-orange-500 hover:bg-orange-600 text-white font-semibold text-xs"
              >
                <Plus className="h-4 w-4" />
                Add team
              </Button>
            ) : (
              <Button
                onClick={loadMonitoringData}
                variant="outline"
                size="sm"
                className="gap-1.5 text-xs text-slate-700"
              >
                <RefreshCw className={cn('h-3.5 w-3.5', monitoringLoading && 'animate-spin')} />
                Refresh Audits
              </Button>
            )}
          </div>
        }
      />

      {/* Module Navigation Tabs */}
      <div className="mb-6 flex border-b border-slate-200">
        <button
          type="button"
          onClick={() => {
            setActiveTab('teams')
            setSearchParams({})
          }}
          className={cn(
            'flex items-center gap-2 border-b-2 px-5 py-3 text-sm font-bold transition-colors cursor-pointer',
            activeTab === 'teams'
              ? 'border-orange-500 text-orange-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          )}
        >
          <UsersRound className="h-4 w-4" />
          <span>Repair Teams & Crews</span>
          <span className="ml-1.5 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600 font-semibold">
            {teams.length}
          </span>
        </button>

        <button
          type="button"
          onClick={() => {
            setActiveTab('monitoring')
            setSearchParams({ tab: 'monitoring' })
          }}
          className={cn(
            'flex items-center gap-2 border-b-2 px-5 py-3 text-sm font-bold transition-colors cursor-pointer',
            activeTab === 'monitoring'
              ? 'border-orange-500 text-orange-600'
              : 'border-transparent text-slate-500 hover:text-slate-800'
          )}
        >
          <HardHat className="h-4 w-4" />
          <span>Work Monitoring & Field Audits</span>
          {workStats.completion_submitted > 0 && (
            <span className="ml-1.5 rounded-full bg-amber-500 px-2 py-0.5 text-xs text-white font-bold animate-pulse">
              {workStats.completion_submitted} Review
            </span>
          )}
        </button>
      </div>

      {loading && <p className="mb-4 text-sm text-muted-foreground">Loading repair teams…</p>}
      {formError && !formOpen && (
        <div
          role="alert"
          className="mb-4 rounded-xl border border-red-200 bg-red-50 p-4 text-xs font-semibold text-red-800"
        >
          {formError}
        </div>
      )}

      {/* ============================================================== */}
      {/* TAB 1: REPAIR TEAMS MANAGEMENT                                 */}
      {/* ============================================================== */}
      {activeTab === 'teams' && (
        <>
          {/* Stats summary */}
          <div className="mb-6 grid gap-4 sm:grid-cols-3">
            <Card>
              <CardContent className="flex items-center gap-4 p-5">
                <div className="rounded-xl bg-sky-50 p-3 text-sky-600">
                  <UsersRound className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">{teams.length}</p>
                  <p className="text-xs text-muted-foreground">Total teams</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="flex items-center gap-4 p-5">
                <div className="rounded-xl bg-emerald-50 p-3 text-emerald-600">
                  <Check className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {teams.filter((team) => team.availability === 'Available').length}
                  </p>
                  <p className="text-xs text-muted-foreground">Available now</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="flex items-center gap-4 p-5">
                <div className="rounded-xl bg-orange-50 p-3 text-orange-600">
                  <MapPin className="h-5 w-5" />
                </div>
                <div>
                  <p className="text-2xl font-bold">
                    {teams.reduce((total, team) => total + team.assignedComplaints.length, 0)}
                  </p>
                  <p className="text-xs text-muted-foreground">Active work orders</p>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Teams List */}
          <Card>
            <CardContent className="p-0">
              <div className="flex flex-col gap-3 border-b p-4 md:flex-row md:items-center md:justify-between">
                <Input
                  aria-label="Search repair teams"
                  value={search}
                  onChange={(event) => setSearch(event.target.value)}
                  placeholder="Search teams, leads, or zones..."
                  className="md:max-w-sm"
                />
                <select
                  aria-label="Team availability filter"
                  value={availabilityFilter}
                  onChange={(event) => setAvailabilityFilter(event.target.value)}
                  className="h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none"
                >
                  <option>All teams</option>
                  <option>Available</option>
                  <option>On job</option>
                  <option>Off duty</option>
                </select>
              </div>

              <div className="divide-y">
                {filtered.map((team) => (
                  <div
                    key={team.id}
                    className="flex flex-col gap-4 p-5 transition-colors hover:bg-slate-50/70 lg:flex-row lg:items-center"
                  >
                    <button
                      type="button"
                      className="flex min-w-0 flex-1 items-center gap-4 text-left cursor-pointer"
                      aria-label={`View ${team.name}`}
                      onClick={() => {
                        setSelectedId(team.id)
                      }}
                    >
                      <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-[#15213d] text-sm font-bold text-white shadow-xs">
                        {team.name.replace('Team ', '').slice(0, 2).toUpperCase()}
                      </div>
                      <div className="min-w-0">
                        <div className="flex items-center gap-2">
                          <p className="truncate font-semibold text-slate-800">{team.name}</p>
                          {team.hasAccount ? (
                            <Badge variant="outline" className="border-emerald-200 bg-emerald-50 text-emerald-700 text-[10px] py-0">
                              App Login Active
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="border-amber-200 bg-amber-50 text-amber-700 text-[10px] py-0">
                              No App Account
                            </Badge>
                          )}
                        </div>
                        <p className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
                          <MapPin className="h-3 w-3" />
                          {team.zone} · {team.members} members · Lead: {team.lead}
                        </p>
                      </div>
                    </button>

                    <div className="flex flex-wrap items-center gap-3 lg:justify-end">
                      <AvailabilityBadge availability={team.availability} />
                      <span className="text-xs text-muted-foreground font-medium">
                        {team.assignedComplaints.length} work orders
                      </span>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Edit ${team.name}`}
                        title="Edit team"
                        onClick={() => openEdit(team)}
                      >
                        <Pencil className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        aria-label={`Delete ${team.name}`}
                        title="Delete team"
                        className="text-slate-400 hover:text-red-600"
                        onClick={() => setConfirmDeleteId(team.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                      <ChevronRight className="hidden h-4 w-4 text-slate-400 lg:block" />
                    </div>
                  </div>
                ))}

                {filtered.length === 0 && (
                  <div className="p-12 text-center text-sm text-muted-foreground">
                    No repair teams match the current filters.
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* ============================================================== */}
      {/* TAB 2: WORK MONITORING SECTION                                 */}
      {/* ============================================================== */}
      {activeTab === 'monitoring' && (
        <div className="space-y-6">
          {/* Work Monitoring KPI Summary Cards */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-6">
            <Card className="cursor-pointer hover:border-slate-400 transition-colors" onClick={() => setMonitoringStatusFilter('ALL')}>
              <CardContent className="p-4">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Total Work Orders</span>
                <p className="text-2xl font-bold text-slate-900 mt-1">{workStats.total}</p>
                <span className="text-[10px] text-muted-foreground">All assignments</span>
              </CardContent>
            </Card>

            <Card className="cursor-pointer hover:border-sky-400 transition-colors" onClick={() => setMonitoringStatusFilter('PENDING')}>
              <CardContent className="p-4">
                <span className="text-[10px] uppercase font-bold text-sky-600 block">Pending Acceptance</span>
                <p className="text-2xl font-bold text-sky-700 mt-1">{workStats.pending}</p>
                <span className="text-[10px] text-muted-foreground">Dispatched to crew</span>
              </CardContent>
            </Card>

            <Card className="cursor-pointer hover:border-blue-400 transition-colors" onClick={() => setMonitoringStatusFilter('IN_PROGRESS')}>
              <CardContent className="p-4">
                <span className="text-[10px] uppercase font-bold text-blue-600 block">Ongoing Repairs</span>
                <p className="text-2xl font-bold text-blue-700 mt-1">{workStats.ongoing}</p>
                <span className="text-[10px] text-muted-foreground">Active in field</span>
              </CardContent>
            </Card>

            <Card className="cursor-pointer hover:border-red-400 transition-colors" onClick={() => setMonitoringStatusFilter('DELAYED')}>
              <CardContent className="p-4">
                <span className="text-[10px] uppercase font-bold text-red-600 block">Delayed Work</span>
                <p className="text-2xl font-bold text-red-700 mt-1">{workStats.delayed}</p>
                <span className="text-[10px] text-muted-foreground">Delay flag reported</span>
              </CardContent>
            </Card>

            <Card className={cn('cursor-pointer transition-colors', workStats.completion_submitted > 0 ? 'border-amber-300 bg-amber-50/40 hover:border-amber-500' : 'hover:border-amber-400')} onClick={() => setMonitoringStatusFilter('COMPLETION_SUBMITTED')}>
              <CardContent className="p-4">
                <span className="text-[10px] uppercase font-bold text-amber-700 block">Awaiting Review</span>
                <p className="text-2xl font-bold text-amber-700 mt-1">{workStats.completion_submitted}</p>
                <span className="text-[10px] text-amber-800 font-semibold">Evidence uploaded</span>
              </CardContent>
            </Card>

            <Card className="cursor-pointer hover:border-emerald-400 transition-colors" onClick={() => setMonitoringStatusFilter('COMPLETED')}>
              <CardContent className="p-4">
                <span className="text-[10px] uppercase font-bold text-emerald-600 block">Completed</span>
                <p className="text-2xl font-bold text-emerald-700 mt-1">{workStats.completed}</p>
                <span className="text-[10px] text-muted-foreground">Verified & resolved</span>
              </CardContent>
            </Card>
          </div>

          {/* Filtering Toolbar */}
          <Card>
            <CardContent className="p-4 space-y-3">
              <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                <div className="relative flex-1 md:max-w-md">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    placeholder="Search work order #, complaint, locality, or team..."
                    value={monitoringSearch}
                    onChange={(e) => setMonitoringSearch(e.target.value)}
                    className="pl-9"
                  />
                </div>

                <div className="flex items-center gap-2">
                  <select
                    value={monitoringTeamFilter}
                    onChange={(e) => setMonitoringTeamFilter(e.target.value)}
                    className="h-10 rounded-lg border border-input bg-background px-3 text-xs outline-none"
                  >
                    <option value="ALL">All Repair Teams</option>
                    {teams.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name} ({t.zone})
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              {/* Status Pills */}
              <div className="flex flex-wrap items-center gap-1.5 border-t pt-3 text-xs">
                <span className="text-[11px] font-bold text-slate-400 mr-2 uppercase">Status Filter:</span>
                {[
                  { key: 'ALL', label: 'All Orders' },
                  { key: 'PENDING', label: 'Pending Acceptance' },
                  { key: 'IN_PROGRESS', label: 'Ongoing Repairs' },
                  { key: 'DELAYED', label: 'Delayed Work' },
                  { key: 'COMPLETION_SUBMITTED', label: 'Completion Submitted' },
                  { key: 'COMPLETED', label: 'Completed & Verified' },
                ].map((tab) => (
                  <button
                    key={tab.key}
                    type="button"
                    onClick={() => setMonitoringStatusFilter(tab.key)}
                    className={cn(
                      'rounded-lg px-2.5 py-1 font-semibold transition-colors cursor-pointer',
                      monitoringStatusFilter === tab.key
                        ? 'bg-orange-500 text-white shadow-2xs'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    )}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Work Orders List */}
          <div className="space-y-3">
            {monitoringLoading ? (
              <div className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-white p-12 text-sm text-muted-foreground">
                <Loader2 className="h-5 w-5 animate-spin text-orange-500" />
                <span>Loading work orders and field monitoring logs…</span>
              </div>
            ) : workOrders.length === 0 ? (
              <div className="rounded-xl border border-dashed border-slate-300 bg-white p-12 text-center text-sm text-muted-foreground">
                No work orders found for the selected criteria.
              </div>
            ) : (
              workOrders.map((wo) => {
                const isOverdue =
                  wo.expectedCompletionDate &&
                  new Date(wo.expectedCompletionDate) < new Date() &&
                  wo.workStatus !== 'COMPLETED'

                return (
                  <div
                    key={wo.id}
                    className="flex flex-col justify-between gap-4 rounded-xl border border-slate-200 bg-white p-5 shadow-2xs hover:border-orange-300 transition-all lg:flex-row lg:items-center"
                  >
                    <div className="flex min-w-0 flex-1 items-start gap-4">
                      <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
                        <HardHat className="h-6 w-6" />
                      </div>
                      <div className="min-w-0 space-y-1">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="font-mono text-xs font-bold text-orange-600">
                            {wo.workOrderNumber}
                          </span>
                          <span className="text-xs text-slate-400">·</span>
                          <span className="font-mono text-xs font-semibold text-slate-500">
                            {wo.complaintNumber}
                          </span>
                          <Badge
                            variant="outline"
                            className={cn('text-[10px] font-bold', workStatusClasses[wo.workStatus] || 'bg-slate-50 text-slate-700')}
                          >
                            {wo.workStatus.replace('_', ' ')}
                          </Badge>
                          <Badge
                            variant="outline"
                            className={`text-[10px] font-bold ${
                              wo.priority === 'CRITICAL'
                                ? 'border-red-200 bg-red-50 text-red-700'
                                : wo.priority === 'HIGH'
                                ? 'border-orange-200 bg-orange-50 text-orange-700'
                                : 'border-slate-200 bg-slate-50 text-slate-700'
                            }`}
                          >
                            {wo.priority}
                          </Badge>
                          {isOverdue && (
                            <Badge variant="destructive" className="text-[10px] font-bold">
                              OVERDUE
                            </Badge>
                          )}
                        </div>

                        <p className="font-semibold text-slate-900 text-sm truncate">
                          {wo.complaintTitle}
                        </p>
                        <p className="flex items-center gap-1.5 text-xs text-muted-foreground truncate">
                          <MapPin className="h-3 w-3 text-orange-500 shrink-0" />
                          <span>{wo.complaintAddress}</span>
                        </p>

                        <div className="flex flex-wrap items-center gap-3 pt-1 text-xs text-slate-600">
                          <span>
                            Assigned to: <strong className="text-slate-800">{wo.teamName}</strong> (Lead: {wo.teamLeadName})
                          </span>
                          <span>·</span>
                          <span>
                            Target:{' '}
                            <strong className={cn(isOverdue ? 'text-red-600 font-bold' : 'text-slate-800')}>
                              {wo.expectedCompletionDate ? formatDate(wo.expectedCompletionDate) : 'No target'}
                            </strong>
                          </span>
                        </div>

                        {/* Progress Bar */}
                        <div className="pt-2 max-w-md">
                          <div className="flex items-center justify-between text-[11px] font-semibold text-slate-600 mb-1">
                            <span>Field Progress</span>
                            <span>{wo.progressPercentage}%</span>
                          </div>
                          <div className="h-1.5 w-full rounded-full bg-slate-100 overflow-hidden">
                            <div
                              className="h-full bg-gradient-to-r from-orange-500 to-emerald-500 transition-all duration-300"
                              style={{ width: `${Math.min(100, Math.max(0, wo.progressPercentage))}%` }}
                            />
                          </div>
                        </div>

                        {wo.delayReason && (
                          <div className="mt-2 flex items-center gap-1.5 rounded-md bg-red-50 px-2.5 py-1 text-xs text-red-700">
                            <AlertTriangle className="h-3.5 w-3.5 shrink-0" />
                            <span>Delay: {wo.delayReason}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    <div className="flex shrink-0 items-center gap-2">
                      <Button
                        variant={wo.workStatus === 'COMPLETION_SUBMITTED' ? 'default' : 'outline'}
                        size="sm"
                        className={cn(
                          'gap-1.5 text-xs font-semibold',
                          wo.workStatus === 'COMPLETION_SUBMITTED'
                            ? 'bg-amber-600 hover:bg-amber-700 text-white'
                            : 'border-slate-200 text-slate-700'
                        )}
                        onClick={() => {
                          setInspectWorkOrder(wo)
                          setVerificationNotes('')
                          setVerificationError('')
                        }}
                      >
                        <Eye className="h-3.5 w-3.5" />
                        {wo.workStatus === 'COMPLETION_SUBMITTED' ? 'Verify Completion' : 'Inspect Work Order'}
                      </Button>
                    </div>
                  </div>
                )
              })
            )}
          </div>
        </div>
      )}

      {/* ============================================================== */}
      {/* MODAL: WORK ORDER INSPECTION & COMPLETION VERIFICATION         */}
      {/* ============================================================== */}
      {inspectWorkOrder && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4"
          onClick={() => setInspectWorkOrder(null)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label={`Work order inspection ${inspectWorkOrder.workOrderNumber}`}
            className="max-h-[92vh] w-full max-w-3xl overflow-y-auto rounded-2xl bg-white shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b p-6 pb-4">
              <div className="flex items-center gap-3">
                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
                  <HardHat className="h-6 w-6" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-xl font-bold text-slate-900">
                      {inspectWorkOrder.workOrderNumber}
                    </h3>
                    <Badge
                      variant="outline"
                      className={cn('text-xs font-bold', workStatusClasses[inspectWorkOrder.workStatus])}
                    >
                      {inspectWorkOrder.workStatus.replace('_', ' ')}
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground mt-0.5">
                    Original Citizen Complaint: {inspectWorkOrder.complaintNumber}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setInspectWorkOrder(null)}
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <div className="p-6 pt-0 space-y-6">
              {/* Top metadata grid */}
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-4 rounded-xl border bg-slate-50 p-4 text-xs">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Assigned Crew</span>
                  <p className="font-semibold text-slate-800">{inspectWorkOrder.teamName}</p>
                  <p className="text-muted-foreground">{inspectWorkOrder.teamLeadName}</p>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Priority</span>
                  <p className="font-semibold text-slate-800">{inspectWorkOrder.priority}</p>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Target Deadline</span>
                  <p className="font-semibold text-slate-800">
                    {inspectWorkOrder.expectedCompletionDate ? formatDate(inspectWorkOrder.expectedCompletionDate) : 'None'}
                  </p>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Progress</span>
                  <p className="font-bold text-orange-600 text-sm">{inspectWorkOrder.progressPercentage}%</p>
                </div>
              </div>

              {/* Complaint summary */}
              <div className="rounded-xl border border-slate-200 p-4 space-y-2">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Citizen Complaint Details
                </p>
                <h4 className="font-bold text-slate-900 text-sm">
                  {inspectWorkOrder.complaintTitle}
                </h4>
                <p className="text-xs text-slate-600 leading-relaxed">
                  {inspectWorkOrder.complaintDescription}
                </p>
                <p className="flex items-center gap-1.5 text-xs text-slate-700 font-medium pt-1">
                  <MapPin className="h-3.5 w-3.5 text-orange-500" />
                  {inspectWorkOrder.complaintAddress}
                </p>
              </div>

              {/* Citizen photo */}
              {inspectWorkOrder.complaintPhotoUrl && (
                <div className="rounded-xl border border-slate-200 p-4 space-y-2">
                  <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                    Citizen Initial Report Photo
                  </p>
                  <img
                    src={inspectWorkOrder.complaintPhotoUrl}
                    alt="Citizen road report"
                    className="max-h-56 w-full rounded-lg object-cover"
                  />
                </div>
              )}

              {/* Field Progress & Notes */}
              <div className="space-y-3">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Field Team Progress & Notes
                </p>
                <div className="rounded-lg bg-slate-50 p-3 text-xs space-y-2 border">
                  {inspectWorkOrder.progressNotes ? (
                    <p className="text-slate-800 italic">“{inspectWorkOrder.progressNotes}”</p>
                  ) : (
                    <p className="text-muted-foreground">No custom progress notes reported yet.</p>
                  )}
                  {inspectWorkOrder.delayReason && (
                    <div className="rounded-md border border-red-200 bg-red-50 p-2 text-xs text-red-800">
                      <strong>Delay Flag:</strong> {inspectWorkOrder.delayReason}
                    </div>
                  )}
                  {inspectWorkOrder.completionNotes && (
                    <div className="rounded-md border border-amber-200 bg-amber-50 p-2 text-xs text-amber-900">
                      <strong>Completion Notes:</strong> {inspectWorkOrder.completionNotes}
                    </div>
                  )}
                </div>
              </div>

              {/* Before and After Photos */}
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-xl border border-slate-200 p-3 space-y-2">
                  <p className="text-xs font-bold text-slate-700">Before Repair Evidence</p>
                  {inspectWorkOrder.beforePhotos.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2">
                      {inspectWorkOrder.beforePhotos.map((url, i) => (
                        <img
                          key={i}
                          src={url}
                          alt="Before repair"
                          className="h-28 w-full rounded-lg object-cover border"
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground py-4 text-center bg-slate-50 rounded-lg">
                      No before photos uploaded.
                    </p>
                  )}
                </div>

                <div className="rounded-xl border border-slate-200 p-3 space-y-2">
                  <p className="text-xs font-bold text-slate-700">After Repair Evidence</p>
                  {inspectWorkOrder.afterPhotos.length > 0 ? (
                    <div className="grid grid-cols-2 gap-2">
                      {inspectWorkOrder.afterPhotos.map((url, i) => (
                        <img
                          key={i}
                          src={url}
                          alt="After repair"
                          className="h-28 w-full rounded-lg object-cover border"
                        />
                      ))}
                    </div>
                  ) : (
                    <p className="text-xs text-muted-foreground py-4 text-center bg-slate-50 rounded-lg">
                      No after photos uploaded.
                    </p>
                  )}
                </div>
              </div>

              {/* Admin Verification Action Section (when submitted or reviewing) */}
              <div className="rounded-xl border border-orange-200 bg-orange-50/40 p-4 space-y-3">
                <p className="text-xs font-bold uppercase tracking-wider text-orange-900">
                  Administrator Quality Verification
                </p>

                {inspectWorkOrder.workStatus === 'COMPLETED' ? (
                  <div className="flex items-center gap-2 rounded-lg bg-emerald-100 p-3 text-xs text-emerald-800 font-medium">
                    <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                    <span>This work order has been verified and approved. The citizen complaint is marked RESOLVED.</span>
                  </div>
                ) : (
                  <>
                    <p className="text-xs text-slate-600 leading-relaxed">
                      Verify field photos and progress. Approving will automatically update the citizen complaint to <strong>RESOLVED</strong>.
                    </p>

                    <div>
                      <label className="text-[11px] font-bold uppercase text-slate-600 block mb-1">
                        Verification & Quality Feedback Notes
                      </label>
                      <textarea
                        value={verificationNotes}
                        onChange={(e) => setVerificationNotes(e.target.value)}
                        placeholder="Enter quality audit comments, asphalt density checks, or rework instructions..."
                        className="w-full min-h-16 rounded-lg border border-input bg-white p-2.5 text-xs outline-none focus:ring-2 focus:ring-orange-500"
                      />
                    </div>

                    {verificationError && (
                      <p className="text-xs font-semibold text-red-700">{verificationError}</p>
                    )}

                    <div className="flex flex-wrap items-center justify-end gap-2 pt-1">
                      <Button
                        type="button"
                        variant="outline"
                        size="sm"
                        disabled={verificationSaving}
                        className="border-amber-300 text-amber-800 hover:bg-amber-100 text-xs font-semibold"
                        onClick={() => handleVerify(false)}
                      >
                        Request Crew Rework
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        disabled={verificationSaving}
                        className="bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold gap-1.5"
                        onClick={() => handleVerify(true)}
                      >
                        <Check className="h-4 w-4" />
                        {verificationSaving ? 'Verifying…' : 'Approve & Mark Resolved'}
                      </Button>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Delete Team Modal Confirmation */}
      {confirmDeleteId && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
          onClick={() => setConfirmDeleteId(null)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Confirm team deletion"
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-red-50 text-red-600">
              <Trash2 className="h-6 w-6" />
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-900">Delete Repair Team?</h3>
              <p className="mt-1.5 text-xs leading-relaxed text-slate-500">
                Are you sure you want to remove this repair crew from the system? Teams
                with assigned complaints cannot be deleted until work orders are reassigned.
              </p>
            </div>
            <div className="flex justify-end gap-2.5 pt-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setConfirmDeleteId(null)}
              >
                Cancel
              </Button>
              <Button
                variant="destructive"
                size="sm"
                disabled={saving}
                onClick={() => deleteTeam(confirmDeleteId)}
              >
                {saving ? 'Deleting…' : 'Delete Team'}
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Team Details Drawer */}
      {selected && (
        <div
          className="fixed inset-0 z-40 flex justify-end bg-slate-950/40"
          onClick={() => setSelectedId(null)}
        >
          <aside
            role="dialog"
            aria-modal="true"
            aria-label={`${selected.name} details`}
            className="flex h-full w-full max-w-lg flex-col overflow-y-auto bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b px-6 py-5">
              <div>
                <p className="text-xs font-bold uppercase tracking-[0.16em] text-orange-500">
                  {selected.id}
                </p>
                <h2 className="mt-2 text-xl font-bold text-slate-900">{selected.name}</h2>
                <p className="mt-1 text-sm text-muted-foreground">{selected.zone}</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setSelectedId(null)}
                aria-label="Close team details"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <div className="space-y-6 p-6">
              <div className="flex items-center justify-between">
                <AvailabilityBadge availability={selected.availability} />
                <span className="text-xs text-muted-foreground">{selected.updatedAt}</span>
              </div>

              {/* Team Leader Account Status Card */}
              {selected.hasAccount ? (
                <div className="rounded-xl border border-emerald-200 bg-emerald-50/60 p-4 space-y-2.5">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-emerald-800">
                      <KeyRound className="h-4 w-4 text-emerald-600" />
                      Team Leader App Login
                    </span>
                    <Badge variant="outline" className="border-emerald-300 bg-emerald-100 text-emerald-800 text-[10px]">
                      Active & Linked
                    </Badge>
                  </div>
                  <p className="text-xs text-emerald-900 leading-relaxed">
                    This leader has active login credentials for the SadakSetu Android App.
                  </p>
                  <div className="rounded-lg bg-white/80 p-2 text-xs text-slate-700">
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Login Email</span>
                    <span className="font-semibold text-slate-900">{selected.email}</span>
                  </div>
                </div>
              ) : (
                <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-amber-800">
                      <KeyRound className="h-4 w-4 text-amber-600" />
                      Team Leader App Login
                    </span>
                    <Badge variant="outline" className="border-amber-300 bg-amber-100 text-amber-800 text-[10px]">
                      No Account Linked
                    </Badge>
                  </div>
                  <p className="text-xs text-amber-900 leading-relaxed">
                    This leader cannot log in to the Android mobile app until an account is created or linked.
                  </p>
                  <div className="flex flex-wrap gap-2 pt-1">
                    <Button
                      size="sm"
                      className="gap-1.5 bg-orange-500 hover:bg-orange-600 text-white text-xs font-semibold"
                      onClick={() => openCreateLeader(selected)}
                    >
                      <UserPlus className="h-3.5 w-3.5" />
                      Create Account
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="gap-1.5 border-slate-300 text-slate-700 hover:bg-slate-100 text-xs font-semibold"
                      onClick={() => openAssignLeader(selected)}
                    >
                      <UserCheck className="h-3.5 w-3.5" />
                      Link Existing
                    </Button>
                  </div>
                </div>
              )}

              {/* Workload Stats */}
              <div className="rounded-xl border bg-slate-50 p-4">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">
                  Team Workload & Assignments
                </p>
                <div className="grid grid-cols-2 gap-2 text-center text-xs sm:grid-cols-4">
                  <div className="rounded-lg bg-white p-2.5 border border-slate-200">
                    <span className="text-lg font-bold text-slate-800 block">
                      {teamWorkStats?.active_assignments ?? selected.assignedComplaints.length}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-slate-400">Active</span>
                  </div>
                  <div className="rounded-lg bg-white p-2.5 border border-slate-200">
                    <span className="text-lg font-bold text-sky-600 block">
                      {teamWorkStats?.pending_assignments ?? 0}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-slate-400">Pending</span>
                  </div>
                  <div className="rounded-lg bg-white p-2.5 border border-slate-200">
                    <span className="text-lg font-bold text-red-600 block">
                      {teamWorkStats?.delayed_assignments ?? 0}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-slate-400">Delayed</span>
                  </div>
                  <div className="rounded-lg bg-white p-2.5 border border-slate-200">
                    <span className="text-lg font-bold text-emerald-600 block">
                      {teamWorkStats?.completed_assignments ?? 0}
                    </span>
                    <span className="text-[10px] uppercase font-bold text-slate-400">Completed</span>
                  </div>
                </div>
              </div>

              {/* Contact Information */}
              <div className="rounded-xl border bg-slate-50 p-4">
                <p className="text-xs font-bold uppercase tracking-wider text-slate-500">
                  Contact information
                </p>
                <div className="mt-4 space-y-3">
                  <p className="flex items-center gap-3 text-sm font-medium text-slate-800">
                    <UsersRound className="h-4 w-4 text-slate-400" />
                    {selected.lead} · {selected.members} members
                  </p>
                  <p className="flex items-center gap-3 text-sm text-slate-600">
                    <Phone className="h-4 w-4 text-slate-400" />
                    {selected.phone}
                  </p>
                  <p className="flex items-center gap-3 text-sm text-slate-600">
                    <Mail className="h-4 w-4 text-slate-400" />
                    {selected.email}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-800">Team availability</p>
                <select
                  aria-label="Team availability"
                  value={selected.availability}
                  onChange={(event) =>
                    updateAvailability(event.target.value as TeamAvailability)
                  }
                  disabled={saving}
                  className="mt-3 h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none"
                >
                  <option>Available</option>
                  <option>On job</option>
                  <option>Off duty</option>
                </select>
              </div>

              <div className="border-t pt-5">
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-800">Team members</p>
                  <span className="text-xs text-muted-foreground">{members.filter((member) => member.isActive).length} active</span>
                </div>
                <div className="mt-3 space-y-2">
                  {members.map((member) => (
                    <div key={member.id} className="flex items-center justify-between rounded-lg border px-3 py-2">
                      <div className="min-w-0"><p className="truncate text-sm font-medium text-slate-800">{member.name}</p><p className="text-xs text-muted-foreground">{member.employeeId}{member.phone ? ` · ${member.phone}` : ''}</p></div>
                      <Button variant="ghost" size="sm" disabled={memberSaving} onClick={() => toggleMember(member)}>{member.isActive ? 'Deactivate' : 'Activate'}</Button>
                    </div>
                  ))}
                  {members.length === 0 && <p className="rounded-lg bg-slate-50 p-3 text-xs text-muted-foreground">No individual members added yet.</p>}
                </div>
                <div className="mt-3 grid gap-2 rounded-lg bg-slate-50 p-3 sm:grid-cols-2">
                  <Input aria-label="Member name" placeholder="Member name" value={memberForm.name} onChange={(event) => setMemberForm((current) => ({ ...current, name: event.target.value }))} />
                  <Input aria-label="Employee ID" placeholder="Employee ID" value={memberForm.employeeId} onChange={(event) => setMemberForm((current) => ({ ...current, employeeId: event.target.value }))} />
                  <Input aria-label="Member phone" placeholder="Phone (optional)" maxLength={10} inputMode="numeric" value={memberForm.phone} onChange={(event) => setMemberForm((current) => ({ ...current, phone: event.target.value.replace(/\D/g, '').slice(0, 10) }))} />
                  <Input aria-label="Member skills" placeholder="Skills, comma separated" value={memberForm.skills} onChange={(event) => setMemberForm((current) => ({ ...current, skills: event.target.value }))} />
                  <Button size="sm" className="gap-2 bg-orange-500 hover:bg-orange-600 sm:col-span-2" disabled={memberSaving} onClick={addMember}><Plus className="h-4 w-4" />{memberSaving ? 'Saving…' : 'Add member'}</Button>
                  {memberError && <p role="alert" className="text-xs font-medium text-red-700 sm:col-span-2">{memberError}</p>}
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-800">Specialties</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {selected.specialties.map((specialty) => (
                    <Badge variant="secondary" key={specialty}>
                      {specialty}
                    </Badge>
                  ))}
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between">
                  <p className="text-sm font-semibold text-slate-800">Assigned work orders</p>
                  <span className="text-xs text-muted-foreground">
                    {selected.assignedComplaints.length}
                  </span>
                </div>
                {selected.assignedComplaints.length > 0 ? (
                  <div className="mt-3 space-y-2">
                    {selected.assignedComplaints.map((complaintId) => (
                      <Link
                        className="flex items-center justify-between rounded-lg border px-3 py-2 text-sm font-medium text-slate-700 hover:border-orange-200 hover:bg-orange-50 hover:text-orange-700"
                        to="/incidents"
                        key={complaintId}
                      >
                        {complaintId}
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 rounded-lg bg-slate-50 p-3 text-xs text-muted-foreground">
                    No work orders assigned.
                  </p>
                )}
              </div>

              <div className="border-t pt-5">
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    className="flex-1 gap-2"
                    onClick={() => openEdit(selected)}
                  >
                    <Pencil className="h-4 w-4" />
                    Edit team
                  </Button>
                  <Button
                    variant="destructive"
                    className="gap-2"
                    onClick={() => setConfirmDeleteId(selected.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                    Delete team
                  </Button>
                </div>
              </div>
            </div>
          </aside>
        </div>
      )}

      {/* Add / Edit Team Form Dialog */}
      {formOpen && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
          onClick={() => setFormOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label={editingId ? 'Edit repair team' : 'Add repair team'}
            className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-xl bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b px-6 py-5">
              <div>
                <h2 className="text-xl font-bold text-slate-900">
                  {editingId ? 'Edit repair team' : 'Add repair team'}
                </h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  Keep crew contact and coverage details current.
                </p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setFormOpen(false)}
                aria-label="Close team form"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>
            <div className="grid gap-4 p-6 sm:grid-cols-2">
              <label className="space-y-2 text-sm font-semibold text-slate-700 sm:col-span-2">
                Team name
                <Input
                  aria-label="Team name"
                  value={form.name}
                  onChange={(event) => updateForm('name', event.target.value)}
                  placeholder="e.g. Team East"
                />
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Team lead
                <Input
                  aria-label="Team lead"
                  value={form.lead}
                  onChange={(event) => updateForm('lead', event.target.value)}
                  placeholder="Full name"
                />
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Zone
                <select
                  aria-label="Team zone"
                  value={form.zone}
                  onChange={(event) => updateForm('zone', event.target.value)}
                  className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm font-normal outline-none"
                >
                  <option>West Zone</option>
                  <option>Central Zone</option>
                  <option>North Zone</option>
                  <option>South Zone</option>
                  <option>East Zone</option>
                </select>
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Phone
                <Input
                  aria-label="Team phone"
                  value={form.phone}
                  maxLength={10}
                  inputMode="numeric"
                  pattern="[0-9]{10}"
                  onChange={(event) =>
                    updateForm(
                      'phone',
                      event.target.value.replace(/\D/g, '').slice(0, 10)
                    )
                  }
                  placeholder="10-digit phone number"
                />
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Email
                <Input
                  aria-label="Team email"
                  type="email"
                  value={form.email}
                  onChange={(event) => updateForm('email', event.target.value)}
                  placeholder="team@sadaksetu.gov.in"
                />
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Members
                <Input
                  aria-label="Team members"
                  type="number"
                  min="1"
                  value={form.members}
                  onChange={(event) => updateForm('members', event.target.value)}
                />
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700">
                Availability
                <select
                  aria-label="New team availability"
                  value={form.availability}
                  onChange={(event) => updateForm('availability', event.target.value)}
                  className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm font-normal outline-none"
                >
                  <option>Available</option>
                  <option>On job</option>
                  <option>Off duty</option>
                </select>
              </label>
              <label className="space-y-2 text-sm font-semibold text-slate-700 sm:col-span-2">
                Specialties
                <span className="block text-xs font-normal text-muted-foreground">
                  Separate specialties with commas
                </span>
                <Input
                  aria-label="Team specialties"
                  value={form.specialties}
                  onChange={(event) => updateForm('specialties', event.target.value)}
                  placeholder="Pothole repair, asphalt milling, drainage"
                />
              </label>
              {formError && (
                <p
                  role="alert"
                  className="rounded-lg bg-red-50 px-3 py-2 text-sm font-medium text-red-700 sm:col-span-2"
                >
                  {formError}
                </p>
              )}
              <div className="flex justify-end gap-2 sm:col-span-2">
                <Button variant="ghost" onClick={() => setFormOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={saveTeam}
                  disabled={saving}
                  className="gap-2 bg-orange-500 hover:bg-orange-600"
                >
                  <Check className="h-4 w-4" />
                  {saving ? 'Saving…' : editingId ? 'Save changes' : 'Create team'}
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Create Team Leader Account Modal */}
      {createLeaderOpen && selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4"
          onClick={() => setCreateLeaderOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Create Team Leader Account"
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
                  <UserPlus className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Create Team Leader Login</h3>
                  <p className="text-xs text-muted-foreground">
                    For {selected.name} · Role: REPAIR_TEAM
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setCreateLeaderOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <form onSubmit={handleCreateLeaderSubmit} className="space-y-3.5">
              <div>
                <label className="text-xs font-bold uppercase text-slate-700 block mb-1">
                  Full Name
                </label>
                <Input
                  value={leaderForm.fullName}
                  onChange={(e) => setLeaderForm((c) => ({ ...c, fullName: e.target.value }))}
                  required
                />
              </div>

              <div>
                <label className="text-xs font-bold uppercase text-slate-700 block mb-1">
                  Login Email
                </label>
                <Input
                  type="email"
                  value={leaderForm.email}
                  onChange={(e) => setLeaderForm((c) => ({ ...c, email: e.target.value }))}
                  required
                />
              </div>

              <div>
                <label className="text-xs font-bold uppercase text-slate-700 block mb-1">
                  Phone
                </label>
                <Input
                  type="tel"
                  maxLength={10}
                  value={leaderForm.phone}
                  onChange={(e) => setLeaderForm((c) => ({ ...c, phone: e.target.value.replace(/\D/g, '').slice(0, 10) }))}
                />
              </div>

              <div>
                <label className="text-xs font-bold uppercase text-slate-700 block mb-1">
                  Initial Password
                </label>
                <Input
                  type="password"
                  value={leaderForm.password}
                  onChange={(e) => setLeaderForm((c) => ({ ...c, password: e.target.value }))}
                  placeholder="Min 6 characters"
                  required
                />
              </div>

              {leaderError && (
                <p className="text-xs font-medium text-red-700 bg-red-50 p-2.5 rounded-lg">
                  {leaderError}
                </p>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCreateLeaderOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={leaderSaving}
                  className="bg-orange-500 hover:bg-orange-600 text-white font-semibold text-xs"
                >
                  {leaderSaving ? 'Creating…' : 'Create & Link Account'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Link Existing Leader Modal */}
      {assignLeaderOpen && selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 p-4"
          onClick={() => setAssignLeaderOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Link Existing Team Leader"
            className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
                  <UserCheck className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Link Existing Leader</h3>
                  <p className="text-xs text-muted-foreground">
                    Connect an existing repair team account to {selected.name}
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setAssignLeaderOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <form onSubmit={handleAssignLeaderSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-bold uppercase text-slate-700 block mb-1.5">
                  Select Team Leader
                </label>
                {availableLeaders.length === 0 ? (
                  <p className="rounded-lg bg-slate-50 p-3 text-xs text-muted-foreground">
                    No unassigned team leader accounts found. You can create a new leader account instead.
                  </p>
                ) : (
                  <select
                    value={selectedLeaderId}
                    onChange={(e) => setSelectedLeaderId(e.target.value)}
                    className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none"
                    required
                  >
                    {availableLeaders.map((l) => (
                      <option key={l.id} value={l.id}>
                        {l.full_name} ({l.email})
                      </option>
                    ))}
                  </select>
                )}
              </div>

              {assignLeaderError && (
                <p className="text-xs font-medium text-red-700 bg-red-50 p-2.5 rounded-lg">
                  {assignLeaderError}
                </p>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setAssignLeaderOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={assignLeaderSaving || availableLeaders.length === 0}
                  className="bg-orange-500 hover:bg-orange-600 text-white font-semibold text-xs"
                >
                  {assignLeaderSaving ? 'Linking…' : 'Link Leader'}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
