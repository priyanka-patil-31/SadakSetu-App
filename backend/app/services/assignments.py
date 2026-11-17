from datetime import UTC, datetime
from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session as DBSession

from app.models import (
    Complaint,
    ComplaintImage,
    ComplaintStatus,
    ComplaintUpdate,
    Notification,
    RepairTeam,
    TeamAssignment,
    TeamAvailability,
    User,
    UserRole,
)
from app.schemas.assignments import AssignmentResponse
from app.services.audit import record_audit
from app.services.complaints import validate_status_transition
from app.services.notifications import create_notifications


def _generate_work_order_number() -> str:
    return f"WO-{datetime.now(UTC):%Y%m%d}-{uuid4().hex[:6].upper()}"


def _get_team_leader_user_ids(db: DBSession, team: RepairTeam) -> list[UUID]:
    user_ids: list[UUID] = []
    if team.lead_user_id:
        user_ids.append(team.lead_user_id)
    # Also find by email
    if team.email:
        leader_user = db.scalar(
            select(User).where(func.lower(User.email) == team.email.strip().lower(), User.is_active.is_(True))
        )
        if leader_user and leader_user.id not in user_ids:
            user_ids.append(leader_user.id)
    return user_ids


def _get_admin_user_ids(db: DBSession) -> list[UUID]:
    return list(
        db.scalars(select(User.id).where(User.role == UserRole.ADMIN, User.is_active.is_(True))).all()
    )


def enrich_assignment(db: DBSession, assignment: TeamAssignment) -> AssignmentResponse:
    complaint = assignment.complaint
    team = assignment.team

    complaint_photo_url = None
    if complaint and complaint.images:
        first_img = complaint.images[0]
        complaint_photo_url = f"/api/v1/complaints/{complaint.id}/images/{first_img.id}"
    elif complaint:
        img = db.scalar(
            select(ComplaintImage)
            .where(ComplaintImage.complaint_id == complaint.id)
            .order_by(ComplaintImage.created_at.asc())
        )
        if img:
            complaint_photo_url = f"/api/v1/complaints/{complaint.id}/images/{img.id}"

    addr = None
    lat = None
    lon = None
    if complaint and complaint.location:
        addr = complaint.location.address or complaint.location.area or complaint.location.zone
        lat = complaint.location.latitude
        lon = complaint.location.longitude

    resp = AssignmentResponse.model_validate(assignment)
    return resp.model_copy(
        update={
            "team_name": team.name if team else None,
            "team_lead_name": team.lead_name if team else None,
            "team_phone": team.phone if team else None,
            "complaint_number": complaint.complaint_number if complaint else None,
            "complaint_title": complaint.title if complaint else None,
            "complaint_description": complaint.description if complaint else None,
            "complaint_status": complaint.status.value if complaint else None,
            "complaint_severity": complaint.severity.value if complaint else None,
            "complaint_address": addr,
            "complaint_latitude": lat,
            "complaint_longitude": lon,
            "complaint_photo_url": complaint_photo_url,
        }
    )


