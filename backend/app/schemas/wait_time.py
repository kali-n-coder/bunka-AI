from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class WaitTimeUpdate(BaseModel):
    current_wait_minutes: int = Field(..., ge=0, le=240)


class WaitTimeResponse(BaseModel):
    id: int
    exhibition_id: int
    current_wait_minutes: int
    updated_at: Optional[datetime] = None
    exhibition_name: Optional[str] = None
    category: Optional[str] = None
    location_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    recommended_for: Optional[str] = None
    cautions: Optional[str] = None
    stage_start_time: Optional[str] = None
    ticket_status: Optional[str] = None
    capacity_status: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
