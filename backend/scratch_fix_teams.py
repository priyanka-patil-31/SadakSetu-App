from sqlalchemy import create_engine, select, or_, func
from sqlalchemy.orm import Session
from app.models.entities import User, RepairTeam
from app.models.enums import UserRole, TeamAvailability

engine = create_engine('postgresql+psycopg://sadaksetu:change-me@localhost:5432/sadaksetu')
with Session(engine) as session:
    repair_users = session.scalars(select(User).where(User.role == UserRole.REPAIR_TEAM)).all()
    for u in repair_users:
        team = session.scalar(select(RepairTeam).where(
            or_(
                RepairTeam.lead_user_id == u.id,
                func.lower(RepairTeam.email) == u.email.strip().lower()
            )
        ))
        if not team:
            tname = f"{u.full_name}'s Unit" if u.full_name else f"Team {u.email.split('@')[0].capitalize()}"
            # Ensure unique name
            existing = session.scalar(select(RepairTeam).where(RepairTeam.name == tname))
            if existing:
                tname = f"{tname} ({u.email.split('@')[0]})"
            new_t = RepairTeam(
                name=tname,
                lead_name=u.full_name or 'Team Lead',
                email=u.email.strip().lower(),
                phone=u.phone or '9876543210',
                specialties=['Pothole Repair', 'Road Resurfacing'],
                availability=TeamAvailability.AVAILABLE,
                lead_user_id=u.id,
                zone='Central Zone',
                members=0,
            )
            session.add(new_t)
            session.commit()
            print(f'Created team for {u.email}: {tname} (id={new_t.id})')
        else:
            if team.lead_user_id is None:
                team.lead_user_id = u.id
                session.commit()
            print(f'User {u.email} already has team: {team.name} (id={team.id})')
