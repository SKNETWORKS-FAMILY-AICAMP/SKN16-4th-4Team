"""
정책 정보 추출 모듈 - 개선된 버전

PDF 문서에서 정책명, 설명, 대상자, 신청방법 등을 추출하여 구조화
"""

import re
import logging
from typing import Dict, List, Optional, Any
from .policy_metadata import find_policy_metadata

logger = logging.getLogger(__name__)


class SimplePolicyExtractor:
    """개선된 정책 정보 추출기 - 불필요한 정보 강력 필터링"""

    def extract_from_text(self, text: str, question: str = "") -> Dict[str, str]:
        """
        텍스트에서 정책 정보 추출

        Returns:
            {
                'name': 정책명,
                'description': 설명,
                'target': 대상,
                'benefits': 혜택,
                'application': 신청방법
            }
        """
        lines = [line.strip() for line in text.split('\n') if line.strip()]

        # 질문에서 키워드 추출
        question_keywords = self._extract_question_keywords(question)

        result = {
            'name': None,
            'description': None,
            'target': None,
            'benefits': None,
            'application': None
        }

        # 정책명 추출
        result['name'] = self._find_policy_name(lines)

        # 각 항목별로 관련 문장 수집 (여러 개 수집 후 가장 좋은 것 선택)
        target_candidates = []
        benefit_candidates = []
        application_candidates = []
        description_candidates = []

        for i, line in enumerate(lines):
            # 너무 짧거나 메타데이터면 스킵
            if len(line) < 20 or self._is_junk(line):
                continue

            # 법률 조문만 있는 라인 제외
            if self._is_pure_law_reference(line):
                continue

            # 부처 연락처만 있는 라인 제외
            if self._is_government_contact(line):
                continue

            cleaned_line = self._clean_sentence(line)

            # 대상 찾기
            if self._is_target_line(line):
                score = self._score_target_line(cleaned_line)
                if score > 0:
                    target_candidates.append((cleaned_line, score))

            # 혜택 찾기
            if self._is_benefit_line(line):
                score = self._score_benefit_line(cleaned_line)
                if score > 0:
                    benefit_candidates.append((cleaned_line, score))

            # 신청 찾기
            if self._is_application_line(line):
                score = self._score_application_line(cleaned_line)
                if score > 0:
                    application_candidates.append((cleaned_line, score))

            # 설명 찾기 (복지 키워드 + 설명 키워드)
            if self._is_description_line(line, question_keywords):
                score = self._score_description_line(cleaned_line, question_keywords)
                if score > 0:
                    description_candidates.append((cleaned_line, score))

        # 가장 점수가 높은 후보 선택
        if target_candidates:
            target_candidates.sort(key=lambda x: x[1], reverse=True)
            result['target'] = target_candidates[0][0][:200]

        if benefit_candidates:
            benefit_candidates.sort(key=lambda x: x[1], reverse=True)
            result['benefits'] = benefit_candidates[0][0][:200]

        if application_candidates:
            application_candidates.sort(key=lambda x: x[1], reverse=True)
            result['application'] = application_candidates[0][0][:200]

        if description_candidates:
            description_candidates.sort(key=lambda x: x[1], reverse=True)
            result['description'] = description_candidates[0][0][:250]

        return result

    def _extract_question_keywords(self, question: str) -> List[str]:
        """질문에서 핵심 키워드 추출"""
        if not question:
            return []

        # 불용어 제거
        stopwords = ['누가', '어떻게', '무엇', '어디', '언제', '왜', '있나요', '있어요', '알려주세요', '뭐야', '어떤', '것들']
        words = re.findall(r'[가-힣]{2,}', question)
        return [w for w in words if w not in stopwords]

    def _find_policy_name(self, lines: List[str]) -> Optional[str]:
        """정책명 찾기 - 여러 패턴 시도"""
        for line in lines[:10]:  # 첫 10줄에서만 검색
            # 1. 「정책명」 패턴
            match = re.search(r'「([^」]{3,40})」', line)
            if match:
                name = match.group(1)
                # 법률명 제외
                if '법률' not in name and '법' not in name[-1:]:
                    return name

            # 2. 숫자. 정책명 패턴
            match = re.match(r'^\d+[\.\)]\s*(.+)', line)
            if match:
                name = match.group(1).strip()
                if 5 <= len(name) <= 50 and any(kw in name for kw in ['사업', '지원', '서비스', '제도', '급여', '연금', '수당']):
                    return name

            # 3. 복지 키워드 + 정책 키워드
            if any(kw in line for kw in ['노인', '어르신', '경로', '장기요양', '기초연금']):
                if any(kw in line for kw in ['사업', '지원', '서비스', '제도', '급여', '연금', '수당']):
                    if 5 <= len(line) <= 50:
                        return line

        return None

    def _is_target_line(self, line: str) -> bool:
        """대상자 관련 문장인지 확인"""
        keywords = ['대상', '신청자격', '수급권자', '받을 수 있', '이용할 수 있', '신청할 수 있', '해당하는 사람', '해당자']
        return any(kw in line for kw in keywords)

    def _is_benefit_line(self, line: str) -> bool:
        """혜택 관련 문장인지 확인"""
        keywords = ['지원내용', '혜택', '급여', '무료', '할인', '감면', '지급', '제공']
        has_keyword = any(kw in line for kw in keywords)
        # 금액이 포함되어 있으면 우선
        has_amount = bool(re.search(r'\d+[만원천백십억조]', line))
        return has_keyword or has_amount

    def _is_application_line(self, line: str) -> bool:
        """신청방법 관련 문장인지 확인"""
        keywords = ['신청방법', '신청절차', '주민센터', '구청', '시청', '읍면동', '동사무소', '문의', '담당', '접수']
        has_keyword = any(kw in line for kw in keywords)
        # 전화번호 패턴
        has_phone = bool(re.search(r'\d{2,4}[- ]\d{3,4}[- ]\d{4}', line))
        return has_keyword or has_phone

    def _is_description_line(self, line: str, question_keywords: List[str]) -> bool:
        """설명 문장인지 확인"""
        # 질문 키워드가 있으면 우선
        if question_keywords and any(kw in line for kw in question_keywords):
            return True

        # 복지 + 설명 키워드
        welfare_kw = ['노인', '어르신', '대상', '혜택', '복지', '급여', '지원', '제공', '고령자']
        desc_kw = ['지원', '제공', '실시', '운영', '위한', '위해', '목적', '사업', '서비스', '프로그램']

        has_welfare = any(kw in line for kw in welfare_kw)
        has_desc = any(kw in line for kw in desc_kw)

        return has_welfare and has_desc

    def _is_junk(self, line: str) -> bool:
        """무용한 메타데이터인지 확인"""
        junk_patterns = [
            r'^제\d+조',  # 법조문
            r'법률\s*제\d+호',
            r'페이지|법제처|국가법령정보센터',
            r'발간등록번호',
            r'Ministry|www\.|http',
            r'^\d{4}년\s*\d{1,2}월\s*\d{1,2}일$',  # 날짜만 있는 줄
            r'^-{3,}$',  # 구분선만
            r'^[○●■□◇◆▶▷]\s*$',  # 불릿만
        ]

        for pattern in junk_patterns:
            if re.search(pattern, line):
                return True

        return False

    def _is_pure_law_reference(self, line: str) -> bool:
        """법률 조문 참조만 있는 라인인지 확인 - 매우 강력하게"""
        # 1. 법률명이 포함되면 무조건 제외
        if '「' in line and '」' in line:
            return True

        # 2. "이하 "약칭"" 패턴
        if re.search(r'이하\s*["\']', line):
            return True

        # 3. "제X조", "제X항", "제X호" 등 조문 패턴
        if re.search(r'제\d+조|제\d+항|제\d+호', line):
            return True

        # 4. 조항 번호로 시작 (①②③④⑤⑥⑦⑧⑨⑩)
        if re.match(r'^[①②③④⑤⑥⑦⑧⑨⑩]', line):
            return True

        # 5. 숫자로 시작하는 조항 (1. 2. 3. 4. 등)
        if re.match(r'^\d+\.\s', line):
            return True

        # 6. "이 법은", "이 영은" 등 법령 문구
        if re.search(r'이\s*법은|이\s*영은|이\s*규칙은', line):
            return True

        # 7. "공포", "시행" 등 법령 시행일 관련
        if '공포' in line and '시행' in line:
            return True

        # 8. "다만," 또는 "단서" 등 법률 특유 표현
        if re.search(r'다만,|단서|부칙|시행령|시행규칙', line):
            return True

        # 9. "귀하의 보호자, 지원기관" 등 서식 내용
        if '귀하의' in line and ('보호자' in line or '지원기관' in line):
            return True

        # 10. "질병관리청장", "특별자치시장" 등 행정 용어
        if any(kw in line for kw in ['질병관리청장', '특별자치시장', '특별자치도지사', '보상청구서', '첨부하여']):
            return True

        # 11. "변경：", "중지：" 등 안내문 패턴
        if re.match(r'^(변경|중지|정지|유의사항|참고|안내)[:：]\s*', line):
            return True

        # 12. "~의 변경을 초래하는" 등 절차 안내
        if re.search(r'변경을\s*초래하는|결혼·이혼|배우자의\s*사망', line):
            return True

        # 13. 주석/각주 패턴 ("*", "※" 등으로 시작)
        if re.match(r'^[*※＊]\s', line):
            return True

        # 14. "예상연금액", "실지급액" 등 안내 문구
        if re.search(r'예상연금액|실지급액|다를\s*수\s*있습니다', line):
            return True

        return False

    def _is_government_contact(self, line: str) -> bool:
        """부처 연락처 정보만 있는 라인인지 확인"""
        # 보건복지부 등 부처명 + 전화번호 패턴
        if re.search(r'보건복지부.*?\d{2,4}[-\s]\d{3,4}[-\s]\d{4}', line):
            # "총괄", "담당", "과" 등이 포함되면 단순 연락처
            if any(kw in line for kw in ['총괄', '담당', '정책과', '인권교육', '취업제한']):
                return True

        # "※ 보건복지부..." 패턴
        if re.match(r'^[※○●■]\s*보건복지부', line):
            return True

        return False

    def _score_target_line(self, line: str) -> float:
        """대상자 정보 점수 계산"""
        score = 0.0

        # 긍정 지표
        positive_keywords = [
            ('지원대상', 3.5), ('신청자격', 3.5), ('수급권자', 3.0),
            ('세 이상', 2.5), ('세이상', 2.5), ('이하인 자', 2.0), ('해당하는 자', 2.5),
            ('노인', 1.0), ('어르신', 1.0), ('고령자', 1.5),
            ('소득인정액', 2.5), ('기준중위소득', 3.0),
            ('가구', 1.5), ('만', 1.0), ('차상위', 2.0)
        ]

        for keyword, weight in positive_keywords:
            if keyword in line:
                score += weight

        # 나이 패턴 (만 XX세)
        if re.search(r'만\s*\d+세', line):
            score += 3.5

        # 부정 지표 (제외할 패턴) - 매우 강력하게
        negative_patterns = [
            (r'신청권자\s*:', -15.0),  # "신청권자: ..." 형식
            (r'신청권자\s*는', -15.0),  # 신청 권한만 설명
            (r'법률.*?제\d+호', -15.0),  # 법률 조문
            (r'「[^」]+」', -12.0),  # 법률명
            (r'이하\s*["\'][^"\']+["\']', -12.0),  # "이하 "약칭""
            (r'\d{3}[-\s]\d{3,4}[-\s]\d{4}', -15.0),  # 전화번호
            (r'보건복지부', -10.0),  # 부처명
            (r'^[※○●■]\s*', -5.0),  # 불릿으로 시작
        ]

        for pattern, weight in negative_patterns:
            if re.search(pattern, line):
                score += weight

        # 너무 짧으면 감점
        if len(line) < 30:
            score -= 3.0

        return score

    def _score_benefit_line(self, line: str) -> float:
        """혜택 정보 점수 계산"""
        score = 0.0

        # 긍정 지표
        positive_keywords = [
            ('지원내용', 3.5), ('지원금액', 3.5), ('급여내용', 3.5),
            ('지원금', 3.0), ('급여액', 3.0),
            ('월', 1.5), ('원', 1.5), ('만원', 3.0),
            ('무료', 3.0), ('할인', 3.0), ('감면', 3.0),
            ('제공', 1.0), ('지원', 1.0), ('지급', 2.5),
            ('서비스', 1.5), ('프로그램', 1.5), ('보조기기', 2.0)
        ]

        for keyword, weight in positive_keywords:
            if keyword in line:
                score += weight

        # 금액 패턴 존재 시 가산점 (더 구체적으로)
        if re.search(r'\d+[,\d]*\s*[만원천백십억조]', line):
            score += 3.5

        # 퍼센트 할인율
        if re.search(r'\d+\s*%', line):
            score += 2.0

        # 부정 지표 - 매우 강력하게
        negative_patterns = [
            (r'법률.*?제\d+호', -15.0),
            (r'「[^」]+」', -12.0),  # 법률명
            (r'이하\s*["\'][^"\']+["\']', -12.0),  # "이하 "약칭""
            (r'\d{3}[-\s]\d{3,4}[-\s]\d{4}', -15.0),  # 전화번호
            (r'보건복지부', -10.0),
            (r'고궁.*?능원.*?박물관', -10.0),  # 시설 나열
            (r'체의\s*수송시설', -10.0),  # 이상한 표현
            (r'^[※○●■]\s*', -5.0),
            (r'사업.*?총괄', -15.0),  # "사업 총괄 및 지원"
            (r'정서적\s*지원\s*등\s*필요한\s*서비스', -10.0),  # 너무 일반적
        ]

        for pattern, weight in negative_patterns:
            if re.search(pattern, line):
                score += weight

        # 너무 짧으면 감점
        if len(line) < 25:
            score -= 3.0

        return score

    def _score_application_line(self, line: str) -> float:
        """신청방법 정보 점수 계산"""
        score = 0.0

        # 긍정 지표
        positive_keywords = [
            ('신청방법', 3.5), ('신청절차', 3.5), ('신청서', 3.0),
            ('주민센터', 3.0), ('구청', 3.0), ('시청', 3.0), ('군청', 3.0),
            ('읍면동', 3.0), ('동사무소', 3.0), ('행정복지센터', 3.0),
            ('온라인', 2.5), ('방문', 2.5), ('우편', 2.5),
            ('제출', 2.0), ('접수', 2.5), ('신청', 1.0)
        ]

        for keyword, weight in positive_keywords:
            if keyword in line:
                score += weight

        # 전화번호 존재 시 - 문맥 확인 후 가산점
        if re.search(r'\d{2,4}[-\s]\d{3,4}[-\s]\d{4}', line):
            # "문의", "상담" 등이 있으면 연락처일 가능성
            if any(kw in line for kw in ['문의', '상담', '콜센터', '안내', '전화']):
                score += 2.5
            # "총괄", "담당" 등이 있으면 부처 연락처 (감점)
            elif any(kw in line for kw in ['총괄', '담당', '정책과']):
                score -= 10.0

        # 부정 지표 - 매우 강력하게
        negative_patterns = [
            (r'법률.*?제\d+호', -15.0),
            (r'「[^」]+」', -12.0),
            (r'보건복지부.*?\(.*?총괄', -20.0),  # 부처 총괄 연락처
            (r'^[※○●■]\s*보건복지부', -20.0),  # 부처명으로 시작
            (r'사례관리사업.*?유관기관', -10.0),  # 의미 없는 나열
            (r'읍면동행정복지센터\s*및\s*유관기관', -10.0),
        ]

        for pattern, weight in negative_patterns:
            if re.search(pattern, line):
                score += weight

        # 너무 짧으면 감점
        if len(line) < 25:
            score -= 3.0

        return score

    def _score_description_line(self, line: str, question_keywords: List[str]) -> float:
        """설명 정보 점수 계산"""
        score = 0.0

        # 질문 키워드 포함 시 가산점
        if question_keywords:
            for keyword in question_keywords:
                if keyword in line:
                    score += 2.5

        # 긍정 지표
        positive_keywords = [
            ('사업', 1.5), ('정책', 2.5), ('제도', 2.5),
            ('목적', 3.5), ('위하여', 2.5), ('위해', 2.5),
            ('지원하는', 2.5), ('제공하는', 2.5),
            ('서비스', 1.5), ('복지', 1.5), ('프로그램', 1.5),
            ('노인', 1.0), ('어르신', 1.0), ('고령자', 1.0),
            ('대상으로', 2.0), ('통하여', 2.0)
        ]

        for keyword, weight in positive_keywords:
            if keyword in line:
                score += weight

        # 설명 패턴 존재 시 가산점
        description_patterns = [
            (r'[이란은는]\s+.*?[하위].*?[는다제]', 2.5),  # "~이란 ~하는 제도"
            (r'목적.*?[하위].*?[다며]', 3.5),  # "목적으로 하는"
            (r'통해.*?지원', 2.5),  # "~를 통해 지원"
            (r'대상으로.*?지원', 3.0),  # "~대상으로 지원"
        ]

        for pattern, weight in description_patterns:
            if re.search(pattern, line):
                score += weight

        # 부정 지표 (법률 조문만 있는 경우) - 매우 강력하게
        negative_patterns = [
            (r'^「[^」]+」.*?제\d+조', -20.0),  # 법률 조문으로 시작
            (r'^「[^」]+법[^」]*」', -15.0),  # 법률명으로 시작
            (r'이하\s*["\'][^"\']+["\'].*?제\d+조', -20.0),
            (r'\d{3}[-\s]\d{3,4}[-\s]\d{4}', -15.0),  # 전화번호
            (r'^[※○●■]\s*보건복지부', -20.0),  # 부처 연락처
            (r'사업\s*총괄.*?지원', -15.0),  # "사업 총괄 및 지원"
            (r'^[가-힣\s]*사업.*?지원$', -10.0),  # 너무 간략한 설명
            (r'인권교육.*?취업제한', -15.0),  # 담당 업무 나열
            (r'치매예방.*?물리치료', -10.0),  # 프로그램 나열만
        ]

        for pattern, weight in negative_patterns:
            if re.search(pattern, line):
                score += weight

        # 적절한 길이 (50자 이상이면 가산점)
        if len(line) >= 50:
            score += 2.5
        elif len(line) >= 40:
            score += 1.5
        elif len(line) < 30:
            score -= 2.0

        return score

    def _clean_sentence(self, sentence: str) -> str:
        """문장 정리"""
        # 앞뒤 불릿 제거
        sentence = re.sub(r'^[○●■□◇◆▶▷•\-※]\s*', '', sentence)
        # 특수문자 정리
        sentence = re.sub(r'[ㆍ]', ' ', sentence)
        # 여러 공백을 하나로
        sentence = re.sub(r'\s+', ' ', sentence)
        return sentence.strip()


