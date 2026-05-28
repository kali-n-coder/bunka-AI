from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session

from app.core.security import verify_exhibition_staff_pin
from app.db.session import get_db
from app.models.exhibition import Exhibition
from app.schemas.planner import StaffLoginRequest, StaffLoginResponse
from fastapi import Depends

router = APIRouter(prefix="/api/v1/staff", tags=["Staff"])


@router.post("/login", response_model=StaffLoginResponse)
def staff_login(payload: StaffLoginRequest, db: Session = Depends(get_db)):
    exhibition = db.get(Exhibition, payload.exhibition_id)
    if not exhibition:
        raise HTTPException(status_code=404, detail="Exhibition not found")

    verify_exhibition_staff_pin(payload.exhibition_id, payload.pin)
    return {
        "ok": True,
        "message": "Staff authentication succeeded.",
        "exhibition_id": exhibition.id,
        "exhibition_name": exhibition.name,
    }
