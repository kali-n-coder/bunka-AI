import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.admin import router as admin_router
from app.api.chat import router as chat_router
from app.api.crowd_reports import router as crowd_reports_router
from app.api.exhibitions import router as exhibitions_router
from app.api.itinerary import router as itinerary_router
from app.api.routes import router as routes_router
from app.api.staff import router as staff_router
from app.api.wait_times import router as wait_times_router
from app.db.session import ensure_database_schema
from app.services.admin_state import install_memory_logging
from app.services.crowd_report_sync import crowd_report_sync_service


logging.basicConfig(level=logging.INFO)
install_memory_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hakuryu Anti-Gravity API",
    description="Backend API for Hakuryu Anti-Gravity AI Guide System",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(admin_router)
app.include_router(crowd_reports_router)
app.include_router(exhibitions_router)
app.include_router(wait_times_router)
app.include_router(routes_router)
app.include_router(itinerary_router)
app.include_router(staff_router)


@app.on_event("startup")
async def startup_event():
    ensure_database_schema()
    crowd_report_sync_service.start_background_sync()


@app.on_event("shutdown")
async def shutdown_event():
    await crowd_report_sync_service.stop_background_sync()


@app.get("/health")
async def health_check():
    return {"status": "healthy", "version": "0.1.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Global exception: %s", exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)},
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
