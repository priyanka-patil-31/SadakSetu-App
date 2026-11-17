from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import AssignmentStatus


class AssignmentCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    team_id: UUID
    priority: str | None = Field(default="MEDIUM", max_length=20)
    expected_completion_date: datetime | None = None
    instructions: str | None = Field(default=None, max_length=5_000)
    note: str | None = Field(default=None, max_length=2_000)


class AssignmentReassign(BaseModel):
    model_config = ConfigDict(extra="ignore")

    team_id: UUID
    reason: str = Field(min_length=2, max_length=2_000)
    priority: str | None = Field(default=None, max_length=20)
    expected_completion_date: datetime | None = None
    instructions: str | None = Field(default=None, max_length=5_000)


class WorkOrderProgressUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    progress_percentage: int = Field(ge=0, le=100)
    progress_notes: str | None = Field(default=None, max_length=2_000)


class WorkOrderDelayReport(BaseModel):
    model_config = ConfigDict(extra="ignore")

    delay_reason: str = Field(min_length=3, max_length=2_000)


class WorkOrderMemberUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    assigned_member_ids: list[str] = Field(default_factory=list)


class WorkOrderPhotosUpdate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    stage: str = Field(default="BEFORE", max_length=20)
    photo_urls: list[str] = Field(default_factory=list)


class WorkOrderCompletionSubmit(BaseModel):
    model_config = ConfigDict(extra="ignore")

    completion_notes: str | None = Field(default=None, max_length=3_000)
    before_photos: list[str] = Field(default_factory=list)
    after_photos: list[str] = Field(default_factory=list)


class WorkOrderVerify(BaseModel):
    model_config = ConfigDict(extra="ignore")

    approved: bool = True
    note: str | None = Field(default=None, max_length=2_000)


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="ignore")

    id: UUID
    complaint_id: UUID
    team_id: UUID
    assigned_by_id: UUID
    status: AssignmentStatus
    released_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    work_order_number: str | None = None
    priority: str | None = "MEDIUM"
    expected_completion_date: datetime | None = None
    instructions: str | None = None
    work_status: str = "PENDING"
    progress_percentage: int = 0
    progress_notes: str | None = None
    delay_reason: str | None = None
    before_photos: list[str] = Field(default_factory=list)
    after_photos: list[str] = Field(default_factory=list)
    assigned_member_ids: list[str] = Field(default_factory=list)
    completion_notes: str | None = None
    completion_submitted_at: datetime | None = None
    verified_at: datetime | None = None
    verified_by_id: UUID | None = None
    reassign_reason: str | None = None

    # Context / Enriched Fields
    team_name: str | None = None
    team_lead_name: str | None = None
    team_phone: str | None = None
    complaint_number: str | None = None
    complaint_title: str | None = None
    complaint_description: str | None = None
    complaint_status: str | None = None
    complaint_severity: str | None = None
    complaint_address: str | None = None
    complaint_latitude: float | None = None
    complaint_longitude: float | None = None
    complaint_photo_url: str | None = None


class AssignmentHistoryResponse(BaseModel):
    items: list[AssignmentResponse]


class WorkMonitoringStats(BaseModel):
    total: int = 0
    pending: int = 0
    ongoing: int = 0
    delayed: int = 0
    completion_submitted: int = 0
    completed: int = 0
