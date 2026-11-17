from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Request, UploadFile, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session as DBSession, joinedload

from app.core.config import get_settings
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_auth
from app.models import Complaint, RepairTeam, TeamAssignment, UserRole
from app.schemas.assignments import (
    AssignmentCreate,
    AssignmentHistoryResponse,
    AssignmentReassign,
    AssignmentResponse,
    WorkMonitoringStats,
    WorkOrderCompletionSubmit,
    WorkOrderDelayReport,
    WorkOrderMemberUpdate,
    WorkOrderProgressUpdate,
    WorkOrderVerify,
)
from app.services.assignments import (
    accept_assignment,
    assign_complaint,
    enrich_assignment,
    reassign_complaint,
    release_complaint_assignment,
    report_delay,
    start_repair,
    submit_completion,
    update_assigned_members,
    update_progress,
    verify_completion,
)
from app.services.auth import AuthenticatedSession, require_roles
from app.storage.files import store_validated_image

router = APIRouter(prefix="/assignments", tags=["assignments"])


def _get_my_team_ids(db: DBSession, auth: AuthenticatedSession) -> list[UUID]:
    teams = db.scalars(
        select(RepairTeam).where(
            or_(
                RepairTeam.lead_user_id == auth.user.id,
                func.lower(RepairTeam.email) == auth.user.email.strip().lower(),
            )
        )
    ).all()
    return [t.id for t in teams]


