import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any

import pytz
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from schedule_service import ScheduleService
from schedule_store import ScheduleStore

VERSION = "1.1.0"
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/schedules.db")
REFRESH_MIN_SECONDS = int(os.getenv("REFRESH_MIN_SECONDS", "180"))
REFRESH_MAX_SECONDS = int(os.getenv("REFRESH_MAX_SECONDS", "420"))
COLLECTOR_ENABLED = os.getenv("COLLECTOR_ENABLED", "true").lower() == "true"

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.WARNING),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

schedule_service = ScheduleService(
    store=ScheduleStore(DATABASE_PATH),
    refresh_min_seconds=REFRESH_MIN_SECONDS,
    refresh_max_seconds=REFRESH_MAX_SECONDS,
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    await schedule_service.initialize()
    if COLLECTOR_ENABLED:
        schedule_service.start()
    yield
    await schedule_service.stop()


app = FastAPI(title="축구장 예약 현황 API", version=VERSION, lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def root() -> FileResponse:
    return FileResponse("static/index.html")


@app.get("/current-time")
async def get_current_time() -> dict[str, Any]:
    kst = pytz.timezone("Asia/Seoul")
    now = datetime.now(kst)
    return {
        "current_time": now.strftime("%H:%M:%S"),
        "current_hour": now.hour,
        "current_minute": now.minute,
        "current_second": now.second,
        "timestamp": now.isoformat(),
    }


@app.get("/today")
async def get_today_schedule() -> dict[str, Any]:
    snapshot, metadata = await schedule_service.get_today()
    if snapshot is None:
        raise HTTPException(
            status_code=503,
            detail={"message": "수집된 예약 데이터가 없습니다.", "metadata": metadata},
        )
    return {**snapshot.payload, "metadata": metadata}


@app.get("/today/raw")
async def get_today_schedule_raw() -> dict[str, Any]:
    snapshot, _ = await schedule_service.get_today()
    if snapshot is None:
        raise HTTPException(status_code=503, detail="수집된 예약 데이터가 없습니다.")
    return snapshot.payload.get("fields", {})


@app.get("/health")
async def health_check() -> dict[str, Any]:
    snapshot, metadata = await schedule_service.get_today()
    return {
        "status": "healthy",
        "version": VERSION,
        "data_available": snapshot is not None,
        "collector_enabled": COLLECTOR_ENABLED,
        "metadata": metadata,
    }
