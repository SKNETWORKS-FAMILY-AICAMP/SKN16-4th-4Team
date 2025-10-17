"""
RAG 기능 모듈

핵심 RAG 로직과 AI 에이전트 구현
"""

import logging
from typing import List, Dict, Any, Optional
import re
import random
import csv
from pathlib import Path

try:
    import openai
except ImportError:
    openai = None

# Django 호환을 위해 rag_config 사용
from . import rag_config
from .advanced_rag import AdvancedRAGPipeline
from .policy_extractor import EnhancedPolicyFormatter

OPENAI_MODEL = rag_config.OPENAI_MODEL
TEMPERATURE = rag_config.TEMPERATURE
MAX_TOKENS = rag_config.MAX_TOKENS
TOP_K_RESULTS = rag_config.TOP_K_RESULTS
get_openai_api_key = rag_config.get_openai_api_key

logger = logging.getLogger(__name__)


# 17개 시도 지역 매핑 (UserProfile 지역명 → 데이터 폴더 지역명)
REGION_MAPPING = {
    '서울특별시': '서울',
    '부산광역시': '부산',
    '대구광역시': '대구',
    '인천광역시': '인천',
    '광주광역시': '광주',
    '대전광역시': '대전',
    '울산광역시': '울산',
    '세종특별자치시': '세종',
    '경기도': '경기',
    '강원특별자치도': '강원',
    '충청북도': '충북',
    '충청남도': '충남',
    '전북특별자치도': '전북',
    '전라남도': '전남',
    '경상북도': '경북',
    '경상남도': '경남',
    '제주특별자치도': '제주',
}

# 데이터 폴더 지역명 → 키워드 리스트 (질문에서 지역 추출용)
REGION_KEYWORDS = {
    '서울': ['서울'],
    '부산': ['부산'],
    '대구': ['대구'],
    '인천': ['인천'],
    '광주': ['광주'],
    '대전': ['대전'],
    '울산': ['울산'],
    '세종': ['세종'],
    '경기': ['경기'],
    '강원': ['강원'],
    '충북': ['충북', '충청북도'],
    '충남': ['충남', '충청남도'],
    '전북': ['전북', '전북특별자치도'],
    '전남': ['전남', '전라남도'],
    '경북': ['경북', '경상북도'],
    '경남': ['경남', '경상남도'],
    '제주': ['제주'],
}


def map_user_region_to_data_folder(user_region: str) -> Optional[str]:
    """
    사용자 프로필의 지역명을 데이터 폴더 지역명으로 변환

    Args:
        user_region: UserProfile의 지역 (예: '경상북도', '부산광역시')

    Returns:
        데이터 폴더 지역명 (예: '경북', '부산') 또는 None
    """
    return REGION_MAPPING.get(user_region)


def extract_region_from_question(question: str) -> Optional[str]:
    """
    질문에서 지역 키워드 추출

    Args:
        question: 사용자 질문

    Returns:
        추출된 지역명 (데이터 폴더 형식) 또는 None
    """
    for region, keywords in REGION_KEYWORDS.items():
        for keyword in keywords:
            if keyword in question:
                return region
    return None


