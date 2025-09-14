#!/bin/bash

# 간단한 테스트 실행 스크립트
echo "테스트 실행 중..."

# 단위 테스트 실행
poetry run pytest tests/test_simple.py -v

echo "테스트 완료!"
