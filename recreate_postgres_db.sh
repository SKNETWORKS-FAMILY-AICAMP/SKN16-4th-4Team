#!/bin/bash
# PostgreSQL 데이터베이스 완전 재설정 스크립트

set -e

echo "🔄 PostgreSQL 데이터베이스 완전 재설정 중..."

# 기존 설정 백업 및 제거
echo "🗑️ 기존 데이터베이스 및 사용자 제거 중..."
sudo -u postgres psql << 'EOF'
-- 연결 종료 강제
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'elderly_rag';

-- 데이터베이스 제거 (존재하는 경우)
DROP DATABASE IF EXISTS elderly_rag;

-- 사용자 제거 (존재하는 경우)  
DROP USER IF EXISTS rag_user;
EOF

# 새 데이터베이스 및 사용자 생성 (슈퍼유저 권한으로)
echo "🆕 새 데이터베이스 및 사용자 생성 중..."
sudo -u postgres psql << 'EOF'
-- 슈퍼유저 권한을 가진 새 사용자 생성
CREATE USER rag_user WITH CREATEDB CREATEROLE LOGIN SUPERUSER;

-- 비밀번호 설정
ALTER USER rag_user WITH PASSWORD 'changeme';

-- 데이터베이스 생성 (소유자를 rag_user로 설정)
CREATE DATABASE elderly_rag OWNER rag_user;

-- 권한 확인
\l elderly_rag
\du rag_user
EOF

echo "✅ 데이터베이스 재설정 완료!"

# 연결 테스트
echo "🧪 연결 테스트 중..."
sudo -u postgres psql -d elderly_rag -U rag_user -c "SELECT 'Connection successful' as status;"

echo "🚀 이제 Django 마이그레이션을 실행하세요:"
echo "   cd /home/ubuntu/4th_project/elderly_rag_chatbot"
echo "   source venv/bin/activate"
echo "   python manage.py migrate"

echo ""
echo "📋 참고: rag_user는 이제 슈퍼유저 권한을 가지고 있어"
echo "    모든 데이터베이스 작업이 가능합니다."