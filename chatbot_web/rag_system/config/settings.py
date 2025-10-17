"""
노인복지 RAG 시스템 - 설정 파일

시스템 전역 설정과 환경 변수 관리
"""

import os
import logging
from typing import Optional

# 프로젝트 루트 경로
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============== 기본 설정 ==============

# OpenAI 설정
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_EMB_MODEL = "text-embedding-ada-002"
TEMPERATURE = 0.1
MAX_TOKENS = 1000

# 데이터 처리 설정
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 5
SIMILARITY_THRESHOLD = 0.7

# 인터페이스 설정
GRADIO_SERVER_PORT = 7860
SHARE_GRADIO = False

# 로깅 설정
LOG_LEVEL = "INFO"
DEBUG_MODE = False

# 파일 경로
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
EMBEDDING_CACHE_DIR = os.path.join(PROJECT_ROOT, "embeddings_cache")
FEEDBACK_DB_PATH = os.path.join(PROJECT_ROOT, "user_feedback.db")
CHROMA_DB_DIR = os.path.join(PROJECT_ROOT, "chroma_db")

# ============== 환경 변수 관리 ==============

def load_env_file():
    """환경 변수 파일 로드"""
    env_path = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

def get_openai_api_key() -> Optional[str]:
    """OpenAI API 키 획득"""
    # 1. 환경변수에서 확인
    api_key = os.environ.get('OPENAI_API_KEY')
    if api_key and api_key != 'your-openai-api-key-here':
        return api_key
    
    # 2. openaikey.txt 파일에서 확인
    key_file = os.path.join(PROJECT_ROOT, "openaikey.txt")
    if os.path.exists(key_file):
        try:
            with open(key_file, 'r', encoding='utf-8') as f:
                key = f.read().strip()
                if key and key != 'your-openai-api-key-here':
                    return key
        except Exception as e:
            logging.warning(f"openaikey.txt 파일 읽기 실패: {e}")
    
    return None

def setup_environment():
    """환경 설정 초기화"""
    # 환경 변수 파일 로드
    load_env_file()
    
    # 디렉토리 생성
    for dir_path in [LOG_DIR, EMBEDDING_CACHE_DIR, DATA_DIR]:
        os.makedirs(dir_path, exist_ok=True)
    
    # OpenAI API 키 설정
    api_key = get_openai_api_key()
    if api_key:
        os.environ['OPENAI_API_KEY'] = api_key
    
    return api_key is not None

def validate_config():
    """설정 검증"""
    # API 키 확인
    api_key = get_openai_api_key()
    if not api_key:
        logging.warning("⚠️ OpenAI API 키가 설정되지 않음")
        return False
    
    # 데이터 디렉토리 확인
    if not os.path.exists(DATA_DIR):
        logging.error(f"❌ 데이터 디렉토리 없음: {DATA_DIR}")
        return False
    
    welfare_data_dir = os.path.join(DATA_DIR, "복지로")
    if not os.path.exists(welfare_data_dir):
        logging.error(f"❌ 복지 데이터 디렉토리 없음: {welfare_data_dir}")
        return False
    
    logging.info("✅ 설정 검증 완료")
    return True

def print_config():
    """현재 설정 출력"""
    api_key = get_openai_api_key()
    
    print("\n📋 현재 설정:")
    print(f"  🔑 API 키: {'✅ 설정됨' if api_key else '❌ 미설정'}")
    print(f"  🤖 모델: {OPENAI_MODEL}")
    print(f"  📊 임베딩: {OPENAI_EMB_MODEL}")
    print(f"  🌡️ 온도: {TEMPERATURE}")
    print(f"  📄 청크 크기: {CHUNK_SIZE}")
    print(f"  🔍 상위 결과: {TOP_K_RESULTS}")
    print(f"  🌐 포트: {GRADIO_SERVER_PORT}")
    print(f"  📂 데이터: {DATA_DIR}")
    print(f"  📝 로그: {LOG_DIR}")
    print("")

# 환경변수 기반 설정 업데이트
def update_from_env():
    """환경 변수로부터 설정 업데이트"""
    global OPENAI_MODEL, OPENAI_EMB_MODEL, TEMPERATURE, MAX_TOKENS
    global CHUNK_SIZE, CHUNK_OVERLAP, TOP_K_RESULTS, SIMILARITY_THRESHOLD
    global GRADIO_SERVER_PORT, LOG_LEVEL, DEBUG_MODE
    
    # OpenAI 설정
    OPENAI_MODEL = os.environ.get('OPENAI_MODEL', OPENAI_MODEL)
    OPENAI_EMB_MODEL = os.environ.get('EMBEDDING_MODEL', OPENAI_EMB_MODEL)
    TEMPERATURE = float(os.environ.get('TEMPERATURE', TEMPERATURE))
    MAX_TOKENS = int(os.environ.get('MAX_TOKENS', MAX_TOKENS))
    
    # RAG 설정
    CHUNK_SIZE = int(os.environ.get('CHUNK_SIZE', CHUNK_SIZE))
    CHUNK_OVERLAP = int(os.environ.get('CHUNK_OVERLAP', CHUNK_OVERLAP))
    TOP_K_RESULTS = int(os.environ.get('TOP_K_RESULTS', TOP_K_RESULTS))
    SIMILARITY_THRESHOLD = float(os.environ.get('SIMILARITY_THRESHOLD', SIMILARITY_THRESHOLD))
    
    # 인터페이스 설정
    GRADIO_SERVER_PORT = int(os.environ.get('GRADIO_SERVER_PORT', GRADIO_SERVER_PORT))
    
    # 로깅 설정
    LOG_LEVEL = os.environ.get('LOG_LEVEL', LOG_LEVEL)
    DEBUG_MODE = os.environ.get('DEBUG_MODE', 'False').lower() == 'true'

# 초기화시 환경변수 적용
update_from_env()