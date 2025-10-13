# =========================================
# 🧠 임베딩 모델 비교 모듈
# =========================================

import os
import logging
import time
import numpy as np
from typing import List, Dict, Any, Optional, Tuple, Union
from abc import ABC, abstractmethod
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import seaborn as sns

# 임베딩 모델 임포트
try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    from langchain_openai import OpenAIEmbeddings
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from transformers import AutoTokenizer, AutoModel
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)


class BaseEmbeddingModel(ABC):
    """임베딩 모델 기본 클래스"""
    
    def __init__(self, model_name: str, model_type: str):
        self.model_name = model_name
        self.model_type = model_type
        self.is_initialized = False
        self.embedding_dim = None
    
    @abstractmethod
    def initialize(self) -> bool:
        """모델 초기화"""
        pass
    
    @abstractmethod
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트를 임베딩으로 변환"""
        pass
    
    @abstractmethod
    def embed_query(self, query: str) -> np.ndarray:
        """단일 쿼리를 임베딩으로 변환"""
        pass
    
    def get_model_info(self) -> Dict[str, Any]:
        """모델 정보 반환"""
        return {
            'model_name': self.model_name,
            'model_type': self.model_type,
            'is_initialized': self.is_initialized,
            'embedding_dim': self.embedding_dim
        }


class OpenAIEmbeddingModel(BaseEmbeddingModel):
    """OpenAI 임베딩 모델"""
    
    def __init__(self, model_name: str = "text-embedding-ada-002"):
        super().__init__(model_name, "OpenAI")
        self.client = None
    
    def initialize(self) -> bool:
        """OpenAI 임베딩 모델 초기화"""
        if not OPENAI_AVAILABLE:
            logger.error("OpenAI 패키지가 설치되지 않았습니다.")
            return False
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            logger.error("OPENAI_API_KEY 환경변수가 설정되지 않았습니다.")
            return False
        
        try:
            self.client = OpenAIEmbeddings(
                model=self.model_name,
                openai_api_key=api_key
            )
            
            # 테스트 임베딩으로 차원 확인
            test_embedding = self.client.embed_query("테스트")
            self.embedding_dim = len(test_embedding)
            self.is_initialized = True
            
            logger.info(f"OpenAI 임베딩 모델 초기화 완료: {self.model_name} (dim: {self.embedding_dim})")
            return True
            
        except Exception as e:
            logger.error(f"OpenAI 임베딩 모델 초기화 실패: {e}")
            return False
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트를 임베딩으로 변환"""
        if not self.is_initialized:
            raise RuntimeError("모델이 초기화되지 않았습니다.")
        
        try:
            embeddings = self.client.embed_documents(texts)
            return np.array(embeddings)
        except Exception as e:
            logger.error(f"텍스트 임베딩 생성 실패: {e}")
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """단일 쿼리를 임베딩으로 변환"""
        if not self.is_initialized:
            raise RuntimeError("모델이 초기화되지 않았습니다.")
        
        try:
            embedding = self.client.embed_query(query)
            return np.array(embedding)
        except Exception as e:
            logger.error(f"쿼리 임베딩 생성 실패: {e}")
            raise


