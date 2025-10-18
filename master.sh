#!/bin/bash
# 🚀 Elderly RAG 챗봇 - 마스터 실행 스크립트
# 이 하나의 파일로 모든 작업을 할 수 있습니다.

echo "🚀 Elderly RAG 챗봇 통합 관리 시스템"
echo "====================================="
echo ""

# 권한 확인 후 실행 파일들 실행 가능하게 만들기
chmod +x /home/ubuntu/4th_project/elderly_rag_chatbot/restart_server.sh 2>/dev/null || true
chmod +x /home/ubuntu/4th_project/elderly_rag_chatbot/monitor_logs.sh 2>/dev/null || true  
chmod +x /home/ubuntu/4th_project/elderly_rag_chatbot/quick_check.sh 2>/dev/null || true

echo "📋 사용 가능한 작업:"
echo ""
echo "🔥 1. 전체 서버 재배포 및 재구동 (원클릭)"
echo "   - 코드 업데이트, 패키지 설치, DB 마이그레이션"  
echo "   - 정적파일 수집, 서비스 재시작"
echo "   - 완전 자동화된 재배포"
echo ""
echo "� 2. 502 오류 해결 (Gunicorn 문제)"
echo "   - Gunicorn 서비스 진단 및 수정"
echo "   - systemd 서비스 파일 재생성"
echo "   - 연결 테스트 및 상태 확인"
echo ""
echo "�📊 3. 실시간 로그 모니터링"
echo "   - Gunicorn, Nginx, 시스템 로그"
echo "   - 실시간 모니터링 및 디버깅"
echo ""
echo "🗑️ 4. 불필요한 파일 정리"
echo "   - 사용하지 않는 스크립트 파일 삭제"
echo "   - 시스템 정리 및 최적화"
echo ""
echo "🌐 5. 웹사이트 바로 가기 정보"
echo ""
echo "0. 종료"
echo ""

read -p "선택하세요 (1-5, 0): " choice

case $choice in
    1)
        echo ""
        echo "🚀 전체 서버 재배포 및 재구동을 시작합니다..."
        echo "이 작업은 몇 분 소요될 수 있습니다."
        echo ""
        sudo bash /home/ubuntu/4th_project/SKN16-4th-4Team/restart_server.sh
        ;;
    2)
        echo ""
        echo "🔧 502 오류 해결을 시작합니다..."
        echo "Gunicorn 서비스 문제를 진단하고 수정합니다."
        echo ""
        sudo bash /home/ubuntu/4th_project/SKN16-4th-4Team/fix_502_error.sh
        ;;
    3)
        echo ""
        echo "📊 실시간 로그 모니터링을 시작합니다..."
        bash /home/ubuntu/4th_project/SKN16-4th-4Team/monitor_logs.sh
        ;;
    4)
        echo ""
        echo "🗑️ 불필요한 파일 정리를 시작합니다..."
        bash /home/ubuntu/4th_project/SKN16-4th-4Team/cleanup_files.sh
        ;;
    5)
        SERVER_IP=$(curl -s ifconfig.me 2>/dev/null || echo "43.202.39.220")
        echo ""
        echo "🌐 웹사이트 접속 정보:"
        echo "===================="
        echo "🏠 메인 사이트:    http://$SERVER_IP"
        echo "🔧 관리자 페이지:  http://$SERVER_IP/admin"
        echo "💬 챗봇 페이지:    http://$SERVER_IP/chatbot"
        echo ""
        echo "👤 기본 관리자 계정 (변경 권장):"
        echo "   사용자명: admin"
        echo "   비밀번호: admin"
        echo ""
        ;;
    0)
        echo "종료합니다."
        exit 0
        ;;
    *)
        echo "잘못된 선택입니다."
        exit 1
        ;;
esac