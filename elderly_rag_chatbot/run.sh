#!/bin/bash

# ========================================
# 🏥 노인복지 정책 RAG 챗봇 시스템
# ========================================

echo "=========================================="
echo "🏥 노인복지 정책 RAG 챗봇 시스템"
echo "=========================================="
echo

# 스크립트 디렉토리를 프로젝트 루트로 설정
cd "$(dirname "$0")"

# Python 가상환경 확인
if [ -f "venv/bin/python" ]; then
    echo "🐍 가상환경을 사용합니다..."
    PYTHON_PATH="venv/bin/python"
elif [ -f "env/bin/python" ]; then
    echo "🐍 가상환경을 사용합니다..."
    PYTHON_PATH="env/bin/python"
else
    echo "🐍 시스템 Python을 사용합니다..."
    PYTHON_PATH="python3"
fi

# 환경 변수 로드
if [ -f ".env" ]; then
    echo "⚙️  환경 변수를 로드합니다..."
    export $(cat .env | grep -v '^#' | xargs)
fi

# 의존성 확인
echo "📦 의존성 패키지를 확인합니다..."
$PYTHON_PATH -c "
import sys
required_packages = [
    'langchain', 'chromadb', 'sentence_transformers', 
    'gradio', 'streamlit', 'numpy', 'pandas'
]
missing = []
for pkg in required_packages:
    try:
        __import__(pkg.replace('-', '_'))
    except ImportError:
        missing.append(pkg)

if missing:
    print(f'❌ 누락된 패키지: {missing}')
    print('다음 명령으로 설치하세요: pip install -r requirements.txt')
    sys.exit(1)
else:
    print('✅ 모든 의존성 패키지가 설치되어 있습니다.')
"

if [ $? -ne 0 ]; then
    echo "설치 후 다시 실행해주세요."
    exit 1
fi

# 데이터 디렉토리 확인
if [ ! -d "data/복지로" ]; then
    echo "⚠️  경고: 데이터 디렉토리 'data/복지로'가 없습니다."
    echo "예시 데이터로 테스트합니다."
fi

# 시스템 실행
echo "🚀 시스템을 시작합니다..."
echo

$PYTHON_PATH main.py "$@"

exit_code=$?

if [ $exit_code -ne 0 ]; then
    echo
    echo "❌ 시스템 실행에 실패했습니다."
    echo "다음을 확인해주세요:"
    echo "1. Python이 올바르게 설치되어 있는지 확인"
    echo "2. 필요한 패키지가 설치되어 있는지 확인: pip install -r requirements.txt"
    echo "3. 데이터 디렉토리가 존재하는지 확인: data/복지로/"
    echo "4. OpenAI API 키가 설정되어 있는지 확인 (선택사항)"
    echo
    exit 1
fi

echo
echo "✅ 시스템이 정상적으로 종료되었습니다."