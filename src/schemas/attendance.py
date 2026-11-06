from datetime import date, datetime
from uuid import UUID
from pydantic import BaseModel, ConfigDict
from src.models.enums import AttendanceStatus

class AttendanceResponse(BaseModel):
    id: UUID
    employee_id: UUID
    attendance_date: date
    check_in: datetime
    check_out: datetime | None
    status: AttendanceStatus
    created_at: datetime
    updated_at: datetime

class AttendanceListResponse(BaseModel):
    items: list[AttendanceResponse]
    total: int
    skip: int
    limit: int