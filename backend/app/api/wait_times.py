from fastapi import APIRouter, Header, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import verify_exhibition_staff_pin
from app.db.session import get_db
from app.models.exhibition import Exhibition
from app.models.wait_time import WaitTime
from app.schemas.wait_time import WaitTimeResponse, WaitTimeUpdate
from app.services.public_wait_sync import publish_wait_time_snapshot_safely

router = APIRouter(prefix="/api/v1", tags=["Wait Times"])


def _response(wait_time: WaitTime, exhibition: Exhibition) -> WaitTimeResponse:
    return WaitTimeResponse(
        id=wait_time.id,
        exhibition_id=wait_time.exhibition_id,
        current_wait_minutes=wait_time.current_wait_minutes or 0,
        updated_at=wait_time.updated_at,
        exhibition_name=exhibition.name if exhibition else None,
        category=exhibition.category if exhibition else None,
        location_name=exhibition.location_name if exhibition else None,
        duration_minutes=exhibition.duration_minutes if exhibition else None,
        recommended_for=exhibition.recommended_for if exhibition else None,
        cautions=exhibition.cautions if exhibition else None,
        stage_start_time=exhibition.stage_start_time if exhibition else None,
        ticket_status=exhibition.ticket_status if exhibition else None,
        capacity_status=exhibition.capacity_status if exhibition else None,
    )


@router.get("/wait-times", response_model=list[WaitTimeResponse])
def list_wait_times(db: Session = Depends(get_db)):
    rows = (
        db.query(WaitTime, Exhibition)
        .join(Exhibition, WaitTime.exhibition_id == Exhibition.id)
        .order_by(Exhibition.id)
        .all()
    )
    return [_response(wait_time, exhibition) for wait_time, exhibition in rows]


@router.get("/exhibitions/{exhibition_id}/wait-time", response_model=WaitTimeResponse)
def get_wait_time(exhibition_id: int, db: Session = Depends(get_db)):
    exhibition = db.get(Exhibition, exhibition_id)
    if not exhibition:
        raise HTTPException(status_code=404, detail="Exhibition not found")

    wait_time = db.query(WaitTime).filter(WaitTime.exhibition_id == exhibition_id).first()
    if not wait_time:
        wait_time = WaitTime(exhibition_id=exhibition_id, current_wait_minutes=0)
        db.add(wait_time)
        db.commit()
        db.refresh(wait_time)
    return _response(wait_time, exhibition)


@router.post(
    "/exhibitions/{exhibition_id}/wait-time",
    response_model=WaitTimeResponse,
)
def update_wait_time(
    exhibition_id: int,
    payload: WaitTimeUpdate,
    x_staff_pin: str = Header(default=""),
    db: Session = Depends(get_db),
):
    exhibition = db.get(Exhibition, exhibition_id)
    if not exhibition:
        raise HTTPException(status_code=404, detail="Exhibition not found")
    verify_exhibition_staff_pin(exhibition_id, x_staff_pin)

    wait_time = db.query(WaitTime).filter(WaitTime.exhibition_id == exhibition_id).first()
    if not wait_time:
        wait_time = WaitTime(exhibition_id=exhibition_id)
        db.add(wait_time)
    wait_time.current_wait_minutes = payload.current_wait_minutes
    db.commit()
    db.refresh(wait_time)
    publish_wait_time_snapshot_safely(db)
    return _response(wait_time, exhibition)
