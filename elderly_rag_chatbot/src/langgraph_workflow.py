# =========================================
# 🔄 LangGraph 워크플로우 모듈
# =========================================

import os
import logging
from typing import List, Dict, Any, Optional, TypedDict, Annotated
from datetime import datetime
import json

# LangGraph 임포트 (최신 API)
try:
    from langgraph.graph import StateGraph, END
    try:
        from langgraph.checkpoint.memory import MemorySaver
    except ImportError:
        from langgraph.checkpoint import MemorySaver
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    
    # 기본 클래스들 정의 (LangGraph가 없을 때)
    class StateGraph:
        def __init__(self, *args, **kwargs):
            self.nodes = {}
            self.edges = []
        
        def add_node(self, name, func):
            self.nodes[name] = func
            return self
        
        def add_edge(self, from_node, to_node):
            self.edges.append((from_node, to_node))
            return self
            
        def add_conditional_edges(self, *args, **kwargs):
            return self
        
        def compile(self, *args, **kwargs):
            return MockWorkflow(self.nodes)
    
    class END:
        pass
    
    class MemorySaver:
        def __init__(self):
            pass
    
    class MockWorkflow:
        def __init__(self, nodes):
            self.nodes = nodes
        
        def invoke(self, state, config=None):
            return state
        
        def stream(self, state, config=None):
            yield state
    
    class MemorySaver:
        def __init__(self, *args, **kwargs):
            pass

# LangChain 임포트
try:
    from langchain_openai import ChatOpenAI
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import Document
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


# 상태 타입 정의
class WelfareQueryState(TypedDict):
    """복지 정책 질의 상태"""
    question: str
    processed_question: str
    user_intent: str
    retrieved_documents: List[Dict]
    answer: str
    confidence_score: float
    sources: List[Dict]
    follow_up_questions: List[str]
    error_message: str
    step_history: List[str]