def assign_complaint(
    db: DBSession,
    complaint_id: UUID,
    team_id: UUID,
    actor_id: UUID,
    priority: str | None = None,
    expected_completion_date: datetime | None = None,
    instructions: str | None = None,
    note: str | None = None,
) -> TeamAssignment:
    complaint = db.scalar(select(Complaint).where(Complaint.id == complaint_id).with_for_update())
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    team = db.scalar(select(RepairTeam).where(RepairTeam.id == team_id).with_for_update())
    if team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Repair team not found")
    if not team.is_active or team.availability == TeamAvailability.OFF_DUTY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Repair team is not available")
    if complaint.status in {ComplaintStatus.RESOLVED, ComplaintStatus.REJECTED}:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Terminal complaints cannot be assigned")

    active_assignments = db.scalars(
        select(TeamAssignment)
        .where(TeamAssignment.complaint_id == complaint.id, TeamAssignment.status == "ACTIVE")
        .with_for_update()
    ).all()

    now = datetime.now(UTC)
    previous_team_id = complaint.assigned_team_id
    for existing in active_assignments:
        existing.status = "RELEASED"
        existing.released_at = now

    old_status = complaint.status
    if complaint.status != ComplaintStatus.ASSIGNED:
        validate_status_transition(complaint.status, ComplaintStatus.ASSIGNED)
        complaint.status = ComplaintStatus.ASSIGNED

    complaint.assigned_team_id = team.id
    team.availability = TeamAvailability.ON_JOB

    eff_priority = (priority or (complaint.severity.value if complaint.severity else "MEDIUM")).upper()
    wo_number = _generate_work_order_number()

    assignment = TeamAssignment(
        complaint_id=complaint.id,
        team_id=team.id,
        assigned_by_id=actor_id,
        status="ACTIVE",
        work_order_number=wo_number,
        priority=eff_priority,
        expected_completion_date=expected_completion_date,
        instructions=instructions or note,
        work_status="PENDING",
        progress_percentage=0,
    )
    db.add(assignment)
    db.add(
        ComplaintUpdate(
            complaint_id=complaint.id,
            actor_id=actor_id,
            event_type="ASSIGNED",
            old_value=str(previous_team_id) if previous_team_id else old_status.value,
            new_value=str(team.id),
            note=f"Assigned to {team.name} ({wo_number}). Priority: {eff_priority}. {instructions or ''}".strip(),
        )
    )

    # Notify Citizen
    create_notifications(
        db,
        [complaint.reporter_id],
        "ASSIGNMENT",
        "Complaint assigned to repair team",
        f"Complaint {complaint.complaint_number} was assigned to {team.name}. Work Order: {wo_number}.",
        complaint_id=complaint.id,
        team_id=team.id,
    )

    # Notify Team Leader
    leader_ids = _get_team_leader_user_ids(db, team)
    if leader_ids:
        create_notifications(
            db,
            leader_ids,
            "WORK_ASSIGNMENT",
            f"New Work Assignment: {wo_number}",
            f"You have been assigned complaint {complaint.complaint_number} ({complaint.title}). Priority: {eff_priority}.",
            complaint_id=complaint.id,
            team_id=team.id,
        )

    record_audit(
        db,
        actor_id=actor_id,
        action="ASSIGN",
        entity_type="Complaint",
        entity_id=complaint.id,
        after_data={
            "team_id": str(team.id),
            "status": complaint.status.value,
            "work_order_number": wo_number,
            "priority": eff_priority,
        },
    )
    db.flush()
    return assignment


def reassign_complaint(
    db: DBSession,
    complaint_id: UUID,
    new_team_id: UUID,
    actor_id: UUID,
    reason: str,
    priority: str | None = None,
    expected_completion_date: datetime | None = None,
    instructions: str | None = None,
) -> TeamAssignment:
    complaint = db.scalar(select(Complaint).where(Complaint.id == complaint_id).with_for_update())
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    new_team = db.scalar(select(RepairTeam).where(RepairTeam.id == new_team_id).with_for_update())
    if new_team is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="New repair team not found")
    if not new_team.is_active or new_team.availability == TeamAvailability.OFF_DUTY:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Target repair team is not available")

    now = datetime.now(UTC)
    active_assignments = db.scalars(
        select(TeamAssignment)
        .where(TeamAssignment.complaint_id == complaint.id, TeamAssignment.status == "ACTIVE")
        .with_for_update()
    ).all()

    old_team_name = "previous team"
    for old_assign in active_assignments:
        old_assign.status = "RELEASED"
        old_assign.released_at = now
        old_assign.reassign_reason = reason
        if old_assign.team:
            old_team_name = old_assign.team.name
            old_leader_ids = _get_team_leader_user_ids(db, old_assign.team)
            if old_leader_ids:
                create_notifications(
                    db,
                    old_leader_ids,
                    "WORK_REASSIGNED",
                    f"Assignment Released: {old_assign.work_order_number or 'Work Order'}",
                    f"Work for complaint {complaint.complaint_number} was reassigned. Reason: {reason}",
                    complaint_id=complaint.id,
                    team_id=old_assign.team_id,
                )

    complaint.assigned_team_id = new_team.id
    complaint.status = ComplaintStatus.ASSIGNED
    new_team.availability = TeamAvailability.ON_JOB

    eff_priority = (priority or (complaint.severity.value if complaint.severity else "MEDIUM")).upper()
    wo_number = _generate_work_order_number()

    new_assignment = TeamAssignment(
        complaint_id=complaint.id,
        team_id=new_team.id,
        assigned_by_id=actor_id,
        status="ACTIVE",
        work_order_number=wo_number,
        priority=eff_priority,
        expected_completion_date=expected_completion_date,
        instructions=instructions,
        work_status="PENDING",
        progress_percentage=0,
        reassign_reason=reason,
    )
    db.add(new_assignment)
    db.add(
        ComplaintUpdate(
            complaint_id=complaint.id,
            actor_id=actor_id,
            event_type="REASSIGNED",
            old_value=old_team_name,
            new_value=new_team.name,
            note=f"Reassigned to {new_team.name} ({wo_number}). Reason: {reason}",
        )
    )

    # Notify Citizen
    create_notifications(
        db,
        [complaint.reporter_id],
        "ASSIGNMENT",
        "Complaint reassigned",
        f"Complaint {complaint.complaint_number} was reassigned to repair team {new_team.name}.",
        complaint_id=complaint.id,
        team_id=new_team.id,
    )

    # Notify New Team Leader
    new_leader_ids = _get_team_leader_user_ids(db, new_team)
    if new_leader_ids:
        create_notifications(
            db,
            new_leader_ids,
            "WORK_ASSIGNMENT",
            f"New Work Assignment: {wo_number}",
            f"Complaint {complaint.complaint_number} was assigned to your team. Reason: {reason}",
            complaint_id=complaint.id,
            team_id=new_team.id,
        )

    record_audit(
        db,
        actor_id=actor_id,
        action="REASSIGN",
        entity_type="Complaint",
        entity_id=complaint.id,
        after_data={
            "new_team_id": str(new_team.id),
            "reason": reason,
            "work_order_number": wo_number,
        },
    )
    db.flush()
    return new_assignment


