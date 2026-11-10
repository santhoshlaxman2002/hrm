from pymongo.asynchronous.collection import AsyncCollection

from src.schemas.audit import AuditLogCreate

class AuditRepository:
    def __init__(self, collection: AsyncCollection):
        self.collection = collection

    async def create(self, audit_data: AuditLogCreate) -> str:
        document = audit_data.model_dump()
        result = await self.collection.insert_one(document=document)

        return str(result.inserted_id)

    async def list_logs(
        self,
        page: int = 1,
        page_size: int = 20,
        actor_user_id: str | None = None,
        action: str | None = None,
    ) -> list[dict]:
            filters = {}
            if actor_user_id:
                 filters["actor_user_id"] = actor_user_id

            if action:
                 filters["action"] = action

            skip = (page - 1) * page_size

            cursor = (
                self.collection.find(filters)
                .sort("created_at", -1)
                .skip(skip)
                .limit(page_size)
            )

            return await cursor.to_list(length=page)