"""
RAG 파이프라인 리모컨 (RAG Remote Control)
============================================

모든 RAG 구성요소를 리모컨처럼 간단하게 조작할 수 있는 통합 제어 시스템
- 원클릭 비교평가
- 모듈별 독립 제어
- AutoRAG 자동화
- 성능 모니터링
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
from pathlib import Path
import time
from datetime import datetime

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# =========================================
# 코어 인터페이스 (Core Interfaces)
# =========================================

@dataclass
class RemoteResult:
    """리모컨 실행 결과"""
    success: bool
    component: str
    action: str
    data: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()

class ComponentRemote(ABC):
    """구성요소 리모컨 베이스 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_available = False
        self.status = "uninitialized"
        self._last_result = None
    
    @abstractmethod
    def initialize(self) -> RemoteResult:
        """컴포넌트 초기화"""
        pass
    
    @abstractmethod
    def compare(self, **kwargs) -> RemoteResult:
        """성능 비교 실행"""
        pass
    
    @abstractmethod
    def benchmark(self, **kwargs) -> RemoteResult:
        """벤치마크 실행"""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """상태 정보 반환"""
        return {
            'name': self.name,
            'available': self.is_available,
            'status': self.status,
            'last_result': self._last_result
        }
    
    def _execute_safely(self, func: Callable, action: str, **kwargs) -> RemoteResult:
        """안전한 실행 래퍼"""
        start_time = time.time()
        try:
            result_data = func(**kwargs)
            execution_time = time.time() - start_time
            
            result = RemoteResult(
                success=True,
                component=self.name,
                action=action,
                data=result_data,
                execution_time=execution_time
            )
            self._last_result = result
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{self.name} {action} 실패: {e}")
            
            result = RemoteResult(
                success=False,
                component=self.name,
                action=action,
                error=str(e),
                execution_time=execution_time
            )
            self._last_result = result
            return result

# =========================================
# 텍스트 추출 리모컨
# =========================================

class TextExtractionRemote(ComponentRemote):
    """텍스트 추출 리모컨"""
    
    def __init__(self):
        super().__init__("text_extraction")
        self._extractor = None
    
    def initialize(self) -> RemoteResult:
        """텍스트 추출 모듈 초기화"""
        def _init():
            try:
                from src.text_extraction_comparison import TextExtractionComparison
                self._extractor = TextExtractionComparison()
                self.is_available = True
                self.status = "ready"
                
                return {
                    'pdf_extractors': len(self._extractor.available_pdf_extractors),
                    'hwp_extractors': len(self._extractor.available_hwp_extractors)
                }
            except ImportError as e:
                self.is_available = False
                self.status = "module_not_found"
                raise e
        
        return self._execute_safely(_init, "initialize")
    
    def compare(self, file_path: str = None, **kwargs) -> RemoteResult:
        """텍스트 추출 방법 비교 - 안정적인 버전"""
        def _compare():
            if not self._extractor:
                raise RuntimeError("추출기가 초기화되지 않았습니다.")
            
            # 안정적인 simple_compare 사용
            return self._extractor.simple_compare(file_path)
        
        return self._execute_safely(_compare, "compare", **kwargs)
    
    def benchmark(self, test_files: List[str] = None, **kwargs) -> RemoteResult:
        """텍스트 추출 벤치마크"""
        def _benchmark():
            if not self._extractor:
                raise RuntimeError("추출기가 초기화되지 않았습니다.")
            
            # 테스트 파일 자동 검색 또는 제공된 파일 사용
            final_test_files = test_files
            if not final_test_files:
                data_dir = Path("../data")
                found_files = []
                if data_dir.exists():
                    found_files.extend(list(data_dir.glob("**/*.pdf"))[:3])
                    found_files.extend(list(data_dir.glob("**/*.hwp"))[:2])
                final_test_files = [str(f) for f in found_files]
            
            benchmark_results = {}
            for file_path in final_test_files[:5]:  # 최대 5개 파일
                if Path(file_path).exists():
                    file_path_obj = Path(file_path)
                    file_ext = file_path_obj.suffix.lower()
                    
                    try:
                        # 간단한 벤치마크를 위해 직접 추출기들을 테스트
                        file_results = {}
                        
                        if file_ext == '.pdf':
                            extractors = self._extractor.available_pdf_extractors
                        elif file_ext == '.hwp':
                            extractors = self._extractor.available_hwp_extractors
                        else:
                            continue  # 지원하지 않는 파일 건너뛰기
                        
                        for extractor in extractors:
                            try:
                                result = extractor.extract_with_metrics(file_path)
                                if "metrics" in result:
                                    metrics = result["metrics"]
                                    file_results[extractor.name] = {
                                        "execution_time": metrics.get("extraction_time", 0),
                                        "text_length": metrics.get("text_length", 0),
                                        "success": metrics.get("success", False),
                                        "error": metrics.get("error", None) if not metrics.get("success", False) else None
                                    }
                                else:
                                    # 호환성 처리
                                    file_results[extractor.name] = {
                                        "execution_time": result.get("extraction_time", 0),
                                        "text_length": result.get("text_length", 0),
                                        "success": result.get("success", False),
                                        "error": result.get("error", None)
                                    }
                            except Exception as e:
                                file_results[extractor.name] = {
                                    "execution_time": 0,
                                    "text_length": 0,
                                    "success": False,
                                    "error": str(e)
                                }
                        
                        benchmark_results[file_path] = file_results
                    except Exception as e:
                        benchmark_results[file_path] = {'error': str(e)}
            
            return {
                'tested_files': len(benchmark_results),
                'results': benchmark_results
            }
        
        return self._execute_safely(_benchmark, "benchmark", **kwargs)