class WelfareRAGChain:
    """노인복지 RAG 체인"""

    def __init__(self, vector_store, embedder):
        self.vector_store = vector_store
        self.embedder = embedder
        self.api_key = get_openai_api_key()
        self.client = None

        # Advanced RAG Pipeline 초기화
        self.advanced_rag = AdvancedRAGPipeline()
        logger.info("🚀 Advanced RAG Pipeline 활성화")

        # Enhanced Policy Formatter 초기화
        self.policy_formatter = EnhancedPolicyFormatter()
        logger.info("✨ Enhanced Policy Formatter 활성화")

        # Policy URL 매핑 로드
        self.policy_url_mapping = self._load_policy_url_mapping()
        logger.info(f"📋 Policy URL 매핑 로드 완료: {len(self.policy_url_mapping)}개")

        if self.api_key and openai:
            try:
                # 안전한 OpenAI 클라이언트 초기화
                self.client = openai.OpenAI(
                    api_key=self.api_key,
                    timeout=30.0,
                    max_retries=3
                )
            except Exception as e:
                logger.warning(f"OpenAI 클라이언트 초기화 실패: {e}")
                self.client = None

    def _load_policy_url_mapping(self) -> Dict[str, str]:
        """policy_mapping.csv 파일에서 정책명 -> URL 매핑 로드 (지역+정책명 조합만 사용)"""
        mapping = {}
        csv_path = Path(__file__).parent.parent.parent / 'policy_mapping.csv'

        try:
            with open(csv_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # xlsx 형식: 시도명, 관심주제, 정책명, 링크
                    policy_name = row.get('정책명', '').strip()
                    url = row.get('링크', '').strip()
                    region = row.get('시도명', '').strip()

                    # 지역+정책명 조합으로만 매핑 (정확한 매칭을 위해)
                    if policy_name and url and region:
                        mapping[f"{region}_{policy_name}"] = url

            logger.info(f"✅ CSV 로드 성공: {csv_path} ({len(mapping)}개 매핑)")
            logger.info(f"📋 매핑 예시: {list(mapping.keys())[:3]}")
        except FileNotFoundError:
            logger.warning(f"⚠️ policy_mapping.csv 파일을 찾을 수 없습니다: {csv_path}")
        except Exception as e:
            logger.error(f"❌ CSV 로드 실패: {e}")

        return mapping

    def process_question(self, question: str, user_region: Optional[str] = None) -> Dict[str, Any]:
        """질문 처리 및 응답 생성"""
        logger.info(f"\n{'='*60}")
        logger.info(f"🔔 새로운 질문 처리 시작: '{question}'")
        logger.info(f"{'='*60}")

        # 1단계: 의도 분석
        intent = self._analyze_intent(question)
        logger.info(f"🎯 의도 분석 결과: '{intent}'")

        if intent == "casual_conversation":
            logger.info("💬 캐주얼 대화로 처리 중...")
            return self._generate_casual_response(question)
        elif intent == "irrelevant":
            logger.info("🚫 무관한 질문으로 처리 중...")
            return self._generate_irrelevant_response(question)

        logger.info("📋 복지 관련 질문으로 처리 - Advanced RAG 시작")

        # 2단계: 지역 우선순위 결정
        # 우선순위 1: 사용자 프로필의 '사는 지역' (최우선!)
        # 우선순위 2: 질문에 명시된 지역 (프로필 없을 때만)
        # 우선순위 3: 전국 + 랜덤 지역 (둘 다 없을 때)

        target_region = None
        question_region = extract_region_from_question(question)

        if user_region:
            # 1순위: 사용자 프로필의 지역 (질문에 지역이 있어도 무시!)
            target_region = map_user_region_to_data_folder(user_region)
            if question_region and question_region != target_region:
                logger.info(f"⚠️ 질문에 '{question_region}' 지역이 있지만, 사용자 프로필 '{target_region}' 우선 적용")
            else:
                logger.info(f"✅ 사용자 프로필 지역: {user_region} → {target_region}")
        elif question_region:
            # 2순위: 질문에서 지역 추출 (프로필 없을 때만)
            target_region = question_region
            logger.info(f"✅ 질문에서 지역 추출: {target_region}")
        else:
            # 3순위: 둘 다 없음 - None으로 유지 (나중에 랜덤 지역 처리)
            logger.info(f"ℹ️ 지역 정보 없음 - 전국 + 랜덤 지역으로 답변")

        # 3-5단계: Advanced RAG Pipeline 실행
        rag_result = self.advanced_rag.process(
            query=question,
            vector_store=self.vector_store,
            embedder=self.embedder,
            top_k=TOP_K_RESULTS
        )

        if rag_result['documents']:
            # 지역 기반 문서 정렬 (Advanced RAG 후)
            relevant_docs = rag_result['documents']
            if target_region:
                relevant_docs = self._sort_docs_by_region(relevant_docs, target_region)
                logger.info(f"지역 '{target_region}' 기준으로 재정렬 완료")

            # 텍스트 정제 및 최종 답변 생성
            return self._generate_welfare_response(question, relevant_docs, target_region)
        else:
            logger.warning(f"관련 문서 없음 - 기본 응답 반환")
            return self._generate_no_docs_response(question)

    def _analyze_intent(self, question: str) -> str:
        """의도 분석 - 복지 정책 관련 질문만 처리"""
        # 1단계: 복지 관련 키워드 확인 (가장 중요!)
        welfare_keywords = [
            '복지', '노인', '어르신', '고령자', '연금', '의료비', '건강보험',
            '장기요양', '돌봄', '경로당', '틀니', '보청기', '목욕', '이미용',
            '식사배달', '효도수당', '장수축하', '참전유공자', '보훈',
            '기초생활수급', '의료급여', '국민기초생활보장', '차상위',
            '긴급복지', '지원', '수당', '서비스', '정책', '혜택', '신청',
            '요양', '간병', '재활', '건강', '의료', '병원', '약', '치료',
            '경로우대', '할인', '교통', '버스', '지하철', '복지관',
            '노인회관', '양로원', '요양원', '급여', '보조금'
        ]

        # 복지 키워드가 있으면 welfare_inquiry로 처리
        for keyword in welfare_keywords:
            if keyword in question:
                return "welfare_inquiry"

        # 2단계: 인사/감사 패턴 (간단한 응답)
        greeting_patterns = [
            r'^안녕$|^안녕하세요$|^안녕하십니까$',
            r'^hi$|^hello$|^하이$',
            r'고마워|감사합니다|고맙습니다'
        ]

        for pattern in greeting_patterns:
            if re.search(pattern, question.strip(), re.IGNORECASE):
                return "casual_conversation"

        # 3단계: 무관한/욕설/공격적 질문 패턴
        irrelevant_patterns = [
            # 욕설 및 비하 표현
            r'바보|멍청|똥|쓰레기|꺼져|닥쳐|시끄|죽어',
            r'fuck|shit|damn|stupid|idiot',

            # 전혀 무관한 주제
            r'자동차|여행|코딩|프로그래밍|스포츠|축구|야구',
            r'주식|투자|부동산|쇼핑|패션|뷰티',
            r'수학|물리|화학|영어|일본어|중국어',
            r'아이스크림|피자|치킨|맥주|음료|카페',
            r'게임|영화|드라마|음악|연예인|아이돌',
            r'컴퓨터|핸드폰|스마트폰|태블릿|노트북',
            r'날씨|기온|비|눈|태풍',
            r'정치|선거|대통령|국회의원',

            # 테스트성 질문
            r'테스트|test|ㅋ|ㅎ|ㄱ|ㄴ|123|abc'
        ]

        for pattern in irrelevant_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                return "irrelevant"

        # 4단계: 질문이 너무 짧거나 의미없는 경우
        if len(question.strip()) < 2:
            return "irrelevant"

        # 5단계: 기본값 - 무관한 질문으로 처리 (복지 키워드 없으면 거부)
        # 이전에는 welfare_inquiry로 처리했지만, 이제는 irrelevant로 처리
        return "irrelevant"

    def _generate_casual_response(self, question: str) -> Dict[str, Any]:
        """캐주얼 대화 응답"""
        responses = {
            "greeting": "안녕하세요! 노인복지 정책에 대해 궁금한 것이 있으시면 언제든 물어보세요.",
            "thanks": "천만에요! 더 궁금한 복지 정책이 있으시면 언제든 말씀해주세요.",
            "general": "안녕하세요! 저는 노인복지 정책 상담을 도와드리는 AI입니다. 복지 관련 질문을 해주시면 도움을 드릴게요!"
        }

        # 간단한 패턴 매칭
        if any(word in question for word in ['안녕', '하이', 'hi', 'hello']):
            response_text = responses["greeting"]
        elif any(word in question for word in ['고마워', '감사', '잘했어']):
            response_text = responses["thanks"]
        else:
            response_text = responses["general"]

        return {
            "answer": response_text,
            "intent": "casual_conversation",
            "sources": [],
            "confidence": "high"
        }

    def _generate_irrelevant_response(self, question: str) -> Dict[str, Any]:
        """무관한 질문 응답"""
        response = """죄송하지만, 저는 노인복지 정책 전문 상담 AI입니다.

다음과 같은 노인복지 관련 질문에 답변드릴 수 있습니다:
• 기초연금 및 노인수당
• 의료비 지원 (건강보험료, 장기요양보험료)
• 노인돌봄서비스 (식사배달, 목욕서비스 등)
• 보건의료 지원 (틀니, 보청기, 건강검진 등)
• 참전유공자 예우
• 지역별 노인복지 정책

복지 정책에 대해 궁금한 점이 있으시면 언제든 말씀해주세요!"""

        return {
            "answer": response,
            "intent": "irrelevant",
            "sources": [],
            "confidence": "high"
        }

    def _sort_docs_by_region(self, docs: List[Dict], target_region: str) -> List[Dict]:
        """
        지역 기반으로 문서 정렬

        우선순위:
        1. '전국' 문서 (최우선! - 모든 지역에 적용되는 정책)
        2. target_region과 일치하는 문서
        3. 다른 지역 문서
        """
        nationwide_docs = []
        target_docs = []
        other_docs = []

        for doc in docs:
            region = doc['metadata'].get('region', '')
            if region == '전국':
                nationwide_docs.append(doc)
            elif region == target_region:
                target_docs.append(doc)
            else:
                other_docs.append(doc)

        # 우선순위에 따라 정렬: 전국 → 해당 지역 → 다른 지역
        return nationwide_docs + target_docs + other_docs

    def _clean_pdf_text(self, text: str) -> str:
        """PDF 텍스트 정제 - 메타데이터 제거 및 정리"""
        # 1. 페이지 구분선 제거
        text = re.sub(r'---\s*페이지\s*\d+\s*---', '', text)

        # 2. 연속된 공백/줄바꿈 정리
        text = re.sub(r'\n{3,}', '\n\n', text)  # 3개 이상 줄바꿈 → 2개로
        text = re.sub(r'[ \t]{2,}', ' ', text)  # 2개 이상 공백 → 1개로

        # 3. 불필요한 특수문자 제거
        text = text.replace('･', '·')
        text = text.replace('‑', '-')

        # 4. 법령/문서 메타정보 패턴 제거
        text = re.sub(r'법제처\s*\d+', '', text)
        text = re.sub(r'국가법령정보센터', '', text)
        text = re.sub(r'\[시행\s*[\d\.\s]+\]', '', text)
        text = re.sub(r'\[법률\s*제\d+호.*?\]', '', text)
        text = re.sub(r'발\s*간\s*등\s*록\s*번\s*호', '', text)
        text = re.sub(r'\d{2}-\d{7}-\d{6}-\d{2}', '', text)  # 등록번호

        # 5. 연락처 패턴 간소화
        text = re.sub(r'보건복지부\s*\(.*?\)\s*\d{3}-\d{3}-\d{4}', '보건복지부', text)

        # 6. 불필요한 기호 정리
        text = re.sub(r'[①②③④⑤⑥⑦⑧⑨⑩]', '•', text)

        # 7. 앞뒤 공백 제거
        text = text.strip()

        return text

    def _extract_key_sentences(self, text: str, max_sentences: int = 3, question: str = "") -> str:
        """핵심 문장 추출 - 복지 관련 내용 + 질문 관련성 체크"""
        # 문장 단위로 분리
        sentences = re.split(r'[\n]+', text)

        # 필터링: 정책/복지 관련 핵심 문장만
        key_sentences = []
        priority_keywords = [
            '지원', '급여', '혜택', '신청', '대상', '조건', '기준',
            '서비스', '정책', '복지', '노인', '어르신', '수당', '연금',
            '의료', '건강', '요양', '돌봄', '보조', '할인', '제공',
            '사업', '프로그램', '교육', '활동', '보험', '장기요양',
            '무료', '감면', '요금', '교통', '시설', '이용', '경로'
        ]

        # 질문에서 핵심 키워드 추출
        question_keywords = []
        if question:
            # 2글자 이상 한글/영문 단어 추출
            words = re.findall(r'[가-힣a-zA-Z]{2,}', question)
            question_keywords = [w for w in words if w not in ['누가', '어떻게', '무엇', '어디', '언제', '왜']]

        # 명확하게 제외할 메타정보와 법률 제목
        exclude_keywords = [
            '페이지', '법제처', '국가법령정보센터', '발간등록번호',
            'Ministry', 'www.', 'http://', 'https://',
            '제', '조', '항', '호'  # 법률 조항
        ]

        # 제외할 패턴
        exclude_patterns = [
            r'^제\d+조',  # "제30조"로 시작
            r'^\d+\.',  # 숫자로 시작하는 조항
            r'법률.*?제\d+호',  # 법률 제xx호
            r'이\s*법은.*?시행한다',  # 법률 시행일
            r'보상청구서.*?증명서류',  # 법률 절차
            r'귀하의.*?지원내용',  # 서식 제목
        ]

        # 불완전한 문장 패턴
        incomplete_patterns = [
            r'^[가-힣]{1,2}의\s',  # "의", "체의" 등으로 시작
            r'할\s*수\s*있$',  # "할 수 있"으로 끝남
            r'^[ㄱ-ㅎㅏ-ㅣ]{1}',  # 자음/모음으로 시작
        ]

        for sentence in sentences:
            sentence = sentence.strip()

            # 1. 너무 짧은 문장 제외
            if len(sentence) < 15:
                continue

            # 2. 명확한 메타정보 제외
            if any(meta in sentence for meta in exclude_keywords):
                continue

            # 3. 제외 패턴 체크
            is_excluded = False
            for pattern in exclude_patterns:
                if re.search(pattern, sentence):
                    is_excluded = True
                    break
            if is_excluded:
                continue

            # 4. 불완전 패턴 제외
            is_incomplete = False
            for pattern in incomplete_patterns:
                if re.search(pattern, sentence):
                    is_incomplete = True
                    break
            if is_incomplete:
                continue

            # 5. 복지 키워드 포함 여부
            has_priority_keyword = any(keyword in sentence for keyword in priority_keywords)

            # 6. 질문 관련성 체크 (질문 키워드가 있으면)
            has_question_keyword = False
            if question_keywords:
                has_question_keyword = any(kw in sentence for kw in question_keywords)

            # 우선순위: 질문 키워드 + 복지 키워드 모두 포함
            # 또는 복지 키워드만 포함
            if (has_question_keyword and has_priority_keyword) or has_priority_keyword:
                # 문장 다듬기
                cleaned_sentence = sentence
                # 불릿포인트 제거
                cleaned_sentence = re.sub(r'^[•·∙※\-]\s*', '', cleaned_sentence)
                # 특수문자 정리
                cleaned_sentence = re.sub(r'[ㆍ]', ' ', cleaned_sentence)
                cleaned_sentence = re.sub(r'\s+', ' ', cleaned_sentence)

                # 질문 키워드 포함 문장은 앞쪽에 배치
                if has_question_keyword:
                    key_sentences.insert(0, (cleaned_sentence.strip(), 2))  # 높은 우선순위
                else:
                    key_sentences.append((cleaned_sentence.strip(), 1))  # 낮은 우선순위

            if len(key_sentences) >= max_sentences * 3:  # 여유있게 수집
                break

        # 우선순위 정렬 및 중복 제거
        key_sentences.sort(key=lambda x: x[1], reverse=True)
        unique_sentences = []
        seen = set()
        for sent, priority in key_sentences:
            if sent not in seen and len(sent) >= 15:
                unique_sentences.append(sent)
                seen.add(sent)
                if len(unique_sentences) >= max_sentences:
                    break

        return '\n'.join(unique_sentences[:max_sentences])

    def _generate_welfare_response(self, question: str, relevant_docs: List[Dict], target_region: Optional[str] = None) -> Dict[str, Any]:
        """복지 관련 응답 생성 - OpenAI LLM 기반 + 검증용 원본 버전 제공"""
        logger.info("🤖 OpenAI LLM 기반 답변 생성 시작...")

        # 1단계: Enhanced Policy Formatter로 원본 버전 생성 (검증용)
        formatted_response = self._generate_formatted_response_fallback(question, relevant_docs, target_region)
        formatted_answer = formatted_response.get('answer', '')

        # OpenAI 클라이언트가 없으면 폴백 (원본 버전만 반환)
        if not self.client:
            logger.warning("⚠️ OpenAI 클라이언트 없음 - 원본 버전만 반환")
            formatted_response['answer_before_llm'] = formatted_answer
            formatted_response['answer_after_llm'] = formatted_answer
            return formatted_response

        # 2단계: 문서 정보 추출 및 컨텍스트 구성 (URL 포함)
        context_parts = []
        seen_regions = set()
        policy_urls = {}  # 정책명 -> URL 매핑

        for doc in relevant_docs[:10]:  # 최대 10개 문서 사용
            region = doc['metadata'].get('region', '지역미상')
            filename = doc['metadata'].get('filename', '정책문서.pdf')

            # Enhanced Policy Formatter로 정보 추출
            policy_result = self.policy_formatter.format_document(doc, question=question)

            if policy_result and policy_result.get('has_content'):
                formatted_text = policy_result.get('formatted_text', '')
                policy_name = policy_result.get('policy_name', '')

                if len(formatted_text) > 20:
                    # URL 찾기 - CSV에 지역+정책명이 정확히 일치하는 경우만 사용
                    url = None

                    if policy_name:
                        # CSV에서 region_정책명 조합 확인 (정확한 일치만 허용)
                        region_policy_key = f"{region}_{policy_name}"

                        if region_policy_key in self.policy_url_mapping:
                            # 정확히 일치: CSV에 해당 지역+정책 조합 존재
                            url = self.policy_url_mapping[region_policy_key]
                            logger.info(f"✅ URL 매칭 성공: {region} - {policy_name}")
                        else:
                            # CSV에 없음: URL 제외
                            logger.debug(f"⚠️ CSV에 없는 정책 조합 (URL 제외): {region} - {policy_name}")

                    # 컨텍스트에 URL 정보 추가 (CSV에 정확히 일치하는 경우만)
                    context_entry = f"[{region} - {filename}]\n{formatted_text}"
                    if url:
                        context_entry += f"\n[신청/상세정보 URL: {url}]"
                        policy_urls[policy_name or filename] = url

                    context_parts.append(context_entry)
                    seen_regions.add(region)

        if not context_parts:
            logger.warning("⚠️ 추출된 정책 정보 없음")
            return self._generate_no_docs_response(question)

        context = "\n\n---\n\n".join(context_parts[:8])  # 최대 8개 컨텍스트
        logger.info(f"📄 컨텍스트 구성 완료: {len(context_parts)}개 정책, {len(context)}자")

        # 2단계: LLM 프롬프트 구성
        prompt = self._build_llm_prompt(question, context, target_region, seen_regions)

        # 3단계: OpenAI API 호출
        try:
            logger.info("🔄 OpenAI API 호출 중...")
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": """당신은 노인복지 정책 전문 상담사입니다.
제공된 정책 자료만을 바탕으로 정확하고 친절하게 답변하세요.
자료에 없는 내용은 절대 지어내지 마세요.
복지 정책과 무관한 질문에는 답변하지 마세요."""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=TEMPERATURE,
                max_tokens=MAX_TOKENS
            )

            llm_answer = response.choices[0].message.content.strip()
            logger.info(f"✅ LLM 답변 생성 완료 (길이: {len(llm_answer)}자)")

            # 4단계: 추가 안내 메시지 추가
            answer_parts = [llm_answer]
            answer_parts.append(f"\n\n💡 **추가 문의**")
            answer_parts.append(f"\n• 더 자세한 내용은 관할 주민센터나 구청에 문의하세요.")
            answer_parts.append(f"\n• 복지로 홈페이지(www.bokjiro.go.kr)에서도 확인할 수 있습니다.")
            answer_parts.append(f"\n• 보건복지상담센터: 129")

            llm_final_answer = "\n".join(answer_parts)
            sources = self._extract_sources(relevant_docs)

            return {
                "answer": llm_final_answer,  # 기본 답변 (일반 챗봇용)
                "answer_before_llm": formatted_answer,  # LLM 전 (검증용)
                "answer_after_llm": llm_final_answer,   # LLM 후 (검증용)
                "intent": "welfare_inquiry",
                "sources": sources,
                "confidence": "high",
                "context_used": len(relevant_docs),
                "method": "openai_llm"
            }

        except Exception as e:
            logger.error(f"❌ OpenAI API 호출 실패: {e}")
            # 실패 시에도 두 버전 제공 (같은 내용)
            fallback_response = self._generate_formatted_response_fallback(question, relevant_docs, target_region)
            fallback_answer = fallback_response.get('answer', '')
            fallback_response['answer_before_llm'] = fallback_answer
            fallback_response['answer_after_llm'] = fallback_answer
            return fallback_response

    def _generate_no_docs_response(self, question: str) -> Dict[str, Any]:
        """관련 문서 없음 응답"""
        response = f"""질문하신 '{question}'에 대한 정확한 정보를 현재 보유한 복지 정책 자료에서 찾지 못했습니다.

다음과 같은 방법으로 도움을 받으실 수 있습니다:
• 가까운 주민센터 또는 구청 방문
• 복지로 홈페이지(www.bokjiro.go.kr) 확인
• 보건복지상담센터(129) 전화상담

더 구체적인 복지 정책에 대해 질문해주시면 도움을 드리겠습니다."""

        return {
            "answer": response,
            "intent": "welfare_inquiry",
            "sources": [],
            "confidence": "low"
        }

    def _generate_fallback_response(self, question: str, relevant_docs: List[Dict]) -> Dict[str, Any]:
        """폴백 응답 - DB 데이터 정제 사용"""
        if relevant_docs:
            answer_parts = []
            answer_parts.append(f"'{question}'에 대한 관련 복지 정책 정보입니다.\n")

            for i, doc in enumerate(relevant_docs[:5], 1):
                region = doc['metadata'].get('region', '지역미상')
                filename = doc['metadata'].get('filename', '정책문서')
                content = doc['content']

                # 텍스트 정제
                cleaned_content = self._clean_pdf_text(content)
                key_content = self._extract_key_sentences(cleaned_content, max_sentences=2)

                if key_content and len(key_content) > 20:
                    answer_parts.append(f"\n**{i}. {region} 지역 정책**\n")
                    answer_parts.append(f"• {key_content}\n")
                    answer_parts.append(f"  (출처: {filename})\n")

            answer_parts.append(f"\n💡 **추가 정보**\n")
            answer_parts.append(f"• 더 자세한 내용은 관할 주민센터나 구청에 문의하세요.\n")
            answer_parts.append(f"• 복지로 홈페이지(www.bokjiro.go.kr)에서도 확인할 수 있습니다.\n")

            response = "".join(answer_parts)
        else:
            response = self._generate_no_docs_response(question)["answer"]

        sources = self._extract_sources(relevant_docs)

        return {
            "answer": response,
            "intent": "welfare_inquiry",
            "sources": sources,
            "confidence": "medium",
            "method": "db_cleaned_fallback"
        }

    def _build_context(self, relevant_docs: List[Dict]) -> str:
        """컨텍스트 구성"""
        context_parts = []

        for i, doc in enumerate(relevant_docs[:5]):
            filename = doc['metadata'].get('filename', f'문서{i+1}')
            region = doc['metadata'].get('region', '지역미상')
            content = doc['content'][:500]  # 길이 제한

            context_parts.append(f"[{filename} - {region}지역]\n{content}")

        return "\n\n---\n\n".join(context_parts)

    def _build_welfare_prompt(self, question: str, context: str, target_region: Optional[str] = None) -> str:
        """복지 정책 프롬프트 구성"""
        region_instruction = ""
        if target_region:
            region_instruction = f"\n- **중요**: 사용자의 거주 지역은 '{target_region}'입니다. 이 지역의 정보를 우선적으로 제공하되, 전국 공통 정책도 함께 안내해주세요."
        else:
            region_instruction = "\n- 지역별로 정책이 다를 경우, 가능한 모든 지역의 정보를 포함하여 안내해주세요."

        return f"""다음 복지 정책 자료를 바탕으로 질문에 답변해주세요:

【정책 자료】
{context}

【질문】
{question}

【답변 지침】{region_instruction}
- 제공된 자료를 바탕으로 정확하고 친절하게 답변해주세요
- 구체적인 수치나 조건이 있다면 명시해주세요
- 신청 방법이나 절차가 있다면 안내해주세요
- 여러 지역의 정보가 있다면 각 지역별로 구분하여 설명해주세요
- 불확실한 정보는 관련 기관 문의를 권해주세요

답변:"""

    def _build_llm_prompt(self, question: str, context: str, target_region: Optional[str], seen_regions: set) -> str:
        """LLM 프롬프트 구성 - 환각 방지 강화 + 지역 표시 강제 + 2개 정책 제한"""
        region_info = ""
        if target_region:
            region_info = f"\n**중요**: 사용자의 거주 지역은 '{target_region}'입니다. 이 지역의 정책을 설명해주세요."
        elif seen_regions:
            regions_str = ', '.join(sorted(seen_regions))
            region_info = f"\n**참고**: 현재 자료에는 다음 지역의 정보가 있습니다: {regions_str}"

        return f"""아래 복지 정책 자료를 바탕으로 질문에 답변해주세요.

【정책 자료】
{context}

【질문】
{question}

【답변 작성 지침】{region_info}
1. **제공된 자료에만 기반**하여 답변하세요. 자료에 없는 내용은 절대 만들어내지 마세요.

2. **정확히 2개의 정책만 설명하세요** (필수! 절대 3개 이상 쓰지 마세요):
   - 우선순위 1: 전국 정책 1개 (자료에 '전국'이 있으면 반드시 먼저)
   - 우선순위 2: 시도 지역 정책 1개 (사용자 지역 우선, 없으면 자료 중 하나)
   - 총 2개 초과하면 안 됩니다!

3. **정책 설명 시 반드시 지역을 명시하세요**:
   - 각 정책 앞에 반드시 지역 정보를 포함하세요
   - 예시: "**부산 지역 - 노인일자리사업**" 또는 "**전국 - 기초연금**"
   - 지역 정보가 없는 정책 설명은 절대 작성하지 마세요

4. **깔끔한 포맷팅 사용**:
   - 정책별로 명확히 구분하세요
   - 불릿 포인트(•)나 하이픈(-) 대신 **볼드체**와 줄바꿈으로 구조화하세요
   - 각 섹션(지원 대상, 지원 내용, 신청 방법)은 볼드체로 제목을 표시하세요

5. 정책명, 지원 대상, 지원 내용, 신청 방법을 명확히 구분하여 설명하세요.

6. 구체적인 금액, 조건, 기준이 있다면 정확히 명시하세요.

7. **신청 방법 작성 시**: 자료에 "[신청/상세정보 URL: ...]" 형식의 링크가 있으면 반드시 신청 방법 섹션에 포함하세요.
   예시: "**신청 방법**: 거주지 주민센터 방문 또는 온라인 신청 ([상세정보 보기](URL))"

8. **중요**: 사용자가 명시적으로 요청한 정보에 대해서만 답변하세요. 사용자가 묻지 않은 지역이나 정책에 대해 "없다"고 언급하지 마세요.

9. 제공된 자료에 있는 정책만 설명하고, 자료에 없는 지역/정책은 아예 언급하지 마세요.

10. 친절하고 이해하기 쉬운 말투로 작성하세요.

【답변 형식 예시 - 정확히 2개만!】
## 전국 - 국민기초생활보장

**지원 대상**
소득인정액이 기준 중위소득 30% 이하인 가구

**지원 내용**
생계급여, 의료급여, 주거급여, 교육급여 제공

**신청 방법**
거주지 주민센터 방문 신청

---

## 부산 지역 - 노인일자리 및 사회활동 지원사업

**지원 대상**
지역사회 내 노인

**지원 내용**
공익 서비스 활동 지원

**신청 방법**
거주지 노인복지관 또는 주민센터 신청

답변:"""

    def _generate_formatted_response_fallback(self, question: str, relevant_docs: List[Dict], target_region: Optional[str] = None) -> Dict[str, Any]:
        """OpenAI 실패 시 폴백 - Enhanced Policy Formatter 사용"""
        logger.warning("⚠️ 폴백 모드: Enhanced Policy Formatter 사용")

        # DB에서 가져온 문서들로 답변 구성
        answer_parts = []
        answer_parts.append(f"'{question}'에 대한 복지 정책 정보를 안내해드리겠습니다.\n")

        # 문서별로 정보 정리
        seen_regions = set()
        doc_info_by_region = {}

        for doc in relevant_docs:
            region = doc['metadata'].get('region', '지역미상')
            filename = doc['metadata'].get('filename', '정책문서.pdf')

            # Enhanced Policy Formatter를 사용하여 정책 정보 추출
            policy_result = self.policy_formatter.format_document(doc, question=question)

            # 비어있으면 건너뛰기
            if not policy_result or not policy_result.get('has_content'):
                continue

            formatted_text = policy_result.get('formatted_text')
            policy_name = policy_result.get('policy_name', '')

            if not formatted_text or len(formatted_text) < 20:
                continue

            # URL 찾기 - CSV에 지역+정책명이 정확히 일치하는 경우만 사용
            url = None
            if policy_name:
                region_policy_key = f"{region}_{policy_name}"
                if region_policy_key in self.policy_url_mapping:
                    url = self.policy_url_mapping[region_policy_key]
                    logger.info(f"✅ [폴백] URL 매칭 성공: {region} - {policy_name}")
                else:
                    logger.debug(f"⚠️ [폴백] CSV에 없는 정책 조합 (URL 제외): {region} - {policy_name}")

            # URL이 있으면 formatted_text에 추가
            if url:
                formatted_text += f"\n**신청/상세정보**: [바로가기]({url})"

            # 지역별로 문서 그룹화
            if region not in doc_info_by_region:
                doc_info_by_region[region] = []

            # 중복 방지: 같은 내용이 이미 있으면 건너뛰기
            if formatted_text not in str(doc_info_by_region[region]):
                doc_info_by_region[region].append({
                    'filename': filename,
                    'region': region,
                    'content': formatted_text
                })

        # ===== 핵심 로직: 정확히 2개의 정책만 표시 =====
        # 0순위: 전국 정책 1개 (있으면 무조건 먼저!)
        # 1순위: 시도 정책 1개 (target_region > 랜덤)

        policies_shown = 0  # 표시된 정책 수 추적

        # 0순위: 전국 정책 1개
        if '전국' in doc_info_by_region and policies_shown < 2:
            answer_parts.append(f"\n{doc_info_by_region['전국'][0]['content']}\n")
            seen_regions.add('전국')
            policies_shown += 1
            logger.info(f"✅ [0순위] 전국 정책 1개 추가")

        # 1순위: 시도 정책 1개
        if policies_shown < 2:
            if target_region and target_region in doc_info_by_region:
                # 1-1순위: target_region (사용자 프로필 또는 질문에서 추출)
                answer_parts.append(f"\n{doc_info_by_region[target_region][0]['content']}\n")
                seen_regions.add(target_region)
                policies_shown += 1
                logger.info(f"✅ [1순위] {target_region} 지역 정책 1개 추가")
            else:
                # 1-2순위: 랜덤 지역 (target_region이 없거나 데이터 없을 때)
                other_regions = [r for r in doc_info_by_region.keys() if r not in seen_regions]
                if other_regions:
                    random_region = random.choice(other_regions)
                    answer_parts.append(f"\n{doc_info_by_region[random_region][0]['content']}\n")
                    policies_shown += 1
                    logger.info(f"✅ [1순위-랜덤] {random_region} 지역 정책 1개 추가")

        logger.info(f"📊 총 {policies_shown}개 정책 표시됨 (목표: 2개)")

        # 추가 안내 메시지
        answer_parts.append(f"\n💡 **추가 문의**\n")
        answer_parts.append(f"• 더 자세한 내용은 관할 주민센터나 구청에 문의하세요.\n")
        answer_parts.append(f"• 복지로 홈페이지(www.bokjiro.go.kr)에서도 확인할 수 있습니다.\n")
        answer_parts.append(f"• 보건복지상담센터: 129\n")

        answer = "".join(answer_parts)

        # 소스 정보 추가
        sources = self._extract_sources(relevant_docs)

        logger.info(f"✅ 폴백 답변 생성 완료 (길이: {len(answer)}자)")

        return {
            "answer": answer,
            "intent": "welfare_inquiry",
            "sources": sources,
            "confidence": "medium",
            "context_used": len(relevant_docs),
            "method": "enhanced_policy_extraction_fallback"
        }

    def _extract_sources(self, relevant_docs: List[Dict]) -> List[Dict[str, str]]:
        """소스 정보 추출"""
        sources = []
        seen_files = set()

        for doc in relevant_docs:
            metadata = doc['metadata']
            filename = metadata.get('filename', '문서명 없음')

            if filename not in seen_files:
                sources.append({
                    'filename': filename,
                    'region': metadata.get('region', '지역미상'),
                    'file_type': metadata.get('file_type', '유형미상')
                })
                seen_files.add(filename)

        return sources

class SimpleWelfareBot:
    """단순화된 복지 봇 인터페이스"""

    def __init__(self, rag_chain: WelfareRAGChain):
        self.rag_chain = rag_chain

    def get_response(self, question: str) -> Dict[str, Any]:
        """질문에 대한 응답 반환"""
        if not question or not question.strip():
            return {
                "answer": "질문을 입력해주세요.",
                "intent": "empty",
                "sources": [],
                "confidence": "high"
            }

        # RAG 체인을 통한 응답 생성
        return self.rag_chain.process_question(question.strip())

    def get_formatted_response(self, question: str) -> str:
        """포맷된 응답 반환"""
        result = self.get_response(question)

        answer = result.get("answer", "죄송합니다. 응답을 생성할 수 없습니다.")
        sources = result.get("sources", [])

        # 소스 정보 추가
        if sources:
            source_text = "\n\n📚 **참고자료:**\n"
            for i, source in enumerate(sources[:3]):
                source_text += f"{i+1}. {source['filename']} ({source['region']})\n"
            answer += source_text

        return answer
