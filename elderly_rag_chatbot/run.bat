@echo off
chcp 65001 >nul
echo ================================================================
echo          🤖 RAG 챗봇 시스템 - 직접 실행 모드
echo ================================================================
echo.
echo 🎯 실행할 모드를 선택하세요:
echo   [1] 스마트 커스텀 챗봇 (가드 기능 포함)
echo   [2] 통합 제어 시스템 (리모컨 런처)
echo   [3] 완전한 분석 시스템 (커스텀 빌더 포함)
echo   [4] 마스터 리모컨 (직접 제어)
echo.

set /p choice="번호를 선택하세요 (1-4): "

cd /d "%~dp0"

REM Python 환경 확인
if exist "..\venv\Scripts\python.exe" (
    echo 🐍 가상환경을 사용합니다...
    set PYTHON_PATH=..\venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    echo 🐍 로컬 가상환경을 사용합니다...
    set PYTHON_PATH=venv\Scripts\python.exe
) else (
    echo 🐍 시스템 Python을 사용합니다...
    set PYTHON_PATH=python
)

if "%choice%"=="1" goto smart_chatbot
if "%choice%"=="2" goto launcher
if "%choice%"=="3" goto analyzer
if "%choice%"=="4" goto remote_control
echo 잘못된 선택입니다.
pause
exit /b

:smart_chatbot
echo.
echo ================================================================
echo              🤖 스마트 커스텀 챗봇 실행
echo ================================================================
echo 🚀 가드 기능이 포함된 메인 챗봇을 시작합니다...
echo 💬 복지 정책에 대해 질문해보세요!
echo 🛡️ 무관한 질문은 자동으로 필터링됩니다
echo.
%PYTHON_PATH% smart_custom_chatbot.py
goto end

:launcher
echo.
echo ================================================================
echo            🎮 통합 제어 시스템 (리모컨 런처)
echo ================================================================
echo 🚀 19개 메뉴 통합 런처를 시작합니다...
echo.
%PYTHON_PATH% rag_launcher.py
goto end

:analyzer
echo.
echo ================================================================
echo         📊 완전한 분석 시스템 (커스텀 빌더 포함)
echo ================================================================
echo 🚀 상세 분석 및 커스텀 챗봇 빌더를 시작합니다...
echo 🏗️ 11번 메뉴에서 서브웨이 스타일 챗봇을 만들 수 있습니다!
echo.
%PYTHON_PATH% final_analyzer.py
goto end

:remote_control
echo.
echo ================================================================
echo              🎮 마스터 리모컨 (직접 제어)
echo ================================================================
echo 🚀 RAG 시스템 마스터 리모컨을 시작합니다...
echo.
%PYTHON_PATH% rag_remote_control.py
goto end

:end
echo.
echo 👋 시스템을 종료합니다.
pause
echo   --rebuild : 벡터 데이터베이스 재구성
echo   --interface streamlit : Streamlit 인터페이스 사용
echo   --port 8080 : 사용자 지정 포트
echo.

%PYTHON_PATH% main.py %*

if %errorlevel% neq 0 (
    echo.
    echo ❌ 시스템 실행에 실패했습니다.
    echo 다음을 확인해주세요:
    echo 1. Python이 설치되어 있는지 확인
    echo 2. 필요한 패키지가 설치되어 있는지 확인: pip install -r requirements.txt
    echo 3. 데이터 디렉토리가 존재하는지 확인: data/복지로/
    echo 4. OpenAI API 키가 설정되어 있는지 확인 (선택사항)
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 시스템이 정상적으로 종료되었습니다.
pause