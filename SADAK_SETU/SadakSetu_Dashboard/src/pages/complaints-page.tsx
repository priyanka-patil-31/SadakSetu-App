import { useEffect, useMemo, useState } from "react";
import {
  AlertTriangle,
  Calendar,
  Check,
  CheckCircle2,
  ChevronLeft,
  ChevronRight,
  Clock3,
  Compass,
  Copy,
  Download,
  FileText,
  Filter,
  HardHat,
  Home,
  Loader2,
  MapPin,
  MessageSquare,
  Navigation,
  Printer,
  RefreshCw,
  Route,
  Search,
  ShieldAlert,
  Trash2,
  UserRound,
  X,
} from "lucide-react";
import { downloadCsv, printTableReport } from "@/lib/export-utils";
import { Link } from "react-router-dom";
import { CircleMarker, MapContainer, Popup, TileLayer, useMap } from "react-leaflet";
import "leaflet/dist/leaflet.css";

import { PageHeader } from "@/components/page-header";
import { StatusBadge } from "@/components/status-badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  complaintService,
  type ComplaintEvidence,
} from "@/services/complaints-service";
import {
  assignmentsService,
  type WorkOrder,
} from "@/services/assignments-service";
import { teamsService } from "@/services/teams-service";
import type { RepairTeam } from "@/lib/teams-data";
import {
  complaintStatusLabels,
  validComplaintTransitions,
} from "@/lib/complaints-data";
import type {
  BackendComplaintStatus,
  Complaint,
  ComplaintPriority,
} from "@/lib/complaints-data";
import { formatDate } from "@/lib/utils";
import {
  reverseGeocode,
  isMeaningfulAddress,
  type ReverseGeocodeResult,
} from "@/services/geocoding-service";

const PAGE_SIZE = 10;
const summaryStatuses = ["Submitted", "In progress", "Resolved", "Rejected"] as const;

const priorityClasses: Record<ComplaintPriority, string> = {
  Critical: "border-red-200 bg-red-50 text-red-700",
  High: "border-orange-200 bg-orange-50 text-orange-700",
  Medium: "border-sky-200 bg-sky-50 text-sky-700",
  Low: "border-slate-200 bg-slate-50 text-slate-600",
};

const severityMarkerColors: Record<ComplaintPriority, string> = {
  Critical: "#ef4444",
  High: "#f97316",
  Medium: "#0284c7",
  Low: "#10b981",
};

function PriorityBadge({ priority }: { priority: ComplaintPriority }) {
  return (
    <Badge
      variant="outline"
      className={`font-medium ${priorityClasses[priority]}`}
    >
      {priority}
    </Badge>
  );
}

/**
 * Validates complaint coordinates before rendering the local map surface.
 */

function hasValidCoordinates(
  complaint: Complaint | null
): complaint is Complaint & { coordinates: [number, number] } {
  if (!complaint?.coordinates) return false;
  const [lat, lng] = complaint.coordinates;
  return (
    typeof lat === "number" &&
    typeof lng === "number" &&
    !isNaN(lat) &&
    !isNaN(lng) &&
    (lat !== 0 || lng !== 0) &&
    lat >= -90 &&
    lat <= 90 &&
    lng >= -180 &&
    lng <= 180
  );
}

/**
 * Map resizer hook ensuring Leaflet correctly calculates dimensions when inside drawers.
 */
function DetailMapResizer({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.invalidateSize();
    const t1 = setTimeout(() => {
      map.invalidateSize();
      map.setView(center, 14);
    }, 150);
    const t2 = setTimeout(() => {
      map.invalidateSize();
    }, 450);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [map, center]);
  return null;
}

