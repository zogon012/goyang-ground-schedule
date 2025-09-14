# 축구장 예약 현황 모니터링 시스템

> **Version 1.0.0** - 고양시 축구장 실시간 예약 현황 확인

## 개요

고양시 축구장의 실시간 예약 현황을 확인할 수 있는 웹 애플리케이션입니다.
빈 시간대를 한눈에 파악하고, 시간대별 예약 가능한 구장을 쉽게 찾을 수 있습니다.

## 주요 기능

- **7개 축구장 실시간 현황** (별무리, 백석, 중산, 충장, 대화, 지영, 신원)
- **시간대별 빈 구장 안내** (07:00 ~ 22:00)
- **실시간 시계** (초 단위 업데이트, KST)
- **반응형 디자인** (모바일/데스크톱)
- **1분 캐시** (과도한 크롤링 방지)

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
# 로컬: http://localhost:8000
# 네트워크: http://192.168.0.70:8000 (실제 서버 IP)
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

# 버전 확인 (로컬)
curl http://localhost:8000/health | jq '.version'

# 버전 확인 (네트워크)
curl http://192.168.0.70:8000/health | jq '.version'
```

## 네트워크 접근

서버는 다음 주소로 접근 가능합니다:

- **로컬 접근**: `http://localhost:8000`
- **네트워크 접근**: `http://192.168.0.70:8000`

Docker 컨테이너는 `0.0.0.0:8000`에서 실행되므로 같은 네트워크의 다른 기기에서도 접근할 수 있습니다.

### 방화벽 설정

macOS에서 다른 기기의 접근을 허용하려면:

```bash
# 방화벽 상태 확인
sudo /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate

# 포트 8000 허용 (필요시)
sudo pfctl -f /etc/pf.conf
```

## 환경 변수

| 변수 | 기본값 | 설명 |
|------|--------|------|
| `DEBUG` | false | 디버그 모드 |
| `LOG_LEVEL` | WARNING | 로그 레벨 |

## 라이선스

MIT License

## 기여

이슈와 풀 리퀘스트를 환영합니다!

---

**첫 번째 릴리스** - 2025.09.14
