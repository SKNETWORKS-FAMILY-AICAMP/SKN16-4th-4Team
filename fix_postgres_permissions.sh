#!/bin/bash
# PostgreSQL 권한 수정 스크립트

set -e

echo "🔧 PostgreSQL 권한 수정 중..."

# PostgreSQL 서비스 상태 확인
echo "📋 PostgreSQL 서비스 상태 확인..."
sudo systemctl status postgresql --no-pager

# 데이터베이스 사용자 권한 수정
echo "🔑 데이터베이스 권한 설정 중..."
sudo -u postgres psql << 'EOF'
-- 기존 사용자와 데이터베이스 확인
\l
\du

-- elderly_rag 데이터베이스에 연결
\c elderly_rag

-- public 스키마 권한 부여
GRANT ALL ON SCHEMA public TO rag_user;
GRANT CREATE ON SCHEMA public TO rag_user;

-- 향후 생성될 테이블에 대한 권한도 미리 부여
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO rag_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO rag_user;

-- 데이터베이스 소유권 변경 (선택사항)
-- ALTER DATABASE elderly_rag OWNER TO rag_user;

-- 권한 확인
\dp
\z

-- 연결 종료
\q
EOF

echo "✅ PostgreSQL 권한 설정 완료!"

# Django 마이그레이션 테스트
echo "🧪 Django 마이그레이션 테스트..."
cd /home/ubuntu/4th_project/elderly_rag_chatbot
source venv/bin/activate

# 데이터베이스 연결 테스트
python -c "
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.django_settings')
django.setup()
from django.db import connection
cursor = connection.cursor()
cursor.execute('SELECT version();')
print('✅ PostgreSQL 연결 성공:', cursor.fetchone()[0])
"

echo "🚀 이제 마이그레이션을 다시 시도하세요:"
echo "   python manage.py migrate"

echo ""
echo "📋 문제가 계속되면 다음 대안을 시도하세요:"
echo "1. 데이터베이스 재생성:"
echo "   sudo -u postgres dropdb elderly_rag"
echo "   sudo -u postgres createdb elderly_rag -O rag_user"
echo ""
echo "2. 새 사용자로 완전 재설정:"
echo "   sudo -u postgres dropuser rag_user"
echo "   sudo -u postgres createuser -s rag_user"
echo "   sudo -u postgres psql -c \"ALTER USER rag_user WITH PASSWORD 'changeme';\""