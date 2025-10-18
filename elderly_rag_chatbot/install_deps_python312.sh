#!/usr/bin/env bash
set -euo pipefail

# install_deps_python312.sh - Python 3.12 환경에서 안전한 의존성 설치
# 목적: numpy, scipy 등 네이티브 빌드가 필요한 패키지를 안전하게 설치

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo "🐍 Python 3.12 호환 의존성 설치 시작"
echo "======================================="

# Python 버전 확인
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
echo "현재 Python 버전: $python_version"

if [[ "$python_version" == "3.12" ]]; then
    echo "✓ Python 3.12 감지 - 호환성 모드로 설치합니다"
else
    echo "⚠ Python $python_version 감지 - 일반 설치를 진행합니다"
fi

# 시스템 패키지 설치 (root 권한 필요한 경우에만)
echo "1. 시스템 빌드 도구 확인 중..."
if command -v apt-get >/dev/null 2>&1; then
    echo "   Ubuntu/Debian 시스템 감지"
    sudo apt-get update
    sudo apt-get install -y \
        build-essential \
        python3-dev \
        python3-venv \
        libopenblas-dev \
        liblapack-dev \
        gfortran \
        libffi-dev \
        libssl-dev \
        pkg-config \
        cmake
elif command -v yum >/dev/null 2>&1; then
    echo "   CentOS/RHEL 시스템 감지"
    sudo yum groupinstall -y "Development Tools"
    sudo yum install -y python3-devel openblas-devel lapack-devel gcc-gfortran
else
    echo "   시스템 패키지 관리자를 찾을 수 없음 - 수동 설치 필요할 수 있습니다"
fi

# 가상환경 재생성 (옵션)
if [[ "${REMOVE_VENV:-false}" == "true" ]] && [[ -d "$VENV_DIR" ]]; then
    echo "2. 기존 venv 제거 중..."
    rm -rf "$VENV_DIR"
fi

# 가상환경 생성
echo "3. 가상환경 생성/활성화 중..."
if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
fi
source "$VENV_DIR/bin/activate"

# 핵심 도구 업그레이드
echo "4. pip/setuptools/wheel 최신 버전으로 업그레이드 중..."
python -m pip install --upgrade pip
python -m pip install --upgrade setuptools wheel build

# Python 3.12 특별 처리
if [[ "$python_version" == "3.12" ]]; then
    echo "5. Python 3.12 호환성을 위한 특별 설치..."
    
    # NumPy 먼저 바이너리로 설치
    echo "   - numpy (바이너리 휠 우선)"
    pip install --prefer-binary "numpy>=1.24.0,<1.27.0"
    
    # SciPy 바이너리로 설치
    echo "   - scipy (바이너리 휠 우선)"
    pip install --prefer-binary "scipy>=1.10.0"
    
    # PyTorch 바이너리로 설치
    echo "   - torch (바이너리 휠 우선)"
    pip install --prefer-binary "torch>=2.0.0,<2.3.0"
    
    # 기타 ML 라이브러리
    echo "   - scikit-learn (바이너리 휠 우선)"
    pip install --prefer-binary "scikit-learn>=1.3.0,<1.5.0"
    
else
    echo "5. 표준 방식으로 핵심 라이브러리 설치 중..."
    pip install --prefer-binary numpy scipy torch scikit-learn
fi

# requirements.txt 설치
echo "6. requirements.txt 설치 중..."
if pip install -r requirements.txt; then
    echo "   ✓ requirements.txt 설치 성공"
else
    echo "   ⚠ requirements.txt 설치 실패 - 개별 설치 시도"
    
    # 실패한 경우 핵심 패키지만 개별 설치
    echo "   핵심 패키지 개별 설치 중..."
    
    # Django 관련
    pip install "Django>=4.2.0,<5.0.0"
    pip install "django-cors-headers>=4.0.0"
    pip install "python-dotenv>=1.0.0"
    pip install "dj-database-url>=1.0.0"
    pip install "psycopg2-binary>=2.9.6"
    
    # LangChain 관련 (실패 시 스킵)
    pip install "langchain-core" || echo "langchain-core 설치 실패 - 스킵"
    pip install "langchain" || echo "langchain 설치 실패 - 스킵"
    pip install "langchain-openai" || echo "langchain-openai 설치 실패 - 스킵"
    pip install "langchain-community" || echo "langchain-community 설치 실패 - 스킵"
    
    # OpenAI
    pip install "openai>=1.0.0,<2.0.0"
    
    # 기타 유틸리티
    pip install pandas requests tqdm pyyaml
    
    echo "   핵심 패키지 개별 설치 완료"
fi

# 설치 결과 확인
echo "7. 설치 결과 확인 중..."
python -c "
import sys
print(f'Python: {sys.version}')

packages = ['numpy', 'pandas', 'django', 'openai']
for pkg in packages:
    try:
        exec(f'import {pkg}')
        print(f'✓ {pkg}: 설치됨')
    except ImportError:
        print(f'✗ {pkg}: 설치되지 않음')
"

echo ""
echo "======================================="
echo "🎉 Python 3.12 의존성 설치 완료!"
echo ""
echo "다음 단계:"
echo "  1. Django 마이그레이션: python manage.py migrate"
echo "  2. 정적 파일 수집: python manage.py collectstatic"
echo "  3. 서버 실행: python manage.py runserver"
echo ""
echo "문제 발생 시:"
echo "  - 로그 확인: 위 출력에서 ✗ 표시된 패키지"
echo "  - venv 재생성: REMOVE_VENV=true bash install_deps_python312.sh"
echo "  - 수동 설치: pip install --prefer-binary PACKAGE_NAME"
echo "======================================="