from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from src.core.mongodb import create_mongodb_client, initialize_mongodb_indexes
from src.core.redis import create_redis_client
from src.core.settings import get_settings
from src.middleware.rate_limit import RateLimitMiddleware
from src.routes.auth import router as auth_router
from src.routes.departments import router as department_router
from src.routes.employees import router as employee_router
from src.routes.attendance import router as attendance_router
from src.routes.leaves import router as leaves_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    redis_client = await create_redis_client()

    try:
        mongo_client = await create_mongodb_client()
    except Exception:
        await redis_client.aclose()
        raise

    app.state.redis = redis_client
    app.state.mongo_client = mongo_client
    app.state.mongo_db = mongo_client[settings.MONGODB_DATABASE]

    await initialize_mongodb_indexes(app.state.mongo_db)

    try:
        yield
    finally:
        await mongo_client.close()
        await redis_client.aclose()

app = FastAPI(title="People Hub API", lifespan=lifespan)

app.add_middleware(RateLimitMiddleware)

app.include_router(
    auth_router,
    prefix="/auth",
    tags=["Auth"]
)
app.include_router(
    department_router,
    prefix="/department",
    tags=["Department"]
)
app.include_router(
    employee_router,
    prefix="/employee",
    tags=["Employee"]
)
app.include_router(
    attendance_router,
    prefix="/attendance",
    tags=["Attendance"]
)
app.include_router(
    leaves_router,
    prefix="/leaves",
    tags=["Leave Management"]
)

@app.get("/")
async def health():
    return {
        "message": "App is Running"
    }

@app.get("/health/redis")
async def redis_health(request: Request):
    redis_client = request.app.state.redis

    is_connected = await redis_client.ping()

    return {
        "service": "redis",
        "connected": is_connected
    }