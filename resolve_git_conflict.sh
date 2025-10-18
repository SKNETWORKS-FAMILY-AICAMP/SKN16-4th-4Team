#!/bin/bash
# 🔧 Git 충돌 해결 및 프로젝트 리팩토링 진행

set -e

echo "🔧 Git 충돌 해결 및 프로젝트 리팩토링"
echo "===================================="
echo ""

echo "📋 현재 상황:"
echo "============="
echo "❌ Git 병합 충돌: restructure_project.sh 파일"
echo "🔄 해결 방법: 로컬 변경사항 커밋 후 병합"
echo ""

cd /home/ubuntu/4th_project/elderly_rag_chatbot

echo "📦 1단계: 현재 변경사항 백업"
echo "=========================="
# 현재 수정된 restructure_project.sh를 백업
cp ../restructure_project.sh ../restructure_project_fixed.sh.backup
echo "✅ 수정된 파일 백업 완료: ../restructure_project_fixed.sh.backup"

echo ""
echo "🔄 2단계: Git 상태 정리"
echo "====================="

# Git stash로 로컬 변경사항 임시 저장
git stash push -m "리팩토링 스크립트 수정사항 임시 저장"
echo "✅ 로컬 변경사항 stash 완료"

# 원격 저장소에서 최신 변경사항 가져오기
git pull origin main
echo "✅ 원격 저장소 동기화 완료"

echo ""
echo "📁 3단계: 수정된 리팩토링 스크립트 복원"
echo "===================================="

# 백업한 수정 버전을 새로운 이름으로 복원
cp ../restructure_project_fixed.sh.backup ../restructure_project_corrected.sh
chmod +x ../restructure_project_corrected.sh
echo "✅ 수정된 리팩토링 스크립트 복원 완료"

echo ""
echo "🏗️ 4단계: 프로젝트 리팩토링 실행"
echo "=============================="

echo "현재 서버 구조에 맞게 수정된 리팩토링 스크립트를 실행합니다."
echo "이 스크립트는 다음을 수행합니다:"
echo ""
echo "✅ 기존 4th_project 전체 백업"
echo "✅ 새로운 elderly_rag_project 구조 생성"
echo "✅ 앱들을 apps/ 디렉토리로 통합"
echo "✅ 템플릿, 정적파일, 스크립트 정리"
echo "✅ systemd, nginx 설정 업데이트"
echo "✅ 서비스 재시작"
echo ""

read -p "리팩토링을 실행하시겠습니까? (y/N): " -n 1 -r
echo

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 프로젝트 리팩토링 시작..."
    sudo ../restructure_project_corrected.sh
else
    echo ""
    echo "⏸️ 리팩토링을 취소했습니다."
    echo ""
    echo "📋 사용 가능한 옵션:"
    echo "1. 나중에 리팩토링 실행:"
    echo "   sudo ../restructure_project_corrected.sh"
    echo ""
    echo "2. 현재 구조로 계속 작업:"
    echo "   기존 방식대로 작업을 계속할 수 있습니다."
    echo ""
    echo "3. Git 변경사항 확인:"
    echo "   git stash list  # stash된 변경사항 확인"
    echo "   git stash pop   # stash 복원 (필요시)"
fi

echo ""
echo "📋 참고 정보:"
echo "============"
echo "🔧 수정된 리팩토링 스크립트: ../restructure_project_corrected.sh"
echo "💾 Git stash 백업: 'git stash list'로 확인 가능"
echo "📁 현재 작업 디렉토리: $(pwd)"
echo ""

if systemctl is-active --quiet elderly_rag_gunicorn; then
    SERVER_IP=$(curl -4 -s ifconfig.me 2>/dev/null || echo "43.202.39.220")
    echo "🌐 현재 웹사이트 상태: 정상 실행 중"
    echo "   접속 주소: http://$SERVER_IP"
else
    echo "⚠️ 현재 웹사이트 상태: 서비스 중단됨"
    echo "   서비스 재시작이 필요할 수 있습니다."
fi