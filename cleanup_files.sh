#!/bin/bash
# 🗑️ 불필요한 실행파일 정리 스크립트

set -e

echo "🗑️ 불필요한 실행파일 정리"
echo "========================"

cd /home/ubuntu/4th_project

# 보관할 필수 파일들
KEEP_FILES=(
    "master.sh"
    "restart_server.sh" 
    "monitor_logs.sh"
    "fix_502_error.sh"
)

echo "📋 보관할 필수 파일:"
for file in "${KEEP_FILES[@]}"; do
    echo "  ✅ $file"
done

echo ""
echo "🗑️ 삭제할 불필요한 파일들:"

# SKN16-4th-4Team 디렉토리의 불필요한 스크립트들
CLEANUP_FILES=(
    "test_postgres_connection.sh"
    "recreate_postgres_db.sh" 
    "quick_fix_static.sh"
    "fix_static_files.sh"
    "fix_postgres_permissions.sh"
    "fix_postgresql_auth.sh"
    "fix_peer_authentication.sh"
    "deployment_checklist.sh"
    "create_superuser_guide.sh"
    "auto_deploy_complete.sh"
    "quick_check.sh"
    "종합실행가이드.bat"
    "run_server.bat"
    "quick_start.bat"
)

# elderly_rag_chatbot 디렉토리의 불필요한 스크립트들
ELDERLY_CLEANUP_FILES=(
    "install_deps_python312.sh"
    "full_setup.sh"
    "fix_env.sh"
    "fix_csrf_origins.sh"
    "deploy_ubuntu24.sh"
    "deploy_linux.sh"
    "validate_setup.sh"
    "deploy.bat"
    "run_comparison.bat"
    "run.bat"
    "커스텀빌더.bat"
    "챗봇실행.bat"
    "성능분석.bat"
    "run.sh"
)

# 메인 디렉토리 정리
cd SKN16-4th-4Team
for file in "${CLEANUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  🗑️ 삭제: $file"
        rm -f "$file"
    fi
done

# elderly_rag_chatbot 디렉토리 정리
cd elderly_rag_chatbot
for file in "${ELDERLY_CLEANUP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  🗑️ 삭제: $file"  
        rm -f "$file"
    fi
done

# 백업 디렉토리 정리 (7일 이상 된 것들)
echo ""
echo "🧹 오래된 백업 파일 정리:"
if [ -d "/home/ubuntu/elderly_rag_backups" ]; then
    find /home/ubuntu/elderly_rag_backups -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    echo "  ✅ 7일 이상 된 백업 삭제 완료"
fi

# 임시 파일 정리
echo ""
echo "🧹 임시 파일 정리:"
cd /home/ubuntu/4th_project/elderly_rag_chatbot
rm -f *.pyc __pycache__ .DS_Store *.log~ 2>/dev/null || true
echo "  ✅ 임시 파일 정리 완료"

echo ""
echo "✅ 파일 정리 완료!"
echo ""
echo "📋 남은 필수 파일들:"
cd /home/ubuntu/4th_project/SKN16-4th-4Team
for file in "${KEEP_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file ($(ls -lh $file | awk '{print $5}'))"
    fi
done

echo ""
echo "🎯 앞으로 이 파일들만 사용하세요:"
echo "  📍 메인 관리: ../master.sh"
echo "  🔧 502 오류 해결: ./fix_502_error.sh"  
echo "  🔄 전체 재배포: ./restart_server.sh"
echo "  📊 로그 모니터링: ./monitor_logs.sh"