from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator

from app.models.enums import AssignmentStatus, ComplaintStatus, SeverityLevel, TeamAvailability


class TeamCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=160)
    lead_name: str = Field(min_length=2, max_length=160)
    phone: str = Field(min_length=10, max_length=10, pattern=r"^\d{10}$")
    email: EmailStr
    zone: str = Field(default="West Zone", min_length=2, max_length=80)
    members: int = Field(default=4, ge=1, le=10_000)
    specialties: list[str] = Field(default_factory=list, max_length=30)
    availability: TeamAvailability = TeamAvailability.AVAILABLE


class TeamUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=160)
    lead_name: str | None = Field(default=None, min_length=2, max_length=160)
    phone: str | None = Field(default=None, min_length=10, max_length=10, pattern=r"^\d{10}$")
    email: EmailStr | None = None
    zone: str | None = Field(default=None, min_length=2, max_length=80)
    members: int | None = Field(default=None, ge=1, le=10_000)
    specialties: list[str] | None = Field(default=None, max_length=30)
    availability: TeamAvailability | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def require_a_change(self):
        values = (self.name, self.lead_name, self.phone, self.email, self.zone, self.members, self.specialties, self.availability, self.is_active)
        if all(value is None for value in values):
            raise ValueError("At least one team field must be provided")
        return self


class TeamAvailabilityUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    availability: TeamAvailability


class TeamLocationUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    address: str | None = None


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID
    name: str
    lead_name: str
    phone: str
    email: EmailStr
    zone: str
    members: int
    specialties: list[str]
    availability: TeamAvailability
    lead_user_id: UUID | None = None
    has_account: bool = False
    current_latitude: float | None = None
    current_longitude: float | None = None
    last_location_update: datetime | None = None
    current_location_address: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    assigned_work_count: int = 0


class TeamListResponse(BaseModel):
    items: list[TeamResponse]
    total: int
    page: int
    page_size: int


class AssignedComplaintResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    complaint_number: str
    status: ComplaintStatus
    severity: SeverityLevel
    title: str
    assigned_team_id: UUID | None
    created_at: datetime
    updated_at: datetime


class TeamAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    complaint_id: UUID
    team_id: UUID
    assigned_by_id: UUID
    status: AssignmentStatus
    released_at: datetime | None
    created_at: datetime
    updated_at: datetime


class TeamMemberCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=2, max_length=160)
    employee_id: str = Field(min_length=1, max_length=80)
    phone: str | None = Field(default=None, min_length=10, max_length=10, pattern=r"^\d{10}$")
    skills: list[str] = Field(default_factory=list, max_length=30)


class TeamMemberUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str | None = Field(default=None, min_length=2, max_length=160)
    employee_id: str | None = Field(default=None, min_length=1, max_length=80)
    phone: str | None = Field(default=None, min_length=10, max_length=10, pattern=r"^\d{10}$")
    skills: list[str] | None = Field(default=None, max_length=30)
    is_active: bool | None = None


class TeamMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    team_id: UUID
    name: str
    employee_id: str
    phone: str | None
    skills: list[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TeamLeaderCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    full_name: str = Field(min_length=2, max_length=160)
    email: str = Field(min_length=5, max_length=320)
    phone: str = Field(min_length=10, max_length=15)
    password: str = Field(min_length=6, max_length=128)


class TeamLeaderAssign(BaseModel):
    model_config = ConfigDict(extra="ignore")

    user_id: UUID


class AvailableLeaderResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    phone: str | None
    is_active: bool


class TeamWorkStatsResponse(BaseModel):
    team_id: UUID
    team_name: str
    active_assignments: int = 0
    completed_assignments: int = 0
    delayed_assignments: int = 0
    pending_assignments: int = 0
