from fastapi import FastAPI
from src.routes.auth import router as auth_router
from src.routes.departments import router as department_router

app = FastAPI(title="People Hub API")

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

@app.get("/")
async def health():
    return {
        "message": "App is Running"
    }