class ElderlyWelfareWorkflow:
    """노인복지 정책 전용 LangGraph 워크플로우"""
    
    def __init__(self, 
                 retriever=None, 
                 llm=None,
                 enable_checkpointing: bool = True):
        """
        Args:
            retriever: 문서 검색기
            llm: 언어 모델
            enable_checkpointing: 체크포인트 활성화 여부
        """
        if not LANGGRAPH_AVAILABLE:
            raise ImportError("LangGraph가 설치되지 않았습니다. pip install langgraph")
        
        self.retriever = retriever
        self.enable_checkpointing = enable_checkpointing
        
        # LLM 설정
        if llm is None and LANGCHAIN_AVAILABLE:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.llm = ChatOpenAI(
                    model="gpt-4o-mini",
                    temperature=0.1,
                    openai_api_key=api_key
                )
            else:
                self.llm = None
                logger.warning("OpenAI API 키가 없습니다. 기본 응답을 사용합니다.")
        else:
            self.llm = llm
        
        # 워크플로우 그래프 생성
        self.graph = self._create_workflow()
        
        # 메모리 체크포인터 (선택적)
        self.checkpointer = MemorySaver() if enable_checkpointing else None
        
        # 컴파일된 워크플로우
        self.compiled_workflow = self.graph.compile(checkpointer=self.checkpointer)
        
        logger.info("노인복지 워크플로우 초기화 완료")
    
    def _create_workflow(self) -> StateGraph:
        """LangGraph 워크플로우 생성"""
        
        # 상태 그래프 생성
        workflow = StateGraph(WelfareQueryState)
        
        # 노드 추가
        workflow.add_node("analyze_query", self._analyze_query)
        workflow.add_node("retrieve_documents", self._retrieve_documents)
        workflow.add_node("evaluate_relevance", self._evaluate_relevance)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("enhance_answer", self._enhance_answer)
        workflow.add_node("generate_followup", self._generate_followup)
        
        # 엣지 정의
        workflow.set_entry_point("analyze_query")
        
        workflow.add_edge("analyze_query", "retrieve_documents")
        workflow.add_edge("retrieve_documents", "evaluate_relevance")
        
        # 조건부 엣지 (관련성에 따른 분기)
        workflow.add_conditional_edges(
            "evaluate_relevance",
            self._decide_next_step,
            {
                "generate": "generate_answer",
                "retry": "retrieve_documents",
                "end": END
            }
        )
        
        workflow.add_edge("generate_answer", "enhance_answer")
        workflow.add_edge("enhance_answer", "generate_followup")
        workflow.add_edge("generate_followup", END)
        
        return workflow
    
    def _analyze_query(self, state: WelfareQueryState) -> WelfareQueryState:
        """질의 분석 및 전처리"""
        
        question = state["question"]
        
        # 질의 전처리
        processed_question = question.strip()
        
        # 의도 분석 (간단한 키워드 기반)
        intent = self._classify_intent(processed_question)
        
        # 상태 업데이트
        state["processed_question"] = processed_question
        state["user_intent"] = intent
        state["step_history"] = state.get("step_history", []) + ["analyze_query"]
        
        logger.debug(f"질의 분석 완료: 의도={intent}")
        
        return state
    
    def _classify_intent(self, question: str) -> str:
        """사용자 의도 분류"""
        
        question_lower = question.lower()
        
        # 의도 분류 키워드
        intent_keywords = {
            "medical_support": ["의료비", "진료비", "치료", "병원", "약", "수술"],
            "care_service": ["돌봄", "간병", "요양", "케어", "방문"],
            "living_support": ["생활비", "수당", "연금", "급여", "보조금"],
            "application_process": ["신청", "방법", "절차", "서류", "조건"],
            "housing_support": ["주거", "임대", "주택", "거주"],
            "transportation": ["교통", "이동", "버스", "지하철", "할인"],
            "general_inquiry": ["정보", "안내", "문의", "알려", "설명"]
        }
        
        # 키워드 매칭으로 의도 분류
        for intent, keywords in intent_keywords.items():
            if any(keyword in question_lower for keyword in keywords):
                return intent
        
        return "general_inquiry"
    
    def _retrieve_documents(self, state: WelfareQueryState) -> WelfareQueryState:
        """문서 검색"""
        
        processed_question = state["processed_question"]
        
        try:
            if self.retriever:
                # 리트리버 사용
                docs = self.retriever.get_relevant_documents(processed_question)
                
                # Document 객체를 딕셔너리로 변환
                retrieved_docs = []
                for doc in docs:
                    doc_dict = {
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "source": doc.metadata.get("source", "Unknown")
                    }
                    retrieved_docs.append(doc_dict)
                
            else:
                # 더미 문서 (테스트용)
                retrieved_docs = [
                    {
                        "content": "노인복지 관련 기본 정보입니다.",
                        "metadata": {"source": "default"},
                        "source": "default"
                    }
                ]
            
            state["retrieved_documents"] = retrieved_docs
            state["step_history"].append("retrieve_documents")
            
            logger.debug(f"문서 검색 완료: {len(retrieved_docs)}개 문서")
            
        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            state["error_message"] = f"문서 검색 중 오류: {str(e)}"
            state["retrieved_documents"] = []
        
        return state
    
    def _evaluate_relevance(self, state: WelfareQueryState) -> WelfareQueryState:
        """검색된 문서의 관련성 평가"""
        
        retrieved_docs = state["retrieved_documents"]
        processed_question = state["processed_question"]
        
        if not retrieved_docs:
            state["confidence_score"] = 0.0
            state["step_history"].append("evaluate_relevance")
            return state
        
        # 간단한 관련성 점수 계산 (키워드 기반)
        question_words = set(processed_question.lower().split())
        
        relevance_scores = []
        for doc in retrieved_docs:
            content_words = set(doc["content"].lower().split())
            
            # 자카드 유사도
            intersection = len(question_words.intersection(content_words))
            union = len(question_words.union(content_words))
            jaccard_score = intersection / union if union > 0 else 0
            
            relevance_scores.append(jaccard_score)
            doc["relevance_score"] = jaccard_score
        
        # 전체 신뢰도 점수
        confidence_score = max(relevance_scores) if relevance_scores else 0.0
        
        state["confidence_score"] = confidence_score
        state["step_history"].append("evaluate_relevance")
        
        logger.debug(f"관련성 평가 완료: 신뢰도={confidence_score:.3f}")
        
        return state
    
    def _decide_next_step(self, state: WelfareQueryState) -> str:
        """다음 단계 결정"""
        
        confidence = state["confidence_score"]
        retrieved_docs = state["retrieved_documents"]
        
        # 결정 로직
        if not retrieved_docs:
            return "end"  # 문서가 없으면 종료
        elif confidence < 0.1:
            return "retry"  # 관련성이 너무 낮으면 재검색
        else:
            return "generate"  # 답변 생성
    
    def _generate_answer(self, state: WelfareQueryState) -> WelfareQueryState:
        """답변 생성"""
        
        processed_question = state["processed_question"]
        retrieved_docs = state["retrieved_documents"]
        user_intent = state["user_intent"]
        
        try:
            if self.llm and retrieved_docs:
                # LLM을 사용한 답변 생성
                answer = self._generate_llm_answer(processed_question, retrieved_docs, user_intent)
            else:
                # 기본 답변 생성
                answer = self._generate_basic_answer(processed_question, retrieved_docs)
            
            state["answer"] = answer
            state["step_history"].append("generate_answer")
            
            logger.debug("답변 생성 완료")
            
        except Exception as e:
            logger.error(f"답변 생성 실패: {e}")
            state["answer"] = "죄송합니다. 답변 생성 중 오류가 발생했습니다."
            state["error_message"] = f"답변 생성 오류: {str(e)}"
        
        return state
    
    def _generate_llm_answer(self, question: str, docs: List[Dict], intent: str) -> str:
        """LLM을 사용한 답변 생성"""
        
        # 컨텍스트 준비
        context = "\n\n".join([
            f"[문서 {i+1}] {doc['content']}" 
            for i, doc in enumerate(docs[:3])
        ])
        
        # 의도별 맞춤 프롬프트
        intent_instructions = {
            "medical_support": "의료비 지원 관련 정확한 금액, 대상자 조건, 신청 방법을 포함해 답변하세요.",
            "care_service": "돌봄 서비스의 종류, 이용 방법, 비용 등을 구체적으로 설명하세요.",
            "living_support": "생활비 지원의 금액, 지급 조건, 신청 절차를 명확히 안내하세요.",
            "application_process": "신청에 필요한 서류, 절차, 접수처를 단계별로 설명하세요.",
            "general_inquiry": "제공된 정보를 바탕으로 친절하고 정확하게 안내하세요."
        }
        
        instruction = intent_instructions.get(intent, intent_instructions["general_inquiry"])
        
        # 프롬프트 구성
        prompt = ChatPromptTemplate.from_messages([
            ("system", f"""당신은 노인복지 정책 전문 상담사입니다.

다음 지침을 따라주세요:
1. {instruction}
2. 제공된 문서 정보만을 바탕으로 답변하세요
3. 문서에 없는 내용은 "제공된 자료에서 확인되지 않습니다"라고 명시하세요
4. 존댓말을 사용하고 친근하게 답변하세요
5. 구체적인 수치나 조건이 있으면 정확히 언급하세요

참고 문서:
{context}"""),
            ("human", question)
        ])
        
        # LLM 호출
        response = self.llm.invoke(prompt.format_messages())
        return response.content
    
    def _generate_basic_answer(self, question: str, docs: List[Dict]) -> str:
        """기본 답변 생성 (LLM 없이)"""
        
        if not docs:
            return "죄송합니다. 관련 정보를 찾을 수 없습니다."
        
        # 가장 관련성 높은 문서 선택
        best_doc = max(docs, key=lambda d: d.get("relevance_score", 0))
        
        return f"""다음 정보를 참고하세요:

{best_doc['content'][:500]}

더 자세한 정보가 필요하시면 관련 기관에 문의하시기 바랍니다."""
    
    def _enhance_answer(self, state: WelfareQueryState) -> WelfareQueryState:
        """답변 향상 및 소스 정보 추가"""
        
        retrieved_docs = state["retrieved_documents"]
        
        # 소스 정보 생성
        sources = []
        for i, doc in enumerate(retrieved_docs[:3]):
            source_info = {
                "index": i + 1,
                "content": doc["content"][:200] + "...",
                "source": doc["source"],
                "relevance_score": doc.get("relevance_score", 0)
            }
            sources.append(source_info)
        
        state["sources"] = sources
        state["step_history"].append("enhance_answer")
        
        logger.debug(f"답변 향상 완료: {len(sources)}개 소스")
        
        return state
    
    def _generate_followup(self, state: WelfareQueryState) -> WelfareQueryState:
        """후속 질문 생성"""
        
        user_intent = state["user_intent"]
        answer = state["answer"]
        
        # 의도별 후속 질문 템플릿
        followup_templates = {
            "medical_support": [
                "의료비 지원 신청 방법이 궁금하신가요?",
                "다른 의료 관련 복지 제도도 알아보시겠어요?",
                "의료비 지원 대상자 조건을 확인하고 싶으신가요?"
            ],
            "care_service": [
                "돌봄 서비스 신청 절차가 궁금하신가요?",
                "요양등급 판정에 대해 알아보시겠어요?",
                "다른 돌봄 관련 서비스도 확인하시겠어요?"
            ],
            "living_support": [
                "생활비 지원 신청 방법이 궁금하신가요?",
                "다른 경제적 지원 제도도 알아보시겠어요?",
                "수급 조건을 자세히 확인하고 싶으신가요?"
            ],
            "general_inquiry": [
                "더 자세한 정보가 필요하신가요?",
                "다른 복지 제도도 알아보시겠어요?",
                "신청 방법에 대해 궁금하신가요?"
            ]
        }
        
        followup_questions = followup_templates.get(
            user_intent, 
            followup_templates["general_inquiry"]
        )
        
        state["follow_up_questions"] = followup_questions
        state["step_history"].append("generate_followup")
        
        logger.debug("후속 질문 생성 완료")
        
        return state
    
    def process_query(self, question: str, config: Dict = None) -> Dict[str, Any]:
        """질의 처리 (워크플로우 실행)"""
        
        # 초기 상태 설정
        initial_state = WelfareQueryState(
            question=question,
            processed_question="",
            user_intent="",
            retrieved_documents=[],
            answer="",
            confidence_score=0.0,
            sources=[],
            follow_up_questions=[],
            error_message="",
            step_history=[]
        )
        
        try:
            # 워크플로우 실행
            if config and self.checkpointer:
                result = self.compiled_workflow.invoke(initial_state, config)
            else:
                result = self.compiled_workflow.invoke(initial_state)
            
            # 결과 포맷팅
            response = {
                "question": result["question"],
                "answer": result["answer"],
                "confidence_score": result["confidence_score"],
                "sources": result["sources"],
                "follow_up_questions": result["follow_up_questions"],
                "user_intent": result["user_intent"],
                "step_history": result["step_history"],
                "success": True,
                "timestamp": datetime.now().isoformat()
            }
            
            if result["error_message"]:
                response["error_message"] = result["error_message"]
                response["success"] = False
            
            return response
            
        except Exception as e:
            logger.error(f"워크플로우 실행 실패: {e}")
            return {
                "question": question,
                "answer": f"처리 중 오류가 발생했습니다: {str(e)}",
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_workflow_visualization(self) -> str:
        """워크플로우 시각화 (간단한 텍스트 버전)"""
        
        workflow_steps = [
            "1. 질의 분석 (analyze_query)",
            "2. 문서 검색 (retrieve_documents)",
            "3. 관련성 평가 (evaluate_relevance)",
            "4. 답변 생성 (generate_answer)",
            "5. 답변 향상 (enhance_answer)",
            "6. 후속 질문 생성 (generate_followup)"
        ]
        
        return "\n".join(workflow_steps)


def main():
    """LangGraph 워크플로우 테스트"""
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    print("🔄 LangGraph 워크플로우 테스트")
    print("=" * 50)
    
    if not LANGGRAPH_AVAILABLE:
        print("❌ LangGraph가 설치되지 않았습니다.")
        print("설치 명령어: pip install langgraph")
        return
    
    try:
        # 워크플로우 생성
        print("📝 워크플로우 생성...")
        workflow = ElderlyWelfareWorkflow(
            retriever=None,  # 테스트용 None
            llm=None,        # OpenAI API 없이 테스트
            enable_checkpointing=False
        )
        
        # 워크플로우 시각화
        print(f"\n📊 워크플로우 구조:")
        print(workflow.get_workflow_visualization())
        
        # 질의 처리 테스트
        print(f"\n❓ 질의 처리 테스트...")
        question = "65세 이상 노인 의료비 지원에 대해 알려주세요"
        
        result = workflow.process_query(question)
        
        print(f"\n📋 처리 결과:")
        print(f"  질문: {result['question']}")
        print(f"  답변: {result['answer'][:200]}...")
        print(f"  성공: {result['success']}")
        print(f"  의도: {result['user_intent']}")
        print(f"  신뢰도: {result['confidence_score']:.3f}")
        print(f"  처리 단계: {' -> '.join(result['step_history'])}")
        
        if result['follow_up_questions']:
            print(f"  후속 질문: {result['follow_up_questions'][0]}")
        
        print(f"\n✅ LangGraph 워크플로우 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()