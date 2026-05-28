import json
from pathlib import Path

from fastapi import Header, HTTPException

from app.core.config import settings

PIN_FILE = Path(__file__).resolve().parents[2] / "config" / "staff_pins.json"


def staff_pin_map() -> dict[int, str]:
    pins: dict[int, str] = {}
    if PIN_FILE.exists():
        data = json.loads(PIN_FILE.read_text(encoding="utf-8"))
        for item in data.get("pins", []):
            try:
                pins[int(item["exhibition_id"])] = str(item["pin"])
            except (KeyError, TypeError, ValueError):
                continue
        if pins:
            return pins

    for item in settings.STAFF_PINS.split(","):
        if ":" not in item:
            continue
        exhibition_id, pin = item.split(":", 1)
        try:
            pins[int(exhibition_id.strip())] = pin.strip()
        except ValueError:
            continue
    return pins


def verify_exhibition_staff_pin(exhibition_id: int, pin: str):
    expected = staff_pin_map().get(exhibition_id)
    if not expected or pin != expected:
        raise HTTPException(status_code=401, detail="Invalid staff PIN for this exhibition")
    return True


def verify_staff_pin(x_staff_pin: str = Header(default="")):
    if x_staff_pin != settings.STAFF_PIN:
        raise HTTPException(status_code=401, detail="Invalid staff PIN")
    return True
