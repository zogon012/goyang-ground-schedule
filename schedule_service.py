import asyncio
import json
import logging
import random
from datetime import datetime, timedelta
from typing import Any

from simple import KST, get_today_complete_info_json
from schedule_store import ScheduleSnapshot, ScheduleStore

logger = logging.getLogger(__name__)


class ScheduleService:
    def __init__(
        self,
        store: ScheduleStore,
        refresh_min_seconds: int,
        refresh_max_seconds: int,
    ) -> None:
        if refresh_min_seconds <= 0 or refresh_max_seconds < refresh_min_seconds:
            raise ValueError("유효하지 않은 수집 주기입니다.")

        self._store = store
        self._refresh_min_seconds = refresh_min_seconds
        self._refresh_max_seconds = refresh_max_seconds
        self._next_refresh_at: datetime | None = None
        self._last_error: str | None = None
        self._collector_task: asyncio.Task[None] | None = None

    async def initialize(self) -> None:
        await asyncio.to_thread(self._store.initialize)

    async def get_today(self) -> tuple[ScheduleSnapshot | None, dict[str, Any]]:
        target_date = self._today_string()
        snapshot = await asyncio.to_thread(self._store.get_latest_snapshot, target_date)
        return snapshot, self.status(snapshot)

    async def collect_today(self) -> None:
        started_at = self._now()
        target_date = self._today_string()
        try:
            payload = await asyncio.to_thread(self._collect_payload)
            completed_at = self._now()
            await asyncio.to_thread(self._store.save_snapshot, payload, completed_at)
            await asyncio.to_thread(
                self._store.save_collection_run,
                target_date,
                started_at,
                completed_at,
                "success",
            )
            self._last_error = None
            logger.info("예약 현황 수집 완료: %s", target_date)
        except Exception as error:
            completed_at = self._now()
            self._last_error = str(error)
            await asyncio.to_thread(
                self._store.save_collection_run,
                target_date,
                started_at,
                completed_at,
                "failure",
                self._last_error,
            )
            logger.exception("예약 현황 수집 실패")

    def start(self) -> None:
        if self._collector_task is None:
            self._collector_task = asyncio.create_task(self._run_collector())

    async def stop(self) -> None:
        if self._collector_task is None:
            return
        self._collector_task.cancel()
        try:
            await self._collector_task
        except asyncio.CancelledError:
            pass
        self._collector_task = None

    def status(self, snapshot: ScheduleSnapshot | None) -> dict[str, Any]:
        now = self._now()
        stale_after = timedelta(seconds=self._refresh_max_seconds * 2)
        is_stale = snapshot is None or now - snapshot.fetched_at > stale_after
        return {
            "fetched_at": snapshot.fetched_at.isoformat() if snapshot else None,
            "next_refresh_at": self._next_refresh_at.isoformat() if self._next_refresh_at else None,
            "is_stale": is_stale,
            "last_error": self._last_error,
        }

    async def _run_collector(self) -> None:
        while True:
            await self.collect_today()
            delay_seconds = random.randint(self._refresh_min_seconds, self._refresh_max_seconds)
            self._next_refresh_at = self._now() + timedelta(seconds=delay_seconds)
            await asyncio.sleep(delay_seconds)

    @staticmethod
    def _collect_payload() -> dict[str, Any]:
        return json.loads(get_today_complete_info_json())

    @staticmethod
    def _now() -> datetime:
        return datetime.now(KST)

    @staticmethod
    def _today_string() -> str:
        return datetime.now(KST).date().isoformat()
