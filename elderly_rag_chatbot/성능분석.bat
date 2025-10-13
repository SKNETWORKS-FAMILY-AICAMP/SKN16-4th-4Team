@echo off
chcp 65001 >nul
title 📊 RAG 시스템 성능 분석

echo ================================================================
echo            📊 RAG 시스템 성능 분석 도구
echo ================================================================
echo.
echo 🎯 분석할 항목을 선택하세요:
echo   [1] 전체 시스템 상태 확인
echo   [2] 텍스트 추출 성능 분석
echo   [3] HWP 파일 전문 분석
echo   [4] AutoRAG 자동 최적화
echo   [5] 종합 성능 리포트 생성
echo   [6] 시스템 벤치마크
echo.

set /p choice="번호를 선택하세요 (1-6): "

cd /d "%~dp0"

REM Python 환경 확인
if exist "..\venv\Scripts\python.exe" (
    set PYTHON_PATH=..\venv\Scripts\python.exe
) else if exist "venv\Scripts\python.exe" (
    set PYTHON_PATH=venv\Scripts\python.exe
) else (
    set PYTHON_PATH=python
)

if "%choice%"=="1" goto system_status
if "%choice%"=="2" goto text_analysis
if "%choice%"=="3" goto hwp_analysis
if "%choice%"=="4" goto autorag
if "%choice%"=="5" goto comprehensive_report
if "%choice%"=="6" goto benchmark
echo 잘못된 선택입니다.
pause
exit /b

:system_status
echo.
echo 🔍 시스템 상태를 확인합니다...
%PYTHON_PATH% rag_launcher.py
goto end

:text_analysis
echo.
echo 📄 텍스트 추출 성능을 분석합니다...
echo ℹ️ final_analyzer.py 실행 후 메뉴 1번을 선택하세요
%PYTHON_PATH% final_analyzer.py
goto end

:hwp_analysis
echo.
echo 📋 HWP 파일을 전문 분석합니다...
echo ℹ️ final_analyzer.py 실행 후 메뉴 2번을 선택하세요
%PYTHON_PATH% final_analyzer.py
goto end

:autorag
echo.
echo 🤖 AutoRAG 자동 최적화를 시작합니다...
echo ℹ️ final_analyzer.py 실행 후 메뉴 9번을 선택하세요
%PYTHON_PATH% final_analyzer.py
goto end

:comprehensive_report
echo.
echo 📊 종합 성능 리포트를 생성합니다...
echo ℹ️ final_analyzer.py 실행 후 메뉴 10번을 선택하세요
%PYTHON_PATH% final_analyzer.py
goto end

:benchmark
echo.
echo 🏃 시스템 벤치마크를 실행합니다...
echo ℹ️ final_analyzer.py 실행 후 메뉴 4번을 선택하세요
%PYTHON_PATH% final_analyzer.py
goto end

:end
echo.
echo 📊 분석이 완료되었습니다!
echo 📁 결과는 results/ 폴더에 저장됩니다.
echo.
pause