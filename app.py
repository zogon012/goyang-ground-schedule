#!/usr/bin/env python3
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from simple import get_today_complete_info_json, get_today_complete_info, TimeEncoder
from datetime import datetime, timedelta
import pytz
import json
import asyncio
import os
import logging
from typing import Optional

# 환경 변수 설정
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "WARNING").upper()

# 로깅 설정
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="축구장 예약 현황 API", version="1.0.0")

# 캐시 저장소
cache = {"data": None, "last_updated": None, "lock": asyncio.Lock()}

CACHE_DURATION = timedelta(minutes=1)  # 1분 캐시

# 정적 파일 서빙
app.mount("/static", StaticFiles(directory="static"), name="static")


async def get_cached_schedule_data():
    """캐시된 스케줄 데이터를 반환하거나, 필요시 새로 가져옴"""
    now = datetime.now()

    async with cache["lock"]:
        # 캐시가 없거나 만료된 경우
        if (
            cache["data"] is None
            or cache["last_updated"] is None
            or now - cache["last_updated"] > CACHE_DURATION
        ):

            logger.info("캐시 만료 - 새로운 데이터 가져오는 중...")

            # 새 데이터 가져오기 - JSON 형태로 가져와서 파싱
            try:
                json_data = get_today_complete_info_json()
                schedule_data = json.loads(json_data)
                cache["data"] = schedule_data
                cache["last_updated"] = now
                logger.info("캐시 업데이트 완료")
            except Exception as e:
                logger.error(f"데이터 가져오기 실패: {str(e)}")
                # 기존 캐시 데이터가 있으면 그것을 사용
                if cache["data"] is not None:
                    logger.warning("기존 캐시 데이터 사용")
                else:
                    raise e
        else:
            remaining_time = CACHE_DURATION - (now - cache["last_updated"])
            if DEBUG:
                logger.debug(
                    f"캐시 사용 중 (남은 시간: {int(remaining_time.total_seconds())}초)"
                )

    return cache["data"]


@app.get("/")
async def root():
    """기본 엔드포인트 - HTML 페이지 반환"""
    return FileResponse("static/index.html")


@app.get("/current-time")
async def get_current_time():
    """현재 KST 시간 반환"""
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
async def get_today_schedule():
    """오늘의 축구장 예약 현황 (JSON 형태 반환) - 1분 캐시 적용"""
    schedule_data = await get_cached_schedule_data()
    return schedule_data


@app.get("/today/raw")
async def get_today_schedule_raw():
    """오늘의 축구장 예약 현황 (필드 데이터만) - 1분 캐시 적용"""
    schedule_data = await get_cached_schedule_data()
    return schedule_data.get("fields", {})


# 헬스체크 엔드포인트
@app.get("/health")
async def health_check():
    """서버 상태 확인용 헬스체크 엔드포인트"""
    try:
        # 캐시 시스템 동작 확인
        now = datetime.now()
        cache_healthy = cache["lock"] is not None

        # 기본적인 API 동작 확인
        kst = pytz.timezone("Asia/Seoul")
        current_time = datetime.now(kst)

        return {
            "status": "healthy",
            "timestamp": current_time.isoformat(),
            "cache_system": "operational" if cache_healthy else "error",
            "version": "1.0.0",
        }
    except Exception as e:
        logger.error(f"헬스체크 실패: {str(e)}")
        return {"status": "unhealthy", "error": "system_error" if not DEBUG else str(e)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
