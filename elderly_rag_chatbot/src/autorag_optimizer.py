# =========================================
# 🤖 AutoRAG 스타일 통합 관리 시스템
# =========================================

import os
import json
import time
import logging
import asyncio
from typing import Dict, List, Any, Optional, Tuple, Callable
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)

# 프로젝트 모듈들 (상대 import 처리)
try:
    from .text_extraction_comparison import TextExtractionComparison
    from .chunk_strategy import ChunkStrategyComparison  
    from .embedding_models import EmbeddingModelComparison
    from .vector_store import WelfareVectorStore
    from .retriever import RetrieverComparison
    from .rag_system import ElderlyWelfareRAGChain, MultiRAGSystem, RAGEvaluator
    from .langgraph_workflow import ElderlyWelfareWorkflow
    from .chatbot_interface import ElderlyWelfareChatbot
except ImportError:
    # 절대 import로 재시도
    try:
        from src.text_extraction_comparison import TextExtractionComparison
        from src.chunk_strategy import ChunkStrategyComparison
        from src.embedding_models import EmbeddingModelComparison
        from src.vector_store import WelfareVectorStore
        from src.retriever import RetrieverComparison
        from src.rag_system import ElderlyWelfareRAGChain, MultiRAGSystem, RAGEvaluator
        from src.langgraph_workflow import ElderlyWelfareWorkflow
        from src.chatbot_interface import ElderlyWelfareChatbot
    except ImportError as e:
        logger.error(f"프로젝트 모듈 import 실패: {e}")
        # 기본 클래스들로 대체
        TextExtractionComparison = None
        ChunkStrategyComparison = None
        EmbeddingModelComparison = None
        WelfareVectorStore = None
        RetrieverComparison = None
        ElderlyWelfareRAGChain = None
        MultiRAGSystem = None
        RAGEvaluator = None
        ElderlyWelfareWorkflow = None
        ElderlyWelfareChatbot = None

logger = logging.getLogger(__name__)


@dataclass
class ComponentSelection:
    """각 컴포넌트 선택 결과"""
    component_name: str
    selected_option: str
    score: float
    reason: str
    metrics: Dict[str, Any]
    
    
@dataclass
class AutoRAGConfig:
    """AutoRAG 시스템 설정"""
    
    # 평가 데이터
    evaluation_queries: List[str]
    evaluation_documents: List[str]
    
    # 평가 메트릭 가중치
    performance_weight: float = 0.3
    quality_weight: float = 0.4
    speed_weight: float = 0.2
    resource_weight: float = 0.1
    
    # 자동화 레벨
    automation_level: str = "full"  # "manual", "semi", "full"
    
    # 최적화 목표
    optimization_target: str = "balanced"  # "speed", "quality", "balanced"
    
    # 실험 설정
    max_experiments: int = 50
    early_stopping_patience: int = 5
    
    # 결과 저장
    save_intermediate_results: bool = True
    results_directory: str = "./autorag_results"


