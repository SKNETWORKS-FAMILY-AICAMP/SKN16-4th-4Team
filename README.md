# 4th-project_mvp

# 🏥 노인 복지 정책 RAG 챗봇 시스템

> **Django 웹 애플리케이션 + RAG 챗봇이 결합된 완전한 복지 정책 상담 시스템**

## 🎯 프로젝트 개요

이 시스템은 **노인 복지 정책에 관한 질문에 정확하게 답변하는 AI 챗봇**과 **웹 기반 관리 시스템**을 제공합니다.

### ✨ 주요 기능
- 🤖 **스마트 복지 정책 챗봇** (무관한 질문 필터링)
- 🌐 **Django 웹 인터페이스** (사용자 관리, 채팅 로그)
- 📊 **고급 RAG 시스템** (텍스트 추출, 임베딩, 검색)
- 🎮 **리모컨 방식 시스템 제어** (성능 분석, 자동 최적화)
- 🏗️ **서브웨이 스타일 커스텀 챗봇 구성**

## 🚀 빠른 시작

### 1. 웹 서비스 실행 (Django)
```bash
# 환경 설정
python -m venv .venv
.venv\Scripts\activate  # 윈도우
pip install -r requirements.txt

# Django 서버 시작
python manage.py migrate
python manage.py runserver

# 브라우저에서 http://localhost:8000 접속
```

### 2. RAG 챗봇 직접 실행
```bash
cd elderly_rag_chatbot
python smart_custom_chatbot.py

# 질문 예시:
# "65세 이상 기초연금이 궁금해요"
# "장애인 활동지원 서비스는 어떻게 신청하나요?"
```

### 3. 통합 제어 시스템
```bash
cd elderly_rag_chatbot
python rag_launcher.py  # 19개 메뉴 통합 런처
python final_analyzer.py  # 상세 분석 및 커스텀 챗봇 빌더
```

## 📁 프로젝트 구조

```
4th-project_mvp/
├── 🌐 Django 웹 애플리케이션
│   ├── elderly_policy/          # Django 프로젝트 설정
│   ├── chatbot/                 # 챗봇 앱
│   ├── templates/               # HTML 템플릿
│   ├── manage.py               # Django 관리 스크립트
│   └── requirements.txt        # 웹 서비스 의존성
│
├── 🤖 RAG 챗봇 시스템
│   └── elderly_rag_chatbot/    # 🔥 핵심 RAG 시스템
│       ├── smart_custom_chatbot.py    # 메인 챗봇
│       ├── rag_remote_control.py      # 리모컨 시스템  
│       ├── final_analyzer.py          # 완전한 분석 도구
│       ├── rag_launcher.py            # 통합 런처
│       ├── src/                       # 핵심 모듈들
│       ├── config/                    # 설정 파일들
│       ├── results/                   # 분석 결과
│       └── README_완전가이드.md       # 🔥 상세 사용법
│
├── 📄 데이터
│   ├── data/복지로/            # 실제 복지 정책 문서들
│   └── documents/              # 문서 처리 모듈
│
└── 🚀 실행 스크립트
    ├── quick_start.bat         # 윈도우 빠른 시작
    ├── run_server.bat          # Django 서버 실행
    └── QUICK_START.md          # 빠른 시작 가이드
```

## 💡 사용 시나리오별 가이드

### 🎯 목적별 선택 가이드

| 목적 | 추천 실행 방법 | 파일 |
|------|-------------|------|
| **웹에서 채팅** | Django 서버 실행 | `python manage.py runserver` |
| **챗봇만 테스트** | RAG 챗봇 직접 실행 | `python smart_custom_chatbot.py` |
| **성능 분석** | 통합 분석 도구 | `python final_analyzer.py` |
| **시스템 제어** | 리모컨 런처 | `python rag_launcher.py` |
| **커스텀 챗봇** | 서브웨이 스타일 빌더 | `final_analyzer.py` → 11번 메뉴 |

### 🔧 관리자용 기능

#### 문서 관리
```bash
# 새 복지 정책 문서 추가
1. data/복지로/ 폴더에 PDF/HWP 파일 추가
2. Django Admin에서 문서 등록
3. RAG 시스템 재시작
```

