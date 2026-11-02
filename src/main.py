from src.routes.auth import router as auth_router
from fastapi import FastAPI

app = FastAPI(title="People Hub API")

app.include_router(
    auth_router,
    prefix="/auth"
)

@app.get("/")
async def health():
    return {
        "message": "App is Running"
    }