class AutoRAGOptimizer:
    """AutoRAG 자동 최적화 시스템"""
    
    def __init__(self, config: AutoRAGConfig, data_directory: str = "./data/복지로"):
        """AutoRAG 시스템 초기화"""
        
        self.config = config
        self.data_directory = data_directory
        
        # 결과 저장 디렉토리
        os.makedirs(config.results_directory, exist_ok=True)
        
        # 컴포넌트 비교 시스템들
        self.text_extraction_comparison = None
        self.chunk_comparison = None
        self.embedding_comparison = None
        self.retriever_comparison = None
        
        # 실험 결과
        self.experiment_results = []
        self.best_pipeline = None
        
        # 진행 상황
        self.current_step = 0
        self.total_steps = 7  # 총 최적화 단계 수
        
        logger.info("AutoRAG 최적화 시스템 초기화 완료")
        
        # 컴포넌트 초기화 확인
        self._validate_components()
    
    def _validate_components(self):
        """필요한 컴포넌트들이 사용 가능한지 확인"""
        
        if TextExtractionComparison is None:
            logger.warning("TextExtractionComparison을 사용할 수 없습니다")
        
        if ChunkStrategyComparison is None:
            logger.warning("ChunkStrategyComparison을 사용할 수 없습니다")
        
        if EmbeddingModelComparison is None:
            logger.warning("EmbeddingModelComparison을 사용할 수 없습니다")
    
    async def optimize_pipeline(self) -> Dict[str, Any]:
        """전체 RAG 파이프라인 자동 최적화"""
        
        logger.info("🤖 AutoRAG 파이프라인 최적화 시작")
        
        optimization_start = time.time()
        
        try:
            # 1. 텍스트 추출 최적화
            self.current_step = 1
            extraction_result = await self._optimize_text_extraction()
            
            # 2. 청킹 전략 최적화
            self.current_step = 2
            chunking_result = await self._optimize_chunking_strategy(extraction_result)
            
            # 3. 임베딩 모델 최적화
            self.current_step = 3
            embedding_result = await self._optimize_embedding_model(chunking_result)
            
            # 4. 벡터 저장소 구성
            self.current_step = 4
            vector_store_result = await self._setup_vector_store(embedding_result)
            
            # 5. 검색기 최적화
            self.current_step = 5
            retriever_result = await self._optimize_retriever(vector_store_result)
            
            # 6. RAG 시스템 최적화
            self.current_step = 6
            rag_result = await self._optimize_rag_system(retriever_result)
            
            # 7. 전체 파이프라인 평가
            self.current_step = 7
            final_result = await self._evaluate_final_pipeline(rag_result)
            
            optimization_time = time.time() - optimization_start
            
            # 최적화 완료
            self.best_pipeline = final_result
            
            # 결과 저장
            await self._save_optimization_results(final_result, optimization_time)
            
            logger.info(f"✅ AutoRAG 파이프라인 최적화 완료 (소요시간: {optimization_time:.2f}초)")
            
            return final_result
            
        except Exception as e:
            logger.error(f"❌ AutoRAG 최적화 실패: {e}")
            raise
    
    async def _optimize_text_extraction(self) -> ComponentSelection:
        """텍스트 추출 방법 최적화"""
        
        logger.info("📄 1단계: 텍스트 추출 방법 최적화")
        
        self.text_extraction_comparison = TextExtractionComparison()
        
        # 샘플 파일들 수집
        pdf_files = list(Path(self.data_directory).rglob("*.pdf"))[:5]
        hwp_files = list(Path(self.data_directory).rglob("*.hwp"))[:5]
        
        # PDF 추출기 비교
        pdf_results = {}
        if pdf_files:
            pdf_comparison = self.text_extraction_comparison.compare_pdf_extractors(
                [str(f) for f in pdf_files]
            )
            if "error" not in pdf_comparison:
                pdf_results = pdf_comparison
        
        # HWP 추출기 비교
        hwp_results = {}
        if hwp_files:
            hwp_comparison = self.text_extraction_comparison.compare_hwp_extractors(
                [str(f) for f in hwp_files]
            )
            if "error" not in hwp_comparison:
                hwp_results = hwp_comparison
        
        # 최적 추출기 선택
        best_extractors = {}
        total_score = 0
        
        if pdf_results and "best_extractor" in pdf_results:
            best_extractors["pdf"] = pdf_results["best_extractor"]
            total_score += pdf_results["best_extractor"]["score"]
        
        if hwp_results and "best_extractor" in hwp_results:
            best_extractors["hwp"] = hwp_results["best_extractor"]
            total_score += hwp_results["best_extractor"]["score"]
        
        avg_score = total_score / len(best_extractors) if best_extractors else 0.5
        
        selection = ComponentSelection(
            component_name="text_extraction",
            selected_option=json.dumps(best_extractors),
            score=avg_score,
            reason="다양한 추출기 중 성공률과 텍스트 품질이 가장 높은 조합 선택",
            metrics={
                "pdf_results": pdf_results,
                "hwp_results": hwp_results,
                "best_extractors": best_extractors
            }
        )
        
        logger.info(f"✅ 텍스트 추출 최적화 완료 (점수: {avg_score:.3f})")
        return selection
    
    async def _optimize_chunking_strategy(self, extraction_result: ComponentSelection) -> ComponentSelection:
        """청킹 전략 최적화"""
        
        logger.info("✂️ 2단계: 청킹 전략 최적화")
        
        self.chunk_comparison = ChunkStrategyComparison()
        
        # 샘플 텍스트 준비 (실제 추출된 텍스트 사용)
        sample_texts = []
        
        # 평가용 쿼리에서 샘플 텍스트 생성 (실제로는 추출된 문서 사용)
        if self.config.evaluation_documents:
            sample_texts = self.config.evaluation_documents[:10]
        else:
            # 기본 샘플 텍스트
            sample_texts = [
                "노인복지법에 따른 의료비 지원 제도는 65세 이상 노인을 대상으로 합니다. " * 20,
                "장기요양보험 제도는 신체적 또는 정신적 장애로 도움이 필요한 노인에게 제공됩니다. " * 20,
                "기초연금은 소득 하위 70% 노인에게 지급되는 기초생활보장 제도입니다. " * 20
            ]
        
        # 청킹 전략 평가
        evaluation_results = self.chunk_comparison.evaluate_strategies(
            sample_texts,
            criteria=["coherence", "coverage", "diversity", "semantic_similarity"]
        )
        
        # 최적 전략 선택
        best_strategy = max(evaluation_results.items(), key=lambda x: x[1]["overall_score"])
        
        selection = ComponentSelection(
            component_name="chunking_strategy",
            selected_option=best_strategy[0],
            score=best_strategy[1]["overall_score"],
            reason=f"일관성, 커버리지, 다양성 측면에서 가장 우수한 성능을 보임",
            metrics={
                "all_strategies": evaluation_results,
                "best_strategy_details": best_strategy[1]
            }
        )
        
        logger.info(f"✅ 청킹 전략 최적화 완료 - {best_strategy[0]} (점수: {best_strategy[1]['overall_score']:.3f})")
        return selection
    
    async def _optimize_embedding_model(self, chunking_result: ComponentSelection) -> ComponentSelection:
        """임베딩 모델 최적화"""
        
        logger.info("🔢 3단계: 임베딩 모델 최적화")
        
        self.embedding_comparison = EmbeddingModelComparison()
        
        # 평가용 텍스트 (복지 정책 관련 키워드)
        evaluation_texts = self.config.evaluation_queries if self.config.evaluation_queries else [
            "65세 이상 노인 의료비 지원 제도",
            "장기요양보험 신청 방법과 절차",
            "기초연금 수급 자격과 금액",
            "독거노인 돌봄 서비스 안내",
            "노인 주거 지원 정책"
        ]
        
        # 임베딩 모델 비교
        comparison_results = self.embedding_comparison.compare_models(evaluation_texts)
        
        # 최적 모델 선택 (성능, 속도, 품질 종합 고려)
        best_model_name = None
        best_score = 0
        
        for model_name, results in comparison_results.items():
            if results["success"]:
                # 종합 점수 계산
                quality_score = results["avg_similarity"]
                speed_score = 1 / (1 + results["avg_time"])  # 빠를수록 높은 점수
                
                combined_score = (
                    quality_score * self.config.quality_weight +
                    speed_score * self.config.speed_weight +
                    0.8 * self.config.performance_weight  # 기본 성능 점수
                )
                
                if combined_score > best_score:
                    best_score = combined_score
                    best_model_name = model_name
        
        if not best_model_name:
            best_model_name = "sentence_transformer"  # 기본값
            best_score = 0.7
        
        selection = ComponentSelection(
            component_name="embedding_model",
            selected_option=best_model_name,
            score=best_score,
            reason=f"품질과 속도를 종합적으로 고려한 최적 모델",
            metrics={
                "comparison_results": comparison_results,
                "optimization_target": self.config.optimization_target
            }
        )
        
        logger.info(f"✅ 임베딩 모델 최적화 완료 - {best_model_name} (점수: {best_score:.3f})")
        return selection
    
    async def _setup_vector_store(self, embedding_result: ComponentSelection) -> ComponentSelection:
        """벡터 저장소 구성"""
        
        logger.info("🗄️ 4단계: 벡터 저장소 구성")
        
        # 선택된 임베딩 모델로 벡터 저장소 생성
        embedding_model_name = embedding_result.selected_option
        
        # 임베딩 모델 인스턴스 생성
        embedding_model = self.embedding_comparison.get_model(embedding_model_name)
        
        # 벡터 저장소 생성
        vector_store = WelfareVectorStore(
            persist_directory=os.path.join(self.config.results_directory, "vector_store"),
            collection_name="autorag_optimized",
            embedding_model=embedding_model
        )
        
        # 성능 메트릭 (간단한 추정)
        setup_score = 0.8  # 기본 점수
        
        selection = ComponentSelection(
            component_name="vector_store",
            selected_option="chromadb_with_optimized_embedding",
            score=setup_score,
            reason="선택된 임베딩 모델과 함께 ChromaDB 벡터 저장소 구성",
            metrics={
                "embedding_model": embedding_model_name,
                "persist_directory": vector_store.persist_directory,
                "collection_name": vector_store.collection_name
            }
        )
        
        # 벡터 저장소를 인스턴스 변수로 저장
        self.vector_store = vector_store
        
        logger.info(f"✅ 벡터 저장소 구성 완료 (점수: {setup_score:.3f})")
        return selection
    
    async def _optimize_retriever(self, vector_store_result: ComponentSelection) -> ComponentSelection:
        """검색기 최적화"""
        
        logger.info("🔍 5단계: 검색기 최적화")
        
        # 검색기 비교 시스템 생성
        self.retriever_comparison = RetrieverComparison(
            vector_store=self.vector_store,
            top_k=5
        )
        
        # 평가용 쿼리
        evaluation_queries = self.config.evaluation_queries if self.config.evaluation_queries else [
            "65세 이상 의료비 지원 방법",
            "노인 돌봄 서비스 신청 절차",
            "기초연금 수급 조건"
        ]
        
        # 검색기 성능 평가
        retriever_evaluation = self.retriever_comparison.evaluate_retrievers(evaluation_queries)
        
        # 최적 검색기 선택
        best_retriever = max(retriever_evaluation.items(), key=lambda x: x[1]["overall_score"])
        
        selection = ComponentSelection(
            component_name="retriever",
            selected_option=best_retriever[0],
            score=best_retriever[1]["overall_score"],
            reason="정확도와 재현율을 종합적으로 고려한 최적 검색 방식",
            metrics={
                "all_retrievers": retriever_evaluation,
                "best_retriever_details": best_retriever[1]
            }
        )
        
        logger.info(f"✅ 검색기 최적화 완료 - {best_retriever[0]} (점수: {best_retriever[1]['overall_score']:.3f})")
        return selection
    
    async def _optimize_rag_system(self, retriever_result: ComponentSelection) -> ComponentSelection:
        """RAG 시스템 최적화"""
        
        logger.info("🤖 6단계: RAG 시스템 최적화")
        
        # 최적 검색기 인스턴스 생성
        best_retriever_name = retriever_result.selected_option
        best_retriever = self.retriever_comparison.get_retriever(best_retriever_name)
        
        # RAG 체인 생성
        rag_chain = ElderlyWelfareRAGChain(
            retriever=best_retriever,
            llm_model="gpt-3.5-turbo",
            temperature=0.1,
            max_tokens=1000
        )
        
        # RAG 시스템 평가
        evaluator = RAGEvaluator()
        
        evaluation_results = []
        for query in (self.config.evaluation_queries or ["기초연금이란 무엇인가요?"]):
            try:
                result = rag_chain.ask(query)
                if result["success"]:
                    # 간단한 평가 메트릭
                    relevance_score = 0.8  # 실제로는 더 정교한 평가 필요
                    evaluation_results.append({
                        "query": query,
                        "success": True,
                        "relevance": relevance_score
                    })
            except Exception as e:
                logger.warning(f"RAG 평가 중 오류: {e}")
                evaluation_results.append({
                    "query": query,
                    "success": False,
                    "relevance": 0.0
                })
        
        # 평균 성능 계산
        avg_score = sum(r["relevance"] for r in evaluation_results) / len(evaluation_results) if evaluation_results else 0.5
        
        selection = ComponentSelection(
            component_name="rag_system",
            selected_option="elderly_welfare_rag_chain",
            score=avg_score,
            reason="최적화된 검색기와 LLM을 결합한 RAG 시스템",
            metrics={
                "evaluation_results": evaluation_results,
                "retriever": best_retriever_name,
                "llm_model": "gpt-3.5-turbo"
            }
        )
        
        # RAG 시스템을 인스턴스 변수로 저장
        self.rag_system = rag_chain
        
        logger.info(f"✅ RAG 시스템 최적화 완료 (점수: {avg_score:.3f})")
        return selection
    
    async def _evaluate_final_pipeline(self, rag_result: ComponentSelection) -> Dict[str, Any]:
        """최종 파이프라인 평가"""
        
        logger.info("🏆 7단계: 최종 파이프라인 평가")
        
        # 전체 파이프라인 구성
        pipeline_components = {
            step.component_name: step for step in [
                result for result in self.experiment_results
            ] + [rag_result]
        }
        
        # 종합 성능 점수 계산
        component_scores = [comp.score for comp in pipeline_components.values()]
        overall_score = sum(component_scores) / len(component_scores)
        
        # 워크플로우 시스템 생성
        workflow = ElderlyWelfareWorkflow(
            rag_chain=self.rag_system,
            enable_intent_classification=True,
            enable_relevance_evaluation=True
        )
        
        # 최종 챗봇 시스템 생성
        chatbot = ElderlyWelfareChatbot(
            rag_system=self.rag_system,
            workflow_system=workflow
        )
        
        # 최종 평가
        final_evaluation = []
        test_queries = self.config.evaluation_queries or [
            "65세 이상 노인 의료비 지원에 대해 알려주세요",
            "노인장기요양보험 신청 방법은 무엇인가요?",
            "기초연금 수급 자격과 신청 절차를 설명해주세요"
        ]
        
        for query in test_queries:
            try:
                start_time = time.time()
                response = chatbot.process_message(query, use_workflow=True)
                end_time = time.time()
                
                final_evaluation.append({
                    "query": query,
                    "success": response["success"],
                    "response_time": end_time - start_time,
                    "answer_length": len(response["answer"]),
                    "sources_count": len(response["sources"])
                })
            except Exception as e:
                logger.warning(f"최종 평가 중 오류: {e}")
                final_evaluation.append({
                    "query": query,
                    "success": False,
                    "response_time": 0,
                    "answer_length": 0,
                    "sources_count": 0
                })
        
        # 최종 결과
        final_result = {
            "optimization_complete": True,
            "overall_score": overall_score,
            "pipeline_components": {name: asdict(comp) for name, comp in pipeline_components.items()},
            "final_evaluation": final_evaluation,
            "chatbot_instance": chatbot,
            "recommended_config": self._generate_recommended_config(pipeline_components),
            "optimization_summary": self._generate_optimization_summary(pipeline_components, overall_score)
        }
        
        logger.info(f"✅ 최종 파이프라인 평가 완료 (전체 점수: {overall_score:.3f})")
        return final_result
    
    def _generate_recommended_config(self, components: Dict[str, ComponentSelection]) -> Dict[str, Any]:
        """추천 설정 생성"""
        
        config = {}
        
        for comp_name, comp in components.items():
            config[comp_name] = {
                "selected": comp.selected_option,
                "score": comp.score,
                "reason": comp.reason
            }
        
        return config
    
    def _generate_optimization_summary(self, components: Dict[str, ComponentSelection], overall_score: float) -> str:
        """최적화 요약 리포트 생성"""
        
        summary = [
            "🤖 AutoRAG 파이프라인 최적화 완료",
            "=" * 50,
            f"전체 성능 점수: {overall_score:.3f}/1.0",
            "",
            "📋 최적화된 컴포넌트:",
        ]
        
        for comp_name, comp in components.items():
            summary.append(f"  • {comp_name}: {comp.selected_option} (점수: {comp.score:.3f})")
            summary.append(f"    - {comp.reason}")
        
        summary.extend([
            "",
            "✨ 최적화 효과:",
            f"  • 자동화된 컴포넌트 선택: {len(components)}개",
            f"  • 예상 성능 향상: {(overall_score - 0.5) * 100:.1f}%",
            f"  • 최적화 시간: {time.time() - self.optimization_start:.1f}초" if hasattr(self, 'optimization_start') else "",
            "",
            "🚀 다음 단계:",
            "  1. 생성된 설정으로 챗봇 시스템 배포",
            "  2. 실제 사용자 피드백 수집",
            "  3. 지속적인 성능 모니터링",
            "",
        ])
        
        return "\n".join(summary)
    
    async def _save_optimization_results(self, results: Dict[str, Any], optimization_time: float):
        """최적화 결과 저장"""
        
        # 타임스탬프
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 결과 파일 경로
        results_file = os.path.join(
            self.config.results_directory,
            f"autorag_results_{timestamp}.json"
        )
        
        # 저장할 데이터 준비 (chatbot_instance 제외)
        save_data = {
            "timestamp": timestamp,
            "optimization_time": optimization_time,
            "config": asdict(self.config),
            "overall_score": results["overall_score"],
            "pipeline_components": results["pipeline_components"],
            "final_evaluation": results["final_evaluation"],
            "recommended_config": results["recommended_config"],
            "optimization_summary": results["optimization_summary"]
        }
        
        # JSON 파일로 저장
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"최적화 결과 저장 완료: {results_file}")
    
    def get_progress(self) -> Dict[str, Any]:
        """현재 진행 상황 반환"""
        
        return {
            "current_step": self.current_step,
            "total_steps": self.total_steps,
            "progress_percentage": (self.current_step / self.total_steps) * 100,
            "step_names": [
                "텍스트 추출 최적화",
                "청킹 전략 최적화",
                "임베딩 모델 최적화",
                "벡터 저장소 구성",
                "검색기 최적화",
                "RAG 시스템 최적화",
                "최종 파이프라인 평가"
            ],
            "completed_components": len(self.experiment_results)
        }
    
    def load_previous_results(self, results_file: str) -> Dict[str, Any]:
        """이전 최적화 결과 로드"""
        
        try:
            with open(results_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"결과 파일 로드 실패: {e}")
            return {}


