"""
정책 정보 추출 모듈 - 간단하고 효과적인 버전

PDF 문서에서 정책명, 설명, 대상자, 신청방법 등을 추출하여 구조화
"""

import re
import logging
from typing import Dict, List, Optional, Any
from .policy_metadata import find_policy_metadata

logger = logging.getLogger(__name__)


class SimplePolicyExtractor:
    """단순하고 효과적인 정책 정보 추출기"""

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

        # 각 항목별로 관련 문장 찾기
        for i, line in enumerate(lines):
            # 너무 짧거나 메타데이터면 스킵
            if len(line) < 15 or self._is_junk(line):
                continue

            # 대상 찾기
            if not result['target'] and self._is_target_line(line):
                result['target'] = self._clean_sentence(line)[:150]

            # 혜택 찾기
            if not result['benefits'] and self._is_benefit_line(line):
                result['benefits'] = self._clean_sentence(line)[:150]

            # 신청 찾기
            if not result['application'] and self._is_application_line(line):
                result['application'] = self._clean_sentence(line)[:150]

            # 설명 찾기 (복지 키워드 + 설명 키워드)
            if not result['description'] and self._is_description_line(line, question_keywords):
                result['description'] = self._clean_sentence(line)[:200]

        return result

    def _extract_question_keywords(self, question: str) -> List[str]:
        """질문에서 핵심 키워드 추출"""
        if not question:
            return []

        # 불용어 제거
        stopwords = ['누가', '어떻게', '무엇', '어디', '언제', '왜', '있나요', '있어요', '알려주세요', '뭐야']
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
        welfare_kw = ['노인', '어르신', '대상', '혜택', '복지', '급여', '지원', '제공']
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

    def _clean_sentence(self, sentence: str) -> str:
        """문장 정리"""
        # 앞뒤 불릿 제거
        sentence = re.sub(r'^[○●■□◇◆▶▷•\-]\s*', '', sentence)
        # 특수문자 정리
        sentence = re.sub(r'[ㆍ]', ' ', sentence)
        # 여러 공백을 하나로
        sentence = re.sub(r'\s+', ' ', sentence)
        return sentence.strip()


class EnhancedPolicyFormatter:
    """향상된 정책 정보 포맷터"""

    def __init__(self):
        self.extractor = SimplePolicyExtractor()

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

        # 최소한 하나라도 추출되었는지 확인
        has_any_info = any([
            policy.get('description'),
            policy.get('target'),
            policy.get('benefits'),
            policy.get('application')
        ]) or policy_meta.get('name')  # 메타데이터에서 정책명을 찾았으면 OK

        if not has_any_info:
            return None

        # 포맷팅
        lines = []

        # 정책명 (하이퍼링크 포함)
        lines.append(f"**📋 [{policy_name}]({policy_url})**\n")

        # 설명
        if policy.get('description'):
            lines.append(f"• **설명**: {policy['description']}\n")

        # 대상
        if policy.get('target'):
            lines.append(f"• **대상**: {policy['target']}\n")

        # 혜택
        if policy.get('benefits'):
            lines.append(f"• **혜택**: {policy['benefits']}\n")

        # 신청방법
        if policy.get('application'):
            lines.append(f"• **신청**: {policy['application']}\n")

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
