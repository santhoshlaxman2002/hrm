import uuid
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import BaseModel

class LeaveBalance(BaseModel):
    __tablename__ = "leave_balances"

    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "leave_type_id",
            "year",
            name="uq_employee_leave_type_year"
        ),
        CheckConstraint(
            "total_days >= 0",
            name="ck_leave_total_days_positive"
        ),
        CheckConstraint(
            "used_days >= 0",
            name="ck_leave_used_days_positive"
        ),
        CheckConstraint(
            "used_days <= total_days",
            name="ck_leave_used_not_exceed_total"
        ),
        Index(
            "idx_leave_balance_employee_year",
            "employee_id",
            "year"
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

    year: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    total_days: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    used_days: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False
    )

    employee: Mapped["Employee"] = relationship(
        "Employee",
        back_populates="leave_balances"
    )

    leave_type: Mapped["LeaveType"] = relationship(
        "LeaveType",
        back_populates="leave_balances"
    )

    @property
    def remaining_days(self) -> int:
        return self.total_days - self.used_days