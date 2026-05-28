from typing import Optional

from pydantic import BaseModel, ConfigDict


class ExhibitionBase(BaseModel):
    name: str
    description: Optional[str] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    category: Optional[str] = None
    location_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    recommended_for: Optional[str] = None
    cautions: Optional[str] = None
    stage_start_time: Optional[str] = None
    ticket_status: Optional[str] = None
    capacity_status: Optional[str] = None


class ExhibitionCreate(ExhibitionBase):
    pass


class ExhibitionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location_x: Optional[float] = None
    location_y: Optional[float] = None
    category: Optional[str] = None
    location_name: Optional[str] = None
    duration_minutes: Optional[int] = None
    recommended_for: Optional[str] = None
    cautions: Optional[str] = None
    stage_start_time: Optional[str] = None
    ticket_status: Optional[str] = None
    capacity_status: Optional[str] = None


class ExhibitionResponse(ExhibitionBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