class AutoRAGInterface:
    """AutoRAG 사용자 인터페이스"""
    
    def __init__(self, data_directory: str = "./data/복지로"):
        self.data_directory = data_directory
        self.optimizer = None
        self.config = None
    
    def create_config_interactive(self) -> AutoRAGConfig:
        """대화형 설정 생성"""
        
        print("🤖 AutoRAG 설정 생성")
        print("=" * 30)
        
        # 평가 쿼리 입력
        print("\n1. 평가용 질문들을 입력하세요 (Enter로 완료):")
        evaluation_queries = []
        while True:
            query = input("질문: ").strip()
            if not query:
                break
            evaluation_queries.append(query)
        
        if not evaluation_queries:
            evaluation_queries = [
                "65세 이상 노인 의료비 지원에 대해 알려주세요",
                "노인장기요양보험 신청 방법은?",
                "기초연금 수급 자격은?"
            ]
        
        # 최적화 목표 선택
        print("\n2. 최적화 목표를 선택하세요:")
        print("  1) speed - 빠른 응답 속도 우선")
        print("  2) quality - 높은 답변 품질 우선")
        print("  3) balanced - 균형잡힌 성능")
        
        target_choice = input("선택 (1-3, 기본값: 3): ").strip()
        optimization_target = {"1": "speed", "2": "quality", "3": "balanced"}.get(target_choice, "balanced")
        
        # 자동화 레벨 선택
        print("\n3. 자동화 레벨을 선택하세요:")
        print("  1) manual - 각 단계별 수동 확인")
        print("  2) semi - 일부 단계 자동화")
        print("  3) full - 완전 자동화")
        
        auto_choice = input("선택 (1-3, 기본값: 3): ").strip()
        automation_level = {"1": "manual", "2": "semi", "3": "full"}.get(auto_choice, "full")
        
        # 설정 생성
        config = AutoRAGConfig(
            evaluation_queries=evaluation_queries,
            evaluation_documents=[],
            optimization_target=optimization_target,
            automation_level=automation_level,
            results_directory=f"./autorag_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        
        return config
    
    async def run_optimization(self, config: AutoRAGConfig = None) -> Dict[str, Any]:
        """최적화 실행"""
        
        if config is None:
            config = self.create_config_interactive()
        
        self.config = config
        self.optimizer = AutoRAGOptimizer(config, self.data_directory)
        
        print(f"\n🚀 AutoRAG 최적화 시작")
        print(f"최적화 목표: {config.optimization_target}")
        print(f"자동화 레벨: {config.automation_level}")
        print(f"평가 쿼리 수: {len(config.evaluation_queries)}")
        
        # 최적화 실행
        results = await self.optimizer.optimize_pipeline()
        
        # 결과 출력
        print("\n" + results["optimization_summary"])
        
        return results
    
    def get_optimized_chatbot(self):
        """최적화된 챗봇 반환"""
        
        if self.optimizer and self.optimizer.best_pipeline:
            return self.optimizer.best_pipeline.get("chatbot_instance")
        return None


async def main():
    """AutoRAG 시스템 테스트"""
    
    logging.basicConfig(level=logging.INFO)
    
    print("🤖 AutoRAG 통합 관리 시스템 테스트")
    print("=" * 50)
    
    # AutoRAG 인터페이스 생성
    autorag = AutoRAGInterface()
    
    # 테스트용 설정 생성
    test_config = AutoRAGConfig(
        evaluation_queries=[
            "65세 이상 노인 의료비 지원 제도는?",
            "노인장기요양보험 신청 방법은?",
            "기초연금 수급 자격은?"
        ],
        evaluation_documents=[],
        optimization_target="balanced",
        automation_level="full"
    )
    
    try:
        # 최적화 실행
        results = await autorag.run_optimization(test_config)
        
        # 최적화된 챗봇 테스트
        optimized_chatbot = autorag.get_optimized_chatbot()
        if optimized_chatbot:
            print("\n🤖 최적화된 챗봇 테스트:")
            test_response = optimized_chatbot.process_message("노인복지 정책에 대해 알려주세요")
            print(f"답변: {test_response['answer'][:200]}...")
        
        print(f"\n✅ AutoRAG 시스템 테스트 완료!")
        
    except Exception as e:
        print(f"❌ AutoRAG 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())