from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session as DBSession

from app.core.security import hash_password
from app.database.dependencies import get_db
from app.dependencies.auth import get_current_auth
from app.models import Complaint, RepairTeam, TeamAssignment, TeamMember, User, UserRole
from app.models.enums import TeamAvailability
from app.schemas.teams import (
    AssignedComplaintResponse,
    AvailableLeaderResponse,
    TeamAssignmentResponse,
    TeamAvailabilityUpdate,
    TeamCreate,
    TeamLeaderAssign,
    TeamLeaderCreate,
    TeamListResponse,
    TeamMemberCreate,
    TeamMemberResponse,
    TeamMemberUpdate,
    TeamResponse,
    TeamUpdate,
    TeamWorkStatsResponse,
)
from app.services.auth import AuthenticatedSession, normalize_email, require_roles

router = APIRouter(prefix="/teams", tags=["repair-teams"])


def _get_team(db: DBSession, team_id: UUID) -> RepairTeam:
    team = db.get(RepairTeam, team_id)
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair team not found")
    return team


def _enrich_team(db: DBSession, team: RepairTeam, assigned_work_count: int | None = None) -> TeamResponse:
    if assigned_work_count is None:
        assigned_work_count = db.scalar(
            select(func.count()).select_from(Complaint).where(Complaint.assigned_team_id == team.id)
        ) or 0

    has_account = False
    if team.lead_user_id is not None:
        has_account = True
    elif team.email:
        u = db.scalar(select(User).where(func.lower(User.email) == team.email.strip().lower(), User.is_active.is_(True)))
        if u is not None:
            has_account = True
            team.lead_user_id = u.id

    resp = TeamResponse.model_validate(team)
    return resp.model_copy(
        update={
            "assigned_work_count": assigned_work_count,
            "has_account": has_account,
            "lead_user_id": team.lead_user_id,
        }
    )


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
def create_team(
    payload: TeamCreate,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> TeamResponse:
    team = RepairTeam(
        name=payload.name.strip(),
        lead_name=payload.lead_name.strip(),
        phone=payload.phone.strip(),
        email=str(payload.email).casefold(),
        zone=payload.zone.strip(),
        members=payload.members,
        specialties=[item.strip() for item in payload.specialties if item.strip()],
        availability=payload.availability,
    )
    # Check if a User with this email already exists
    existing_user = db.scalar(select(User).where(func.lower(User.email) == team.email))
    if existing_user and existing_user.role == UserRole.REPAIR_TEAM:
        team.lead_user_id = existing_user.id

    db.add(team)
    try:
        db.commit()
        db.refresh(team)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A repair team with this name already exists"
        ) from exc
    return _enrich_team(db, team, 0)


