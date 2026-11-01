import uuid
from datetime import datetime, date
from src.models.base import BaseModel
from sqlalchemy import (
    UniqueConstraint,
    CheckConstraint,
    Index,
    ForeignKey,
    Date,
    DateTime,
    Enum as SQLAlchemyEnum,
    text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.enums import AttendanceStatus

class Attendance(BaseModel):
    __tablename__ = "attendance"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name="uq_employee_attendance_date"
        ),
        CheckConstraint(
            "check_out IS NULL OR check_out > check_in",
            name="ck_attendance_checkout_after_checkin"
        ),
        Index(
            "idx_attendance_employee_date",
            "employee_id",
            "attendance_date"
        )
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("employees.id", ondelete="RESTRICT"),
        nullable=False   
    )

    attendance_date: Mapped[date] = mapped_column(
        Date,
        nullable=False
    )

    check_in: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    check_out: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    status: Mapped[AttendanceStatus] = mapped_column(
        SQLAlchemyEnum(
            AttendanceStatus,
            name="attendance_status",
            value_callable=lambda enum: [
                item.value for item in enum
            ]
        ),
        default=AttendanceStatus.PRESENT,
        server_default=text("'PRESENT'"),
        nullable=False
    )

    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="attendance_records"
    )