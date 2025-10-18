# 📋 완전 배포 가이드 (Complete Deployment Guide)

이 가이드는 AWS Lightsail Ubuntu 24 서버에서 elderly_rag_chatbot을 완전히 자동 설치하는 방법을 설명합니다.

## 🚀 빠른 시작 (MobaXterm 사용)

### 1단계: 서버 접속 및 프로젝트 다운로드
```bash
# SSH로 서버 접속 (MobaXterm)
ssh ubuntu@YOUR_SERVER_IP

# 프로젝트 클론
git clone https://github.com/SKNETWORKS-FAMILY-AICAMP/SKN16-4th-4Team.git
cd SKN16-4th-4Team/elderly_rag_chatbot
```

### 2단계: 환경 설정 파일 생성
```bash
# .env 파일 생성 (예시에서 복사)
cp .env.example .env

# 실제 값으로 편집 (nano 또는 vi 사용)
nano .env
```

**필수 편집 항목:**
- `SECRET_KEY`: 자동 생성됨 (또는 수동으로 안전한 키 입력)
- `DATABASE_URL`: PostgreSQL 연결 문자열
- `OPENAI_API_KEY`: OpenAI API 키
- `DOMAIN`: 실제 도메인명 (예: example.com)
- `POSTGRES_PASSWORD`: 강력한 비밀번호

### 3단계: 자동 배포 실행

#### A. 완전 새로 설치 (처음 배포)
```bash
# 비대화형 전체 설치 (PostgreSQL 포함)
sudo AUTO_CONFIRM=true REMOVE_VENV=true POSTGRES_INSTALL=true \
  POSTGRES_DB=elderly_rag POSTGRES_USER=rag_user POSTGRES_PASSWORD='YourStrongPassword!' \
  DOMAIN=yourdomain.com bash full_setup.sh
```

#### B. 코드 업데이트만 (재배포)
```bash
# 코드 업데이트 후 빠른 재배포
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate --noinput
python manage.py collectstatic --noinput
sudo systemctl restart elderly_rag_gunicorn
sudo systemctl restart nginx
```

### 4단계: 서비스 상태 확인
```bash
# 서비스 상태 확인
sudo systemctl status elderly_rag_gunicorn --no-pager
sudo systemctl status nginx --no-pager

# 로그 확인 (문제 발생 시)
sudo journalctl -u elderly_rag_gunicorn -f

# 웹 접속 테스트
curl -I http://localhost/
```

## 🔧 문제 해결

### .env 파일 문법 에러
```bash
# 자동 복구 스크립트 실행
bash fix_env.sh

# 또는 수동 복구
cp .env.example .env
nano .env  # 실제 값 입력
```

### 의존성 설치 실패 (numpy/chroma-hnswlib 빌드 에러)
```bash
# venv 재생성 및 바이너리 우선 설치
rm -rf venv
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
pip install --prefer-binary numpy
pip install -r requirements.txt
```

### 서비스 시작 실패
```bash
# 상세 로그 확인
sudo journalctl -xeu elderly_rag_gunicorn -n 200 --no-pager

# 수동 테스트
cd /path/to/elderly_rag_chatbot
source venv/bin/activate
export DJANGO_SETTINGS_MODULE=config.django_settings
python manage.py check
python manage.py runserver 0.0.0.0:8000
```

## 📁 프로젝트 구조 이해

```
elderly_rag_chatbot/
├── manage.py                    # Django 관리 스크립트
├── config/                      # Django 설정
│   ├── django_settings.py      # 메인 설정 파일
│   ├── urls.py                  # URL 라우팅
│   └── wsgi.py                  # WSGI 애플리케이션
├── chatbot_web/                 # 메인 Django 앱
│   ├── models.py               # 데이터베이스 모델
│   ├── views.py                # 뷰 함수
│   ├── urls.py                 # 앱 URL 패턴
│   └── rag_system/             # RAG 시스템
├── templates/                   # HTML 템플릿
├── static/                      # 정적 파일
├── .env.example                # 환경변수 예시
├── requirements.txt            # Python 의존성
├── full_setup.sh              # 완전 자동 설치
├── deploy_ubuntu24.sh         # Ubuntu 배포 스크립트
└── fix_env.sh                 # .env 복구 스크립트
```

## 🔐 보안 고려사항

1. **SECRET_KEY**: 프로덕션에서는 반드시 안전한 키 사용
2. **DEBUG**: 프로덕션에서는 반드시 `False`
3. **ALLOWED_HOSTS**: 실제 도메인만 허용
4. **데이터베이스**: 강력한 비밀번호 사용
5. **HTTPS**: Let's Encrypt로 SSL 인증서 설정

## 🌐 HTTPS 설정 (선택사항)

```bash
# 도메인 설정 후 SSL 인증서 발급
sudo certbot --nginx -d yourdomain.com

# 자동 갱신 테스트
sudo certbot renew --dry-run
```

## 🔄 정기 유지보수

### 일일 체크
```bash
# 서비스 상태 확인
sudo systemctl status elderly_rag_gunicorn nginx

# 디스크 사용량 확인
df -h

# 로그 크기 확인
sudo du -sh /var/log/
```

### 주간 체크
```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 백업 확인
ls -la *.bak.*

# SSL 인증서 상태 확인 (HTTPS 사용 시)
sudo certbot certificates
```

## 📞 지원 및 문의

- 프로젝트 이슈: GitHub Issues
- 기술 문서: `README.md`, `INSTALLATION_GUIDE.md`
- 배포 문제: `DEPLOYMENT_README.md` 참조

---

**💡 팁**: 이 가이드의 모든 명령어는 Ubuntu 24 LTS 기준으로 작성되었습니다. 다른 OS에서는 일부 명령어나 경로가 다를 수 있습니다.