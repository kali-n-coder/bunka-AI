from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.planner import ItineraryRequest, ItineraryResponse
from app.services.itinerary_planner import build_itinerary

router = APIRouter(prefix="/api/v1/itinerary", tags=["Itinerary"])


@router.post("/plan", response_model=ItineraryResponse)
def plan_itinerary(payload: ItineraryRequest, db: Session = Depends(get_db)):
    return build_itinerary(
        db=db,
        exhibition_ids=payload.exhibition_ids,
        start_exhibition_id=payload.start_exhibition_id,
        end_exhibition_id=payload.end_exhibition_id,
        available_minutes=payload.available_minutes,
        include_wait_times=payload.include_wait_times,
    )
