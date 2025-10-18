#!/bin/bash
# 🔧 502 오류 해결 및 Gunicorn 서비스 수정 스크립트

set -e

echo "🔧 502 오류 진단 및 해결"
echo "======================="

cd /home/ubuntu/4th_project/elderly_rag_chatbot

echo "📋 1단계: 현재 오류 진단"
echo "========================"

# Gunicorn 서비스 로그 확인
echo "🔍 Gunicorn 서비스 로그:"
sudo journalctl -u elderly_rag_gunicorn -n 20 --no-pager

echo ""
echo "📋 2단계: 수동 Gunicorn 테스트"
echo "=============================="

# 가상환경 활성화 및 수동 테스트
source venv/bin/activate

echo "🧪 Django 애플리케이션 테스트:"
python manage.py check

echo ""
echo "🧪 Gunicorn 수동 실행 테스트:"
timeout 5 gunicorn config.wsgi:application --bind 0.0.0.0:8000 &
GUNICORN_PID=$!
sleep 2

# 수동 실행 테스트
if kill -0 $GUNICORN_PID 2>/dev/null; then
    echo "✅ Gunicorn 수동 실행 성공"
    kill $GUNICORN_PID 2>/dev/null || true
else
    echo "❌ Gunicorn 수동 실행 실패"
fi

echo ""
echo "📋 3단계: systemd 서비스 파일 수정"
echo "================================="

# 올바른 systemd 서비스 파일 생성
sudo tee /etc/systemd/system/elderly_rag_gunicorn.service > /dev/null << EOF
[Unit]
Description=Gunicorn instance to serve Elderly RAG Chatbot
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/4th_project/elderly_rag_chatbot
Environment="PATH=/home/ubuntu/4th_project/elderly_rag_chatbot/venv/bin"
ExecStart=/home/ubuntu/4th_project/elderly_rag_chatbot/venv/bin/gunicorn --workers 3 --bind 0.0.0.0:8000 config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd 서비스 파일 업데이트 완료"

echo ""
echo "📋 4단계: 서비스 재시작"
echo "======================"

sudo systemctl daemon-reload
sudo systemctl stop elderly_rag_gunicorn 2>/dev/null || true
sudo systemctl start elderly_rag_gunicorn
sudo systemctl enable elderly_rag_gunicorn

echo "✅ 서비스 재시작 완료"

echo ""
echo "📋 5단계: 상태 확인"
echo "=================="

sleep 3
echo "🔍 Gunicorn 서비스 상태:"
sudo systemctl status elderly_rag_gunicorn --no-pager

echo ""
echo "🔍 포트 8000 확인:"
sudo netstat -tlnp | grep :8000 || echo "포트 8000이 열려있지 않음"

echo ""
echo "🧪 HTTP 연결 테스트:"
curl -s -o /dev/null -w "HTTP 응답: %{http_code}\n" "http://localhost:8000/" || echo "연결 실패"

echo ""
echo "📋 6단계: Nginx 재시작"
echo "====================="
sudo systemctl restart nginx

echo ""
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "localhost")
echo "🌐 웹 접속 테스트:"
curl -s -o /dev/null -w "외부 접속 응답: %{http_code}\n" "http://$SERVER_IP/" || echo "외부 접속 실패"

echo ""
if systemctl is-active --quiet elderly_rag_gunicorn; then
    echo "✅ 502 오류 해결 완료!"
    echo "🌐 웹사이트: http://$SERVER_IP"
    echo "🔧 관리자: http://$SERVER_IP/admin"
else
    echo "❌ 아직 문제가 있습니다. 추가 진단이 필요합니다."
    echo "🔍 로그 확인: sudo journalctl -u elderly_rag_gunicorn -f"
fi