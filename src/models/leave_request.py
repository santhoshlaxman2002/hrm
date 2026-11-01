import uuid
from datetime import date, datetime
from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum as SQLAlchemyEnum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import BaseModel
from src.models.enums import LeaveRequestStatus

class LeaveRequest(BaseModel):
    __tablename__ = "leave_requests"

    __table_args__ = (
        CheckConstraint(
            "end_date >= start_date",
            name="ck_leave_end_after_start"
        ),
        CheckConstraint(
            "total_days > 0",
            name="ck_leave_request_days_positive"
        ),
        Index(
            "idx_leave_request_employee_status",
            "employee_id",
            "status"
        ),
        Index(
            "idx_leave_request_reviewer_status",
            "reviewed_by",
            "status"
        )
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False
    )

    leave_type_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("leave_types.id", ondelete="RESTRICT"),
        nullable=False
    )

    start_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    end_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    total_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True
    )

    status: Mapped[LeaveRequestStatus] = mapped_column(
        SQLAlchemyEnum(
            LeaveRequestStatus,
            name="leave_request_status",
            values_callable=lambda enum: [
                item.value for item in enum
            ]
        ),
        default=LeaveRequestStatus.PENDING,
        nullable=False
    )

    reviewed_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=True
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="leave_requests",
        foreign_keys=[employee_id]
    )

    leave_type: Mapped["LeaveType"] = relationship(
        "LeaveType",
        back_populates="leave_requests"
    )

    reviewer: Mapped["Employee | None"] = relationship(
        "Employee",
        back_populates="reviewed_leave_requests",
        foreign_keys=[reviewed_by]
    )