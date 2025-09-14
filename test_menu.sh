#!/bin/bash

# 테스트 선택 스크립트
echo "축구장 예약 시스템 테스트"
echo "=========================="
echo "실행할 테스트를 선택하세요:"
echo ""
echo "1) 단위 테스트만 (빠름)"
echo "2) FastAPI 테스트만"
echo "3) 모든 테스트 (단위 + FastAPI)"
echo "4) 통합 테스트 (서버 필요)"
echo "5) 커버리지 포함 테스트"
echo "6) 종료"
echo ""

read -p "선택 (1-6): " choice

case $choice in
    1)
        echo "단위 테스트 실행 중..."
        poetry run pytest tests/test_simple.py -v
        ;;
    2)
        echo "FastAPI 테스트 실행 중..."
        poetry run pytest tests/test_app.py -v
        ;;
    3)
        echo "모든 기본 테스트 실행 중..."
        poetry run pytest tests/test_simple.py tests/test_app.py -v
        ;;
    4)
        echo "통합 테스트 실행 중..."
        echo "주의: 서버가 실행되어야 합니다 (docker-compose up -d)"
        poetry run pytest tests/test_integration.py -v
        ;;
    5)
        echo "커버리지 테스트 실행 중..."
        poetry run pytest --cov=. --cov-report=html --cov-report=term-missing tests/test_simple.py tests/test_app.py
        echo "커버리지 리포트: htmlcov/index.html"
        ;;
    6)
        echo "종료합니다."
        exit 0
        ;;
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac

echo ""
echo "테스트 완료!"
