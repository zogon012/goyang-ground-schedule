#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from datetime import date, time, datetime
from pydantic import BaseModel
from typing import List
import re
import json
import pytz

# 상수 정의
TOTAL_FIELDS = 8  # 1~7번 필드 (range에서는 8까지)
KST = pytz.timezone("Asia/Seoul")


class TimeEncoder(json.JSONEncoder):
    """time 객체를 JSON으로 직렬화하는 커스텀 인코더"""

    def default(self, obj):
        if isinstance(obj, time):
            return obj.strftime("%H:%M")
        return super().default(obj)


class Match(BaseModel):
    """경기 정보 모델"""

    date: date
    field_name: str
    team_name: str
    start_time: time
    end_time: time


class FieldSchedule(BaseModel):
    """구장 스케줄 모델"""

    field_name: str
    matches: List[Match]


class DaySchedule(BaseModel):
    """하루 전체 스케줄 모델"""

    date: date
    fields: List[FieldSchedule]


def parse_time_slot(time_slot: str) -> tuple[time, time]:
    """시간 문자열을 파싱해서 시작시간, 끝시간 반환"""
    # "07시 ~ 10시 (3시간)" 패턴
    pattern = r"(\d{1,2})시\s*~\s*(\d{1,2})시"
    match = re.search(pattern, time_slot)

    if match:
        start_hour = int(match.group(1))
        end_hour = int(match.group(2))
        return time(start_hour, 0), time(end_hour, 0)
    else:
        return time(0, 0), time(0, 0)


def get_schedule(target_date=None) -> DaySchedule:
    """BeautifulSoup로 간단하게 스케줄 가져오기"""
    if target_date is None:
        target_date = date.today()

    url = "https://e-soccer.gys.or.kr"
    params = {
        "nyear": str(target_date.year),
        "nmonth": str(target_date.month),
        "nday": str(target_date.day),
    }

    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, params=params, headers=headers, timeout=10)
    response.encoding = "euc-kr"
    soup = BeautifulSoup(response.text, "html.parser")

    games_section = soup.find("div", class_="notice_box h_size")
    if not games_section:
        return DaySchedule(date=target_date, fields=[])

    fields = []

    for game_index in range(1, TOTAL_FIELDS):
        # 경기장 이름
        title_h3 = games_section.find("h3", {"id": f"h3Game{game_index}"})
        field_name = title_h3.text.strip() if title_h3 else f"경기장{game_index}"

        # 경기 목록
        ul = games_section.find("ul", {"id": f"ulMainGame{game_index}"})
        matches = []

        if ul:
            current_team = ""  # 현재 팀명 저장

            for li in ul.find_all("li"):
                title_span = li.find("span", class_="title")
                date_span = li.find("span", class_="date")

                # 팀명이 있으면 업데이트
                if title_span and title_span.text.strip():
                    current_team = title_span.text.strip()

                # 시간 정보가 있으면 매치 추가
                if date_span and date_span.text.strip():
                    time_slot = date_span.text.strip()

                    # 팀명이 없으면 "공백"으로 처리
                    team_name = current_team if current_team else "이름없음"

                    start_time, end_time = parse_time_slot(time_slot)
                    matches.append(
                        Match(
                            date=target_date,
                            field_name=field_name,
                            team_name=team_name,
                            start_time=start_time,
                            end_time=end_time,
                        )
                    )

        fields.append(FieldSchedule(field_name=field_name, matches=matches))

    return DaySchedule(date=target_date, fields=fields)


def get_empty_slots(schedule: DaySchedule) -> dict:
    """빈 시간 체크"""
    empty_slots = {}

    for field in schedule.fields:
        field_empty = []

        # 예약된 시간들을 시간 순으로 정렬
        booked_times = [
            (match.start_time.hour, match.end_time.hour) for match in field.matches
        ]
        booked_times.sort()

        if not booked_times:
            # 예약이 없으면 전체 시간 비어있음
            field_empty.append({"start_time": time(7, 0), "end_time": time(22, 0)})
        else:
            current_hour = 7

            for start_hour, end_hour in booked_times:
                if current_hour < start_hour:
                    field_empty.append(
                        {
                            "start_time": time(current_hour, 0),
                            "end_time": time(start_hour, 0),
                        }
                    )
                current_hour = max(current_hour, end_hour)

            if current_hour < 22:
                field_empty.append(
                    {"start_time": time(current_hour, 0), "end_time": time(22, 0)}
                )

        empty_slots[field.field_name] = field_empty

    return empty_slots


def get_today_empty_slots() -> dict:
    """오늘의 빈 시간을 반환하는 순수 함수 (KST 기준)"""
    # KST 기준 현재 날짜 계산
    kst_now = datetime.now(KST)
    today = kst_now.date()

    schedule = get_schedule(today)
    return get_empty_slots(schedule)


def get_today_complete_info() -> dict:
    """오늘의 빈 시간과 예약 정보를 모두 반환하는 함수 (KST 기준)"""
    # KST 기준 현재 날짜 계산
    kst_now = datetime.now(KST)
    today = kst_now.date()

    schedule = get_schedule(today)
    empty_slots = get_empty_slots(schedule)

    complete_info = {}

    for field in schedule.fields:
        # 예약된 팀 정보
        booked_matches = []
        for match in field.matches:
            booked_matches.append(
                {
                    "team_name": match.team_name,
                    "start_time": match.start_time,
                    "end_time": match.end_time,
                }
            )

        complete_info[field.field_name] = {
            "empty_slots": empty_slots.get(field.field_name, []),
            "booked_matches": booked_matches,
        }

    return complete_info


def get_today_complete_info_json() -> str:
    """오늘의 완전한 정보를 JSON으로 반환하는 함수 (KST 기준)"""
    # KST 기준 현재 날짜 계산
    kst_now = datetime.now(KST)
    today = kst_now.date()
    weekday = ["월", "화", "수", "목", "금", "토", "일"][today.weekday()]

    complete_info = get_today_complete_info()

    result = {
        "date": today.strftime("%Y-%m-%d"),
        "weekday": weekday,
        "fields": complete_info,
    }

    return json.dumps(result, ensure_ascii=False, indent=2, cls=TimeEncoder)


def main():
    """메인 실행 함수"""
    json_result = get_today_complete_info_json()
    print(json_result)


if __name__ == "__main__":
    main()
