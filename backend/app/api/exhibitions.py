from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.security import verify_staff_pin
from app.db.session import get_db
from app.models.exhibition import Exhibition
from app.schemas.exhibition import ExhibitionCreate, ExhibitionResponse, ExhibitionUpdate

router = APIRouter(prefix="/api/v1/exhibitions", tags=["Exhibitions"])


@router.get("", response_model=list[ExhibitionResponse])
def list_exhibitions(
    category: Optional[str] = None,
    q: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Exhibition)
    if category:
        query = query.filter(Exhibition.category == category)
    if q:
        pattern = f"%{q}%"
        query = query.filter(
            (Exhibition.name.like(pattern)) | (Exhibition.description.like(pattern))
        )
    return query.order_by(Exhibition.id).all()


@router.get("/{exhibition_id}", response_model=ExhibitionResponse)
def get_exhibition(exhibition_id: int, db: Session = Depends(get_db)):
    exhibition = db.get(Exhibition, exhibition_id)
    if not exhibition:
        raise HTTPException(status_code=404, detail="Exhibition not found")
    return exhibition


@router.post("", response_model=ExhibitionResponse, dependencies=[Depends(verify_staff_pin)])
def create_exhibition(payload: ExhibitionCreate, db: Session = Depends(get_db)):
    exhibition = Exhibition(**payload.model_dump())
    db.add(exhibition)
    db.commit()
    db.refresh(exhibition)
    return exhibition


@router.patch("/{exhibition_id}", response_model=ExhibitionResponse, dependencies=[Depends(verify_staff_pin)])
def update_exhibition(
    exhibition_id: int,
    payload: ExhibitionUpdate,
    db: Session = Depends(get_db),
):
    exhibition = db.get(Exhibition, exhibition_id)
    if not exhibition:
        raise HTTPException(status_code=404, detail="Exhibition not found")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(exhibition, key, value)
    db.commit()
    db.refresh(exhibition)
    return exhibition
