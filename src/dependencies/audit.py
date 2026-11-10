from fastapi import Request

from src.repository.audit import AuditRepository
from src.services.audit import AuditService
from src.services.auth import AuthService


def get_audit_service(request: Request) -> AuthService:
    collection = request.app.state.mongo_db["audit_logs"]
    repository = AuditRepository(collection=collection)

    return AuditService(repository)