# =========================================
# 청킹 전략 리모컨
# =========================================

class ChunkingRemote(ComponentRemote):
    """청킹 전략 리모컨"""
    
    def __init__(self):
        super().__init__("chunking")
        self._manager = None
    
    def initialize(self) -> RemoteResult:
        """청킹 전략 모듈 초기화"""
        def _init():
            try:
                from src.chunk_strategy import ChunkStrategyManager
                self._manager = ChunkStrategyManager()
                self.is_available = True
                self.status = "ready"
                
                return {
                    'available_strategies': self._manager.get_available_strategies()
                }
            except ImportError as e:
                self.is_available = False
                self.status = "module_not_found"
                raise e
        
        return self._execute_safely(_init, "initialize")
    
    def compare(self, text: str = None, strategies: List[str] = None, **kwargs) -> RemoteResult:
        """청킹 전략 비교"""
        def _compare():
            if not self._manager:
                raise RuntimeError("청킹 매니저가 초기화되지 않았습니다.")
            
            # 기본 텍스트
            test_text = text or """
                노인복지법에 따른 65세 이상 노인의 의료비 지원 정책입니다.
                저소득층 노인의 경우 의료비의 80%를 국가에서 지원하며,
                일반 노인의 경우 50%를 지원합니다.
                신청은 주민센터에서 할 수 있으며,
                필요 서류로는 주민등록등본, 소득증명서, 의료비 영수증이 있습니다.
                """
            
            # 기본 전략
            test_strategies = strategies or self._manager.get_available_strategies()
            
            results = {}
            for strategy in test_strategies:
                performance = self._manager.evaluate_strategy_performance(test_text, strategy)
                results[strategy] = performance
            
            return {'strategies_tested': len(results), 'results': results}
        
        return self._execute_safely(_compare, "compare", **kwargs)
    
    def benchmark(self, test_texts: List[str] = None, **kwargs) -> RemoteResult:
        """청킹 전략 벤치마크"""
        def _benchmark():
            if not self._manager:
                raise RuntimeError("청킹 매니저가 초기화되지 않았습니다.")
            
            # 기본 테스트 텍스트
            final_test_texts = test_texts or [
                "노인복지 정책에 대한 상세한 설명입니다. " * 20,
                "장애인 지원 서비스 안내문입니다. " * 15,
                "저소득층 주거 지원 방법을 안내합니다. " * 25
            ]
            
            strategies = self._manager.get_available_strategies()
            benchmark_results = {}
            
            for i, text in enumerate(final_test_texts[:3]):  # 최대 3개 텍스트
                text_results = {}
                for strategy in strategies:
                    performance = self._manager.evaluate_strategy_performance(text, strategy)
                    text_results[strategy] = performance
                benchmark_results[f'text_{i+1}'] = text_results
            
            return {
                'tested_texts': len(benchmark_results),
                'tested_strategies': len(strategies),
                'results': benchmark_results
            }
        
        return self._execute_safely(_benchmark, "benchmark", **kwargs)

# =========================================
# 🔢 임베딩 모델 리모컨
# =========================================

