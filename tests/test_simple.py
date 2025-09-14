import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, date, time
from simple import (
    get_schedule,
    get_empty_slots,
    get_today_complete_info,
    get_today_complete_info_json,
    TimeEncoder,
    DaySchedule,
    FieldSchedule,
    Match,
)
import json


class TestSimpleFunctions:
    """simple.py 모듈의 함수들을 테스트"""

    def test_time_encoder(self):
        """TimeEncoder가 time 객체를 올바르게 직렬화하는지 테스트"""
        test_time = time(14, 30)
        result = json.dumps({"time": test_time}, cls=TimeEncoder)
        expected = '{"time": "14:30"}'
        assert result == expected

    @patch("simple.requests.get")
    def test_get_schedule_success(self, mock_get):
        """get_schedule 함수가 정상적으로 동작하는지 테스트"""
        # Mock HTML 응답 준비
        mock_html = """
        <html>
        <body>
        <table>
        <tr><td>별무리</td><td>우주FC</td><td>07:00~10:00</td></tr>
        <tr><td>백석</td><td>장성FC</td><td>10:00~13:00</td></tr>
        </table>
        </body>
        </html>
        """
        mock_response = MagicMock()
        mock_response.text = mock_html
        mock_response.encoding = "utf-8"
        mock_get.return_value = mock_response

        test_date = date(2025, 9, 14)
        result = get_schedule(test_date)

        assert isinstance(result, DaySchedule)
        assert result.date == test_date
        mock_get.assert_called_once()

    def test_get_empty_slots(self):
        """빈 시간 슬롯 계산이 올바른지 테스트"""
        # 테스트용 스케줄 데이터 생성
        test_date = date(2025, 9, 14)
        matches = [
            Match(
                date=test_date,
                field_name="테스트구장",
                team_name="테스트팀1",
                start_time=time(10, 0),
                end_time=time(13, 0),
            ),
            Match(
                date=test_date,
                field_name="테스트구장",
                team_name="테스트팀2",
                start_time=time(16, 0),
                end_time=time(19, 0),
            ),
        ]
        field = FieldSchedule(field_name="테스트구장", matches=matches)
        schedule = DaySchedule(date=test_date, fields=[field])

        empty_slots = get_empty_slots(schedule)

        assert "테스트구장" in empty_slots
        field_empty = empty_slots["테스트구장"]

        # 예상되는 빈 시간: 07:00-10:00, 13:00-16:00, 19:00-22:00
        assert len(field_empty) == 3
        assert field_empty[0]["start_time"] == time(7, 0)
        assert field_empty[0]["end_time"] == time(10, 0)

    @patch("simple.get_schedule")
    def test_get_today_complete_info(self, mock_get_schedule):
        """완전한 정보 조회 함수 테스트"""
        # Mock 데이터 준비
        test_date = date(2025, 9, 14)
        matches = [
            Match(
                date=test_date,
                field_name="테스트구장",
                team_name="테스트팀",
                start_time=time(10, 0),
                end_time=time(13, 0),
            )
        ]
        field = FieldSchedule(field_name="테스트구장", matches=matches)
        mock_schedule = DaySchedule(date=test_date, fields=[field])
        mock_get_schedule.return_value = mock_schedule

        result = get_today_complete_info()

        assert "테스트구장" in result
        assert "empty_slots" in result["테스트구장"]
        assert "booked_matches" in result["테스트구장"]
        assert len(result["테스트구장"]["booked_matches"]) == 1
        assert result["테스트구장"]["booked_matches"][0]["team_name"] == "테스트팀"

    @patch("simple.get_today_complete_info")
    def test_get_today_complete_info_json(self, mock_get_info):
        """JSON 반환 함수 테스트"""
        # Mock 데이터 준비
        mock_info = {
            "테스트구장": {
                "empty_slots": [{"start_time": time(7, 0), "end_time": time(10, 0)}],
                "booked_matches": [
                    {
                        "team_name": "테스트팀",
                        "start_time": time(10, 0),
                        "end_time": time(13, 0),
                    }
                ],
            }
        }
        mock_get_info.return_value = mock_info

        with patch("simple.date") as mock_date:
            mock_date_instance = mock_date.today.return_value
            mock_date_instance.strftime.return_value = "2025-09-14"
            mock_date_instance.weekday.return_value = 6  # 일요일

            result = get_today_complete_info_json()

        # JSON이 올바르게 형성되었는지 확인
        parsed_result = json.loads(result)
        assert "date" in parsed_result
        assert "weekday" in parsed_result
        assert "fields" in parsed_result
        assert parsed_result["date"] == "2025-09-14"


class TestDataModels:
    """데이터 모델들의 동작을 테스트"""

    def test_match_creation(self):
        """Match 객체 생성 테스트"""
        match = Match(
            date=date(2025, 9, 14),
            field_name="테스트구장",
            team_name="테스트팀",
            start_time=time(10, 0),
            end_time=time(13, 0),
        )
        assert match.team_name == "테스트팀"
        assert match.start_time == time(10, 0)
        assert match.end_time == time(13, 0)
        assert match.field_name == "테스트구장"
        assert match.date == date(2025, 9, 14)

    def test_field_schedule_creation(self):
        """FieldSchedule 객체 생성 테스트"""
        test_date = date(2025, 9, 14)
        matches = [
            Match(
                date=test_date,
                field_name="테스트구장",
                team_name="팀1",
                start_time=time(10, 0),
                end_time=time(13, 0),
            ),
            Match(
                date=test_date,
                field_name="테스트구장",
                team_name="팀2",
                start_time=time(16, 0),
                end_time=time(19, 0),
            ),
        ]
        field = FieldSchedule(field_name="테스트구장", matches=matches)

        assert field.field_name == "테스트구장"
        assert len(field.matches) == 2
        assert field.matches[0].team_name == "팀1"

    def test_day_schedule_creation(self):
        """DaySchedule 객체 생성 테스트"""
        test_date = date(2025, 9, 14)
        matches = [
            Match(
                date=test_date,
                field_name="구장1",
                team_name="팀1",
                start_time=time(10, 0),
                end_time=time(13, 0),
            )
        ]
        field = FieldSchedule(field_name="구장1", matches=matches)
        schedule = DaySchedule(date=test_date, fields=[field])

        assert schedule.date == date(2025, 9, 14)
        assert len(schedule.fields) == 1
        assert schedule.fields[0].field_name == "구장1"
