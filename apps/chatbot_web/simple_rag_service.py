"""
간소화된 RAG 서비스
- 사전 구축된 벡터 DB 로딩
- .env 기반 설정
- 리트리버 + GPT API 하이브리드
- 자연스러운 응답 생성
"""

import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)


class SimpleRAGService:
    """간단한 RAG 서비스"""

    def __init__(self):
        """환경변수 기반 초기화"""
        # 환경변수 로드
        self.embedding_model = os.getenv('EMBEDDING_MODEL', 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
        self.embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'huggingface')
        self.chroma_persist_dir = os.getenv('CHROMA_PERSIST_DIR', 'chromadb_storage')
        self.chunk_size = int(os.getenv('CHUNK_SIZE', '1000'))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', '200'))
        self.top_k = int(os.getenv('TOP_K_RESULTS', '5'))

        # OpenAI 설정
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.openai_model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        self.temperature = float(os.getenv('OPENAI_TEMPERATURE', '0.7'))
        self.max_tokens = int(os.getenv('OPENAI_MAX_TOKENS', '2000'))

        # 임베딩 모델 초기화
        self.embeddings = self._initialize_embeddings()

        # 벡터스토어 로드
        self.vectorstore = self._load_vectorstore()

        # LLM 초기화
        self.llm = self._initialize_llm()

        logger.info("SimpleRAGService 초기화 완료")

    def _initialize_embeddings(self):
        """임베딩 모델 초기화"""
        if self.embedding_provider == 'openai':
            if not self.openai_api_key:
                raise ValueError("OPENAI_API_KEY가 설정되지 않았습니다.")
            return OpenAIEmbeddings(
                model=self.embedding_model,
                openai_api_key=self.openai_api_key
            )
        else:
            # HuggingFace 임베딩 (기본값)
            return HuggingFaceEmbeddings(
                model_name=self.embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )

    def _load_vectorstore(self) -> Optional[Chroma]:
        """사전 구축된 벡터스토어 로드"""
        persist_dir = Path(self.chroma_persist_dir)

        if not persist_dir.exists():
            logger.warning(f"벡터 DB가 없습니다: {persist_dir}")
            logger.warning("먼저 'python manage.py load_welfare_documents'를 실행하여 DB를 생성하세요.")
            return None

        try:
            vectorstore = Chroma(
                persist_directory=str(persist_dir),
                embedding_function=self.embeddings,
                collection_name='elderly_welfare_docs'
            )

            # 벡터스토어 검증
            count = vectorstore._collection.count()
            logger.info(f"벡터 DB 로드 완료: {count}개 문서")

            return vectorstore
        except Exception as e:
            logger.error(f"벡터 DB 로드 실패: {e}")
            return None

    def _initialize_llm(self):
        """OpenAI LLM 초기화"""
        if not self.openai_api_key:
            logger.warning("OPENAI_API_KEY가 없습니다. GPT 답변 보강 기능이 비활성화됩니다.")
            return None

        return ChatOpenAI(
            model=self.openai_model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            openai_api_key=self.openai_api_key
        )

    def retrieve_documents(self, query: str, k: Optional[int] = None) -> List[Document]:
        """문서 검색"""
        if not self.vectorstore:
            return []

        k = k or self.top_k

        try:
            # 먼저 벡터 기반 검색 수행
            try:
                vector_results = self.vectorstore.similarity_search_with_score(query, k=k)
                # vector_results: list of (Document, score) where score higher = more similar (depends on vectorstore impl)
                docs = [doc for doc, _ in vector_results]
            except Exception:
                # Fallback: some vectorstore wrappers only provide similarity_search
                docs = self.vectorstore.similarity_search(query, k=k)
                # synthesize coarse semantic scores (descending)
                vector_results = []
                total = len(docs)
                for idx, d in enumerate(docs):
                    # higher score for earlier results
                    score = float(max(0.0, (total - idx)))
                    vector_results.append((d, score))

            # 시맨틱(벡터) 점수와 레키컬(텍스트) 점수의 하이브리드 리랭킹
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                from sklearn.metrics.pairwise import cosine_similarity

                # Prepare corpus: use returned docs' page_content
                corpus = [d.page_content for d in docs]
                if corpus and len(corpus) > 0:
                    tfidf = TfidfVectorizer().fit(corpus + [query])
                    corpus_vecs = tfidf.transform(corpus)
                    query_vec = tfidf.transform([query])
                    lexical_sims = cosine_similarity(query_vec, corpus_vecs).flatten()
                else:
                    lexical_sims = [0.0] * len(docs)
            except Exception:
                # If sklearn not available or fails, treat lexical sims as zeros
                lexical_sims = [0.0] * len(docs)

            # extract semantic scores (normalize to 0-1)
            semantic_scores = []
            for _, score in vector_results:
                try:
                    s = float(score)
                except Exception:
                    s = 0.0
                semantic_scores.append(s)

            # normalize semantic and lexical scores
            import numpy as _np
            sem = _np.array(semantic_scores, dtype=float)
            lex = _np.array(lexical_sims, dtype=float)

            def _normalize(arr):
                if arr.size == 0:
                    return arr
                minv = arr.min()
                maxv = arr.max()
                if maxv - minv <= 1e-12:
                    return _np.ones_like(arr)
                return (arr - minv) / (maxv - minv)

            sem_n = _normalize(sem)
            lex_n = _normalize(lex)

            weight = float(os.getenv('HYBRID_RERANK_WEIGHT', '0.7'))
            # semantic:lexical = weight : (1-weight)
            hybrid_scores = weight * sem_n + (1.0 - weight) * lex_n

            # sort by hybrid_scores desc and return top k documents
            idx_sorted = _np.argsort(-hybrid_scores)
            sorted_docs = [docs[i] for i in idx_sorted]
            logger.info(f"Hybrid rerank applied (w={weight}), returned {len(sorted_docs)} docs")
            return sorted_docs[:k]
        except Exception as e:
            logger.error(f"문서 검색 실패: {e}")
            return []

    def _is_greeting(self, query: str) -> bool:
        """인사말인지 확인"""
        greetings = [
            'ㅎㅇ', '안녕', '안녕하세요', '반갑', '처음', 'hi', 'hello',
            '하이', '헬로', '굿모닝', '좋은아침', '좋은 아침', '잘자',
            '굿나잇', '굿밤', '좋은밤', '좋은 밤', '감사', '고마워',
            '고맙', '땡큐', 'thank', 'thanks'
        ]
        query_lower = query.lower().strip()
        return any(greeting in query_lower for greeting in greetings) or len(query_lower) <= 3

    def _is_relevant_question(self, query: str) -> bool:
        """복지 정책 관련 질문인지 확인"""
        welfare_keywords = [
            '복지', '정책', '지원', '급여', '수당', '연금', '의료', '건강',
            '노인', '어르신', '장애인', '주거', '일자리', '문화', '여가',
            '돌봄', '요양', '간병', '생활', '보조', '혜택', '신청', '자격',
            '기초', '국민', '서비스', '프로그램', '사업'
        ]

        query_lower = query.lower()
        return any(keyword in query_lower for keyword in welfare_keywords)

    def generate_answer(self, query: str, user_region: Optional[str] = None) -> Dict[str, Any]:
        """
        질의응답 생성 (리트리버 + GPT 하이브리드)

        Returns:
            {
                'answer': str,
                'sources': List[Dict],
                'retrieved_count': int,
                'used_gpt': bool
            }
        """
        # 1. 인사말 확인
        if self._is_greeting(query):
            greeting_response = """안녕하세요! 노인 복지 정책 안내 챗봇입니다. 😊

저는 노인 복지 정책, 지원 프로그램, 신청 방법 등에 대해 도움을 드릴 수 있습니다.

궁금하신 복지 정책이나 지원 프로그램에 대해 자유롭게 질문해 주세요!

예를 들면:
- 기초연금은 누가 받을 수 있나요?
- 노인 장기요양보험 신청 방법을 알려주세요
- 우리 지역에는 어떤 복지 정책이 있나요?"""
            return {
                'answer': greeting_response,
                'sources': [],
                'retrieved_count': 0,
                'used_gpt': False,
                'is_greeting': True
            }

        # 2. 관련성 검사
        if not self._is_relevant_question(query):
            return {
                'answer': '죄송합니다. 저는 노인 복지 정책에 대해서만 답변을 드릴 수 있어요. 복지 정책, 지원 프로그램, 신청 방법 등에 대해 물어봐 주세요. 😊',
                'sources': [],
                'retrieved_count': 0,
                'used_gpt': False,
                'is_off_topic': True
            }

        # 2. 문서 검색
        retrieved_docs = self.retrieve_documents(query)

        if not retrieved_docs:
            return {
                'answer': '죄송합니다. 관련된 복지 정책 정보를 찾을 수 없습니다. 다른 방식으로 질문해 주시거나, 관리자에게 문의해 주세요.',
                'sources': [],
                'retrieved_count': 0,
                'used_gpt': False,
                'no_documents': True
            }

        # 3. 검색된 문서 정보 구성
        sources = []
        context_parts = []

        for i, doc in enumerate(retrieved_docs, 1):
            metadata = doc.metadata
            source_info = {
                'index': i,
                'content': doc.page_content[:200] + '...',
                'region': metadata.get('region', '전국'),
                'source': metadata.get('source', 'Unknown')
            }
            sources.append(source_info)

            # 컨텍스트 구성
            region_tag = f"[{metadata.get('region', '전국')}]"
            context_parts.append(f"{region_tag} {doc.page_content}")

        context = "\n\n".join(context_parts)

        # 4. GPT로 답변 생성
        if self.llm:
            try:
                answer = self._generate_gpt_answer(query, context, user_region)
                used_gpt = True
            except Exception as e:
                logger.error(f"GPT 답변 생성 실패: {e}")
                # GPT 실패 시 검색된 문서 요약 반환
                answer = self._generate_simple_answer(retrieved_docs, user_region)
                used_gpt = False
        else:
            answer = self._generate_simple_answer(retrieved_docs, user_region)
            used_gpt = False

        return {
            'answer': answer,
            'sources': sources,
            'retrieved_count': len(retrieved_docs),
            'used_gpt': used_gpt
        }

    def _generate_gpt_answer(self, query: str, context: str, user_region: Optional[str]) -> str:
        """GPT API로 답변 생성"""
        region_context = f"\n\n사용자 지역: {user_region}" if user_region else ""

        system_prompt = """당신은 노인 복지 정책 전문 상담사입니다.
다음 규칙을 반드시 따르세요:

1. 친절하고 이해하기 쉽게 설명하세요
2. 마크다운 형식을 사용하지 말고, 자연스러운 대화체로 답변하세요
3. 제공된 정책 정보만 사용하여 답변하세요
4. 신청 방법, 자격 조건, 혜택 내용을 명확히 설명하세요
5. 사용자 지역이 제공된 경우, 해당 지역 정책을 우선적으로 안내하세요
6. 정보가 불충분한 경우 솔직히 말씀드리고, 관련 기관 문의를 권장하세요
7. 답변은 3-5문단으로 간결하게 작성하세요
"""

        user_prompt = f"""질문: {query}{region_context}

관련 정책 정보:
{context}

위 정보를 바탕으로 질문에 답변해 주세요. 자연스러운 대화체로, 마크다운 없이 답변하세요."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = self.llm.invoke(messages)
        return response.content.strip()

    def _generate_simple_answer(self, docs: List[Document], user_region: Optional[str]) -> str:
        """간단한 답변 생성 (GPT 없이)"""
        # 지역 우선순위로 정렬
        if user_region:
            docs = sorted(docs, key=lambda d: 0 if d.metadata.get('region') == user_region else 1)

        answer_parts = ["관련 복지 정책 정보를 찾았습니다.\n"]

        for i, doc in enumerate(docs[:3], 1):  # 상위 3개만
            region = doc.metadata.get('region', '전국')
            content = doc.page_content[:300]

            answer_parts.append(f"{i}. [{region}] {content}...")

        answer_parts.append("\n더 자세한 정보가 필요하시면 해당 지역 복지센터나 주민센터에 문의하시기 바랍니다.")

        return "\n\n".join(answer_parts)


# 싱글톤 인스턴스
_rag_service_instance = None


def get_rag_service() -> SimpleRAGService:
    """RAG 서비스 싱글톤 인스턴스 반환"""
    global _rag_service_instance

    if _rag_service_instance is None:
        _rag_service_instance = SimpleRAGService()

    return _rag_service_instance