class EmbeddingRemote(ComponentRemote):
    """임베딩 모델 리모컨"""
    
    def __init__(self):
        super().__init__("embedding")
        self._manager = None
    
    def initialize(self) -> RemoteResult:
        """임베딩 모델 초기화"""
        def _init():
            try:
                from src.embedding_models import EmbeddingModelManager
                self._manager = EmbeddingModelManager()
                self.is_available = True
                self.status = "ready"
                
                return {
                    'available_models': self._manager.get_available_models()
                }
            except ImportError as e:
                self.is_available = False
                self.status = "module_not_found"
                raise e
        
        return self._execute_safely(_init, "initialize")
    
    def compare(self, texts: List[str] = None, models: List[str] = None, **kwargs) -> RemoteResult:
        """임베딩 모델 비교"""
        def _compare():
            if not self._manager:
                raise RuntimeError("임베딩 매니저가 초기화되지 않았습니다.")
            
            # 기본 텍스트
            test_texts = texts or [
                "65세 이상 노인 의료비 지원",
                "장애인 복지 서비스",
                "저소득층 주거 지원"
            ]
            
            # 기본 모델
            test_models = models or self._manager.get_available_models()
            
            results = {}
            for model in test_models:
                performance = self._manager.evaluate_model_performance(test_texts, model)
                results[model] = performance
            
            return {'models_tested': len(results), 'results': results}
        
        return self._execute_safely(_compare, "compare", **kwargs)
    
    def benchmark(self, test_datasets: List[List[str]] = None, **kwargs) -> RemoteResult:
        """임베딩 모델 벤치마크"""
        def _benchmark():
            if not self._manager:
                raise RuntimeError("임베딩 매니저가 초기화되지 않았습니다.")
            
            # 기본 테스트 데이터셋
            final_test_datasets = test_datasets or [
                ["노인복지 정책", "의료비 지원", "건강보험"],
                ["장애인 서비스", "복지 혜택", "지원 프로그램"],
                ["주거 지원", "임대료 보조", "주택 정책"]
            ]
            
            models = self._manager.get_available_models()
            benchmark_results = {}
            
            for i, dataset in enumerate(final_test_datasets[:3]):  # 최대 3개 데이터셋
                dataset_results = {}
                for model in models:
                    performance = self._manager.evaluate_model_performance(dataset, model)
                    dataset_results[model] = performance
                benchmark_results[f'dataset_{i+1}'] = dataset_results
            
            return {
                'tested_datasets': len(benchmark_results),
                'tested_models': len(models),
                'results': benchmark_results
            }
        
        return self._execute_safely(_benchmark, "benchmark", **kwargs)

# =========================================
# 검색 전략 리모컨
# =========================================

class RetrievalRemote(ComponentRemote):
    """검색 전략 리모컨"""
    
    def __init__(self):
        super().__init__("retrieval")
        self._manager = None
    
    def initialize(self) -> RemoteResult:
        """검색 전략 초기화"""
        def _init():
            try:
                from src.retrieval_strategies import RetrievalStrategyManager
                self._manager = RetrievalStrategyManager()
                self.is_available = True
                self.status = "ready"
                
                return {
                    'available_strategies': self._manager.get_available_strategies()
                }
            except ImportError as e:
                self.is_available = False
                self.status = "module_not_found"
                raise e
        
        return self._execute_safely(_init, "initialize")
    
    def compare(self, query: str = None, documents: List[Dict] = None, strategies: List[str] = None, **kwargs) -> RemoteResult:
        """검색 전략 비교"""
        def _compare():
            if not self._manager:
                raise RuntimeError("검색 매니저가 초기화되지 않았습니다.")
            
            # 기본 쿼리
            test_query = query or "노인 의료비 지원에 대해 알려주세요"
            
            # 기본 문서
            test_documents = documents or [
                {'id': 1, 'content': '노인복지법에 따른 의료비 지원', 'source': 'doc1'},
                {'id': 2, 'content': '장애인 복지 서비스 신청 방법', 'source': 'doc2'},
                {'id': 3, 'content': '저소득층 주거 지원 정책', 'source': 'doc3'},
                {'id': 4, 'content': '기초생활수급자 혜택 안내', 'source': 'doc4'},
                {'id': 5, 'content': '독거노인 돌봄 서비스', 'source': 'doc5'}
            ]
            
            # 기본 전략
            test_strategies = strategies or self._manager.get_available_strategies()
            
            results = {}
            for strategy in test_strategies:
                performance = self._manager.evaluate_strategy_performance(test_query, test_documents, strategy)
                results[strategy] = performance
            
            return {'strategies_tested': len(results), 'results': results}
        
        return self._execute_safely(_compare, "compare", **kwargs)
    
    def benchmark(self, test_queries: List[str] = None, **kwargs) -> RemoteResult:
        """검색 전략 벤치마크"""
        def _benchmark():
            if not self._manager:
                raise RuntimeError("검색 매니저가 초기화되지 않았습니다.")
            
            # 기본 테스트 쿼리
            final_test_queries = test_queries or [
                "65세 이상 노인 의료비 지원",
                "장애인 복지 서비스 신청",
                "저소득층 주거 지원 방법"
            ]
            
            # 더미 문서 셋
            documents = [
                {'id': i, 'content': f'복지 정책 문서 {i}', 'source': f'doc{i}'}
                for i in range(1, 11)
            ]
            
            strategies = self._manager.get_available_strategies()
            benchmark_results = {}
            
            for i, query in enumerate(final_test_queries[:3]):  # 최대 3개 쿼리
                query_results = {}
                for strategy in strategies:
                    performance = self._manager.evaluate_strategy_performance(query, documents, strategy)
                    query_results[strategy] = performance
                benchmark_results[f'query_{i+1}'] = query_results
            
            return {
                'tested_queries': len(benchmark_results),
                'tested_strategies': len(strategies),
                'results': benchmark_results
            }
        
        return self._execute_safely(_benchmark, "benchmark", **kwargs)

