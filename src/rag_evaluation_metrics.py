"""
RAG 시스템 평가 메트릭

정교한 평가 지표를 통해 RAG 시스템의 품질을 측정합니다.
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np
from collections import Counter
import re

logger = logging.getLogger(__name__)


@dataclass
class EvaluationMetrics:
    """평가 메트릭 결과"""

    # 검색 품질 메트릭
    retrieval_precision: float = 0.0  # 검색된 문서 중 관련 문서 비율
    retrieval_recall: float = 0.0     # 관련 문서 중 검색된 문서 비율
    retrieval_f1: float = 0.0         # Precision과 Recall의 조화평균
    mrr: float = 0.0                   # Mean Reciprocal Rank
    ndcg: float = 0.0                  # Normalized Discounted Cumulative Gain

    # 답변 품질 메트릭
    answer_relevance: float = 0.0     # 답변과 질문의 관련성
    answer_faithfulness: float = 0.0  # 답변이 검색된 문서에 충실한 정도
    answer_completeness: float = 0.0  # 답변의 완전성
    answer_conciseness: float = 0.0   # 답변의 간결성

    # 컨텍스트 품질 메트릭
    context_relevance: float = 0.0    # 검색된 컨텍스트의 관련성
    context_diversity: float = 0.0    # 검색된 컨텍스트의 다양성
    context_coverage: float = 0.0     # 컨텍스트가 질문을 커버하는 정도

    # 종합 메트릭
    overall_score: float = 0.0        # 전체 종합 점수

    # 추가 정보
    latency_ms: float = 0.0           # 응답 시간 (밀리초)
    token_count: int = 0              # 생성된 토큰 수
    source_count: int = 0             # 사용된 소스 문서 수

    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        return {
            "retrieval_quality": {
                "precision": round(self.retrieval_precision, 3),
                "recall": round(self.retrieval_recall, 3),
                "f1": round(self.retrieval_f1, 3),
                "mrr": round(self.mrr, 3),
                "ndcg": round(self.ndcg, 3),
            },
            "answer_quality": {
                "relevance": round(self.answer_relevance, 3),
                "faithfulness": round(self.answer_faithfulness, 3),
                "completeness": round(self.answer_completeness, 3),
                "conciseness": round(self.answer_conciseness, 3),
            },
            "context_quality": {
                "relevance": round(self.context_relevance, 3),
                "diversity": round(self.context_diversity, 3),
                "coverage": round(self.context_coverage, 3),
            },
            "overall": {
                "score": round(self.overall_score, 3),
                "latency_ms": round(self.latency_ms, 2),
                "token_count": self.token_count,
                "source_count": self.source_count,
            }
        }


class RAGEvaluationMetrics:
    """RAG 시스템 평가 메트릭 계산기"""

    def __init__(
        self,
        use_llm_evaluation: bool = False,
        llm_model: str = "gpt-3.5-turbo"
    ):
        """
        Args:
            use_llm_evaluation: LLM 기반 평가 사용 여부
            llm_model: 평가에 사용할 LLM 모델
        """
        self.use_llm_evaluation = use_llm_evaluation
        self.llm_model = llm_model

        logger.info(f"RAG 평가 메트릭 초기화 (LLM 평가: {use_llm_evaluation})")

    def evaluate(
        self,
        query: str,
        answer: str,
        retrieved_contexts: List[str],
        ground_truth: Optional[str] = None,
        relevant_doc_ids: Optional[List[str]] = None,
        retrieved_doc_ids: Optional[List[str]] = None,
        latency_ms: float = 0.0
    ) -> EvaluationMetrics:
        """
        RAG 시스템 종합 평가

        Args:
            query: 사용자 질문
            answer: 생성된 답변
            retrieved_contexts: 검색된 컨텍스트 리스트
            ground_truth: 정답 (있는 경우)
            relevant_doc_ids: 관련 문서 ID 리스트 (있는 경우)
            retrieved_doc_ids: 검색된 문서 ID 리스트
            latency_ms: 응답 시간 (밀리초)

        Returns:
            EvaluationMetrics 객체
        """
        metrics = EvaluationMetrics()

        # 1. 검색 품질 평가
        if relevant_doc_ids and retrieved_doc_ids:
            retrieval_metrics = self._evaluate_retrieval(
                relevant_doc_ids, retrieved_doc_ids
            )
            metrics.retrieval_precision = retrieval_metrics["precision"]
            metrics.retrieval_recall = retrieval_metrics["recall"]
            metrics.retrieval_f1 = retrieval_metrics["f1"]
            metrics.mrr = retrieval_metrics["mrr"]
            metrics.ndcg = retrieval_metrics["ndcg"]

        # 2. 답변 품질 평가
        answer_metrics = self._evaluate_answer_quality(
            query, answer, retrieved_contexts, ground_truth
        )
        metrics.answer_relevance = answer_metrics["relevance"]
        metrics.answer_faithfulness = answer_metrics["faithfulness"]
        metrics.answer_completeness = answer_metrics["completeness"]
        metrics.answer_conciseness = answer_metrics["conciseness"]

        # 3. 컨텍스트 품질 평가
        context_metrics = self._evaluate_context_quality(
            query, retrieved_contexts
        )
        metrics.context_relevance = context_metrics["relevance"]
        metrics.context_diversity = context_metrics["diversity"]
        metrics.context_coverage = context_metrics["coverage"]

        # 4. 기본 정보
        metrics.latency_ms = latency_ms
        metrics.token_count = len(answer.split())
        metrics.source_count = len(retrieved_contexts)

        # 5. 종합 점수 계산
        metrics.overall_score = self._calculate_overall_score(metrics)

        return metrics

    def _evaluate_retrieval(
        self,
        relevant_doc_ids: List[str],
        retrieved_doc_ids: List[str]
    ) -> Dict[str, float]:
        """
        검색 품질 평가

        Returns:
            precision, recall, f1, mrr, ndcg
        """
        relevant_set = set(relevant_doc_ids)
        retrieved_set = set(retrieved_doc_ids)

        # Precision & Recall
        if len(retrieved_set) == 0:
            precision = 0.0
            recall = 0.0
            f1 = 0.0
        else:
            intersection = len(relevant_set & retrieved_set)
            precision = intersection / len(retrieved_set)
            recall = intersection / len(relevant_set) if len(relevant_set) > 0 else 0.0
            f1 = (2 * precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0

        # MRR (Mean Reciprocal Rank)
        mrr = 0.0
        for i, doc_id in enumerate(retrieved_doc_ids):
            if doc_id in relevant_set:
                mrr = 1.0 / (i + 1)
                break

        # NDCG (Normalized Discounted Cumulative Gain)
        dcg = 0.0
        idcg = 0.0

        for i, doc_id in enumerate(retrieved_doc_ids):
            relevance = 1.0 if doc_id in relevant_set else 0.0
            dcg += relevance / np.log2(i + 2)  # i+2 to avoid log2(1)=0

        # Ideal DCG (모든 관련 문서가 상위에 있는 경우)
        for i in range(min(len(relevant_doc_ids), len(retrieved_doc_ids))):
            idcg += 1.0 / np.log2(i + 2)

        ndcg = dcg / idcg if idcg > 0 else 0.0

        return {
            "precision": precision,
            "recall": recall,
            "f1": f1,
            "mrr": mrr,
            "ndcg": ndcg
        }

    def _evaluate_answer_quality(
        self,
        query: str,
        answer: str,
        contexts: List[str],
        ground_truth: Optional[str] = None
    ) -> Dict[str, float]:
        """답변 품질 평가"""

        # 1. Relevance (답변-질문 관련성)
        relevance = self._calculate_semantic_similarity(query, answer)

        # 2. Faithfulness (답변-컨텍스트 충실도)
        faithfulness = self._calculate_faithfulness(answer, contexts)

        # 3. Completeness (답변 완전성)
        completeness = self._calculate_completeness(query, answer, ground_truth)

        # 4. Conciseness (답변 간결성)
        conciseness = self._calculate_conciseness(answer)

        return {
            "relevance": relevance,
            "faithfulness": faithfulness,
            "completeness": completeness,
            "conciseness": conciseness
        }

    def _evaluate_context_quality(
        self,
        query: str,
        contexts: List[str]
    ) -> Dict[str, float]:
        """컨텍스트 품질 평가"""

        if not contexts:
            return {
                "relevance": 0.0,
                "diversity": 0.0,
                "coverage": 0.0
            }

        # 1. Context Relevance (컨텍스트-질문 관련성)
        relevance_scores = [
            self._calculate_semantic_similarity(query, ctx)
            for ctx in contexts
        ]
        avg_relevance = np.mean(relevance_scores)

        # 2. Context Diversity (컨텍스트 다양성)
        diversity = self._calculate_diversity(contexts)

        # 3. Context Coverage (컨텍스트 커버리지)
        coverage = self._calculate_coverage(query, contexts)

        return {
            "relevance": avg_relevance,
            "diversity": diversity,
            "coverage": coverage
        }

    def _calculate_semantic_similarity(self, text1: str, text2: str) -> float:
        """
        두 텍스트의 의미적 유사도 계산 (간단한 버전)
        실제로는 임베딩 기반 코사인 유사도 사용 권장
        """
        # 단어 기반 Jaccard 유사도로 간단히 구현
        words1 = set(self._tokenize(text1))
        words2 = set(self._tokenize(text2))

        if not words1 or not words2:
            return 0.0

        intersection = len(words1 & words2)
        union = len(words1 | words2)

        return intersection / union if union > 0 else 0.0

    def _calculate_faithfulness(self, answer: str, contexts: List[str]) -> float:
        """
        답변이 컨텍스트에 충실한 정도 측정
        답변의 각 문장이 컨텍스트에서 지지되는지 확인
        """
        if not contexts:
            return 0.0

        # 답변을 문장으로 분리
        answer_sentences = self._split_sentences(answer)

        if not answer_sentences:
            return 0.0

        # 각 문장이 컨텍스트에서 지지되는지 확인
        supported_count = 0
        combined_context = " ".join(contexts)

        for sentence in answer_sentences:
            # 문장의 주요 키워드가 컨텍스트에 포함되어 있는지 확인
            sentence_words = set(self._tokenize(sentence))
            context_words = set(self._tokenize(combined_context))

            # 최소 50% 이상의 키워드가 컨텍스트에 있으면 지지됨으로 간주
            overlap = len(sentence_words & context_words)
            if len(sentence_words) > 0 and overlap / len(sentence_words) >= 0.5:
                supported_count += 1

        return supported_count / len(answer_sentences)

    def _calculate_completeness(
        self,
        query: str,
        answer: str,
        ground_truth: Optional[str] = None
    ) -> float:
        """답변의 완전성 측정"""

        # Ground truth가 있으면 비교
        if ground_truth:
            return self._calculate_semantic_similarity(answer, ground_truth)

        # Ground truth가 없으면 질문의 키워드 커버리지로 측정
        query_keywords = self._extract_keywords(query)
        answer_words = set(self._tokenize(answer))

        if not query_keywords:
            return 0.5  # 기본 점수

        covered = len(query_keywords & answer_words)
        return covered / len(query_keywords)

    def _calculate_conciseness(self, answer: str) -> float:
        """
        답변의 간결성 측정
        적절한 길이 (100-500자)를 벗어나면 감점
        """
        length = len(answer)

        # 최적 길이 범위
        optimal_min = 100
        optimal_max = 500

        if optimal_min <= length <= optimal_max:
            return 1.0
        elif length < optimal_min:
            return length / optimal_min
        else:
            # 너무 길면 감점
            excess = length - optimal_max
            penalty = min(excess / optimal_max, 0.5)
            return 1.0 - penalty

    def _calculate_diversity(self, contexts: List[str]) -> float:
        """
        컨텍스트 간 다양성 측정
        서로 다른 정보를 포함할수록 높은 점수
        """
        if len(contexts) <= 1:
            return 0.0

        # 각 컨텍스트 간 유사도 계산
        similarities = []
        for i in range(len(contexts)):
            for j in range(i + 1, len(contexts)):
                sim = self._calculate_semantic_similarity(contexts[i], contexts[j])
                similarities.append(sim)

        # 유사도가 낮을수록 다양성이 높음
        avg_similarity = np.mean(similarities) if similarities else 0.0
        diversity = 1.0 - avg_similarity

        return diversity

    def _calculate_coverage(self, query: str, contexts: List[str]) -> float:
        """컨텍스트가 질문을 커버하는 정도"""

        query_keywords = self._extract_keywords(query)

        if not query_keywords:
            return 0.5

        # 모든 컨텍스트에서 키워드 찾기
        covered_keywords = set()
        combined_context = " ".join(contexts)
        context_words = set(self._tokenize(combined_context))

        covered_keywords = query_keywords & context_words

        return len(covered_keywords) / len(query_keywords)

    def _calculate_overall_score(self, metrics: EvaluationMetrics) -> float:
        """종합 점수 계산 (가중 평균)"""

        scores = []

        # 검색 품질 (30%)
        if metrics.retrieval_f1 > 0:
            scores.append(("retrieval", metrics.retrieval_f1, 0.3))

        # 답변 품질 (40%)
        answer_score = np.mean([
            metrics.answer_relevance,
            metrics.answer_faithfulness,
            metrics.answer_completeness,
            metrics.answer_conciseness
        ])
        scores.append(("answer", answer_score, 0.4))

        # 컨텍스트 품질 (30%)
        context_score = np.mean([
            metrics.context_relevance,
            metrics.context_diversity,
            metrics.context_coverage
        ])
        scores.append(("context", context_score, 0.3))

        # 가중 평균
        total_weight = sum(weight for _, _, weight in scores)
        weighted_sum = sum(score * weight for _, score, weight in scores)

        return weighted_sum / total_weight if total_weight > 0 else 0.0

    def _tokenize(self, text: str) -> List[str]:
        """텍스트 토크나이징 (한국어 고려)"""
        # 간단한 토크나이징 (실제로는 KoNLPy 등 사용 권장)
        text = text.lower()
        # 한글, 영문, 숫자만 남기기
        text = re.sub(r'[^가-힣a-z0-9\s]', ' ', text)
        words = text.split()
        # 불용어 제거 (간단한 버전)
        stopwords = {'은', '는', '이', '가', '을', '를', '의', '에', '와', '과',
                    'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for'}
        return [w for w in words if w not in stopwords and len(w) > 1]

    def _extract_keywords(self, text: str) -> set:
        """텍스트에서 키워드 추출"""
        words = self._tokenize(text)
        # 빈도 기반으로 중요 단어 추출
        word_freq = Counter(words)
        # 상위 50% 빈도 단어를 키워드로 간주
        threshold = max(1, len(word_freq) // 2)
        keywords = {word for word, _ in word_freq.most_common(threshold)}
        return keywords

    def _split_sentences(self, text: str) -> List[str]:
        """텍스트를 문장으로 분리"""
        # 간단한 문장 분리 (실제로는 더 정교한 방법 사용 권장)
        sentences = re.split(r'[.!?]\s+', text)
        return [s.strip() for s in sentences if s.strip()]


class BatchRAGEvaluator:
    """여러 쿼리에 대한 일괄 평가"""

    def __init__(self, metrics_calculator: RAGEvaluationMetrics):
        self.metrics_calculator = metrics_calculator

    def evaluate_batch(
        self,
        test_cases: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        여러 테스트 케이스를 일괄 평가

        Args:
            test_cases: 각 테스트 케이스는 다음 키를 포함:
                - query: 질문
                - answer: 답변
                - contexts: 검색된 컨텍스트
                - ground_truth: 정답 (선택)
                - relevant_doc_ids: 관련 문서 ID (선택)
                - retrieved_doc_ids: 검색된 문서 ID (선택)

        Returns:
            평균 메트릭 및 개별 결과
        """
        all_results = []

        for test_case in test_cases:
            metrics = self.metrics_calculator.evaluate(
                query=test_case["query"],
                answer=test_case["answer"],
                retrieved_contexts=test_case["contexts"],
                ground_truth=test_case.get("ground_truth"),
                relevant_doc_ids=test_case.get("relevant_doc_ids"),
                retrieved_doc_ids=test_case.get("retrieved_doc_ids"),
                latency_ms=test_case.get("latency_ms", 0.0)
            )
            all_results.append(metrics)

        # 평균 메트릭 계산
        avg_metrics = self._calculate_average_metrics(all_results)

        return {
            "individual_results": [m.to_dict() for m in all_results],
            "average_metrics": avg_metrics,
            "summary": self._generate_summary(avg_metrics, all_results)
        }

    def _calculate_average_metrics(
        self,
        results: List[EvaluationMetrics]
    ) -> Dict[str, float]:
        """평균 메트릭 계산"""

        if not results:
            return {}

        return {
            "retrieval_precision": np.mean([r.retrieval_precision for r in results]),
            "retrieval_recall": np.mean([r.retrieval_recall for r in results]),
            "retrieval_f1": np.mean([r.retrieval_f1 for r in results]),
            "mrr": np.mean([r.mrr for r in results]),
            "ndcg": np.mean([r.ndcg for r in results]),
            "answer_relevance": np.mean([r.answer_relevance for r in results]),
            "answer_faithfulness": np.mean([r.answer_faithfulness for r in results]),
            "answer_completeness": np.mean([r.answer_completeness for r in results]),
            "answer_conciseness": np.mean([r.answer_conciseness for r in results]),
            "context_relevance": np.mean([r.context_relevance for r in results]),
            "context_diversity": np.mean([r.context_diversity for r in results]),
            "context_coverage": np.mean([r.context_coverage for r in results]),
            "overall_score": np.mean([r.overall_score for r in results]),
            "avg_latency_ms": np.mean([r.latency_ms for r in results]),
            "avg_token_count": np.mean([r.token_count for r in results]),
        }

    def _generate_summary(
        self,
        avg_metrics: Dict[str, float],
        results: List[EvaluationMetrics]
    ) -> str:
        """평가 요약 리포트 생성"""

        summary = [
            "=" * 60,
            "RAG 시스템 평가 리포트",
            "=" * 60,
            f"총 테스트 케이스: {len(results)}개",
            "",
            "📊 평균 성능:",
            f"  • 전체 점수: {avg_metrics.get('overall_score', 0):.3f}",
            "",
            "🔍 검색 품질:",
            f"  • Precision: {avg_metrics.get('retrieval_precision', 0):.3f}",
            f"  • Recall: {avg_metrics.get('retrieval_recall', 0):.3f}",
            f"  • F1 Score: {avg_metrics.get('retrieval_f1', 0):.3f}",
            f"  • MRR: {avg_metrics.get('mrr', 0):.3f}",
            f"  • NDCG: {avg_metrics.get('ndcg', 0):.3f}",
            "",
            "📝 답변 품질:",
            f"  • 관련성: {avg_metrics.get('answer_relevance', 0):.3f}",
            f"  • 충실성: {avg_metrics.get('answer_faithfulness', 0):.3f}",
            f"  • 완전성: {avg_metrics.get('answer_completeness', 0):.3f}",
            f"  • 간결성: {avg_metrics.get('answer_conciseness', 0):.3f}",
            "",
            "📚 컨텍스트 품질:",
            f"  • 관련성: {avg_metrics.get('context_relevance', 0):.3f}",
            f"  • 다양성: {avg_metrics.get('context_diversity', 0):.3f}",
            f"  • 커버리지: {avg_metrics.get('context_coverage', 0):.3f}",
            "",
            "⚡ 성능:",
            f"  • 평균 응답시간: {avg_metrics.get('avg_latency_ms', 0):.2f}ms",
            f"  • 평균 토큰 수: {avg_metrics.get('avg_token_count', 0):.0f}",
            "=" * 60,
        ]

        return "\n".join(summary)
