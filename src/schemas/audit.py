from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogCreate(BaseModel):
    actor_user_id: str | None = None
    action: str = Field(min_length=1, max_length=100)
    entity_type: str = Field(min_length=1, max_length=100)
    entity_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    ip_address: str | None = None
    user_agent: str | None = None
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

class AuditLogResponse(AuditLogCreate):
    id: str
    model_config = ConfigDict(from_attributes=True)