#### 성능 모니터링
```bash
cd elderly_rag_chatbot
python final_analyzer.py
# "10. 성능 종합 리포트 생성" 선택
```

#### 채팅 로그 분석
- Django Admin → 채팅 로그 → 통계 확인
- 사용자 질문 패턴 분석
- 답변 정확도 평가

## 📊 시스템 특징

### 🛡️ 가드 시스템
- **복지 정책 질문만** 처리 (음식, 게임 등 차단)
- **정보 없음** 친절한 안내
- **부적절한 질문** 자동 필터링

### 🎮 리모컨 시스템  
- **원클릭** 모든 기능 제어
- **성능 비교** 자동 분석
- **AutoRAG** 최적화

### 🏗️ 커스텀 챗봇 빌더
- **서브웨이 스타일** 5단계 구성
- **실시간 성능** 테스트
- **구성 저장/로드** 기능

## 🆘 문제해결

### 자주 묻는 질문

**Q: 챗봇이 "정보가 없다"고만 답변해요**  
A: `data/복지로/` 폴더에 문서가 있는지 확인하고, `python rag_launcher.py` → "18. 시스템 상태"로 확인

**Q: HWP 파일이 처리되지 않아요**  
A: HWP는 제한적 지원. PDF 변환 권장 또는 `pip install olefile` 설치

**Q: 메모리 오류가 발생해요**  
A: `config/` 폴더에서 청킹 크기를 1024→512로 줄이거나 CPU 모드 사용

### 상세 문제해결
👉

## 📚 상세 문서

### 🔥 필수 읽기
- **[📖 완전 가이드](elderly_rag_chatbot/README_완전가이드.md)** - 처음 보는 사람도 쉽게 따라할 수 있는 친절한 설명서
- **[🚀 빠른 시작](QUICK_START.md)** - 5분 만에 시작하기
- **[🔧 설치 가이드](INSTALLATION.md)** - 상세 설치 방법

### 📋 추가 문서
- **[📊 RAG 시스템 구현 상세](RAG_시스템_구현_상세_설명.txt)**
- **[📁 디렉토리 구조](elderly_rag_chatbot/DIRECTORY_STRUCTURE.md)**
- **[📄 최종 보고서](elderly_rag_chatbot/FINAL_REPORT.md)**

## 🎉 주요 성과

### ✅ 완성된 기능들
- ✅ **실제 복지 정책 데이터** 기반 정확한 답변
- ✅ **무관한 질문 필터링** 시스템  
- ✅ **서브웨이 스타일** 커스텀 챗봇 구성
- ✅ **리모컨 방식** 통합 제어 시스템
- ✅ **Django 웹** 인터페이스
- ✅ **성능 분석 및 최적화** 도구
- ✅ **사용자 친화적** 메뉴 시스템

### 🏆 기술적 성취
- **8가지 복지 정책** 실데이터 탑재
- **5단계 RAG 파이프라인** 구축
- **95% 신뢰도** 답변 시스템
- **19개 메뉴** 통합 제어 시스템
- **가드 기능** 완벽 구현

## 🚀 시작하세요!

### 🎯 추천 시작 순서
1. **환경 설정**: `pip install -r requirements.txt`
2. **Django 서버**: `python manage.py runserver` (웹 인터페이스)
3. **RAG 챗봇**: `cd elderly_rag_chatbot && python smart_custom_chatbot.py`
4. **전체 둘러보기**: `python rag_launcher.py`
5. **커스텀 챗봇**: `python final_analyzer.py` → 11번 메뉴

### 💬 질문 예시
- "65세 이상 기초연금은 얼마나 받을 수 있나요?"
- "장애인 활동지원 서비스 신청 방법이 궁금해요"
- "저소득층 의료비 지원 조건을 알려주세요"
- "한부모가족 지원 정책에 대해 설명해주세요"

**🎉 즐거운 복지 정책 챗봇 개발 되세요!** 🚀

## 📋 프로젝트 구조

