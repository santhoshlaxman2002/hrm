import logging

from fastapi import Request

from src.repository.audit import AuditRepository
from src.schemas.audit import AuditLogCreate


logger = logging.getLogger(__name__)

class AuditService:
    def __init__(self, repository: AuditRepository):
        self.repository = repository

    async def log_event(
        self,
        *,
        actor_user_id: str | None,
        action: str,
        entity_type: str,
        entity_id: str | None = None,
        metadata: dict | None = None,
        request: Request | None = None,
    ):
        try:
            audit_data = AuditLogCreate(
                actor_user_id=actor_user_id,
                action=action,
                entity_type=entity_type,
                entity_id=entity_id,
                metadata=metadata or {},
                ip_address=(
                    request.client.host
                    if request and request.client
                    else None
                ),
                user_agent=(
                    request.headers.get("user-agent")
                    if request
                    else None
                ),
            )

            await self.repository.create(audit_data=audit_data)
        except Exception:
            logger.exception(
                "Failed to write audit event: %s",
                action,
            )