class SentenceTransformerModel(BaseEmbeddingModel):
    """SentenceTransformer 기반 임베딩 모델"""
    
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        super().__init__(model_name, "SentenceTransformer")
        self.model = None
    
    def initialize(self) -> bool:
        """SentenceTransformer 모델 초기화"""
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            logger.error("sentence-transformers 패키지가 설치되지 않았습니다.")
            return False
        
        try:
            self.model = SentenceTransformer(self.model_name)
            
            # 테스트 임베딩으로 차원 확인
            test_embedding = self.model.encode("테스트")
            self.embedding_dim = len(test_embedding)
            self.is_initialized = True
            
            logger.info(f"SentenceTransformer 모델 초기화 완료: {self.model_name} (dim: {self.embedding_dim})")
            return True
            
        except Exception as e:
            logger.error(f"SentenceTransformer 모델 초기화 실패: {e}")
            return False
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트를 임베딩으로 변환"""
        if not self.is_initialized:
            raise RuntimeError("모델이 초기화되지 않았습니다.")
        
        try:
            embeddings = self.model.encode(texts, convert_to_numpy=True)
            return embeddings
        except Exception as e:
            logger.error(f"텍스트 임베딩 생성 실패: {e}")
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """단일 쿼리를 임베딩으로 변환"""
        if not self.is_initialized:
            raise RuntimeError("모델이 초기화되지 않았습니다.")
        
        try:
            embedding = self.model.encode(query, convert_to_numpy=True)
            return embedding
        except Exception as e:
            logger.error(f"쿼리 임베딩 생성 실패: {e}")
            raise


class KoBERTEmbeddingModel(BaseEmbeddingModel):
    """한국어 BERT 임베딩 모델 (Transformers 기반)"""
    
    def __init__(self, model_name: str = "klue/bert-base"):
        super().__init__(model_name, "KoBERT")
        self.tokenizer = None
        self.model = None
        self.device = None
    
    def initialize(self) -> bool:
        """KoBERT 모델 초기화"""
        if not TRANSFORMERS_AVAILABLE:
            logger.error("transformers 패키지가 설치되지 않았습니다.")
            return False
        
        try:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            
            self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            self.model = AutoModel.from_pretrained(self.model_name)
            self.model.to(self.device)
            self.model.eval()
            
            # 테스트 임베딩으로 차원 확인
            test_embedding = self._encode_text("테스트")
            self.embedding_dim = len(test_embedding)
            self.is_initialized = True
            
            logger.info(f"KoBERT 모델 초기화 완료: {self.model_name} (dim: {self.embedding_dim})")
            return True
            
        except Exception as e:
            logger.error(f"KoBERT 모델 초기화 실패: {e}")
            return False
    
    def _encode_text(self, text: str) -> np.ndarray:
        """단일 텍스트 인코딩"""
        inputs = self.tokenizer(
            text, 
            return_tensors="pt", 
            truncation=True, 
            padding=True, 
            max_length=512
        )
        
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = self.model(**inputs)
            # [CLS] 토큰의 임베딩 사용
            embeddings = outputs.last_hidden_state[:, 0, :].cpu().numpy()
        
        return embeddings.squeeze()
    
    def embed_texts(self, texts: List[str]) -> np.ndarray:
        """텍스트 리스트를 임베딩으로 변환"""
        if not self.is_initialized:
            raise RuntimeError("모델이 초기화되지 않았습니다.")
        
        try:
            embeddings = []
            for text in texts:
                embedding = self._encode_text(text)
                embeddings.append(embedding)
            
            return np.array(embeddings)
        except Exception as e:
            logger.error(f"텍스트 임베딩 생성 실패: {e}")
            raise
    
    def embed_query(self, query: str) -> np.ndarray:
        """단일 쿼리를 임베딩으로 변환"""
        if not self.is_initialized:
            raise RuntimeError("모델이 초기화되지 않았습니다.")
        
        try:
            return self._encode_text(query)
        except Exception as e:
            logger.error(f"쿼리 임베딩 생성 실패: {e}")
            raise


class EmbeddingModelComparator:
    """임베딩 모델 비교 및 평가 클래스"""
    
    def __init__(self):
        self.models = {}
        self.welfare_keywords = [
            "노인", "어르신", "고령자", "복지", "지원", "혜택",
            "의료비", "간병", "요양", "돌봄", "생활지원", "수당",
            "신청", "대상", "자격", "조건", "방법", "절차"
        ]
        
        # 노인복지 관련 테스트 텍스트
        self.test_texts = [
            "만 65세 이상 노인을 대상으로 의료비를 지원합니다.",
            "기초생활수급자 어르신에게 생활비를 지원하는 제도입니다.",
            "요양보호사가 방문하여 돌봄서비스를 제공합니다.",
            "거동이 불편한 고령자를 위한 이동지원 서비스입니다.",
            "치매 어르신을 위한 인지기능 향상 프로그램입니다."
        ]
        
        self.test_queries = [
            "노인 의료비 지원",
            "어르신 돌봄 서비스",
            "고령자 복지 혜택",
            "노인복지 신청 방법"
        ]
    
    def register_model(self, model: BaseEmbeddingModel, alias: str = None) -> bool:
        """임베딩 모델 등록"""
        if alias is None:
            alias = model.model_type.lower()
        
        if model.initialize():
            self.models[alias] = model
            logger.info(f"모델 등록 완료: {alias}")
            return True
        else:
            logger.error(f"모델 등록 실패: {alias}")
            return False
    
    def initialize_available_models(self) -> Dict[str, bool]:
        """사용 가능한 모든 모델 초기화"""
        results = {}
        
        # OpenAI 모델
        try:
            openai_model = OpenAIEmbeddingModel()
            results['openai'] = self.register_model(openai_model, 'openai')
        except Exception as e:
            logger.warning(f"OpenAI 모델 초기화 건너뜀: {e}")
            results['openai'] = False
        
        # SentenceTransformer 모델들
        sentence_models = [
            ("sentence-transformers/all-MiniLM-L6-v2", "minilm"),
            ("sentence-transformers/all-mpnet-base-v2", "mpnet"),
            ("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", "multilingual")
        ]
        
        for model_name, alias in sentence_models:
            try:
                st_model = SentenceTransformerModel(model_name)
                results[alias] = self.register_model(st_model, alias)
            except Exception as e:
                logger.warning(f"{alias} 모델 초기화 건너뜀: {e}")
                results[alias] = False
        
        # KoBERT 모델들
        kobert_models = [
            ("klue/bert-base", "kobert_klue"),
            ("monologg/kobert", "kobert_mono")
        ]
        
        for model_name, alias in kobert_models:
            try:
                kobert_model = KoBERTEmbeddingModel(model_name)
                results[alias] = self.register_model(kobert_model, alias)
            except Exception as e:
                logger.warning(f"{alias} 모델 초기화 건너뜀: {e}")
                results[alias] = False
        
        logger.info(f"사용 가능한 모델: {sum(results.values())}/{len(results)}")
        return results
    
    def benchmark_models(self, custom_texts: List[str] = None) -> pd.DataFrame:
        """모델 성능 벤치마크"""
        if not self.models:
            logger.error("등록된 모델이 없습니다.")
            return pd.DataFrame()
        
        texts_to_test = custom_texts if custom_texts else self.test_texts
        
        benchmark_results = []
        
        for model_alias, model in self.models.items():
            logger.info(f"벤치마킹: {model_alias}")
            
            try:
                # 임베딩 생성 시간 측정
                start_time = time.time()
                embeddings = model.embed_texts(texts_to_test)
                embedding_time = time.time() - start_time
                
                # 쿼리 임베딩 시간 측정
                query_times = []
                for query in self.test_queries:
                    start_time = time.time()
                    query_embedding = model.embed_query(query)
                    query_times.append(time.time() - start_time)
                
                avg_query_time = np.mean(query_times)
                
                # 품질 메트릭 계산
                quality_metrics = self._calculate_quality_metrics(
                    model, embeddings, texts_to_test
                )
                
                result = {
                    'model': model_alias,
                    'model_type': model.model_type,
                    'embedding_dim': model.embedding_dim,
                    'total_embedding_time': round(embedding_time, 3),
                    'avg_query_time': round(avg_query_time, 3),
                    'texts_per_second': round(len(texts_to_test) / embedding_time, 2),
                    **quality_metrics
                }
                
                benchmark_results.append(result)
                
            except Exception as e:
                logger.error(f"{model_alias} 벤치마킹 실패: {e}")
                continue
        
        df = pd.DataFrame(benchmark_results)
        
        if not df.empty:
            # 종합 점수 계산 (속도와 품질의 가중평균)
            df['overall_score'] = (
                df['semantic_coherence'] * 0.4 +
                df['keyword_relevance'] * 0.3 +
                (1 / (df['avg_query_time'] + 0.001)) * 0.2 +  # 속도 점수
                df['cluster_quality'] * 0.1
            )
            
            # 정규화 (0-1 범위)
            df['overall_score'] = (df['overall_score'] - df['overall_score'].min()) / (
                df['overall_score'].max() - df['overall_score'].min()
            )
        
        return df.sort_values('overall_score', ascending=False) if not df.empty else df
    
    def _calculate_quality_metrics(self, model: BaseEmbeddingModel, 
                                 embeddings: np.ndarray, 
                                 texts: List[str]) -> Dict[str, float]:
        """임베딩 품질 메트릭 계산"""
        metrics = {}
        
        try:
            # 1. 의미적 일관성 (같은 주제 텍스트들의 유사도)
            similarity_matrix = cosine_similarity(embeddings)
            # 대각선 제외한 평균 유사도
            upper_tri_indices = np.triu_indices_from(similarity_matrix, k=1)
            avg_similarity = np.mean(similarity_matrix[upper_tri_indices])
            metrics['semantic_coherence'] = round(avg_similarity, 3)
            
            # 2. 키워드 관련성 (복지 키워드가 포함된 텍스트들의 유사도)
            keyword_similarities = []
            for i, text1 in enumerate(texts):
                for j, text2 in enumerate(texts[i+1:], i+1):
                    # 둘 다 키워드를 포함하는 경우
                    if (any(kw in text1 for kw in self.welfare_keywords) and 
                        any(kw in text2 for kw in self.welfare_keywords)):
                        keyword_similarities.append(similarity_matrix[i, j])
            
            metrics['keyword_relevance'] = round(
                np.mean(keyword_similarities) if keyword_similarities else 0, 3
            )
            
            # 3. 클러스터링 품질 (실루엣 스코어)
            if len(embeddings) >= 3:
                try:
                    n_clusters = min(3, len(embeddings) - 1)
                    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
                    cluster_labels = kmeans.fit_predict(embeddings)
                    
                    from sklearn.metrics import silhouette_score
                    silhouette = silhouette_score(embeddings, cluster_labels)
                    metrics['cluster_quality'] = round(silhouette, 3)
                except:
                    metrics['cluster_quality'] = 0.0
            else:
                metrics['cluster_quality'] = 0.0
            
            # 4. 차원 다양성 (PCA 설명 분산 비율)
            if embeddings.shape[1] > 1:
                pca = PCA(n_components=min(5, embeddings.shape[1]))
                pca.fit(embeddings)
                explained_variance_ratio = np.sum(pca.explained_variance_ratio_[:3])
                metrics['dimension_diversity'] = round(explained_variance_ratio, 3)
            else:
                metrics['dimension_diversity'] = 0.0
            
        except Exception as e:
            logger.warning(f"품질 메트릭 계산 중 오류: {e}")
            metrics = {
                'semantic_coherence': 0.0,
                'keyword_relevance': 0.0,
                'cluster_quality': 0.0,
                'dimension_diversity': 0.0
            }
        
        return metrics
    
    def compare_retrieval_performance(self, documents: List[str], 
                                    queries: List[str]) -> pd.DataFrame:
        """검색 성능 비교"""
        if not self.models:
            logger.error("등록된 모델이 없습니다.")
            return pd.DataFrame()
        
        results = []
        
        for model_alias, model in self.models.items():
            logger.info(f"검색 성능 테스트: {model_alias}")
            
            try:
                # 문서 임베딩 생성
                doc_embeddings = model.embed_texts(documents)
                
                # 각 쿼리에 대한 검색 성능 측정
                precision_scores = []
                recall_scores = []
                
                for query in queries:
                    query_embedding = model.embed_query(query)
                    
                    # 코사인 유사도 계산
                    similarities = cosine_similarity(
                        query_embedding.reshape(1, -1), 
                        doc_embeddings
                    )[0]
                    
                    # 상위 3개 문서 선택
                    top_3_indices = np.argsort(similarities)[-3:][::-1]
                    top_3_scores = similarities[top_3_indices]
                    
                    # 관련성 판단 (간단한 키워드 기반)
                    relevant_docs = []
                    query_keywords = [kw for kw in self.welfare_keywords if kw in query]
                    
                    for idx in top_3_indices:
                        doc = documents[idx]
                        if any(kw in doc for kw in query_keywords):
                            relevant_docs.append(idx)
                    
                    # Precision@3 계산
                    precision = len(relevant_docs) / 3
                    precision_scores.append(precision)
                
                avg_precision = np.mean(precision_scores)
                
                result = {
                    'model': model_alias,
                    'avg_precision_at_3': round(avg_precision, 3),
                    'avg_similarity_score': round(np.mean([
                        np.max(cosine_similarity(
                            model.embed_query(q).reshape(1, -1), 
                            doc_embeddings
                        )) for q in queries
                    ]), 3)
                }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"{model_alias} 검색 성능 테스트 실패: {e}")
                continue
        
        return pd.DataFrame(results)
    
    def get_model_recommendation(self, 
                               custom_texts: List[str] = None,
                               priority: str = "balanced") -> Dict[str, Any]:
        """
        모델 추천
        
        Args:
            custom_texts: 커스텀 테스트 텍스트
            priority: "speed", "quality", "balanced"
        """
        benchmark_df = self.benchmark_models(custom_texts)
        
        if benchmark_df.empty:
            return {
                'recommended_model': None,
                'reason': '사용 가능한 모델 없음',
                'benchmark_results': benchmark_df
            }
        
        if priority == "speed":
            # 속도 우선
            best_model = benchmark_df.loc[benchmark_df['texts_per_second'].idxmax()]
            reason = f"가장 빠른 처리 속도 ({best_model['texts_per_second']:.1f} texts/sec)"
        
        elif priority == "quality":
            # 품질 우선
            quality_score = (
                benchmark_df['semantic_coherence'] * 0.4 +
                benchmark_df['keyword_relevance'] * 0.6
            )
            best_idx = quality_score.idxmax()
            best_model = benchmark_df.loc[best_idx]
            reason = f"최고 품질 점수 (의미 일관성: {best_model['semantic_coherence']:.3f})"
        
        else:
            # 균형 (기본)
            best_model = benchmark_df.iloc[0]  # overall_score로 정렬되어 있음
            reason = f"최고 종합 점수 ({best_model['overall_score']:.3f})"
        
        return {
            'recommended_model': best_model['model'],
            'model_info': best_model.to_dict(),
            'reason': reason,
            'benchmark_results': benchmark_df
        }
    
    def visualize_model_comparison(self, benchmark_df: pd.DataFrame, 
                                 save_path: str = None) -> None:
        """모델 비교 결과 시각화"""
        if benchmark_df.empty:
            logger.warning("시각화할 데이터가 없습니다.")
            return
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('임베딩 모델 성능 비교', fontsize=16, fontweight='bold')
        
        # 1. 종합 점수
        axes[0, 0].bar(benchmark_df['model'], benchmark_df['overall_score'])
        axes[0, 0].set_title('종합 점수')
        axes[0, 0].set_ylabel('점수')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # 2. 속도 비교
        axes[0, 1].bar(benchmark_df['model'], benchmark_df['texts_per_second'], 
                      color='orange')
        axes[0, 1].set_title('처리 속도 (texts/second)')
        axes[0, 1].set_ylabel('속도')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # 3. 품질 메트릭
        quality_metrics = ['semantic_coherence', 'keyword_relevance', 'cluster_quality']
        quality_data = benchmark_df[['model'] + quality_metrics].set_index('model')
        quality_data.plot(kind='bar', ax=axes[1, 0])
        axes[1, 0].set_title('품질 메트릭')
        axes[1, 0].set_ylabel('점수')
        axes[1, 0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 4. 임베딩 차원 vs 쿼리 시간
        scatter = axes[1, 1].scatter(benchmark_df['embedding_dim'], 
                                   benchmark_df['avg_query_time'],
                                   c=benchmark_df['overall_score'], 
                                   cmap='viridis', s=100, alpha=0.7)
        axes[1, 1].set_xlabel('임베딩 차원')
        axes[1, 1].set_ylabel('평균 쿼리 시간 (초)')
        axes[1, 1].set_title('차원 vs 속도 (색상: 종합점수)')
        
        # 각 점에 모델명 표시
        for i, model in enumerate(benchmark_df['model']):
            axes[1, 1].annotate(model, 
                               (benchmark_df.iloc[i]['embedding_dim'], 
                                benchmark_df.iloc[i]['avg_query_time']),
                               xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        plt.colorbar(scatter, ax=axes[1, 1])
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')
            logger.info(f"차트 저장: {save_path}")
        
        plt.show()


def main():
    """임베딩 모델 비교 테스트"""
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    print("🧠 임베딩 모델 비교 테스트")
    print("=" * 50)
    
    comparator = EmbeddingModelComparator()
    
    # 사용 가능한 모델 초기화
    print("\n📥 모델 초기화 중...")
    model_status = comparator.initialize_available_models()
    
    for model, status in model_status.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {model}")
    
    if not any(model_status.values()):
        print("❌ 사용 가능한 모델이 없습니다.")
        return
    
    # 벤치마크 실행
    print(f"\n🔬 모델 벤치마킹...")
    benchmark_df = comparator.benchmark_models()
    
    if not benchmark_df.empty:
        print(f"\n📊 벤치마크 결과:")
        print(benchmark_df.to_string(index=False))
        
        # 모델 추천
        print(f"\n🏆 모델 추천:")
        for priority in ["balanced", "speed", "quality"]:
            recommendation = comparator.get_model_recommendation(priority=priority)
            print(f"  {priority.title()}: {recommendation['recommended_model']} "
                  f"({recommendation['reason']})")
        
        # 시각화 (선택적)
        try:
            comparator.visualize_model_comparison(benchmark_df)
        except Exception as e:
            print(f"시각화 건너뜀: {e}")
    
    else:
        print("❌ 벤치마크 결과가 없습니다.")


class EmbeddingModelManager:
    """임베딩 모델 관리 클래스 (통합 비교평가용)"""
    
    def __init__(self):
        """임베딩 모델 관리자 초기화"""
        self.comparator = EmbeddingModelComparator()
        self.models = {}
        logger.info("임베딩 모델 관리자 초기화 완료")
    
    def get_embedding(self, text: str, model_name: str = "sentence-transformers") -> Optional[List[float]]:
        """
        지정된 모델로 텍스트 임베딩 생성
        
        Args:
            text: 임베딩할 텍스트
            model_name: 사용할 모델 이름
            
        Returns:
            Optional[List[float]]: 임베딩 벡터 (실패시 None)
        """
        try:
            # 모델 매핑
            model_mapping = {
                'sentence-transformers': 'sentence_transformers',
                'openai': 'openai',
                'huggingface': 'huggingface'
            }
            
            actual_model = model_mapping.get(model_name, 'sentence_transformers')
            
            # 모델이 없다면 생성 및 초기화 시도
            if actual_model not in self.models:
                if actual_model == 'sentence_transformers' and SENTENCE_TRANSFORMERS_AVAILABLE:
                    model = SentenceTransformerModel()
                    if model.initialize():
                        self.models[actual_model] = model
                    else:
                        logger.warning(f"SentenceTransformer 모델 초기화 실패")
                        return None
                elif actual_model == 'openai' and OPENAI_AVAILABLE:
                    model = OpenAIEmbeddingModel()
                    if model.initialize():
                        self.models[actual_model] = model
                    else:
                        logger.warning(f"OpenAI 모델 초기화 실패")
                        return None
                elif actual_model == 'huggingface' and TRANSFORMERS_AVAILABLE:
                    model = KoBERTEmbeddingModel()
                    if model.initialize():
                        self.models[actual_model] = model
                    else:
                        logger.warning(f"HuggingFace 모델 초기화 실패")
                        return None
                else:
                    logger.warning(f"모델 {actual_model}을 사용할 수 없습니다.")
                    return None
            
            # 임베딩 생성
            model = self.models[actual_model]
            embeddings = model.embed_texts([text])
            
            if embeddings is not None and len(embeddings) > 0:
                return embeddings[0]
            else:
                return None
            
        except Exception as e:
            logger.error(f"임베딩 생성 실패 ({model_name}): {e}")
            return None
    
    def get_available_models(self) -> List[str]:
        """사용 가능한 임베딩 모델 목록 반환"""
        available = []
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            available.append('sentence-transformers')
        if OPENAI_AVAILABLE and os.getenv('OPENAI_API_KEY'):
            available.append('openai')
        if TRANSFORMERS_AVAILABLE:
            available.append('huggingface')
            
        return available
    
    def evaluate_model_performance(self, texts: List[str], model_name: str) -> Dict[str, Any]:
        """
        특정 모델의 성능 평가
        
        Args:
            texts: 평가할 텍스트 목록
            model_name: 평가할 모델 이름
            
        Returns:
            Dict[str, Any]: 성능 평가 결과
        """
        try:
            start_time = time.time()
            
            # 임베딩 생성
            embeddings = []
            success_count = 0
            
            for text in texts:
                embedding = self.get_embedding(text, model_name)
                if embedding is not None:
                    embeddings.append(embedding)
                    success_count += 1
            
            processing_time = time.time() - start_time
            
            return {
                'model': model_name,
                'total_texts': len(texts),
                'successful_embeddings': success_count,
                'success_rate': success_count / len(texts) if texts else 0,
                'processing_time': processing_time,
                'avg_time_per_text': processing_time / len(texts) if texts else 0,
                'embedding_dimension': len(embeddings[0]) if embeddings is not None and len(embeddings) > 0 else 0,
                'success': success_count > 0
            }
            
        except Exception as e:
            return {
                'model': model_name,
                'total_texts': len(texts),
                'successful_embeddings': 0,
                'success_rate': 0,
                'processing_time': 0,
                'avg_time_per_text': 0,
                'embedding_dimension': 0,
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    main()