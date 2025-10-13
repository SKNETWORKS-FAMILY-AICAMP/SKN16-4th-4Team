@echo off
chcp 65001 >nul
title 🏗️ 서브웨이 스타일 커스텀 챗봇 빌더

echo ================================================================
echo      🏗️ 서브웨이 스타일 커스텀 챗봇 빌더
echo ================================================================
echo.
echo 🥪 서브웨이처럼 5단계로 나만의 챗봇을 만들어보세요!
echo.
echo 🍞 1단계: 빵 선택 (텍스트 추출 방법)
echo    - PyPDF2, pdfplumber, PyMuPDF 중 선택
echo.
echo 🧀 2단계: 치즈 선택 (청킹 전략)
echo    - recursive, fixed_size, semantic 중 선택
echo.
echo 🥬 3단계: 야채 선택 (임베딩 모델)
echo    - sentence-transformers, openai 중 선택
echo.
echo 🥄 4단계: 소스 선택 (검색 전략)
echo    - similarity, mmr, diversity 중 선택
echo.
echo 🍟 5단계: 사이드 선택 (기타 옵션)
echo    - 성능 최적화, 로깅 등
echo.

cd /d "%~dp0"

REM Python 환경 확인
if exist "..\venv\Scripts\python.exe" (
    echo 🐍 가상환경 사용 중...
    ..\venv\Scripts\python.exe final_analyzer.py
) else if exist "venv\Scripts\python.exe" (
    echo 🐍 로컬 가상환경 사용 중...
    venv\Scripts\python.exe final_analyzer.py
) else (
    echo 🐍 시스템 Python 사용 중...
    python final_analyzer.py
)

echo.
echo 💾 구성이 config/ 폴더에 저장되었습니다!
echo 👋 커스텀 빌더를 종료합니다.
pause