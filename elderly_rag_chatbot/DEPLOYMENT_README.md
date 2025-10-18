배포 가이드 (간단)

1) 환경 설정
 - .env 파일을 프로젝트 루트에 복사
   cp .env.example .env
 - .env에서 POSTGRES_* 값을 설정하거나 DATABASE_URL을 설정
 - DEBUG=False로 설정 권장

2) 의존성 설치
 - Linux: ./deploy_linux.sh
 - Windows: deploy.bat

3) 서비스 시작 (Linux)
 - sudo systemctl start elderly_rag_gunicorn
 - sudo systemctl status elderly_rag_gunicorn
 - nginx 설정을 /etc/nginx/sites-available/에 복사 후 링크 생성

4) 주의사항
 - SECRET_KEY와 API 키를 반드시 설정하세요
 - DB 마이그레이션 및 collectstatic을 확인하세요

5) 마이그레이션 및 테스트
 - 가상환경 활성화 후:
   python manage.py makemigrations
   python manage.py migrate
 - 관리자 계정 생성:
   python manage.py createsuperuser
 - 서버 로컬 실행 확인:
   python manage.py runserver

== AWS Lightsail (Ubuntu 24) 배포 안내 ==

1) 인스턴스 생성
 - OS: Ubuntu 24
 - 메모리: 최소 2GB 권장(벡터 DB/임베딩 모델 사용 시 더 필요할 수 있음)

2) 네트워크 설정
 - Lightsail 콘솔에서 인스턴스의 네트워킹 탭에서 HTTP(80), HTTPS(443), SSH(22)를 허용

3) 서버에서 실행
 - 프로젝트를 서버에 업로드 (git clone 또는 scp)
 - 서버에 접속 후 프로젝트 디렉토리로 이동
 - 실행:
   sudo bash deploy_ubuntu24.sh

4) 도메인/SSL
 - 도메인이 있으면 `sudo certbot --nginx -d your_domain`로 HTTPS 설정

5) PostgreSQL
 - deploy_ubuntu24.sh에서 Postgres 설치 및 DB 생성 옵션 제공
 - 또는 외부 RDS/Postgres를 사용하려면 `.env`에 `DATABASE_URL`을 설정하세요

6) Troubleshooting
 - systemd 서비스 로그: sudo journalctl -u elderly_rag_gunicorn -f
 - nginx 로그: /var/log/nginx/error.log
