"""
검색 전략 모듈
=============

다양한 검색 전략을 구현하고 비교하는 모듈
"""

import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class BaseRetrievalStrategy(ABC):
    """검색 전략 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def retrieve(self, query: str, documents: List[Dict], k: int = 5) -> List[Dict]:
        """문서 검색 추상 메소드"""
        pass


class SimilarityRetrievalStrategy(BaseRetrievalStrategy):
    """유사도 기반 검색 전략"""
    
    def __init__(self):
        super().__init__("similarity")
    
    def retrieve(self, query: str, documents: List[Dict], k: int = 5) -> List[Dict]:
        """유사도 기반 문서 검색"""
        try:
            # 더미 구현 - 실제로는 임베딩 유사도 계산
            logger.info(f"유사도 검색: {query[:50]}...")
            
            # 랜덤 점수로 문서 정렬 (더미)
            scored_docs = []
            for i, doc in enumerate(documents[:k*2]):  # k의 2배만큼 고려
                score = np.random.uniform(0.3, 1.0)
                scored_docs.append({
                    **doc,
                    'retrieval_score': score,
                    'retrieval_method': 'similarity'
                })
            
            # 점수순 정렬 후 상위 k개 반환
            scored_docs.sort(key=lambda x: x['retrieval_score'], reverse=True)
            return scored_docs[:k]
            
        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            return []


class MMRRetrievalStrategy(BaseRetrievalStrategy):
    """MMR (Maximal Marginal Relevance) 검색 전략"""
    
    def __init__(self):
        super().__init__("mmr")
    
    def retrieve(self, query: str, documents: List[Dict], k: int = 5) -> List[Dict]:
        """MMR 기반 문서 검색"""
        try:
            logger.info(f"MMR 검색: {query[:50]}...")
            
            # 더미 구현 - 실제로는 다양성을 고려한 선택
            scored_docs = []
            for i, doc in enumerate(documents[:k*2]):
                relevance_score = np.random.uniform(0.4, 1.0)
                diversity_score = np.random.uniform(0.2, 0.8)
                # MMR 점수 = λ * relevance + (1-λ) * diversity
                mmr_score = 0.7 * relevance_score + 0.3 * diversity_score
                
                scored_docs.append({
                    **doc,
                    'retrieval_score': mmr_score,
                    'relevance_score': relevance_score,
                    'diversity_score': diversity_score,
                    'retrieval_method': 'mmr'
                })
            
            scored_docs.sort(key=lambda x: x['retrieval_score'], reverse=True)
            return scored_docs[:k]
            
        except Exception as e:
            logger.error(f"MMR 검색 실패: {e}")
            return []


class DiversityRetrievalStrategy(BaseRetrievalStrategy):
    """다양성 기반 검색 전략"""
    
    def __init__(self):
        super().__init__("diversity")
    
    def retrieve(self, query: str, documents: List[Dict], k: int = 5) -> List[Dict]:
        """다양성 기반 문서 검색"""
        try:
            logger.info(f"다양성 검색: {query[:50]}...")
            
            # 더미 구현 - 실제로는 클러스터링 등을 통한 다양성 확보
            scored_docs = []
            for i, doc in enumerate(documents[:k*2]):
                diversity_score = np.random.uniform(0.3, 1.0)
                scored_docs.append({
                    **doc,
                    'retrieval_score': diversity_score,
                    'retrieval_method': 'diversity'
                })
            
            scored_docs.sort(key=lambda x: x['retrieval_score'], reverse=True)
            return scored_docs[:k]
            
        except Exception as e:
            logger.error(f"다양성 검색 실패: {e}")
            return []


class RetrievalStrategyManager:
    """검색 전략 관리 클래스"""
    
    def __init__(self):
        """검색 전략 관리자 초기화"""
        self.strategies = {
            'similarity': SimilarityRetrievalStrategy(),
            'mmr': MMRRetrievalStrategy(),
            'diversity': DiversityRetrievalStrategy()
        }
        logger.info("검색 전략 관리자 초기화 완료")
    
    def retrieve(self, query: str, documents: List[Dict], strategy: str = "similarity", k: int = 5) -> List[Dict]:
        """
        지정된 전략으로 문서 검색
        
        Args:
            query: 검색 쿼리
            documents: 검색할 문서 목록
            strategy: 검색 전략 ('similarity', 'mmr', 'diversity')
            k: 반환할 문서 수
            
        Returns:
            List[Dict]: 검색된 문서 목록
        """
        try:
            if strategy not in self.strategies:
                logger.warning(f"알 수 없는 검색 전략: {strategy}, 기본값 사용")
                strategy = 'similarity'
            
            strategy_obj = self.strategies[strategy]
            return strategy_obj.retrieve(query, documents, k)
            
        except Exception as e:
            logger.error(f"문서 검색 실패 ({strategy}): {e}")
            return []
    
    def get_available_strategies(self) -> List[str]:
        """사용 가능한 검색 전략 목록 반환"""
        return list(self.strategies.keys())
    
    def evaluate_strategy_performance(self, query: str, documents: List[Dict], strategy: str, k: int = 5) -> Dict[str, Any]:
        """
        특정 검색 전략의 성능 평가
        
        Args:
            query: 평가 쿼리
            documents: 문서 목록
            strategy: 검색 전략
            k: 검색할 문서 수
            
        Returns:
            Dict[str, Any]: 성능 평가 결과
        """
        try:
            start_time = time.time()
            
            # 검색 실행
            results = self.retrieve(query, documents, strategy, k)
            
            processing_time = time.time() - start_time
            
            # 성능 지표 계산
            return {
                'strategy': strategy,
                'retrieved_count': len(results),
                'requested_count': k,
                'processing_time': processing_time,
                'avg_score': np.mean([r.get('retrieval_score', 0) for r in results]) if results else 0,
                'success': len(results) > 0,
                'coverage_ratio': len(results) / k if k > 0 else 0
            }
            
        except Exception as e:
            return {
                'strategy': strategy,
                'retrieved_count': 0,
                'requested_count': k,
                'processing_time': 0,
                'avg_score': 0,
                'success': False,
                'coverage_ratio': 0,
                'error': str(e)
            }


def main():
    """테스트 실행 함수"""
    print("🔍 검색 전략 테스트")
    print("="*30)
    
    # 샘플 문서
    documents = [
        {'id': 1, 'content': '노인복지법에 따른 의료비 지원', 'source': 'doc1.pdf'},
        {'id': 2, 'content': '장애인 복지 서비스 신청 방법', 'source': 'doc2.pdf'},
        {'id': 3, 'content': '저소득층 주거 지원 정책', 'source': 'doc3.pdf'},
        {'id': 4, 'content': '기초생활수급자 혜택 안내', 'source': 'doc4.pdf'},
        {'id': 5, 'content': '독거노인 돌봄 서비스', 'source': 'doc5.pdf'}
    ]
    
    manager = RetrievalStrategyManager()
    test_query = "노인 의료비 지원에 대해 알려주세요"
    
    print(f"🔍 테스트 쿼리: {test_query}")
    print(f"📄 문서 수: {len(documents)}")
    
    # 각 전략 테스트
    for strategy in manager.get_available_strategies():
        print(f"\n[{strategy.upper()} 전략]")
        
        # 성능 평가
        performance = manager.evaluate_strategy_performance(test_query, documents, strategy)
        
        if performance['success']:
            print(f"  ✅ 검색 성공: {performance['retrieved_count']}개 문서")
            print(f"  ⏱️ 처리 시간: {performance['processing_time']:.3f}초")
            print(f"  📊 평균 점수: {performance['avg_score']:.3f}")
            
            # 검색 결과
            results = manager.retrieve(test_query, documents, strategy, k=3)
            for i, doc in enumerate(results, 1):
                score = doc.get('retrieval_score', 0)
                print(f"    {i}. {doc['content'][:30]}... (점수: {score:.3f})")
        else:
            print(f"  ❌ 검색 실패: {performance.get('error', '알 수 없는 오류')}")


if __name__ == "__main__":
    main()