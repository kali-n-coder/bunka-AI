import logging
from typing import Any
from urllib.parse import urlencode

import httpx
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.exhibition import Exhibition
from app.models.wait_time import WaitTime

logger = logging.getLogger(__name__)


def _firebase_url() -> str:
    raw_url = settings.FIREBASE_WAIT_TIMES_URL.strip()
    if not raw_url:
        return ""

    url = raw_url if raw_url.endswith(".json") else f"{raw_url.rstrip('/')}.json"
    if settings.FIREBASE_WAIT_TIMES_AUTH:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}{urlencode({'auth': settings.FIREBASE_WAIT_TIMES_AUTH})}"
    return url


def _payload(wait_time: WaitTime, exhibition: Exhibition) -> dict[str, Any]:
    return {
        "id": wait_time.id,
        "exhibition_id": wait_time.exhibition_id,
        "exhibition_name": exhibition.name,
        "category": exhibition.category,
        "location_name": exhibition.location_name,
        "duration_minutes": exhibition.duration_minutes,
        "recommended_for": exhibition.recommended_for,
        "cautions": exhibition.cautions,
        "stage_start_time": exhibition.stage_start_time,
        "ticket_status": exhibition.ticket_status,
        "capacity_status": exhibition.capacity_status,
        "current_wait_minutes": wait_time.current_wait_minutes or 0,
        "updated_at": wait_time.updated_at.isoformat() if wait_time.updated_at else None,
    }


def wait_time_snapshot(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.query(WaitTime, Exhibition)
        .join(Exhibition, WaitTime.exhibition_id == Exhibition.id)
        .order_by(Exhibition.id)
        .all()
    )
    return [_payload(wait_time, exhibition) for wait_time, exhibition in rows]


def publish_wait_time_snapshot(db: Session) -> dict[str, Any]:
    url = _firebase_url()
    if not url:
        return {"enabled": False, "published": 0}

    payload = wait_time_snapshot(db)
    with httpx.Client(timeout=10.0) as client:
        response = client.put(url, json=payload)
        response.raise_for_status()

    return {"enabled": True, "published": len(payload)}


def publish_wait_time_snapshot_safely(db: Session) -> None:
    try:
        result = publish_wait_time_snapshot(db)
        if result.get("enabled"):
            logger.info("Published public wait-time snapshot: %s items", result.get("published", 0))
    except Exception as exc:
        logger.warning("Failed to publish public wait-time snapshot: %s", exc)
