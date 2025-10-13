@echo off
chcp 65001 >nul
echo ================================================================
echo     🏥 노인 복지 정책 RAG 챗봇 시스템 - 빠른 시작
echo ================================================================
echo.
echo 🎯 선택하세요:
echo   [1] Django 웹 서버 시작 (웹 인터페이스)
echo   [2] RAG 챗봇 직접 실행 (콘솔 챗봇)
echo   [3] 통합 제어 시스템 (리모컨 런처)
echo   [4] 커스텀 챗봇 빌더 (서브웨이 스타일)
echo.

set /p choice="번호를 선택하세요 (1-4): "

cd /d "%~dp0"

if "%choice%"=="1" goto django_server
if "%choice%"=="2" goto rag_chatbot
if "%choice%"=="3" goto control_system
if "%choice%"=="4" goto custom_builder
echo 잘못된 선택입니다.
pause
exit /b

:django_server
echo.
echo ================================================================
echo             🌐 Django 웹 서버 시작
echo ================================================================
echo [1/3] 데이터베이스 마이그레이션...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe manage.py migrate
) else (
    python manage.py migrate
)

echo [2/3] 관리자 계정 확인...
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe create_admin.py
) else (
    python create_admin.py
)

echo [3/3] Django 서버 실행...
echo.
echo 🌐 웹 브라우저에서 접속: http://127.0.0.1:8000
echo 👤 관리자 로그인: admin / admin
echo 🛑 서버 중지: Ctrl+C
echo.

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe manage.py runserver
) else (
    python manage.py runserver
)
goto end

:rag_chatbot
echo.
echo ================================================================
echo               🤖 RAG 챗봇 직접 실행
echo ================================================================
cd elderly_rag_chatbot
echo 🚀 스마트 커스텀 챗봇 시작...
echo 💬 복지 정책 질문을 입력하세요!
echo.
if exist "..\venv\Scripts\python.exe" (
    ..\venv\Scripts\python.exe smart_custom_chatbot.py
) else (
    python smart_custom_chatbot.py
)
goto end

:control_system
echo.
echo ================================================================
echo            🎮 통합 제어 시스템 (리모컨 런처)
echo ================================================================
cd elderly_rag_chatbot
echo 🚀 19개 메뉴 통합 런처 시작...
echo.
if exist "..\venv\Scripts\python.exe" (
    ..\venv\Scripts\python.exe rag_launcher.py
) else (
    python rag_launcher.py
)
goto end

:custom_builder
echo.
echo ================================================================
echo         🏗️ 커스텀 챗봇 빌더 (서브웨이 스타일)
echo ================================================================
cd elderly_rag_chatbot
echo 🏗️ 5단계 커스텀 챗봇 빌더 시작...
echo 🥪 서브웨이처럼 챗봇을 구성해보세요!
echo.
if exist "..\venv\Scripts\python.exe" (
    ..\venv\Scripts\python.exe final_analyzer.py
) else (
    python final_analyzer.py
)
goto end

:end
echo.
echo 👋 시스템을 종료합니다.
pause
