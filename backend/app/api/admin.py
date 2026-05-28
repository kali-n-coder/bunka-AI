import time
import json
from pathlib import Path
from typing import Any, Dict

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import PIN_FILE
from app.db.session import get_db
from app.models.exhibition import Exhibition
from app.models.wait_time import WaitTime
from app.services.admin_state import memory_log_handler
from app.services.public_wait_sync import publish_wait_time_snapshot, publish_wait_time_snapshot_safely
from app.services.vector_store import vector_store

router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


class AdminWaitUpdate(BaseModel):
    current_wait_minutes: int = Field(..., ge=0, le=240)


class AdminPinUpdate(BaseModel):
    pin: str = Field(..., min_length=4, max_length=12)


def verify_admin_pin(x_admin_pin: str = Header(default="")) -> bool:
    if x_admin_pin != settings.STAFF_PIN:
        raise HTTPException(status_code=401, detail="Invalid admin PIN")
    return True


def _model_name_candidates(model_name: str) -> set[str]:
    if ":" in model_name:
        base_name = model_name.split(":", 1)[0]
        return {model_name, base_name}
    return {model_name, f"{model_name}:latest"}


def _read_pin_items() -> list[dict[str, Any]]:
    if not PIN_FILE.exists():
        return []
    data = json.loads(PIN_FILE.read_text(encoding="utf-8"))
    pins = data.get("pins", [])
    return pins if isinstance(pins, list) else []


def _write_pin_items(items: list[dict[str, Any]]) -> None:
    PIN_FILE.parent.mkdir(parents=True, exist_ok=True)
    PIN_FILE.write_text(json.dumps({"pins": items}, ensure_ascii=False, indent=2), encoding="utf-8")


async def _ollama_has_model(model_name: str) -> Dict[str, Any]:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.OLLAMA_BASE_URL}/api/tags")
            response.raise_for_status()
        models = response.json().get("models", [])
        names = [model.get("name") for model in models if isinstance(model, dict)]
        candidates = _model_name_candidates(model_name)
        matched_name = next((name for name in names if name in candidates), None)
        return {
            "name": model_name,
            "ok": matched_name is not None,
            "matched_name": matched_name,
            "available_models": names,
            "latency_ms": round((time.perf_counter() - started) * 1000),
        }
    except Exception as exc:
        return {
            "name": model_name,
            "ok": False,
            "available_models": [],
            "latency_ms": round((time.perf_counter() - started) * 1000),
            "error": str(exc),
        }


@router.get("/logs")
async def logs(limit: int = 50):
    return {"logs": memory_log_handler.recent(limit)}


@router.get("/model-status")
async def model_status():
    answer_model = await _ollama_has_model(settings.OLLAMA_MODEL)
    embedding_model = await _ollama_has_model(settings.OLLAMA_EMBEDDING_MODEL)
    try:
        collection_count = vector_store.count()
        vector_ok = True
        vector_error = None
    except Exception as exc:
        collection_count = 0
        vector_ok = False
        vector_error = str(exc)

    return {
        "ollama_base_url": settings.OLLAMA_BASE_URL,
        "answer_model": answer_model,
        "embedding_model": embedding_model,
        "vector_store": {
            "ok": vector_ok,
            "collection_count": collection_count,
            "error": vector_error,
        },
    }


@router.get("/staff-pins", dependencies=[Depends(verify_admin_pin)])
async def staff_pins(db: Session = Depends(get_db)):
    pin_map = {}
    for item in _read_pin_items():
        try:
            pin_map[int(item["exhibition_id"])] = str(item["pin"])
        except (KeyError, TypeError, ValueError):
            continue

    exhibitions = db.query(Exhibition).order_by(Exhibition.id).all()
    return {
        "pins": [
            {
                "exhibition_id": exhibition.id,
                "name": exhibition.name,
                "pin": pin_map.get(exhibition.id, ""),
            }
            for exhibition in exhibitions
        ]
    }


@router.put("/staff-pins/{exhibition_id}", dependencies=[Depends(verify_admin_pin)])
async def update_staff_pin(
    exhibition_id: int,
    payload: AdminPinUpdate,
    db: Session = Depends(get_db),
):
    exhibition = db.get(Exhibition, exhibition_id)
    if not exhibition:
        raise HTTPException(status_code=404, detail="Exhibition not found")

    items = _read_pin_items()
    updated = False
    normalized = []
    for item in items:
        try:
            item_exhibition_id = int(item["exhibition_id"])
        except (KeyError, TypeError, ValueError):
            continue
        if item_exhibition_id == exhibition_id:
            normalized.append({"exhibition_id": exhibition.id, "name": exhibition.name, "pin": payload.pin})
            updated = True
        else:
            normalized.append(
                {
                    "exhibition_id": item_exhibition_id,
                    "name": str(item.get("name", "")),
                    "pin": str(item.get("pin", "")),
                }
            )
    if not updated:
        normalized.append({"exhibition_id": exhibition.id, "name": exhibition.name, "pin": payload.pin})

    normalized.sort(key=lambda item: item["exhibition_id"])
    _write_pin_items(normalized)
    return {"ok": True, "exhibition_id": exhibition.id, "name": exhibition.name, "pin": payload.pin}


@router.post("/wait-times/{exhibition_id}", dependencies=[Depends(verify_admin_pin)])
async def update_any_wait_time(
    exhibition_id: int,
    payload: AdminWaitUpdate,
    db: Session = Depends(get_db),
):
    exhibition = db.get(Exhibition, exhibition_id)
    if not exhibition:
        raise HTTPException(status_code=404, detail="Exhibition not found")

    wait_time = db.query(WaitTime).filter(WaitTime.exhibition_id == exhibition_id).first()
    if not wait_time:
        wait_time = WaitTime(exhibition_id=exhibition_id)
        db.add(wait_time)
    wait_time.current_wait_minutes = payload.current_wait_minutes
    db.commit()
    db.refresh(wait_time)
    publish_wait_time_snapshot_safely(db)

    return {
        "ok": True,
        "exhibition_id": exhibition.id,
        "exhibition_name": exhibition.name,
        "current_wait_minutes": wait_time.current_wait_minutes,
    }


@router.post("/public-wait-times/publish", dependencies=[Depends(verify_admin_pin)])
async def publish_public_wait_times(db: Session = Depends(get_db)):
    return publish_wait_time_snapshot(db)
