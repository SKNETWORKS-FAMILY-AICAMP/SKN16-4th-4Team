@echo off
REM 간단 Windows 배포 배치파일 (개발/테스트용)
SETLOCAL ENABLEDELAYEDEXPANSION

SET PROJECT_DIR=%~dp0
SET VENV_DIR=%PROJECT_DIR%venv

echo Project dir: %PROJECT_DIR%

if not exist "%VENV_DIR%\Scripts\activate.bat" (
    python -m venv "%VENV_DIR%"
)

call "%VENV_DIR%\Scripts\activate.bat"
pip install --upgrade pip
pip install -r "%PROJECT_DIR%requirements.txt"

echo Running migrations...
set DJANGO_SETTINGS_MODULE=config.django_settings
python manage.py makemigrations --noinput || echo makemigrations failed
python manage.py migrate --noinput
python manage.py collectstatic --noinput
echo Done. For production, configure Gunicorn (WSGI) and Nginx on Linux.
pause
