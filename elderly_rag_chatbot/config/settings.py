# =========================================
# ⚙️ 시스템 설정 파일
# =========================================

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

# 환경 변수 기반 설정
def get_env_or_default(key: str, default: Any = None) -> str:
    """환경 변수 값 가져오기 (기본값 포함)"""
    return os.getenv(key, default)


@dataclass
class EmbeddingConfig:
    """임베딩 모델 설정"""
    
    # OpenAI 설정
    openai_api_key: str = field(default_factory=lambda: get_env_or_default("OPENAI_API_KEY", ""))
    openai_model: str = "text-embedding-ada-002"
    openai_timeout: int = 30
    
    # SentenceTransformer 설정
    sentence_transformer_models: List[str] = field(default_factory=lambda: [
        "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
        "jhgan/ko-sroberta-multitask",
        "snunlp/KR-SBERT-V40K-klueNLI-augSTS"
    ])
    
    # KoBERT 설정
    kobert_model: str = "skt/kobert-base-v1"
    
    # 기본 임베딩 모델
    default_model: str = "sentence_transformer"
    
    # 차원 설정
    embedding_dimensions: Dict[str, int] = field(default_factory=lambda: {
        "openai": 1536,
        "sentence_transformer": 384,
        "kobert": 768
    })


@dataclass
class VectorStoreConfig:
    """벡터 저장소 설정"""
    
    # ChromaDB 설정
    persist_directory: str = "./data/chroma_db"
    collection_name: str = "elderly_welfare_policies"
    
    # 검색 설정
    similarity_top_k: int = 5
    similarity_threshold: float = 0.7
    
    # 메타데이터 필터
    enable_metadata_filter: bool = True
    default_filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkingConfig:
    """문서 청킹 설정"""
    
    # 기본 청킹 설정
    default_strategy: str = "recursive"
    chunk_size: int = 1000
    chunk_overlap: int = 200
    
    # 전략별 설정
    recursive_separators: List[str] = field(default_factory=lambda: ["\n\n", "\n", ". ", " ", ""])
    
    # 의미 기반 청킹
    semantic_threshold: float = 0.75
    semantic_min_chunk_size: int = 300
    
    # 문단 기반 청킹
    paragraph_min_length: int = 100


@dataclass
class RetrieverConfig:
    """검색기 설정"""
    
    # 키워드 검색
    keyword_analyzer: str = "korean"
    keyword_top_k: int = 5
    
    # 의미 검색
    semantic_top_k: int = 5
    semantic_score_threshold: float = 0.7
    
    # 하이브리드 검색
    hybrid_alpha: float = 0.5  # 키워드:의미 비율
    hybrid_top_k: int = 10
    
    # 재순위화
    enable_reranking: bool = True
    rerank_top_k: int = 3


@dataclass
class RAGConfig:
    """RAG 시스템 설정"""
    
    # 언어 모델 설정
    llm_provider: str = "openai"  # "openai", "huggingface", "local"
    llm_model: str = "gpt-3.5-turbo"
    llm_temperature: float = 0.1
    llm_max_tokens: int = 1000
    
    # 대화 메모리
    memory_type: str = "buffer_window"  # "buffer", "buffer_window", "summary"
    memory_k: int = 10
    
    # 컨텍스트 설정
    max_context_length: int = 4000
    context_overlap: int = 200
    
    # 답변 품질 제어
    min_confidence_threshold: float = 0.6
    enable_source_citation: bool = True
    max_sources: int = 5


@dataclass
class WorkflowConfig:
    """LangGraph 워크플로우 설정"""
    
    # 의도 분류
    enable_intent_classification: bool = True
    intent_confidence_threshold: float = 0.8
    
    # 관련성 평가
    enable_relevance_evaluation: bool = True
    relevance_threshold: float = 0.7
    
    # 후속 질문 생성
    enable_followup_generation: bool = True
    max_followup_questions: int = 3
    
    # 워크플로우 단계별 설정
    max_retries: int = 2
    timeout_seconds: int = 30


@dataclass
class InterfaceConfig:
    """인터페이스 설정"""
    
    # Gradio 설정
    gradio_server_name: str = "0.0.0.0"
    gradio_server_port: int = 7860
    gradio_share: bool = False
    gradio_debug: bool = False
    
    # Streamlit 설정
    streamlit_port: int = 8501
    
    # 대화 설정
    max_conversation_history: int = 20
    enable_conversation_export: bool = True
    
    # 피드백 설정
    enable_user_feedback: bool = True
    feedback_scale: tuple = (1, 5)


@dataclass
class DataConfig:
    """데이터 설정"""
    
    # 문서 경로
    data_directory: str = "./data/복지로"
    supported_formats: List[str] = field(default_factory=lambda: [".pdf", ".hwp", ".txt"])
    
    # 전처리 설정
    enable_preprocessing: bool = True
    remove_special_chars: bool = True
    normalize_spacing: bool = True
    
    # 캐시 설정
    enable_document_cache: bool = True
    cache_directory: str = "./cache"
    cache_ttl_hours: int = 24


@dataclass
class EvaluationConfig:
    """평가 설정"""
    
    # 자동 평가
    enable_auto_evaluation: bool = True
    evaluation_metrics: List[str] = field(default_factory=lambda: [
        "relevance", "faithfulness", "answer_correctness", "context_precision"
    ])
    
    # 성능 모니터링
    enable_performance_monitoring: bool = True
    log_response_times: bool = True
    
    # 사용자 만족도
    target_satisfaction_score: float = 4.0
    min_feedback_count: int = 10


