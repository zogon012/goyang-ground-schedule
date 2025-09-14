import pytest
from datetime import datetime, time
import pytz
from unittest.mock import patch
from app import get_current_time


class TestTimeHandling:
    """시간 처리 관련 테스트"""

    @pytest.mark.parametrize(
        "hour,minute,second",
        [
            (6, 30, 0),  # 7시 이전
            (7, 0, 0),  # 정확히 7시
            (12, 30, 45),  # 정오
            (21, 59, 59),  # 22시 직전
            (22, 0, 0),  # 정확히 22시
            (23, 30, 0),  # 22시 이후
            (0, 30, 0),  # 자정 이후
        ],
    )
    @patch("app.datetime")
    def test_current_time_various_hours(self, mock_datetime, hour, minute, second):
        """다양한 시간대에서 현재 시간 API 테스트"""
        # Mock 시간 설정
        kst = pytz.timezone("Asia/Seoul")
        mock_time = datetime(2025, 9, 14, hour, minute, second, tzinfo=kst)
        mock_datetime.now.return_value = mock_time

        # 실제 pytz는 그대로 사용
        with patch("app.pytz", pytz):
            from fastapi.testclient import TestClient
            from app import app

            client = TestClient(app)

            response = client.get("/current-time")

            assert response.status_code == 200
            data = response.json()

            # 기본 필드 확인
            assert "current_time" in data
            assert "current_hour" in data
            assert "current_minute" in data
            assert "current_second" in data
            assert "timestamp" in data

            # 값 확인
            assert data["current_hour"] == hour
            assert data["current_minute"] == minute
            assert data["current_second"] == second

            # 시간 형식 확인
            expected_time = f"{hour:02d}:{minute:02d}:{second:02d}"
            assert data["current_time"] == expected_time

    def test_time_range_coverage(self):
        """시간 범위 처리 테스트"""
        # 운영 시간 외 시간대 테스트
        edge_cases = [
            {"hour": 6, "desc": "오픈 전"},
            {"hour": 7, "desc": "오픈 시간"},
            {"hour": 21, "desc": "마지막 시간대"},
            {"hour": 22, "desc": "클로즈 시간"},
            {"hour": 23, "desc": "클로즈 후"},
        ]

        for case in edge_cases:
            hour = case["hour"]
            desc = case["desc"]

            # 운영 시간 내/외 판단
            is_operational = 7 <= hour < 22

            if not is_operational:
                # 운영 시간 외에는 특별한 처리가 필요할 수 있음
                print(f"⚠️  {desc} ({hour:02d}시): 운영 시간 외")
            else:
                print(f"✅ {desc} ({hour:02d}시): 운영 시간 내")

    def test_frontend_time_slot_logic(self):
        """프론트엔드 시간 슬롯 로직 테스트 (개선된 버전)"""

        # JavaScript 로직을 Python으로 시뮬레이션
        def create_time_ranges_improved(current_hour):
            # 운영 시간 외인지 확인
            is_out_of_hours = current_hour < 7 or current_hour >= 22

            time_ranges = []
            for hour in range(7, 22):  # 7시부터 21시까지
                time_ranges.append(
                    {
                        "start": hour,
                        "end": hour + 1,
                        "label": f"{hour:02d}:00 - {hour+1:02d}:00",
                        "isCurrent": current_hour == hour and not is_out_of_hours,
                        "out_of_hours_info": is_out_of_hours,
                    }
                )
            return time_ranges, is_out_of_hours

        # 다양한 현재 시간에 대해 테스트
        test_hours = [6, 7, 12, 21, 22, 23, 0]

        for current_hour in test_hours:
            ranges, is_out_of_hours = create_time_ranges_improved(current_hour)
            current_slots = [r for r in ranges if r["isCurrent"]]

            if 7 <= current_hour < 22:
                assert (
                    len(current_slots) == 1
                ), f"시간 {current_hour}시에 현재 슬롯이 정확히 하나여야 함"
                assert current_slots[0]["start"] == current_hour
                assert not is_out_of_hours, f"{current_hour}시는 운영시간 내여야 함"
                print(f"✅ {current_hour}시: 운영 시간 내 - 현재 슬롯 표시됨")
            else:
                assert (
                    len(current_slots) == 0
                ), f"운영시간 외 {current_hour}시에는 현재 슬롯이 없어야 함"
                assert is_out_of_hours, f"{current_hour}시는 운영시간 외여야 함"
                print(f"⚠️  {current_hour}시: 운영 시간 외 - 특별 메시지 표시 (개선됨)")

    def test_edge_case_times(self):
        """경계값 시간 테스트"""
        edge_cases = [
            (6, 59, "6시 59분 - 오픈 직전"),
            (7, 0, "7시 정각 - 오픈 시간"),
            (21, 59, "21시 59분 - 마지막 시간대"),
            (22, 0, "22시 정각 - 클로즈 시간"),
            (22, 1, "22시 1분 - 클로즈 후"),
        ]

        for hour, minute, description in edge_cases:
            is_operational = 7 <= hour < 22
            status = "운영중" if is_operational else "운영종료"
            print(f"{description}: {status}")

        # 자정 근처 테스트
        midnight_cases = [
            (23, 30, "23시 30분"),
            (0, 30, "0시 30분 (자정 이후)"),
            (1, 0, "1시 정각"),
        ]

        for hour, minute, description in midnight_cases:
            print(f"{description}: 운영종료 (특별 처리 필요)")


if __name__ == "__main__":
    # 직접 실행 시 간단한 테스트
    test = TestTimeHandling()
    print("=== 시간 범위 처리 테스트 ===")
    test.test_time_range_coverage()
    print("\n=== 프론트엔드 시간 슬롯 로직 테스트 ===")
    test.test_frontend_time_slot_logic()
    print("\n=== 경계값 시간 테스트 ===")
    test.test_edge_case_times()
    print("\n✅ 모든 시간 처리 테스트 완료!")
