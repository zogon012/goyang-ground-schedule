import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime, date, time, timedelta
import json
from app import app, get_cached_schedule_data, cache, CACHE_DURATION


class TestFastAPIApp:
    """FastAPI 애플리케이션 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.client = TestClient(app)
        # 캐시 초기화
        cache["data"] = None
        cache["last_updated"] = None

    def test_root_endpoint(self):
        """루트 엔드포인트 테스트"""
        response = self.client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_current_time_endpoint(self):
        """현재 시간 엔드포인트 테스트"""
        response = self.client.get("/current-time")
        assert response.status_code == 200

        data = response.json()
        required_fields = [
            "current_time",
            "current_hour",
            "current_minute",
            "current_second",
            "timestamp",
        ]

        for field in required_fields:
            assert field in data

        # 시간 형식 검증
        assert isinstance(data["current_hour"], int)
        assert 0 <= data["current_hour"] <= 23
        assert isinstance(data["current_minute"], int)
        assert 0 <= data["current_minute"] <= 59

    @patch("app.get_today_complete_info_json")
    def test_today_endpoint(self, mock_get_info):
        """today 엔드포인트 테스트"""
        # Mock 데이터 준비
        mock_json_data = json.dumps(
            {
                "date": "2025-09-14",
                "weekday": "일",
                "fields": {
                    "테스트구장": {
                        "empty_slots": [{"start_time": "07:00", "end_time": "10:00"}],
                        "booked_matches": [
                            {
                                "team_name": "테스트팀",
                                "start_time": "10:00",
                                "end_time": "13:00",
                            }
                        ],
                    }
                },
            }
        )
        mock_get_info.return_value = mock_json_data

        response = self.client.get("/today")
        assert response.status_code == 200

        data = response.json()
        assert "date" in data
        assert "weekday" in data
        assert "fields" in data
        assert "테스트구장" in data["fields"]

    @patch("app.get_today_complete_info_json")
    def test_today_raw_endpoint(self, mock_get_info):
        """today/raw 엔드포인트 테스트"""
        mock_json_data = json.dumps(
            {
                "date": "2025-09-14",
                "weekday": "일",
                "fields": {"테스트구장": {"empty_slots": [], "booked_matches": []}},
            }
        )
        mock_get_info.return_value = mock_json_data

        response = self.client.get("/today/raw")
        assert response.status_code == 200

        data = response.json()
        # raw 엔드포인트는 fields 부분만 반환
        assert "테스트구장" in data
        assert "empty_slots" in data["테스트구장"]
        assert "booked_matches" in data["테스트구장"]

    def test_health_endpoint(self):
        """헬스체크 엔드포인트 테스트"""
        response = self.client.get("/health")
        assert response.status_code == 200

        data = response.json()
        required_fields = ["status", "timestamp", "cache_system", "version"]

        for field in required_fields:
            assert field in data

        assert data["status"] in ["healthy", "unhealthy"]
        assert data["version"] == "1.0.0"

    def test_static_files_mounting(self):
        """정적 파일 마운팅 테스트"""
        # 정적 파일 경로 접근 테스트 (실제 파일이 없어도 마운팅 여부 확인)
        response = self.client.get("/static/test.txt")
        # 404는 정상 (파일이 없음), 500이나 다른 에러가 나면 마운팅 문제
        assert response.status_code in [404, 200]


class TestCacheSystem:
    """캐시 시스템 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 캐시 초기화"""
        cache["data"] = None
        cache["last_updated"] = None

    @pytest.mark.asyncio
    @patch("app.get_today_complete_info_json")
    async def test_cache_miss(self, mock_get_info):
        """캐시 미스 시 새 데이터 가져오기 테스트"""
        mock_json_data = json.dumps(
            {
                "date": "2025-09-14",
                "weekday": "일",
                "fields": {"테스트구장": {"empty_slots": [], "booked_matches": []}},
            }
        )
        mock_get_info.return_value = mock_json_data

        result = await get_cached_schedule_data()

        assert result is not None
        assert cache["data"] is not None
        assert cache["last_updated"] is not None
        mock_get_info.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.get_today_complete_info_json")
    async def test_cache_hit(self, mock_get_info):
        """캐시 히트 시 기존 데이터 사용 테스트"""
        # 캐시에 데이터 미리 설정
        test_data = {"test": "cached_data"}
        cache["data"] = test_data
        cache["last_updated"] = datetime.now()

        result = await get_cached_schedule_data()

        assert result == test_data
        # 새로운 데이터를 가져오지 않아야 함
        mock_get_info.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.get_today_complete_info_json")
    async def test_cache_expiry(self, mock_get_info):
        """캐시 만료 시 새 데이터 가져오기 테스트"""
        # 만료된 캐시 데이터 설정
        old_data = {"test": "old_data"}
        cache["data"] = old_data
        cache["last_updated"] = datetime.now() - CACHE_DURATION - timedelta(seconds=1)

        new_json_data = json.dumps(
            {
                "date": "2025-09-14",
                "weekday": "일",
                "fields": {"테스트구장": {"empty_slots": [], "booked_matches": []}},
            }
        )
        mock_get_info.return_value = new_json_data

        result = await get_cached_schedule_data()

        assert result != old_data  # 새로운 데이터여야 함
        assert cache["data"] != old_data  # 캐시도 업데이트되어야 함
        mock_get_info.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.get_today_complete_info_json")
    async def test_cache_error_fallback(self, mock_get_info):
        """데이터 가져오기 실패 시 기존 캐시 사용 테스트"""
        # 기존 캐시 데이터 설정
        old_data = {"test": "fallback_data"}
        cache["data"] = old_data
        cache["last_updated"] = datetime.now() - CACHE_DURATION - timedelta(seconds=1)

        # Mock에서 예외 발생시키기
        mock_get_info.side_effect = Exception("네트워크 오류")

        result = await get_cached_schedule_data()

        assert result == old_data  # 기존 데이터 반환
        mock_get_info.assert_called_once()


class TestErrorHandling:
    """에러 처리 테스트"""

    def setup_method(self):
        """각 테스트 메서드 실행 전 설정"""
        self.client = TestClient(app)

    @patch("app.get_cached_schedule_data")
    def test_today_endpoint_error(self, mock_get_data):
        """today 엔드포인트 에러 처리 테스트"""
        mock_get_data.side_effect = Exception("데이터 가져오기 실패")

        response = self.client.get("/today")
        assert response.status_code == 500

    def test_health_endpoint_error_handling(self):
        """헬스체크 엔드포인트 에러 처리 테스트"""
        with patch("app.datetime") as mock_datetime:
            mock_datetime.now.side_effect = Exception("시간 오류")

            response = self.client.get("/health")
            # 에러가 발생해도 응답은 받아야 함
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "unhealthy"