@dataclass
class LoggingConfig:
    """로깅 설정"""
    
    # 로그 레벨
    log_level: str = "INFO"
    
    # 로그 파일
    log_directory: str = "./logs"
    log_file_name: str = "elderly_rag_chatbot.log"
    max_log_file_size: int = 10_000_000  # 10MB
    backup_count: int = 5
    
    # 로그 포맷
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    
    # 특별 로깅
    log_user_interactions: bool = True
    log_system_errors: bool = True
    log_performance_metrics: bool = True


class SystemSettings:
    """전체 시스템 설정 관리"""
    
    def __init__(self):
        """설정 초기화"""
        
        # 각 모듈별 설정
        self.embedding = EmbeddingConfig()
        self.vector_store = VectorStoreConfig()
        self.chunking = ChunkingConfig()
        self.retriever = RetrieverConfig()
        self.rag = RAGConfig()
        self.workflow = WorkflowConfig()
        self.interface = InterfaceConfig()
        self.data = DataConfig()
        self.evaluation = EvaluationConfig()
        self.logging = LoggingConfig()
        
        # 환경별 설정 적용
        self._apply_environment_settings()
    
    def _apply_environment_settings(self):
        """환경 변수 기반 설정 적용"""
        
        # 개발/운영 환경 구분
        env = get_env_or_default("ELDERLY_RAG_ENV", "development")
        
        if env == "production":
            # 운영 환경 설정
            self.rag.llm_temperature = 0.0
            self.interface.gradio_debug = False
            self.logging.log_level = "WARNING"
            
        elif env == "development":
            # 개발 환경 설정
            self.interface.gradio_debug = True
            self.logging.log_level = "DEBUG"
            
        # API 키 설정
        if self.embedding.openai_api_key:
            self.rag.llm_provider = "openai"
        
        # 디렉토리 생성
        self._ensure_directories()
    
    def _ensure_directories(self):
        """필요한 디렉토리 생성"""
        
        directories = [
            self.vector_store.persist_directory,
            self.data.cache_directory,
            self.logging.log_directory
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)
    
    def get_config_dict(self) -> Dict[str, Any]:
        """설정을 딕셔너리로 반환"""
        
        return {
            "embedding": self.embedding.__dict__,
            "vector_store": self.vector_store.__dict__,
            "chunking": self.chunking.__dict__,
            "retriever": self.retriever.__dict__,
            "rag": self.rag.__dict__,
            "workflow": self.workflow.__dict__,
            "interface": self.interface.__dict__,
            "data": self.data.__dict__,
            "evaluation": self.evaluation.__dict__,
            "logging": self.logging.__dict__
        }
    
    def update_config(self, config_dict: Dict[str, Any]):
        """설정 업데이트"""
        
        for section, settings in config_dict.items():
            if hasattr(self, section):
                config_obj = getattr(self, section)
                for key, value in settings.items():
                    if hasattr(config_obj, key):
                        setattr(config_obj, key, value)
    
    def save_config(self, file_path: str = "config/settings.json"):
        """설정을 파일로 저장"""
        
        import json
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.get_config_dict(), f, ensure_ascii=False, indent=2)
    
    def load_config(self, file_path: str = "config/settings.json"):
        """파일에서 설정 로드"""
        
        import json
        
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                config_dict = json.load(f)
                self.update_config(config_dict)


# 전역 설정 인스턴스
settings = SystemSettings()


# 환경 변수 템플릿 (예시)
ENV_TEMPLATE = """
# =========================================
# 환경 변수 설정 예시 (.env 파일)
# =========================================

# 실행 환경
ELDERLY_RAG_ENV=development

# OpenAI API 키
OPENAI_API_KEY=your_openai_api_key_here

# 데이터 디렉토리
DATA_DIRECTORY=./data/복지로

# 로그 레벨
LOG_LEVEL=INFO

# 인터페이스 설정
GRADIO_PORT=7860
STREAMLIT_PORT=8501

# 데이터베이스 설정
CHROMA_PERSIST_DIR=./data/chroma_db
"""


def main():
    """설정 파일 테스트"""
    
    print("⚙️ 시스템 설정 테스트")
    print("=" * 50)
    
    # 설정 인스턴스 생성
    config = SystemSettings()
    
    # 설정 출력
    print("임베딩 설정:")
    print(f"  기본 모델: {config.embedding.default_model}")
    print(f"  OpenAI 모델: {config.embedding.openai_model}")
    
    print(f"\nRAG 설정:")
    print(f"  LLM 모델: {config.rag.llm_model}")
    print(f"  온도: {config.rag.llm_temperature}")
    print(f"  최대 토큰: {config.rag.llm_max_tokens}")
    
    print(f"\n인터페이스 설정:")
    print(f"  Gradio 포트: {config.interface.gradio_server_port}")
    print(f"  대화 기록 최대 수: {config.interface.max_conversation_history}")
    
    # 설정 저장 테스트
    try:
        config.save_config("config/test_settings.json")
        print(f"\n✅ 설정 파일 저장 성공")
    except Exception as e:
        print(f"\n❌ 설정 파일 저장 실패: {e}")
    
    # 환경 변수 템플릿 출력
    print(f"\n📄 환경 변수 템플릿:")
    print(ENV_TEMPLATE)


if __name__ == "__main__":
    main()