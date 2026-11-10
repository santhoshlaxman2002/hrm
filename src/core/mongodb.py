from pymongo import AsyncMongoClient
from pymongo.server_api import ServerApi

from src.core.settings import get_settings


settings = get_settings()

async def create_mongodb_client() -> AsyncMongoClient:
    client = AsyncMongoClient(
        settings.MONGODB_URL.get_secret_value(),
        server_api=ServerApi("1"),
        serverSelectionTimeoutMS=5000,
        connectTimeoutMS=5000,
    )

    await client.admin.command("ping")

    return client

async def initialize_mongodb_indexes(database):
    collection = database["audit_logs"]

    await collection.create_index(
        [("actor_user_id", 1), ("created_at", -1)]
    )

    await collection.create_index(
        [("entity_type", 1), ("entity_id", 1)]
    )

    await collection.create_index(
        [("action", 1), ("created_at", -1)]
    )

    await collection.create_index(
        [("created_at", -1)]
    )