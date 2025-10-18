#!/bin/bash
# 🏗️ 올바른 Django 프로젝트 구조로 재구성

set -e

echo "🏗️ Django 프로젝트 구조 재구성"
echo "=============================="
echo ""

echo "📋 현재 구조 분석:"
echo "=================="
echo "❌ 문제점:"
echo "   - 루트에 Django 파일들과 elderly_rag_chatbot/ 중복"
echo "   - 두 개의 manage.py, requirements.txt 존재"
echo "   - 배포 스크립트 경로 혼란"
echo ""

echo "✅ 목표 구조:"
echo "============="
cat << 'EOF'
elderly_rag_project/
├── manage.py                 # Django 관리 스크립트
├── requirements.txt          # Python 패키지 의존성
├── .env                      # 환경변수 설정
├── config/                   # Django 프로젝트 설정
│   ├── __init__.py
│   ├── django_settings.py   # 메인 설정 파일
│   ├── urls.py              # URL 라우팅
│   └── wsgi.py              # WSGI 설정
├── apps/                     # Django 앱들
│   ├── chatbot_web/         # 웹 챗봇 앱
│   ├── documents/           # 문서 관리 앱
│   └── __init__.py
├── templates/               # HTML 템플릿
├── static/                  # 정적 파일 (CSS, JS, 이미지)
├── media/                   # 업로드된 파일
├── data/                    # RAG 데이터
├── src/                     # RAG 시스템 코드
├── logs/                    # 로그 파일
├── scripts/                 # 관리 스크립트들
│   ├── deploy.sh
│   ├── restart_server.sh
│   └── monitor.sh
└── docs/                    # 문서
EOF

echo ""
echo "🔄 구조 재구성을 진행하시겠습니까?"
echo "   이 작업은 현재 서버를 중단하고 파일들을 재구성합니다."
echo ""
read -p "계속하시겠습니까? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "작업을 취소합니다."
    exit 0
fi

cd /home/ubuntu/4th_project

echo ""
echo "📦 1단계: 백업 생성"
echo "=================="
BACKUP_DIR="/home/ubuntu/project_backup_$(date +%Y%m%d_%H%M%S)"
echo "백업 디렉토리: $BACKUP_DIR"
cp -r SKN16-4th-4Team "$BACKUP_DIR"
echo "✅ 전체 백업 완료"

echo ""
echo "🏗️ 2단계: 새로운 프로젝트 구조 생성"
echo "===================================="

# 임시 디렉토리에서 새로운 구조 생성
TEMP_DIR="/tmp/elderly_rag_restructure"
rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"

cd "$TEMP_DIR"

# 새로운 프로젝트 디렉토리 구조 생성
mkdir -p {config,apps,templates,static,media,data,src,logs,scripts,docs}

echo "✅ 기본 디렉토리 구조 생성 완료"

echo ""
echo "📁 3단계: 파일 이동 및 통합"
echo "=========================="

