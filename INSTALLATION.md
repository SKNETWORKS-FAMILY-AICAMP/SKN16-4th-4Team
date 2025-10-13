# 설치 및 실행 가이드

## 빠른 시작

### 1. 가상환경 생성 및 패키지 설치

```bash
cd 팀프로젝트4/4th-project_mvp

# 가상환경이 없다면 생성
python -m venv venv

# 가상환경 활성화 (Windows)
venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt
```

### 2. 관리자 계정 생성

```bash
# admin/admin 계정 자동 생성
python create_admin.py
```

### 3. 데이터베이스 마이그레이션

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. 문서 로드 및 임베딩

```bash
python setup.py
```

OCR 사용 여부를 물으면:
- `y`: 이미지 PDF도 처리 (시간 오래 걸림, Tesseract 설치 필요)
- `n`: 일반 텍스트 PDF만 처리 (빠름)

### 5. 서버 실행

```bash
python manage.py runserver
```

브라우저에서 http://localhost:8000 접속

## 로그인 정보

- **관리자 계정**: admin / admin
- 일반 사용자는 회원가입 필요

## OCR 설정 (선택사항)

이미지 기반 PDF를 처리하려면 Tesseract OCR을 설치해야 합니다:

### Windows
1. https://github.com/UB-Mannheim/tesseract/wiki 에서 설치 파일 다운로드
2. 설치 시 "Additional language data" 에서 Korean 선택
3. 환경 변수 PATH에 Tesseract 경로 추가

### Mac
```bash
brew install tesseract tesseract-lang
```

### Linux
```bash
sudo apt-get install tesseract-ocr tesseract-ocr-kor
```

## 문제 해결

### Port 이미 사용 중
```bash
python manage.py runserver 8001
```

### ChromaDB 오류
```bash
# chroma_db 폴더 삭제 후 다시 setup
rm -rf chroma_db
python setup.py
```

### 마이그레이션 오류
```bash
python manage.py migrate --run-syncdb
```
