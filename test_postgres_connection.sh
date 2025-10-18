#!/bin/bash
# 간단한 PostgreSQL 연결 테스트 및 해결 스크립트

set -e

echo "🔍 PostgreSQL 연결 문제 진단 및 해결..."

# 1. 현재 인증 설정 확인
echo "📋 현재 PostgreSQL 인증 설정:"
sudo grep "^local" /etc/postgresql/*/main/pg_hba.conf 2>/dev/null || echo "pg_hba.conf를 찾을 수 없습니다."

# 2. 호스트 기반 연결 테스트 (peer 인증 우회)
echo "🧪 호스트 기반 연결 테스트 (127.0.0.1)..."
PGPASSWORD='changeme' psql -h 127.0.0.1 -U rag_user -d elderly_rag -c "SELECT 'TCP connection successful' as status;" || {
    echo "❌ 호스트 연결 실패. pg_hba.conf를 확인해야 합니다."
}

# 3. Django 설정에서 명시적으로 호스트 사용 확인
echo "🔧 Django에서 호스트 기반 연결 사용 확인..."
cd /home/ubuntu/4th_project/elderly_rag_chatbot
source venv/bin/activate

# .env 파일 확인
if [ -f .env ]; then
    echo "📄 현재 .env 파일의 데이터베이스 설정:"
    grep -E "^(DATABASE_URL|POSTGRES_)" .env || echo "데이터베이스 설정을 찾을 수 없습니다."
else
    echo "❌ .env 파일이 없습니다. .env.example을 복사하여 .env를 생성하세요."
    echo "cp .env.example .env"
    exit 1
fi

# 4. Django 데이터베이스 연결 테스트
echo "🧪 Django 데이터베이스 연결 테스트..."
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django_settings')
django.setup()
from django.db import connection
try:
    cursor = connection.cursor()
    cursor.execute('SELECT version();')
    print('✅ Django PostgreSQL 연결 성공:', cursor.fetchone()[0][:50] + '...')
except Exception as e:
    print('❌ Django 연결 실패:', str(e))
    print('💡 DATABASE_URL이 올바른지 확인하세요: postgres://user:pass@127.0.0.1:5432/dbname')
"

echo ""
echo "🚀 연결이 성공했다면 마이그레이션을 시도하세요:"
echo "   python manage.py migrate"

echo ""
echo "❌ 연결이 실패했다면 다음을 확인하세요:"
echo "1. .env 파일에 올바른 DATABASE_URL 설정"
echo "2. PostgreSQL이 TCP 연결을 허용하는지 확인"
echo "3. pg_hba.conf에서 호스트 연결 설정 확인"