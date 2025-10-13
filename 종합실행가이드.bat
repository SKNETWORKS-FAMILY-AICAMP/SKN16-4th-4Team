@echo off
chcp 65001 >nul
title 🚀 노인 복지 정책 RAG 챗봇 시스템 - 종합 가이드

echo ================================================================
echo    🏥 노인 복지 정책 RAG 챗봇 시스템 - 종합 실행 가이드
echo ================================================================
echo.
echo 🎯 어떤 기능을 사용하시겠습니까?
echo.
echo ┌─ 💬 챗봇 사용 ────────────────────────────────────────┐
echo │ [1] Django 웹 채팅 (브라우저에서 사용)                │
echo │ [2] 콘솔 챗봇 (터미널에서 바로 채팅)                   │
echo └─────────────────────────────────────────────────────┘
echo.
echo ┌─ 🏗️ 커스텀 챗봇 만들기 ──────────────────────────────┐
echo │ [3] 서브웨이 스타일 챗봇 빌더 (5단계 구성)             │
echo │ [4] 성능 분석 및 최적화                               │
echo └─────────────────────────────────────────────────────┘
echo.
echo ┌─ 🎮 고급 제어 시스템 ─────────────────────────────────┐
echo │ [5] 통합 제어 런처 (19개 메뉴)                        │
echo │ [6] 마스터 리모컨 (직접 제어)                          │
echo └─────────────────────────────────────────────────────┘
echo.
echo ┌─ 📊 분석 및 진단 ─────────────────────────────────────┐
echo │ [7] 시스템 상태 확인                                  │
echo │ [8] 성능 분석 도구                                    │
echo └─────────────────────────────────────────────────────┘
echo.
echo   [9] 도움말 (README 가이드 열기)
echo   [0] 종료
echo.

set /p choice="번호를 선택하세요 (0-9): "

cd /d "%~dp0"

if "%choice%"=="1" goto django_web
if "%choice%"=="2" goto console_chatbot
if "%choice%"=="3" goto custom_builder
if "%choice%"=="4" goto performance_analysis
if "%choice%"=="5" goto integrated_launcher
if "%choice%"=="6" goto master_remote
if "%choice%"=="7" goto system_status
if "%choice%"=="8" goto performance_tools
if "%choice%"=="9" goto help_guide
if "%choice%"=="0" goto exit_program
echo 잘못된 선택입니다.
pause
goto start

:django_web
echo.
echo ================================================================
echo              🌐 Django 웹 채팅 시작
echo ================================================================
call run_server.bat
goto end

:console_chatbot
echo.
echo ================================================================
echo              💬 콘솔 챗봇 실행
echo ================================================================
cd elderly_rag_chatbot
call 챗봇실행.bat
goto end

:custom_builder
echo.
echo ================================================================
echo           🏗️ 서브웨이 스타일 챗봇 빌더
echo ================================================================
cd elderly_rag_chatbot
call 커스텀빌더.bat
goto end

:performance_analysis
echo.
echo ================================================================
echo             📈 성능 분석 및 최적화
echo ================================================================
cd elderly_rag_chatbot
call 성능분석.bat
goto end

:integrated_launcher
echo.
echo ================================================================
echo            🎮 통합 제어 런처 (19개 메뉴)
echo ================================================================
cd elderly_rag_chatbot
call run_comparison.bat
goto end

:master_remote
echo.
echo ================================================================
echo             🎮 마스터 리모컨 (직접 제어)
echo ================================================================
cd elderly_rag_chatbot
if exist "..\venv\Scripts\python.exe" (
    ..\venv\Scripts\python.exe rag_remote_control.py
) else (
    python rag_remote_control.py
)
goto end

:system_status
echo.
echo ================================================================
echo              🔍 시스템 상태 확인
echo ================================================================
cd elderly_rag_chatbot
if exist "..\venv\Scripts\python.exe" (
    echo 🐍 Python 환경: 가상환경
    ..\venv\Scripts\python.exe --version
    echo.
    echo 🚀 통합 런처에서 "18. 시스템 상태"를 선택하세요
    ..\venv\Scripts\python.exe rag_launcher.py
) else (
    echo 🐍 Python 환경: 시스템 Python
    python --version
    echo.
    echo 🚀 통합 런처에서 "18. 시스템 상태"를 선택하세요
    python rag_launcher.py
)
goto end

:performance_tools
echo.
echo ================================================================
echo              📊 성능 분석 도구
echo ================================================================
cd elderly_rag_chatbot
call 성능분석.bat
goto end

:help_guide
echo.
echo ================================================================
echo              📚 도움말 가이드
echo ================================================================
echo.
echo 📖 상세한 사용법은 다음 문서들을 참고하세요:
echo.
echo 🔥 완전 가이드: elderly_rag_chatbot\README_완전가이드.md
echo 📋 프로젝트 개요: README.md
echo 🚀 빠른 시작: QUICK_START.md
echo.
echo 💡 주요 파일들:
echo   - 챗봇실행.bat: 바로 채팅 시작
echo   - 커스텀빌더.bat: 나만의 챗봇 만들기
echo   - 성능분석.bat: 시스템 성능 확인
echo   - run_server.bat: 웹 서비스 시작
echo.
echo 🌐 웹에서 README 보기 (메모장으로 열기):
if exist "elderly_rag_chatbot\README_완전가이드.md" (
    notepad elderly_rag_chatbot\README_완전가이드.md
) else (
    notepad README.md
)
goto end

:exit_program
echo.
echo 👋 시스템을 종료합니다.
exit /b

:end
echo.
echo 🔄 메인 메뉴로 돌아가려면 아무 키나 누르세요...
pause >nul
cls
goto start

:start
cls
echo ================================================================
echo    🏥 노인 복지 정책 RAG 챗봇 시스템 - 종합 실행 가이드
echo ================================================================
echo.
echo 🎯 어떤 기능을 사용하시겠습니까?
echo.
echo ┌─ 💬 챗봇 사용 ────────────────────────────────────────┐
echo │ [1] Django 웹 채팅 (브라우저에서 사용)                │
echo │ [2] 콘솔 챗봇 (터미널에서 바로 채팅)                   │
echo └─────────────────────────────────────────────────────┘
echo.
echo ┌─ 🏗️ 커스텀 챗봇 만들기 ──────────────────────────────┐
echo │ [3] 서브웨이 스타일 챗봇 빌더 (5단계 구성)             │
echo │ [4] 성능 분석 및 최적화                               │
echo └─────────────────────────────────────────────────────┘
echo.
echo ┌─ 🎮 고급 제어 시스템 ─────────────────────────────────┐
echo │ [5] 통합 제어 런처 (19개 메뉴)                        │
echo │ [6] 마스터 리모컨 (직접 제어)                          │
echo └─────────────────────────────────────────────────────┘
echo.
echo ┌─ 📊 분석 및 진단 ─────────────────────────────────────┐
echo │ [7] 시스템 상태 확인                                  │
echo │ [8] 성능 분석 도구                                    │
echo └─────────────────────────────────────────────────────┘
echo.
echo   [9] 도움말 (README 가이드 열기)
echo   [0] 종료
echo.

set /p choice="번호를 선택하세요 (0-9): "