@router.get("/available-leaders", response_model=list[AvailableLeaderResponse])
def list_available_leaders(
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> list[AvailableLeaderResponse]:
    users = db.scalars(
        select(User).where(User.role == UserRole.REPAIR_TEAM, User.is_active.is_(True)).order_by(User.full_name)
    ).all()
    return [
        AvailableLeaderResponse(
            id=u.id,
            email=u.email,
            full_name=u.full_name,
            phone=u.phone,
            is_active=u.is_active,
        )
        for u in users
    ]


def _resolve_or_create_user_team(db: DBSession, user: User) -> RepairTeam:
    team = db.scalar(
        select(RepairTeam).where(
            or_(
                RepairTeam.lead_user_id == user.id,
                func.lower(RepairTeam.email) == user.email.strip().lower(),
            )
        )
    )
    if team is not None:
        if team.lead_user_id is None:
            team.lead_user_id = user.id
            db.commit()
            db.refresh(team)
        return team

    # 1. Try to link to an unassigned team
    unassigned = db.scalar(select(RepairTeam).where(RepairTeam.lead_user_id.is_(None)))
    if unassigned is not None:
        unassigned.lead_user_id = user.id
        if not unassigned.email:
            unassigned.email = user.email.strip().lower()
        if not unassigned.lead_name:
            unassigned.lead_name = user.full_name or "Team Lead"
        db.commit()
        db.refresh(unassigned)
        return unassigned

    # 2. Automatically create a team for this leader
    team_name = f"{user.full_name}'s Unit" if user.full_name else f"Team {user.email.split('@')[0].capitalize()}"
    new_team = RepairTeam(
        name=team_name,
        lead_name=user.full_name or "Team Lead",
        email=user.email.strip().lower(),
        phone=user.phone or "9876543210",
        specialties=["Pothole Repair", "Road Resurfacing"],
        availability=TeamAvailability.AVAILABLE,
        lead_user_id=user.id,
        zone="Central Zone",
        members=0,
    )
    db.add(new_team)
    db.commit()
    db.refresh(new_team)
    return new_team


@router.get("/my-team", response_model=TeamResponse)
def get_my_team(
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> TeamResponse:
    team = _resolve_or_create_user_team(db, auth.user)
    return _enrich_team(db, team)


@router.get("/my-team/members", response_model=list[TeamMemberResponse])
def get_my_team_members(
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> list[TeamMember]:
    team = _resolve_or_create_user_team(db, auth.user)
    return db.scalars(select(TeamMember).where(TeamMember.team_id == team.id).order_by(TeamMember.name)).all()


@router.post("/my-team/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def create_my_team_member(
    payload: TeamMemberCreate,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> TeamMember:
    team = _resolve_or_create_user_team(db, auth.user)
    member = TeamMember(
        team_id=team.id,
        name=payload.name.strip(),
        employee_id=payload.employee_id.strip(),
        phone=payload.phone.strip() if payload.phone else None,
        skills=[item.strip() for item in payload.skills if item.strip()],
    )
    db.add(member)
    team.members = (team.members or 0) + 1
    try:
        db.commit()
        db.refresh(member)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID already exists") from exc
    return member


@router.patch("/my-team/members/{member_id}", response_model=TeamMemberResponse)
def update_my_team_member(
    member_id: UUID,
    payload: TeamMemberUpdate,
    auth: AuthenticatedSession = Depends(require_roles(UserRole.REPAIR_TEAM, UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> TeamMember:
    team = _resolve_or_create_user_team(db, auth.user)
    member = db.scalar(select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team.id))
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")

    for field in ("name", "employee_id", "phone"):
        value = getattr(payload, field)
        if value is not None:
            setattr(member, field, value.strip())
    if payload.skills is not None:
        member.skills = [item.strip() for item in payload.skills if item.strip()]
    if payload.is_active is not None:
        member.is_active = payload.is_active
    try:
        db.commit()
        db.refresh(member)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID already exists") from exc
    return member


@router.get("", response_model=TeamListResponse)
def list_teams(
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    search: str | None = Query(default=None, min_length=1, max_length=160),
    availability: str | None = Query(default=None),
    is_active: bool | None = Query(default=None),
) -> TeamListResponse:
    filters = []
    if search:
        search_term = f"%{search.strip().casefold()}%"
        filters.append(
            func.lower(RepairTeam.name).like(search_term) | func.lower(RepairTeam.lead_name).like(search_term)
        )
    if availability:
        filters.append(RepairTeam.availability == availability.upper())
    if is_active is not None:
        filters.append(RepairTeam.is_active == is_active)
    total = db.scalar(select(func.count()).select_from(RepairTeam).where(*filters)) or 0
    team_rows = db.execute(
        select(RepairTeam, func.count(Complaint.id).label("assigned_work_count"))
        .outerjoin(Complaint, Complaint.assigned_team_id == RepairTeam.id)
        .where(*filters)
        .group_by(RepairTeam.id)
        .order_by(RepairTeam.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    items = [
        _enrich_team(db, team, assigned_work_count)
        for team, assigned_work_count in team_rows
    ]
    return TeamListResponse(items=items, total=total, page=page, page_size=page_size)


@router.get("/{team_id}", response_model=TeamResponse)
def get_team(
    team_id: UUID,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> TeamResponse:
    team = _get_team(db, team_id)
    return _enrich_team(db, team)


@router.post("/{team_id}/leader", response_model=TeamResponse)
def create_team_leader_account(
    team_id: UUID,
    payload: TeamLeaderCreate,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> TeamResponse:
    team = _get_team(db, team_id)
    normalized = normalize_email(str(payload.email))

    user = db.scalar(select(User).where(User.email == normalized))
    if user is not None:
        # If user exists, update password and role to REPAIR_TEAM
        user.password_hash = hash_password(payload.password)
        user.role = UserRole.REPAIR_TEAM
        user.full_name = payload.full_name.strip()
        user.phone = payload.phone.strip()
        user.is_active = True
    else:
        user = User(
            email=normalized,
            password_hash=hash_password(payload.password),
            full_name=payload.full_name.strip(),
            phone=payload.phone.strip(),
            role=UserRole.REPAIR_TEAM,
            is_active=True,
        )
        db.add(user)
        db.flush()

    team.lead_user_id = user.id
    team.lead_name = user.full_name
    team.email = user.email
    team.phone = user.phone or team.phone

    db.commit()
    db.refresh(team)
    return _enrich_team(db, team)


@router.post("/{team_id}/assign-leader", response_model=TeamResponse)
def assign_team_leader(
    team_id: UUID,
    payload: TeamLeaderAssign,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> TeamResponse:
    team = _get_team(db, team_id)
    user = db.get(User, payload.user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User account not found")

    user.role = UserRole.REPAIR_TEAM
    team.lead_user_id = user.id
    team.lead_name = user.full_name
    team.email = user.email
    if user.phone:
        team.phone = user.phone

    db.commit()
    db.refresh(team)
    return _enrich_team(db, team)


@router.get("/{team_id}/work-stats", response_model=TeamWorkStatsResponse)
def get_team_work_stats(
    team_id: UUID,
    _: AuthenticatedSession = Depends(get_current_auth),
    db: DBSession = Depends(get_db),
) -> TeamWorkStatsResponse:
    team = _get_team(db, team_id)
    assignments = db.scalars(select(TeamAssignment).where(TeamAssignment.team_id == team_id)).all()

    active = sum(1 for a in assignments if a.status == "ACTIVE" and a.work_status in ["PENDING", "ACCEPTED", "IN_PROGRESS"])
    pending = sum(1 for a in assignments if a.status == "ACTIVE" and a.work_status in ["PENDING", "ACCEPTED"])
    delayed = sum(1 for a in assignments if a.status == "ACTIVE" and a.work_status == "DELAYED")
    completed = sum(1 for a in assignments if a.work_status == "COMPLETED")

    return TeamWorkStatsResponse(
        team_id=team.id,
        team_name=team.name,
        active_assignments=active,
        completed_assignments=completed,
        delayed_assignments=delayed,
        pending_assignments=pending,
    )


@router.patch("/{team_id}", response_model=TeamResponse)
def update_team(
    team_id: UUID,
    payload: TeamUpdate,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> TeamResponse:
    team = _get_team(db, team_id)
    for field in ("name", "lead_name", "phone", "zone", "availability", "is_active"):
        value = getattr(payload, field)
        if value is not None:
            setattr(team, field, value.strip() if isinstance(value, str) else value)
    if payload.members is not None:
        team.members = payload.members
    if payload.specialties is not None:
        team.specialties = [item.strip() for item in payload.specialties if item.strip()]
    if payload.email is not None:
        team.email = str(payload.email).casefold()
    try:
        db.commit()
        db.refresh(team)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="A repair team with this name already exists"
        ) from exc
    return _enrich_team(db, team)


@router.patch("/{team_id}/availability", response_model=TeamResponse)
def update_team_availability(
    team_id: UUID,
    payload: TeamAvailabilityUpdate,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN, UserRole.REPAIR_TEAM)),
    db: DBSession = Depends(get_db),
) -> TeamResponse:
    team = _get_team(db, team_id)
    team.availability = payload.availability
    db.commit()
    db.refresh(team)
    return _enrich_team(db, team)


@router.delete("/{team_id}", response_model=dict[str, str])
def delete_team(
    team_id: UUID,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> dict[str, str]:
    team = _get_team(db, team_id)
    assignment_exists = db.scalar(
        select(func.count()).select_from(TeamAssignment).where(TeamAssignment.team_id == team.id)
    )
    complaint_exists = db.scalar(
        select(func.count()).select_from(Complaint).where(Complaint.assigned_team_id == team.id)
    )
    if assignment_exists or complaint_exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Teams with assignment history or assigned complaints cannot be deleted",
        )
    db.delete(team)
    db.commit()
    return {"message": "Repair team deleted"}


@router.get("/{team_id}/complaints", response_model=list[AssignedComplaintResponse])
def assigned_complaints(
    team_id: UUID,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> list[Complaint]:
    _get_team(db, team_id)
    return db.scalars(
        select(Complaint)
        .where(Complaint.assigned_team_id == team_id)
        .order_by(Complaint.created_at.desc())
    ).all()


@router.get("/{team_id}/assignments", response_model=list[TeamAssignmentResponse])
def assignment_history(
    team_id: UUID,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN)),
    db: DBSession = Depends(get_db),
) -> list[TeamAssignment]:
    _get_team(db, team_id)
    return db.scalars(
        select(TeamAssignment)
        .where(TeamAssignment.team_id == team_id)
        .order_by(TeamAssignment.created_at.desc())
    ).all()


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
def list_team_members(
    team_id: UUID,
    _: AuthenticatedSession = Depends(get_current_auth),
    db: DBSession = Depends(get_db),
) -> list[TeamMember]:
    _get_team(db, team_id)
    return db.scalars(select(TeamMember).where(TeamMember.team_id == team_id).order_by(TeamMember.name)).all()


@router.post("/{team_id}/members", response_model=TeamMemberResponse, status_code=status.HTTP_201_CREATED)
def create_team_member(
    team_id: UUID,
    payload: TeamMemberCreate,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN, UserRole.REPAIR_TEAM)),
    db: DBSession = Depends(get_db),
) -> TeamMember:
    _get_team(db, team_id)
    member = TeamMember(
        team_id=team_id,
        name=payload.name.strip(),
        employee_id=payload.employee_id.strip(),
        phone=payload.phone.strip() if payload.phone else None,
        skills=[item.strip() for item in payload.skills if item.strip()],
    )
    db.add(member)
    try:
        db.commit()
        db.refresh(member)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID already exists") from exc
    return member


@router.patch("/{team_id}/members/{member_id}", response_model=TeamMemberResponse)
def update_team_member(
    team_id: UUID,
    member_id: UUID,
    payload: TeamMemberUpdate,
    _: AuthenticatedSession = Depends(require_roles(UserRole.ADMIN, UserRole.REPAIR_TEAM)),
    db: DBSession = Depends(get_db),
) -> TeamMember:
    _get_team(db, team_id)
    member = db.scalar(select(TeamMember).where(TeamMember.id == member_id, TeamMember.team_id == team_id))
    if member is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Team member not found")
    for field in ("name", "employee_id", "phone"):
        value = getattr(payload, field)
        if value is not None:
            setattr(member, field, value.strip())
    if payload.skills is not None:
        member.skills = [item.strip() for item in payload.skills if item.strip()]
    if payload.is_active is not None:
        member.is_active = payload.is_active
    try:
        db.commit()
        db.refresh(member)
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee ID already exists") from exc
    return member