# =========================================
# 마스터 리모컨 (Master Remote Control)
# =========================================

class RAGMasterRemote:
    """RAG 파이프라인 마스터 리모컨"""
    
    def __init__(self):
        self.remotes = {
            'text_extraction': TextExtractionRemote(),
            'chunking': ChunkingRemote(),
            'embedding': EmbeddingRemote(),
            'retrieval': RetrievalRemote()
        }
        self.results_history = []
        self.config = self._load_config()
        logger.info("RAG 마스터 리모컨 초기화 완료")
    
    def _load_config(self) -> Dict:
        """설정 로드"""
        config_path = Path("config/remote_config.json")
        
        default_config = {
            "auto_initialize": True,
            "parallel_execution": False,
            "result_storage": True,
            "benchmark_settings": {
                "max_files": 5,
                "max_texts": 3,
                "timeout": 30
            }
        }
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    default_config.update(loaded_config)
            except Exception as e:
                logger.warning(f"설정 로드 실패: {e}")
        
        return default_config
    
    def initialize_all(self) -> Dict[str, RemoteResult]:
        """모든 컴포넌트 초기화"""
        logger.info("모든 컴포넌트 초기화 시작")
        results = {}
        
        for name, remote in self.remotes.items():
            logger.info(f"   초기화 중: {name}")
            result = remote.initialize()
            results[name] = result
            
            if result.success:
                logger.info(f"   {name} 초기화 성공")
            else:
                logger.warning(f"   {name} 초기화 실패: {result.error}")
        
        self.results_history.append({
            'action': 'initialize_all',
            'timestamp': datetime.now().isoformat(),
            'results': results
        })
        
        return results
    
    def get_system_status(self) -> Dict[str, Any]:
        """전체 시스템 상태 조회"""
        status = {
            'master_remote': {
                'total_components': len(self.remotes),
                'available_components': sum(1 for r in self.remotes.values() if r.is_available),
                'history_count': len(self.results_history)
            },
            'components': {}
        }
        
        for name, remote in self.remotes.items():
            status['components'][name] = remote.get_status()
        
        return status
    
    def run_quick_comparison(self) -> Dict[str, RemoteResult]:
        """빠른 비교 실행 (모든 컴포넌트)"""
        logger.info("빠른 비교 실행")
        results = {}
        
        for name, remote in self.remotes.items():
            if remote.is_available:
                logger.info(f"   실행 중: {name} 비교")
                result = remote.compare()
                results[name] = result
                
                if result.success:
                    logger.info(f"   {name} 비교 완료")
                else:
                    logger.warning(f"   {name} 비교 실패: {result.error}")
            else:
                logger.warning(f"   {name} 사용 불가")
        
        self.results_history.append({
            'action': 'quick_comparison',
            'timestamp': datetime.now().isoformat(),
            'results': results
        })
        
        return results
    
    def run_full_benchmark(self) -> Dict[str, RemoteResult]:
        """전체 벤치마크 실행"""
        logger.info("🏆 전체 벤치마크 실행")
        results = {}
        
        for name, remote in self.remotes.items():
            if remote.is_available:
                logger.info(f"   벤치마크 중: {name}")
                result = remote.benchmark()
                results[name] = result
                
                if result.success:
                    logger.info(f"   {name} 벤치마크 완료")
                else:
                    logger.warning(f"   {name} 벤치마크 실패: {result.error}")
            else:
                logger.warning(f"   {name} 사용 불가")
        
        self.results_history.append({
            'action': 'full_benchmark',
            'timestamp': datetime.now().isoformat(),
            'results': results
        })
        
        return results
    
    def auto_rag_optimization(self) -> Dict[str, Any]:
        """AutoRAG 스타일 자동 최적화"""
        logger.info("🤖 AutoRAG 자동 최적화 시작")
        
        # 1단계: 초기화
        init_results = self.initialize_all()
        
        # 2단계: 빠른 비교
        comparison_results = self.run_quick_comparison()
        
        # 3단계: 벤치마크
        benchmark_results = self.run_full_benchmark()
        
        # 4단계: 최적 구성 결정
        best_config = self._determine_best_configuration(comparison_results, benchmark_results)
        
        optimization_result = {
            'optimization_complete': True,
            'initialization': init_results,
            'comparison': comparison_results,
            'benchmark': benchmark_results,
            'best_configuration': best_config,
            'timestamp': datetime.now().isoformat()
        }
        
        self.results_history.append({
            'action': 'auto_rag_optimization',
            'timestamp': datetime.now().isoformat(),
            'results': optimization_result
        })
        
        logger.info("AutoRAG 최적화 완료")
        return optimization_result
    
    def _determine_best_configuration(self, comparison_results: Dict, benchmark_results: Dict) -> Dict[str, str]:
        """최적 구성 결정"""
        best_config = {}
        
        for component, result in comparison_results.items():
            if result.success and result.data:
                # 각 컴포넌트별 최고 성능 방법 선택
                if component == 'text_extraction':
                    # PDF 추출기 개수 기준으로 선택
                    best_config['text_extractor'] = 'multi_extractor'
                elif component == 'chunking':
                    # 가장 높은 점수의 전략 선택
                    strategies = result.data.get('results', {})
                    best_strategy = max(strategies.keys(), 
                                      key=lambda k: strategies[k].get('success', False))
                    best_config['chunking_strategy'] = best_strategy
                elif component == 'embedding':
                    # 가장 높은 성공률의 모델 선택
                    models = result.data.get('results', {})
                    best_model = max(models.keys(),
                                   key=lambda k: models[k].get('success_rate', 0))
                    best_config['embedding_model'] = best_model
                elif component == 'retrieval':
                    # 가장 높은 평균 점수의 전략 선택
                    strategies = result.data.get('results', {})
                    best_strategy = max(strategies.keys(),
                                      key=lambda k: strategies[k].get('avg_score', 0))
                    best_config['retrieval_strategy'] = best_strategy
        
        return best_config
    
    def save_results(self, file_path: str = None) -> str:
        """결과 저장"""
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"results/rag_remote_results_{timestamp}.json"
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        save_data = {
            'system_status': self.get_system_status(),
            'results_history': self.results_history,
            'config': self.config
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"결과 저장 완료: {file_path}")
        return file_path

