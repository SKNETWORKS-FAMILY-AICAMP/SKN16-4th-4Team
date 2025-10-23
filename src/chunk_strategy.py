# =========================================
# ✂️ 청킹 전략 모듈
# =========================================

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from abc import ABC, abstractmethod
from dataclasses import dataclass
import pandas as pd

# LangChain 텍스트 스플리터
try:
    from langchain.text_splitter import (
        RecursiveCharacterTextSplitter,
        CharacterTextSplitter,
        TokenTextSplitter,
    )
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class ChunkMetadata:
    """청크 메타데이터"""
    chunk_id: str
    chunk_index: int
    chunk_size: int
    source_file: str
    chunk_strategy: str
    overlap_size: int = 0
    parent_section: str = ""
    
    
class BaseChunkStrategy(ABC):
    """청킹 전략 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        """텍스트를 청킹하는 추상 메소드"""
        pass
    
    def _create_chunk_dict(self, text: str, index: int, metadata: Dict = None) -> Dict[str, Any]:
        """청크 딕셔너리 생성 헬퍼"""
        chunk_metadata = ChunkMetadata(
            chunk_id=f"{metadata.get('file_name', 'unknown')}_{self.name}_{index}",
            chunk_index=index,
            chunk_size=len(text),
            source_file=metadata.get('file_name', ''),
            chunk_strategy=self.name,
            parent_section=metadata.get('section', '')
        )
        
        return {
            'text': text.strip(),
            'metadata': chunk_metadata.__dict__,
            'chunk_size': len(text.strip())
        }


class RecursiveChunkStrategy(BaseChunkStrategy):
    """재귀적 문자 분할 전략 (LangChain 기반)"""
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200, 
                 separators: List[str] = None):
        super().__init__("recursive_character")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        if separators is None:
            # 한국어 문서에 최적화된 구분자
            self.separators = [
                "\n\n",  # 문단 구분
                "\n",    # 줄바꿈
                "。",    # 한국어 마침표
                ".",     # 영어 마침표
                "!",     # 느낌표
                "?",     # 물음표
                "；",    # 세미콜론
                ";",
                "：",    # 콜론
                ":",
                " ",     # 공백
                ""       # 마지막 대안
            ]
        else:
            self.separators = separators
        
        if LANGCHAIN_AVAILABLE:
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                separators=self.separators,
                length_function=len
            )
        else:
            logger.warning("LangChain이 설치되지 않아 자체 구현을 사용합니다.")
            self.splitter = None
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        if metadata is None:
            metadata = {}
        
        if self.splitter:
            # LangChain 스플리터 사용
            chunks = self.splitter.split_text(text)
        else:
            # 자체 구현 사용
            chunks = self._manual_recursive_split(text)
        
        results = []
        for i, chunk_text in enumerate(chunks):
            if chunk_text.strip():  # 빈 청크 제외
                chunk_dict = self._create_chunk_dict(chunk_text, i, metadata)
                chunk_dict['metadata']['overlap_size'] = self.chunk_overlap
                results.append(chunk_dict)
        
        return results
    
    def _manual_recursive_split(self, text: str) -> List[str]:
        """수동 재귀 분할 구현"""
        chunks = []
        
        def split_by_separator(text: str, separators: List[str]) -> List[str]:
            if not separators or len(text) <= self.chunk_size:
                return [text]
            
            separator = separators[0]
            if separator in text:
                parts = text.split(separator)
                result = []
                current_chunk = ""
                
                for part in parts:
                    if len(current_chunk) + len(part) + len(separator) <= self.chunk_size:
                        current_chunk += part + separator
                    else:
                        if current_chunk:
                            result.append(current_chunk.rstrip(separator))
                        current_chunk = part + separator
                
                if current_chunk:
                    result.append(current_chunk.rstrip(separator))
                
                return result
            else:
                return split_by_separator(text, separators[1:])
        
        return split_by_separator(text, self.separators)


class ParagraphChunkStrategy(BaseChunkStrategy):
    """문단 기반 청킹 전략"""
    
    def __init__(self, min_paragraph_size: int = 50, max_paragraph_size: int = 2000):
        super().__init__("paragraph_based")
        self.min_paragraph_size = min_paragraph_size
        self.max_paragraph_size = max_paragraph_size
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        if metadata is None:
            metadata = {}
        
        # 문단 구분 (이중 줄바꿈 또는 특정 패턴)
        paragraphs = re.split(r'\n\s*\n|(?<=[.。!?])\s*\n(?=\s*[가-힣A-Z])', text)
        
        results = []
        chunk_index = 0
        
        current_chunk = ""
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
            
            # 문단이 너무 작으면 누적
            if len(paragraph) < self.min_paragraph_size:
                current_chunk += "\n\n" + paragraph if current_chunk else paragraph
            else:
                # 현재 누적된 청크가 있으면 먼저 처리
                if current_chunk:
                    chunk_dict = self._create_chunk_dict(current_chunk, chunk_index, metadata)
                    results.append(chunk_dict)
                    chunk_index += 1
                    current_chunk = ""
                
                # 문단이 너무 크면 분할
                if len(paragraph) > self.max_paragraph_size:
                    sub_chunks = self._split_large_paragraph(paragraph)
                    for sub_chunk in sub_chunks:
                        chunk_dict = self._create_chunk_dict(sub_chunk, chunk_index, metadata)
                        results.append(chunk_dict)
                        chunk_index += 1
                else:
                    chunk_dict = self._create_chunk_dict(paragraph, chunk_index, metadata)
                    results.append(chunk_dict)
                    chunk_index += 1
        
        # 마지막 누적 청크 처리
        if current_chunk:
            chunk_dict = self._create_chunk_dict(current_chunk, chunk_index, metadata)
            results.append(chunk_dict)
        
        return results
    
    def _split_large_paragraph(self, paragraph: str) -> List[str]:
        """큰 문단을 작은 단위로 분할"""
        sentences = re.split(r'(?<=[.。!?])\s+', paragraph)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.max_paragraph_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


class SentenceChunkStrategy(BaseChunkStrategy):
    """문장 기반 청킹 전략"""
    
    def __init__(self, sentences_per_chunk: int = 3, min_chunk_size: int = 100):
        super().__init__("sentence_based")
        self.sentences_per_chunk = sentences_per_chunk
        self.min_chunk_size = min_chunk_size
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        if metadata is None:
            metadata = {}
        
        # 문장 분할 (한국어와 영어 모두 고려)
        sentences = self._split_sentences(text)
        
        results = []
        chunk_index = 0
        
        for i in range(0, len(sentences), self.sentences_per_chunk):
            chunk_sentences = sentences[i:i + self.sentences_per_chunk]
            chunk_text = " ".join(chunk_sentences).strip()
            
            # 최소 크기 확인
            if len(chunk_text) >= self.min_chunk_size:
                chunk_dict = self._create_chunk_dict(chunk_text, chunk_index, metadata)
                results.append(chunk_dict)
                chunk_index += 1
        
        return results
    
    def _split_sentences(self, text: str) -> List[str]:
        """한국어/영어 문장 분할"""
        # 한국어와 영어 문장 종결 패턴
        sentence_endings = r'[.。!?！？]\s*'
        sentences = re.split(sentence_endings, text)
        
        # 빈 문장 제거 및 정리
        sentences = [s.strip() for s in sentences if s.strip()]
        return sentences


class SemanticChunkStrategy(BaseChunkStrategy):
    """의미 기반 청킹 전략 (정책 문서 특화)"""
    
    def __init__(self, chunk_size: int = 800, policy_keywords: List[str] = None):
        super().__init__("semantic_policy")
        self.chunk_size = chunk_size
        
        if policy_keywords is None:
            # 노인복지 정책 키워드
            self.policy_keywords = [
                "지원", "혜택", "대상", "자격", "조건", "신청", "방법",
                "기준", "범위", "한도", "기간", "절차", "서류", "제출",
                "노인", "어르신", "고령자", "복지", "보조금", "수당",
                "의료비", "간병", "요양", "돌봄", "생활지원"
            ]
        else:
            self.policy_keywords = policy_keywords
    
    def chunk_text(self, text: str, metadata: Dict = None) -> List[Dict[str, Any]]:
        if metadata is None:
            metadata = {}
        
        # 정책 섹션 탐지 및 분할
        sections = self._detect_policy_sections(text)
        
        results = []
        chunk_index = 0
        
        for section_title, section_text in sections:
            # 섹션이 너무 크면 추가 분할
            if len(section_text) > self.chunk_size * 1.5:
                sub_chunks = self._split_semantic_section(section_text)
                for sub_chunk in sub_chunks:
                    chunk_dict = self._create_chunk_dict(sub_chunk, chunk_index, metadata)
                    chunk_dict['metadata']['parent_section'] = section_title
                    results.append(chunk_dict)
                    chunk_index += 1
            else:
                chunk_dict = self._create_chunk_dict(section_text, chunk_index, metadata)
                chunk_dict['metadata']['parent_section'] = section_title
                results.append(chunk_dict)
                chunk_index += 1
        
        return results
    
    def _detect_policy_sections(self, text: str) -> List[Tuple[str, str]]:
        """정책 문서의 의미적 섹션 탐지"""
        sections = []
        
        # 섹션 제목 패턴 (숫자, 한글, 특수문자 조합)
        section_patterns = [
            r'^[0-9]+\.\s*[가-힣\s]+',  # "1. 지원대상"
            r'^[가-힣]+\s*[:：]\s*',      # "지원내용:"
            r'^※\s*[가-힣\s]+',         # "※ 신청방법"
            r'^[▶▷■□○●]\s*[가-힣\s]+', # "▶ 지원범위"
            r'^[가나다라마바사아자차카타파하]\.\s*[가-힣\s]+' # "가. 대상자"
        ]
        
        lines = text.split('\n')
        current_section = "기타"
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # 섹션 제목인지 확인
            is_section_title = False
            for pattern in section_patterns:
                if re.match(pattern, line):
                    # 이전 섹션 저장
                    if current_content:
                        sections.append((current_section, '\n'.join(current_content)))
                    
                    # 새 섹션 시작
                    current_section = line
                    current_content = []
                    is_section_title = True
                    break
            
            if not is_section_title:
                current_content.append(line)
        
        # 마지막 섹션 저장
        if current_content:
            sections.append((current_section, '\n'.join(current_content)))
        
        return sections
    
    def _split_semantic_section(self, text: str) -> List[str]:
        """의미적 섹션을 적절한 크기로 분할"""
        # 키워드 기반으로 분할점 찾기
        sentences = re.split(r'(?<=[.。!?])\s+', text)
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            # 키워드가 포함된 문장에서 우선적으로 분할
            has_keyword = any(keyword in sentence for keyword in self.policy_keywords)
            
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks


class ChunkStrategyComparator:
    """청킹 전략 비교 및 평가 클래스"""
    
    def __init__(self):
        self.strategies = {
            'recursive': RecursiveChunkStrategy(),
            'paragraph': ParagraphChunkStrategy(),
            'sentence': SentenceChunkStrategy(),
            'semantic': SemanticChunkStrategy()
        }
    
    def compare_strategies(self, text: str, metadata: Dict = None) -> Dict[str, Any]:
        """모든 전략으로 청킹하고 결과 비교"""
        if metadata is None:
            metadata = {'file_name': 'sample_text'}
        
        results = {}
        
        for strategy_name, strategy in self.strategies.items():
            try:
                chunks = strategy.chunk_text(text, metadata)
                
                # 통계 계산
                chunk_sizes = [chunk['chunk_size'] for chunk in chunks]
                
                stats = {
                    'total_chunks': len(chunks),
                    'avg_chunk_size': sum(chunk_sizes) / len(chunk_sizes) if chunk_sizes else 0,
                    'min_chunk_size': min(chunk_sizes) if chunk_sizes else 0,
                    'max_chunk_size': max(chunk_sizes) if chunk_sizes else 0,
                    'total_characters': sum(chunk_sizes),
                    'coverage_ratio': sum(chunk_sizes) / len(text) if text else 0,
                    'chunks': chunks[:3]  # 처음 3개 청크만 저장
                }
                
                results[strategy_name] = stats
                
            except Exception as e:
                logger.error(f"전략 {strategy_name} 실행 중 오류: {e}")
                results[strategy_name] = {'error': str(e)}
        
        return results
    
    def evaluate_chunking_quality(self, text: str, metadata: Dict = None) -> pd.DataFrame:
        """청킹 품질 평가 및 추천"""
        comparison = self.compare_strategies(text, metadata)
        
        evaluation_data = []
        
        for strategy_name, stats in comparison.items():
            if 'error' in stats:
                continue
            
            # 품질 점수 계산
            quality_scores = self._calculate_quality_scores(stats, len(text))
            
            row = {
                'strategy': strategy_name,
                'total_chunks': stats['total_chunks'],
                'avg_chunk_size': round(stats['avg_chunk_size'], 1),
                'size_consistency': quality_scores['size_consistency'],
                'coverage_ratio': round(stats['coverage_ratio'], 3),
                'overall_score': quality_scores['overall_score']
            }
            
            evaluation_data.append(row)
        
        df = pd.DataFrame(evaluation_data)
        
        if not df.empty:
            # 점수순 정렬
            df = df.sort_values('overall_score', ascending=False)
        
        return df
    
    def _calculate_quality_scores(self, stats: Dict, original_length: int) -> Dict[str, float]:
        """청킹 품질 점수 계산"""
        # 크기 일관성 (표준편차가 작을수록 좋음)
        avg_size = stats['avg_chunk_size']
        min_size = stats['min_chunk_size']
        max_size = stats['max_chunk_size']
        
        if avg_size > 0:
            size_variance = ((max_size - avg_size) ** 2 + (min_size - avg_size) ** 2) / 2
            size_consistency = 1 / (1 + size_variance / (avg_size ** 2))
        else:
            size_consistency = 0
        
        # 적절한 청크 수 (너무 많거나 적으면 감점)
        optimal_chunks = original_length / 800  # 800자당 1청크가 적절
        chunk_count_score = 1 / (1 + abs(stats['total_chunks'] - optimal_chunks) / optimal_chunks)
        
        # 커버리지 점수
        coverage_score = min(stats['coverage_ratio'], 1.0)
        
        # 전체 점수 (가중평균)
        overall_score = (
            size_consistency * 0.3 +
            chunk_count_score * 0.3 +
            coverage_score * 0.4
        )
        
        return {
            'size_consistency': round(size_consistency, 3),
            'chunk_count_score': round(chunk_count_score, 3),
            'coverage_score': round(coverage_score, 3),
            'overall_score': round(overall_score, 3)
        }
    
    def get_strategy_recommendation(self, text: str, metadata: Dict = None) -> Dict[str, Any]:
        """텍스트에 최적화된 청킹 전략 추천"""
        evaluation_df = self.evaluate_chunking_quality(text, metadata)
        
        if evaluation_df.empty:
            return {
                'recommended_strategy': 'recursive',
                'reason': '기본 전략',
                'evaluation': None
            }
        
        best_strategy = evaluation_df.iloc[0]
        
        # 추천 이유 생성
        reasons = []
        if best_strategy['overall_score'] > 0.8:
            reasons.append("높은 전체 품질 점수")
        if best_strategy['size_consistency'] > 0.8:
            reasons.append("일관된 청크 크기")
        if best_strategy['coverage_ratio'] > 0.95:
            reasons.append("높은 텍스트 커버리지")
        
        return {
            'recommended_strategy': best_strategy['strategy'],
            'score': best_strategy['overall_score'],
            'reason': ', '.join(reasons) if reasons else '최적 성능',
            'evaluation': evaluation_df
        }


def main():
    """청킹 전략 테스트 및 비교"""
    
    # 테스트 텍스트 (노인복지 정책 예시)
    sample_text = """
    노인복지법에 따른 생활지원 서비스 안내
    
    1. 지원대상
    만 65세 이상 노인 중 기초생활수급자 및 차상위 계층에 해당하는 분들을 대상으로 합니다.
    
    2. 지원내용
    가. 생활비 지원: 월 최대 30만원까지 지원
    나. 의료비 지원: 연간 200만원 한도 내에서 본인부담금 지원
    다. 돌봄서비스: 주 3회, 회당 4시간 돌봄서비스 제공
    
    3. 신청방법
    거주지 관할 주민센터 또는 복지관에 신청서류를 제출하시면 됩니다.
    
    ▶ 필요서류
    - 신청서 (주민센터 비치)
    - 소득증명서
    - 건강보험료 납부확인서
    - 가족관계증명서
    
    ※ 신청 후 7일 이내에 결과 통보
    심사 기간 중 추가 서류 요청이 있을 수 있습니다.
    """
    
    print("🔍 청킹 전략 비교 테스트")
    print("=" * 50)
    
    comparator = ChunkStrategyComparator()
    
    # 전략별 비교
    results = comparator.compare_strategies(sample_text)
    
    print("\n📊 전략별 청킹 결과:")
    for strategy, stats in results.items():
        if 'error' not in stats:
            print(f"\n[{strategy.upper()}]")
            print(f"  총 청크 수: {stats['total_chunks']}")
            print(f"  평균 청크 크기: {stats['avg_chunk_size']:.1f}자")
            print(f"  크기 범위: {stats['min_chunk_size']}-{stats['max_chunk_size']}자")
            print(f"  커버리지: {stats['coverage_ratio']:.1%}")
            
            # 첫 번째 청크 미리보기
            if stats['chunks']:
                preview = stats['chunks'][0]['text'][:100] + "..."
                print(f"  첫 청크 미리보기: {preview}")
    
    # 품질 평가
    evaluation_df = comparator.evaluate_chunking_quality(sample_text)
    
    print(f"\n🏆 청킹 품질 평가:")
    print(evaluation_df.to_string(index=False))
    
    # 최적 전략 추천
    recommendation = comparator.get_strategy_recommendation(sample_text)
    
    print(f"\n✅ 추천 전략: {recommendation['recommended_strategy'].upper()}")
    print(f"   점수: {recommendation['score']}")
    print(f"   이유: {recommendation['reason']}")


class ChunkStrategyManager:
    """청킹 전략 관리 클래스 (통합 비교평가용)"""
    
    def __init__(self):
        """청킹 전략 관리자 초기화"""
        self.comparator = ChunkStrategyComparator()
        logger.info("청킹 전략 관리자 초기화 완료")
    
    def chunk_text(self, text: str, strategy: str = "recursive") -> List[str]:
        """
        지정된 전략으로 텍스트 청킹
        
        Args:
            text: 청킹할 텍스트
            strategy: 청킹 전략 ('recursive', 'semantic', 'fixed_size', 'sentence')
            
        Returns:
            List[str]: 청킹된 텍스트 조각들
        """
        try:
            # 전략 매핑
            strategy_mapping = {
                'recursive': 'recursive',
                'semantic': 'semantic', 
                'fixed_size': 'fixed_size',
                'sentence': 'sentence'
            }
            
            actual_strategy = strategy_mapping.get(strategy, 'recursive')
            
            # 청킹 실행
            results = self.comparator.compare_strategies(text)
            
            if actual_strategy in results and 'chunks' in results[actual_strategy]:
                chunks = results[actual_strategy]['chunks']
                return [chunk['text'] for chunk in chunks]
            else:
                # 기본 청킹 (문장 단위)
                sentences = re.split(r'[.!?]+\s*', text)
                return [s.strip() for s in sentences if s.strip()]
                
        except Exception as e:
            logger.error(f"청킹 실행 실패 ({strategy}): {e}")
            # 기본 청킹
            return [text[i:i+500] for i in range(0, len(text), 500)]
    
    def get_available_strategies(self) -> List[str]:
        """사용 가능한 청킹 전략 목록 반환"""
        return ['recursive', 'semantic', 'fixed_size', 'sentence']
    
    def evaluate_strategy_performance(self, text: str, strategy: str) -> Dict[str, Any]:
        """
        특정 전략의 성능 평가
        
        Args:
            text: 평가할 텍스트
            strategy: 청킹 전략
            
        Returns:
            Dict[str, Any]: 성능 평가 결과
        """
        try:
            results = self.comparator.compare_strategies(text)
            
            if strategy in results and 'error' not in results[strategy]:
                stats = results[strategy]
                
                return {
                    'strategy': strategy,
                    'chunk_count': stats['total_chunks'],
                    'avg_chunk_size': stats['avg_chunk_size'],
                    'coverage_ratio': stats['coverage_ratio'],
                    'processing_time': stats.get('processing_time', 0),
                    'success': True
                }
            else:
                return {
                    'strategy': strategy,
                    'chunk_count': 0,
                    'avg_chunk_size': 0,
                    'coverage_ratio': 0,
                    'processing_time': 0,
                    'success': False,
                    'error': results.get(strategy, {}).get('error', 'Unknown error')
                }
                
        except Exception as e:
            return {
                'strategy': strategy,
                'chunk_count': 0,
                'avg_chunk_size': 0,
                'coverage_ratio': 0,
                'processing_time': 0,
                'success': False,
                'error': str(e)
            }


if __name__ == "__main__":
    main()