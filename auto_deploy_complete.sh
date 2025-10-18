#!/bin/bash
# 전체 배포 자동화 실행 가이드

set -e

echo "🚀 전체 배포 자동화 실행 가이드"
echo "================================="
echo ""

cd /home/ubuntu/4th_project/elderly_rag_chatbot

echo "📋 사용 가능한 자동 배포 스크립트들:"
echo ""
echo "1️⃣ 완전 자동 배포 (full_setup.sh) - 권장"
echo "   - 시스템 패키지, PostgreSQL, Python 환경, Django 설정, Gunicorn, Nginx 모든 것 포함"
echo "   - 실행 명령:"
echo "   sudo AUTO_CONFIRM=true REMOVE_VENV=true POSTGRES_INSTALL=false \\"
echo "        POSTGRES_DB=elderly_rag POSTGRES_USER=rag_user POSTGRES_PASSWORD=changeme \\"
echo "        DOMAIN=43.202.39.220 bash full_setup.sh"
echo ""

echo "2️⃣ Ubuntu 24 전용 배포 (deploy_ubuntu24.sh)"
echo "   - AWS Lightsail Ubuntu 24 최적화"
echo "   - 실행 명령:"
echo "   sudo AUTO_CONFIRM=true POSTGRES_INSTALL=false bash deploy_ubuntu24.sh"
echo ""

echo "3️⃣ 단계별 수동 실행 (현재 방식)"
echo "   - 각 단계를 하나씩 실행"
echo "   - 문제 발생시 디버깅 용이"
echo ""

echo "💡 현재 상황 분석:"
echo "- ✅ PostgreSQL: 이미 설치되고 DB 생성됨"  
echo "- ✅ Django 마이그레이션: 완료"
echo "- ✅ 정적 파일 수집: 완료"
echo "- ❌ 슈퍼유저: 미생성"
echo "- ❌ 환경변수: 미설정 (.env 파일)"
echo "- ❌ Gunicorn 서비스: 미설정"
echo "- ❌ Nginx: 미설정"
echo ""

echo "🎯 권장 방법 (이미 PostgreSQL이 설정되어 있으므로):"
echo ""
echo "OPTION A: 완전 자동화 (PostgreSQL 건너뛰기)"
echo "sudo AUTO_CONFIRM=true REMOVE_VENV=false POSTGRES_INSTALL=false \\"
echo "     POSTGRES_DB=elderly_rag POSTGRES_USER=rag_user POSTGRES_PASSWORD=changeme \\"
echo "     DOMAIN=43.202.39.220 bash full_setup.sh"
echo ""

echo "OPTION B: 남은 단계만 수동 실행"
echo "1. python create_admin.py                    # 슈퍼유저 생성"
echo "2. nano .env                                 # 환경변수 설정"
echo "3. sudo bash deploy_ubuntu24.sh              # Gunicorn + Nginx 설정"
echo ""

echo "🔥 추천: OPTION A 실행 (완전 자동화)"
echo "    기존 설정을 그대로 두고 누락된 부분만 자동 설정됩니다."
echo ""

read -p "전체 자동 배포를 실행하시겠습니까? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 전체 자동 배포 시작..."
    sudo AUTO_CONFIRM=true REMOVE_VENV=false POSTGRES_INSTALL=false \
         POSTGRES_DB=elderly_rag POSTGRES_USER=rag_user POSTGRES_PASSWORD=changeme \
         DOMAIN=43.202.39.220 bash full_setup.sh
else
    echo "수동 배포를 계속 진행하세요."
    echo "다음 명령어: python create_admin.py"
fi