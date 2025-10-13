# 빠른 시작 가이드

## 🚀 1분만에 시작하기

### 방법 1: 배치 파일 실행 (추천)

프로젝트 폴더에서 `quick_start.bat` 더블클릭

```
4th-project_mvp/
└── quick_start.bat  <-- 이 파일을 더블클릭
```

### 방법 2: 명령어로 실행

```bash
# 프로젝트 폴더로 이동
cd 팀프로젝트4\4th-project_mvp

# Django 서버 실행
venv\Scripts\python.exe manage.py runserver
```

## 📱 접속하기

서버가 시작되면 브라우저에서 다음 주소로 접속:

**http://127.0.0.1:8000**

## 🔑 로그인 정보

### 관리자 계정
- **아이디**: `admin`
- **비밀번호**: `admin`

### 일반 사용자
- 회원가입 페이지에서 새 계정 생성

## 📋 주요 기능

### 일반 사용자
1. **회원가입/로그인** - http://127.0.0.1:8000/register/
2. **프로필 설정** - 지역, 나이, 소득수준 등 입력
3. **정책 목록** - http://127.0.0.1:8000/policies/
4. **챗봇 상담** - http://127.0.0.1:8000/chatbot/

### 관리자 (admin으로 로그인 후)
1. **대시보드** - http://127.0.0.1:8000/admin-dashboard/
   - 전체 통계 확인
   - 사용자 활동 모니터링

2. **사용자 관리** - http://127.0.0.1:8000/admin-users/
   - 사용자 목록 조회
   - 관리자 권한 부여/제거

3. **질의응답 로그** - http://127.0.0.1:8000/admin-chats/
   - 모든 채팅 기록 확인
   - 사용자별/날짜별 필터링
   - 응답 품질 평가

4. **문서 관리** - http://127.0.0.1:8000/admin-documents/
   - 새 정책 문서 업로드 (PDF/HWP/HWPX)
   - 기존 문서 삭제
   - ChromaDB 재동기화

## ⚠️ 문제 해결

### Poppler 오류 발생 시

```
OCR 오류: Unable to get page count. Is poppler installed and in PATH?
```

**해결방법**: 
1. Poppler 다운로드: https://github.com/oschwartz10612/poppler-windows/releases/
2. 압축 해제 후 환경변수 PATH에 추가
3. 또는 OCR 없이 문서 로드:
   ```bash
   # setup.py 실행 시 "n" 입력
   venv\Scripts\python.exe setup.py
   ```

### 문서가 로드되지 않은 경우

```bash
# data 폴더의 문서를 ChromaDB에 로드
venv\Scripts\python.exe setup.py

# OCR 사용 여부 물어보면 n 또는 y 입력
# n: OCR 없이 빠르게 로드 (이미지 PDF 제외)
# y: OCR 포함 전체 로드 (시간 오래 걸림, Poppler 필요)
```

### Django 모듈을 찾을 수 없는 경우

```bash
# 패키지 재설치
venv\Scripts\pip.exe install -r requirements.txt
```

## 🛠️ 추가 명령어

### 데이터베이스 초기화
```bash
venv\Scripts\python.exe manage.py migrate
```

### 관리자 계정 재설정
```bash
venv\Scripts\python.exe create_admin.py
```

### 서버 중지
키보드에서 `Ctrl + C` 입력

## 📂 프로젝트 구조

```
4th-project_mvp/
├── quick_start.bat          # 빠른 시작 스크립트
├── run_server.bat            # 서버 실행 스크립트
├── setup.py                  # 문서 초기 로드
├── create_admin.py           # 관리자 생성
├── manage.py                 # Django 관리 명령
├── chatbot/                  # 메인 앱
├── documents/                # 문서 처리 모듈
├── templates/                # HTML 템플릿
├── static/                   # CSS/JS
├── data/                     # 정책 문서 (PDF/HWP)
├── chroma_db/                # 벡터 DB
├── media/                    # 업로드 파일
└── db.sqlite3                # 데이터베이스
```

## 💡 다음 단계

1. **admin/admin**으로 로그인
2. **문서 관리**에서 새 정책 문서 업로드
3. **챗봇**에서 정책 질문
4. **대시보드**에서 통계 확인

## 📞 도움이 필요하신가요?

- 자세한 설치 가이드: `INSTALLATION.md` 참고
- GitHub: https://github.com/yangjiwoo8465/Elderly-Policy-Information-Project-.git
