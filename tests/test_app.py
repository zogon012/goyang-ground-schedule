import asyncio
from datetime import datetime

from fastapi.testclient import TestClient

import app as app_module
from schedule_service import ScheduleService
from schedule_store import ScheduleStore


def test_root_endpoint() -> None:
    client = TestClient(app_module.app)
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_current_time_endpoint() -> None:
    client = TestClient(app_module.app)
    response = client.get("/current-time")
    assert response.status_code == 200
    assert response.json()["current_time"]


def test_today_returns_service_snapshot(tmp_path, monkeypatch) -> None:
    service = ScheduleService(ScheduleStore(str(tmp_path / "schedules.db")), 180, 420)
    asyncio.run(service.initialize())
    payload = {
        "date": service._today_string(),
        "weekday": "토",
        "fields": {"테스트구장": {"empty_slots": [], "booked_matches": []}},
    }
    service._store.save_snapshot(payload, datetime.now().astimezone())
    monkeypatch.setattr(app_module, "schedule_service", service)

    client = TestClient(app_module.app)
    response = client.get("/today")

    assert response.status_code == 200
    assert response.json()["fields"] == payload["fields"]
    assert "metadata" in response.json()


def test_health_endpoint() -> None:
    client = TestClient(app_module.app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["version"] == "1.2.1"


def test_lifespan_collects_initial_schedule(tmp_path, monkeypatch) -> None:
    service = ScheduleService(ScheduleStore(str(tmp_path / "schedules.db")), 180, 420)
    payload = {"date": service._today_string(), "weekday": "일", "fields": {}}

    async def collect_initial_schedule() -> bool:
        service._store.save_snapshot(payload, datetime.now().astimezone())
        return True

    monkeypatch.setattr(service, "collect_today", collect_initial_schedule)
    monkeypatch.setattr(app_module, "schedule_service", service)
    monkeypatch.setattr(app_module, "COLLECTOR_ENABLED", False)

    with TestClient(app_module.app) as client:
        response = client.get("/today")

    assert response.status_code == 200
    assert response.json()["date"] == payload["date"]
