#!/bin/bash
# PostgreSQL Peer 인증 문제 해결 스크립트

set -e

echo "🔧 PostgreSQL Peer 인증 문제 해결 중..."

# PostgreSQL 설정 파일 경로 확인
PG_VERSION=$(sudo -u postgres psql -t -c "SHOW server_version;" | grep -oE '[0-9]+' | head -1)
PG_CONFIG_DIR="/etc/postgresql/${PG_VERSION}/main"
PG_HBA_CONF="${PG_CONFIG_DIR}/pg_hba.conf"

echo "📋 PostgreSQL 버전: ${PG_VERSION}"
echo "📁 설정 파일 위치: ${PG_HBA_CONF}"

# 기존 pg_hba.conf 백업
echo "💾 pg_hba.conf 백업 중..."
sudo cp "${PG_HBA_CONF}" "${PG_HBA_CONF}.backup.$(date +%Y%m%d_%H%M%S)"

# pg_hba.conf에서 local 연결을 md5 인증으로 변경
echo "🔑 인증 방식을 md5로 변경 중..."
sudo sed -i.bak \
    -e 's/^local\s\+all\s\+postgres\s\+peer$/local   all             postgres                                peer/' \
    -e 's/^local\s\+all\s\+all\s\+peer$/local   all             all                                     md5/' \
    "${PG_HBA_CONF}"

# 변경사항 확인
echo "📄 현재 pg_hba.conf 로컬 연결 설정:"
sudo grep "^local" "${PG_HBA_CONF}"

# PostgreSQL 재시작
echo "🔄 PostgreSQL 서비스 재시작 중..."
sudo systemctl reload postgresql
sleep 2

# 연결 테스트 (비밀번호 인증 사용)
echo "🧪 새로운 인증 방식으로 연결 테스트..."
PGPASSWORD='changeme' psql -h localhost -U rag_user -d elderly_rag -c "SELECT 'Connection successful with password auth' as status;"

echo "✅ PostgreSQL 인증 설정 완료!"

echo ""
echo "🚀 이제 Django 마이그레이션을 다시 시도하세요:"
echo "   cd /home/ubuntu/4th_project/elderly_rag_chatbot"
echo "   source venv/bin/activate"
echo "   python manage.py migrate"

echo ""
echo "📋 참고사항:"
echo "- 로컬 연결이 이제 비밀번호 인증(md5)을 사용합니다"
echo "- postgres 사용자는 여전히 peer 인증을 사용합니다"
echo "- 백업 파일: ${PG_HBA_CONF}.backup.*"