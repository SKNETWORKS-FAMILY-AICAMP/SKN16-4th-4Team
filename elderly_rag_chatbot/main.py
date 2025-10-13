# =========================================
# 🚀 노인복지 정책 RAG 챗봇 메인 실행 스크립트
# =========================================

import os
import sys
import logging
import argparse
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 프로젝트 모듈 임포트
try:
    from config.settings import SystemSettings
    from src.text_extractor import WelfareDocumentExtractor
    from src.text_extraction_comparison import TextExtractionComparison
    from src.chunk_strategy import ChunkStrategyComparator
    from src.embedding_models import EmbeddingModelComparator
    from src.vector_store import WelfareVectorStore
    from src.retriever import RetrieverComparator
    from src.rag_system import ElderlyWelfareRAGChain, MultiRAGSystem
    from src.langgraph_workflow import ElderlyWelfareWorkflow
    from src.chatbot_interface import ElderlyWelfareChatbot, GradioInterface, StreamlitInterface
    from src.autorag_optimizer import AutoRAGOptimizer, AutoRAGInterface, AutoRAGConfig
except ImportError as e:
    print(f"❌ 모듈 임포트 실패: {e}")
    print("필요한 패키지를 설치하고 프로젝트 구조를 확인해주세요.")
    print("다음 명령으로 패키지를 설치하세요: pip install -r requirements.txt")
    sys.exit(1)