class EnhancedPolicyFormatter:
    """향상된 정책 정보 포맷터"""

    def __init__(self):
        self.extractor = SimplePolicyExtractor()

    def _is_policy_relevant(self, policy_name: str, question: str) -> bool:
        """정책명이 질문과 관련 있는지 확인"""
        if not question:
            return True  # 질문이 없으면 모두 허용

        # 질문에서 키워드 추출
        question_lower = question.lower()
        policy_lower = policy_name.lower()

        # 직접적인 키워드 매칭
        question_keywords = re.findall(r'[가-힣]{2,}', question)

        # 불용어 제거
        stopwords = ['누가', '어떻게', '무엇', '어디', '언제', '왜', '있나요', '있어요', '알려주세요', '뭐야', '어떤', '것들', '대해', '정책', '복지']
        question_keywords = [kw for kw in question_keywords if kw not in stopwords]

        # 질문 키워드가 정책명에 하나라도 포함되면 관련 있음
        if question_keywords:
            for keyword in question_keywords:
                if keyword in policy_name:
                    return True

        # 유사 키워드 매핑 (동의어 체크)
        synonym_map = {
            '기초연금': ['기초연금', '노령연금'],
            '의료급여': ['의료급여', '의료지원', '의료비'],
            '장기요양': ['장기요양', '요양', '돌봄'],
            '일자리': ['일자리', '취업', '근로'],
            '보훈': ['보훈', '유공자', '참전'],
            '건강': ['건강', '의료', '진료'],
        }

        # 질문에 포함된 키워드로 동의어 체크
        for main_keyword, synonyms in synonym_map.items():
            if main_keyword in question_lower:
                # 정책명에 동의어가 있는지 확인
                if any(syn in policy_lower for syn in synonyms):
                    return True
                # 정책명에 메인 키워드나 동의어가 없으면 관련 없음
                if not any(syn in policy_name for syn in synonyms):
                    return False

        # 일반적인 복지 키워드는 허용
        general_keywords = ['노인', '어르신', '복지', '지원', '서비스']
        if any(kw in question for kw in general_keywords):
            return True

        return True  # 기본적으로 허용

    def format_document(self, doc: Dict[str, Any], question: str = "") -> Optional[Dict[str, Any]]:
        """
        문서를 포맷팅하여 정책 정보로 변환

        Returns:
            {
                'formatted_text': 포맷된 텍스트,
                'has_content': 내용 유무,
                'filename': 파일명,
                'region': 지역,
                'policy_url': 정책 URL
            }
        """
        content = doc.get('content', '')
        metadata = doc.get('metadata', {})
        filename = metadata.get('filename', '정책문서.pdf')
        region = metadata.get('region', '지역미상')

        # 정책 메타데이터 찾기 (정책명, URL)
        policy_meta = find_policy_metadata(content, filename)

        # 정책 정보 추출
        policy = self.extractor.extract_from_text(content, question)

        # 정책명을 메타데이터에서 가져오기 (없으면 추출한 것 사용)
        policy_name = policy_meta.get('name') or policy.get('name') or '복지 정책'
        policy_url = policy_meta.get('url', 'https://www.bokjiro.go.kr')

        # 질문과 정책명의 관련성 체크
        if question and not self._is_policy_relevant(policy_name, question):
            logger.info(f"❌ 정책 '{policy_name}'은 질문 '{question}'과 무관하여 필터링됨")
            return None

        # 최소한 하나라도 추출되었는지 확인
        has_any_info = any([
            policy.get('description'),
            policy.get('target'),
            policy.get('benefits'),
            policy.get('application')
        ]) or policy_meta.get('name')  # 메타데이터에서 정책명을 찾았으면 OK

        if not has_any_info:
            return None

        # 중복 내용 제거 - 설명과 혜택이 같으면 하나만 표시
        description = policy.get('description', '')
        target = policy.get('target', '')
        benefits = policy.get('benefits', '')
        application = policy.get('application', '')

        # 설명과 혜택이 너무 유사하면 혜택 제거
        if description and benefits and (description == benefits or description in benefits or benefits in description):
            benefits = ''

        # 포맷팅
        lines = []

        # 정책명 (링크 제거 - 텍스트만)
        lines.append(f"**📋 {policy_name}**\n")

        # 설명
        if description:
            lines.append(f"• **설명**: {description}\n")

        # 대상
        if target:
            lines.append(f"• **대상**: {target}\n")

        # 혜택
        if benefits:
            lines.append(f"• **혜택**: {benefits}\n")

        # 신청방법
        if application:
            lines.append(f"• **신청**: {application}\n")

        # 출처 (파일명 + 링크)
        lines.append(f"• **출처**: [{filename}]({policy_url}) ({region})")

        formatted_text = ''.join(lines)

        return {
            'formatted_text': formatted_text,
            'has_content': True,
            'filename': filename,
            'region': region,
            'policy_name': policy_name,
            'policy_url': policy_url
        }
