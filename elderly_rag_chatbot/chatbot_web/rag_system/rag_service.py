"""
Django RAG Service
간단한 RAG 서비스 래퍼 - 로컬 모듈 사용
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

# 로컬 rag_system 모듈에서 직접 import
from . import rag_config
from .data_processing import DataProcessor
from .rag_functions import WelfareRAGChain

logger = logging.getLogger(__name__)


class RAGService:
    """RAG 서비스 클래스"""

    def __init__(self, data_dir: Path, chroma_db_dir: Path, is_validation: bool = False):
        self.data_dir = data_dir
        self.chroma_db_dir = chroma_db_dir
        self.is_validation = is_validation
        self.initialized = False
        self.processor = None
        self.rag_chain = None

        # OpenAI API 키 설정
        api_key = rag_config.get_openai_api_key()
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        else:
            logger.warning("⚠️ OpenAI API key not found!")

    def initialize(self):
        """RAG 시스템 초기화"""
        if self.initialized:
            return

        try:
            # 데이터 프로세서 초기화
            logger.info(f"Initializing RAG system with data_dir: {self.data_dir}")

            # DataProcessor 초기화 (data_dir는 "복지로" 폴더 경로, chroma_db_dir는 "chroma_db/main 또는 validation")
            self.processor = DataProcessor(str(self.data_dir), str(self.chroma_db_dir))

            # Vector store와 embedder 가져오기
            vector_store = self.processor.vector_store
            embedder = self.processor.embedder

            if vector_store is None or embedder is None:
                raise ValueError("Vector store or embedder initialization failed")

            # RAG 체인 초기화
            self.rag_chain = WelfareRAGChain(vector_store, embedder)

            # Vector store가 비어있는지 확인
            doc_count = vector_store.get_document_count()
            logger.info(f"Vector store 문서 수: {doc_count}개")

            if doc_count == 0:
                validation_text = "검증용 " if self.is_validation else ""
                logger.warning(f"⚠️ {validation_text}Vector store가 비어있습니다! 데이터베이스를 먼저 구축해주세요.")

            self.initialized = True
            logger.info("✅ RAG system initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize RAG system: {e}")
            raise

    def process_question(self, question: str, history: Optional[List[Dict]] = None, user_region: Optional[str] = None) -> Dict:
        """
        질문 처리

        Args:
            question: 사용자 질문
            history: 대화 기록 (선택)
            user_region: 사용자 지역 (선택)

        Returns:
            {
                "answer": str,
                "sources": list,
                "intent": str
            }
        """
        if not self.initialized:
            try:
                self.initialize()
            except Exception as e:
                logger.error(f"RAG 초기화 실패: {e}", exc_info=True)
                return {
                    "answer": f"죄송합니다. RAG 시스템 초기화에 실패했습니다. 데이터베이스가 구축되어 있는지 확인해주세요.\n오류: {str(e)}",
                    "sources": [],
                    "intent": "error"
                }

        # 초기화 후에도 rag_chain이나 processor가 없으면 오류
        if self.rag_chain is None or self.processor is None:
            logger.error(f"RAG 초기화 실패: rag_chain={self.rag_chain}, processor={self.processor}")
            return {
                "answer": "죄송합니다. RAG 시스템이 제대로 초기화되지 않았습니다. 관리자에게 문의해주세요.",
                "sources": [],
                "intent": "error"
            }

        # Vector store가 비어있는지 확인
        try:
            doc_count = self.processor.vector_store.get_document_count()
        except Exception as e:
            logger.error(f"문서 개수 확인 실패: {e}")
            doc_count = 0

        if doc_count == 0:
            validation_text = "[검증용] " if self.is_validation else ""
            db_type = "--validation" if self.is_validation else ""
            logger.error(f"{validation_text}Vector store가 비어있습니다. 문서 수: 0")
            return {
                "answer": f"""죄송합니다. {validation_text}데이터베이스가 아직 구축되지 않았습니다.

관리자는 다음 명령어로 데이터베이스를 먼저 구축해주세요:

```
python manage.py build_rag_database {db_type}
```

데이터베이스 구축 후 다시 질문해주시면 답변드리겠습니다.""",
                "sources": [],
                "intent": "error"
            }

        try:
            result = self.rag_chain.process_question(question, user_region=user_region)
            return result
        except Exception as e:
            logger.error(f"질문 처리 중 오류: {e}", exc_info=True)
            return {
                "answer": f"죄송합니다. 질문 처리 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "intent": "error"
            }

    def build_database(self, force_rebuild: bool = False):
        """
        데이터베이스 구축 (청킹/임베딩)

        Args:
            force_rebuild: 강제 재구축 여부
        """
        try:
            logger.info(f"Building vector database for {self.data_dir}")

            if force_rebuild:
                # 기존 ChromaDB 삭제
                import shutil
                if self.chroma_db_dir.exists():
                    logger.warning(f"Removing existing database: {self.chroma_db_dir}")
                    shutil.rmtree(self.chroma_db_dir)
                    self.chroma_db_dir.mkdir(parents=True, exist_ok=True)

            # DataProcessor 초기화
            if not self.processor:
                self.processor = DataProcessor(str(self.data_dir), str(self.chroma_db_dir))

            # Vector store 구축
            result = self.processor.build_vector_store()

            logger.info(f"✅ Database build completed: {result}")
            return result

        except Exception as e:
            logger.error(f"❌ Failed to build database: {e}")
            raise


# 글로벌 인스턴스
_main_rag_service = None
_validation_rag_service = None


def get_main_rag_service() -> RAGService:
    """메인 RAG 서비스 인스턴스"""
    global _main_rag_service
    if _main_rag_service is None:
        _main_rag_service = RAGService(
            data_dir=rag_config.MAIN_DATA_DIR,
            chroma_db_dir=rag_config.MAIN_CHROMA_DB_DIR,
            is_validation=False
        )
    return _main_rag_service


def get_validation_rag_service() -> RAGService:
    """검증용 RAG 서비스 인스턴스"""
    global _validation_rag_service
    if _validation_rag_service is None:
        _validation_rag_service = RAGService(
            data_dir=rag_config.VALIDATION_DATA_DIR,
            chroma_db_dir=rag_config.VALIDATION_CHROMA_DB_DIR,
            is_validation=True
        )
    return _validation_rag_service
