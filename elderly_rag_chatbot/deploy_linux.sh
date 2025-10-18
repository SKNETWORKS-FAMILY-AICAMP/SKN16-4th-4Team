#!/bin/bash
set -e

# 간단 배포 스크립트 (Ubuntu 계열 가정)
# 역할: 가상환경 생성, 패키지 설치, 마이그레이션, collectstatic, systemd 서비스 파일 생성

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
DJANGO_SETTINGS_MODULE="config.django_settings"
GUNICORN_SERVICE_NAME="elderly_rag_gunicorn"

echo "Project dir: $PROJECT_DIR"

# 가상환경
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

pip install --upgrade pip
pip install -r "$PROJECT_DIR/requirements.txt"

# 환경변수 확인
if [ ! -f "$PROJECT_DIR/.env" ]; then
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
        echo ".env 파일이 생성되었습니다. 필요시 값들을 수정하세요."
    fi
fi

export DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

# Django 관리 작업
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput
python manage.py collectstatic --noinput

# systemd 서비스 파일 생성 (사용자 권한 필요)
SERVICE_FILE="/etc/systemd/system/$GUNICORN_SERVICE_NAME.service"

if [ ! -f "$SERVICE_FILE" ]; then
    sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Gunicorn instance to serve elderly_rag_chatbot
After=network.target

[Service]
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$PROJECT_DIR
Environment=DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$PROJECT_DIR/gunicorn.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
EOF
    sudo systemctl daemon-reload
    sudo systemctl enable $GUNICORN_SERVICE_NAME
    echo "Created systemd service: $GUNICORN_SERVICE_NAME"
fi

# Nginx 설정 안내
NGINX_CONF="$PROJECT_DIR/deploy_nginx_template.conf"
if [ ! -f "$NGINX_CONF" ]; then
    cat > "$NGINX_CONF" <<'NGINX'
server {
    listen 80;
    server_name _;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root PROJECT_DIR_PLACEHOLDER;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:PROJECT_DIR_PLACEHOLDER/gunicorn.sock;
    }
}
NGINX
    sed -i "s|PROJECT_DIR_PLACEHOLDER|$PROJECT_DIR|g" "$NGINX_CONF"
    echo "Nginx 템플릿이 생성되었습니다: $NGINX_CONF"
fi

# 시작
sudo systemctl start $GUNICORN_SERVICE_NAME || true
sudo systemctl status $GUNICORN_SERVICE_NAME --no-pager || true

echo "배포 스크립트 완료. Nginx 설정 후 재시작하세요."
