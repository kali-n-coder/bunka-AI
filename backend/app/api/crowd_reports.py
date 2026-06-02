from fastapi import APIRouter, Depends

from app.api.admin import verify_admin_pin
from app.schemas.crowd_report import CrowdReportSummary, CrowdReportSyncResponse
from app.services.crowd_report_sync import crowd_report_sync_service

router = APIRouter(prefix="/api/v1", tags=["Crowd Reports"])


@router.get("/crowd-reports/summary", response_model=list[CrowdReportSummary])
async def crowd_report_summary():
    return await crowd_report_sync_service.summary()


@router.post(
    "/admin/crowd-reports/sync",
    response_model=CrowdReportSyncResponse,
    dependencies=[Depends(verify_admin_pin)],
)
async def sync_crowd_reports():
    return await crowd_report_sync_service.sync()