def release_complaint_assignment(
    db: DBSession,
    complaint_id: UUID,
    actor_id: UUID,
    note: str | None,
) -> None:
    complaint = db.scalar(select(Complaint).where(Complaint.id == complaint_id).with_for_update())
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    active_assignments = db.scalars(
        select(TeamAssignment)
        .where(TeamAssignment.complaint_id == complaint.id, TeamAssignment.status == "ACTIVE")
        .with_for_update()
    ).all()
    if not active_assignments:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Complaint has no active assignment")
    now = datetime.now(UTC)
    for assignment in active_assignments:
        assignment.status = "RELEASED"
        assignment.released_at = now
    previous_team_id = complaint.assigned_team_id
    complaint.assigned_team_id = None
    if complaint.status == ComplaintStatus.ASSIGNED:
        complaint.status = ComplaintStatus.UNDER_REVIEW
        new_status = ComplaintStatus.UNDER_REVIEW.value
    else:
        new_status = complaint.status.value
    db.add(
        ComplaintUpdate(
            complaint_id=complaint.id,
            actor_id=actor_id,
            event_type="ASSIGNMENT_RELEASED",
            old_value=str(previous_team_id) if previous_team_id else None,
            new_value=new_status,
            note=note,
        )
    )
    create_notifications(
        db,
        [complaint.reporter_id],
        "ASSIGNMENT_RELEASED",
        "Complaint assignment released",
        f"Complaint {complaint.complaint_number} is back in operational review.",
        complaint_id=complaint.id,
    )
    record_audit(
        db,
        actor_id=actor_id,
        action="RELEASE_ASSIGNMENT",
        entity_type="Complaint",
        entity_id=complaint.id,
        after_data={"status": complaint.status.value},
    )


