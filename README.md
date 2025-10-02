# 4th-project_mvp

4차 프로젝트를 위한 MVP (Minimum Viable Product) 개발 저장소입니다.

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
