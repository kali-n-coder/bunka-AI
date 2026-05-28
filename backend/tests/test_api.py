from app.core.security import staff_pin_map


STAFF_HEADERS = {"x-staff-pin": "1234"}


def _pin_for(exhibition_id: int) -> str:
    return staff_pin_map()[exhibition_id]


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_staff_login(client):
    created = client.post(
        "/api/v1/exhibitions",
        json={"name": "白龍の舞", "category": "展示"},
        headers=STAFF_HEADERS,
    ).json()
    ok = client.post("/api/v1/staff/login", json={"exhibition_id": created["id"], "pin": _pin_for(created["id"])})
    ng = client.post("/api/v1/staff/login", json={"exhibition_id": created["id"], "pin": "wrong"})

    assert ok.status_code == 200
    assert ok.json()["ok"] is True
    assert ok.json()["exhibition_id"] == created["id"]
    assert ng.status_code == 401


def test_exhibition_and_wait_time_flow(client):
    created = client.post(
        "/api/v1/exhibitions",
        json={
            "name": "白龍の舞",
            "description": "ステージ展示",
            "category": "展示",
            "location_x": 30,
            "location_y": 30,
        },
        headers=STAFF_HEADERS,
    )
    assert created.status_code == 200
    exhibition_id = created.json()["id"]

    listed = client.get("/api/v1/exhibitions")
    assert listed.status_code == 200
    assert len(listed.json()) == 1

    wait = client.post(
        f"/api/v1/exhibitions/{exhibition_id}/wait-time",
        json={"current_wait_minutes": 12},
        headers={"x-staff-pin": _pin_for(exhibition_id)},
    )
    assert wait.status_code == 200
    assert wait.json()["current_wait_minutes"] == 12

    blocked = client.post(
        f"/api/v1/exhibitions/{exhibition_id}/wait-time",
        json={"current_wait_minutes": 30},
        headers={"x-staff-pin": "wrong"},
    )
    assert blocked.status_code == 401

    wait_list = client.get("/api/v1/wait-times")
    assert wait_list.status_code == 200
    assert wait_list.json()[0]["exhibition_name"] == "白龍の舞"


def test_route_and_itinerary_flow(client):
    first = client.post(
        "/api/v1/exhibitions",
        json={"name": "受付", "category": "案内", "location_x": 5, "location_y": 5},
        headers=STAFF_HEADERS,
    ).json()
    second = client.post(
        "/api/v1/exhibitions",
        json={"name": "体育館展示", "category": "展示", "location_x": 30, "location_y": 30},
        headers=STAFF_HEADERS,
    ).json()

    distance = client.get(
        f"/api/v1/routes/distance?from_id={first['id']}&to_id={second['id']}"
    )
    assert distance.status_code == 200
    assert distance.json()["estimated_walk_minutes"] >= 1

    plan = client.post(
        "/api/v1/itinerary/plan",
        json={
            "exhibition_ids": [first["id"], second["id"]],
            "available_minutes": 90,
            "include_wait_times": True,
        },
    )
    assert plan.status_code == 200
    assert plan.json()["total_minutes"] <= 90
