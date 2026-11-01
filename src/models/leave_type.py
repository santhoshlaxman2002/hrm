from sqlalchemy import Boolean, Integer, String, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.models.base import BaseModel

class LeaveType(BaseModel):
    __tablename__ = "leave_types"

    __table_args__ = (
        CheckConstraint(
            "annual_allowance >= 0",
            name="ck_leave_type_allowance_positive"
        ),
    )

    name: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )

    annual_allowance: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False
    )

    leave_balances: Mapped[list["LeaveBalance"]] = relationship(
        "LeaveBalance",
        back_populates="leave_type"
    )

    leave_requests: Mapped[list["LeaveRequest"]] = relationship(
        "LeaveRequest",
        back_populates="leave_type"
    )