"""
고급 RAG 기능 모듈
OpenAI API 없이 성능 향상

기법:
1. Query Expansion - 동의어/유사어 확장
2. Reranking - TF-IDF 기반 재순위화
3. Multi-Query - 여러 각도로 질문 재구성
4. Answer Synthesis - 구조화된 답변 생성
"""

import logging
from typing import List, Dict, Any, Optional
from collections import Counter
import re

logger = logging.getLogger(__name__)


class QueryExpander:
    """질문 확장 - 동의어/유사어 추가"""

    def __init__(self):
        # 노인복지 도메인 특화 동의어 사전
        self.synonym_dict = {
            '노인': ['어르신', '고령자', '경로', '노년층', '실버'],
            '복지': ['혜택', '지원', '서비스', '정책'],
            '수당': ['급여', '보조금', '지원금'],
            '의료': ['건강', '진료', '치료'],
            '요양': ['돌봄', '간병', '케어'],
            '경로당': ['노인회관', '복지관'],
            '연금': ['기초연금', '노령연금'],
            '지원': ['혜택', '서비스', '보조', '제공'],
            '신청': ['접수', '등록', '가입'],
            '할인': ['감면', '경감', '우대'],
            '병원': ['의료기관', '요양병원'],
            '교통': ['버스', '지하철', '대중교통'],
            '긴급': ['응급', '급여', '즉시'],
        }

        # 복지 정책 관련 확장 키워드
        self.expansion_keywords = {
            '연금': ['기초연금', '국민연금', '노령연금'],
            '의료비': ['진료비', '치료비', '약값', '병원비'],
            '돌봄': ['요양', '간병', '돌봄서비스', '방문요양'],
            '할인': ['경로우대', '할인혜택', '무료이용'],
        }

    def expand_query(self, query: str) -> List[str]:
        """질문을 확장하여 여러 버전 생성"""
        queries = [query]  # 원본 질문 포함

        # 동의어 확장
        for original, synonyms in self.synonym_dict.items():
            if original in query:
                for synonym in synonyms[:2]:  # 상위 2개만
                    expanded = query.replace(original, synonym)
                    if expanded != query:
                        queries.append(expanded)

        # 확장 키워드 추가
        for keyword, expansions in self.expansion_keywords.items():
            if keyword in query:
                for expansion in expansions[:1]:  # 1개만
                    queries.append(f"{query} {expansion}")

        # 중복 제거
        queries = list(dict.fromkeys(queries))

        logger.info(f"Query Expansion: {len(queries)}개 쿼리 생성")
        for i, q in enumerate(queries[:5], 1):
            logger.info(f"  {i}. {q}")

        return queries[:5]  # 최대 5개


