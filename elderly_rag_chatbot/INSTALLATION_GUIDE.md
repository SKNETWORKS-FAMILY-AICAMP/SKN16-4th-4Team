# 노인복지 정책 RAG 챗봇 시스템 - 설치 가이드

## 📦 패키지 설치

### 1. 기본 설치
```bash
# 가상환경 활성화
cd elderly_rag_chatbot
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate

# 필수 패키지 설치
pip install -r requirements.txt
```

### 2. HWP 지원 라이브러리 (선택사항)

시스템은 기본적으로 `olefile`을 사용하여 HWP 파일을 처리합니다.
더 나은 HWP 지원을 원하시면 다음 라이브러리를 추가로 설치하세요:

```bash
# pyhwp 설치 (추천)
pip install git+https://github.com/mete0r/pyhwp.git

# 또는 수동 설치
git clone https://github.com/mete0r/pyhwp.git
cd pyhwp
pip install .
```

### 3. 설치 확인

```bash
python test_integration.py
```

## 🚀 실행 방법

### 기본 실행 (OpenAI API 없이)
```bash
python main.py --interface none
```

### 텍스트 추출 비교 테스트
```bash
python test_extraction.py
```

### AutoRAG 최적화 실행
```bash
python main.py --autorag --autorag-target speed
python main.py --autorag --autorag-target quality
python main.py --autorag --autorag-target balanced
```

### 웹 인터페이스 실행 (OpenAI API 필요)
```bash
# 환경변수 설정
set OPENAI_API_KEY=your_api_key_here

# Gradio 인터페이스
python main.py --interface gradio --port 7860

# Streamlit 인터페이스  
python main.py --interface streamlit --port 8501
```

## 📊 지원되는 파일 형식

### PDF 추출기 (4개)
- **PyMuPDF** (추천) - 빠르고 정확
- **pdfplumber** - 표 추출에 우수
- **PyPDF2** - 경량화된 처리
- **pdfminer** - 복잡한 레이아웃 처리

### HWP 추출기 (3개)
- **olefile** (기본) - 기본적인 HWP 지원
- **pyhwp** (선택) - 향상된 HWP 처리
- **hwp5** (선택) - 고급 HWP 기능

## ⚙️ 시스템 요구사항

- Python 3.8+
- RAM: 최소 4GB (권장 8GB)
- 디스크: 2GB 이상 여유공간
- OS: Windows 10/11, Linux, macOS

## 🔧 문제 해결

### 패키지 설치 오류
```bash
# pip 업그레이드
python -m pip install --upgrade pip

# 캐시 정리 후 재설치
pip cache purge
pip install -r requirements.txt --no-cache-dir
```

### CUDA/GPU 설정 (선택사항)
```bash
# GPU 버전 PyTorch 설치
pip uninstall torch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### 메모리 부족 오류
```bash
# 경량화된 모델 사용
export TOKENIZERS_PARALLELISM=false
```

## 📝 추가 정보

- 텍스트 추출 성능 비교 결과: `test_extraction.py` 실행
- AutoRAG 최적화 옵션: `python main.py --help`
- 로그 파일: `logs/` 디렉토리 확인