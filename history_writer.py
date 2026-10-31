from datetime import datetime
from pathlib import Path
from typing import Any

import pyarrow as pa
import pyarrow.parquet as pq


class HistoryWriter:
    def __init__(self, base_path: str) -> None:
        self._base_path = Path(base_path)

    def write_snapshot(self, payload: dict[str, Any], collected_at: datetime) -> None:
        target_date = str(payload["date"])
        rows: list[dict[str, str | int | bool]] = []
        for field_name, field in payload["fields"].items():
            for hour in range(7, 23):
                is_available = any(
                    int(slot["start_time"][:2]) <= hour < int(slot["end_time"][:2])
                    for slot in field["empty_slots"]
                )
                rows.append(
                    {
                        "collected_at": collected_at.isoformat(),
                        "target_date": target_date,
                        "field_name": field_name,
                        "hour": hour,
                        "is_available": is_available,
                    }
                )

        partition_path = self._base_path / f"date={target_date}"
        partition_path.mkdir(parents=True, exist_ok=True)
        filename = f"snapshot-{collected_at.strftime('%H%M%S%f')}.parquet"
        pq.write_table(pa.Table.from_pylist(rows), partition_path / filename, compression="zstd")
