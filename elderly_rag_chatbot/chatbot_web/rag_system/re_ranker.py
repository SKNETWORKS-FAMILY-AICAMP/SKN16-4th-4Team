"""하이브리드 리랭커

의미 기반 점수와 도메인 가중치(메타데이터 기반)를 결합해 결과를 재정렬합니다.

사용 예:
    from chatbot_web.rag_system.re_ranker import hybrid_rerank
    reranked = hybrid_rerank(results, alpha=0.6, domain_boosts={'region': {'서울특별시': 0.2}})

입력 형식 예시 (results):
  [
    {'id': 'doc1', 'score': 0.78, 'metadata': {'region':'서울특별시', 'provider':'A'}},
    {'id': 'doc2', 'score': 0.72, 'metadata': {'region':'부산광역시', 'provider':'B'}},
  ]

알고리즘: final_score = alpha * semantic_score + (1-alpha) * (semantic_score + domain_boost)
"""

from typing import List, Dict, Any


def hybrid_rerank(results: List[Dict[str, Any]], alpha: float = 0.6, domain_boosts: Dict[str, Dict[str, float]] = None, normalize: bool = True) -> List[Dict[str, Any]]:
    """하이브리드 재순위

    - results: list of dicts with 'score' (semantic) and optional 'metadata'
    - alpha: 의미 기반 가중치 (0..1)
    - domain_boosts: 예: {'region': {'서울특별시': 0.2}}

    반환: 입력 항목에 'final_score' 필드를 추가하고 재정렬된 리스트를 반환
    """
    domain_boosts = domain_boosts or {}

    # 기본: domain boost 합산
    for r in results:
        semantic = r.get('score', 0.0)
        meta = r.get('metadata', {}) or {}
        boost = 0.0
        for key, mapping in domain_boosts.items():
            val = meta.get(key)
            if val and val in mapping:
                boost += float(mapping[val])
        # final_score 계산
        # hybrid: weighted combination, keep in the same scale as semantic scores (0..1)
        final = alpha * semantic + (1 - alpha) * min(1.0, semantic + boost)
        r['domain_boost'] = boost
        r['final_score'] = final

    # 정규화(선택적)
    if normalize:
        max_score = max((r['final_score'] for r in results), default=1.0)
        if max_score > 0:
            for r in results:
                r['final_score'] = r['final_score'] / max_score

    # 정렬
    results_sorted = sorted(results, key=lambda x: x.get('final_score', 0.0), reverse=True)
    return results_sorted
