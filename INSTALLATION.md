# 노인 정책 안내 챗봇 시스템 설치 가이드

## 1. Poppler 설치 (PDF OCR을 위한 필수 도구)

### Windows 설치 방법:

1. **Poppler 다운로드**
   - 다운로드 링크: https://github.com/oschwartz10612/poppler-windows/releases/
   - 최신 Release에서 `poppler-xx.xx.x.zip` 다운로드

2. **Poppler 압축 해제 및 설치**
   ```cmd
   # 예: C:\Program Files\poppler 폴더에 압축 해제
   # 압축 해제 후 폴더 구조: C:\Program Files\poppler\Library\bin\
   ```

3. **환경 변수 PATH 추가**
   - 시스템 환경 변수 편집
   - Path 변수에 추가: `C:\Program Files\poppler\Library\bin`

   또는 명령어로 추가 (관리자 권한 cmd):
   ```cmd
   setx PATH "%PATH%;C:\Program Files\poppler\Library\bin"
   ```

4. **설치 확인**
   ```cmd
   pdftoppm -v
   ```

## 2. Tesseract OCR 설치 (한글 OCR 지원)

### Windows 설치 방법:

1. **Tesseract 다운로드**
   - 다운로드 링크: https://github.com/UB-Mannheim/tesseract/wiki
   - `tesseract-ocr-w64-setup-5.x.x.exe` 다운로드

2. **Tesseract 설치**
   - 설치 중 "Additional language data" 선택 시 **Korean (kor)** 체크
   - 기본 경로: `C:\Program Files\Tesseract-OCR`

3. **환경 변수 PATH 추가**
   ```cmd
   setx PATH "%PATH%;C:\Program Files\Tesseract-OCR"
   ```

4. **설치 확인**
   ```cmd
   tesseract --version
   ```

## 3. Python 가상환경 및 패키지 설치

```bash
# 프로젝트 폴더로 이동
cd 팀프로젝트4\4th-project_mvp

# 가상환경 활성화 (이미 생성되어 있는 경우)
.\venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

## 4. 데이터베이스 마이그레이션

```bash
# 마이그레이션 파일 생성
python manage.py makemigrations

# 마이그레이션 실행
python manage.py migrate
```

## 5. 관리자 계정 생성

```bash
# admin/admin 계정 자동 생성
python create_admin.py
```

## 6. 문서 처리 (PDF/HWP 파일 로드 및 임베딩)

```bash
# data 폴더의 모든 문서를 ChromaDB에 저장
python setup.py
```

이 과정에서 다음과 같은 작업이 수행됩니다:
- PDF/HWP/HWPX 파일 읽기 (OCR 포함)
- 텍스트 청킹 (500자 단위)
- 임베딩 생성 (ko-sroberta-multitask)
- ChromaDB 저장

## 7. Django 서버 실행

```bash
python manage.py runserver
```

서버가 시작되면: http://127.0.0.1:8000 접속

## 8. 로그인 및 테스트

### 관리자 로그인
- URL: http://127.0.0.1:8000/login/
- 아이디: `admin`
- 비밀번호: `admin`

### 관리자 기능 테스트
1. **대시보드**: 통계 확인
2. **사용자 관리**: 사용자 권한 부여/제거
3. **질의응답 로그**: 채팅 기록 확인 및 평가
4. **문서 관리**: 새 정책 문서 업로드/삭제/재동기화

### 일반 사용자 테스트
1. 회원가입
2. 프로필 설정 (지역, 나이, 소득수준 등)
3. 정책 목록 확인
4. 챗봇으로 정책 질문

## 트러블슈팅

### Poppler 오류 시
Poppler가 PATH에 없으면 setup.py에서 직접 경로 지정:
```python
# setup.py 상단에 추가
import os
os.environ['PATH'] += r';C:\Program Files\poppler\Library\bin'
```

### Tesseract 오류 시
```python
# setup.py 상단에 추가
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
```

### OCR 없이 실행하려면
```bash
# OCR 기능 비활성화하고 문서 로드
python setup.py --no-ocr
```

## 주요 URL 경로

- 메인: http://127.0.0.1:8000/
- 로그인: http://127.0.0.1:8000/login/
- 회원가입: http://127.0.0.1:8000/register/
- 정책 목록: http://127.0.0.1:8000/policies/
- 챗봇: http://127.0.0.1:8000/chatbot/
- 프로필: http://127.0.0.1:8000/profile/
- 관리자 대시보드: http://127.0.0.1:8000/admin-dashboard/
- 문서 관리: http://127.0.0.1:8000/admin-documents/

## 프로젝트 구조

```
4th-project_mvp/
├── chatbot/              # Django 앱
│   ├── models.py        # User, Policy, ChatHistory, Document 모델
│   ├── views.py         # 모든 뷰 로직
│   └── urls.py          # URL 라우팅
├── documents/           # 문서 처리 모듈
│   ├── loader.py        # PDF/HWP 로더
│   ├── embedder.py      # 임베딩 생성
│   ├── vectorstore.py   # ChromaDB 관리
│   ├── document_manager.py  # 문서 CRUD 및 동기화
│   └── langgraph_rag.py # LangGraph RAG 시스템
├── templates/           # HTML 템플릿
├── static/             # CSS, JS
├── data/               # 정책 문서 (PDF/HWP)
├── chroma_db/          # ChromaDB 저장소
├── media/              # 업로드된 문서
├── setup.py            # 초기 문서 로드 스크립트
├── create_admin.py     # 관리자 생성 스크립트
└── manage.py           # Django 관리 명령어
```
