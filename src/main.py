from fastapi import FastAPI
from src.routes.auth import router as auth_router
from src.routes.departments import router as department_router
from src.routes.employees import router as employee_router
from src.routes.attendance import router as attendance_router
from src.routes.leaves import router as leaves_router

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