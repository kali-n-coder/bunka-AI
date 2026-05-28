from sqlalchemy.orm import Session

from app.models.exhibition import Exhibition
from app.models.wait_time import WaitTime
from app.services.map_graph import nearest_node, shortest_path


def estimate_between(from_exhibition: Exhibition, to_exhibition: Exhibition):
    start = nearest_node(from_exhibition.location_x, from_exhibition.location_y)
    goal = nearest_node(to_exhibition.location_x, to_exhibition.location_y)
    distance, path = shortest_path(start, goal)
    return {
        "distance": distance,
        "estimated_walk_minutes": max(1, round(distance)),
        "path": path,
    }


def get_wait_minutes(db: Session, exhibition_id: int) -> int:
    wait_time = db.query(WaitTime).filter(WaitTime.exhibition_id == exhibition_id).first()
    return wait_time.current_wait_minutes if wait_time else 0


def build_itinerary(
    db: Session,
    exhibition_ids: list[int],
    start_exhibition_id: int | None,
    end_exhibition_id: int | None,
    available_minutes: int,
    include_wait_times: bool,
):
    exhibitions = {
        exhibition.id: exhibition
        for exhibition in db.query(Exhibition).filter(Exhibition.id.in_(exhibition_ids)).all()
    }
    skipped = [exhibition_id for exhibition_id in exhibition_ids if exhibition_id not in exhibitions]
    remaining = [exhibitions[exhibition_id] for exhibition_id in exhibition_ids if exhibition_id in exhibitions]

    if not remaining:
        return [], 0, skipped, "見学できる展示が見つかりませんでした。"

    current = db.get(Exhibition, start_exhibition_id) if start_exhibition_id else None
    stops = []
    elapsed = 0
    total_travel = 0
    total_wait = 0
    total_visit = 0

    while remaining:
        if current:
            remaining.sort(key=lambda item: estimate_between(current, item)["estimated_walk_minutes"])
        next_exhibition = remaining.pop(0)
        travel = estimate_between(current, next_exhibition)["estimated_walk_minutes"] if current else 0
        wait = get_wait_minutes(db, next_exhibition.id) if include_wait_times else 0
        visit_minutes = next_exhibition.duration_minutes or 15
        needed = travel + wait + visit_minutes

        if elapsed + needed > available_minutes:
            skipped.append(next_exhibition.id)
            continue

        elapsed += needed
        total_travel += travel
        total_wait += wait
        total_visit += visit_minutes
        stops.append(
            {
                "exhibition_id": next_exhibition.id,
                "exhibition_name": next_exhibition.name,
                "wait_minutes": wait,
                "visit_minutes": visit_minutes,
                "travel_minutes_from_previous": travel,
                "elapsed_minutes": elapsed,
            }
        )
        current = next_exhibition

    return_travel = 0
    end_exhibition = db.get(Exhibition, end_exhibition_id) if end_exhibition_id else None
    if current and end_exhibition:
        return_travel = estimate_between(current, end_exhibition)["estimated_walk_minutes"]
        if elapsed + return_travel <= available_minutes:
            elapsed += return_travel
            total_travel += return_travel
        else:
            skipped.append(end_exhibition.id)

    note = "待ち時間と移動時間を考慮して、近い展示から順に組み立てました。"
    return {
        "stops": stops,
        "total_minutes": elapsed,
        "total_travel_minutes": total_travel,
        "total_wait_minutes": total_wait,
        "total_visit_minutes": total_visit,
        "return_travel_minutes": return_travel,
        "skipped_exhibition_ids": skipped,
        "note": note,
    }
