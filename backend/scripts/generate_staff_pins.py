import json
import os
import random
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from app.db.session import SessionLocal, ensure_database_schema
from app.models.exhibition import Exhibition


def main():
    ensure_database_schema()
    db = SessionLocal()
    try:
        exhibitions = db.query(Exhibition).order_by(Exhibition.id).all()
        rng = random.SystemRandom()
        used = set()
        pins = []
        for exhibition in exhibitions:
            pin = ""
            while not pin or pin in used:
                pin = f"{rng.randint(0, 9999):04d}"
            used.add(pin)
            pins.append({"exhibition_id": exhibition.id, "name": exhibition.name, "pin": pin})

        output = ROOT / "config" / "staff_pins.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps({"pins": pins}, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"Generated {len(pins)} staff PINs: {output}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