@router.post(
    "/complaints/{complaint_id}",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_assignment(
    complaint_id: UUID,
    payload: AssignmentCreate,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = assign_complaint(
        db=db,
        complaint_id=complaint_id,
        team_id=payload.team_id,
        actor_id=auth.user.id,
        priority=payload.priority,
        expected_completion_date=payload.expected_completion_date,
        instructions=payload.instructions,
        note=payload.note,
    )
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post(
    "/complaints/{complaint_id}/reassign",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def reassign_work_order(
    complaint_id: UUID,
    payload: AssignmentReassign,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = reassign_complaint(
        db=db,
        complaint_id=complaint_id,
        new_team_id=payload.team_id,
        actor_id=auth.user.id,
        reason=payload.reason,
        priority=payload.priority,
        expected_completion_date=payload.expected_completion_date,
        instructions=payload.instructions,
    )
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post("/complaints/{complaint_id}/release", response_model=dict[str, str])
def release_assignment(
    complaint_id: UUID,
    note: str | None = None,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> dict[str, str]:
    release_complaint_assignment(db, complaint_id, auth.user.id, note)
    db.commit()
    return {"message": "Complaint assignment released"}


@router.get("/complaints/{complaint_id}", response_model=AssignmentHistoryResponse)
def complaint_assignment_history(
    complaint_id: UUID,
    auth: AuthenticatedSession = Depends(get_current_auth),
    db: DBSession = Depends(get_db),
) -> AssignmentHistoryResponse:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    if auth.user.role == UserRole.CITIZEN and complaint.reporter_id != auth.user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    items = db.scalars(
        select(TeamAssignment)
        .options(joinedload(TeamAssignment.complaint), joinedload(TeamAssignment.team))
        .where(TeamAssignment.complaint_id == complaint_id)
        .order_by(TeamAssignment.created_at.desc())
    ).all()
    return AssignmentHistoryResponse(items=[enrich_assignment(db, item) for item in items])


@router.get("/stats", response_model=WorkMonitoringStats)
def work_monitoring_stats(
    auth: AuthenticatedSession = Depends(get_current_auth),
    db: DBSession = Depends(get_db),
) -> WorkMonitoringStats:
    base_query = select(TeamAssignment)
    if auth.user.role == UserRole.REPAIR_TEAM:
        my_team_ids = _get_my_team_ids(db, auth)
        base_query = base_query.where(TeamAssignment.team_id.in_(my_team_ids))

    all_assignments = db.scalars(base_query).all()
    total = len(all_assignments)
    pending = sum(1 for a in all_assignments if a.status == "ACTIVE" and a.work_status in {"PENDING", "ACCEPTED"})
    ongoing = sum(1 for a in all_assignments if a.status == "ACTIVE" and a.work_status == "IN_PROGRESS")
    delayed = sum(1 for a in all_assignments if a.status == "ACTIVE" and a.work_status == "DELAYED")
    submitted = sum(1 for a in all_assignments if a.status == "ACTIVE" and a.work_status == "COMPLETION_SUBMITTED")
    completed = sum(1 for a in all_assignments if a.work_status == "COMPLETED")

    return WorkMonitoringStats(
        total=total,
        pending=pending,
        ongoing=ongoing,
        delayed=delayed,
        completion_submitted=submitted,
        completed=completed,
    )


@router.get("", response_model=list[AssignmentResponse])
def list_assignments(
    status_filter: str | None = Query(default=None, alias="status"),
    team_id: UUID | None = None,
    search: str | None = None,
    auth: AuthenticatedSession = Depends(get_current_auth),
    db: DBSession = Depends(get_db),
) -> list[AssignmentResponse]:
    query = (
        select(TeamAssignment)
        .options(
            joinedload(TeamAssignment.complaint).joinedload(Complaint.location),
            joinedload(TeamAssignment.complaint).joinedload(Complaint.images),
            joinedload(TeamAssignment.team),
        )
        .order_by(TeamAssignment.created_at.desc())
    )

    if auth.user.role == UserRole.REPAIR_TEAM:
        my_team_ids = _get_my_team_ids(db, auth)
        query = query.where(TeamAssignment.team_id.in_(my_team_ids))
    elif team_id:
        query = query.where(TeamAssignment.team_id == team_id)

    if status_filter and status_filter.upper() != "ALL":
        sf = status_filter.upper()
        if sf == "PENDING":
            query = query.where(TeamAssignment.status == "ACTIVE", TeamAssignment.work_status.in_(["PENDING", "ACCEPTED"]))
        elif sf in {"ONGOING", "IN_PROGRESS"}:
            query = query.where(TeamAssignment.status == "ACTIVE", TeamAssignment.work_status == "IN_PROGRESS")
        elif sf == "DELAYED":
            query = query.where(TeamAssignment.status == "ACTIVE", TeamAssignment.work_status == "DELAYED")
        elif sf in {"COMPLETION_SUBMITTED", "SUBMITTED"}:
            query = query.where(TeamAssignment.status == "ACTIVE", TeamAssignment.work_status == "COMPLETION_SUBMITTED")
        elif sf == "COMPLETED":
            query = query.where(TeamAssignment.work_status == "COMPLETED")
        elif sf == "ACTIVE":
            query = query.where(TeamAssignment.status == "ACTIVE")
        else:
            query = query.where(TeamAssignment.work_status == sf)

    assignments = db.scalars(query).unique().all()

    if search:
        s = search.strip().casefold()
        filtered = []
        for a in assignments:
            wo = (a.work_order_number or "").casefold()
            c_num = (a.complaint.complaint_number or "").casefold() if a.complaint else ""
            c_title = (a.complaint.title or "").casefold() if a.complaint else ""
            t_name = (a.team.name or "").casefold() if a.team else ""
            if s in wo or s in c_num or s in c_title or s in t_name:
                filtered.append(a)
        assignments = filtered

    return [enrich_assignment(db, a) for a in assignments]


@router.get("/my-work", response_model=list[AssignmentResponse])
def get_my_work(
    work_status: str | None = None,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> list[AssignmentResponse]:
    my_team_ids = _get_my_team_ids(db, auth)
    if not my_team_ids and auth.user.role == UserRole.REPAIR_TEAM:
        return []

    query = (
        select(TeamAssignment)
        .options(
            joinedload(TeamAssignment.complaint).joinedload(Complaint.location),
            joinedload(TeamAssignment.complaint).joinedload(Complaint.images),
            joinedload(TeamAssignment.team),
        )
        .order_by(TeamAssignment.created_at.desc())
    )
    if my_team_ids:
        query = query.where(TeamAssignment.team_id.in_(my_team_ids))

    if work_status and work_status.upper() != "ALL":
        ws = work_status.upper()
        if ws == "PENDING":
            query = query.where(TeamAssignment.status == "ACTIVE", TeamAssignment.work_status.in_(["PENDING", "ACCEPTED"]))
        elif ws in {"ONGOING", "IN_PROGRESS"}:
            query = query.where(TeamAssignment.status == "ACTIVE", TeamAssignment.work_status == "IN_PROGRESS")
        elif ws == "DELAYED":
            query = query.where(TeamAssignment.status == "ACTIVE", TeamAssignment.work_status == "DELAYED")
        elif ws in {"COMPLETION_SUBMITTED", "SUBMITTED"}:
            query = query.where(TeamAssignment.status == "ACTIVE", TeamAssignment.work_status == "COMPLETION_SUBMITTED")
        elif ws == "COMPLETED":
            query = query.where(TeamAssignment.work_status == "COMPLETED")
        else:
            query = query.where(TeamAssignment.work_status == ws)

    assignments = db.scalars(query).unique().all()
    return [enrich_assignment(db, a) for a in assignments]


@router.get("/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(
    assignment_id: UUID,
    auth: AuthenticatedSession = Depends(get_current_auth),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = db.execute(
        select(TeamAssignment)
        .options(
            joinedload(TeamAssignment.complaint).joinedload(Complaint.location),
            joinedload(TeamAssignment.complaint).joinedload(Complaint.images),
            joinedload(TeamAssignment.team),
        )
        .where(TeamAssignment.id == assignment_id)
    ).unique().scalar_one_or_none()

    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    if auth.user.role == UserRole.REPAIR_TEAM:
        my_team_ids = _get_my_team_ids(db, auth)
        if assignment.team_id not in my_team_ids:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return enrich_assignment(db, assignment)


@router.post("/{assignment_id}/accept", response_model=AssignmentResponse)
def accept_work_order(
    assignment_id: UUID,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = accept_assignment(db, assignment_id, auth.user)
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post("/{assignment_id}/start", response_model=AssignmentResponse)
def start_work_order(
    assignment_id: UUID,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = start_repair(db, assignment_id, auth.user)
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post("/{assignment_id}/progress", response_model=AssignmentResponse)
def update_work_order_progress(
    assignment_id: UUID,
    payload: WorkOrderProgressUpdate,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = update_progress(
        db, assignment_id, auth.user, payload.progress_percentage, payload.progress_notes
    )
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post("/{assignment_id}/delay", response_model=AssignmentResponse)
def report_work_order_delay(
    assignment_id: UUID,
    payload: WorkOrderDelayReport,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = report_delay(db, assignment_id, auth.user, payload.delay_reason)
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post("/{assignment_id}/members", response_model=AssignmentResponse)
def assign_team_members_to_work_order(
    assignment_id: UUID,
    payload: WorkOrderMemberUpdate,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = update_assigned_members(db, assignment_id, auth.user, payload.assigned_member_ids)
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post("/{assignment_id}/photos", response_model=AssignmentResponse)
async def upload_work_order_photo(
    assignment_id: UUID,
    request: Request,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = db.scalar(select(TeamAssignment).where(TeamAssignment.id == assignment_id).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    content_type = request.headers.get("content-type", "").lower()
    if "multipart/form-data" in content_type:
        form = await request.form()
        photo = form.get("photo")
        stage = str(form.get("stage") or "BEFORE").upper().strip()
        if not photo or not hasattr(photo, "read"):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No photo file provided")
        settings = get_settings()
        stored = await store_validated_image(photo, assignment.complaint_id, settings)
        photo_key = stored.storage_key
    elif "application/json" in content_type:
        body = await request.json()
        stage = (body.get("photo_type") or body.get("stage") or "BEFORE").upper().strip()
        photo_key = body.get("photo_url") or (body.get("photo_urls") or [""])[0]
        if not photo_key:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="photo_url is required")
    else:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Unsupported content type")

    if stage == "BEFORE":
        current = list(assignment.before_photos or [])
        current.append(photo_key)
        assignment.before_photos = current
    else:
        current = list(assignment.after_photos or [])
        current.append(photo_key)
        assignment.after_photos = current

    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post("/{assignment_id}/submit-completion", response_model=AssignmentResponse)
def submit_work_order_completion(
    assignment_id: UUID,
    payload: WorkOrderCompletionSubmit,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = submit_completion(
        db,
        assignment_id,
        auth.user,
        payload.completion_notes,
        payload.before_photos,
        payload.after_photos,
    )
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)


@router.post("/{assignment_id}/verify", response_model=AssignmentResponse)
def verify_work_order_completion(
    assignment_id: UUID,
    payload: WorkOrderVerify,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> AssignmentResponse:
    assignment = verify_completion(db, assignment_id, auth.user, payload.approved, payload.note)
    db.commit()
    db.refresh(assignment)
    return enrich_assignment(db, assignment)
