# 노인 복지 정책 RAG 챗봇

지역별 노인 복지 정책 PDF 문서를 기반으로 한 RAG(Retrieval-Augmented Generation) 챗봇 시스템입니다.

## 프로젝트 구조

```
4th-project_mvp/
├── elderly_rag_chatbot/     # Django 메인 애플리케이션
│   ├── chatbot_web/         # 챗봇 웹 앱
│   ├── elderly_rag_chatbot/ # Django 설정
│   ├── chroma_db/           # 벡터 데이터베이스
│   └── manage.py            # Django 관리 스크립트
├── data/                    # PDF 원본 데이터
│   └── 복지로 - 복사본/     # 지역별 복지 정책 PDF
├── venv/                    # Python 가상환경
├── 기타/                    # 이전 버전 및 문서
├── requirements.txt         # Python 패키지 목록
├── start.bat               # 서버 시작 스크립트
└── build_database.bat      # DB 구축 스크립트
```

## 빠른 시작

### 1. 필수 요구사항

- Python 3.9 이상 (3.10 권장)
- OpenAI API 키
- Git (프로젝트 클론용)
- 최소 4GB RAM (8GB 권장)

### 2. 프로젝트 클론

```bash
# 프로젝트 클론
git clone <repository-url>
cd 4th-project_mvp

# 또는 ZIP 다운로드 후 압축 해제
```

### 3. 가상환경 및 패키지 설치

**Windows**:
```bash
# 방법 1: BAT 파일 실행 (권장)
1_install_requirements.bat 더블클릭

# 방법 2: 수동 설치
python -m venv venv
venv\Scripts\activate
pip install --upgrade pip
pip install -r elderly_rag_chatbot/requirements.txt
```

**Linux/Mac**:
```bash
python -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r elderly_rag_chatbot/requirements.txt
```

### 4. 환경 설정 파일 생성

**중요**: 본인의 환경에 맞게 .env 파일을 설정해야 합니다!

```bash
# elderly_rag_chatbot 폴더로 이동
cd elderly_rag_chatbot

# .env.example 파일을 .env로 복사
# Windows:
copy .env.example .env

# Linux/Mac:
cp .env.example .env
```

### 5. .env 파일 편집

메모장 또는 VS Code로 `elderly_rag_chatbot/.env` 파일을 열고 설정:

```bash
# ============== OpenAI API 설정 (필수) ==============
OPENAI_API_KEY=sk-your-actual-api-key-here

# ============== 데이터 경로 (선택) ==============
# 대부분의 경우 비워두면 기본값 사용
MAIN_DATA_DIR=
VALIDATION_DATA_DIR=

# ============== 프로젝트 루트 (선택) ==============
# 비워두면 자동 감지
PROJECT_ROOT=
```

**OpenAI API 키 발급**:
1. https://platform.openai.com/ 접속
2. 로그인 후 API Keys 메뉴로 이동
3. "Create new secret key" 클릭
4. 생성된 키를 복사하여 .env 파일에 입력

### 6. 데이터베이스 구축

**최초 1회 또는 데이터 변경 시 실행**:

```bash
# 방법 1: BAT 파일 실행 (권장 - Windows)
2_build_database.bat 더블클릭

# 방법 2: 수동 실행
cd elderly_rag_chatbot
venv\Scripts\python.exe manage.py build_rag_database --validation
```

⚠️ 주의: 이 작업은 10-20분 정도 소요됩니다.

### 7. 서버 시작

```bash
# 방법 1: BAT 파일 실행 (권장 - Windows)
3_run_server.bat 더블클릭

# 방법 2: 수동 실행
cd elderly_rag_chatbot
venv\Scripts\python.exe manage.py runserver
```

브라우저에서 http://127.0.0.1:8000 또는 http://localhost:8000 접속

## 주요 기능

### 1. 사용자 타입별 챗봇
- **일반 사용자**: 기본 복지 정책 안내
- **관리자**: 검증용 챗봇 (상세 소스 표시)

### 2. 지역 기반 정책 추천
- 사용자 프로필의 거주 지역 우선
- 질문에서 지역 추출
- 전국 공통 정책 포함

### 3. RAG 시스템
- PDF 문서 자동 처리 (PyMuPDF, OCR)
- OpenAI 임베딩 (text-embedding-ada-002)
- SQLite 기반 벡터 검색 (ChromaDB HNSW 우회)
- GPT-4o-mini 답변 생성

## 관리자 계정

- **아이디**: admin
- **비밀번호**: admin123!

## 기술 스택

- **Backend**: Django 4.2
- **Vector DB**: ChromaDB (SQLite 백엔드)
- **LLM**: OpenAI GPT-4o-mini
- **Embedding**: OpenAI text-embedding-ada-002
- **PDF Processing**: PyMuPDF, pdfplumber, pytesseract
- **Frontend**: Bootstrap 5

## 개발 노트

### ChromaDB HNSW 인덱스 버그 해결

Windows 환경에서 ChromaDB의 HNSW 인덱스 생성 버그가 발생하여, SQLite에서 직접 임베딩 데이터를 읽어 NumPy로 코사인 유사도를 계산하는 방식으로 구현했습니다.

**파일**: `elderly_rag_chatbot/chatbot_web/rag_system/data_processing.py:530-655`

### 지역 매핑

한국의 17개 광역자치단체를 지원합니다:
- 특별시/광역시: 서울, 부산, 대구, 인천, 광주, 대전, 울산
- 특별자치시: 세종
- 도: 경기, 강원, 충북, 충남, 전북, 전남, 경북, 경남, 제주

**파일**: `elderly_rag_chatbot/chatbot_web/rag_system/rag_functions.py:28-68`

## 문제 해결

### Q: 챗봇이 답변을 못 찾습니다
**A**: `build_database.bat`를 실행하여 데이터베이스를 재구축하세요.

### Q: OpenAI API 오류
**A**: `.env` 파일의 API 키를 확인하세요.

### Q: 서버가 시작되지 않습니다
**A**:
1. 가상환경이 활성화되었는지 확인
2. `python manage.py check` 명령으로 오류 확인
3. 8000 포트가 사용 중인지 확인

## 라이선스

MIT License

## 기여

팀프로젝트 4조
