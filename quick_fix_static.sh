#!/bin/bash
# 즉시 정적 파일 문제 해결 - 간단한 방법

set -e

echo "🚀 정적 파일 수집 문제 즉시 해결"
echo "================================"

cd /home/ubuntu/4th_project/elderly_rag_chatbot
source venv/bin/activate

# 방법 1: 환경변수 해제하고 프로젝트 내 디렉토리 사용
echo "1️⃣ 환경변수 해제하고 프로젝트 내 staticfiles 사용"
unset STATIC_ROOT
mkdir -p staticfiles
python manage.py collectstatic --noinput

echo "✅ 완료!"
echo ""
echo "🎯 다음 명령어를 실행하세요:"
echo "python manage.py createsuperuser"