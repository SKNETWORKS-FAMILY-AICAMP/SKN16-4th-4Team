# 🚀 Quick Start Guide

4차 프로젝트 MVP를 빠르게 시작하는 방법

## ⚡️ 빠른 시작 (3단계)

### 1단계: 의존성 설치
```bash
cd backend
npm install
```

### 2단계: 백엔드 서버 실행
```bash
npm start
```
서버가 http://localhost:3000 에서 실행됩니다.

### 3단계: 프론트엔드 열기
새 터미널 창을 열고:
```bash
cd frontend/public
python3 -m http.server 8000
# 또는
npx http-server -p 8000
```

브라우저에서 http://localhost:8000 접속

## 🧪 테스트

### API 테스트 (curl 사용)

1. **헬스 체크**
```bash
curl http://localhost:3000/health
```

2. **데이터 조회**
```bash
curl http://localhost:3000/api/data
```

3. **데이터 추가**
```bash
curl -X POST http://localhost:3000/api/data \
  -H "Content-Type: application/json" \
  -d '{"name":"테스트","description":"테스트 데이터입니다"}'
```

## 📋 주요 기능

- ✅ 서버 상태 모니터링
- ✅ 샘플 데이터 조회
- ✅ 새 데이터 추가
- ✅ 실시간 피드백
- ✅ 반응형 UI

## 🔧 포트 변경

백엔드 포트를 변경하려면:
1. `backend/.env.example`을 `backend/.env`로 복사
2. `PORT=3000`을 원하는 포트로 변경
3. `frontend/public/app.js`의 `API_URL`도 함께 변경

## 💡 팁

- 백엔드와 프론트엔드를 동시에 실행해야 정상 작동합니다
- CORS가 활성화되어 있어 다른 포트에서도 접근 가능합니다
- 개발 중에는 브라우저 개발자 도구(F12)를 열어 로그를 확인하세요

## 🐛 문제 해결

**문제: "서버에 연결할 수 없습니다"**
- 백엔드 서버가 실행 중인지 확인
- 포트 3000이 이미 사용 중인지 확인: `lsof -i :3000`

**문제: CORS 오류**
- 백엔드에서 CORS가 활성화되어 있는지 확인
- `backend/package.json`에 `cors` 패키지가 있는지 확인

## 📞 지원

문제가 있으시면 GitHub Issues에 등록해주세요.
