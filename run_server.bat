@echo off
chcp 65001 >nul
echo ================================================================
echo       🌐 노인 복지 정책 RAG 챗봇 - Django 웹 서버
echo ================================================================
echo.

cd /d "%~dp0"

echo 🔍 Python 환경 확인...
if exist "venv\Scripts\python.exe" (
    echo ✅ 가상환경을 사용합니다 (venv)
    set PYTHON_CMD=venv\Scripts\python.exe
) else (
    echo ⚠️  시스템 Python을 사용합니다
    set PYTHON_CMD=python
)

echo.
echo [1/4] 의존성 패키지 확인...
%PYTHON_CMD% -c "import django; print('Django 버전:', django.get_version())"

echo.
echo [2/4] 데이터베이스 마이그레이션...
%PYTHON_CMD% manage.py migrate

echo.
echo [3/4] 관리자 계정 생성/확인...
%PYTHON_CMD% create_admin.py

echo.
echo [4/4] Django 웹 서버 실행...
echo.
echo ================================================================
echo   🌐 웹 브라우저에서 다음 주소로 접속하세요:
echo      http://127.0.0.1:8000
echo.
echo   👤 관리자 페이지: http://127.0.0.1:8000/admin
echo      아이디: admin
echo      비밀번호: admin
echo.
echo   💬 챗봇 페이지: http://127.0.0.1:8000/chatbot
echo.
echo   🛑 서버 중지: Ctrl+C 를 누르세요
echo ================================================================
echo.

%PYTHON_CMD% manage.py runserver

echo.
echo 👋 Django 서버가 종료되었습니다.
pause
