#!/bin/bash

# 테스트 실행 스크립트

echo "축구장 예약 시스템 테스트 시작"
echo "=================================="

# 단위 테스트 실행
echo "단위 테스트 실행 중..."
poetry run pytest tests/test_simple.py tests/test_app.py -v --tb=short

if [ $? -ne 0 ]; then
    echo "단위 테스트 실패"
    exit 1
fi

echo "단위 테스트 완료"
echo ""

# 서버가 실행 중인지 확인
echo "서버 상태 확인 중..."
SERVER_RUNNING=$(curl -s http://localhost:8000/health > /dev/null && echo "true" || echo "false")

if [ "$SERVER_RUNNING" = "true" ]; then
    echo "서버가 실행 중입니다"
    echo ""
    
    # 통합 테스트 실행
    echo "통합 테스트 실행 중..."
    poetry run pytest tests/test_integration.py::TestIntegration -v --tb=short
    
    if [ $? -ne 0 ]; then
        echo "통합 테스트 실패"
        exit 1
    fi
    
    echo "통합 테스트 완료"
    echo ""
    
    # 성능 테스트 실행 (선택적)
    if [ "$1" = "--performance" ]; then
        echo "성능 테스트 실행 중..."
        poetry run pytest tests/test_integration.py::TestPerformance -v --tb=short
        
        if [ $? -ne 0 ]; then
            echo "성능 테스트에서 일부 문제 발견"
        else
            echo "성능 테스트 완료"
        fi
        echo ""
    fi
    
else
    echo "경고: 서버가 실행되지 않아 통합 테스트를 건너뜁니다"
    echo "   서버 실행: docker-compose up -d"
    echo ""
fi

# 테스트 커버리지 생성
echo "테스트 커버리지 생성 중..."
poetry run pytest --cov=. --cov-report=html --cov-report=term-missing tests/test_simple.py tests/test_app.py

echo ""
echo "모든 테스트 완료!"
echo "커버리지 리포트: htmlcov/index.html"
echo "=================================="
