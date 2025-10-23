"""
Django RAG Wrapper
elderly_welfare_rag의 RAG 시스템을 Django에서 사용하기 위한 래퍼
"""

import os
import sys
from pathlib import Path

# Add elderly_welfare_rag to path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ELDERLY_RAG_PATH = BASE_DIR / 'elderly_welfare_rag' / 'elderly_welfare_rag'
sys.path.insert(0, str(ELDERLY_RAG_PATH))

from src.rag_functions import WelfareRAGChain
from src.data_processing import DataProcessor


class DjangoRAGSystem:
    """Django용 RAG 시스템"""
    
    def __init__(self, data_path: str, is_validation: bool = False):
        """
        Args:
            data_path: 데이터 폴더 경로
            is_validation: 검증용 여부
        """
        self.data_path = data_path
        self.is_validation = is_validation
        self.processor = None
        self.rag_chain = None
        self._initialized = False
    
    def initialize(self):
        """RAG 시스템 초기화"""
        if self._initialized:
            return
        
        # 데이터 프로세서 초기화
        self.processor = DataProcessor(self.data_path)
        
        # Vector store와 embedder 가져오기
        vector_store = self.processor.get_vector_store()
        embedder = self.processor.get_embedder()
        
        # RAG 체인 초기화
        self.rag_chain = WelfareRAGChain(vector_store, embedder)
        
        self._initialized = True
    
    def process_question(self, question: str, conversation_history: list = None) -> dict:
        """
        질문 처리
        
        Args:
            question: 사용자 질문
            conversation_history: 대화 기록 리스트 [{"role": "user", "content": "..."}, ...]
        
        Returns:
            {"answer": str, "sources": list, "intent": str}
        """
        if not self._initialized:
            self.initialize()
        
        return self.rag_chain.process_question(question)
    
    def build_vector_store(self):
        """Vector store 구축 (데이터 청킹/임베딩)"""
        if not self.processor:
            self.processor = DataProcessor(self.data_path)
        
        return self.processor.build_vector_store()


# 글로벌 인스턴스
_main_rag_system = None
_validation_rag_system = None


def get_main_rag_system():
    """메인 RAG 시스템 가져오기"""
    global _main_rag_system
    if _main_rag_system is None:
        data_path = str(BASE_DIR.parent / 'data' / '복지로')
        _main_rag_system = DjangoRAGSystem(data_path, is_validation=False)
    return _main_rag_system


def get_validation_rag_system():
    """검증용 RAG 시스템 가져오기"""
    global _validation_rag_system
    if _validation_rag_system is None:
        data_path = str(BASE_DIR.parent / 'data' / '복지로 - 복사본')
        _validation_rag_system = DjangoRAGSystem(data_path, is_validation=True)
    return _validation_rag_system
