"""
LangGraph를 사용한 고급 RAG 시스템
"""

from typing import TypedDict, List, Dict
from langchain_core.messages import HumanMessage, AIMessage


class GraphState(TypedDict):
    """그래프 상태"""
    question: str
    user_profile: Dict
    retrieved_docs: List[Dict]
    context: str
    answer: str
    quality_score: float


class LangGraphRAG:
    """LangGraph 기반 향상된 RAG 시스템"""

    def __init__(self, vectorstore, embedder):
        self.vectorstore = vectorstore
        self.embedder = embedder

    def retrieve_documents(self, state: GraphState) -> GraphState:
        """문서 검색 노드"""
        question = state['question']
        user_profile = state.get('user_profile')

        # 사용자 프로필 기반 쿼리 향상
        enhanced_query = question
        if user_profile:
            profile_context = []
            if user_profile.get('age'):
                profile_context.append(f"{user_profile['age']}세")
            if user_profile.get('region'):
                profile_context.append(f"{user_profile['region']} 지역")
            if user_profile.get('disability'):
                profile_context.append("장애인")
            if user_profile.get('veteran'):
                profile_context.append("보훈 대상자")
            if user_profile.get('low_income'):
                profile_context.append("저소득층")

            if profile_context:
                enhanced_query = f"{question} (대상: {', '.join(profile_context)})"

        # 임베딩 및 검색
        query_embedding = self.embedder.embed_query(enhanced_query)
        results = self.vectorstore.search(query_embedding, n_results=5)

        retrieved_docs = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"],
            results["metadatas"],
            results["distances"]
        )):
            retrieved_docs.append({
                "rank": i + 1,
                "content": doc,
                "file_name": metadata["file_name"],
                "similarity_score": 1 - distance
            })

        state['retrieved_docs'] = retrieved_docs
        return state

    def rerank_documents(self, state: GraphState) -> GraphState:
        """문서 재순위화 노드 - 더 관련성 높은 문서 선별"""
        docs = state['retrieved_docs']

        # 간단한 재순위화: 유사도 점수 기반
        # 실제로는 더 복잡한 알고리즘 사용 가능
        docs.sort(key=lambda x: x['similarity_score'], reverse=True)

        # 상위 3개만 선택
        state['retrieved_docs'] = docs[:3]
        return state

    def generate_context(self, state: GraphState) -> GraphState:
        """컨텍스트 생성 노드"""
        docs = state['retrieved_docs']

        context_parts = []
        for doc in docs:
            context_parts.append(f"[출처: {doc['file_name']}]\n{doc['content'][:800]}")

        state['context'] = "\n\n---\n\n".join(context_parts)
        return state

    def generate_answer(self, state: GraphState) -> GraphState:
        """답변 생성 노드"""
        question = state['question']
        context = state['context']
        docs = state['retrieved_docs']

        # 간단한 답변 생성 (실제로는 LLM 사용)
        answer = f"질문: {question}\n\n"
        answer += "관련 정책 정보를 찾았습니다:\n\n"

        for i, doc in enumerate(docs, 1):
            answer += f"{i}. {doc['file_name']}\n"
            answer += f"   관련도: {doc['similarity_score']:.2%}\n"
            answer += f"   내용: {doc['content'][:300]}...\n\n"

        answer += "\n더 자세한 정보는 해당 정책 문서를 참고하시거나 복지로 웹사이트를 방문해주세요."

        state['answer'] = answer
        return state

    def evaluate_quality(self, state: GraphState) -> GraphState:
        """답변 품질 평가 노드"""
        docs = state['retrieved_docs']

        # 간단한 품질 점수 계산
        if docs:
            avg_similarity = sum(d['similarity_score'] for d in docs) / len(docs)
            quality_score = avg_similarity * 100
        else:
            quality_score = 0

        state['quality_score'] = quality_score
        return state

    def should_rerank(self, state: GraphState) -> str:
        """재순위화 필요 여부 결정"""
        docs = state['retrieved_docs']
        if len(docs) > 3 and docs[0]['similarity_score'] < 0.7:
            return "rerank"
        return "generate"

    def run(self, question: str, user_profile: Dict = None) -> Dict:
        """RAG 파이프라인 실행"""
        # 초기 상태
        state = GraphState(
            question=question,
            user_profile=user_profile or {},
            retrieved_docs=[],
            context="",
            answer="",
            quality_score=0.0
        )

        # 순차적 실행
        state = self.retrieve_documents(state)
        state = self.rerank_documents(state)
        state = self.generate_context(state)
        state = self.generate_answer(state)
        state = self.evaluate_quality(state)

        return {
            'answer': state['answer'],
            'sources': [d['file_name'] for d in state['retrieved_docs']],
            'quality_score': state['quality_score'],
            'retrieved_docs': state['retrieved_docs']
        }
