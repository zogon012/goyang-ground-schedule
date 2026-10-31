import json
import hashlib
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ScheduleSnapshot:
    payload: dict[str, Any]
    fetched_at: datetime


class ScheduleStore:
    def __init__(self, database_path: str) -> None:
        self._database_path = database_path

    def initialize(self) -> None:
        Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS schedule_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_date TEXT NOT NULL,
                    payload TEXT NOT NULL,
                    fetched_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_schedule_snapshots_date_fetched
                ON schedule_snapshots(target_date, fetched_at DESC)
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS collection_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    target_date TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error_message TEXT
                )
                """
            )

    def save_snapshot(self, payload: dict[str, Any], fetched_at: datetime) -> bool:
        target_date = str(payload["date"])
        serialized_payload = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        fingerprint = hashlib.sha256(serialized_payload.encode()).hexdigest()
        with self._connect() as connection:
            latest_row = connection.execute(
                """
                SELECT payload
                FROM schedule_snapshots
                WHERE target_date = ?
                ORDER BY fetched_at DESC
                LIMIT 1
                """,
                (target_date,),
            ).fetchone()
            if latest_row is not None:
                latest_fingerprint = hashlib.sha256(
                    json.dumps(
                        json.loads(latest_row[0]),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ).encode()
                ).hexdigest()
                if latest_fingerprint == fingerprint:
                    return False
            connection.execute(
                "INSERT INTO schedule_snapshots(target_date, payload, fetched_at) VALUES (?, ?, ?)",
                (target_date, serialized_payload, fetched_at.isoformat()),
            )
        return True

    def get_latest_snapshot(self, target_date: str) -> ScheduleSnapshot | None:
        try:
            with self._connect() as connection:
                row = connection.execute(
                    """
                    SELECT payload, fetched_at
                    FROM schedule_snapshots
                    WHERE target_date = ?
                    ORDER BY fetched_at DESC
                    LIMIT 1
                    """,
                    (target_date,),
                ).fetchone()
        except sqlite3.OperationalError as error:
            if "no such table" not in str(error):
                raise
            return None

        if row is None:
            return None

        return ScheduleSnapshot(
            payload=json.loads(row[0]),
            fetched_at=datetime.fromisoformat(row[1]),
        )

    def get_available_dates(self) -> list[tuple[str, datetime]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT target_date, MAX(fetched_at)
                FROM schedule_snapshots
                GROUP BY target_date
                ORDER BY target_date DESC
                """
            ).fetchall()
        return [(row[0], datetime.fromisoformat(row[1])) for row in rows]

    def save_collection_run(
        self,
        target_date: str,
        started_at: datetime,
        completed_at: datetime,
        status: str,
        error_message: str | None = None,
    ) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO collection_runs(
                    target_date, started_at, completed_at, status, error_message
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    target_date,
                    started_at.isoformat(),
                    completed_at.isoformat(),
                    status,
                    error_message,
                ),
            )

    def _connect(self) -> sqlite3.Connection:
        Path(self._database_path).parent.mkdir(parents=True, exist_ok=True)
        return sqlite3.connect(self._database_path)
