# =========================================
# 🤖 RAG 시스템 모듈
# =========================================

import os
import logging
import json
import time
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path

try:
    import numpy as np
except ImportError:
    np = None

# LangChain 임포트
try:
    from langchain.chains import ConversationalRetrievalChain, RetrievalQA
    from langchain.memory import ConversationBufferWindowMemory
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate, ChatPromptTemplate
    from langchain.schema import Document, BaseRetriever
    from langchain.schema.runnable import Runnable
    from langchain.callbacks.manager import CallbackManagerForChainRun
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


class ElderlyWelfareRAGChain:
    """노인복지 정책 전용 RAG 체인"""
    
    def __init__(self, 
                 retriever: BaseRetriever,
                 llm: Optional[Any] = None,
                 memory_k: int = 5):
        """
        Args:
            retriever: 문서 검색기
            llm: 언어 모델 (None이면 OpenAI GPT 사용)
            memory_k: 대화 기록 저장 개수
        """
        self.retriever = retriever
        self.memory_k = memory_k
        
        # LLM 설정
        if llm is None:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                # OpenAI API key가 있을 때만 사용
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.1,
                    max_tokens=1500,
                    openai_api_key=api_key
                )
            else:
                # API key가 없으면 더미 LLM 사용
                self.llm = None
                print("⚠️ OPENAI_API_KEY가 설정되지 않았습니다. 더미 모드로 실행합니다.")
        else:
            self.llm = llm
        
        # 메모리 설정
        self.memory = ConversationBufferWindowMemory(
            k=memory_k,
            memory_key="chat_history",
            return_messages=True,
            output_key="answer"
        )
        
        # 프롬프트 템플릿 설정
        self._setup_prompts()
        
        # 체인 구성
        self._setup_chains()
        
        logger.info("노인복지 RAG 체인 초기화 완료")
    
    def _setup_prompts(self):
        """프롬프트 템플릿 설정"""
        
        # 기본 QA 프롬프트 (대화 기록 없을 때)
        self.qa_prompt = PromptTemplate.from_template(
            """당신은 노인복지 정책 전문 상담사입니다. 제공된 문서를 바탕으로 정확하고 친절하게 답변해주세요.

답변 규칙:
1. 제공된 문서 내용만을 근거로 답변하세요
2. 문서에 없는 내용은 "제공된 자료에서 확인되지 않습니다"라고 명시하세요
3. 구체적인 금액, 조건, 절차가 있다면 정확히 안내하세요
4. 신청 방법이나 문의처가 있다면 함께 안내하세요
5. 존댓말을 사용하고 친근하게 응답하세요

참고 문서:
{context}

질문: {question}

답변:"""
        )
        
        # 대화형 QA 프롬프트 (대화 기록 있을 때)
        self.conversational_prompt = ChatPromptTemplate.from_messages([
            ("system", """당신은 노인복지 정책 전문 상담사입니다. 
            
다음 원칙을 지켜주세요:
- 제공된 문서 내용을 정확히 전달하세요
- 이전 대화 내용을 고려하여 연속성 있게 답변하세요
- 추가 질문이 있으면 자연스럽게 유도하세요
- 복지 혜택을 받기 위한 구체적인 방법을 안내하세요
- 항상 존댓말을 사용하세요

참고 문서:
{context}"""),
            ("human", "{question}")
        ])
    
    def _setup_chains(self):
        """RAG 체인 구성"""
        if not LANGCHAIN_AVAILABLE:
            logger.warning("LangChain을 사용할 수 없습니다. 기본 구현을 사용합니다.")
            self.qa_chain = None
            self.conversational_chain = None
            return
        
        try:
            # 기본 QA 체인
            self.qa_chain = RetrievalQA.from_chain_type(
                llm=self.llm,
                chain_type="stuff",
                retriever=self.retriever,
                chain_type_kwargs={
                    "prompt": self.qa_prompt
                },
                return_source_documents=True
            )
            
            # 대화형 검색 체인
            self.conversational_chain = ConversationalRetrievalChain.from_llm(
                llm=self.llm,
                retriever=self.retriever,
                memory=self.memory,
                combine_docs_chain_kwargs={
                    "prompt": self.conversational_prompt
                },
                return_source_documents=True,
                verbose=False
            )
            
            logger.info("RAG 체인 구성 완료")
            
        except Exception as e:
            logger.error(f"RAG 체인 구성 실패: {e}")
            self.qa_chain = None
            self.conversational_chain = None
    
    def ask(self, 
            question: str, 
            use_conversation: bool = True,
            include_sources: bool = True) -> Dict[str, Any]:
        """질문에 대한 답변 생성"""
        
        # LLM이 없으면 더미 응답
        if self.llm is None:
            return {
                "question": question,
                "answer": f"[더미 모드] 질문: '{question}'에 대한 답변을 생성하려면 OPENAI_API_KEY가 필요합니다.",
                "sources": [],
                "conversation_id": None,
                "timestamp": time.time(),
                "metadata": {"mode": "dummy", "llm_available": False}
            }
        
        try:
            if use_conversation and self.conversational_chain:
                # 대화형 체인 사용
                result = self.conversational_chain({
                    "question": question,
                    "chat_history": self.memory.chat_memory.messages
                })
            elif self.qa_chain:
                # 기본 QA 체인 사용
                result = self.qa_chain({"query": question})
            else:
                # 체인이 없으면 직접 구현
                return self._fallback_answer(question)
            
            # 결과 포맷팅
            answer = result.get("answer", "답변을 생성할 수 없습니다.")
            source_docs = result.get("source_documents", [])
            
            # 소스 정보 정리
            sources = []
            if include_sources and source_docs:
                for i, doc in enumerate(source_docs[:3]):  # 상위 3개만
                    source_info = {
                        "index": i + 1,
                        "content": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content,
                        "metadata": doc.metadata
                    }
                    sources.append(source_info)
            
            return {
                "answer": answer,
                "sources": sources,
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"질문 처리 실패: {e}")
            return {
                "answer": f"죄송합니다. 답변 생성 중 오류가 발생했습니다: {str(e)}",
                "sources": [],
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    def _fallback_answer(self, question: str) -> Dict[str, Any]:
        """체인이 없을 때 사용할 기본 답변 생성"""
        
        try:
            # 리트리버에서 관련 문서 검색
            docs = self.retriever.get_relevant_documents(question)
            
            if not docs:
                return {
                    "answer": "죄송합니다. 관련 정보를 찾을 수 없습니다.",
                    "sources": [],
                    "question": question,
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }
            
            # 간단한 답변 생성 (문서 내용 요약)
            context = "\n\n".join([doc.page_content for doc in docs[:3]])
            
            # LLM 없이 기본 답변
            answer = f"다음 정보를 참고하세요:\n\n{context[:500]}..."
            
            sources = [
                {
                    "index": i + 1,
                    "content": doc.page_content[:200] + "...",
                    "metadata": doc.metadata
                }
                for i, doc in enumerate(docs[:3])
            ]
            
            return {
                "answer": answer,
                "sources": sources,
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Fallback 답변 생성 실패: {e}")
            return {
                "answer": "시스템 오류로 답변할 수 없습니다.",
                "sources": [],
                "question": question,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    def clear_memory(self):
        """대화 기록 초기화"""
        if self.memory:
            self.memory.clear()
            logger.info("대화 기록 초기화 완료")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """대화 기록 조회"""
        if not self.memory:
            return []
        
        history = []
        messages = self.memory.chat_memory.messages
        
        for i in range(0, len(messages), 2):
            if i + 1 < len(messages):
                human_msg = messages[i]
                ai_msg = messages[i + 1]
                
                history.append({
                    "question": human_msg.content,
                    "answer": ai_msg.content,
                    "timestamp": getattr(human_msg, 'timestamp', '')
                })
        
        return history
    
    def save_conversation(self, file_path: str = None) -> str:
        """대화 기록 저장"""
        if file_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"conversation_history_{timestamp}.json"
        
        history = self.get_conversation_history()
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump({
                    "conversation_history": history,
                    "saved_at": datetime.now().isoformat(),
                    "total_exchanges": len(history)
                }, f, ensure_ascii=False, indent=2)
            
            logger.info(f"대화 기록 저장 완료: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"대화 기록 저장 실패: {e}")
            raise


class MultiRAGSystem:
    """다중 RAG 시스템 (여러 리트리버 조합)"""
    
    def __init__(self):
        self.rag_chains = {}
        self.default_chain = None
    
    def register_rag_chain(self, name: str, rag_chain: ElderlyWelfareRAGChain, is_default: bool = False):
        """RAG 체인 등록"""
        self.rag_chains[name] = rag_chain
        
        if is_default or self.default_chain is None:
            self.default_chain = name
        
        logger.info(f"RAG 체인 등록: {name} (기본: {is_default})")
    
    def ask_all(self, question: str) -> Dict[str, Dict[str, Any]]:
        """모든 RAG 체인에서 답변 생성"""
        results = {}
        
        for name, chain in self.rag_chains.items():
            try:
                result = chain.ask(question)
                results[name] = result
            except Exception as e:
                logger.error(f"{name} 체인 실행 실패: {e}")
                results[name] = {
                    "answer": f"오류: {str(e)}",
                    "success": False,
                    "error": str(e)
                }
        
        return results
    
    def ask_best(self, question: str) -> Dict[str, Any]:
        """최적 RAG 체인 선택하여 답변"""
        # 모든 체인에서 답변 생성
        all_results = self.ask_all(question)
        
        # 성공한 결과들만 필터링
        successful_results = {
            name: result for name, result in all_results.items() 
            if result.get('success', False)
        }
        
        if not successful_results:
            return {
                "answer": "모든 시스템에서 답변을 생성할 수 없습니다.",
                "success": False,
                "all_results": all_results
            }
        
        # 소스가 많은 결과 선택 (정보가 풍부한 답변)
        best_name = max(
            successful_results.keys(), 
            key=lambda name: len(successful_results[name].get('sources', []))
        )
        
        best_result = successful_results[best_name]
        best_result['selected_chain'] = best_name
        best_result['all_results'] = all_results
        
        return best_result
    
    def ask(self, question: str, chain_name: str = None) -> Dict[str, Any]:
        """지정된 체인 또는 기본 체인으로 답변"""
        target_chain = chain_name or self.default_chain
        
        if target_chain not in self.rag_chains:
            return {
                "answer": f"지정된 RAG 체인을 찾을 수 없습니다: {target_chain}",
                "success": False,
                "available_chains": list(self.rag_chains.keys())
            }
        
        return self.rag_chains[target_chain].ask(question)


class RAGEvaluator:
    """RAG 시스템 평가 클래스"""
    
    def __init__(self):
        self.test_questions = [
            "65세 이상 노인 의료비 지원 제도에 대해 알려주세요",
            "치매 환자를 위한 돌봄 서비스는 어떤 것이 있나요?",
            "기초생활수급자 노인이 받을 수 있는 혜택은?",
            "노인장기요양보험 신청 방법을 알려주세요",
            "독거노인을 위한 안전확인 서비스가 있나요?"
        ]
    
    def evaluate_rag_chain(self, rag_chain: ElderlyWelfareRAGChain, 
                          custom_questions: List[str] = None) -> Dict[str, Any]:
        """RAG 체인 성능 평가"""
        
        questions = custom_questions or self.test_questions
        results = []
        
        for question in questions:
            try:
                result = rag_chain.ask(question)
                
                # 평가 메트릭 계산
                metrics = self._calculate_metrics(question, result)
                
                evaluation = {
                    "question": question,
                    "answer_length": len(result.get("answer", "")),
                    "source_count": len(result.get("sources", [])),
                    "success": result.get("success", False),
                    "response_time": metrics.get("response_time", 0),
                    "relevance_score": metrics.get("relevance_score", 0)
                }
                
                results.append(evaluation)
                
            except Exception as e:
                logger.error(f"평가 실패 - {question}: {e}")
                results.append({
                    "question": question,
                    "success": False,
                    "error": str(e)
                })
        
        # 전체 통계
        successful_results = [r for r in results if r.get("success", False)]
        
        summary = {
            "total_questions": len(questions),
            "successful_answers": len(successful_results),
            "success_rate": len(successful_results) / len(questions) if questions else 0,
            "avg_answer_length": sum([r["answer_length"] for r in successful_results]) / len(successful_results) if successful_results else 0,
            "avg_source_count": sum([r["source_count"] for r in successful_results]) / len(successful_results) if successful_results else 0,
            "results": results
        }
        
        return summary
    
    def _calculate_metrics(self, question: str, result: Dict[str, Any]) -> Dict[str, float]:
        """답변 품질 메트릭 계산"""
        metrics = {}
        
        # 응답 시간 (실제 측정은 별도 구현 필요)
        metrics["response_time"] = 1.0
        
        # 관련성 점수 (간단한 키워드 매칭 기반)
        answer = result.get("answer", "")
        question_words = set(question.lower().split())
        answer_words = set(answer.lower().split())
        
        if question_words and answer_words:
            intersection = len(question_words.intersection(answer_words))
            union = len(question_words.union(answer_words))
            metrics["relevance_score"] = intersection / union if union > 0 else 0
        else:
            metrics["relevance_score"] = 0
        
        return metrics
    
    def compare_rag_systems(self, rag_systems: Dict[str, ElderlyWelfareRAGChain]) -> Dict[str, Any]:
        """여러 RAG 시스템 비교 평가"""
        
        comparison_results = {}
        
        for name, rag_chain in rag_systems.items():
            logger.info(f"RAG 시스템 평가: {name}")
            evaluation = self.evaluate_rag_chain(rag_chain)
            comparison_results[name] = evaluation
        
        # 전체 비교 요약
        summary = {
            "system_count": len(rag_systems),
            "systems": {}
        }
        
        for name, eval_result in comparison_results.items():
            summary["systems"][name] = {
                "success_rate": eval_result["success_rate"],
                "avg_answer_length": eval_result["avg_answer_length"],
                "avg_source_count": eval_result["avg_source_count"]
            }
        
        # 최고 성능 시스템 선택
        if comparison_results:
            best_system = max(
                comparison_results.keys(),
                key=lambda name: comparison_results[name]["success_rate"]
            )
            summary["best_system"] = best_system
        
        summary["detailed_results"] = comparison_results
        
        return summary


def main():
    """RAG 시스템 테스트"""
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    print("🤖 RAG 시스템 모듈 테스트")
    print("=" * 50)
    
    try:
        # 테스트용 더미 리트리버
        class DummyRetriever:
            def get_relevant_documents(self, query):
                return [
                    Document(
                        page_content="만 65세 이상 노인을 대상으로 의료비를 지원합니다.",
                        metadata={"source": "의료비지원.pdf"}
                    )
                ]
        
        dummy_retriever = DummyRetriever()
        
        # RAG 체인 생성 (LLM 없이)
        print("📝 RAG 체인 생성...")
        rag_chain = ElderlyWelfareRAGChain(
            retriever=dummy_retriever,
            llm=None  # OpenAI API 없이 테스트
        )
        
        # 질문 테스트
        print("❓ 질문 테스트...")
        question = "노인 의료비 지원에 대해 알려주세요"
        result = rag_chain.ask(question)
        
        print(f"질문: {result['question']}")
        print(f"답변: {result['answer'][:200]}...")
        print(f"성공: {result['success']}")
        print(f"소스 개수: {len(result['sources'])}")
        
        # 다중 RAG 시스템 테스트
        print(f"\n🔄 다중 RAG 시스템 테스트...")
        multi_rag = MultiRAGSystem()
        multi_rag.register_rag_chain("default", rag_chain, is_default=True)
        
        result = multi_rag.ask("노인복지 제도는?")
        print(f"다중 RAG 답변: {result['answer'][:100]}...")
        
        print(f"\n✅ RAG 시스템 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()