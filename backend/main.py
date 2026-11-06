from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from backend.database import initialize_database
from backend.routers import auth, booking_services, bookings, customers, dashboard, payments, reports, rooms, services


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(title="Hotel Management System API", description="Raw SQLite API for hotel operations", version="1.0.0", lifespan=lifespan)


@app.exception_handler(RequestValidationError)
async def request_validation_handler(request: Request, exc: RequestValidationError):
    if request.url.path == "/api/bookings" or request.url.path.startswith("/api/bookings/"):
        messages = [error.get("msg", "Invalid booking data") for error in exc.errors()]
        if any("check-out date" in message.lower() for message in messages):
            return JSONResponse(status_code=400, content={"detail": "Check-out date must be after check-in date."})
        return JSONResponse(status_code=400, content={"detail": messages[0] if messages else "Invalid booking data"})
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


app.include_router(auth.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(customers.router, prefix="/api")
app.include_router(rooms.router, prefix="/api")
app.include_router(bookings.router, prefix="/api")
app.include_router(booking_services.router, prefix="/api")
app.include_router(payments.router, prefix="/api")
app.include_router(services.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/")
def root():
    return {"message": "Hotel Management System API is running"}