class ElderlyRAGChatbotSystem:
    """노인복지 정책 RAG 챗봇 전체 시스템"""
    
    def __init__(self, config_path: Optional[str] = None):
        """시스템 초기화"""
        
        # 설정 로드
        self.settings = SystemSettings()
        if config_path and os.path.exists(config_path):
            self.settings.load_config(config_path)
        
        # 로깅 설정
        self._setup_logging()
        
        # 시스템 컴포넌트
        self.document_extractor = None
        self.chunk_comparison = None
        self.embedding_comparison = None
        self.vector_store = None
        self.retriever_comparison = None
        self.rag_system = None
        self.workflow_system = None
        self.chatbot = None
        
        # 초기화 상태
        self.is_initialized = False
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("노인복지 RAG 챗봇 시스템 초기화")
    
    def _setup_logging(self):
        """로깅 설정"""
        
        # 로그 디렉토리 생성
        os.makedirs(self.settings.logging.log_directory, exist_ok=True)
        
        # 로그 파일 경로
        log_file = os.path.join(
            self.settings.logging.log_directory,
            self.settings.logging.log_file_name
        )
        
        # 로깅 설정
        logging.basicConfig(
            level=getattr(logging, self.settings.logging.log_level),
            format=self.settings.logging.log_format,
            datefmt=self.settings.logging.date_format,
            handlers=[
                logging.FileHandler(log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
    
    async def initialize_system(self, force_rebuild: bool = False) -> bool:
        """전체 시스템 초기화"""
        
        try:
            self.logger.info("🚀 시스템 초기화 시작...")
            
            # 1. 문서 추출기 초기화
            self.logger.info("📄 문서 추출기 초기화...")
            self.document_extractor = WelfareDocumentExtractor(
                data_directory=self.settings.data.data_directory,
                cache_enabled=self.settings.data.enable_document_cache,
                cache_directory=self.settings.data.cache_directory
            )
            
            # 2. 청킹 전략 비교 시스템 초기화
            self.logger.info("✂️ 청킹 전략 시스템 초기화...")
            self.chunk_comparison = ChunkStrategyComparator()
            
            # 3. 임베딩 모델 비교 시스템 초기화
            self.logger.info("🔢 임베딩 모델 시스템 초기화...")
            self.embedding_comparison = EmbeddingModelComparator()
            
            # 4. 벡터 저장소 초기화
            self.logger.info("🗄️ 벡터 저장소 초기화...")
            
            # 최적 임베딩 모델 선택
            recommendation = self.embedding_comparison.get_model_recommendation(priority="balanced")
            best_embedding_model = recommendation.get('recommended_model', 'sentence-transformers/all-MiniLM-L6-v2')
            
            self.vector_store = WelfareVectorStore(
                persist_directory=self.settings.vector_store.persist_directory,
                collection_name=self.settings.vector_store.collection_name,
                embedding_function=best_embedding_model
            )
            
            # 5. 문서 처리 및 벡터화 (필요시)
            if force_rebuild or not self.vector_store.collection.count():
                self.logger.info("📚 문서 처리 및 벡터화...")
                await self._process_documents()
            else:
                self.logger.info("📚 기존 벡터 데이터베이스 사용")
            
            # 6. 검색기 비교 시스템 초기화
            self.logger.info("🔍 검색기 시스템 초기화...")
            self.retriever_comparison = RetrieverComparator()
            
            # 7. RAG 시스템 초기화
            self.logger.info("🤖 RAG 시스템 초기화...")
            
            # 최적 검색기 선택
            # 기본 리트리버 사용 (비교 시스템은 나중에 구현)
            best_retriever = None
            
            self.rag_system = ElderlyWelfareRAGChain(
                retriever=best_retriever,
                llm=None,  # 기본 OpenAI GPT 사용
                memory_k=self.settings.rag.memory_k
            )
            
            # 8. 워크플로우 시스템 초기화
            self.logger.info("🔄 워크플로우 시스템 초기화...")
            self.workflow_system = ElderlyWelfareWorkflow(
                retriever=best_retriever,
                llm=None,  # 더미 모드 사용
                enable_checkpointing=True
            )
            
            # 9. 챗봇 인터페이스 초기화
            self.logger.info("💬 챗봇 인터페이스 초기화...")
            self.chatbot = ElderlyWelfareChatbot(
                rag_system=self.rag_system,
                workflow_system=self.workflow_system
            )
            
            self.is_initialized = True
            self.logger.info("✅ 시스템 초기화 완료!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 초기화 실패: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _process_documents(self):
        """문서 처리 및 벡터화"""
        
        try:
            # 문서 추출
            self.logger.info("문서 추출 중...")
            documents = self.document_extractor.extract_all_documents()
            
            if not documents:
                self.logger.warning("추출된 문서가 없습니다.")
                return
            
            self.logger.info(f"{len(documents)}개 문서 추출 완료")
            
            # 최적 청킹 전략 선택
            self.logger.info("최적 청킹 전략 평가 중...")
            sample_texts = [doc["content"] for doc in documents[:5]]  # 샘플로 평가
            
            chunk_evaluation = self.chunk_comparison.evaluate_strategies(
                sample_texts,
                criteria=["coherence", "coverage", "diversity"]
            )
            
            best_strategy = max(chunk_evaluation.items(), key=lambda x: x[1]["overall_score"])[0]
            self.logger.info(f"최적 청킹 전략: {best_strategy}")
            
            # 문서 청킹
            self.logger.info("문서 청킹 중...")
            chunked_documents = []
            
            for doc in documents:
                chunks = self.chunk_comparison.apply_strategy(
                    best_strategy,
                    doc["content"],
                    metadata={
                        "source": doc["source"],
                        "region": doc.get("region", ""),
                        "document_type": doc.get("document_type", "")
                    }
                )
                chunked_documents.extend(chunks)
            
            self.logger.info(f"{len(chunked_documents)}개 청크 생성 완료")
            
            # 벡터 저장소에 추가
            self.logger.info("벡터 저장소에 문서 추가 중...")
            self.vector_store.add_documents(chunked_documents)
            
            self.logger.info("문서 처리 완료")
            
        except Exception as e:
            self.logger.error(f"문서 처리 실패: {e}")
            raise
    
    def run_evaluation(self) -> Dict[str, Any]:
        """전체 시스템 성능 평가"""
        
        if not self.is_initialized:
            raise ValueError("시스템이 초기화되지 않았습니다.")
        
        self.logger.info("🔍 시스템 성능 평가 시작...")
        
        evaluation_results = {}
        
        try:
            # 1. 청킹 전략 평가
            if self.chunk_comparison:
                self.logger.info("청킹 전략 평가...")
                # 샘플 텍스트로 평가
                sample_docs = self.document_extractor.extract_documents_by_region("전국")[:3]
                if sample_docs:
                    sample_texts = [doc["content"] for doc in sample_docs]
                    chunk_eval = self.chunk_comparison.evaluate_strategies(sample_texts)
                    evaluation_results["chunking"] = chunk_eval
            
            # 2. 임베딩 모델 평가
            if self.embedding_comparison:
                self.logger.info("임베딩 모델 평가...")
                embedding_eval = self.embedding_comparison.compare_models(
                    ["노인 의료비 지원", "돌봄 서비스", "기초연금"]
                )
                evaluation_results["embedding"] = embedding_eval
            
            # 3. 검색기 성능 평가
            if self.retriever_comparison:
                self.logger.info("검색기 성능 평가...")
                retriever_eval = self.retriever_comparison.evaluate_retrievers(
                    ["65세 이상 의료비 지원 방법은?", "노인 돌봄 서비스 신청 절차는?"]
                )
                evaluation_results["retrieval"] = retriever_eval
            
            # 4. RAG 시스템 평가 (간단한 테스트 질문으로)
            if self.rag_system:
                self.logger.info("RAG 시스템 평가...")
                
                test_questions = [
                    "65세 이상 노인 의료비 지원 제도는 무엇인가요?",
                    "노인장기요양보험 신청 방법을 알려주세요.",
                    "독거노인을 위한 돌봄 서비스는 어떤 것들이 있나요?"
                ]
                
                rag_results = []
                for question in test_questions:
                    result = self.rag_system.ask(question)
                    rag_results.append({
                        "question": question,
                        "success": result.get("success", False),
                        "response_length": len(result.get("answer", "")),
                        "sources_count": len(result.get("sources", []))
                    })
                
                evaluation_results["rag_system"] = {
                    "test_results": rag_results,
                    "success_rate": sum(r["success"] for r in rag_results) / len(rag_results),
                    "avg_response_length": sum(r["response_length"] for r in rag_results) / len(rag_results)
                }
            
            self.logger.info("✅ 성능 평가 완료!")
            return evaluation_results
            
        except Exception as e:
            self.logger.error(f"❌ 성능 평가 실패: {e}")
            return {"error": str(e)}
    
    def run_interface(self, interface_type: str = "gradio", **kwargs):
        """사용자 인터페이스 실행"""
        
        if not self.is_initialized:
            raise ValueError("시스템이 초기화되지 않았습니다.")
        
        self.logger.info(f"🌐 {interface_type} 인터페이스 실행...")
        
        try:
            if interface_type.lower() == "gradio":
                gradio_interface = GradioInterface(self.chatbot)
                return gradio_interface.launch(
                    server_name=self.settings.interface.gradio_server_name,
                    server_port=self.settings.interface.gradio_server_port,
                    share=self.settings.interface.gradio_share,
                    debug=self.settings.interface.gradio_debug,
                    **kwargs
                )
            
            elif interface_type.lower() == "streamlit":
                streamlit_interface = StreamlitInterface(self.chatbot)
                return streamlit_interface.run_interface()
            
            else:
                raise ValueError(f"지원하지 않는 인터페이스 타입: {interface_type}")
                
        except Exception as e:
            self.logger.error(f"❌ 인터페이스 실행 실패: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """시스템 상태 정보"""
        
        return {
            "initialized": self.is_initialized,
            "components": {
                "document_extractor": self.document_extractor is not None,
                "chunk_comparison": self.chunk_comparison is not None,
                "embedding_comparison": self.embedding_comparison is not None,
                "vector_store": self.vector_store is not None,
                "retriever_comparison": self.retriever_comparison is not None,
                "rag_system": self.rag_system is not None,
                "workflow_system": self.workflow_system is not None,
                "chatbot": self.chatbot is not None
            },
            "vector_store_count": self.vector_store.collection.count() if self.vector_store else 0,
            "settings": self.settings.get_config_dict()
        }


async def main():
    """메인 실행 함수"""
    
    # 명령줄 인수 파싱
    parser = argparse.ArgumentParser(description="노인복지 정책 RAG 챗봇 시스템")
    
    parser.add_argument(
        "--config", "-c",
        type=str,
        help="설정 파일 경로",
        default=None
    )
    
    parser.add_argument(
        "--interface", "-i",
        type=str,
        choices=["gradio", "streamlit", "none"],
        default="gradio",
        help="인터페이스 타입"
    )
    
    parser.add_argument(
        "--rebuild", "-r",
        action="store_true",
        help="벡터 데이터베이스 재구성"
    )
    
    parser.add_argument(
        "--evaluate", "-e",
        action="store_true",
        help="시스템 성능 평가 실행"
    )
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        help="인터페이스 포트 번호",
        default=None
    )
    
    parser.add_argument(
        "--autorag", "-a",
        action="store_true",
        help="AutoRAG 자동 최적화 실행"
    )
    
    parser.add_argument(
        "--autorag-target",
        type=str,
        choices=["speed", "quality", "balanced"],
        default="balanced",
        help="AutoRAG 최적화 목표"
    )
    
    args = parser.parse_args()
    
    # 시스템 초기화
    print("🚀 노인복지 정책 RAG 챗봇 시스템")
    print("=" * 50)
    
    # AutoRAG 자동 최적화 실행
    if args.autorag:
        print("\n🤖 AutoRAG 자동 최적화 모드")
        print("=" * 30)
        
        try:
            autorag_interface = AutoRAGInterface()
            
            # AutoRAG 설정 생성
            autorag_config = AutoRAGConfig(
                evaluation_queries=[
                    "65세 이상 노인 의료비 지원에 대해 알려주세요",
                    "노인장기요양보험 신청 방법은 무엇인가요?",
                    "기초연금 수급 자격과 신청 절차를 설명해주세요",
                    "독거노인을 위한 돌봄 서비스는 어떤 것이 있나요?",
                    "노인 주거 지원 정책에 대해 설명해주세요"
                ],
                evaluation_documents=[],
                optimization_target=args.autorag_target,
                automation_level="full"
            )
            
            # 자동 최적화 실행
            optimization_results = await autorag_interface.run_optimization(autorag_config)
            
            # 최적화된 챗봇으로 시스템 구성
            optimized_chatbot = autorag_interface.get_optimized_chatbot()
            
            if optimized_chatbot and args.interface != "none":
                print(f"\n🌐 최적화된 {args.interface} 인터페이스 시작...")
                
                if args.interface == "gradio":
                    from src.chatbot_interface import GradioInterface
                    gradio_interface = GradioInterface(optimized_chatbot)
                    gradio_interface.launch(
                        server_port=args.port or 7860,
                        share=False,
                        debug=False
                    )
                elif args.interface == "streamlit":
                    from src.chatbot_interface import StreamlitInterface  
                    streamlit_interface = StreamlitInterface(optimized_chatbot)
                    streamlit_interface.run_interface()
            else:
                print("✅ AutoRAG 최적화 완료. 최적화된 설정이 저장되었습니다.")
            
            return
            
        except Exception as e:
            print(f"❌ AutoRAG 최적화 실패: {e}")
            print("일반 모드로 계속 진행합니다...")
    
    # 일반 시스템 초기화
    system = ElderlyRAGChatbotSystem(config_path=args.config)
    
    # 시스템 초기화
    print("⚙️ 시스템 초기화 중...")
    success = await system.initialize_system(force_rebuild=args.rebuild)
    
    if not success:
        print("❌ 시스템 초기화 실패")
        sys.exit(1)
    
    # 시스템 상태 출력
    status = system.get_system_status()
    print(f"✅ 시스템 초기화 완료")
    print(f"📊 벡터 저장소: {status['vector_store_count']}개 문서")
    
    # 성능 평가 실행
    if args.evaluate:
        print("\n🔍 시스템 성능 평가 중...")
        evaluation_results = system.run_evaluation()
        
        if "error" not in evaluation_results:
            print("✅ 성능 평가 완료")
            
            # 간단한 결과 요약
            if "chunking" in evaluation_results:
                best_chunk = max(evaluation_results["chunking"].items(), 
                               key=lambda x: x[1]["overall_score"])
                print(f"📝 최적 청킹 전략: {best_chunk[0]} (점수: {best_chunk[1]['overall_score']:.3f})")
            
            if "rag_system" in evaluation_results:
                success_rate = evaluation_results["rag_system"]["success_rate"]
                print(f"🤖 RAG 시스템 성공률: {success_rate:.1%}")
        else:
            print(f"❌ 성능 평가 실패: {evaluation_results['error']}")
    
    # 인터페이스 실행
    if args.interface != "none":
        print(f"\n🌐 {args.interface} 인터페이스 시작...")
        
        # 포트 설정
        kwargs = {}
        if args.port:
            if args.interface == "gradio":
                kwargs["server_port"] = args.port
            elif args.interface == "streamlit":
                kwargs["port"] = args.port
        
        try:
            system.run_interface(interface_type=args.interface, **kwargs)
        except KeyboardInterrupt:
            print("\n👋 시스템 종료")
        except Exception as e:
            print(f"\n❌ 인터페이스 실행 실패: {e}")
    else:
        print("\n✅ 시스템 준비 완료 (인터페이스 미실행)")
        print("시스템을 프로그래밍 방식으로 사용하실 수 있습니다.")


if __name__ == "__main__":
    # 비동기 실행
    asyncio.run(main())