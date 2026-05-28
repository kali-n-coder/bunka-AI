import argparse
import csv
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List


ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = ROOT / "docs" / "data"

EXPECTED_FIELDS = [
    "name",
    "description",
    "category",
    "location_name",
    "duration_minutes",
    "recommended_for",
    "cautions",
    "stage_start_time",
    "ticket_status",
    "capacity_status",
    "location_x",
    "location_y",
    "current_wait_minutes",
]
REQUIRED_TEXT_FIELDS = [
    "name",
    "description",
    "category",
    "location_name",
    "recommended_for",
    "cautions",
]
REQUIRED_NUMBER_FIELDS = [
    "duration_minutes",
    "location_x",
    "location_y",
    "current_wait_minutes",
]
OPTIONAL_TEXT_FIELDS = [
    "stage_start_time",
    "ticket_status",
    "capacity_status",
]
TIME_PATTERN = re.compile(r"^\d{1,2}:\d{2}$")


def _load_rows(path: Path) -> List[Dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as file:
            return list(csv.DictReader(file))

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return data
        if isinstance(data, dict):
            return data.get("exhibitions", [])

    raise ValueError(f"Unsupported file type: {path}")


def _load_csv_rows_and_fields(path: Path) -> tuple[List[Dict[str, Any]], List[str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)
        return rows, list(reader.fieldnames or [])


def _is_blank(value: Any) -> bool:
    return value is None or str(value).strip() == ""


def _validate_number(row: Dict[str, Any], row_number: int, field: str, errors: List[str]) -> None:
    value = row.get(field)
    if _is_blank(value):
        errors.append(f"{row_number}行目: {field} が空です。")
        return
    try:
        number = float(value)
    except (TypeError, ValueError):
        errors.append(f"{row_number}行目: {field} は数値で入力してください。")
        return
    if field in {"duration_minutes", "current_wait_minutes"} and number < 0:
        errors.append(f"{row_number}行目: {field} は0以上にしてください。")


def validate_columns(fieldnames: Iterable[str]) -> List[str]:
    errors: List[str] = []
    fields = [str(field).strip() for field in fieldnames]
    missing = [field for field in EXPECTED_FIELDS if field not in fields]
    extra = [field for field in fields if field not in EXPECTED_FIELDS]

    if missing:
        errors.append("CSVの列が不足しています: " + ", ".join(missing))
    if extra:
        errors.append("CSVに未使用の列があります: " + ", ".join(extra))
    if fields and fields != EXPECTED_FIELDS:
        errors.append("CSVの列順がテンプレートと違います。docs/data_template.csv と同じ順番にしてください。")

    return errors


def validate_rows(rows: Iterable[Dict[str, Any]]) -> List[str]:
    errors: List[str] = []
    names = set()

    for index, row in enumerate(rows, start=2):
        name = str(row.get("name", "")).strip()
        if name:
            if name in names:
                errors.append(f"{index}行目: 企画名 `{name}` が重複しています。")
            names.add(name)

        for field in REQUIRED_TEXT_FIELDS:
            if _is_blank(row.get(field)):
                errors.append(f"{index}行目: {field} が空です。")

        for field in REQUIRED_NUMBER_FIELDS:
            _validate_number(row, index, field, errors)

        for field in OPTIONAL_TEXT_FIELDS:
            value = row.get(field)
            if value is not None and not isinstance(value, str):
                errors.append(f"{index}行目: {field} は文字列で入力してください。")

        stage_start_time = str(row.get("stage_start_time", "")).strip()
        if stage_start_time and not TIME_PATTERN.match(stage_start_time):
            errors.append(f"{index}行目: stage_start_time は 10:30 のような HH:MM 形式で入力してください。")

    if not names:
        errors.append("企画データが1件もありません。")

    return errors


def validate_data_file(path: Path) -> tuple[List[Dict[str, Any]], List[str]]:
    if path.suffix.lower() == ".csv":
        rows, fieldnames = _load_csv_rows_and_fields(path)
        return rows, validate_columns(fieldnames) + validate_rows(rows)

    rows = _load_rows(path)
    return rows, validate_rows(rows)


def resolve_data_file(profile: str, file_path: str | None) -> Path:
    if file_path:
        return Path(file_path).resolve()

    profile_dir = DATA_ROOT / profile
    for filename in ("exhibitions.csv", "exhibitions.json"):
        candidate = profile_dir / filename
        if candidate.exists():
            return candidate
    return profile_dir / "exhibitions.csv"


def main() -> int:
    parser = argparse.ArgumentParser(description="企画データの入力チェックを行います。")
    parser.add_argument("--profile", choices=["sample", "production"], default="sample")
    parser.add_argument("--file", help="直接チェックするCSVまたはJSONファイル")
    args = parser.parse_args()

    path = resolve_data_file(args.profile, args.file)
    if not path.exists():
        print(f"ERROR: データファイルが見つかりません: {path}")
        return 1

    try:
        rows, errors = validate_data_file(path)
    except Exception as exc:
        print(f"ERROR: 読み込みに失敗しました: {exc}")
        return 1

    if errors:
        print(f"NG: {path} に {len(errors)} 件の問題があります。")
        for error in errors:
            print(f"- {error}")
        return 1

    print(f"OK: {path} の企画データは問題ありません。件数: {len(rows)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
