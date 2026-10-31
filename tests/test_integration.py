import pytest
import requests
import time
from datetime import datetime


@pytest.mark.integration
class TestIntegration:
    """실제 서버와의 통합 테스트"""

    BASE_URL = "http://localhost:8000"

    def test_server_health(self):
        """서버가 정상적으로 응답하는지 테스트"""
        try:
            response = requests.get(f"{self.BASE_URL}/health", timeout=5)
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "healthy"
            assert "timestamp" in data
            assert "version" in data
        except requests.exceptions.RequestException:
            pytest.skip("서버가 실행되지 않음")

    def test_api_endpoints_integration(self):
        """주요 API 엔드포인트들의 통합 테스트"""
        endpoints = ["/", "/current-time", "/today", "/today/raw", "/health"]

        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.BASE_URL}{endpoint}", timeout=10)
                assert response.status_code == 200, f"{endpoint} 엔드포인트 실패"

                # JSON 응답인 경우 파싱 테스트
                if endpoint in ["/current-time", "/today", "/today/raw", "/health"]:
                    response.json()  # JSON 파싱 에러가 없는지 확인

            except requests.exceptions.RequestException:
                pytest.skip(f"서버 접근 불가: {endpoint}")

    def test_cache_behavior_integration(self):
        """캐시 동작 통합 테스트"""
        try:
            # 첫 번째 요청
            start_time = time.time()
            response1 = requests.get(f"{self.BASE_URL}/today", timeout=10)
            first_duration = time.time() - start_time

            # 두 번째 요청 (캐시된 데이터 사용)
            start_time = time.time()
            response2 = requests.get(f"{self.BASE_URL}/today", timeout=10)
            second_duration = time.time() - start_time

            assert response1.status_code == 200
            assert response2.status_code == 200

            # 캐시로 인해 두 번째 요청이 더 빨라야 함
            assert second_duration < first_duration or second_duration < 0.5

            # 데이터 일관성 확인
            data1 = response1.json()
            data2 = response2.json()
            assert data1 == data2

        except requests.exceptions.RequestException:
            pytest.skip("서버가 실행되지 않음")

    def test_real_time_clock_integration(self):
        """실시간 시계 기능 통합 테스트"""
        try:
            response = requests.get(f"{self.BASE_URL}/current-time", timeout=5)
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
                assert field in data, f"{field} 필드가 누락됨"

            # 시간 값 유효성 검증
            assert 0 <= data["current_hour"] <= 23
            assert 0 <= data["current_minute"] <= 59
            assert 0 <= data["current_second"] <= 59

            # 타임스탬프 형식 검증
            timestamp = data["timestamp"]
            datetime.fromisoformat(timestamp.replace("Z", "+00:00"))  # ISO 형식 검증

        except requests.exceptions.RequestException:
            pytest.skip("서버가 실행되지 않음")

    def test_static_files_serving(self):
        """정적 파일 서빙 테스트"""
        try:
            # 메인 페이지 접근
            response = requests.get(f"{self.BASE_URL}/", timeout=5)
            assert response.status_code == 200
            assert "text/html" in response.headers.get("content-type", "")

        except requests.exceptions.RequestException:
            pytest.skip("서버가 실행되지 않음")


@pytest.mark.slow
class TestPerformance:
    """성능 테스트"""

    BASE_URL = "http://localhost:8000"

    def test_response_time_performance(self):
        """응답 시간 성능 테스트"""
        try:
            # 여러 번 요청해서 평균 응답 시간 측정
            response_times = []

            for _ in range(5):
                start_time = time.time()
                response = requests.get(f"{self.BASE_URL}/current-time", timeout=5)
                duration = time.time() - start_time

                assert response.status_code == 200
                response_times.append(duration)

            avg_response_time = sum(response_times) / len(response_times)

            # 평균 응답 시간이 1초 이하여야 함
            assert (
                avg_response_time < 1.0
            ), f"응답 시간이 너무 느림: {avg_response_time}s"

        except requests.exceptions.RequestException:
            pytest.skip("서버가 실행되지 않음")

    def test_concurrent_requests(self):
        """동시 요청 처리 테스트"""
        try:
            import threading
            import queue

            results = queue.Queue()

            def make_request():
                try:
                    response = requests.get(f"{self.BASE_URL}/current-time", timeout=5)
                    results.put(response.status_code)
                except Exception as e:
                    results.put(str(e))

            # 10개의 동시 요청
            threads = []
            for _ in range(10):
                thread = threading.Thread(target=make_request)
                threads.append(thread)
                thread.start()

            # 모든 스레드 완료 대기
            for thread in threads:
                thread.join(timeout=10)

            # 결과 확인
            success_count = 0
            while not results.empty():
                result = results.get()
                if result == 200:
                    success_count += 1

            if success_count == 0:
                pytest.skip("서버가 실행되지 않음")

            # 최소 80% 성공률
            assert success_count >= 8, f"동시 요청 성공률이 낮음: {success_count}/10"

        except requests.exceptions.RequestException:
            pytest.skip("서버가 실행되지 않음")
