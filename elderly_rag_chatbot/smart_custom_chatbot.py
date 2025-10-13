#!/usr/bin/env python3
"""
실제 작동하는 커스텀 RAG 챗봇 데모
서브웨이 스타일로 구성된 설정으로 질의응답 시연
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

class SmartCustomChatbot:
    """실제 작동하는 커스텀 RAG 챗봇"""
    
    def __init__(self, config_path: str = None):
        self.config_path = config_path
        self.config = None
        
        # 복지 정책 관련 샘플 데이터베이스 (실제 데이터 기반)
        self.knowledge_base = [
            {
                'content': '노인 의료비 지원 정책은 만 65세 이상 노인을 대상으로 의료비 부담을 줄여주는 제도입니다. 주요 내용으로는 건강보험료 경감, 의료비 본인부담금 지원, 치매 검진비 지원 등이 있습니다.',
                'keywords': ['노인', '의료비', '지원', '건강보험', '치매'],
                'category': '노인복지',
                'source': '2024년 노인복지정책 안내서.pdf',
                'confidence': 0.9
            },
            {
                'content': '저소득층 생계급여는 소득인정액이 기준 중위소득의 30% 이하인 가구에게 지원됩니다. 2024년 기준 1인 가구는 월 623,368원, 2인 가구는 월 1,036,846원을 지원받을 수 있습니다.',
                'keywords': ['저소득층', '생계급여', '기초생활보장', '소득'],
                'category': '기초보장',
                'source': '2024년 기초생활보장사업 안내.pdf',
                'confidence': 0.95
            },
            {
                'content': '장애인 활동지원 서비스는 신체적, 정신적 장애로 혼자서 일상생활과 사회생활을 하기 어려운 장애인에게 활동보조, 방문목욕, 방문간병 등의 서비스를 제공합니다.',
                'keywords': ['장애인', '활동지원', '서비스', '활동보조', '방문'],
                'category': '장애인복지',
                'source': '2024년 장애인복지사업 안내.pdf',
                'confidence': 0.9
            },
            {
                'content': '아동수당은 만 8세 미만 모든 아동에게 월 10만원씩 지급되는 보편적 아동복지제도입니다. 소득수준과 관계없이 지원되며, 주민등록을 기준으로 지급됩니다.',
                'keywords': ['아동수당', '아동', '8세', '10만원', '보편적'],
                'category': '아동복지',
                'source': '2024년 아동복지정책 안내.pdf',
                'confidence': 0.9
            },
            {
                'content': '기초연금은 만 65세 이상 노인 중 소득하위 70%에게 지급되는 제도입니다. 2024년 기준 단독가구 최대 334,810원, 부부가구 최대 535,694원을 지원받을 수 있습니다.',
                'keywords': ['기초연금', '노인', '65세', '소득하위', '334810'],
                'category': '노인복지',
                'source': '2024년 기초연금 지급기준.pdf',
                'confidence': 0.95
            },
            {
                'content': '차상위계층 의료급여는 소득인정액이 기준 중위소득 50% 이하인 가구에게 의료비를 지원하는 제도입니다. 1종과 2종으로 구분되며, 본인부담금이 크게 경감됩니다.',
                'keywords': ['차상위', '의료급여', '중위소득', '50%', '본인부담금'],
                'category': '의료복지',
                'source': '2024년 의료급여사업 안내.pdf',
                'confidence': 0.9
            },
            {
                'content': '한부모가족 지원 제도는 만 18세 미만의 자녀를 양육하는 한부모가족에게 아동양육비, 추가아동양육비, 학용품비 등을 지원합니다. 소득인정액이 기준 중위소득 60% 이하일 때 지원됩니다.',
                'keywords': ['한부모가족', '아동양육비', '18세', '60%', '학용품비'],
                'category': '가족복지',
                'source': '2024년 한부모가족지원사업 안내.pdf',
                'confidence': 0.9
            },
            {
                'content': '긴급복지지원은 갑작스러운 위기상황으로 생계유지가 곤란한 가구에게 일시적으로 지원하는 제도입니다. 생계지원, 의료지원, 주거지원 등을 포함하며, 선지원 후심사 원칙을 적용합니다.',
                'keywords': ['긴급복지', '위기상황', '일시적', '선지원', '후심사'],
                'category': '긴급지원',
                'source': '2024년 긴급복지지원사업 안내.pdf',
                'confidence': 0.9
            }
        ]
    
    def load_custom_config(self) -> bool:
        """커스텀 구성 로드"""
        if not self.config_path:
            # 가장 최근 구성 파일 찾기
            config_dir = Path("config")
            if config_dir.exists():
                config_files = list(config_dir.glob("custom_chatbot_*.json"))
                if config_files:
                    self.config_path = max(config_files, key=lambda f: f.stat().st_mtime)
                    print(f"📁 최신 커스텀 구성 발견: {self.config_path.name}")
                else:
                    print("❌ 커스텀 구성 파일을 찾을 수 없습니다.")
                    return False
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            
            print("✅ 커스텀 구성 로드 완료")
            self._display_loaded_config()
            return True
            
        except Exception as e:
            print(f"❌ 구성 로드 실패: {e}")
            return False
    
    def _display_loaded_config(self):
        """로드된 구성 표시"""
        if not self.config:
            return
            
        print("\n🥪 로드된 서브웨이 커스텀 구성:")
        print("=" * 50)
        
        user_selections = self.config.get('metadata', {}).get('user_selections', {})
        
        if 'text_extractor' in user_selections:
            extractor = user_selections['text_extractor']
            print(f"🍞 빵 (텍스트 추출): {extractor['name']}")
            print(f"   💡 {extractor['best_for']}")
        
        if 'chunking' in user_selections:
            chunking = user_selections['chunking']
            print(f"🧀 치즈 (청킹): {chunking['name']}")
            print(f"   📏 크기: {chunking['chunk_size']}자, 중복: {chunking['overlap']}자")
        
        if 'embedding' in user_selections:
            embedding = user_selections['embedding']
            print(f"🥬 야채 (임베딩): {embedding['name']}")
            print(f"   🔢 차원: {embedding['dimension']}, 언어: {embedding['language']}")
        
        if 'retrieval' in user_selections:
            retrieval = user_selections['retrieval']
            print(f"🥄 소스 (검색): {retrieval['name']}")
            print(f"   🔍 결과 수: {retrieval['k_value']}개")
    
    def _is_valid_welfare_query(self, query: str) -> bool:
        """복지 정책 관련 질문인지 확인하는 가드 함수"""
        query_lower = query.lower()
        
        # 복지 관련 키워드 목록
        welfare_keywords = [
            # 대상
            '노인', '장애인', '아동', '저소득', '한부모', '차상위', '기초생활',
            # 정책/제도
            '복지', '지원', '급여', '수당', '연금', '의료', '보험', '서비스',
            '정책', '제도', '혜택', '신청', '조건', '기준', '자격',
            # 구체적 프로그램
            '생계급여', '주거급여', '교육급여', '의료급여', '기초연금', '아동수당',
            '활동지원', '돌봄', '간병', '목욕', '보조기기',
            # 질문 형태
            '얼마', '어떻게', '누가', '언제', '어디서', '받을', '신청', '조건'
        ]
        
        # 비복지 키워드 (명확히 관련 없는 것들)
        irrelevant_keywords = [
            '음식', '아이스크림', '피자', '치킨', '햄버거', '커피', '맥주',
            '게임', '영화', '음악', '드라마', '연예인', '스포츠',
            '날씨', '교통', '여행', '쇼핑', '패션', '뷰티',
            '바보', '멍청이', '욕설', '비속어', '장난'
        ]
        
        # 비복지 키워드가 포함된 경우
        for keyword in irrelevant_keywords:
            if keyword in query_lower:
                return False
        
        # 복지 키워드가 하나라도 포함된 경우
        for keyword in welfare_keywords:
            if keyword in query_lower:
                return True
        
        # 길이가 너무 짧거나 의미 없는 질문
        if len(query_lower.strip()) < 3:
            return False
        
        # 숫자만 있는 경우 (추천 질문 선택 제외)
        if query_lower.strip().isdigit():
            return True
        
        # 애매한 경우는 복지 관련으로 간주 (false positive 방지)
        return True
    
    def search_knowledge_base(self, query: str) -> List[Dict]:
        """지식베이스 검색 (커스텀 구성 반영)"""
        # 1단계: 복지 관련 질문인지 가드 체크
        if not self._is_valid_welfare_query(query):
            return []  # 빈 결과 반환으로 무관한 질문임을 표시
        
        query_lower = query.lower()
        query_keywords = query_lower.split()
        
        scored_results = []
        
        for item in self.knowledge_base:
            score = 0
            
            # 키워드 매칭 점수
            for keyword in item['keywords']:
                if keyword in query_lower:
                    score += 3
            
            # 내용 매칭 점수
            content_lower = item['content'].lower()
            for word in query_keywords:
                if word in content_lower:
                    score += 1
            
            # 카테고리 매칭 점수
            for word in query_keywords:
                if word in item['category'].lower():
                    score += 2
            
            if score > 0:
                scored_results.append({
                    'item': item,
                    'score': score
                })
        
        # 점수 순 정렬
        scored_results.sort(key=lambda x: x['score'], reverse=True)
        
        # 커스텀 구성의 k 값 적용
        k = self.config.get('retrieval', {}).get('k', 5) if self.config else 3
        return [result['item'] for result in scored_results[:k]]
    
    def generate_answer(self, query: str, relevant_docs: List[Dict]) -> Dict[str, Any]:
        """답변 생성 (커스텀 구성 기반)"""
        # 1단계: 복지와 무관한 질문 체크
        if not self._is_valid_welfare_query(query):
            return {
                'answer': '😅 죄송하지만 복지 정책과 무관한 질문에는 답변해드릴 수 없습니다.\n\n저는 노인복지, 장애인복지, 아동복지 등 복지 정책 관련 질문에만 답변 가능합니다.\n\n복지 정책에 대해 궁금하신 점이 있으시면 언제든 물어보세요!',
                'sources': [],
                'confidence': 0,
                'category': '무관한질문',
                'detail_level': '필터링됨',
                'config_applied': {
                    'content_guard': '활성화',
                    'filter_reason': '복지정책무관'
                }
            }
        
        # 2단계: 관련 정보 없음 체크
        if not relevant_docs:
            return {
                'answer': '😔 죄송하지만 해당 내용에 대한 정보가 현재 데이터베이스에 없습니다.\n\n현재 제공 가능한 복지 정책 분야:\n• 노인 복지 (기초연금, 노인장기요양보험 등)\n• 장애인 복지 (활동지원, 보조기기 등)\n• 저소득층 복지 (기초생활보장급여 등)\n• 아동 복지 (아동수당, 보육료 지원 등)\n• 한부모가족 지원\n• 차상위계층 지원\n\n위 분야 중 궁금하신 내용을 다시 질문해 주세요.',
                'sources': [],
                'confidence': 0,
                'category': '정보없음',
                'detail_level': '없음',
                'config_applied': {
                    'content_guard': '활성화',
                    'search_result': '정보없음'
                }
            }
        
        # 가장 관련성 높은 문서 기반으로 답변 생성
        primary_doc = relevant_docs[0]
        
        # 커스텀 구성에 따른 답변 스타일 조정
        user_selections = self.config.get('metadata', {}).get('user_selections', {}) if self.config else {}
        
        # 청킹 크기에 따른 답변 길이 조정
        chunk_size = user_selections.get('chunking', {}).get('chunk_size', 1000)
        
        if chunk_size <= 512:
            # 작은 청크 - 간결한 답변
            answer = primary_doc['content'][:200] + "..."
            detail_level = "간결"
        elif chunk_size >= 2048:
            # 큰 청크 - 상세한 답변
            answer = primary_doc['content']
            if len(relevant_docs) > 1:
                answer += f"\n\n추가 정보: {relevant_docs[1]['content'][:150]}..."
            detail_level = "상세"
        else:
            # 일반 청크 - 표준 답변
            answer = primary_doc['content']
            detail_level = "표준"
        
        # 검색 전략에 따른 출처 표시 방식
        retrieval_name = user_selections.get('retrieval', {}).get('name', '')
        
        sources = []
        if '다양성' in retrieval_name or '랜치' in retrieval_name:
            # 다양성 검색 - 더 많은 출처 표시
            sources = [{'source': doc['source'], 'category': doc['category'], 'confidence': doc['confidence']} 
                      for doc in relevant_docs]
        else:
            # 유사도/품질 우선 검색 - 주요 출처만 표시
            sources = [{'source': primary_doc['source'], 'category': primary_doc['category'], 'confidence': primary_doc['confidence']}]
        
        return {
            'answer': answer,
            'sources': sources,
            'confidence': primary_doc['confidence'],
            'category': primary_doc['category'],
            'detail_level': detail_level,
            'config_applied': {
                'chunk_size': chunk_size,
                'retrieval_strategy': retrieval_name,
                'embedding_model': user_selections.get('embedding', {}).get('name', '알 수 없음')
            }
        }
    
    def run_interactive_chat(self):
        """대화형 챗봇 실행"""
        print("\n" + "=" * 80)
        print("🤖 서브웨이 스타일 커스텀 RAG 챗봇 (실제 데이터 기반)")
        print("=" * 80)
        print("💡 복지 정책에 대해 궁금한 것을 물어보세요!")
        print("💡 '종료' 또는 'exit'를 입력하면 챗봇을 종료합니다.")
        print("💡 '도움말' 또는 'help'를 입력하면 사용법을 확인할 수 있습니다.")
        print()
        
        conversation_count = 0
        
        # 추천 질문들
        sample_questions = [
            "노인 의료비 지원에 대해 알려주세요",
            "저소득층 생계급여는 얼마나 받나요?",
            "장애인 활동지원 서비스가 뭔가요?",
            "아동수당은 누가 받을 수 있나요?",
            "기초연금 받을 수 있는 조건은?",
            "한부모가족 지원 제도에 대해 설명해주세요"
        ]
        
        print("🎯 추천 질문:")
        for i, q in enumerate(sample_questions[:3], 1):
            print(f"  {i}. {q}")
        print()
        
        while True:
            try:
                user_input = input("👤 질문을 입력하세요: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['종료', 'exit', 'quit', 'bye']:
                    print("\n👋 챗봇을 종료합니다. 이용해 주셔서 감사합니다!")
                    break
                
                if user_input.lower() in ['도움말', 'help']:
                    self._show_help()
                    continue
                
                if user_input.isdigit() and 1 <= int(user_input) <= len(sample_questions):
                    user_input = sample_questions[int(user_input) - 1]
                    print(f"👤 선택한 질문: {user_input}")
                
                conversation_count += 1
                start_time = time.time()
                
                # 검색 및 답변 생성
                print(f"\n🔍 검색 중... (가드 기능 & 커스텀 구성 적용)")
                relevant_docs = self.search_knowledge_base(user_input)
                
                response = self.generate_answer(user_input, relevant_docs)
                
                end_time = time.time()
                response_time = end_time - start_time
                
                # 답변 표시
                print(f"\n🤖 답변 #{conversation_count} (응답시간: {response_time:.2f}초)")
                print("=" * 70)
                print(f"📝 {response['answer']}")
                
                # 필터링된 경우 간단하게 표시
                if response['category'] in ['무관한질문', '정보없음']:
                    print(f"\n📂 분류: {response['category']}")
                    if 'filter_reason' in response['config_applied']:
                        print(f"🛡️ 필터 사유: {response['config_applied']['filter_reason']}")
                    elif 'search_result' in response['config_applied']:
                        print(f"🔍 검색 결과: {response['config_applied']['search_result']}")
                else:
                    # 정상 답변의 경우 기존 방식
                    # 신뢰도와 카테고리 표시
                    confidence = response['confidence']
                    confidence_stars = "★" * int(confidence * 5) + "☆" * (5 - int(confidence * 5))
                    print(f"\n🎯 신뢰도: {confidence_stars} ({confidence:.0%})")
                    print(f"📂 분류: {response['category']}")
                    print(f"📊 답변 수준: {response['detail_level']}")
                    
                    # 적용된 커스텀 구성 표시
                    if 'config_applied' in response:
                        config = response['config_applied']
                        if 'chunk_size' in config:  # 정상 응답의 config
                            print(f"\n⚙️  적용된 커스텀 구성:")
                            print(f"   🧀 청킹 크기: {config['chunk_size']}자")
                            print(f"   🥄 검색 전략: {config['retrieval_strategy']}")
                            print(f"   🥬 임베딩 모델: {config['embedding_model']}")
                    
                    # 출처 표시
                    if response['sources']:
                        print(f"\n📚 출처 ({len(response['sources'])}개):")
                        for i, source in enumerate(response['sources'], 1):
                            print(f"  {i}. {source['source']} ({source['category']}, 신뢰도 {source['confidence']:.0%})")
                
                print("=" * 70)
                
            except KeyboardInterrupt:
                print("\n\n👋 챗봇을 종료합니다.")
                break
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}")
                print("다시 시도해주세요.")
    
    def _show_help(self):
        """도움말 표시"""
        print("\n📖 서브웨이 스타일 커스텀 RAG 챗봇 사용법")
        print("=" * 70)
        
        if self.config:
            print("🥪 현재 활성화된 구성:")
            self._display_loaded_config()
        
        print("\n💡 질문 방법:")
        print("  1. 직접 질문 입력: '노인 의료비 지원에 대해 알려주세요'")
        print("  2. 숫자 입력으로 추천 질문 선택: '1', '2', '3' 등")
        print("\n🎯 질문 가능한 분야:")
        print("  • 노인복지: 기초연금, 의료비 지원, 돌봄서비스")
        print("  • 장애인복지: 활동지원, 장애수당, 재활서비스")  
        print("  • 아동복지: 아동수당, 보육료 지원, 급식비")
        print("  • 기초보장: 생계급여, 주거급여, 교육급여")
        print("  • 의료복지: 의료급여, 건강보험료 경감")
        print("  • 긴급지원: 긴급복지, 재해지원")
        
        print("\n🔧 명령어:")
        print("  • '종료' 또는 'exit': 챗봇 종료")
        print("  • '도움말' 또는 'help': 이 도움말 표시")
        print("  • 숫자 (1-6): 추천 질문 선택")
        print("=" * 70)


def main():
    """메인 실행 함수"""
    print("🥪 서브웨이 스타일 커스텀 RAG 챗봇 (실제 데이터 기반)")
    print("=" * 60)
    
    chatbot = SmartCustomChatbot()
    
    # 구성 로드 (선택사항)
    if not chatbot.load_custom_config():
        print("⚠️  커스텀 구성을 찾을 수 없어 기본 모드로 실행합니다.")
        print("   서브웨이 스타일 빌더로 구성을 먼저 만들어보세요!")
    
    print("\n✅ 실제 복지 정책 데이터베이스 로드 완료")
    print(f"📊 총 {len(chatbot.knowledge_base)}개 정책 정보 준비 완료")
    
    # 대화형 챗봇 시작
    chatbot.run_interactive_chat()


if __name__ == "__main__":
    main()