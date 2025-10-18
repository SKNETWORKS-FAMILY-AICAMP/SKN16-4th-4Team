#!/usr/bin/env bash
set -euo pipefail

# validate_setup.sh - 설치 상태 검증 스크립트
# 용도: 배포 후 시스템이 정상 작동하는지 확인

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔍 elderly_rag_chatbot 설치 상태 검증"
echo "========================================"

# 1. Python 환경 확인
echo "1. Python 환경 검증..."
if [ -d "$PROJECT_DIR/venv" ]; then
    echo "   ✓ 가상환경 존재"
    source "$PROJECT_DIR/venv/bin/activate"
    echo "   ✓ Python $(python --version)"
else
    echo "   ✗ 가상환경 없음"
    exit 1
fi

# 2. Django 설정 검증
echo "2. Django 설정 검증..."
export DJANGO_SETTINGS_MODULE=config.django_settings
if python manage.py check --deploy 2>/dev/null; then
    echo "   ✓ Django 설정 정상"
else
    echo "   ⚠ Django 설정 경고 (일부 프로덕션 설정 필요)"
fi

# 3. 데이터베이스 연결 확인
echo "3. 데이터베이스 연결 검증..."
if python manage.py migrate --check 2>/dev/null; then
    echo "   ✓ 데이터베이스 마이그레이션 상태 정상"
else
    echo "   ⚠ 마이그레이션 필요 또는 DB 연결 문제"
fi

# 4. 필수 파일 존재 확인
echo "4. 필수 파일 검증..."
required_files=(
    "manage.py"
    "config/django_settings.py"
    "config/urls.py"
    "config/wsgi.py"
    "chatbot_web/models.py"
    "chatbot_web/views.py"
    ".env"
    "requirements.txt"
)

for file in "${required_files[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ✗ $file 없음"
    fi
done

# 5. 서비스 상태 확인
echo "5. 시스템 서비스 검증..."
if systemctl is-active --quiet elderly_rag_gunicorn 2>/dev/null; then
    echo "   ✓ Gunicorn 서비스 실행 중"
else
    echo "   ⚠ Gunicorn 서비스 비활성 또는 없음"
fi

if systemctl is-active --quiet nginx 2>/dev/null; then
    echo "   ✓ Nginx 서비스 실행 중"
else
    echo "   ⚠ Nginx 서비스 비활성 또는 없음"
fi

# 6. 포트 확인
echo "6. 네트워크 포트 검증..."
if netstat -tuln 2>/dev/null | grep -q ":80 "; then
    echo "   ✓ HTTP 포트 (80) 리스닝"
else
    echo "   ⚠ HTTP 포트 (80) 리스닝하지 않음"
fi

if netstat -tuln 2>/dev/null | grep -q ":443 "; then
    echo "   ✓ HTTPS 포트 (443) 리스닝"
else
    echo "   ⚠ HTTPS 포트 (443) 리스닝하지 않음 (SSL 미설정)"
fi

# 7. 웹 접근 테스트
echo "7. 웹 서비스 접근 검증..."
if curl -s -o /dev/null -w "%{http_code}" http://localhost/ | grep -q "200\|301\|302"; then
    echo "   ✓ 웹 서비스 정상 응답"
else
    echo "   ⚠ 웹 서비스 응답 없음 또는 오류"
fi

echo ""
echo "========================================"
echo "검증 완료!"
echo ""
echo "📋 추가 확인 사항:"
echo "  - 브라우저에서 http://SERVER_IP 접속 테스트"
echo "  - 로그: sudo journalctl -u elderly_rag_gunicorn -f"
echo "  - 관리자 페이지: http://SERVER_IP/admin/"
echo ""
echo "🔧 문제 발생 시:"
echo "  - 로그 확인: sudo journalctl -u elderly_rag_gunicorn -n 200"
echo "  - 환경 복구: bash fix_env.sh"
echo "  - 서비스 재시작: sudo systemctl restart elderly_rag_gunicorn nginx"