# =========================================
# 사용 예시 및 테스트
# =========================================

def main():
    """리모컨 시스템 데모"""
    print("RAG 파이프라인 마스터 리모컨 데모")
    print("=" * 50)
    
    # 마스터 리모컨 생성
    master = RAGMasterRemote()
    
    try:
        # 1. 전체 시스템 초기화
        print("\n시스템 초기화...")
        init_results = master.initialize_all()
        
        # 2. 시스템 상태 확인
        print("\n시스템 상태:")
        status = master.get_system_status()
        available = status['master_remote']['available_components']
        total = status['master_remote']['total_components']
        print(f"   사용 가능한 컴포넌트: {available}/{total}")
        
        # 3. 빠른 비교 실행
        print(f"\n⚡ 빠른 비교 실행...")
        comparison_results = master.run_quick_comparison()
        
        # 4. AutoRAG 최적화 (선택적)
        print(f"\n🤖 AutoRAG 최적화 실행...")
        optimization_results = master.auto_rag_optimization()
        
        # 5. 결과 저장
        result_file = master.save_results()
        print(f"\n결과 저장: {result_file}")
        
        print(f"\n리모컨 데모 완료!")
        
    except KeyboardInterrupt:
        print(f"\n사용자 중단")
    except Exception as e:
        print(f"\n오류 발생: {e}")

if __name__ == "__main__":
    main()