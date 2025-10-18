#!/usr/bin/env bash
set -euo pipefail

# full_setup.sh
# One-shot setup: optionally remove existing venv, install system packages,
# recreate venv, install Python dependencies, run migrations, collectstatic,
# and configure gunicorn + nginx. Designed for Ubuntu 24 (Lightsail) and
# run from project folder: ~/.../elderly_rag_chatbot
#
# Usage examples:
#   # interactive mode (will prompt for POSTGRES_PASSWORD if needed)
#   sudo bash full_setup.sh
#
#   # non-interactive with Postgres creation
#   sudo AUTO_CONFIRM=true REMOVE_VENV=true POSTGRES_INSTALL=true \
#     POSTGRES_DB=elderly_rag POSTGRES_USER=rag_user POSTGRES_PASSWORD=changeme \
#     DOMAIN=yourdomain.com bash full_setup.sh
#

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

AUTO_CONFIRM=${AUTO_CONFIRM:-false}
REMOVE_VENV=${REMOVE_VENV:-true}
POSTGRES_INSTALL=${POSTGRES_INSTALL:-false}
POSTGRES_DB=${POSTGRES_DB:-elderly_rag}
POSTGRES_USER=${POSTGRES_USER:-rag_user}
POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-}
DOMAIN=${DOMAIN:-_}

echo "== Full setup starting in $PROJECT_DIR =="

echo "== Update & install system packages =="
apt update && apt upgrade -y
apt install -y build-essential python3-venv python3-dev python3-pip git curl wget unzip \
    libpq-dev libssl-dev cmake pkg-config libopenblas-dev liblapack-dev gfortran nginx certbot python3-certbot-nginx

if [[ "$POSTGRES_INSTALL" == "true" ]]; then
    echo "== Installing PostgreSQL and creating DB/user =="
    apt install -y postgresql postgresql-contrib
    systemctl enable --now postgresql
    if [ -z "$POSTGRES_PASSWORD" ]; then
        if [ "$AUTO_CONFIRM" = "true" ]; then
            echo "POSTGRES_PASSWORD not set and AUTO_CONFIRM=true => aborting"
            exit 1
        else
            read -s -p "Enter Postgres password for $POSTGRES_USER: " POSTGRES_PASSWORD
            echo
        fi
    fi
    sudo -u postgres psql -c "CREATE DATABASE ${POSTGRES_DB};" || true
    sudo -u postgres psql -c "CREATE USER ${POSTGRES_USER} WITH PASSWORD '${POSTGRES_PASSWORD}';" || true
    sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};" || true
    export DATABASE_URL="postgres://${POSTGRES_USER}:${POSTGRES_PASSWORD}@localhost:5432/${POSTGRES_DB}"
fi

# .env 로드/초기화
load_or_init_env() {
    if [ -f "$PROJECT_DIR/.env" ]; then
        echo "Loading .env from $PROJECT_DIR/.env"
        set -a; source "$PROJECT_DIR/.env"; set +a
        return
    fi

    if [ -f "$PROJECT_DIR/.env.example" ]; then
        echo ".env not found — creating from .env.example"
        cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"

        if [ ! -z "${DATABASE_URL:-}" ]; then
            if grep -q "^DATABASE_URL=" "$PROJECT_DIR/.env"; then
                sed -i "s|^DATABASE_URL=.*|DATABASE_URL=${DATABASE_URL}|" "$PROJECT_DIR/.env"
            else
                echo "DATABASE_URL=${DATABASE_URL}" >> "$PROJECT_DIR/.env"
            fi
        fi

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

# call loader so later steps use env values
load_or_init_env

if [[ "$REMOVE_VENV" == "true" && -d "$VENV_DIR" ]]; then
    echo "== Removing existing venv: $VENV_DIR =="
    rm -rf "$VENV_DIR"
fi

echo "== Creating venv and upgrading pip/setuptools/wheel =="
python3 -m venv "$VENV_DIR"
source "$VENV_DIR/bin/activate"
python -m pip install --upgrade pip setuptools wheel build

echo "== Pre-installing numpy (prefer binary) to avoid build issues =="
# Install system build dependencies first
apt install -y build-essential libopenblas-dev liblapack-dev gfortran python3-dev

# Install numpy binary wheel (avoid source compilation)
pip install --prefer-binary numpy

echo "== Installing Python requirements =="
pip install -r requirements.txt || {
    echo "pip install failed — attempting with additional build dependencies"
    apt install -y libffi-dev libssl-dev
    pip install --prefer-binary --no-cache-dir -r requirements.txt
}

echo "== Django migrations & collectstatic =="
export DJANGO_SETTINGS_MODULE=config.django_settings
python manage.py makemigrations || true
python manage.py migrate --noinput
python manage.py collectstatic --noinput

echo "== Setup systemd service for gunicorn =="
GUNICORN_SERVICE_NAME="elderly_rag_gunicorn"
GUNICORN_SOCKET="$PROJECT_DIR/gunicorn.sock"
SERVICE_FILE="/etc/systemd/system/$GUNICORN_SERVICE_NAME.service"

cat > /tmp/${GUNICORN_SERVICE_NAME}.service <<EOF
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

mv /tmp/${GUNICORN_SERVICE_NAME}.service "$SERVICE_FILE"
systemctl daemon-reload
systemctl enable --now $GUNICORN_SERVICE_NAME

echo "== Configure nginx site =="
NGINX_SITE="/etc/nginx/sites-available/elderly_rag"
cat > /tmp/elderly_rag_nginx <<NGINX
server {
    listen 80;
    server_name ${DOMAIN};

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
mv /tmp/elderly_rag_nginx "$NGINX_SITE"
ln -sf "$NGINX_SITE" /etc/nginx/sites-enabled/elderly_rag
nginx -t
systemctl restart nginx

echo "== Full setup completed. Check services: systemctl status $GUNICORN_SERVICE_NAME && sudo journalctl -u $GUNICORN_SERVICE_NAME -f" 
echo "If you have a domain, run: sudo certbot --nginx -d yourdomain.com"

deactivate || true

exit 0
