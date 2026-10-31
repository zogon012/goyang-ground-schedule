# 축구장 예약 현황 모니터링 시스템

> **Version 1.1.1** - 고양시 축구장 실시간 예약 현황 확인

## 개요

고양시 축구장의 실시간 예약 현황을 확인할 수 있는 웹 애플리케이션입니다.
빈 시간대를 한눈에 파악하고, 시간대별 예약 가능한 구장을 쉽게 찾을 수 있습니다.

## 최근 변경

- `1.1.1`: 예약 현황 화면을 정보 중심으로 개편하고, 수집 주기를 45분에서 90분 사이로 조정했습니다.

버전은 SemVer를 따릅니다. 호환되지 않는 변경은 메이저, 기능 추가는 마이너, 버그 수정은 패치 버전을 올립니다.

## 주요 기능

- **7개 축구장 실시간 현황** (별무리, 백석, 중산, 충장, 대화, 지영, 신원)
- **시간대별 빈 구장 안내** (07:00 ~ 22:00)
- **실시간 시계** (초 단위 업데이트, KST)
- **반응형 디자인** (모바일/데스크톱)
- **45분에서 90분 무작위 수집** (과도한 크롤링 방지)

## 미리보기

```
┌─────────────────────────────────────────┐
│ 축구장 예약 현황        현재: 14:25:30  │
├─────────────────────────────────────────┤
│ 14:00-15:00  가능: 중산, 대화, 신원     │
│ 15:00-16:00  가능: 백석, 충장           │
│ 16:00-17:00  예약 가능한 구장 없음      │
│ 17:00-18:00  가능: 별무리, 지영         │
└─────────────────────────────────────────┘
```

## 빠른 시작

### Docker로 실행 (추천)

```bash
# 저장소 클론
git clone <repository-url>
cd ground

# 도커 실행
docker-compose up -d

# 웹 브라우저에서 접속
open http://localhost:8000
```

### 개발 환경 설정

```bash
# 의존성 설치
poetry install

# 개발 서버 실행
poetry run uvicorn app:app --reload --port 8000

# 테스트 실행
./test.sh
```

## API 엔드포인트

| 엔드포인트 | 설명 |
|------------|------|
| `/` | 메인 웹 페이지 |
| `/today` | 오늘의 예약 현황 (JSON) |
| `/current-time` | 현재 KST 시간 |
| `/health` | 서버 상태 확인 |

## 기술 스택

- **Backend**: Python 3.12, FastAPI, BeautifulSoup4
- **Frontend**: Vanilla JavaScript, CSS3
- **Deployment**: Docker, Docker Compose
- **Testing**: pytest, pytest-asyncio

## 테스트

```bash
# 모든 테스트 실행
make test

# 단위 테스트만
poetry run pytest tests/test_simple.py -v

# 통합 테스트 (서버 필요)
poetry run pytest tests/test_integration.py -v

# 버전 확인
curl http://localhost:8000/health | jq '.version'
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DEBUG` | false | 디버그 모드 |
| `LOG_LEVEL` | WARNING | 로그 레벨 |
| `DATABASE_PATH` | `data/schedules.db` | 예약 현황 저장소 경로 |
| `REFRESH_MIN_SECONDS` | 2700 | 최소 수집 주기(초) |
| `REFRESH_MAX_SECONDS` | 5400 | 최대 수집 주기(초) |

## 라이선스

MIT License

## 기여

작업 전 이슈를 생성하고, 이슈를 참조하는 풀 리퀘스트로 변경을 제안해 주세요.
작업 흐름, 병합 방식, 버전 및 문서 기준은 [CONTRIBUTING.md](CONTRIBUTING.md)를 확인해 주세요.

---

**첫 번째 릴리스** - 2025.09.14
