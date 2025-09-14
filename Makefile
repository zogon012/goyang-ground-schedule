# Makefile for 축구장 예약 시스템

.PHONY: help install test test-unit test-integration test-performance test-coverage clean dev build up down logs

# 기본 도움말
help:
	@echo "축구장 예약 시스템 - 사용 가능한 명령어"
	@echo "================================================"
	@echo "설치 및 설정:"
	@echo "  install           - 의존성 설치"
	@echo "  dev              - 개발 서버 실행"
	@echo ""
	@echo "테스트:"
	@echo "  test             - 모든 테스트 실행"
	@echo "  test-unit        - 단위 테스트만 실행"
	@echo "  test-integration - 통합 테스트만 실행 (서버 필요)"
	@echo "  test-performance - 성능 테스트 실행 (서버 필요)"
	@echo "  test-coverage    - 커버리지 포함 테스트"
	@echo ""
	@echo "Docker 관리:"
	@echo "  build            - Docker 이미지 빌드"
	@echo "  up               - Docker 컨테이너 실행"
	@echo "  down             - Docker 컨테이너 중지"
	@echo "  logs             - Docker 로그 확인"
	@echo ""
	@echo "기타:"
	@echo "  clean            - 캐시 및 임시 파일 정리"

# 의존성 설치
install:
	poetry install

# 개발 서버 실행
dev:
	poetry run uvicorn app:app --reload --host 0.0.0.0 --port 8000

# 모든 테스트 실행
test:
	./run_tests.sh

# 단위 테스트만 실행
test-unit:
	poetry run pytest tests/test_simple.py tests/test_app.py -v

# 통합 테스트만 실행
test-integration:
	poetry run pytest tests/test_integration.py::TestIntegration -v

# 성능 테스트 실행
test-performance:
	poetry run pytest tests/test_integration.py::TestPerformance -v

# 커버리지 포함 테스트
test-coverage:
	poetry run pytest --cov=. --cov-report=html --cov-report=term-missing tests/test_simple.py tests/test_app.py

# Docker 이미지 빌드
build:
	docker-compose build

# Docker 컨테이너 실행
up:
	docker-compose up -d

# Docker 컨테이너 중지
down:
	docker-compose down

# Docker 로그 확인
logs:
	docker-compose logs -f

# 캐시 및 임시 파일 정리
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name ".pytest_cache" -delete
	rm -rf htmlcov/
	rm -rf .coverage
