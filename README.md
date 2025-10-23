# 노인 복지 정책 RAG 챗봇 시스템

[![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat&logo=docker&logoColor=white)](https://www.docker.com/)
[![Django](https://img.shields.io/badge/Django-092E20?style=flat&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-316192?style=flat&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![LangChain](https://img.shields.io/badge/LangChain-121212?style=flat&logo=chainlink&logoColor=white)](https://www.langchain.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-412991?style=flat&logo=openai&logoColor=white)](https://openai.com/)

> RAG(Retrieval-Augmented Generation) 기술을 활용한 지능형 노인 복지 정책 안내 챗봇

**프로젝트**: SKN16-4th-4Team
**버전**: 2.1.0
**최종 업데이트**: 2025-10-23

---

## 목차

- [프로젝트 소개](#-프로젝트-소개)
- [주요 기능](#-주요-기능)
- [기술 스택](#%EF%B8%8F-기술-스택)
- [시스템 아키텍처](#%EF%B8%8F-시스템-아키텍처)
- [빠른 시작](#-빠른-시작)
- [프로젝트 구조](#-프로젝트-구조)
- [환경 변수 설정](#-환경-변수-설정)
- [API 문서](#-api-문서)
- [배포 가이드](#-배포-가이드)
- [라이센스](#-라이센스)

---

## 프로젝트 소개

노인 복지 챗봇은 **RAG(Retrieval-Augmented Generation)** 기술을 활용하여 노인과 그 가족들이 복지 정책 정보를 쉽게 찾고 이해할 수 있도록 돕는 지능형 챗봇 시스템입니다.

### 주요 특징

-  **정확한 정보 제공**: 최신 복지 정책 문서를 기반으로 정확한 정보 제공
-  **자연어 대화**: GPT-4를 활용한 자연스러운 한국어 대화
-  **지역별 맞춤 정보**: 17개 시도별 복지 정책 정보 제공
-  **AI 기반 피드백 분석**: OpenAI를 활용한 사용자 피드백 자동 분류 및 감정 분석
-  **사용자 피드백**: 메시지 및 세션 평가 시스템
-  **북마크 기능**: 유용한 답변 저장 및 관리
-  **맞춤형 추천**: 사용자 프로필 기반 복지 정책 추천
-  **간편한 배포**: Docker 기반 원클릭 배포 시스템
-  **안정적인 운영**: PostgreSQL + ChromaDB 통합

### 두 가지 챗봇 시스템

1. **일반 챗봇**: 일반 사용자를 위한 실제 서비스
2. **검증 챗봇**: 관리자용 RAG 시스템 테스트 및 검증 (디버그 정보 포함)

---

##  주요 기능

### 1. 지능형 챗봇
![Initial](https://github.com/user-attachments/assets/d4a2a51f-3aee-4c16-8491-86a03e81992e)
- GPT-4 기반 자연어 이해 및 응답
- 복지 정책 문서 기반 RAG 시스템
- 대화 히스토리 관리 및 컨텍스트 유지
- 세션 평가 시스템 (별점 0.5~5.0)
- 실시간 피드백 수집 (thumbs up/down)

### 2. 복지 정책 검색
![Initial](https://github.com/user-attachments/assets/6738bd2c-daf9-4ce3-b026-498bd5c709bd)
- 지역별 복지 정책 검색 (17개 시도)
- 카테고리별 정책 분류
- 신청 자격 및 방법 안내
- FAQ 시스템
- 출처 표시 (파일 확장자 제거로 깔끔한 UI)

### 3. 맞춤형 추천 시스템
![Initial](https://github.com/user-attachments/assets/a6e79514-6dfb-4861-888f-84d749edb391)
- **프로필 기반 자동 분기**: 프로필 설정 여부에 따라 자동으로 간소화된 폼 제공
- 나이, 지역, 성별 기반 필터링
- 관심 분야별 정책 추천 (기초연금, 장기요양보험, 의료지원, 주거지원, 일자리, 문화/여가)
- 추가 대상 정책 선택 (장애인, 국가유공자, 저소득층)
- 간편 추천 (기존 프로필 사용자)
- 상세 추천 (신규 사용자)

### 4. 사용자 관리
![Initial](https://github.com/user-attachments/assets/d6d5d722-5bc2-4ef4-bdeb-779e363654d7)
- **일반 로그인** 및 **카카오 간편 로그인** 지원
- 회원가입 및 로그인
- 카카오 OAuth 2.0 연동 (자동 회원가입)
- **개선된 프로필 관리**:
  - 기본 정보: 나이, 성별, 지역
  - 비밀번호 변경 별도 페이지 분리
  - 카카오 사용자는 비밀번호 변경 불가
- 대화 기록 저장 및 조회
- 북마크 관리

### 5. 관리자 기능
![Initial](https://github.com/user-attachments/assets/c6a6ed69-2105-459d-a800-b9d71ccccec1)
- 복지 정책 데이터 관리
- 사용자 관리
- 챗봇 대화 로그 분석
- **고급 피드백 분석 대시보드**:
  - AI 기반 피드백 자동 분류 (기능 요청, 버그, 사용성 문제, 칭찬, 기타)
  - 감정 분석 (긍정, 중립, 부정)
  - 카테고리별 분포 차트
  - 감정 분석 차트
  - 카테고리별 평균 평점 분석
- 검증용 챗봇 (디버그 정보 포함)
- **AutoRAG 최적화 시스템**:
  - 전체 파이프라인 자동 최적화
  - 텍스트 추출 방법 최적화 (PDF, HWP)
  - 청킹 전략 최적화
  - 임베딩 모델 최적화
  - 검색기 성능 최적화
  - 최적 설정 자동 추천

---

## 기술 스택

### Backend
- **Django 4.2+**: 웹 프레임워크
- **Gunicorn**: WSGI HTTP 서버
- **PostgreSQL 15**: 관계형 데이터베이스
- **Redis**: 캐싱 및 세션 관리

### AI/ML
- **OpenAI GPT-4**: 자연어 생성
- **LangChain**: RAG 파이프라인 구축
- **ChromaDB**: 벡터 데이터베이스
- **HuggingFace Embeddings**: 문서 임베딩

### Frontend
- **HTML5/CSS3**: 마크업 및 스타일링
- **Bootstrap 5**: UI 프레임워크
- **JavaScript**: 인터랙티브 기능
- **Chart.js**: 데이터 시각화

### DevOps
- **Docker & Docker Compose**: 컨테이너화
- **Nginx**: 리버스 프록시 및 정적 파일 서빙
- **Let's Encrypt**: SSL/TLS 인증서
- **AWS Lightsail**: 클라우드 호스팅

---

## 시스템 아키텍처

```
┌─────────────┐
│   사용자    │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│            Nginx                    │
│   (Reverse Proxy + SSL/TLS)        │
└─────────────┬───────────────────────┘
              │
              ▼
┌────────────────────────────────────┐
│         Django Application         │
│  ┌──────────────────────────────┐  │
│  │    Chat Interface            │  │
│  │  ┌────────┐    ┌──────────┐  │  │
│  │  │ User   │    │  Admin   │  │  │
│  │  │Chatbot │    │ Chatbot  │  │  │
│  │  └────────┘    └──────────┘  │  │
│  └──────────────────────────────┘  │
│  ┌──────────────────────────────┐  │
│  │    RAG System                │  │
│  │  ┌────────────────────────┐  │  │
│  │  │   LangChain Pipeline   │  │  │
│  │  │  ┌──────┐  ┌────────┐  │  │  │
│  │  │  │GPT-4 │  │Chroma  │  │  │  │
│  │  │  │o-mini│  │  DB    │  │  │  │
│  │  │  └──────┘  └────────┘  │  │  │
│  │  └────────────────────────┘  │  │
│  └──────────────────────────────┘  │
└─────────────┬──────────────────────┘
              │
       ┌──────┴──────┐
       │             │
       ▼             ▼
┌─────────────┐ ┌─────────────┐
│ PostgreSQL  │ │  ChromaDB   │
│             │ │   (Vector   │
│  - Users    │ │    Store)   │
│  - Sessions │ │             │
│  - Messages │ │  - Policy   │
│  - Policies │ │    Docs     │
│  - Feedback │ │  - Embed-   │
│             │ │    dings    │
└─────────────┘ └─────────────┘
```

---

## 빠른 시작

### 사전 요구사항

- Docker & Docker Compose
- OpenAI API Key

### Docker 배포 (권장)

1. **저장소 클론**
```bash
git clone https://github.com/yourusername/elderly-welfare-chatbot.git
cd elderly-welfare-chatbot
```

2. **환경 변수 설정**
```bash
cp .env.example .env
# .env 파일을 편집하여 필수 변수 설정
```

3. **Docker 컨테이너 실행**
```bash
docker compose -f docker-compose.prod.yml up -d
```

4. **데이터베이스 마이그레이션**
```bash
docker compose -f docker-compose.prod.yml exec django python manage.py migrate
```

5. **관리자 계정 생성**
```bash
docker compose -f docker-compose.prod.yml exec django python manage.py createsuperuser
```

6. **정적 파일 수집**
```bash
docker compose -f docker-compose.prod.yml exec django python manage.py collectstatic --noinput
```

7. **접속**
- 일반 사용자: http://localhost
- 관리자: http://localhost/admin

### SSL/HTTPS 설정 (선택사항)

```bash
./setup_ssl.sh your-domain.com your-email@example.com
```

---

## 프로젝트 구조

```
c:\develop1\d\
├── db.sqlite3                  # 개발용 DB (gitignore됨)
├── docker-compose.yml          # 개발용 Docker 설정
├── docker-compose.prod.yml     # 프로덕션 Docker 설정
├── docker-entrypoint.sh        # Docker 실행 스크립트
├── Dockerfile                  # Docker 이미지 빌드
├── gunicorn_config.py          # Gunicorn 설정
├── manage.py                   # Django 관리 명령
├── README.md                   # 프로젝트 문서
├── requirements.txt            # Python 의존성
├── requirements-prod.txt       # 프로덕션 의존성
├── apps/                       # Django 앱
├── config/                     # Django 설정
├── docker/                     # Docker 설정 파일
├── src/                        # RAG 시스템 소스
├── static/                     # 정적 파일
└── templates/     
```

---

## 환경 변수 설정

`.env` 파일에 다음 변수들을 설정하세요:

```env
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com

# Database
POSTGRES_DB=chatbot_db
POSTGRES_USER=chatbot_user
POSTGRES_PASSWORD=strong-password-here
POSTGRES_HOST=db
POSTGRES_PORT=5432

# OpenAI
OPENAI_API_KEY=sk-your-api-key-here

# Kakao Login (선택사항)
KAKAO_REST_API_KEY=your-kakao-rest-api-key
KAKAO_REDIRECT_URI=http://your-domain/kakao/callback/

# Email (선택사항)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

---

## API 문서

### 주요 엔드포인트

#### 1. 채팅 API
```http
POST /chat/api/message/
Content-Type: application/json

{
  "session_id": "uuid-string",
  "message": "기초연금이 무엇인가요?"
}
```

**응답:**
```json
{
  "response": "기초연금은...",
  "sources": [...],
  "retrieved_count": 3,
  "message_id": 123
}
```

#### 2. 피드백 제출 API
```http
POST /feedback/submit/
Content-Type: application/json

{
  "message_id": 123,
  "rating": 5,
  "comment": "매우 유용한 정보입니다"
}
```

**응답:**
```json
{
  "success": true,
  "feedback_id": 456,
  "message": "피드백이 저장되었습니다."
}
```

#### 3. 맞춤형 추천 API
```http
POST /quick-start/recommend/
Content-Type: application/json

{
  "age": 70,
  "region": "서울",
  "interests": ["기초연금", "의료지원"],
  "disability": false,
  "veteran": false,
  "low_income": false
}
```

**응답:**
```json
{
  "summary": "추천 정책 요약",
  "recommendations": [...]
}
```

---

## 🚢 배포 가이드

### AWS Lightsail 배포

1. **Lightsail 인스턴스 생성**
   - OS: Ubuntu 20.04 LTS
   - 플랜: 최소 2GB RAM

2. **방화벽 설정**
   - HTTP (80)
   - HTTPS (443)
   - Custom (8000) - 개발용

3. **배포 스크립트 실행**
```bash
./deploy_final.sh
```

4. **SSL 설정**
```bash
./setup_ssl.sh your-domain.com your-email@example.com
```

### 주요 명령어

**서비스 재시작:**
```bash
docker compose -f docker-compose.prod.yml restart
```

**로그 확인:**
```bash
docker compose -f docker-compose.prod.yml logs -f django
docker compose -f docker-compose.prod.yml logs -f nginx
```

**데이터베이스 백업:**
```bash
docker compose -f docker-compose.prod.yml exec db pg_dump -U chatbot_user chatbot_db > backup.sql
```

---

## 주요 업데이트 (v2.0.0)

### Phase 1: 긴급 버그 수정
- CSRF 보안 강화 (@csrf_exempt 제거)
- 출처 표시 개선 (파일 확장자 제거)
- 검증용 챗봇 UI 통일
- 피드백 message_id 누락 문제 해결

### Phase 2: 기능 개선
- 프로필 설정 리팩토링 (비밀번호 변경 분리)
- 빠른 챗봇 실행 분기 개선
- 민감 정보 체크박스 재배치
- 국가유공자 옵션 추가

### Phase 3: 고급 기능
- AI 기반 피드백 자동 분류 및 감정 분석
- 피드백 분석 대시보드 개선
- Chart.js 기반 시각화 강화

---

## 라이센스

This project is licensed under the MIT License.

---

## 팀

**SKN16-4th-4Team**

- 프로젝트 기간: 2025.10
- 기술 스택: Django, OpenAI, LangChain, ChromaDB, Docker
- 배포: AWS Lightsail

---

## 문의

프로젝트 관련 문의사항이 있으시면 이슈를 생성해주세요.

---

**Made with ❤️ by SKN16-4th-4Team**
