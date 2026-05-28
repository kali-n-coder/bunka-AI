from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.exhibition import Exhibition
from app.schemas.planner import DistanceResponse, RouteEstimateRequest
from app.services.itinerary_planner import estimate_between

router = APIRouter(prefix="/api/v1/routes", tags=["Routes"])


@router.get("/distance", response_model=DistanceResponse)
def distance(from_id: int, to_id: int, db: Session = Depends(get_db)):
    source = db.get(Exhibition, from_id)
    target = db.get(Exhibition, to_id)
    if not source or not target:
        raise HTTPException(status_code=404, detail="Exhibition not found")
    result = estimate_between(source, target)
    return {"from_id": from_id, "to_id": to_id, **result}


@router.post("/estimate")
def estimate_route(payload: RouteEstimateRequest, db: Session = Depends(get_db)):
    total = 0
    legs = []
    for from_id, to_id in zip(payload.exhibition_ids, payload.exhibition_ids[1:]):
        source = db.get(Exhibition, from_id)
        target = db.get(Exhibition, to_id)
        if not source or not target:
            raise HTTPException(status_code=404, detail="Exhibition not found")
        result = estimate_between(source, target)
        total += result["estimated_walk_minutes"]
        legs.append({"from_id": from_id, "to_id": to_id, **result})
    return {"total_walk_minutes": total, "legs": legs}
