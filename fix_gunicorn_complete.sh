#!/bin/bash
# 🔧 Gunicorn 설치 및 경로 문제 해결 스크립트

set -e

echo "🔧 Gunicorn 설치 및 경로 문제 해결"
echo "=================================="

cd /home/ubuntu/4th_project/elderly_rag_chatbot
source venv/bin/activate

echo "📋 1단계: Gunicorn 설치 확인 및 설치"
echo "==================================="

# Gunicorn 설치 상태 확인
echo "🔍 현재 Gunicorn 설치 상태:"
pip list | grep gunicorn || echo "❌ Gunicorn이 설치되지 않음"

# Gunicorn 설치
echo ""
echo "📦 Gunicorn 설치 중..."
pip install --upgrade gunicorn
echo "✅ Gunicorn 설치 완료"

# 설치 확인
echo ""
echo "🔍 Gunicorn 경로 확인:"
which gunicorn
gunicorn --version

echo ""
echo "📋 2단계: 수동 Gunicorn 테스트"
echo "=============================="

# Django 설정 확인
echo "🧪 Django 설정 확인:"
python manage.py check --deploy

echo ""
echo "🧪 Gunicorn 수동 실행 테스트 (5초):"
timeout 5 gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 1 &
GUNICORN_PID=$!
sleep 3

# 테스트 연결
echo "🔍 로컬 연결 테스트:"
curl -s -o /dev/null -w "응답코드: %{http_code}\n" "http://127.0.0.1:8000/" || echo "연결 실패"

# 프로세스 정리
kill $GUNICORN_PID 2>/dev/null || true
wait $GUNICORN_PID 2>/dev/null || true

echo ""
echo "📋 3단계: 올바른 systemd 서비스 파일 생성"
echo "========================================"

# 가상환경 경로 확인
VENV_PATH="/home/ubuntu/4th_project/elderly_rag_chatbot/venv"
GUNICORN_PATH="$VENV_PATH/bin/gunicorn"
PROJECT_PATH="/home/ubuntu/4th_project/elderly_rag_chatbot"

echo "🔍 경로 확인:"
echo "  가상환경: $VENV_PATH"
echo "  Gunicorn: $GUNICORN_PATH"
echo "  프로젝트: $PROJECT_PATH"

# 경로 존재 확인
if [ ! -f "$GUNICORN_PATH" ]; then
    echo "❌ Gunicorn 실행파일이 없습니다: $GUNICORN_PATH"
    exit 1
fi

echo "✅ 모든 경로 확인 완료"

# 올바른 systemd 서비스 파일 생성
sudo tee /etc/systemd/system/elderly_rag_gunicorn.service > /dev/null << EOF
[Unit]
Description=Gunicorn instance to serve Elderly RAG Chatbot
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=$PROJECT_PATH
Environment="PATH=$VENV_PATH/bin"
ExecStart=$GUNICORN_PATH --workers 3 --bind 127.0.0.1:8000 --timeout 120 config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
Restart=on-failure
RestartSec=5
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd 서비스 파일 생성 완료"

echo ""
echo "📋 4단계: 서비스 재시작 및 활성화"
echo "================================"

sudo systemctl daemon-reload
sudo systemctl stop elderly_rag_gunicorn 2>/dev/null || true
sudo systemctl start elderly_rag_gunicorn
sudo systemctl enable elderly_rag_gunicorn

echo "✅ 서비스 재시작 완료"

echo ""
echo "📋 5단계: 최종 상태 확인"
echo "======================="

sleep 5

echo "🔍 Gunicorn 서비스 상태:"
sudo systemctl status elderly_rag_gunicorn --no-pager

echo ""
echo "🔍 서비스 실행 확인:"
if systemctl is-active --quiet elderly_rag_gunicorn; then
    echo "✅ Gunicorn 서비스가 정상 실행 중입니다!"
else
    echo "❌ 아직 문제가 있습니다."
    echo ""
    echo "🔍 최근 로그:"
    sudo journalctl -u elderly_rag_gunicorn -n 10 --no-pager
fi

echo ""
echo "🔍 포트 8000 확인:"
sudo netstat -tlnp | grep :8000 || echo "포트 8000이 열려있지 않음"

echo ""
echo "🧪 로컬 HTTP 테스트:"
curl -s -o /dev/null -w "로컬 응답: %{http_code}\n" "http://127.0.0.1:8000/" || echo "로컬 연결 실패"

echo ""
echo "📋 6단계: Nginx 재시작"
echo "====================="
sudo systemctl restart nginx

echo ""
echo "🧪 외부 HTTP 테스트:"
SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "43.202.39.220")
curl -s -o /dev/null -w "외부 응답: %{http_code}\n" "http://$SERVER_IP/" || echo "외부 연결 실패"

echo ""
if systemctl is-active --quiet elderly_rag_gunicorn && systemctl is-active --quiet nginx; then
    echo "🎉 502 오류 해결 완료!"
    echo "=========================="
    echo "🌐 웹사이트: http://$SERVER_IP"
    echo "🔧 관리자: http://$SERVER_IP/admin (admin/admin)"
    echo "💬 챗봇: http://$SERVER_IP/chatbot"
else
    echo "❌ 아직 문제가 있습니다."
    echo ""
    echo "🔍 추가 진단을 위한 명령어:"
    echo "sudo journalctl -u elderly_rag_gunicorn -f"
    echo "sudo systemctl status nginx"
fi