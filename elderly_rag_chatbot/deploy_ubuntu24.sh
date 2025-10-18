#!/usr/bin/env bash
set -euo pipefail

# Ubuntu 24 배포 스크립트 (AWS Lightsail 권장)
# 목적: 시스템 패키지 설치, PostgreSQL 설정(선택), 가상환경 및 의존성 설치, systemd/gunicorn/nginx 설정
# Non-interactive usage supported via environment variables:
#   AUTO_CONFIRM=true            # skip prompts
#   POSTGRES_INSTALL=true        # install and create DB
#   POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD
#   DOMAIN=example.com           # for nginx server_name and certbot

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"
GUNICORN_SERVICE_NAME="elderly_rag_gunicorn"
GUNICORN_SOCKET="$PROJECT_DIR/gunicorn.sock"

echo "==== Ubuntu 24 배포 시작 (Project: $PROJECT_DIR) ===="

sudo apt update && sudo apt upgrade -y

echo "== 필수 시스템 패키지 설치 =="
sudo apt install -y build-essential python3-venv python3-dev python3-pip git curl \
    libpq-dev libssl-dev cmake pkg-config nginx certbot python3-certbot-nginx \
    libopenblas-dev liblapack-dev

echo "== PostgreSQL 설치 여부 확인 (환경변수 POSTGRES_INSTALL) =="
POSTGRES_INSTALL=${POSTGRES_INSTALL:-false}
AUTO_CONFIRM=${AUTO_CONFIRM:-false}
if [[ "$POSTGRES_INSTALL" == "true" ]]; then
    echo "-> 자동으로 PostgreSQL을 설치하고 DB/사용자를 생성합니다"
    sudo apt install -y postgresql postgresql-contrib
    sudo systemctl enable --now postgresql
    pg_db=${POSTGRES_DB:-elderly_rag}
    pg_user=${POSTGRES_USER:-rag_user}
    pg_pass=${POSTGRES_PASSWORD:-}
    if [ -z "$pg_pass" ]; then
        if [ "$AUTO_CONFIRM" = "true" ]; then
            echo "POSTGRES_PASSWORD가 설정되어 있지 않습니다. 중단합니다. 환경변수로 POSTGRES_PASSWORD를 설정하세요."
            exit 1
        else
            read -s -p "DB 비밀번호 입력: " pg_pass
            echo
        fi
    fi
    sudo -u postgres psql -c "CREATE DATABASE ${pg_db};"
    sudo -u postgres psql -c "CREATE USER ${pg_user} WITH PASSWORD '${pg_pass}';"
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${pg_db} TO ${pg_user};"
    echo "Postgres DB 및 사용자 생성 완료"
    export DATABASE_URL="postgres://${pg_user}:${pg_pass}@localhost:5432/${pg_db}"
fi

echo "== 가상환경 생성 및 의존성 설치 =="
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"
pip install --upgrade pip setuptools wheel

echo "== Pre-installing numpy (prefer binary) to avoid build issues =="
# try to detect pinned numpy in requirements.txt
PINNED_NUMPY=$(grep -E "^numpy==" requirements.txt || true)
if [ -n "$PINNED_NUMPY" ]; then
    echo "Found pinned numpy: $PINNED_NUMPY"
    pip install --prefer-binary ${PINNED_NUMPY#*==}
else
    pip install --prefer-binary numpy
fi

echo "== Installing Python requirements =="
pip install -r "$PROJECT_DIR/requirements.txt" || {
    echo "pip install failed — attempting to install build deps and retry"
    sudo apt install -y build-essential libopenblas-dev liblapack-dev gfortran
    pip install -r "$PROJECT_DIR/requirements.txt"
}

## .env 로드/초기화 함수
load_or_init_env() {
    # 우선 .env 파일이 있으면 source
    if [ -f "$PROJECT_DIR/.env" ]; then
        echo "Loading .env from $PROJECT_DIR/.env"
        # export all variables defined in .env (ignore comments)
        set -a; source "$PROJECT_DIR/.env"; set +a
        return
    fi

    # .env 가 없으면 .env.example을 복사하고 최소값 채움
    if [ -f "$PROJECT_DIR/.env.example" ]; then
        echo ".env not found — creating from .env.example"
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"

        # if DATABASE_URL provided via env, ensure it's set in .env
        if [ ! -z "${DATABASE_URL:-}" ]; then
            if grep -q "^DATABASE_URL=" "$PROJECT_DIR/.env"; then
                sed -i "s|^DATABASE_URL=.*|DATABASE_URL=${DATABASE_URL}|" "$PROJECT_DIR/.env"
            else
                echo "DATABASE_URL=${DATABASE_URL}" >> "$PROJECT_DIR/.env"
            fi
        fi

        # generate SECRET_KEY if missing
        if ! grep -q "^SECRET_KEY=" "$PROJECT_DIR/.env"; then
            SECRET_KEY_VAL=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(50))
PY
)
            echo "SECRET_KEY=${SECRET_KEY_VAL}" >> "$PROJECT_DIR/.env"
        fi

        set -a; source "$PROJECT_DIR/.env"; set +a
    else
        echo "Warning: .env and .env.example both missing. Proceeding with environment variables only."
    fi
}

# load or init .env so subsequent commands can use variables
load_or_init_env

echo "== Django 마이그레이션 및 collectstatic =="
export DJANGO_SETTINGS_MODULE=config.django_settings
# ensure environment variables from .env are exported
set -a; true; set +a
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "== systemd 서비스 파일 생성 (gunicorn) =="
SERVICE_FILE="/etc/systemd/system/$GUNICORN_SERVICE_NAME.service"
sudo tee "$SERVICE_FILE" > /dev/null <<EOF
[Unit]
Description=Gunicorn instance to serve elderly_rag_chatbot
After=network.target

[Service]
User=$(whoami)
Group=$(id -gn)
WorkingDirectory=$PROJECT_DIR
Environment=DJANGO_SETTINGS_MODULE=config.django_settings
Environment=PATH=$VENV_DIR/bin
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:$GUNICORN_SOCKET config.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now $GUNICORN_SERVICE_NAME

echo "== Nginx 설정 템플릿 생성 =="
NGINX_SITE="/etc/nginx/sites-available/elderly_rag"
SERVER_NAME=${DOMAIN:-_}
sudo tee "$NGINX_SITE" > /dev/null <<NGINX
server {
    listen 80;
    server_name ${SERVER_NAME};

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        alias ${PROJECT_DIR}/static/;
    }

    location /media/ {
        alias ${PROJECT_DIR}/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:${PROJECT_DIR}/gunicorn.sock;
    }
}
NGINX
sudo ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/elderly_rag

sudo nginx -t && sudo systemctl restart nginx

echo "== 방화벽(UFW) 설정 안내 =="
if command -v ufw >/dev/null 2>&1; then
    echo "UFW가 감지되었습니다. 80,443 포트를 허용합니다."
    sudo ufw allow 'Nginx Full'
    sudo ufw allow OpenSSH
    sudo ufw enable || true
fi

echo "== HTTPS (Let's Encrypt) 설정 안내 =="
echo "도메인이 있다면 certbot을 사용해 HTTPS를 설정하세요: sudo certbot --nginx -d your_domain"

echo "배포 완료. 서비스 상태 확인: sudo systemctl status $GUNICORN_SERVICE_NAME"
echo "Nginx 설정 파일: $NGINX_SITE"
echo "Lightsail 콘솔의 네트워킹에서 HTTP(80) 및 HTTPS(443) 포트 허용을 잊지 마세요."

deactivate || true

exit 0