```
4th-project_mvp/
├── backend/          # Express.js 백엔드 서버
│   ├── server.js     # 메인 서버 파일
│   ├── package.json  # 백엔드 의존성
│   └── .env.example  # 환경 변수 예시
└── frontend/         # 프론트엔드 애플리케이션
    ├── public/       # 정적 파일
    │   ├── index.html
    │   └── style.css
    └── src/          # 소스 코드
        └── app.js
```

## 🚀 시작하기

### 필수 요구사항

- Node.js (v14 이상)
- npm 또는 yarn

### 설치 방법

1. **저장소 클론**
   ```bash
   git clone https://github.com/inucreativehrd21/4th-project_mvp.git
   cd 4th-project_mvp
   ```

2. **백엔드 설정**
   ```bash
   cd backend
   npm install
   ```

3. **환경 변수 설정** (선택사항)
   ```bash
   cp .env.example .env
   # .env 파일을 필요에 맞게 수정
   ```

### 실행 방법

1. **백엔드 서버 실행**
   ```bash
   cd backend
   npm start
   ```
   서버는 기본적으로 `http://localhost:3000`에서 실행됩니다.

2. **프론트엔드 실행**
   
   프론트엔드는 정적 HTML 파일이므로, 다음 방법 중 하나로 실행할 수 있습니다:
   
   - **방법 1: 브라우저에서 직접 열기**
     ```bash
     # frontend/public/index.html 파일을 브라우저에서 열기
     ```
   
   - **방법 2: 간단한 HTTP 서버 사용**
     ```bash
     cd frontend/public
     # Python 3
     python -m http.server 8000
     # 또는 Node.js의 http-server
     npx http-server -p 8000
     ```
     브라우저에서 `http://localhost:8000` 접속

## 📡 API 엔드포인트

### 헬스 체크
- **GET** `/health`
  - 서버 상태 확인
  - Response: `{ status, message, timestamp }`

### 데이터 조회
- **GET** `/api/hello`
  - 환영 메시지
  - Response: `{ message, version }`

- **GET** `/api/data`
  - 샘플 데이터 조회
  - Response: `{ items: [...] }`

### 데이터 생성
- **POST** `/api/data`
  - 새로운 데이터 추가
  - Body: `{ name, description }`
  - Response: `{ message, data }`

## 🛠️ 기술 스택

### 백엔드
- **Node.js** - JavaScript 런타임
- **Express.js** - 웹 프레임워크
- **CORS** - Cross-Origin Resource Sharing
- **dotenv** - 환경 변수 관리

### 프론트엔드
- **HTML5** - 마크업
- **CSS3** - 스타일링 (그라디언트, 반응형 디자인)
- **Vanilla JavaScript** - 클라이언트 로직
- **Fetch API** - HTTP 요청

## 📝 주요 기능

1. **서버 상태 확인**
   - 실시간 헬스 체크
   - 서버 연결 상태 모니터링

2. **데이터 조회**
   - REST API를 통한 데이터 가져오기
   - 샘플 데이터 표시

3. **데이터 생성**
   - 폼을 통한 데이터 입력
   - POST 요청으로 데이터 추가
   - 성공/실패 피드백

## 🎨 UI 특징

- 반응형 디자인 (모바일 지원)
- 그라디언트 배경과 현대적인 디자인
- 직관적인 사용자 인터페이스
- 한국어 지원

## 🔧 개발 가이드

### 새로운 API 엔드포인트 추가

`backend/server.js` 파일에 새로운 라우트를 추가:

```javascript
app.get('/api/your-endpoint', (req, res) => {
  res.json({ message: 'Your response' });
});
```

### 프론트엔드 기능 추가

`frontend/src/app.js` 파일에 새로운 함수를 추가하고, `index.html`에서 호출:

```javascript
async function yourFunction() {
  const response = await fetch(`${API_URL}/api/your-endpoint`);
  const data = await response.json();
  // 데이터 처리
}
```

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이선스

This project is licensed under the ISC License.

## 📧 문의

프로젝트 관련 문의사항이 있으시면 이슈를 등록해주세요.

---

**Made with ❤️ for the 4th Project**
