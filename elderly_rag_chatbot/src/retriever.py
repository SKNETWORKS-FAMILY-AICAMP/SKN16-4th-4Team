# =========================================
# 🔍 리트리버 구성 모듈
# =========================================

import os
import logging
import numpy as np
from typing import List, Dict, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd

# LangChain 임포트
try:
    from langchain.schema import Document
    from langchain.schema.retriever import BaseRetriever
    from langchain.callbacks.manager import CallbackManagerForRetrieverRun
    from langchain_community.retrievers import BM25Retriever
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    # LangChain 없이도 기본 기능 구현
    class Document:
        def __init__(self, page_content: str, metadata: Dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}

logger = logging.getLogger(__name__)


class BaseWelfareRetriever(ABC):
    """복지 정책 리트리버 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.documents = []
        self.is_initialized = False
    
    @abstractmethod
    def add_documents(self, documents: List[Document]) -> None:
        """문서 추가"""
        pass
    
    @abstractmethod
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        """쿼리에 대한 관련 문서 검색"""
        pass
    
    def get_retriever_info(self) -> Dict[str, Any]:
        """리트리버 정보 반환"""
        return {
            'name': self.name,
            'document_count': len(self.documents),
            'is_initialized': self.is_initialized
        }


class KeywordRetriever(BaseWelfareRetriever):
    """키워드 기반 리트리버 (TF-IDF + BM25)"""
    
    def __init__(self, use_bm25: bool = True):
        super().__init__("keyword_retriever")
        self.use_bm25 = use_bm25
        self.tfidf_vectorizer = None
        self.tfidf_matrix = None
        self.bm25_retriever = None
        
        # 노인복지 전용 키워드 가중치
        self.welfare_keywords = {
            "노인": 2.0, "어르신": 2.0, "고령자": 2.0,
            "복지": 1.8, "지원": 1.8, "혜택": 1.5,
            "의료비": 1.7, "간병": 1.6, "요양": 1.6, "돌봄": 1.6,
            "생활지원": 1.5, "수당": 1.4, "연금": 1.4,
            "신청": 1.3, "대상": 1.3, "자격": 1.3, "조건": 1.3
        }
    
    def add_documents(self, documents: List[Document]) -> None:
        """문서 추가 및 인덱싱"""
        self.documents = documents
        texts = [doc.page_content for doc in documents]
        
        # TF-IDF 벡터화
        self.tfidf_vectorizer = TfidfVectorizer(
            stop_words=None,  # 한국어 불용어는 별도 처리
            ngram_range=(1, 2),  # 1-2gram
            max_features=10000,
            token_pattern=r'[가-힣]+|[a-zA-Z]+|\d+'  # 한글, 영어, 숫자
        )
        
        try:
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(texts)
            logger.info(f"TF-IDF 매트릭스 생성 완료: {self.tfidf_matrix.shape}")
        except Exception as e:
            logger.error(f"TF-IDF 벡터화 실패: {e}")
            raise
        
        # BM25 리트리버 (LangChain 사용 가능 시)
        if self.use_bm25 and LANGCHAIN_AVAILABLE:
            try:
                self.bm25_retriever = BM25Retriever.from_documents(documents)
                self.bm25_retriever.k = 5
                logger.info("BM25 리트리버 초기화 완료")
            except Exception as e:
                logger.warning(f"BM25 리트리버 초기화 실패, TF-IDF만 사용: {e}")
                self.use_bm25 = False
        
        self.is_initialized = True
        logger.info(f"키워드 리트리버 초기화 완료: {len(documents)}개 문서")
    
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        """키워드 기반 문서 검색"""
        if not self.is_initialized:
            logger.error("리트리버가 초기화되지 않았습니다.")
            return []
        
        results = []
        
        # BM25 검색 (가능한 경우)
        if self.use_bm25 and self.bm25_retriever:
            try:
                bm25_docs = self.bm25_retriever.get_relevant_documents(query)
                bm25_scores = self._calculate_keyword_boost(query, bm25_docs)
                
                for doc, score in zip(bm25_docs[:k], bm25_scores):
                    doc.metadata['retriever_type'] = 'bm25'
                    doc.metadata['score'] = score
                    results.append(doc)
                
            except Exception as e:
                logger.warning(f"BM25 검색 실패: {e}")
        
        # TF-IDF 검색 (보완 또는 메인)
        if not results or len(results) < k:
            tfidf_docs = self._tfidf_search(query, k)
            
            # BM25 결과와 중복 제거
            existing_contents = {doc.page_content for doc in results}
            
            for doc in tfidf_docs:
                if doc.page_content not in existing_contents and len(results) < k:
                    doc.metadata['retriever_type'] = 'tfidf'
                    results.append(doc)
        
        return results[:k]
    
    def _tfidf_search(self, query: str, k: int) -> List[Document]:
        """TF-IDF 기반 검색"""
        try:
            # 쿼리 벡터화
            query_vector = self.tfidf_vectorizer.transform([query])
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_vector, self.tfidf_matrix)[0]
            
            # 키워드 가중치 적용
            boosted_similarities = self._apply_keyword_boost(query, similarities)
            
            # 상위 k개 선택
            top_indices = np.argsort(boosted_similarities)[::-1][:k]
            
            results = []
            for idx in top_indices:
                doc = self.documents[idx]
                # 메타데이터에 점수 추가
                doc.metadata = doc.metadata.copy()  # 원본 변경 방지
                doc.metadata['tfidf_score'] = float(similarities[idx])
                doc.metadata['boosted_score'] = float(boosted_similarities[idx])
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"TF-IDF 검색 실패: {e}")
            return []
    
    def _apply_keyword_boost(self, query: str, similarities: np.ndarray) -> np.ndarray:
        """복지 키워드 가중치 적용"""
        boosted_similarities = similarities.copy()
        
        # 쿼리에서 복지 키워드 찾기
        query_keywords = [kw for kw in self.welfare_keywords.keys() if kw in query]
        
        if not query_keywords:
            return boosted_similarities
        
        # 각 문서에서 키워드 매칭 확인하여 가중치 적용
        for i, doc in enumerate(self.documents):
            boost_factor = 1.0
            
            for keyword in query_keywords:
                if keyword in doc.page_content:
                    boost_factor *= self.welfare_keywords[keyword]
            
            if boost_factor > 1.0:
                boosted_similarities[i] *= min(boost_factor, 3.0)  # 최대 3배까지 증폭
        
        return boosted_similarities
    
    def _calculate_keyword_boost(self, query: str, documents: List[Document]) -> List[float]:
        """BM25 결과에 대한 키워드 가중치 계산"""
        scores = []
        query_keywords = [kw for kw in self.welfare_keywords.keys() if kw in query]
        
        for doc in documents:
            boost_factor = 1.0
            
            for keyword in query_keywords:
                if keyword in doc.page_content:
                    boost_factor *= self.welfare_keywords[keyword]
            
            scores.append(min(boost_factor, 3.0))
        
        return scores


class SemanticRetriever(BaseWelfareRetriever):
    """의미 기반 리트리버 (임베딩 벡터 유사도)"""
    
    def __init__(self, embedding_function, vector_store=None):
        super().__init__("semantic_retriever")
        self.embedding_function = embedding_function
        self.vector_store = vector_store
        self.document_embeddings = None
    
    def add_documents(self, documents: List[Document]) -> None:
        """문서 추가 및 임베딩 생성"""
        self.documents = documents
        
        # 벡터스토어가 있으면 사용, 없으면 직접 임베딩
        if self.vector_store:
            # 벡터스토어에 문서 추가
            texts = [doc.page_content for doc in documents]
            metadatas = [doc.metadata for doc in documents]
            self.vector_store.add_documents(texts, metadatas)
            logger.info(f"벡터스토어에 {len(documents)}개 문서 추가")
        else:
            # 직접 임베딩 생성
            try:
                texts = [doc.page_content for doc in documents]
                
                if hasattr(self.embedding_function, 'embed_documents'):
                    # LangChain 스타일
                    self.document_embeddings = self.embedding_function.embed_documents(texts)
                else:
                    # 커스텀 임베딩 함수
                    self.document_embeddings = [
                        self.embedding_function.embed_texts([text])[0] 
                        for text in texts
                    ]
                
                self.document_embeddings = np.array(self.document_embeddings)
                logger.info(f"문서 임베딩 생성 완료: {self.document_embeddings.shape}")
                
            except Exception as e:
                logger.error(f"문서 임베딩 생성 실패: {e}")
                raise
        
        self.is_initialized = True
    
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        """의미 기반 문서 검색"""
        if not self.is_initialized:
            logger.error("리트리버가 초기화되지 않았습니다.")
            return []
        
        if self.vector_store:
            # 벡터스토어 사용
            return self._vector_store_search(query, k)
        else:
            # 직접 임베딩 비교
            return self._embedding_search(query, k)
    
    def _vector_store_search(self, query: str, k: int) -> List[Document]:
        """벡터스토어를 이용한 검색"""
        try:
            results = self.vector_store.similarity_search(query, k)
            
            # Document 객체로 변환
            documents = []
            for result in results:
                doc = Document(
                    page_content=result['document'],
                    metadata={
                        **result['metadata'],
                        'retriever_type': 'semantic_vectorstore',
                        'similarity_score': result['similarity_score']
                    }
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"벡터스토어 검색 실패: {e}")
            return []
    
    def _embedding_search(self, query: str, k: int) -> List[Document]:
        """임베딩 유사도 기반 검색"""
        try:
            # 쿼리 임베딩 생성
            if hasattr(self.embedding_function, 'embed_query'):
                query_embedding = self.embedding_function.embed_query(query)
            else:
                query_embedding = self.embedding_function.embed_texts([query])[0]
            
            query_embedding = np.array(query_embedding).reshape(1, -1)
            
            # 코사인 유사도 계산
            similarities = cosine_similarity(query_embedding, self.document_embeddings)[0]
            
            # 의미적 유사도 향상을 위한 후처리
            enhanced_similarities = self._enhance_semantic_similarity(query, similarities)
            
            # 상위 k개 선택
            top_indices = np.argsort(enhanced_similarities)[::-1][:k]
            
            results = []
            for idx in top_indices:
                doc = self.documents[idx]
                doc.metadata = doc.metadata.copy()
                doc.metadata.update({
                    'retriever_type': 'semantic_embedding',
                    'similarity_score': float(similarities[idx]),
                    'enhanced_score': float(enhanced_similarities[idx])
                })
                results.append(doc)
            
            return results
            
        except Exception as e:
            logger.error(f"임베딩 검색 실패: {e}")
            return []
    
    def _enhance_semantic_similarity(self, query: str, similarities: np.ndarray) -> np.ndarray:
        """의미적 유사도 향상 (복지 정책 특화)"""
        enhanced = similarities.copy()
        
        # 쿼리와 문서의 의미적 관련성 분석
        query_lower = query.lower()
        
        # 의료 관련 질의 처리
        if any(word in query_lower for word in ['의료', '치료', '병원', '약', '수술']):
            for i, doc in enumerate(self.documents):
                if any(word in doc.page_content for word in ['의료비', '진료', '치료비', '약값']):
                    enhanced[i] *= 1.3
        
        # 돌봄 관련 질의 처리
        if any(word in query_lower for word in ['돌봄', '간병', '요양', '케어']):
            for i, doc in enumerate(self.documents):
                if any(word in doc.page_content for word in ['돌봄서비스', '요양보호사', '간병인']):
                    enhanced[i] *= 1.3
        
        # 경제적 지원 관련 질의 처리
        if any(word in query_lower for word in ['지원금', '수당', '보조금', '생활비']):
            for i, doc in enumerate(self.documents):
                if any(word in doc.page_content for word in ['지원', '수당', '급여', '보조금']):
                    enhanced[i] *= 1.2
        
        return enhanced


class HybridRetriever(BaseWelfareRetriever):
    """하이브리드 리트리버 (키워드 + 의미 기반 결합)"""
    
    def __init__(self, 
                 keyword_retriever: KeywordRetriever,
                 semantic_retriever: SemanticRetriever,
                 keyword_weight: float = 0.3,
                 semantic_weight: float = 0.7):
        super().__init__("hybrid_retriever")
        self.keyword_retriever = keyword_retriever
        self.semantic_retriever = semantic_retriever
        self.keyword_weight = keyword_weight
        self.semantic_weight = semantic_weight
        
        # 가중치 정규화
        total_weight = keyword_weight + semantic_weight
        self.keyword_weight /= total_weight
        self.semantic_weight /= total_weight
    
    def add_documents(self, documents: List[Document]) -> None:
        """두 리트리버에 문서 추가"""
        self.documents = documents
        
        self.keyword_retriever.add_documents(documents)
        self.semantic_retriever.add_documents(documents)
        
        self.is_initialized = True
        logger.info(f"하이브리드 리트리버 초기화 완료: {len(documents)}개 문서")
    
    def retrieve(self, query: str, k: int = 5) -> List[Document]:
        """하이브리드 검색 (키워드 + 의미 기반 결합)"""
        if not self.is_initialized:
            logger.error("리트리버가 초기화되지 않았습니다.")
            return []
        
        # 각 리트리버에서 더 많은 결과 가져오기
        expanded_k = min(k * 2, len(self.documents))
        
        keyword_results = self.keyword_retriever.retrieve(query, expanded_k)
        semantic_results = self.semantic_retriever.retrieve(query, expanded_k)
        
        # 점수 정규화 및 결합
        combined_scores = self._combine_results(keyword_results, semantic_results, query)
        
        # 상위 k개 선택
        sorted_results = sorted(combined_scores.items(), key=lambda x: x[1], reverse=True)
        
        final_results = []
        for doc_content, score in sorted_results[:k]:
            # 원본 문서 찾기
            for doc in self.documents:
                if doc.page_content == doc_content:
                    result_doc = Document(
                        page_content=doc.page_content,
                        metadata={
                            **doc.metadata,
                            'retriever_type': 'hybrid',
                            'combined_score': score,
                            'keyword_weight': self.keyword_weight,
                            'semantic_weight': self.semantic_weight
                        }
                    )
                    final_results.append(result_doc)
                    break
        
        return final_results
    
    def _combine_results(self, 
                        keyword_results: List[Document], 
                        semantic_results: List[Document],
                        query: str) -> Dict[str, float]:
        """키워드와 의미 기반 결과 결합"""
        combined_scores = {}
        
        # 키워드 리트리버 결과 처리
        for doc in keyword_results:
            content = doc.page_content
            
            # 키워드 점수 추출 (여러 가능한 키 확인)
            keyword_score = 0.0
            for key in ['boosted_score', 'score', 'tfidf_score']:
                if key in doc.metadata:
                    keyword_score = float(doc.metadata[key])
                    break
            
            combined_scores[content] = keyword_score * self.keyword_weight
        
        # 의미 기반 리트리버 결과 처리
        for doc in semantic_results:
            content = doc.page_content
            
            # 의미 점수 추출
            semantic_score = 0.0
            for key in ['enhanced_score', 'similarity_score', 'score']:
                if key in doc.metadata:
                    semantic_score = float(doc.metadata[key])
                    break
            
            if content in combined_scores:
                combined_scores[content] += semantic_score * self.semantic_weight
            else:
                combined_scores[content] = semantic_score * self.semantic_weight
        
        return combined_scores


class RetrieverComparator:
    """리트리버 성능 비교 및 평가 클래스"""
    
    def __init__(self):
        self.retrievers = {}
        self.test_queries = [
            "65세 이상 노인 의료비 지원 방법",
            "치매 어르신 돌봄 서비스",
            "기초생활수급자 생활비 지원",
            "노인 요양보호사 신청 절차",
            "고령자 교통비 할인 혜택"
        ]
    
    def register_retriever(self, name: str, retriever: BaseWelfareRetriever):
        """리트리버 등록"""
        self.retrievers[name] = retriever
        logger.info(f"리트리버 등록: {name}")
    
    def compare_retrievers(self, 
                          test_documents: List[Document],
                          custom_queries: List[str] = None) -> pd.DataFrame:
        """리트리버 성능 비교"""
        
        queries = custom_queries or self.test_queries
        results = []
        
        for name, retriever in self.retrievers.items():
            logger.info(f"리트리버 테스트: {name}")
            
            try:
                # 문서 추가
                retriever.add_documents(test_documents)
                
                # 각 쿼리에 대한 성능 측정
                query_results = []
                
                for query in queries:
                    retrieved_docs = retriever.retrieve(query, k=5)
                    
                    # 관련성 점수 계산 (단순 키워드 매칭 기반)
                    relevance_score = self._calculate_relevance(query, retrieved_docs)
                    query_results.append(relevance_score)
                
                # 평균 성능 계산
                avg_relevance = np.mean(query_results)
                
                result = {
                    'retriever': name,
                    'avg_relevance': round(avg_relevance, 3),
                    'document_count': len(test_documents),
                    'test_queries': len(queries),
                    'retriever_info': retriever.get_retriever_info()
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"{name} 테스트 실패: {e}")
                continue
        
        df = pd.DataFrame(results)
        return df.sort_values('avg_relevance', ascending=False) if not df.empty else df
    
    def _calculate_relevance(self, query: str, retrieved_docs: List[Document]) -> float:
        """관련성 점수 계산 (단순 키워드 기반)"""
        if not retrieved_docs:
            return 0.0
        
        query_words = set(query.lower().split())
        relevance_scores = []
        
        for doc in retrieved_docs:
            doc_words = set(doc.page_content.lower().split())
            
            # 자카드 유사도 계산
            intersection = len(query_words.intersection(doc_words))
            union = len(query_words.union(doc_words))
            
            jaccard_score = intersection / union if union > 0 else 0
            relevance_scores.append(jaccard_score)
        
        return np.mean(relevance_scores)
    
    def benchmark_speed(self, 
                       test_documents: List[Document],
                       num_queries: int = 10) -> pd.DataFrame:
        """리트리버 속도 벤치마크"""
        
        import time
        
        results = []
        test_query = "노인 복지 지원 제도"
        
        for name, retriever in self.retrievers.items():
            try:
                # 문서 추가 시간 측정
                start_time = time.time()
                retriever.add_documents(test_documents)
                indexing_time = time.time() - start_time
                
                # 검색 시간 측정
                search_times = []
                for _ in range(num_queries):
                    start_time = time.time()
                    retriever.retrieve(test_query, k=5)
                    search_times.append(time.time() - start_time)
                
                avg_search_time = np.mean(search_times)
                
                result = {
                    'retriever': name,
                    'indexing_time': round(indexing_time, 3),
                    'avg_search_time': round(avg_search_time, 4),
                    'queries_per_second': round(1 / avg_search_time, 2),
                    'documents_indexed': len(test_documents)
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"{name} 속도 테스트 실패: {e}")
                continue
        
        return pd.DataFrame(results)


def main():
    """리트리버 테스트"""
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    print("🔍 리트리버 구성 모듈 테스트")
    print("=" * 50)
    
    # 테스트 문서
    test_docs = [
        Document(
            page_content="만 65세 이상 노인을 대상으로 의료비를 월 최대 30만원까지 지원합니다.",
            metadata={"category": "의료지원", "region": "전국"}
        ),
        Document(
            page_content="기초생활수급자 어르신에게 생활비를 월 50만원씩 지원하는 제도입니다.",
            metadata={"category": "생활지원", "region": "서울"}
        ),
        Document(
            page_content="요양보호사가 주 3회 방문하여 돌봄서비스를 제공합니다.",
            metadata={"category": "돌봄서비스", "region": "부산"}
        ),
        Document(
            page_content="치매 어르신을 위한 인지기능 향상 프로그램을 운영합니다.",
            metadata={"category": "의료지원", "region": "대구"}
        ),
        Document(
            page_content="저소득 노인을 위한 교통비 할인 혜택을 제공합니다.",
            metadata={"category": "교통지원", "region": "전국"}
        )
    ]
    
    # 키워드 리트리버 테스트
    print("📝 키워드 리트리버 테스트...")
    try:
        keyword_retriever = KeywordRetriever(use_bm25=False)  # BM25 없이 테스트
        keyword_retriever.add_documents(test_docs)
        
        query = "노인 의료비 지원"
        results = keyword_retriever.retrieve(query, k=3)
        
        print(f"쿼리: '{query}'")
        for i, doc in enumerate(results, 1):
            score = doc.metadata.get('boosted_score', 0)
            print(f"  [{i}] 점수: {score:.3f} - {doc.page_content[:50]}...")
        
    except Exception as e:
        print(f"키워드 리트리버 테스트 실패: {e}")
    
    # 성능 비교 (간단 버전)
    print(f"\n📊 리트리버 성능 비교:")
    comparator = RetrieverComparator()
    
    try:
        # 키워드 리트리버만 등록 (의미 기반은 임베딩 함수 필요)
        comparator.register_retriever("keyword", KeywordRetriever(use_bm25=False))
        
        # 성능 비교
        performance_df = comparator.compare_retrievers(test_docs)
        
        if not performance_df.empty:
            print(performance_df.to_string(index=False))
        else:
            print("성능 비교 결과 없음")
            
    except Exception as e:
        print(f"성능 비교 실패: {e}")
    
    print(f"\n✅ 리트리버 테스트 완료!")


if __name__ == "__main__":
    main()