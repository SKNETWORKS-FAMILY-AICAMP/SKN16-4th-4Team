@echo off
echo ====================================
echo 노인 정책 안내 챗봇 서버 시작
echo ====================================
echo.

cd /d "%~dp0"

echo [1/3] 가상환경 활성화...
call venv\Scripts\activate.bat

echo [2/3] 마이그레이션 확인...
python manage.py migrate

echo [3/3] Django 서버 실행...
echo.
echo 서버가 시작되면 다음 URL로 접속하세요:
echo http://127.0.0.1:8000
echo.
echo 관리자 로그인:
echo   아이디: admin
echo   비밀번호: admin
echo.
echo 서버를 중지하려면 Ctrl+C를 누르세요.
echo.

python manage.py runserver

pause
