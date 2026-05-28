import app.api.admin as admin_api
import app.api.chat as chat_api
from app.core.security import staff_pin_map


STAFF_HEADERS = {"x-staff-pin": "1234"}


def _pin_for(exhibition_id: int) -> str:
    return staff_pin_map()[exhibition_id]


def _create_exhibition(client, name, x, y, duration=15, category="demo"):
    response = client.post(
        "/api/v1/exhibitions",
        json={
            "name": name,
            "description": f"{name} description",
            "category": category,
            "location_x": x,
            "location_y": y,
            "location_name": f"{name} room",
            "duration_minutes": duration,
            "recommended_for": "visitors",
            "cautions": "none",
        },
        headers=STAFF_HEADERS,
    )
    assert response.status_code == 200
    return response.json()


def test_chat_api_uses_rag_service_without_ollama(client, monkeypatch):
    async def fake_answer(message, history, filters=None):
        assert message == "show empty exhibitions"
        assert history == []
        assert filters == {"wait": "empty"}
        return {
            "answer": "Use Exhibit A first.",
            "sources": [
                {
                    "content": "Exhibit A has a short wait.",
                    "metadata": {"title": "Exhibit A"},
                    "distance": 0.12,
                }
            ],
            "used_context": True,
        }

    monkeypatch.setattr(chat_api.rag_service, "answer", fake_answer)

    response = client.post(
        "/api/v1/chat",
        json={"message": "show empty exhibitions", "filters": {"wait": "empty"}},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["answer"] == "Use Exhibit A first."
    assert body["used_context"] is True
    assert body["sources"][0]["metadata"]["title"] == "Exhibit A"


def test_rag_status_and_search_contracts(client, monkeypatch):
    monkeypatch.setattr(chat_api.vector_store, "count", lambda: 12)

    async def fake_search(query, top_k=4, filters=None):
        assert query == "gym"
        assert top_k == 2
        assert filters == {"category": "stage"}
        return [{"content": "Gym stage information", "metadata": {"title": "Stage"}, "distance": 0.2}]

    monkeypatch.setattr(chat_api.rag_service, "search", fake_search)

    status = client.get("/api/v1/rag/status")
    assert status.status_code == 200
    assert status.json()["collection_count"] == 12

    search = client.post(
        "/api/v1/rag/search",
        json={"query": "gym", "top_k": 2, "filters": {"category": "stage"}},
    )
    assert search.status_code == 200
    assert search.json()["results"][0]["metadata"]["title"] == "Stage"


def test_itinerary_totals_include_wait_visit_travel_and_return(client):
    first = _create_exhibition(client, "Entrance Demo", 5, 5, duration=10, category="guide")
    second = _create_exhibition(client, "Gym Demo", 30, 30, duration=20, category="stage")
    end = _create_exhibition(client, "Exit Demo", 5, 5, duration=5, category="guide")

    wait_first = client.post(
        f"/api/v1/exhibitions/{first['id']}/wait-time",
        json={"current_wait_minutes": 5},
        headers={"x-staff-pin": _pin_for(first["id"])},
    )
    wait_second = client.post(
        f"/api/v1/exhibitions/{second['id']}/wait-time",
        json={"current_wait_minutes": 10},
        headers={"x-staff-pin": _pin_for(second["id"])},
    )
    assert wait_first.status_code == 200
    assert wait_second.status_code == 200

    response = client.post(
        "/api/v1/itinerary/plan",
        json={
            "exhibition_ids": [first["id"], second["id"]],
            "end_exhibition_id": end["id"],
            "available_minutes": 200,
            "include_wait_times": True,
        },
    )

    assert response.status_code == 200
    plan = response.json()
    assert len(plan["stops"]) == 2
    assert plan["total_wait_minutes"] == 15
    assert plan["total_visit_minutes"] == 30
    assert plan["return_travel_minutes"] >= 1
    assert plan["total_travel_minutes"] >= plan["return_travel_minutes"]
    assert plan["total_minutes"] == plan["total_wait_minutes"] + plan["total_visit_minutes"] + plan["total_travel_minutes"]
    assert plan["skipped_exhibition_ids"] == []


def test_admin_logs_and_model_status_contracts(client, monkeypatch):
    async def fake_ollama_has_model(model_name):
        return {
            "name": model_name,
            "ok": True,
            "matched_name": f"{model_name}:latest",
            "available_models": [f"{model_name}:latest"],
            "latency_ms": 1,
        }

    monkeypatch.setattr(admin_api, "_ollama_has_model", fake_ollama_has_model)
    monkeypatch.setattr(admin_api.vector_store, "count", lambda: 7)

    logs = client.get("/api/v1/admin/logs?limit=5")
    assert logs.status_code == 200
    assert isinstance(logs.json()["logs"], list)

    status = client.get("/api/v1/admin/model-status")
    assert status.status_code == 200
    body = status.json()
    assert body["answer_model"]["ok"] is True
    assert body["embedding_model"]["ok"] is True
    assert body["vector_store"]["ok"] is True
    assert body["vector_store"]["collection_count"] == 7


def test_stage_ticket_and_capacity_fields_are_returned(client):
    response = client.post(
        "/api/v1/exhibitions",
        json={
            "name": "Stage Contract",
            "description": "Stage event",
            "category": "stage",
            "location_x": 10,
            "location_y": 20,
            "location_name": "Gym",
            "stage_start_time": "13:30",
            "ticket_status": "整理券あり",
            "capacity_status": "残りわずか",
        },
        headers=STAFF_HEADERS,
    )
    assert response.status_code == 200
    exhibition = response.json()
    assert exhibition["stage_start_time"] == "13:30"
    assert exhibition["ticket_status"] == "整理券あり"
    assert exhibition["capacity_status"] == "残りわずか"

    wait = client.get(f"/api/v1/exhibitions/{exhibition['id']}/wait-time")
    assert wait.status_code == 200
    wait_body = wait.json()
    assert wait_body["stage_start_time"] == "13:30"
    assert wait_body["ticket_status"] == "整理券あり"
    assert wait_body["capacity_status"] == "残りわずか"


def test_admin_can_update_any_wait_time_and_staff_pin(client, monkeypatch, tmp_path):
    pin_file = tmp_path / "staff_pins.json"
    pin_file.write_text('{"pins": []}', encoding="utf-8")
    monkeypatch.setattr(admin_api, "PIN_FILE", pin_file)

    created = client.post(
        "/api/v1/exhibitions",
        json={"name": "Admin Demo", "category": "展示"},
        headers=STAFF_HEADERS,
    ).json()

    wait_response = client.post(
        f"/api/v1/admin/wait-times/{created['id']}",
        json={"current_wait_minutes": 33},
        headers={"x-admin-pin": "1234"},
    )
    assert wait_response.status_code == 200
    assert wait_response.json()["current_wait_minutes"] == 33

    pin_response = client.put(
        f"/api/v1/admin/staff-pins/{created['id']}",
        json={"pin": "7777"},
        headers={"x-admin-pin": "1234"},
    )
    assert pin_response.status_code == 200
    assert pin_response.json()["pin"] == "7777"

    pins = client.get("/api/v1/admin/staff-pins", headers={"x-admin-pin": "1234"})
    assert pins.status_code == 200
    assert any(item["exhibition_id"] == created["id"] and item["pin"] == "7777" for item in pins.json()["pins"])
