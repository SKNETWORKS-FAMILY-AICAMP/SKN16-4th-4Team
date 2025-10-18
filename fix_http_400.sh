#!/bin/bash
# 🔧 HTTP 400 오류 및 외부 연결 문제 해결 스크립트

set -e

echo "🔧 HTTP 400 오류 및 외부 연결 문제 해결"
echo "====================================="

cd /home/ubuntu/4th_project/elderly_rag_chatbot

echo "📋 1단계: 서버 IP 주소 확인"
echo "=========================="

# IPv4 주소 가져오기 (여러 방법 시도)
SERVER_IPv4=$(curl -4 -s ifconfig.me 2>/dev/null || curl -4 -s icanhazip.com 2>/dev/null || echo "")
if [ -z "$SERVER_IPv4" ]; then
    SERVER_IPv4=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "43.202.39.220")
fi

echo "🔍 감지된 서버 IPv4 주소: $SERVER_IPv4"

# 내부 IP도 확인
INTERNAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "127.0.0.1")
echo "🔍 내부 IP 주소: $INTERNAL_IP"

echo ""
echo "📋 2단계: .env 파일 수정"
echo "======================="

# .env 파일 백업
cp .env .env.backup.$(date +%Y%m%d_%H%M%S) 2>/dev/null || echo "기존 .env 없음"

# .env 파일이 없으면 생성
if [ ! -f ".env" ]; then
    echo "📄 .env 파일 생성 중..."
    cp .env.example .env
fi

# ALLOWED_HOSTS 설정 (기존 내용 보존하면서 수정)
echo "🔧 ALLOWED_HOSTS 설정 중..."

# 기존 .env에서 ALLOWED_HOSTS 라인 수정
if grep -q "^ALLOWED_HOSTS=" .env; then
    sed -i "s/^ALLOWED_HOSTS=.*/ALLOWED_HOSTS=localhost,127.0.0.1,${SERVER_IPv4},${INTERNAL_IP}/" .env
else
    echo "ALLOWED_HOSTS=localhost,127.0.0.1,${SERVER_IPv4},${INTERNAL_IP}" >> .env
fi

# CSRF_TRUSTED_ORIGINS 설정
if grep -q "^CSRF_TRUSTED_ORIGINS=" .env; then
    sed -i "s|^CSRF_TRUSTED_ORIGINS=.*|CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,http://${SERVER_IPv4},http://${INTERNAL_IP}|" .env
else
    echo "CSRF_TRUSTED_ORIGINS=http://localhost,http://127.0.0.1,http://${SERVER_IPv4},http://${INTERNAL_IP}" >> .env
fi

# DEBUG=False 설정 (프로덕션)
if grep -q "^DEBUG=" .env; then
    sed -i "s/^DEBUG=.*/DEBUG=False/" .env
else
    echo "DEBUG=False" >> .env
fi

echo "✅ .env 파일 수정 완료"

echo ""
echo "📋 3단계: Django 설정 확인"
echo "========================="

source venv/bin/activate

echo "🔍 현재 Django 설정:"
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django_settings')
django.setup()
from django.conf import settings
print('ALLOWED_HOSTS:', settings.ALLOWED_HOSTS)
print('CSRF_TRUSTED_ORIGINS:', getattr(settings, 'CSRF_TRUSTED_ORIGINS', []))
print('DEBUG:', settings.DEBUG)
"

echo ""
echo "📋 4단계: Nginx 설정 확인 및 수정"
echo "==============================="

# Nginx 설정 파일 확인
NGINX_CONFIG="/etc/nginx/sites-available/elderly_rag"
if [ -f "$NGINX_CONFIG" ]; then
    echo "📄 기존 Nginx 설정 파일 발견"
else
    echo "📄 Nginx 설정 파일 생성 중..."
fi

# 올바른 Nginx 설정 생성
sudo tee "$NGINX_CONFIG" > /dev/null << EOF
server {
    listen 80;
    server_name $SERVER_IPv4 $INTERNAL_IP localhost;

    # 정적 파일
    location /static/ {
        alias /var/www/elderly_rag/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }

    # 미디어 파일
    location /media/ {
        alias /home/ubuntu/4th_project/elderly_rag_chatbot/media/;
    }

    # Django 애플리케이션
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$http_host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
EOF

echo "✅ Nginx 설정 파일 생성 완료"

# Nginx 설정 활성화
sudo ln -sf "$NGINX_CONFIG" /etc/nginx/sites-enabled/elderly_rag

# 기본 Nginx 사이트 비활성화
sudo rm -f /etc/nginx/sites-enabled/default

echo ""
echo "📋 5단계: 서비스 재시작"
echo "======================"

# Gunicorn 재시작
sudo systemctl restart elderly_rag_gunicorn

# Nginx 설정 테스트 및 재시작
sudo nginx -t
sudo systemctl restart nginx

echo "✅ 모든 서비스 재시작 완료"

echo ""
echo "📋 6단계: 최종 연결 테스트"
echo "========================"

sleep 5

echo "🔍 서비스 상태 확인:"
systemctl is-active elderly_rag_gunicorn && echo "✅ Gunicorn: 실행중" || echo "❌ Gunicorn: 중단됨"
systemctl is-active nginx && echo "✅ Nginx: 실행중" || echo "❌ Nginx: 중단됨"

echo ""
echo "🧪 HTTP 연결 테스트:"

# 로컬 테스트
echo "🔍 로컬 테스트 (127.0.0.1):"
curl -s -o /dev/null -w "응답코드: %{http_code}, 응답시간: %{time_total}초\n" "http://127.0.0.1/" || echo "연결 실패"

# 내부 IP 테스트  
echo "🔍 내부 IP 테스트 ($INTERNAL_IP):"
curl -s -o /dev/null -w "응답코드: %{http_code}, 응답시간: %{time_total}초\n" "http://$INTERNAL_IP/" || echo "연결 실패"

# 외부 IP 테스트
echo "🔍 외부 IP 테스트 ($SERVER_IPv4):"
curl -s -o /dev/null -w "응답코드: %{http_code}, 응답시간: %{time_total}초\n" "http://$SERVER_IPv4/" || echo "연결 실패"

echo ""
echo "📋 7단계: 포트 확인"
echo "=================="

# ss 명령어로 포트 확인 (netstat 대체)
echo "🔍 열려있는 포트:"
sudo ss -tlnp | grep -E ':80|:8000' || echo "포트 정보를 가져올 수 없습니다"

echo ""
if systemctl is-active --quiet elderly_rag_gunicorn && systemctl is-active --quiet nginx; then
    echo "🎉 모든 문제 해결 완료!"
    echo "======================="
    echo "🌐 웹사이트: http://$SERVER_IPv4"
    echo "🔧 관리자: http://$SERVER_IPv4/admin"
    echo "💬 챗봇: http://$SERVER_IPv4/chatbot"
    echo ""
    echo "👤 기본 관리자 계정:"
    echo "   사용자명: admin"
    echo "   비밀번호: admin"
    echo ""
    echo "🔍 추가 확인이 필요하면:"
    echo "   - 로그: sudo journalctl -u elderly_rag_gunicorn -f"
    echo "   - Nginx 로그: sudo tail -f /var/log/nginx/error.log"
else
    echo "❌ 아직 문제가 있습니다."
    echo "🔍 로그를 확인하세요:"
    echo "   sudo journalctl -u elderly_rag_gunicorn -n 20"
    echo "   sudo journalctl -u nginx -n 20"
fi