export function ComplaintsPage() {
  const [complaints, setComplaints] = useState<Complaint[]>([]);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All statuses");
  const [priorityFilter, setPriorityFilter] = useState("All priorities");
  const [sortBy, setSortBy] = useState("Newest first");
  const [page, setPage] = useState(1);
  const [selected, setSelected] = useState<Complaint | null>(null);
  const [pendingStatus, setPendingStatus] = useState<BackendComplaintStatus | null>(
    null,
  );
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [evidence, setEvidence] = useState<ComplaintEvidence[]>([]);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [copiedCoords, setCopiedCoords] = useState(false);
  const [downloadPriority, setDownloadPriority] = useState<string>("ALL");

  // Work Order Assignment States
  const [activeAssignment, setActiveAssignment] = useState<WorkOrder | null>(null);
  const [assignmentLoading, setAssignmentLoading] = useState(false);
  const [assignModalOpen, setAssignModalOpen] = useState(false);
  const [reassignModalOpen, setReassignModalOpen] = useState(false);
  const [availableTeams, setAvailableTeams] = useState<RepairTeam[]>([]);

  // Assign Form
  const [assignTeamId, setAssignTeamId] = useState("");
  const [assignPriority, setAssignPriority] = useState<string>("HIGH");
  const [assignDeadline, setAssignDeadline] = useState("");
  const [assignInstructions, setAssignInstructions] = useState("");
  const [assignSubmitting, setAssignSubmitting] = useState(false);
  const [assignError, setAssignError] = useState("");

  // Reassign Form
  const [reassignTeamId, setReassignTeamId] = useState("");
  const [reassignReason, setReassignReason] = useState("");
  const [reassignPriority, setReassignPriority] = useState<string>("HIGH");
  const [reassignDeadline, setReassignDeadline] = useState("");
  const [reassignInstructions, setReassignInstructions] = useState("");
  const [reassignSubmitting, setReassignSubmitting] = useState(false);
  const [reassignError, setReassignError] = useState("");

  const handleExportCsv = (priorityToExport?: string) => {
    const targetPriority = priorityToExport || downloadPriority;
    const records = targetPriority === "ALL"
      ? complaints
      : complaints.filter((c) => c.priority === targetPriority);

    const prefix = targetPriority === "ALL" ? "all-complaints" : `${targetPriority.toLowerCase()}-priority-complaints`;

    downloadCsv({
      filename: `sadaksetu-${prefix}-${new Date().toISOString().slice(0, 10)}.csv`,
      headers: [
        "Complaint ID",
        "Title",
        "Description",
        "Category",
        "Priority",
        "Status",
        "Citizen Reporter",
        "Reporter Email",
        "Area / Locality",
        "Address",
        "Latitude",
        "Longitude",
        "Assigned Repair Team",
        "Reported Date",
        "Photo",
      ],
      rows: records.map((c) => [
        c.id,
        c.title,
        c.description,
        c.category,
        c.priority,
        c.status,
        c.reporter,
        c.reporterEmail,
        c.area || "Area Not Provided",
        c.address || c.location,
        c.coordinates ? c.coordinates[0] : "",
        c.coordinates ? c.coordinates[1] : "",
        c.assignedTeam || "Unassigned",
        formatDate(c.reportedAt),
        c.photoUrl ? "Available" : "Not uploaded",
      ]),
    });
  };

  const handlePrintPdf = () => {
    const records = downloadPriority === "ALL"
      ? complaints
      : complaints.filter((c) => c.priority === downloadPriority);

    printTableReport({
      title: "Complaints Management Report",
      subtitle: `Official Incident Log · Priority Filter: ${downloadPriority}`,
      filters: {
        "Priority Scope": downloadPriority === "ALL" ? "All Priorities" : downloadPriority,
        "Status Filter": statusFilter,
        "Total Found": String(records.length),
      },
      summaryCards: [
        { label: "Total Complaints", value: complaints.length },
        { label: "Critical", value: complaints.filter((c) => c.priority === "Critical").length },
        { label: "High", value: complaints.filter((c) => c.priority === "High").length },
        { label: "Medium", value: complaints.filter((c) => c.priority === "Medium").length },
        { label: "Low", value: complaints.filter((c) => c.priority === "Low").length },
      ],
      headers: [
        "Complaint ID",
        "Title",
        "Category",
        "Priority",
        "Status",
        "Reporter",
        "Area / Address",
        "Assigned Team",
      ],
      rows: records.map((c) => [
        c.id,
        c.title,
        c.category,
        c.priority,
        c.status,
        c.reporter,
        c.area || c.address || c.location,
        c.assignedTeam || "Unassigned",
      ]),
      photoUrls: records.map((c) => c.photoUrl),
    });
  };
  const [copiedAddress, setCopiedAddress] = useState(false);
  const [resolvedAddress, setResolvedAddress] = useState<string>("");
  const [addressDetails, setAddressDetails] = useState<ReverseGeocodeResult | null>(null);
  const [addressLoading, setAddressLoading] = useState(false);

  useEffect(() => {
    let active = true;
    complaintService
      .list({ page: 1, pageSize: 100 })
      .then((response) => {
        if (active) setComplaints(response.items);
      })
      .catch((reason: unknown) => {
        if (active)
          setError(
            reason instanceof Error
              ? reason.message
              : "Unable to load complaints.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const filteredComplaints = useMemo(() => {
    const query = search.trim().toLowerCase();
    return [
      ...complaints.filter((complaint) => {
        const haystack =
          `${complaint.id} ${complaint.title} ${complaint.location} ${complaint.category} ${complaint.reporter}`.toLowerCase();
        return (
          haystack.includes(query) &&
          (statusFilter === "All statuses" ||
            complaint.status === statusFilter) &&
          (priorityFilter === "All priorities" ||
            complaint.priority === priorityFilter)
        );
      }),
    ].sort((left, right) =>
      sortBy === "Oldest first"
        ? left.reportedAt.localeCompare(right.reportedAt)
        : right.reportedAt.localeCompare(left.reportedAt),
    );
  }, [complaints, priorityFilter, search, sortBy, statusFilter]);

  const pageCount = Math.max(
    1,
    Math.ceil(filteredComplaints.length / PAGE_SIZE),
  );
  const safePage = Math.min(page, pageCount);
  const visibleComplaints = filteredComplaints.slice(
    (safePage - 1) * PAGE_SIZE,
    safePage * PAGE_SIZE,
  );

  const openDetails = (complaint: Complaint) => {
    setSelected(complaint);
    setPendingStatus(complaint.backendStatus);
    setNote("");
    setEvidence([]);
    setDeleteConfirmOpen(false);
    setCopiedCoords(false);
    setCopiedAddress(false);
    setEvidenceLoading(true);
    setActiveAssignment(null);
    setAssignmentLoading(true);

    const initialAddr = isMeaningfulAddress(complaint.address)
      ? complaint.address!
      : isMeaningfulAddress(complaint.location)
      ? complaint.location
      : "";
    setResolvedAddress(initialAddr);
    setAddressDetails(null);

    if (hasValidCoordinates(complaint)) {
      setAddressLoading(true);
      const [lat, lng] = complaint.coordinates;
      reverseGeocode(lat, lng)
        .then((result) => {
          if (result?.displayName) {
            setResolvedAddress(result.displayName);
            setAddressDetails(result);
          }
        })
        .finally(() => {
          setAddressLoading(false);
        });
    }

    complaintService
      .getEvidence(complaint.backendId)
      .then(setEvidence)
      .catch(() => setEvidence([]))
      .finally(() => setEvidenceLoading(false));

    // Fetch active assignment linked to this complaint
    assignmentsService
      .getComplaintAssignments(complaint.backendId)
      .then((items) => {
        const active = items.find((i) => i.status === "ACTIVE") || null;
        setActiveAssignment(active);
      })
      .catch(() => setActiveAssignment(null))
      .finally(() => setAssignmentLoading(false));
  };

  const closeDetails = () => {
    setSelected(null);
    setPendingStatus(null);
    setNote("");
    setDeleteConfirmOpen(false);
    setActiveAssignment(null);
    setAssignModalOpen(false);
    setReassignModalOpen(false);
  };

  const openAssignModal = async () => {
    if (!selected) return;
    setAssignError("");
    setAssignInstructions("");
    // Default deadline to 3 days from now
    const d = new Date();
    d.setDate(d.getDate() + 3);
    setAssignDeadline(d.toISOString().slice(0, 16));
    setAssignPriority(selected.priority.toUpperCase());
    try {
      const list = await teamsService.list();
      setAvailableTeams(list);
      if (list.length > 0) {
        setAssignTeamId(list[0].id);
      }
    } catch {
      setAvailableTeams([]);
    }
    setAssignModalOpen(true);
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !assignTeamId) {
      setAssignError("Please select a repair team.");
      return;
    }
    setAssignSubmitting(true);
    setAssignError("");
    try {
      const result = await assignmentsService.assignComplaint(selected.backendId, {
        team_id: assignTeamId,
        priority: assignPriority,
        expected_completion_date: assignDeadline ? new Date(assignDeadline).toISOString() : undefined,
        instructions: assignInstructions.trim() || undefined,
      });
      setActiveAssignment(result);
      setAssignModalOpen(false);
      // Reload complaints list to reflect changes
      const updatedList = await complaintService.list({ page: 1, pageSize: 100 });
      setComplaints(updatedList.items);
      const updatedSelected = updatedList.items.find((c) => c.backendId === selected.backendId);
      if (updatedSelected) {
        setSelected(updatedSelected);
      }
    } catch (err) {
      setAssignError(err instanceof Error ? err.message : "Failed to assign work order");
    } finally {
      setAssignSubmitting(false);
    }
  };

  const openReassignModal = async () => {
    if (!selected || !activeAssignment) return;
    setReassignError("");
    setReassignReason("");
    setReassignInstructions(activeAssignment.instructions || "");
    setReassignPriority(activeAssignment.priority || "HIGH");
    if (activeAssignment.expectedCompletionDate) {
      setReassignDeadline(new Date(activeAssignment.expectedCompletionDate).toISOString().slice(0, 16));
    } else {
      const d = new Date();
      d.setDate(d.getDate() + 3);
      setReassignDeadline(d.toISOString().slice(0, 16));
    }
    try {
      const list = await teamsService.list();
      setAvailableTeams(list);
      const otherTeam = list.find((t) => t.id !== activeAssignment.teamId) || list[0];
      if (otherTeam) setReassignTeamId(otherTeam.id);
    } catch {
      setAvailableTeams([]);
    }
    setReassignModalOpen(true);
  };

  const handleReassignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || !reassignTeamId) {
      setReassignError("Please select a new repair team.");
      return;
    }
    if (!reassignReason.trim()) {
      setReassignError("A reason for reassignment is mandatory.");
      return;
    }
    setReassignSubmitting(true);
    setReassignError("");
    try {
      const result = await assignmentsService.reassignWorkOrder(selected.backendId, {
        team_id: reassignTeamId,
        reason: reassignReason.trim(),
        priority: reassignPriority,
        expected_completion_date: reassignDeadline ? new Date(reassignDeadline).toISOString() : undefined,
        instructions: reassignInstructions.trim() || undefined,
      });
      setActiveAssignment(result);
      setReassignModalOpen(false);
      const updatedList = await complaintService.list({ page: 1, pageSize: 100 });
      setComplaints(updatedList.items);
    } catch (err) {
      setReassignError(err instanceof Error ? err.message : "Failed to reassign work order");
    } finally {
      setReassignSubmitting(false);
    }
  };

  const canDeleteSelected = selected
    ? selected.backendStatus === "SUBMITTED" || selected.backendStatus === "REJECTED"
    : false;

  const deleteSelected = async () => {
    if (!selected || !canDeleteSelected) return;
    setDeleting(true);
    try {
      await complaintService.remove(selected.backendId, "Removed by administrator");
      setComplaints((current) => current.filter((item) => item.backendId !== selected.backendId));
      closeDetails();
    } catch (reason: unknown) {
      setError(reason instanceof Error ? reason.message : "Unable to delete complaint.");
    } finally {
      setDeleting(false);
    }
  };

  const saveStatus = async () => {
    if (!selected || !pendingStatus || pendingStatus === selected.backendStatus)
      return;
    try {
      const updated = await complaintService.update(selected.backendId, {
        status: pendingStatus,
      });
      setComplaints((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setSelected(updated);
    } catch (reason: unknown) {
      setError(
        reason instanceof Error
          ? reason.message
          : "Unable to update complaint status.",
      );
    }
  };

  const addNote = async () => {
    if (!selected || !note.trim()) return;
    try {
      const updated = await complaintService.update(selected.backendId, {
        note: note.trim(),
      });
      setComplaints((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      setSelected(updated);
      setNote("");
    } catch (reason: unknown) {
      setError(
        reason instanceof Error ? reason.message : "Unable to save the note.",
      );
    }
  };

  const clearFilters = () => {
    setSearch("");
    setStatusFilter("All statuses");
    setPriorityFilter("All priorities");
    setPage(1);
  };

  const copyCoordinates = (coords: [number, number]) => {
    const text = `${coords[0].toFixed(6)}, ${coords[1].toFixed(6)}`;
    navigator.clipboard.writeText(text).then(() => {
      setCopiedCoords(true);
      setTimeout(() => setCopiedCoords(false), 2500);
    });
  };

  const copyAddress = (addressText: string) => {
    if (!addressText) return;
    navigator.clipboard.writeText(addressText).then(() => {
      setCopiedAddress(true);
      setTimeout(() => setCopiedAddress(false), 2500);
    });
  };

  return (
    <div>
      <PageHeader
        eyebrow="Operations"
        title="Complaint management"
        description="Review, triage, and resolve road issues reported through the backend."
        action={
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center rounded-lg border border-slate-200 bg-white shadow-2xs">
              <select
                aria-label="Export priority filter"
                value={downloadPriority}
                onChange={(e) => setDownloadPriority(e.target.value)}
                className="h-8 rounded-l-lg border-0 bg-transparent px-2.5 text-xs font-semibold text-slate-700 outline-none"
              >
                <option value="ALL">All Priorities ({complaints.length})</option>
                <option value="Critical">Critical ({complaints.filter((c) => c.priority === "Critical").length})</option>
                <option value="High">High ({complaints.filter((c) => c.priority === "High").length})</option>
                <option value="Medium">Medium ({complaints.filter((c) => c.priority === "Medium").length})</option>
                <option value="Low">Low ({complaints.filter((c) => c.priority === "Low").length})</option>
              </select>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => handleExportCsv()}
                className="h-8 rounded-none rounded-r-lg border-l border-slate-200 px-2.5 text-xs font-semibold hover:bg-slate-50"
                title="Download CSV for selected priority"
              >
                <Download className="mr-1 h-3.5 w-3.5 text-slate-500" />
                <span>Export CSV</span>
              </Button>
            </div>

            <Button
              variant="outline"
              size="sm"
              onClick={handlePrintPdf}
              className="h-8 gap-1.5 text-xs font-semibold"
            >
              <Printer className="h-3.5 w-3.5 text-slate-500" />
              <span>Print PDF</span>
            </Button>
          </div>
        }
      />
      <div className="mb-6 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {summaryStatuses.map((status) => (
          <Card key={status}>
            <CardContent className="p-4">
              <p className="text-xs font-medium text-muted-foreground">
                {status}
              </p>
              <p className="mt-1 text-2xl font-bold text-slate-900">
                {
                  complaints.filter((complaint) => complaint.status === status)
                    .length
                }
              </p>
            </CardContent>
          </Card>
        ))}
      </div>
      <Card>
        <CardContent className="p-0">
          <div className="flex flex-col gap-3 border-b p-4 lg:flex-row lg:items-center lg:justify-between">
            <div className="relative w-full lg:max-w-sm">
              <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
              <Input
                aria-label="Search complaints"
                value={search}
                onChange={(event) => {
                  setSearch(event.target.value);
                  setPage(1);
                }}
                placeholder="Search complaint ID, title, location, or citizen..."
                className="pl-9"
              />
            </div>
            <div className="flex flex-wrap gap-2">
              <select
                aria-label="Status filter"
                value={statusFilter}
                onChange={(event) => {
                  setStatusFilter(event.target.value);
                  setPage(1);
                }}
                className="h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none"
              >
                <option>All statuses</option>
                <option>Submitted</option>
                <option>Under review</option>
                <option>AI processing</option>
                <option>Assigned</option>
                <option>In progress</option>
                <option>Resolved</option>
                <option>Rejected</option>
              </select>
              <select
                aria-label="Priority filter"
                value={priorityFilter}
                onChange={(event) => {
                  setPriorityFilter(event.target.value);
                  setPage(1);
                }}
                className="h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none"
              >
                <option>All priorities</option>
                <option>Critical</option>
                <option>High</option>
                <option>Medium</option>
                <option>Low</option>
              </select>
              <select
                aria-label="Sort complaints"
                value={sortBy}
                onChange={(event) => {
                  setSortBy(event.target.value);
                  setPage(1);
                }}
                className="h-10 rounded-lg border border-input bg-background px-3 text-sm outline-none"
              >
                <option>Newest first</option>
                <option>Oldest first</option>
              </select>
              <Button variant="outline" size="icon" aria-label="Filter summary">
                <Filter className="h-4 w-4" />
              </Button>
            </div>
          </div>
          {error && (
            <p
              role="alert"
              className="border-b bg-red-50 px-5 py-3 text-sm font-medium text-red-700"
            >
              {error}
            </p>
          )}
          {loading ? (
            <div className="p-12 text-center text-sm text-muted-foreground">
              Loading complaints...
            </div>
          ) : visibleComplaints.length === 0 ? (
            <div className="p-12 text-center">
              <Search className="mx-auto h-8 w-8 text-slate-300" />
              <p className="mt-3 text-sm font-semibold text-slate-700">
                No complaints found
              </p>
              <p className="mt-1 text-xs text-muted-foreground">
                No backend records are currently available.
              </p>
              <Button
                variant="ghost"
                className="mt-3 text-orange-600"
                onClick={clearFilters}
              >
                Clear filters
              </Button>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Complaint / Citizen</TableHead>
                  <TableHead className="w-24">Map</TableHead>
                  <TableHead>Location</TableHead>
                  <TableHead>Priority</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Reported</TableHead>
                  <TableHead className="w-28 text-right">Action</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {visibleComplaints.map((complaint) => {
                  const hasCoord = hasValidCoordinates(complaint);
                  return (
                    <TableRow key={complaint.id}>
                      <TableCell>
                        <button
                          type="button"
                          className="text-left"
                          onClick={() => openDetails(complaint)}
                          aria-label={`Open complaint ${complaint.id}`}
                        >
                          <p className="font-semibold text-slate-800 hover:text-orange-600">
                            {complaint.title}
                          </p>
                          <p className="mt-0.5 text-xs text-muted-foreground">
                            {complaint.id} · {complaint.category} · Raised by {complaint.reporter || "Citizen"}
                          </p>
                        </button>
                      </TableCell>

                      {/* Small Map Preview in Table */}
                      <TableCell>
                        {hasCoord ? (
                          <button
                            type="button"
                            onClick={() => openDetails(complaint)}
                            className="group relative flex h-11 w-16 shrink-0 overflow-hidden rounded-lg border border-slate-200 bg-slate-100 shadow-2xs hover:border-orange-300 transition-all cursor-pointer"
                            title={`Inspect location on map for ${complaint.location}`}
                          >
                            <div className="relative h-full w-full bg-slate-200">
                              <div className="absolute left-1/2 top-0 h-full w-1 -translate-x-1/2 rotate-12 bg-white/80" />
                              <div className="absolute left-0 top-1/2 h-1 w-full -rotate-6 bg-white/80" />
                              <span className="absolute inset-0 m-auto h-3 w-3 rounded-full border-2 border-white bg-orange-500 shadow" />
                              <span className="absolute bottom-0.5 left-1 right-1 rounded bg-slate-900/70 px-0.5 text-center text-[7px] font-bold text-white">LOCAL GPS</span>
                            </div>
                            <div className="absolute inset-0 flex items-center justify-center bg-black/5 group-hover:bg-transparent">
                              <div className="flex h-4.5 w-4.5 items-center justify-center rounded-full bg-white shadow-xs ring-1 ring-black/10">
                                <MapPin className="h-2.5 w-2.5 text-orange-600" />
                              </div>
                            </div>
                          </button>
                        ) : (
                          <div className="flex h-11 w-16 items-center justify-center rounded-lg border border-dashed border-slate-200 bg-slate-50 text-[10px] text-slate-400">
                            No GPS
                          </div>
                        )}
                      </TableCell>

                      <TableCell>
                        <div
                          className="flex items-center gap-1.5 text-sm text-slate-800 font-semibold"
                          title={complaint.address || complaint.location}
                        >
                          <MapPin className="h-3.5 w-3.5 text-orange-500 shrink-0" />
                          <span className="truncate max-w-[220px]">
                            {complaint.address || complaint.location}
                          </span>
                        </div>
                        <div className="mt-1 flex items-center gap-2">
                          <span className="text-xs text-muted-foreground truncate max-w-[130px]">
                            {complaint.area || complaint.zone}
                          </span>
                          {hasCoord && (
                            <span className="font-mono text-[10px] text-slate-400">
                              {complaint.coordinates[0].toFixed(3)},{" "}
                              {complaint.coordinates[1].toFixed(3)}
                            </span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell>
                        <PriorityBadge priority={complaint.priority} />
                      </TableCell>
                      <TableCell>
                        <StatusBadge status={complaint.status} />
                      </TableCell>
                      <TableCell className="whitespace-nowrap text-sm text-slate-600">
                        {formatDate(complaint.reportedAt)}
                      </TableCell>
                      <TableCell className="text-right whitespace-nowrap">
                        <div className="flex items-center justify-end gap-1.5">
                          {complaint.backendStatus !== "RESOLVED" && complaint.backendStatus !== "REJECTED" && (
                            <Button
                              variant="outline"
                              size="sm"
                              className="gap-1 border-orange-200 text-orange-600 hover:bg-orange-50 hover:text-orange-700 text-xs"
                              onClick={() => {
                                openDetails(complaint);
                                setTimeout(openAssignModal, 150);
                              }}
                            >
                              <HardHat className="h-3.5 w-3.5" />
                              Assign
                            </Button>
                          )}
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={() => openDetails(complaint)}
                          >
                            View details
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}

          {/* Mobile Complaint Cards */}
          <div className="divide-y md:hidden">
            {visibleComplaints.map((complaint) => {
              const hasCoord = hasValidCoordinates(complaint);
              return (
                <div
                  key={complaint.id}
                  className="flex items-center justify-between p-4 gap-3"
                >
                  <button
                    type="button"
                    className="flex-1 text-left min-w-0"
                    onClick={() => openDetails(complaint)}
                    aria-label={`Open complaint ${complaint.id}`}
                  >
                    <p className="font-semibold text-slate-800 truncate">
                      {complaint.title}
                    </p>
                    <p className="mt-0.5 text-xs text-muted-foreground truncate">
                      {complaint.id} · {complaint.address || complaint.location}
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <PriorityBadge priority={complaint.priority} />
                      <StatusBadge status={complaint.status} />
                    </div>
                  </button>

                  {hasCoord && (
                    <button
                      type="button"
                      onClick={() => openDetails(complaint)}
                      className="group relative flex h-12 w-16 shrink-0 overflow-hidden rounded-lg border border-slate-200 bg-slate-100 shadow-2xs"
                    >
                      <div className="relative h-full w-full bg-slate-200">
                        <span className="absolute inset-0 m-auto h-3 w-3 rounded-full border-2 border-white bg-orange-500 shadow" />
                      </div>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <div className="flex h-4.5 w-4.5 items-center justify-center rounded-full bg-white shadow-xs">
                          <MapPin className="h-2.5 w-2.5 text-orange-600" />
                        </div>
                      </div>
                    </button>
                  )}
                </div>
              );
            })}
          </div>

          <div className="flex flex-col gap-3 border-t px-5 py-4 text-xs text-muted-foreground sm:flex-row sm:items-center sm:justify-between">
            <span>
              Page {safePage} of {pageCount}
            </span>
            <div className="flex gap-1">
              <Button
                variant="outline"
                size="sm"
                disabled={safePage === 1}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                <ChevronLeft className="mr-1 h-3.5 w-3.5" />
                Previous
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={safePage === pageCount}
                onClick={() =>
                  setPage((current) => Math.min(pageCount, current + 1))
                }
              >
                Next
                <ChevronRight className="ml-1 h-3.5 w-3.5" />
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Complaint Details Drawer */}
      {selected && (
        <div
          className="fixed inset-0 z-40 flex justify-end bg-slate-950/40"
          onClick={closeDetails}
        >
          <aside
            role="dialog"
            aria-modal="true"
            aria-label={`Complaint details ${selected.id}`}
            className="flex h-full w-full max-w-xl flex-col overflow-y-auto bg-white shadow-2xl"
            onClick={(event) => event.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b px-6 py-5">
              <div>
                <div className="flex items-center gap-2">
                  <p className="text-xs font-bold uppercase tracking-[0.16em] text-orange-500">
                    {selected.id}
                  </p>
                  <StatusBadge status={selected.status} />
                </div>
                <h2 className="mt-2 text-xl font-bold tracking-tight text-slate-900">
                  {selected.title}
                </h2>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={closeDetails}
                aria-label="Close complaint details"
              >
                <X className="h-5 w-5" />
              </Button>
            </div>

            <div className="space-y-6 p-6">
              {/* Summary metadata grid */}
              <div className="grid grid-cols-2 gap-4 rounded-xl border bg-slate-50 p-4">
                <div>
                  <p className="text-xs text-muted-foreground">Reported by</p>
                  <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-slate-800">
                    <UserRound className="h-3.5 w-3.5 text-slate-400" />
                    {selected.reporter}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Reported on</p>
                  <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-slate-800">
                    <Clock3 className="h-3.5 w-3.5 text-slate-400" />
                    {formatDate(selected.reportedAt)}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Category</p>
                  <p className="mt-1 flex items-center gap-1.5 text-sm font-semibold text-slate-800">
                    <Route className="h-3.5 w-3.5 text-slate-400" />
                    {selected.category}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-muted-foreground">Priority</p>
                  <div className="mt-1">
                    <PriorityBadge priority={selected.priority} />
                  </div>
                </div>
              </div>

              {/* Work Order Assignment / Management Section */}
              <div className="space-y-3">
                {assignmentLoading ? (
                  <div className="flex items-center justify-center gap-2 rounded-xl border border-slate-200 bg-slate-50 p-4 text-xs text-muted-foreground">
                    <Loader2 className="h-4 w-4 animate-spin text-orange-500" />
                    <span>Loading work order assignment…</span>
                  </div>
                ) : activeAssignment ? (
                  <div className="rounded-xl border border-orange-200 bg-gradient-to-br from-orange-50/50 via-white to-slate-50 p-4 space-y-3.5 shadow-2xs">
                    <div className="flex items-center justify-between border-b border-orange-100 pb-2.5">
                      <div className="flex items-center gap-2">
                        <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-orange-500 text-white shadow-xs">
                          <HardHat className="h-4 w-4" />
                        </div>
                        <div>
                          <p className="font-mono text-xs font-bold text-slate-900">
                            {activeAssignment.workOrderNumber}
                          </p>
                          <p className="text-[10px] text-muted-foreground">Active Work Order</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          variant="outline"
                          className={`text-[10px] font-bold ${
                            activeAssignment.workStatus === "COMPLETED"
                              ? "border-emerald-200 bg-emerald-50 text-emerald-700"
                              : activeAssignment.workStatus === "COMPLETION_SUBMITTED"
                              ? "border-amber-200 bg-amber-50 text-amber-700 animate-pulse"
                              : activeAssignment.workStatus === "DELAYED"
                              ? "border-red-200 bg-red-50 text-red-700"
                              : activeAssignment.workStatus === "IN_PROGRESS"
                              ? "border-sky-200 bg-sky-50 text-sky-700"
                              : "border-slate-200 bg-white text-slate-700"
                          }`}
                        >
                          {activeAssignment.workStatus.replace("_", " ")}
                        </Badge>
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 gap-1 px-2 text-xs font-semibold text-orange-700 border-orange-200 hover:bg-orange-50"
                          onClick={openReassignModal}
                        >
                          <RefreshCw className="h-3 w-3" />
                          Reassign
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-2 text-xs">
                      <div className="rounded-lg bg-white p-2.5 border border-slate-200/80">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">
                          Assigned Team
                        </span>
                        <p className="font-semibold text-slate-900 truncate">
                          {activeAssignment.teamName}
                        </p>
                        <p className="text-[11px] text-muted-foreground truncate">
                          Lead: {activeAssignment.teamLeadName}
                        </p>
                      </div>
                      <div className="rounded-lg bg-white p-2.5 border border-slate-200/80">
                        <span className="text-[10px] uppercase font-bold text-slate-400 block">
                          Target Deadline
                        </span>
                        <p className="font-semibold text-slate-900 truncate">
                          {activeAssignment.expectedCompletionDate
                            ? new Date(activeAssignment.expectedCompletionDate).toLocaleString("en-IN", {
                                dateStyle: "medium",
                                timeStyle: "short",
                              })
                            : "No target set"}
                        </p>
                        <p className="text-[11px] text-muted-foreground">
                          Priority: {activeAssignment.priority}
                        </p>
                      </div>
                    </div>

                    {/* Progress tracking */}
                    <div className="space-y-1.5 rounded-lg bg-white p-2.5 border border-slate-200/80">
                      <div className="flex items-center justify-between text-xs font-semibold text-slate-700">
                        <span>Repair Progress</span>
                        <span className="font-bold text-orange-600">
                          {activeAssignment.progressPercentage}%
                        </span>
                      </div>
                      <div className="h-2 w-full rounded-full bg-slate-100 overflow-hidden border border-slate-200/60">
                        <div
                          className="h-full bg-gradient-to-r from-orange-500 to-emerald-500 transition-all duration-300"
                          style={{
                            width: `${Math.min(100, Math.max(0, activeAssignment.progressPercentage))}%`,
                          }}
                        />
                      </div>
                      {activeAssignment.progressNotes && (
                        <p className="mt-1 text-xs text-slate-600 italic">
                          “{activeAssignment.progressNotes}”
                        </p>
                      )}
                    </div>

                    {activeAssignment.delayReason && (
                      <div className="rounded-lg border border-red-200 bg-red-50 p-2.5 text-xs text-red-800 flex items-start gap-2">
                        <AlertTriangle className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
                        <div>
                          <span className="font-bold">Delay Reported by Crew:</span>
                          <p className="mt-0.5 text-red-700">{activeAssignment.delayReason}</p>
                        </div>
                      </div>
                    )}

                    {activeAssignment.instructions && (
                      <div className="rounded-lg bg-white p-2.5 border border-slate-200/80 text-xs">
                        <span className="font-bold text-slate-500 block mb-0.5 uppercase text-[10px]">
                          Repair Instructions:
                        </span>
                        <p className="text-slate-700 leading-relaxed">{activeAssignment.instructions}</p>
                      </div>
                    )}
                  </div>
                ) : selected.backendStatus !== "RESOLVED" && selected.backendStatus !== "REJECTED" ? (
                  <div className="rounded-xl border border-dashed border-orange-300 bg-orange-50/40 p-4 flex items-center justify-between gap-3 shadow-2xs">
                    <div className="space-y-0.5">
                      <p className="text-xs font-bold text-slate-800 flex items-center gap-1.5">
                        <HardHat className="h-4 w-4 text-orange-600" />
                        No Repair Team Assigned
                      </p>
                      <p className="text-[11px] text-muted-foreground leading-normal">
                        Create a linked work order and dispatch this issue to an available crew.
                      </p>
                    </div>
                    <Button
                      size="sm"
                      onClick={openAssignModal}
                      className="gap-1.5 bg-orange-500 hover:bg-orange-600 text-white font-semibold text-xs shrink-0 shadow-xs"
                    >
                      <HardHat className="h-3.5 w-3.5" />
                      Assign Work
                    </Button>
                  </div>
                ) : null}
              </div>

              {/* Physical Street Address & Location Details Card */}
              <div className="rounded-xl border border-slate-200 bg-slate-50/70 p-4 space-y-3.5 shadow-2xs">
                <div className="flex items-center justify-between">
                  <span className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-slate-700">
                    <Home className="h-4 w-4 text-orange-500" />
                    Physical Street Address
                  </span>
                  <div className="flex items-center gap-1">
                    {hasValidCoordinates(selected) && (
                      <Button
                        variant="outline"
                        size="sm"
                        className="h-7 px-2.5 text-xs font-semibold bg-white text-slate-700 hover:text-slate-900 border-slate-200 shadow-2xs"
                        title="Copy human-readable address"
                        onClick={() =>
                          copyAddress(
                            resolvedAddress ||
                              selected.address ||
                              selected.location
                          )
                        }
                      >
                        {copiedAddress ? (
                          <>
                            <Check className="mr-1 h-3.5 w-3.5 text-emerald-600" />
                            <span className="text-emerald-600 font-bold">Copied!</span>
                          </>
                        ) : (
                          <>
                            <Copy className="mr-1 h-3.5 w-3.5 text-slate-500" />
                            <span>Copy Address</span>
                          </>
                        )}
                      </Button>
                    )}
                  </div>
                </div>

                {/* Primary Human-Readable Address Display */}
                <div className="rounded-lg border border-slate-200/90 bg-white p-3 shadow-2xs">
                  {addressLoading ? (
                    <div className="flex items-center gap-2 py-1 text-xs text-slate-500">
                      <Loader2 className="h-3.5 w-3.5 animate-spin text-orange-500" />
                      <span>Resolving physical street address from GPS coordinates…</span>
                    </div>
                  ) : (
                    <p className="text-sm font-semibold leading-relaxed text-slate-900">
                      {resolvedAddress || selected.address || selected.location}
                    </p>
                  )}
                </div>

                {/* Structured Breakdown: Road, Area, District, State, Zone, GPS */}
                <div className="grid grid-cols-2 gap-2.5 text-xs">
                  <div className="rounded-md bg-white p-2 border border-slate-200/60">
                    <span className="text-muted-foreground block text-[10px] uppercase font-semibold">
                      Road / Street
                    </span>
                    <span className="font-semibold text-slate-800 truncate block">
                      {addressDetails?.road ||
                        selected.address ||
                        selected.location.split(",")[0] ||
                        "Road segment"}
                    </span>
                  </div>

                  <div className="rounded-md bg-white p-2 border border-slate-200/60">
                    <span className="text-muted-foreground block text-[10px] uppercase font-semibold">
                      Area / Ward
                    </span>
                    <span className="font-semibold text-slate-800 truncate block">
                      {addressDetails?.suburb ||
                        addressDetails?.neighbourhood ||
                        addressDetails?.village ||
                        selected.area ||
                        "General ward"}
                    </span>
                  </div>

                  <div className="rounded-md bg-white p-2 border border-slate-200/60">
                    <span className="text-muted-foreground block text-[10px] uppercase font-semibold">
                      District / City
                    </span>
                    <span className="font-semibold text-slate-800 truncate block">
                      {addressDetails?.city ||
                        addressDetails?.district ||
                        selected.zone}
                    </span>
                  </div>

                  <div className="rounded-md bg-white p-2 border border-slate-200/60">
                    <span className="text-muted-foreground block text-[10px] uppercase font-semibold">
                      State & PIN
                    </span>
                    <span className="font-semibold text-slate-800 truncate block">
                      {addressDetails?.state || "State recorded"}
                      {addressDetails?.postcode ? ` - ${addressDetails.postcode}` : ""}
                    </span>
                  </div>
                </div>

                {/* GPS Coordinates with copy */}
                {hasValidCoordinates(selected) && (
                  <div className="flex items-center justify-between rounded-md bg-white px-3 py-2 border border-slate-200/60 text-xs">
                    <div className="flex items-center gap-2">
                      <Compass className="h-3.5 w-3.5 text-orange-500 shrink-0" />
                      <span className="text-muted-foreground font-medium">GPS Coordinates:</span>
                      <span className="font-mono text-xs font-bold text-slate-800">
                        {selected.coordinates[0].toFixed(6)}, {selected.coordinates[1].toFixed(6)}
                      </span>
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="h-6 px-1.5 text-[11px] text-slate-500 hover:text-slate-800"
                      onClick={() => copyCoordinates(selected.coordinates!)}
                    >
                      {copiedCoords ? (
                        <span className="text-emerald-600 font-bold">Copied!</span>
                      ) : (
                        <span className="flex items-center gap-1">
                          <Copy className="h-3 w-3" />
                          <span>Copy</span>
                        </span>
                      )}
                    </Button>
                  </div>
                )}
              </div>

              {/* Geographic Road Map & Links */}
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <p className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                    <MapPin className="h-4 w-4 text-orange-500" />
                    Geographic Road Location
                  </p>
                  <span className="text-xs text-muted-foreground font-medium">
                    {selected.zone}
                  </span>
                </div>

                {/* Interactive Leaflet Map Canvas */}
                <div className="relative h-64 w-full overflow-hidden rounded-xl border border-slate-200 bg-slate-100 shadow-inner">
                  {hasValidCoordinates(selected) ? (
                    <MapContainer
                      center={selected.coordinates}
                      zoom={14}
                      preferCanvas
                      scrollWheelZoom={false}
                      className="h-full w-full"
                      style={{ height: "100%", width: "100%" }}
                    >
                      <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                        maxZoom={19}
                      />
                      <DetailMapResizer center={selected.coordinates} />
                      <CircleMarker
                        center={selected.coordinates}
                        radius={10}
                        pathOptions={{
                          color: "#ffffff",
                          weight: 3,
                          fillColor:
                            severityMarkerColors[selected.priority] || "#f97316",
                          fillOpacity: 0.95,
                        }}
                      >
                        <Popup>
                          <div className="text-xs font-sans min-w-[200px] max-w-[280px] space-y-1">
                            <span className="font-mono font-bold text-orange-600 block">
                              {selected.id}
                            </span>
                            <p className="font-bold text-slate-900 leading-snug">
                              {selected.title}
                            </p>
                            <p className="text-slate-600 font-medium leading-relaxed">
                              {resolvedAddress || selected.address || selected.location}
                            </p>
                            <p className="text-[10px] text-slate-400 font-mono">
                              {selected.coordinates[0].toFixed(5)}, {selected.coordinates[1].toFixed(5)}
                            </p>
                          </div>
                        </Popup>
                      </CircleMarker>
                    </MapContainer>
                  ) : (
                    <div className="flex h-full w-full items-center justify-center text-xs text-slate-400">
                      GPS coordinates not captured for this complaint
                    </div>
                  )}
                </div>

                {/* Direct External and Internal Navigation Links */}
                <div className="flex flex-wrap items-center gap-2 pt-1">
                  <Link
                    to="/map"
                    className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2 text-xs font-bold text-slate-700 shadow-2xs hover:bg-slate-50 hover:border-slate-300 transition-colors"
                  >
                    <Navigation className="h-3.5 w-3.5 text-orange-500" />
                    <span>Open in Live Monitoring Map</span>
                  </Link>

                  {hasValidCoordinates(selected) && (
                    <div className="flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-teal-200 bg-teal-50 px-3 py-2 text-center text-xs font-bold text-teal-800">
                      <MapPin className="h-3.5 w-3.5 text-teal-600" />
                      <span>GPS · {selected.coordinates[0].toFixed(5)}, {selected.coordinates[1].toFixed(5)}</span>
                    </div>
                  )}
                </div>
              </div>

              <div>
                <p className="text-sm font-semibold text-slate-800">
                  Complaint description
                </p>
                <p className="mt-2 text-sm leading-6 text-slate-600">
                  {selected.description}
                </p>
              </div>

              <div className="border-t pt-5">
                <p className="text-sm font-semibold text-slate-800">
                  Mobile evidence
                </p>
                {evidenceLoading ? (
                  <p className="mt-3 text-sm text-muted-foreground">
                    Loading uploaded photo and running AI detection…
                  </p>
                ) : evidence.length === 0 ? (
                  <p className="mt-3 text-sm text-muted-foreground">
                    No photo was uploaded with this complaint.
                  </p>
                ) : (
                  <div className="mt-3 space-y-4">
                    {evidence.map((item) => (
                      <div className="rounded-xl border bg-slate-50 p-3" key={item.id}>
                        <img
                          src={item.imageUrl}
                          alt="Uploaded road condition"
                          className="max-h-64 w-full rounded-lg object-cover"
                        />
                        <div className="mt-3 grid grid-cols-2 gap-3 text-xs">
                          <div>
                            <p className="text-muted-foreground">Latitude</p>
                            <p className="font-semibold text-slate-800">
                              {item.latitude ?? "Not captured"}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">Longitude</p>
                            <p className="font-semibold text-slate-800">
                              {item.longitude ?? "Not captured"}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">
                              Potholes/patches detected
                            </p>
                            <p className="font-semibold text-slate-800">
                              {item.detectionCount}
                            </p>
                          </div>
                          <div>
                            <p className="text-muted-foreground">
                              Detection status
                            </p>
                            <p
                              className={`font-semibold ${
                                item.status === "FAILED"
                                  ? "text-red-600"
                                  : item.status === "COMPLETED"
                                  ? "text-emerald-700"
                                  : "text-slate-800"
                              }`}
                            >
                              {item.status}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              <div className="border-t pt-5">
                <p className="text-sm font-semibold text-slate-800">
                  Status update
                </p>
                <div className="mt-3 flex gap-2">
                  <select
                    aria-label="Complaint status"
                    value={pendingStatus ?? selected.backendStatus}
                    onChange={(event) =>
                      setPendingStatus(
                        event.target.value as BackendComplaintStatus
                      )
                    }
                    className="h-10 flex-1 rounded-lg border border-input bg-background px-3 text-sm outline-none"
                  >
                    <option value={selected.backendStatus}>
                      {complaintStatusLabels[selected.backendStatus]}
                    </option>
                    {validComplaintTransitions[selected.backendStatus].map(
                      (status) => (
                        <option value={status} key={status}>
                          {complaintStatusLabels[status]}
                        </option>
                      )
                    )}
                  </select>
                  <Button
                    onClick={saveStatus}
                    disabled={
                      pendingStatus === selected.backendStatus ||
                      validComplaintTransitions[selected.backendStatus].length === 0
                    }
                    className="gap-2 bg-orange-500 hover:bg-orange-600"
                  >
                    <Check className="h-4 w-4" />
                    Update
                  </Button>
                </div>
                {validComplaintTransitions[selected.backendStatus].length === 0 && (
                  <p className="mt-2 text-xs text-muted-foreground">
                    No further status transitions are available.
                  </p>
                )}
              </div>

              <div className="border-t pt-5">
                <p className="flex items-center gap-2 text-sm font-semibold text-slate-800">
                  <MessageSquare className="h-4 w-4 text-slate-400" />
                  Administrative notes
                </p>
                <div className="mt-3 flex gap-2">
                  <textarea
                    aria-label="Administrative note"
                    value={note}
                    onChange={(event) => setNote(event.target.value)}
                    placeholder="Write an administrative note..."
                    className="min-h-20 flex-1 resize-none rounded-lg border border-input bg-background px-3 py-2 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring"
                  />
                  <Button
                    onClick={addNote}
                    disabled={!note.trim()}
                    className="self-end bg-slate-900 hover:bg-slate-800"
                  >
                    Add note
                  </Button>
                </div>
                {selected.notes.length > 0 && (
                  <div className="mt-4 space-y-3">
                    {selected.notes.map((item) => (
                      <div className="rounded-lg bg-slate-50 p-3" key={item.id}>
                        <p className="text-sm leading-5 text-slate-700">
                          {item.text}
                        </p>
                        <p className="mt-2 text-xs text-muted-foreground">
                          {item.author} · {item.createdAt}
                        </p>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {canDeleteSelected && (
                <div className="border-t pt-5">
                  {deleteConfirmOpen ? (
                    <div className="rounded-lg border border-red-200 bg-red-50 p-4">
                      <p className="text-sm font-semibold text-red-800">
                        Delete this complaint?
                      </p>
                      <p className="mt-1 text-xs leading-5 text-red-700">
                        This removes the report and its uploaded evidence
                        permanently.
                      </p>
                      <div className="mt-3 flex gap-2">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={deleteSelected}
                          disabled={deleting}
                        >
                          <Trash2 className="mr-1.5 h-3.5 w-3.5" />
                          {deleting ? "Deleting…" : "Confirm delete"}
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setDeleteConfirmOpen(false)}
                          disabled={deleting}
                        >
                          Cancel
                        </Button>
                      </div>
                    </div>
                  ) : (
                    <Button
                      variant="ghost"
                      className="gap-2 text-red-600 hover:bg-transparent hover:text-red-700"
                      onClick={() => setDeleteConfirmOpen(true)}
                    >
                      <Trash2 className="h-4 w-4" />
                      Delete complaint
                    </Button>
                  )}
                </div>
              )}
            </div>
          </aside>
        </div>
      )}

      {/* Assign Work Order Modal */}
      {assignModalOpen && selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
          onClick={() => setAssignModalOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Assign Work Order"
            className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
                  <HardHat className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Assign Work Order</h3>
                  <p className="text-xs text-muted-foreground">
                    Link {selected.id} to a field repair crew
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setAssignModalOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <form onSubmit={handleAssignSubmit} className="space-y-4">
              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                  Select Repair Team & Leader *
                </label>
                <select
                  value={assignTeamId}
                  onChange={(e) => setAssignTeamId(e.target.value)}
                  className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-orange-500"
                  required
                >
                  {availableTeams.length === 0 ? (
                    <option value="">No teams found</option>
                  ) : (
                    availableTeams.map((team) => (
                      <option key={team.id} value={team.id}>
                        {team.name} ({team.zone}) — Lead: {team.lead} [{team.assignedComplaints.length} active jobs]
                      </option>
                    ))
                  )}
                </select>
                <p className="mt-1 text-[11px] text-muted-foreground">
                  Shows crew name, zone, leader, and current active workload.
                </p>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                    Priority
                  </label>
                  <select
                    value={assignPriority}
                    onChange={(e) => setAssignPriority(e.target.value)}
                    className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                    Expected Completion
                  </label>
                  <Input
                    type="datetime-local"
                    value={assignDeadline}
                    onChange={(e) => setAssignDeadline(e.target.value)}
                    className="text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                  Repair Instructions
                </label>
                <textarea
                  value={assignInstructions}
                  onChange={(e) => setAssignInstructions(e.target.value)}
                  placeholder="e.g. Clean debris, apply hot asphalt sealant, ensure traffic caution cones are set..."
                  className="min-h-20 w-full rounded-lg border border-input bg-background p-2.5 text-xs outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              {assignError && (
                <div className="rounded-lg bg-red-50 p-2.5 text-xs font-medium text-red-700">
                  {assignError}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setAssignModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={assignSubmitting || !assignTeamId}
                  className="bg-orange-500 hover:bg-orange-600 gap-1.5 text-white"
                >
                  <CheckCircle2 className="h-4 w-4" />
                  {assignSubmitting ? "Assigning…" : "Confirm Assignment"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reassign Work Order Modal */}
      {reassignModalOpen && selected && activeAssignment && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4"
          onClick={() => setReassignModalOpen(false)}
        >
          <div
            role="dialog"
            aria-modal="true"
            aria-label="Reassign Work Order"
            className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl space-y-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between border-b pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-orange-100 text-orange-600">
                  <RefreshCw className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-slate-900">Reassign Work Order</h3>
                  <p className="text-xs text-muted-foreground">
                    Transfer {activeAssignment.workOrderNumber} to another crew
                  </p>
                </div>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setReassignModalOpen(false)}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            <form onSubmit={handleReassignSubmit} className="space-y-4">
              <div className="rounded-lg bg-slate-50 p-3 text-xs border border-slate-200">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">
                  Currently Assigned To
                </span>
                <p className="font-semibold text-slate-800">
                  {activeAssignment.teamName} · Lead: {activeAssignment.teamLeadName}
                </p>
              </div>

              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                  Select New Repair Team *
                </label>
                <select
                  value={reassignTeamId}
                  onChange={(e) => setReassignTeamId(e.target.value)}
                  className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-orange-500"
                  required
                >
                  {availableTeams.map((team) => (
                    <option key={team.id} value={team.id}>
                      {team.name} ({team.zone}) — Lead: {team.lead} [{team.assignedComplaints.length} active jobs]
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                  Reason for Reassignment *
                </label>
                <textarea
                  value={reassignReason}
                  onChange={(e) => setReassignReason(e.target.value)}
                  placeholder="Explain why this work order is being transferred (e.g. crew overload, equipment breakdown, zone redistribution)..."
                  className="min-h-20 w-full rounded-lg border border-input bg-background p-2.5 text-xs outline-none focus:ring-2 focus:ring-orange-500"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                    Priority
                  </label>
                  <select
                    value={reassignPriority}
                    onChange={(e) => setReassignPriority(e.target.value)}
                    className="h-10 w-full rounded-lg border border-input bg-background px-3 text-sm outline-none focus:ring-2 focus:ring-orange-500"
                  >
                    <option value="CRITICAL">Critical</option>
                    <option value="HIGH">High</option>
                    <option value="MEDIUM">Medium</option>
                    <option value="LOW">Low</option>
                  </select>
                </div>

                <div>
                  <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                    Expected Completion
                  </label>
                  <Input
                    type="datetime-local"
                    value={reassignDeadline}
                    onChange={(e) => setReassignDeadline(e.target.value)}
                    className="text-xs"
                  />
                </div>
              </div>

              <div>
                <label className="text-xs font-bold uppercase tracking-wider text-slate-700 block mb-1.5">
                  Updated Repair Instructions
                </label>
                <textarea
                  value={reassignInstructions}
                  onChange={(e) => setReassignInstructions(e.target.value)}
                  placeholder="Additional instructions for the new crew..."
                  className="min-h-16 w-full rounded-lg border border-input bg-background p-2.5 text-xs outline-none focus:ring-2 focus:ring-orange-500"
                />
              </div>

              {reassignError && (
                <div className="rounded-lg bg-red-50 p-2.5 text-xs font-medium text-red-700">
                  {reassignError}
                </div>
              )}

              <div className="flex justify-end gap-2 pt-2 border-t">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setReassignModalOpen(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={reassignSubmitting || !reassignTeamId || !reassignReason.trim()}
                  className="bg-orange-500 hover:bg-orange-600 gap-1.5 text-white"
                >
                  <RefreshCw className="h-4 w-4" />
                  {reassignSubmitting ? "Reassigning…" : "Confirm Reassignment"}
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
