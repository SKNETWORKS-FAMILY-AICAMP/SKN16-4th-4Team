"""간단한 re-rank 동작 테스트 스크립트
- hybrid_rerank와 advanced_rag의 reranking 연동을 간단히 검증

사용:
  python tools\quick_rerank_test.py
"""
from chatbot_web.rag_system.re_ranker import hybrid_rerank

sample = [
    {'id':'a','score':0.9,'metadata':{'region':'서울','filename':'a.txt'}},
    {'id':'b','score':0.85,'metadata':{'region':'부산','filename':'b.txt'}},
    {'id':'c','score':0.8,'metadata':{'region':'전국','filename':'c.txt'}}
]

print('원본:')
for s in sample:
    print(s)

out = hybrid_rerank(sample, alpha=0.6, domain_boosts={'region': {'서울':0.15}})

print('\n하이브리드 결과:')
for o in out:
    print(o)
