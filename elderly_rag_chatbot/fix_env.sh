#!/usr/bin/env bash
set -euo pipefail

# fix_env.sh - .env 파일 자동 복구 스크립트
# 용도: 서버에서 .env 파싱 에러 발생 시 자동으로 백업/복구/검증

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "== .env 파일 자동 복구 시작 =="

# 백업 생성
if [ -f "$PROJECT_DIR/.env" ]; then
    backup_file=".env.bak.$(date +%Y%m%d_%H%M%S)"
    cp "$PROJECT_DIR/.env" "$PROJECT_DIR/$backup_file"
    echo "백업 생성: $backup_file"
fi

# .env가 없으면 .env.example에서 복사
if [ ! -f "$PROJECT_DIR/.env" ] && [ -f "$PROJECT_DIR/.env.example" ]; then
    echo ".env 파일이 없음 - .env.example에서 생성"
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
fi

# 문제가 되는 문자들 제거
if [ -f "$PROJECT_DIR/.env" ]; then
    echo "문제 문자 제거 중..."
    
    # Markdown 코드블록 마커 제거
    sed -i '/^```/d' "$PROJECT_DIR/.env"
    sed -i '/^````/d' "$PROJECT_DIR/.env"
    
    # 모든 백틱 제거
    sed -i 's/`//g' "$PROJECT_DIR/.env"
    
    # 빈 줄 정리
    sed -i '/^$/N;/^\n$/d' "$PROJECT_DIR/.env"
    
    echo "문제 문자 제거 완료"
fi

# SECRET_KEY 안전하게 재생성
echo "SECRET_KEY 재생성 중..."
NEW_SECRET=$(python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(50))
PY
)

if grep -q '^SECRET_KEY=' "$PROJECT_DIR/.env"; then
    sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${NEW_SECRET}|" "$PROJECT_DIR/.env"
else
    echo "SECRET_KEY=${NEW_SECRET}" >> "$PROJECT_DIR/.env"
fi

echo "SECRET_KEY 재생성 완료"

# .env 문법 검증
echo "문법 검증 중..."
if bash -n -c "set -a; source '$PROJECT_DIR/.env'; set +a" 2>/dev/null; then
    echo "✓ .env 문법 검증 통과"
else
    echo "✗ .env 문법 에러 - 수동 편집 필요"
    echo "편집: nano $PROJECT_DIR/.env"
    exit 1
fi

# 현재 .env 상태 요약 출력
echo ""
echo "== .env 복구 완료 =="
echo "파일 위치: $PROJECT_DIR/.env"
echo "백업 파일: $PROJECT_DIR/$backup_file"
echo ""
echo "주요 설정 확인:"
grep -E '^(DEBUG|SECRET_KEY|DATABASE_URL|OPENAI_API_KEY|DOMAIN)=' "$PROJECT_DIR/.env" | sed 's/SECRET_KEY=.*/SECRET_KEY=***/' | sed 's/OPENAI_API_KEY=.*/OPENAI_API_KEY=***/' || true

echo ""
echo "다음 단계: 서비스 재시작"
echo "sudo systemctl restart elderly_rag_gunicorn"
echo "sudo systemctl restart nginx"