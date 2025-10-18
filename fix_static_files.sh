#!/bin/bash
# 정적 파일 수집을 위한 권한 및 디렉토리 설정 스크립트

set -e

echo "🔧 정적 파일 수집을 위한 디렉토리 설정 중..."

# 현재 프로젝트 디렉토리로 이동
cd /home/ubuntu/4th_project/elderly_rag_chatbot
source venv/bin/activate

# 현재 STATIC_ROOT 설정 확인
echo "📋 현재 STATIC_ROOT 설정 확인:"
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django_settings')
django.setup()
from django.conf import settings
print('STATIC_ROOT:', settings.STATIC_ROOT)
print('STATIC_URL:', settings.STATIC_URL)
"

echo ""
echo "🔧 해결 방법 1: 프로젝트 내 staticfiles 디렉토리 사용 (권장)"
echo "================================================"

# 프로젝트 내 staticfiles 디렉토리 생성 및 권한 설정
mkdir -p staticfiles
chmod 755 staticfiles

# STATIC_ROOT 환경변수 해제하고 collectstatic 실행
echo "🚀 STATIC_ROOT를 프로젝트 디렉토리로 설정하여 collectstatic 실행..."
unset STATIC_ROOT
python manage.py collectstatic --noinput

echo "✅ 정적 파일 수집 완료 (프로젝트 디렉토리 사용)"

echo ""
echo "🔧 해결 방법 2: /var/www 디렉토리 사용하고 싶다면"
echo "=============================================="
echo "sudo mkdir -p /var/www/elderly_rag/static"
echo "sudo chown -R ubuntu:www-data /var/www/elderly_rag"
echo "sudo chmod -R 755 /var/www/elderly_rag"
echo "export STATIC_ROOT=/var/www/elderly_rag/static"
echo "python manage.py collectstatic --noinput"

echo ""
echo "📋 권장사항:"
echo "- 개발/테스트: 프로젝트 내 staticfiles 디렉토리 사용"
echo "- 프로덕션 배포: /var/www 디렉토리 사용 + Nginx 설정"

echo ""
echo "🎯 다음 단계:"
echo "1. 정적 파일 수집이 완료되었으면 슈퍼유저를 생성하세요:"
echo "   python manage.py createsuperuser"
echo ""
echo "2. 또는 자동 관리자 생성 스크립트를 사용하세요:"
echo "   python create_admin.py"