class DocumentReranker:
    """문서 재순위화 - TF-IDF 기반"""

    def __init__(self):
        # 불용어 (stopwords)
        self.stopwords = set([
            '이', '그', '저', '것', '수', '등', '및', '에', '의', '가', '을', '를',
            '은', '는', '이다', '있다', '하다', '되다', '있는', '하는', '되는'
        ])

    def _tokenize(self, text: str) -> List[str]:
        """간단한 토크나이저"""
        # 한글, 영문, 숫자만 추출
        tokens = re.findall(r'[가-힣a-zA-Z0-9]+', text)
        # 불용어 제거 및 소문자 변환
        tokens = [t.lower() for t in tokens if t not in self.stopwords and len(t) > 1]
        return tokens

    def _calculate_tf(self, tokens: List[str]) -> Dict[str, float]:
        """TF (Term Frequency) 계산"""
        tf = {}
        total = len(tokens)
        counter = Counter(tokens)

        for token, count in counter.items():
            tf[token] = count / total if total > 0 else 0

        return tf

    def _calculate_idf(self, all_docs: List[List[str]]) -> Dict[str, float]:
        """IDF (Inverse Document Frequency) 계산"""
        import math

        idf = {}
        total_docs = len(all_docs)

        # 각 토큰이 나타나는 문서 수 계산
        token_doc_count = {}
        for doc_tokens in all_docs:
            unique_tokens = set(doc_tokens)
            for token in unique_tokens:
                token_doc_count[token] = token_doc_count.get(token, 0) + 1

        # IDF 계산
        for token, doc_count in token_doc_count.items():
            idf[token] = math.log((total_docs + 1) / (doc_count + 1))

        return idf

    def rerank(self, query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
        """TF-IDF 기반 재순위화"""
        if not documents:
            return []

        logger.info(f"📊 Reranking {len(documents)}개 문서...")

        # 쿼리 토큰화
        query_tokens = self._tokenize(query)

        # 모든 문서 토큰화
        docs_tokens = []
        for doc in documents:
            content = doc.get('content', '')
            tokens = self._tokenize(content)
            docs_tokens.append(tokens)

        # IDF 계산
        idf = self._calculate_idf(docs_tokens)

        # 각 문서의 점수 계산
        scores = []
        for i, doc_tokens in enumerate(docs_tokens):
            # TF 계산
            tf = self._calculate_tf(doc_tokens)

            # TF-IDF 점수 계산 (쿼리 토큰에 대해서만)
            score = 0.0
            for token in query_tokens:
                if token in tf:
                    tfidf = tf[token] * idf.get(token, 0)
                    score += tfidf

            # 기존 유사도와 결합 (가중치 7:3)
            original_similarity = documents[i].get('similarity', 0.5)
            combined_score = 0.7 * original_similarity + 0.3 * min(score, 1.0)

            scores.append((i, combined_score))

        # 점수 기준 정렬
        scores.sort(key=lambda x: x[1], reverse=True)

        # 상위 k개 반환
        reranked = []
        for idx, score in scores[:top_k]:
            doc = documents[idx].copy()
            doc['rerank_score'] = score
            reranked.append(doc)

        logger.info(f"✅ Reranking 완료: 상위 {len(reranked)}개 선택")
        for i, doc in enumerate(reranked[:3], 1):
            filename = doc['metadata'].get('filename', 'unknown')
            rerank_score = doc.get('rerank_score', 0)
            logger.info(f"  {i}. {filename} (score: {rerank_score:.4f})")

        return reranked


class MultiQueryGenerator:
    """Multi-Query RAG - 질문을 여러 각도로 재구성"""

    def __init__(self):
        # 질문 재구성 템플릿
        self.query_templates = {
            '정의': '{keyword}이란 무엇인가?',
            '대상': '{keyword}의 대상자는 누구인가?',
            '신청': '{keyword}은 어떻게 신청하나?',
            '혜택': '{keyword}의 혜택은 무엇인가?',
            '조건': '{keyword}의 조건은 무엇인가?',
        }

    def extract_keywords(self, query: str) -> List[str]:
        """질문에서 핵심 키워드 추출"""
        # 복지 관련 키워드 패턴
        welfare_keywords = [
            '기초연금', '노인수당', '의료비', '요양', '돌봄', '경로당',
            '긴급복지', '장기요양', '건강보험', '틀니', '보청기',
            '복지정책', '노인복지', '경로우대', '할인'
        ]

        keywords = []
        for keyword in welfare_keywords:
            if keyword in query:
                keywords.append(keyword)

        # 키워드가 없으면 명사 추출 (간단한 방법)
        if not keywords:
            # 2글자 이상 한글 단어 추출
            words = re.findall(r'[가-힣]{2,}', query)
            keywords = words[:2]  # 최대 2개

        return keywords

    def generate_multi_queries(self, query: str) -> List[str]:
        """원본 질문에서 여러 하위 질문 생성"""
        queries = [query]  # 원본 포함

        # 키워드 추출
        keywords = self.extract_keywords(query)

        if keywords:
            main_keyword = keywords[0]

            # 템플릿 기반 질문 생성 (2개만)
            for template_type in ['대상', '혜택']:
                if template_type in self.query_templates:
                    new_query = self.query_templates[template_type].format(keyword=main_keyword)
                    queries.append(new_query)

        logger.info(f"Multi-Query: {len(queries)}개 질문 생성")
        for i, q in enumerate(queries, 1):
            logger.info(f"  {i}. {q}")

        return queries[:3]  # 최대 3개


class AdvancedAnswerSynthesizer:
    """고급 답변 합성 - 구조화된 답변 생성"""

    def __init__(self):
        self.answer_template = {
            '정의': '**{policy}이란?**\n{content}',
            '대상': '**지원 대상**\n{content}',
            '조건': '**신청 조건**\n{content}',
            '혜택': '**제공 혜택**\n{content}',
            '신청': '**신청 방법**\n{content}',
        }

    def categorize_content(self, content: str) -> str:
        """내용을 카테고리별로 분류"""
        # 키워드 기반 카테고리 매칭
        if any(kw in content for kw in ['대상', '해당', '자격']):
            return '대상'
        elif any(kw in content for kw in ['조건', '기준', '요건']):
            return '조건'
        elif any(kw in content for kw in ['혜택', '지원', '급여', '서비스']):
            return '혜택'
        elif any(kw in content for kw in ['신청', '접수', '등록', '제출']):
            return '신청'
        else:
            return '정의'

    def synthesize_structured_answer(
        self,
        question: str,
        doc_contents: List[Dict[str, str]]
    ) -> str:
        """문서들을 구조화된 답변으로 합성"""

        # 카테고리별 분류
        categorized = {}
        for doc in doc_contents:
            content = doc.get('content', '')
            region = doc.get('region', '지역미상')
            filename = doc.get('filename', '정책문서')

            category = self.categorize_content(content)

            if category not in categorized:
                categorized[category] = []

            categorized[category].append({
                'content': content,
                'region': region,
                'filename': filename
            })

        # 구조화된 답변 생성
        answer_parts = []
        answer_parts.append(f"'{question}'에 대한 상세 정보를 안내해드리겠습니다.\n")

        # 카테고리 우선순위
        category_order = ['정의', '대상', '조건', '혜택', '신청']

        for category in category_order:
            if category in categorized:
                # 섹션 헤더
                if category == '정의':
                    answer_parts.append("\n📋 **정책 개요**\n")
                elif category == '대상':
                    answer_parts.append("\n👥 **지원 대상**\n")
                elif category == '조건':
                    answer_parts.append("\n📌 **신청 조건**\n")
                elif category == '혜택':
                    answer_parts.append("\n💰 **제공 혜택**\n")
                elif category == '신청':
                    answer_parts.append("\n📝 **신청 방법**\n")

                # 내용 추가 (최대 2개)
                for i, item in enumerate(categorized[category][:2], 1):
                    answer_parts.append(f"{i}. {item['content']}\n")
                    answer_parts.append(f"   (출처: {item['filename']}, {item['region']})\n\n")

        # 추가 안내
        answer_parts.append("\n💡 **추가 문의**\n")
        answer_parts.append("• 더 자세한 내용은 관할 주민센터나 구청에 문의하세요.\n")
        answer_parts.append("• 복지로 홈페이지(www.bokjiro.go.kr)에서도 확인할 수 있습니다.\n")

        return "".join(answer_parts)


class AdvancedRAGPipeline:
    """통합 고급 RAG 파이프라인"""

    def __init__(self):
        self.query_expander = QueryExpander()
        self.reranker = DocumentReranker()
        self.multi_query_gen = MultiQueryGenerator()
        self.answer_synthesizer = AdvancedAnswerSynthesizer()

    def process(
        self,
        query: str,
        vector_store,
        embedder,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """고급 RAG 파이프라인 실행"""

        logger.info(f"\n{'='*60}")
        logger.info(f"🚀 Advanced RAG Pipeline 시작")
        logger.info(f"{'='*60}")

        # Step 1: Query Expansion
        logger.info("\n[Step 1] Query Expansion")
        expanded_queries = self.query_expander.expand_query(query)

        # Step 2: Multi-Query 검색
        logger.info("\n[Step 2] Multi-Query Search")
        all_docs = []
        seen_ids = set()

        for exp_query in expanded_queries:
            docs = vector_store.similarity_search(exp_query, embedder, k=top_k * 2)
            for doc in docs:
                # 중복 제거 (content 기반)
                doc_id = doc.get('content', '')[:100]
                if doc_id not in seen_ids:
                    all_docs.append(doc)
                    seen_ids.add(doc_id)

        logger.info(f"📊 총 {len(all_docs)}개 문서 수집 (중복 제거 후)")

        # Step 3: Reranking
        logger.info("\n[Step 3] Reranking")
        reranked_docs = self.reranker.rerank(query, all_docs, top_k=top_k)

        # Step 4: Answer Synthesis
        logger.info("\n[Step 4] Answer Synthesis")
        if reranked_docs:
            doc_contents = []
            for doc in reranked_docs:
                doc_contents.append({
                    'content': doc.get('content', ''),
                    'region': doc['metadata'].get('region', '지역미상'),
                    'filename': doc['metadata'].get('filename', '정책문서')
                })

            answer = self.answer_synthesizer.synthesize_structured_answer(
                query, doc_contents
            )

            return {
                'answer': answer,
                'documents': reranked_docs,
                'method': 'advanced_rag'
            }
        else:
            return {
                'answer': f"'{query}'에 대한 정보를 찾지 못했습니다.",
                'documents': [],
                'method': 'advanced_rag_no_docs'
            }
