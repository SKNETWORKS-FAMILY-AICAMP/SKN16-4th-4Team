@echo off
chcp 65001 > nul
title � RAG 성능 분석 및 비교평가 시스템

echo ================================================================
echo        � RAG 성능 분석 및 비교평가 시스템
echo ================================================================
echo.
echo � 실행할 분석을 선택하세요:
echo   [1] 통합 런처 (19개 메뉴)
echo   [2] 완전한 분석 시스템 (상세 분석)
echo   [3] 텍스트 추출 성능 비교
echo   [4] AutoRAG 자동 최적화
echo   [5] 커스텀 챗봇 빌더 (서브웨이 스타일)
echo.

set /p choice="번호를 선택하세요 (1-5): "

cd /d "%~dp0"

REM Python 환경 확인
if exist "..\venv\Scripts\python.exe" (
    echo 📦 가상환경을 사용합니다...
    set PYTHON_PATH=..\venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    echo 📦 로컬 가상환경을 사용합니다...
    set PYTHON_PATH=venv\Scripts\python.exe
) else (
    echo 🐍 시스템 Python을 사용합니다...
    set PYTHON_PATH=python
)

echo 🐍 Python 환경: %PYTHON_PATH%
%PYTHON_PATH% --version
echo.

if "%choice%"=="1" goto launcher
if "%choice%"=="2" goto full_analyzer
if "%choice%"=="3" goto text_extraction
if "%choice%"=="4" goto autorag
if "%choice%"=="5" goto custom_builder
echo 잘못된 선택입니다.
pause
exit /b

:launcher
echo ================================================================
echo            🎮 통합 런처 (19개 메뉴 시스템)
echo ================================================================
echo 🚀 모든 기능에 접근할 수 있는 통합 메뉴를 시작합니다...
echo.
%PYTHON_PATH% rag_launcher.py
goto end

:full_analyzer
echo ================================================================
echo           📊 완전한 분석 시스템 (상세 분석)
echo ================================================================
echo 🚀 11개 메뉴 상세 분석 시스템을 시작합니다...
echo 📈 실제 파일 분석, HWP 전문 분석, 성능 리포트 등
echo.
%PYTHON_PATH% final_analyzer.py
goto end

:text_extraction
echo ================================================================
echo          📄 텍스트 추출 성능 비교 분석
echo ================================================================
echo 🚀 final_analyzer.py 메뉴 1번으로 이동합니다...
echo 📊 PyPDF2, pdfplumber, PyMuPDF, pdfminer 성능 비교
echo.
%PYTHON_PATH% final_analyzer.py
goto end

:autorag
echo ================================================================
echo             🤖 AutoRAG 자동 최적화 시스템
echo ================================================================
echo 🚀 final_analyzer.py 메뉴 9번으로 이동합니다...
echo ⚡ 7단계 자동 최적화 프로세스
echo.
%PYTHON_PATH% final_analyzer.py
goto end

:custom_builder
echo ================================================================
echo        🏗️ 커스텀 챗봇 빌더 (서브웨이 스타일)
echo ================================================================
echo 🚀 final_analyzer.py 메뉴 11번으로 이동합니다...
echo 🥪 5단계로 나만의 챗봇을 구성하세요!
echo.
%PYTHON_PATH% final_analyzer.py
goto end

:end
echo.
echo 📊 분석이 완료되었습니다!
echo 📁 결과는 results/ 폴더에 저장됩니다.
echo.
echo 👋 시스템을 종료합니다.
pause