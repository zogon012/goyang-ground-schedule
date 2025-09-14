# Python 3.12 슬림 이미지 사용
FROM python:3.12-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 의존성 설치 (BeautifulSoup용)
RUN apt-get update && apt-get install -y \
    && rm -rf /var/lib/apt/lists/*

# Poetry 설치
RUN pip install poetry

# Poetry 설정 - 가상환경을 만들지 않고 시스템에 직접 설치
RUN poetry config virtualenvs.create false

# Poetry 파일들 복사
COPY pyproject.toml poetry.lock ./

# 의존성 설치
RUN poetry install --only=main --no-root

# 소스 코드 복사
COPY . .

# 포트 노출
EXPOSE 8000

# FastAPI 서버 실행
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
