#!/bin/bash
# PostgreSQL pg_hba.conf 설정 개선 스크립트

set -e

echo "🔧 PostgreSQL pg_hba.conf 설정 개선 중..."

# PostgreSQL 버전과 설정 파일 경로 찾기
PG_VERSION=$(sudo -u postgres psql -t -c "SELECT version();" | grep -oE 'PostgreSQL [0-9]+' | grep -oE '[0-9]+')
PG_CONFIG_PATH=$(sudo -u postgres psql -t -c "SHOW config_file;" | tr -d ' ')
PG_DATA_DIR=$(dirname "$PG_CONFIG_PATH")
PG_HBA_CONF="${PG_DATA_DIR}/pg_hba.conf"

echo "📋 PostgreSQL 버전: $PG_VERSION"
echo "📁 설정 파일: $PG_HBA_CONF"

# 백업 생성
echo "💾 현재 설정 백업 중..."
sudo cp "$PG_HBA_CONF" "${PG_HBA_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# 현재 설정 확인
echo "📄 현재 pg_hba.conf 설정:"
sudo head -20 "$PG_HBA_CONF"

# 호스트 연결 설정 추가/수정
echo "🔑 호스트 기반 연결 설정 추가 중..."

# 기존 설정 주석 처리하고 새 설정 추가
sudo tee "$PG_HBA_CONF" > /dev/null << 'EOF'
# PostgreSQL Client Authentication Configuration File
# ===================================================
#
# TYPE  DATABASE        USER            ADDRESS                 METHOD

# "local" is for Unix domain socket connections only
local   all             postgres                                peer
local   all             all                                     md5

# IPv4 local connections:
host    all             all             127.0.0.1/32            md5
host    all             all             ::1/128                 md5

# Allow replication connections from localhost, by a user with the
# replication privilege.
local   replication     all                                     peer
host    replication     all             127.0.0.1/32            md5
host    replication     all             ::1/128                 md5
EOF

echo "✅ pg_hba.conf 설정 완료!"

# 설정 적용
echo "🔄 PostgreSQL 설정 다시 로드 중..."
sudo systemctl reload postgresql

# 잠시 대기
sleep 3

# 연결 테스트
echo "🧪 연결 테스트 중..."
PGPASSWORD='changeme' psql -h 127.0.0.1 -U rag_user -d elderly_rag -c "SELECT 'Host-based connection successful!' as status;"

echo ""
echo "✅ PostgreSQL 설정이 완료되었습니다!"
echo ""
echo "🚀 이제 Django 마이그레이션을 실행하세요:"
echo "   cd /home/ubuntu/4th_project/elderly_rag_chatbot"
echo "   source venv/bin/activate"
echo "   python manage.py migrate"

echo ""
echo "📋 변경사항:"
echo "- local 연결: postgres는 peer, 일반 사용자는 md5"  
echo "- host 연결: 모든 사용자 md5 (비밀번호) 인증"
echo "- 백업 파일: ${PG_HBA_CONF}.backup.*"