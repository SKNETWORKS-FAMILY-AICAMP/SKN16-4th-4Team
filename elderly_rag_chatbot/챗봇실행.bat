@echo off
chcp 65001 >nul
title 🤖 스마트 복지 정책 챗봇

echo ================================================================
echo          🤖 스마트 복지 정책 챗봇 - 바로 시작
echo ================================================================
echo.
echo 💬 복지 정책에 대해 궁금한 점을 질문해보세요!
echo 🛡️ 무관한 질문은 자동으로 필터링됩니다
echo.
echo 📝 질문 예시:
echo   - "65세 이상 기초연금이 궁금해요"
echo   - "장애인 활동지원 서비스는 어떻게 신청하나요?"
echo   - "저소득층 의료비 지원 조건을 알려주세요"
echo.
echo 🛑 종료하려면 'quit' 또는 'exit'를 입력하세요
echo.

cd /d "%~dp0"

REM Python 환경 확인
if exist "..\venv\Scripts\python.exe" (
    echo 🐍 가상환경 사용 중...
    ..\venv\Scripts\python.exe smart_custom_chatbot.py
) else if exist "venv\Scripts\python.exe" (
    echo 🐍 로컬 가상환경 사용 중...
    venv\Scripts\python.exe smart_custom_chatbot.py
) else (
    echo 🐍 시스템 Python 사용 중...
    python smart_custom_chatbot.py
)

echo.
echo 👋 챗봇을 종료합니다.
pause