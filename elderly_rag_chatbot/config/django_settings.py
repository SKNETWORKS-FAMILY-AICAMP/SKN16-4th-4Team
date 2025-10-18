"""
Django settings for elderly_rag_chatbot project.
"""

import os
from pathlib import Path

# Load environment variables from .env file
from dotenv import load_dotenv

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file
env_file = BASE_DIR / '.env'
if env_file.exists():
    load_dotenv(env_file)
else:
    # Try loading from default location (if running from different directory)
    load_dotenv()

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-elderly-rag-chatbot-development-key-change-in-production'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True').lower() in ('true', '1', 'yes', 'on')

# ALLOWED_HOSTS - 콤마로 구분된 호스트 리스트
ALLOWED_HOSTS_STR = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1')
ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',') if host.strip()]
if not ALLOWED_HOSTS or DEBUG:
    ALLOWED_HOSTS.append('*')  # DEBUG 모드에서는 모든 호스트 허용

# ngrok 도메인 허용
ALLOWED_HOSTS.append('.ngrok-free.app')
ALLOWED_HOSTS.append('.ngrok-free.dev')
ALLOWED_HOSTS.append('.ngrok.io')

# CSRF 신뢰할 수 있는 출처 설정 (ngrok 도메인 포함)
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'https://*.ngrok-free.app',
    'https://*.ngrok-free.dev',
    'https://*.ngrok.io',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'chatbot_web',  # Our RAG chatbot app
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database
import dj_database_url

# DATABASE 설정: 기본 sqlite 사용, 환경변수로 POSTGRES 또는 DATABASE_URL 설정 가능
DATABASE_URL = os.getenv('DATABASE_URL')
POSTGRES_DB = os.getenv('POSTGRES_DB')
POSTGRES_USER = os.getenv('POSTGRES_USER')
POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD')
POSTGRES_HOST = os.getenv('POSTGRES_HOST')
POSTGRES_PORT = os.getenv('POSTGRES_PORT')

if DATABASE_URL:
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
elif POSTGRES_DB and POSTGRES_USER and POSTGRES_PASSWORD:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': POSTGRES_DB,
            'USER': POSTGRES_USER,
            'PASSWORD': POSTGRES_PASSWORD,
            'HOST': POSTGRES_HOST or 'localhost',
            'PORT': POSTGRES_PORT or '5432',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'ko-kr'
TIME_ZONE = 'Asia/Seoul'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Login URLs
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/login/'

# Session
SESSION_COOKIE_AGE = 3600 * 24  # 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# OpenAI API Key (optional)
# OpenAI 임베딩 모델을 사용하려면 아래에 API 키를 입력하세요.
# 방법 1: 직접 입력 (개발용)
#   OPENAI_API_KEY = 'sk-proj-your-key-here'
# 방법 2: 환경변수 사용 (프로덕션 권장)
#   set OPENAI_API_KEY=sk-proj-your-key-here
# 또는 무료인 SentenceTransformer 모델을 사용하세요 (KoSRoBERTa 권장)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# RAG System Settings
RAG_DATA_DIR = BASE_DIR.parent / 'data'
RAG_CHROMA_DB_DIR = BASE_DIR / 'chroma_db'
RAG_CACHE_DIR = BASE_DIR / 'cache'

# Create necessary directories
os.makedirs(RAG_DATA_DIR, exist_ok=True)
os.makedirs(RAG_CHROMA_DB_DIR, exist_ok=True)
os.makedirs(RAG_CACHE_DIR, exist_ok=True)
os.makedirs(BASE_DIR / 'static', exist_ok=True)
os.makedirs(BASE_DIR / 'templates', exist_ok=True)