def accept_assignment(db: DBSession, assignment_id: UUID, actor: User) -> TeamAssignment:
    assignment = db.scalar(select(TeamAssignment).where(TeamAssignment.id == assignment_id).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    assignment.work_status = "ACCEPTED"
    assignment.progress_percentage = max(5, assignment.progress_percentage or 0)

    db.add(
        ComplaintUpdate(
            complaint_id=assignment.complaint_id,
            actor_id=actor.id,
            event_type="WORK_ACCEPTED",
            note=f"Team Leader {actor.full_name} accepted work order {assignment.work_order_number or ''}.",
        )
    )

    admin_ids = _get_admin_user_ids(db)
    create_notifications(
        db,
        admin_ids,
        "WORK_ACCEPTED",
        f"Work Accepted: {assignment.work_order_number or 'Work Order'}",
        f"Team Leader {actor.full_name} accepted work for complaint {assignment.complaint.complaint_number if assignment.complaint else ''}.",
        complaint_id=assignment.complaint_id,
        team_id=assignment.team_id,
    )
    db.flush()
    return assignment


def start_repair(db: DBSession, assignment_id: UUID, actor: User) -> TeamAssignment:
    assignment = db.scalar(select(TeamAssignment).where(TeamAssignment.id == assignment_id).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    assignment.work_status = "IN_PROGRESS"
    assignment.progress_percentage = max(15, assignment.progress_percentage or 0)

    complaint = db.scalar(select(Complaint).where(Complaint.id == assignment.complaint_id).with_for_update())
    if complaint and complaint.status != ComplaintStatus.IN_PROGRESS:
        complaint.status = ComplaintStatus.IN_PROGRESS

    db.add(
        ComplaintUpdate(
            complaint_id=assignment.complaint_id,
            actor_id=actor.id,
            event_type="REPAIR_STARTED",
            note="Repair team has started physical work on-site.",
        )
    )

    if complaint:
        create_notifications(
            db,
            [complaint.reporter_id],
            "STATUS_CHANGE",
            "Repair work in progress",
            f"The repair team has arrived on site and started repairing complaint {complaint.complaint_number}.",
            complaint_id=complaint.id,
            team_id=assignment.team_id,
        )

    admin_ids = _get_admin_user_ids(db)
    create_notifications(
        db,
        admin_ids,
        "WORK_STARTED",
        f"Repair Started: {assignment.work_order_number or 'Work Order'}",
        f"Team {assignment.team.name if assignment.team else ''} started repair on {complaint.complaint_number if complaint else ''}.",
        complaint_id=assignment.complaint_id,
        team_id=assignment.team_id,
    )
    db.flush()
    return assignment


def update_progress(
    db: DBSession,
    assignment_id: UUID,
    actor: User,
    progress_percentage: int,
    notes: str | None = None,
) -> TeamAssignment:
    assignment = db.scalar(select(TeamAssignment).where(TeamAssignment.id == assignment_id).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    assignment.progress_percentage = progress_percentage
    if notes:
        assignment.progress_notes = notes
    if assignment.work_status in {"PENDING", "ACCEPTED", "DELAYED"}:
        assignment.work_status = "IN_PROGRESS"

    db.add(
        ComplaintUpdate(
            complaint_id=assignment.complaint_id,
            actor_id=actor.id,
            event_type="PROGRESS_UPDATE",
            note=f"Progress updated to {progress_percentage}%: {notes or 'In progress'}",
        )
    )

    admin_ids = _get_admin_user_ids(db)
    create_notifications(
        db,
        admin_ids,
        "WORK_PROGRESS",
        f"Progress Update: {assignment.work_order_number or 'Work Order'} ({progress_percentage}%)",
        f"Team Leader {actor.full_name} reported {progress_percentage}% completion. {notes or ''}".strip(),
        complaint_id=assignment.complaint_id,
        team_id=assignment.team_id,
    )
    db.flush()
    return assignment


def report_delay(
    db: DBSession,
    assignment_id: UUID,
    actor: User,
    delay_reason: str,
) -> TeamAssignment:
    assignment = db.scalar(select(TeamAssignment).where(TeamAssignment.id == assignment_id).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    assignment.work_status = "DELAYED"
    assignment.delay_reason = delay_reason

    db.add(
        ComplaintUpdate(
            complaint_id=assignment.complaint_id,
            actor_id=actor.id,
            event_type="DELAY_REPORTED",
            note=f"Delay reported by team lead: {delay_reason}",
        )
    )

    admin_ids = _get_admin_user_ids(db)
    create_notifications(
        db,
        admin_ids,
        "WORK_DELAYED",
        f"Work Delayed: {assignment.work_order_number or 'Work Order'}",
        f"Team Leader {actor.full_name} reported a delay: {delay_reason}",
        complaint_id=assignment.complaint_id,
        team_id=assignment.team_id,
    )
    db.flush()
    return assignment


def update_assigned_members(
    db: DBSession,
    assignment_id: UUID,
    actor: User,
    assigned_member_ids: list[str],
) -> TeamAssignment:
    assignment = db.scalar(select(TeamAssignment).where(TeamAssignment.id == assignment_id).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    assignment.assigned_member_ids = assigned_member_ids
    db.flush()
    return assignment


def submit_completion(
    db: DBSession,
    assignment_id: UUID,
    actor: User,
    completion_notes: str | None,
    before_photos: list[str],
    after_photos: list[str],
) -> TeamAssignment:
    assignment = db.scalar(select(TeamAssignment).where(TeamAssignment.id == assignment_id).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    assignment.work_status = "COMPLETION_SUBMITTED"
    assignment.progress_percentage = 100
    assignment.completion_submitted_at = datetime.now(UTC)
    if completion_notes:
        assignment.completion_notes = completion_notes
    if before_photos:
        assignment.before_photos = before_photos
    if after_photos:
        assignment.after_photos = after_photos

    complaint = assignment.complaint
    db.add(
        ComplaintUpdate(
            complaint_id=assignment.complaint_id,
            actor_id=actor.id,
            event_type="COMPLETION_SUBMITTED",
            note="Team submitted completion evidence for Admin verification.",
        )
    )

    admin_ids = _get_admin_user_ids(db)
    create_notifications(
        db,
        admin_ids,
        "COMPLETION_SUBMITTED",
        f"Verification Required: {assignment.work_order_number or 'Work Order'}",
        f"Team {assignment.team.name if assignment.team else ''} completed repair on {complaint.complaint_number if complaint else ''}. Review photos and verify.",
        complaint_id=assignment.complaint_id,
        team_id=assignment.team_id,
    )
    db.flush()
    return assignment


def verify_completion(
    db: DBSession,
    assignment_id: UUID,
    actor: User,
    approved: bool,
    note: str | None = None,
) -> TeamAssignment:
    assignment = db.scalar(select(TeamAssignment).where(TeamAssignment.id == assignment_id).with_for_update())
    if assignment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")

    complaint = db.scalar(select(Complaint).where(Complaint.id == assignment.complaint_id).with_for_update())
    now = datetime.now(UTC)

    if approved:
        assignment.work_status = "COMPLETED"
        assignment.verified_at = now
        assignment.verified_by_id = actor.id

        if complaint:
            complaint.status = ComplaintStatus.RESOLVED

        # Check if team has other active jobs
        active_count = db.scalar(
            select(func.count())
            .select_from(TeamAssignment)
            .where(
                TeamAssignment.team_id == assignment.team_id,
                TeamAssignment.status == "ACTIVE",
                TeamAssignment.id != assignment.id,
                TeamAssignment.work_status.in_(["PENDING", "ACCEPTED", "IN_PROGRESS", "DELAYED", "COMPLETION_SUBMITTED"]),
            )
        ) or 0
        if active_count == 0 and assignment.team:
            assignment.team.availability = TeamAvailability.AVAILABLE

        db.add(
            ComplaintUpdate(
                complaint_id=assignment.complaint_id,
                actor_id=actor.id,
                event_type="VERIFIED_AND_RESOLVED",
                old_value=ComplaintStatus.IN_PROGRESS.value,
                new_value=ComplaintStatus.RESOLVED.value,
                note=f"Admin verified completion: {note or 'Repair approved and closed'}",
            )
        )

        # Notify Citizen
        if complaint:
            create_notifications(
                db,
                [complaint.reporter_id],
                "STATUS_CHANGE",
                "Road repair resolved and verified!",
                f"Your complaint {complaint.complaint_number} ({complaint.title}) has been verified and marked as RESOLVED. Thank you!",
                complaint_id=complaint.id,
                team_id=assignment.team_id,
            )

        # Notify Team Leader
        if assignment.team:
            leader_ids = _get_team_leader_user_ids(db, assignment.team)
            if leader_ids:
                create_notifications(
                    db,
                    leader_ids,
                    "WORK_VERIFIED",
                    f"Work Order Approved: {assignment.work_order_number or ''}",
                    f"Admin has approved your repair completion on {complaint.complaint_number if complaint else ''}.",
                    complaint_id=assignment.complaint_id,
                    team_id=assignment.team_id,
                )
    else:
        # Re-opened for rework
        assignment.work_status = "IN_PROGRESS"
        if complaint:
            complaint.status = ComplaintStatus.IN_PROGRESS
        db.add(
            ComplaintUpdate(
                complaint_id=assignment.complaint_id,
                actor_id=actor.id,
                event_type="REWORK_REQUESTED",
                note=f"Admin requested rework: {note or 'Additional repair work needed'}",
            )
        )
        if assignment.team:
            leader_ids = _get_team_leader_user_ids(db, assignment.team)
            if leader_ids:
                create_notifications(
                    db,
                    leader_ids,
                    "REWORK_REQUESTED",
                    f"Rework Needed: {assignment.work_order_number or ''}",
                    f"Admin reviewed repair completion and requested rework: {note or 'Please review instructions'}",
                    complaint_id=assignment.complaint_id,
                    team_id=assignment.team_id,
                )

    db.flush()
    return assignment
