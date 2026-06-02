from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel


CrowdStatus = Literal["empty", "short", "busy", "closed"]


class CrowdReportSummary(BaseModel):
    exhibition_id: int
    status: CrowdStatus
    label: str
    report_count: int
    last_reported_at: datetime
    source: str = "visitor"


class CrowdReportSyncResponse(BaseModel):
    enabled: bool
    synced: bool
    report_count: int = 0
    summary_count: int = 0
    last_synced_at: Optional[datetime] = None
    error: Optional[str] = None
