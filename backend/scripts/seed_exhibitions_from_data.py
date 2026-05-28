import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List


BACKEND_ROOT = Path(__file__).resolve().parents[1]
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))
os.chdir(BACKEND_ROOT)

from app.db.session import SessionLocal, ensure_database_schema
from app.models.exhibition import Exhibition
from app.models.wait_time import WaitTime
from validate_exhibition_data import validate_data_file


DATA_ROOT = PROJECT_ROOT / "docs" / "data"


def _load_rows(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else data.get("exhibitions", [])

    raise ValueError(f"Unsupported file type: {path}")


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or str(value).strip() == "":
        return default
    return int(float(value))


def _to_float(value: Any, default: float = 0.0) -> float:
    if value is None or str(value).strip() == "":
        return default
    return float(value)


def resolve_data_file(profile: str, file_path: str | None) -> Path:
    if file_path:
        return Path(file_path).resolve()

    profile_dir = DATA_ROOT / profile
    for filename in ("exhibitions.csv", "exhibitions.json"):
        candidate = profile_dir / filename
        if candidate.exists():
            return candidate
    return profile_dir / "exhibitions.csv"


def normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "name": str(row.get("name", "")).strip(),
        "description": str(row.get("description", "")).strip(),
        "category": str(row.get("category", "")).strip(),
        "location_name": str(row.get("location_name", "")).strip(),
        "duration_minutes": _to_int(row.get("duration_minutes"), 15),
        "recommended_for": str(row.get("recommended_for", "")).strip(),
        "cautions": str(row.get("cautions", "")).strip(),
        "stage_start_time": str(row.get("stage_start_time", "")).strip(),
        "ticket_status": str(row.get("ticket_status", "")).strip(),
        "capacity_status": str(row.get("capacity_status", "")).strip(),
        "location_x": _to_float(row.get("location_x"), 0.0),
        "location_y": _to_float(row.get("location_y"), 0.0),
        "current_wait_minutes": _to_int(row.get("current_wait_minutes"), 0),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="CSV/JSONから企画データをSQLiteへ投入します。")
    parser.add_argument("--profile", choices=["sample", "production"], default="sample")
    parser.add_argument("--file", help="直接投入するCSVまたはJSONファイル")
    args = parser.parse_args()

    path = resolve_data_file(args.profile, args.file)
    if not path.exists():
        print(f"ERROR: データファイルが見つかりません: {path}")
        return 1

    raw_rows, errors = validate_data_file(path)
    if errors:
        print(f"ERROR: {path} に {len(errors)} 件の問題があるため投入を中止します。")
        for error in errors:
            print(f"- {error}")
        return 1

    rows = [normalize_row(row) for row in raw_rows]
    ensure_database_schema()

    db = SessionLocal()
    try:
        created = 0
        updated = 0
        for row in rows:
            wait_minutes = row.pop("current_wait_minutes")
            exhibition = db.query(Exhibition).filter(Exhibition.name == row["name"]).first()
            if exhibition:
                for key, value in row.items():
                    setattr(exhibition, key, value)
                updated += 1
            else:
                exhibition = Exhibition(**row)
                db.add(exhibition)
                db.flush()
                created += 1

            wait_time = db.query(WaitTime).filter(WaitTime.exhibition_id == exhibition.id).first()
            if wait_time:
                wait_time.current_wait_minutes = wait_minutes
            else:
                db.add(WaitTime(exhibition_id=exhibition.id, current_wait_minutes=wait_minutes))

        db.commit()
        print(f"Seed completed from {path}. Created exhibitions: {created}. Updated exhibitions: {updated}.")
        return 0
    finally:
        db.close()


if __name__ == "__main__":
    sys.exit(main())
