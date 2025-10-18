"""
Django용 RAG 시스템 설정
"""

import os
from pathlib import Path

# Django 프로젝트 루트 (elderly_rag_chatbot 폴더)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# 프로젝트 루트 경로 (환경변수로 설정 가능)
PROJECT_ROOT = os.environ.get('PROJECT_ROOT', '')
if PROJECT_ROOT:
    BASE_DIR = Path(PROJECT_ROOT) / 'elderly_rag_chatbot'

# ============== OpenAI 설정 ==============
OPENAI_MODEL = os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')
OPENAI_EMB_MODEL = os.environ.get('OPENAI_EMB_MODEL', 'text-embedding-3-small')
TEMPERATURE = float(os.environ.get('TEMPERATURE', '0.1'))
MAX_TOKENS = int(os.environ.get('MAX_TOKENS', '1000'))

# ============== RAG 설정 ==============
# 기본 청킹: recursive character 방식 권장
CHUNKING_STRATEGY = os.environ.get('CHUNKING_STRATEGY', 'recursive')
CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', '1000'))
CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', '200'))
TOP_K_RESULTS = int(os.environ.get('TOP_K_RESULTS', '5'))
SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', '0.7'))

# ============== 데이터 경로 ==============
# 환경변수에서 경로 읽기 (상대 경로 또는 절대 경로)
def _get_data_path(env_var: str, default_relative_path: str) -> Path:
    """환경변수 또는 기본 경로 반환"""
    env_path = os.environ.get(env_var, '')

    if env_path:
        path = Path(env_path)
        # 상대 경로면 BASE_DIR 기준으로 변환
        if not path.is_absolute():
            path = (BASE_DIR / path).resolve()
        return path
    else:
        # 기본 경로 사용
        return (BASE_DIR.parent / default_relative_path).resolve()

MAIN_DATA_DIR = _get_data_path('MAIN_DATA_DIR', 'data/복지로')
VALIDATION_DATA_DIR = _get_data_path('VALIDATION_DATA_DIR', 'data/복지로 - 복사본')

# ============== ChromaDB 설정 ==============
# ChromaDB 경로도 환경변수로 설정 가능
CHROMA_DB_ROOT_STR = os.environ.get('CHROMA_DB_ROOT', 'chroma_db')
CHROMA_DB_ROOT = BASE_DIR / CHROMA_DB_ROOT_STR

MAIN_CHROMA_DB_STR = os.environ.get('MAIN_CHROMA_DB_DIR', 'chroma_db/main')
MAIN_CHROMA_DB_DIR = BASE_DIR / MAIN_CHROMA_DB_STR

VALIDATION_CHROMA_DB_STR = os.environ.get('VALIDATION_CHROMA_DB_DIR', 'chroma_db/validation')
VALIDATION_CHROMA_DB_DIR = BASE_DIR / VALIDATION_CHROMA_DB_STR

# 디렉토리 생성
for dir_path in [CHROMA_DB_ROOT, MAIN_CHROMA_DB_DIR, VALIDATION_CHROMA_DB_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


def get_openai_api_key():
    """OpenAI API 키 가져오기 - 3가지 위치 확인"""
    # 1. 환경변수에서
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key and api_key != 'your-openai-api-key-here':
        return api_key

    # 2. elderly_rag_chatbot/openaikey.txt
    key_file = BASE_DIR / 'openaikey.txt'
    if key_file.exists():
        try:
            key = key_file.read_text(encoding='utf-8').strip()
            if key and key != 'your-openai-api-key-here':
                return key
        except Exception:
            pass

    # 3. elderly_welfare_rag/elderly_welfare_rag/openaikey.txt
    key_file = BASE_DIR / 'elderly_welfare_rag' / 'elderly_welfare_rag' / 'openaikey.txt'
    if key_file.exists():
        try:
            key = key_file.read_text(encoding='utf-8').strip()
            if key and key != 'your-openai-api-key-here':
                return key
        except Exception:
            pass

    return None