# 핵심 Django 파일들 이동 (elderly_rag_chatbot에서 가져오기)
cp /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/manage.py ./
cp /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/requirements.txt ./
cp -r /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/config/* config/

# Django 앱들 이동
cp -r /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/chatbot_web apps/
cp -r /home/ubuntu/4th_project/SKN16-4th-4Team/documents apps/

# 템플릿과 정적 파일 이동
cp -r /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/templates/* templates/ 2>/dev/null || true
cp -r /home/ubuntu/4th_project/SKN16-4th-4Team/templates/* templates/ 2>/dev/null || true
cp -r /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/static/* static/ 2>/dev/null || true

# RAG 시스템 파일들 이동
cp -r /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/src/* src/ 2>/dev/null || true
cp -r /home/ubuntu/4th_project/SKN16-4th-4Team/data/* data/ 2>/dev/null || true

# 중요한 설정 파일들
cp /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/.env.example ./
cp /home/ubuntu/4th_project/SKN16-4th-4Team/elderly_rag_chatbot/.env ./ 2>/dev/null || true

# 관리 스크립트들을 scripts 디렉토리로 정리
cp /home/ubuntu/4th_project/SKN16-4th-4Team/restart_server.sh scripts/
cp /home/ubuntu/4th_project/SKN16-4th-4Team/monitor_logs.sh scripts/
cp /home/ubuntu/4th_project/SKN16-4th-4Team/master.sh scripts/

echo "✅ 파일 이동 완료"

echo ""
echo "⚙️ 4단계: 설정 파일 수정"
echo "======================="

# Django 설정에서 앱 경로 수정
sed -i "s/'chatbot_web'/'apps.chatbot_web'/g" config/django_settings.py
sed -i "s/'documents'/'apps.documents'/g" config/django_settings.py

# apps/__init__.py 생성
touch apps/__init__.py

echo "✅ 설정 파일 수정 완료"

echo ""
echo "🔄 5단계: 기존 서비스 중단"
echo "======================="
sudo systemctl stop elderly_rag_gunicorn 2>/dev/null || true
sudo systemctl stop nginx 2>/dev/null || true

echo ""
echo "📂 6단계: 프로젝트 교체"
echo "======================="

cd /home/ubuntu/4th_project
mv SKN16-4th-4Team SKN16-4th-4Team.old
mv "$TEMP_DIR" elderly_rag_project

echo "✅ 새로운 프로젝트 구조로 교체 완료"

echo ""
echo "🔧 7단계: systemd 서비스 경로 수정"
echo "==============================="

# 새로운 프로젝트 경로로 systemd 서비스 파일 수정
sudo tee /etc/systemd/system/elderly_rag_gunicorn.service > /dev/null << EOF
[Unit]
Description=Gunicorn instance to serve Elderly RAG Chatbot
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/4th_project/elderly_rag_project
Environment="PATH=/home/ubuntu/4th_project/elderly_rag_project/venv/bin"
ExecStart=/home/ubuntu/4th_project/elderly_rag_project/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 --timeout 120 config.wsgi:application
ExecReload=/bin/kill -s HUP \$MAINPID
KillMode=mixed
Restart=on-failure
RestartSec=5
TimeoutStopSec=5

[Install]
WantedBy=multi-user.target
EOF

echo "✅ systemd 서비스 경로 수정 완료"

echo ""
echo "🔧 8단계: Nginx 설정 수정"
echo "======================="

sudo tee /etc/nginx/sites-available/elderly_rag > /dev/null << 'EOF'
server {
    listen 80;
    server_name 43.202.39.220 172.26.10.127 localhost _;
    
    client_max_body_size 100M;
    
    location /static/ {
        alias /home/ubuntu/4th_project/elderly_rag_project/static/;
        expires 30d;
        add_header Cache-Control "public, no-transform";
    }
    
    location /media/ {
        alias /home/ubuntu/4th_project/elderly_rag_project/media/;
        expires 7d;
    }
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        proxy_buffering off;
    }
}
EOF

echo "✅ Nginx 설정 수정 완료"

echo ""
echo "🐍 9단계: 가상환경 재생성"
echo "======================="

cd /home/ubuntu/4th_project/elderly_rag_project

# 기존 가상환경이 있다면 복사, 없다면 새로 생성
if [ -d "/home/ubuntu/4th_project/SKN16-4th-4Team.old/elderly_rag_chatbot/venv" ]; then
    echo "기존 가상환경 복사 중..."
    cp -r /home/ubuntu/4th_project/SKN16-4th-4Team.old/elderly_rag_chatbot/venv ./
else
    echo "새로운 가상환경 생성 중..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip setuptools wheel
    pip install -r requirements.txt
fi

echo "✅ 가상환경 설정 완료"

echo ""
echo "🔄 10단계: 서비스 재시작"
echo "======================="

sudo systemctl daemon-reload
sudo systemctl start elderly_rag_gunicorn
sudo systemctl start nginx
sudo nginx -t

echo "✅ 서비스 재시작 완료"

echo ""
echo "🧪 11단계: 최종 테스트"
echo "===================="

sleep 5

echo "🔍 서비스 상태:"
systemctl is-active elderly_rag_gunicorn && echo "✅ Gunicorn: 실행중" || echo "❌ Gunicorn: 문제있음"
systemctl is-active nginx && echo "✅ Nginx: 실행중" || echo "❌ Nginx: 문제있음"

echo ""
echo "🧪 웹사이트 테스트:"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://43.202.39.220/" 2>/dev/null || echo "000")
echo "HTTP 응답: $HTTP_CODE"

echo ""
echo "🎉 프로젝트 구조 재구성 완료!"
echo "============================"
echo ""
echo "📁 새로운 프로젝트 위치:"
echo "   /home/ubuntu/4th_project/elderly_rag_project/"
echo ""
echo "💾 백업 위치:"
echo "   $BACKUP_DIR"
echo ""
echo "🌐 웹사이트 접속:"
echo "   http://43.202.39.220/"
echo ""
echo "🔧 관리 명령어 (새 위치에서):"
echo "   cd /home/ubuntu/4th_project/elderly_rag_project"
echo "   ./scripts/master.sh"
EOF