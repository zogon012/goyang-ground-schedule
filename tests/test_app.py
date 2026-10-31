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
        "date": "2026-10-31",
        "weekday": "토",
        "fields": {"테스트구장": {"empty_slots": [], "booked_matches": []}},
    }
    service._store.save_snapshot(payload, datetime.fromisoformat("2026-10-31T10:00:00+09:00"))
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
    assert response.json()["version"] == "1.1.2"
