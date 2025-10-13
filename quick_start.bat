@echo off
chcp 65001 >nul
echo ====================================
echo 노인 정책 안내 챗봇 빠른 시작
echo ====================================
echo.

cd /d "%~dp0"

echo [단계 1] 데이터베이스 마이그레이션
venv\Scripts\python.exe manage.py migrate
echo.

echo [단계 2] 관리자 계정 확인
venv\Scripts\python.exe create_admin.py
echo.

echo [단계 3] Django 서버 실행
echo.
echo 서버 주소: http://127.0.0.1:8000
echo.
echo 관리자 로그인 정보:
echo   - 아이디: admin
echo   - 비밀번호: admin
echo.
echo 서버 중지: Ctrl+C
echo.
echo ====================================
echo.

venv\Scripts\python.exe manage.py runserver
