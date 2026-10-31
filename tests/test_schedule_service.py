import asyncio
from datetime import datetime

import pytest

from schedule_service import ScheduleService
from schedule_store import ScheduleStore


@pytest.mark.asyncio
async def test_collection_saves_snapshot(tmp_path, monkeypatch) -> None:
    service = ScheduleService(ScheduleStore(str(tmp_path / "schedules.db")), 180, 420)
    await service.initialize()
    payload = {"date": "2026-10-31", "weekday": "토", "fields": {}}
    monkeypatch.setattr(service, "_collect_payload", lambda: payload)

    await service.collect_today()
    snapshot, metadata = await service.get_today()

    assert snapshot is not None
    assert snapshot.payload == payload
    assert metadata["fetched_at"] is not None


def test_store_returns_latest_snapshot(tmp_path) -> None:
    store = ScheduleStore(str(tmp_path / "schedules.db"))
    store.initialize()
    payload = {"date": "2026-10-31", "weekday": "토", "fields": {}}
    fetched_at = datetime.fromisoformat("2026-10-31T10:00:00+09:00")
    store.save_snapshot(payload, fetched_at)

    snapshot = store.get_latest_snapshot("2026-10-31")

    assert snapshot is not None
    assert snapshot.fetched_at == fetched_at
