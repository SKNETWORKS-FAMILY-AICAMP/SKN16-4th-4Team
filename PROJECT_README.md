# 노인계층을 위한 정책 안내 챗봇

노인분들을 위한 맞춤형 정책 정보를 제공하는 AI 챗봇 시스템입니다.

## 주요 기능

1. **문서 처리 시스템**
   - PDF/HWP 파일 자동 로드
   - 텍스트 청킹 및 임베딩
   - ChromaDB 벡터 저장소

2. **Django 웹 애플리케이션**
   - 사용자 로그인/로그아웃
   - 정책 목록 페이지
   - AI 챗봇 (RAG 기반)
   - 사용자 프로필 관리

3. **맞춤형 정책 추천**
   - 지역, 나이, 성별 기반
   - 장애/보훈/저소득층 여부 고려

## 설치 방법

### 1. 필요 패키지 설치

```bash
pip install -r requirements.txt
```

### 2. 문서 로드 및 임베딩

```bash
python setup.py
```

이 스크립트는 `data` 폴더의 모든 PDF/HWP 파일을 읽어 ChromaDB에 저장합니다.

### 3. 데이터베이스 마이그레이션

```bash
python manage.py migrate
```

### 4. 관리자 계정 생성

```bash
python manage.py createsuperuser
```

### 5. 서버 실행

```bash
python manage.py runserver
```

브라우저에서 `http://localhost:8000` 접속

## 프로젝트 구조

```
팀프로젝트4/4th-project_mvp/
├── data/                     # 정책 문서 (PDF, HWP)
├── documents/                # 문서 처리 모듈
│   ├── loader.py            # PDF/HWP 로더
│   ├── embedder.py          # 임베딩 및 청킹
│   └── vectorstore.py       # ChromaDB 관리
├── elderly_policy/           # Django 프로젝트
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── chatbot/                  # Django 앱
│   ├── models.py            # User, Profile, Policy 모델
│   ├── views.py             # 뷰 로직
│   ├── urls.py
│   └── admin.py
├── templates/                # HTML 템플릿
│   ├── base.html
│   ├── index.html
│   ├── policies.html
│   ├── chatbot.html
│   ├── profile.html
│   └── registration/
├── static/                   # CSS, JS (Bootstrap 사용)
├── chroma_db/               # ChromaDB 저장소 (자동 생성)
├── requirements.txt
├── setup.py                 # 초기 설정 스크립트
└── manage.py
```

## 사용 방법

### 1. 회원가입 및 로그인
- 상단 메뉴에서 "회원가입" 클릭
- 로그인 후 모든 기능 이용 가능

### 2. 프로필 설정
- "내 정보" 메뉴에서 개인 정보 입력
- 나이, 지역, 성별 등 입력 시 더 정확한 맞춤형 정책 추천

### 3. 정책 목록 확인
- "정책 목록" 메뉴에서 카테고리별 정책 확인
- 각 정책 링크 클릭 시 복지로 사이트로 이동

### 4. 챗봇 사용
- "챗봇" 메뉴에서 궁금한 정책 질문
- RAG 시스템이 관련 문서를 찾아 답변 제공

## 기술 스택

- **Backend**: Django 5.0+, Python 3.10+
- **Vector DB**: ChromaDB
- **문서 처리**: PyPDF2, olefile
- **임베딩**: LangChain, sentence-transformers (ko-sroberta-multitask)
- **Frontend**: HTML, CSS, JavaScript, Bootstrap 5

## 주의사항

1. **문서 로드**: 처음 실행 시 `setup.py`를 반드시 실행하여 문서를 로드해야 합니다.
2. **임베딩 시간**: 문서가 많을 경우 임베딩에 시간이 걸릴 수 있습니다.
3. **LLM 연동**: 현재는 간단한 답변 생성만 구현되어 있습니다. 실제 운영 시에는 OpenAI API 등을 연동해야 합니다.

## 향후 개선 사항

- [ ] OpenAI API 연동하여 더 정확한 답변 생성
- [ ] 더 많은 정책 문서 추가
- [ ] 음성 인식 기능 추가 (노인 친화적)
- [ ] 모바일 반응형 UI 개선

## 라이선스

MIT License

## 문의

프로젝트 관련 문의는 이슈로 등록해주세요.
