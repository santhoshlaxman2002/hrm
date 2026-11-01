import uuid
from datetime import datetime
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    String
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.models.base import BaseModel

class RefreshToken(BaseModel):
    __tablename__ = "refresh_tokens"

    __table_args__ = (
        Index(
            "idx_refresh_token_user",
            "user_id"
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False
    )

    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="refresh_tokens"
    )