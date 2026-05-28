from typing import List, Optional

from pydantic import BaseModel, Field


class DistanceResponse(BaseModel):
    from_id: int
    to_id: int
    distance: float
    estimated_walk_minutes: int
    path: List[str]


class RouteEstimateRequest(BaseModel):
    exhibition_ids: List[int] = Field(..., min_length=2)


class ItineraryRequest(BaseModel):
    exhibition_ids: List[int] = Field(..., min_length=1)
    start_exhibition_id: Optional[int] = None
    end_exhibition_id: Optional[int] = None
    available_minutes: int = Field(120, ge=1)
    include_wait_times: bool = True


class ItineraryStop(BaseModel):
    exhibition_id: int
    exhibition_name: str
    wait_minutes: int
    visit_minutes: int
    travel_minutes_from_previous: int
    elapsed_minutes: int


class ItineraryResponse(BaseModel):
    stops: List[ItineraryStop]
    total_minutes: int
    total_travel_minutes: int = 0
    total_wait_minutes: int = 0
    total_visit_minutes: int = 0
    return_travel_minutes: int = 0
    skipped_exhibition_ids: List[int]
    note: str


class StaffLoginRequest(BaseModel):
    exhibition_id: int
    pin: str


class StaffLoginResponse(BaseModel):
    ok: bool
    message: str
    exhibition_id: int
    exhibition_name: Optional[str] = None
