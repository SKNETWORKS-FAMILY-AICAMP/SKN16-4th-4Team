#!/usr/bin/env bash
set -euo pipefail

# fix_csrf_origins.sh - CSRF_TRUSTED_ORIGINS 스키마 문제 자동 수정
# Django 4.0+ 호환성: http:// 또는 https:// 스키마 자동 추가

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "🔧 CSRF_TRUSTED_ORIGINS 스키마 문제 수정 중..."

if [ -f "$PROJECT_DIR/.env" ]; then
    # .env 파일 백업
    cp "$PROJECT_DIR/.env" "$PROJECT_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
    
    # CSRF_TRUSTED_ORIGINS 라인 찾아서 수정
    if grep -q "^CSRF_TRUSTED_ORIGINS=" "$PROJECT_DIR/.env"; then
        current_value=$(grep "^CSRF_TRUSTED_ORIGINS=" "$PROJECT_DIR/.env" | cut -d'=' -f2-)
        echo "현재 값: $current_value"
        
        # 스키마가 없으면 추가
        if [[ "$current_value" != *"http"* ]]; then
            # IP 주소인지 도메인인지 확인
            if [[ "$current_value" =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+.*$ ]]; then
                # IP 주소면 http:// 추가
                new_value="http://$current_value"
            else
                # 도메인이면 https:// 추가
                new_value="https://$current_value"
            fi
            
            # .env 파일에서 해당 라인 교체
            sed -i "s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=${new_value}|" "$PROJECT_DIR/.env"
            echo "✓ 수정됨: CSRF_TRUSTED_ORIGINS=${new_value}"
        else
            echo "✓ 이미 올바른 형식입니다"
        fi
    else
        echo "⚠ CSRF_TRUSTED_ORIGINS 설정이 .env에 없습니다"
        echo "수동으로 추가하세요:"
        echo "CSRF_TRUSTED_ORIGINS=http://YOUR_SERVER_IP"
    fi
else
    echo "⚠ .env 파일이 없습니다. .env.example에서 복사하세요:"
    echo "cp .env.example .env"
fi

echo ""
echo "수정 완료! 이제 마이그레이션을 다시 실행하세요:"
echo "python manage.py migrate"