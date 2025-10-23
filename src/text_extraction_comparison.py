# =========================================
# 📄 텍스트 추출 방법 비교 시스템
# =========================================

import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from abc import ABC, abstractmethod
import hashlib
import re

# PDF 추출 라이브러리들
try:
    import PyPDF2
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfminer
    from pdfminer.high_level import extract_text as pdfminer_extract_text
    PDFMINER_AVAILABLE = True
except ImportError:
    PDFMINER_AVAILABLE = False

# HWP 추출 라이브러리들
try:
    import olefile
    OLEFILE_AVAILABLE = True
except ImportError:
    OLEFILE_AVAILABLE = False

try:
    import hwp5
    HWP5_AVAILABLE = True
except ImportError:
    HWP5_AVAILABLE = False

try:
    import pyhwp
    PYHWP_AVAILABLE = True
except ImportError:
    PYHWP_AVAILABLE = False

# 평가 라이브러리
import re
from collections import Counter
import pandas as pd

logger = logging.getLogger(__name__)


def clean_text(text: str, remove_unicode: bool = True, markdown_format: bool = False) -> str:
    """
    텍스트 정리 함수
    
    Args:
        text: 정리할 텍스트
        remove_unicode: 유니코드 특수문자 제거 여부
        markdown_format: 마크다운 형식 적용 여부
    
    Returns:
        정리된 텍스트
    """
    if not text:
        return ""
    
    cleaned = text
    
    # 유니코드 특수문자 제거
    if remove_unicode:
        # 한글, 영문, 숫자, 기본 문장부호만 유지
        cleaned = re.sub(r'[^\x20-\x7E가-힣ㄱ-ㅎㅏ-ㅣ\s\n\r\t]', '', cleaned)
        # 제어 문자 제거 (탭, 개행, 캐리지 리턴 제외)
        cleaned = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', cleaned)
    
    # 마크다운 형식 적용
    if markdown_format:
        lines = cleaned.split('\n')
        markdown_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                markdown_lines.append('')
                continue
            
            # 제목 감지 및 변환 (단독 줄에 있는 짧은 텍스트)
            if len(line) < 100 and not line.endswith(('.', '?', '!')):
                if any(keyword in line for keyword in ['조례', '규칙', '지침', '계획', '사업', '안내']):
                    markdown_lines.append(f'# {line}')
                elif any(keyword in line for keyword in ['제', '조', '항', '호']):
                    markdown_lines.append(f'## {line}')
                else:
                    markdown_lines.append(line)
            # 목록 항목 감지 및 변환
            elif re.match(r'^\s*[-•◦▪▫]\s*', line):
                item_text = re.sub(r'^\s*[-•◦▪▫]\s*', '', line)
                markdown_lines.append(f'- {item_text}')
            # 번호 목록 감지 및 변환
            elif re.match(r'^\s*\d+\.\s*', line):
                markdown_lines.append(line)
            # 일반 문단
            else:
                markdown_lines.append(line)
        
        cleaned = '\n'.join(markdown_lines)
    
    # 공백 및 줄바꿈 정리
    cleaned = re.sub(r'[ \t]+', ' ', cleaned)  # 공백과 탭을 단일 공백으로
    cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)  # 3개 이상 연속 줄바꿈을 2개로
    cleaned = re.sub(r'^\s+|\s+$', '', cleaned, flags=re.MULTILINE)  # 각 줄의 앞뒤 공백 제거
    
    return cleaned.strip()


class BaseTextExtractor(ABC):
    """텍스트 추출기 기본 클래스"""
    
    def __init__(self, name: str):
        self.name = name
        self.performance_metrics = {}
    
    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """텍스트 추출 추상 메서드"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """라이브러리 사용 가능 여부"""
        pass
    
    def extract_with_metrics(self, file_path: str, clean_unicode: bool = True, 
                           markdown_format: bool = False) -> Dict[str, Any]:
        """성능 메트릭과 함께 텍스트 추출"""
        
        start_time = time.time()
        
        try:
            raw_text = self.extract_text(file_path)
            # 텍스트 정리 적용
            text = clean_text(raw_text, remove_unicode=clean_unicode, 
                            markdown_format=markdown_format)
            success = True
            error = None
        except Exception as e:
            text = ""
            raw_text = ""
            success = False
            error = str(e)
        
        end_time = time.time()
        
        # 텍스트 예시 추출 (다양한 부분에서)
        text_examples = self._extract_text_samples(text) if text else {}
        
        # 성능 메트릭 계산
        metrics = {
            "extractor_name": self.name,
            "file_path": file_path,
            "success": success,
            "error": error,
            "extraction_time": end_time - start_time,
            "text_length": len(text) if text else 0,
            "line_count": text.count('\n') if text else 0,
            "word_count": len(text.split()) if text else 0,
            "text_preview": text[:200] + "..." if len(text) > 200 else text,
            "text_examples": text_examples,
            "text_hash": hashlib.md5(text.encode()).hexdigest() if text else None,
            "raw_text_length": len(raw_text) if raw_text else 0,
            "cleaning_applied": {"unicode": clean_unicode, "markdown": markdown_format}
        }
        
        return {
            "text": text,
            "metrics": metrics
        }
    
    def _extract_text_samples(self, text: str) -> Dict[str, str]:
        """텍스트에서 다양한 샘플 추출"""
        if not text or len(text) < 100:
            return {"short": text}
        
        samples = {}
        text_len = len(text)
        
        # 시작 부분
        samples["beginning"] = text[:150] + "..." if len(text) > 150 else text
        
        # 중간 부분
        if text_len > 300:
            mid_start = text_len // 2 - 75
            mid_end = text_len // 2 + 75
            samples["middle"] = "..." + text[mid_start:mid_end] + "..."
        
        # 끝 부분
        if text_len > 150:
            samples["ending"] = "..." + text[-150:]
        
        return samples


# =========================================
# PDF 텍스트 추출기들
# =========================================

class PyPDF2Extractor(BaseTextExtractor):
    """PyPDF2 기반 PDF 텍스트 추출기"""
    
    def __init__(self):
        super().__init__("PyPDF2")
    
    def is_available(self) -> bool:
        return PYPDF2_AVAILABLE
    
    def extract_text(self, file_path: str) -> str:
        if not self.is_available():
            raise ImportError("PyPDF2가 설치되지 않았습니다")
        
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                # 페이지 수 확인
                if hasattr(pdf_reader, 'pages') and pdf_reader.pages:
                    for page in pdf_reader.pages:
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                        except Exception as e:
                            logger.warning(f"PyPDF2 페이지 추출 실패: {e}")
                            continue
                else:
                    logger.warning("PyPDF2: 페이지를 찾을 수 없습니다")
                    
        except Exception as e:
            logger.error(f"PyPDF2 파일 읽기 실패: {e}")
            raise
        
        return text.strip()


class PDFPlumberExtractor(BaseTextExtractor):
    """pdfplumber 기반 PDF 텍스트 추출기"""
    
    def __init__(self):
        super().__init__("pdfplumber")
    
    def is_available(self) -> bool:
        return PDFPLUMBER_AVAILABLE
    
    def extract_text(self, file_path: str) -> str:
        if not self.is_available():
            raise ImportError("pdfplumber가 설치되지 않았습니다")
        
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                # 페이지 리스트 확인
                if hasattr(pdf, 'pages') and pdf.pages:
                    for page in pdf.pages:
                        try:
                            page_text = page.extract_text()
                            if page_text:
                                text += page_text + "\n"
                        except Exception as e:
                            logger.warning(f"PDFPlumber 페이지 추출 실패: {e}")
                            continue
                else:
                    logger.warning("PDFPlumber: 페이지를 찾을 수 없습니다")
                    
        except Exception as e:
            logger.error(f"PDFPlumber 파일 읽기 실패: {e}")
            raise
        
        return text.strip()


class PyMuPDFExtractor(BaseTextExtractor):
    """PyMuPDF 기반 PDF 텍스트 추출기"""
    
    def __init__(self):
        super().__init__("PyMuPDF")
    
    def is_available(self) -> bool:
        return PYMUPDF_AVAILABLE
    
    def extract_text(self, file_path: str) -> str:
        if not self.is_available():
            raise ImportError("PyMuPDF가 설치되지 않았습니다")
        
        text = ""
        doc = None
        try:
            doc = fitz.open(file_path)
            
            # 페이지 수 확인
            page_count = getattr(doc, 'page_count', 0)
            if not isinstance(page_count, int) or page_count <= 0:
                logger.warning(f"PyMuPDF: 유효하지 않은 페이지 수 - {page_count}")
                return ""
            
            for page_num in range(page_count):
                try:
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as e:
                    logger.warning(f"PyMuPDF 페이지 {page_num} 추출 실패: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"PyMuPDF 파일 읽기 실패: {e}")
            raise
        finally:
            if doc:
                doc.close()
        
        return text.strip()


class PDFMinerExtractor(BaseTextExtractor):
    """pdfminer 기반 PDF 텍스트 추출기"""
    
    def __init__(self):
        super().__init__("pdfminer")
    
    def is_available(self) -> bool:
        return PDFMINER_AVAILABLE
    
    def extract_text(self, file_path: str) -> str:
        if not self.is_available():
            raise ImportError("pdfminer가 설치되지 않았습니다")
        
        return pdfminer_extract_text(file_path)


# =========================================
# HWP 텍스트 추출기들
# =========================================

class OleFileHWPExtractor(BaseTextExtractor):
    """olefile 기반 HWP 텍스트 추출기"""
    
    def __init__(self):
        super().__init__("olefile")
    
    def is_available(self) -> bool:
        return OLEFILE_AVAILABLE
    
    def extract_text(self, file_path: str) -> str:
        if not self.is_available():
            raise ImportError("olefile이 설치되지 않았습니다")
        
        try:
            with olefile.OleFileIO(file_path) as ole:
                # HWP 파일 구조 분석
                streams = ole.listdir()
                text_content = ""
                
                logger.info(f"HWP 파일 스트림 수: {len(streams)}개")
                
                # HWP 5.0 이상의 경우 BodyText 스트림 우선 검색
                priority_streams = []
                other_streams = []
                
                for stream_path in streams:
                    stream_name = '/'.join(str(s) for s in stream_path).lower()
                    
                    # 우선순위 스트림 (BodyText 관련)
                    if any(keyword in stream_name for keyword in [
                        'bodytext', 'section', 'paragraph', 'contents'
                    ]):
                        priority_streams.append(stream_path)
                    else:
                        other_streams.append(stream_path)
                
                # 우선순위 스트림부터 처리
                all_streams_to_try = priority_streams + other_streams
                
                for stream_path in all_streams_to_try:
                    try:
                        stream_data = ole.get_stream(stream_path).read()
                        
                        # 스트림 크기 확인
                        if len(stream_data) < 50:
                            continue
                        
                        # HWP 파일의 텍스트 데이터 패턴 검색
                        extracted_text = self._extract_hwp_text_from_stream(stream_data)
                        
                        if extracted_text:
                            text_content += extracted_text + " "
                            
                    except Exception as e:
                        logger.debug(f"스트림 {stream_path} 처리 실패: {e}")
                        continue
                
                result = text_content.strip()
                if result:
                    logger.info(f"HWP 텍스트 추출 성공: {len(result)}자")
                else:
                    logger.warning("HWP에서 텍스트를 찾을 수 없습니다")
                    # 원시 바이너리 분석 시도
                    result = self._extract_text_from_binary(file_path)
                
                return result
        
        except Exception as e:
            logger.error(f"olefile을 사용한 HWP 추출 실패: {e}")
            return ""
    
    def _extract_hwp_text_from_stream(self, stream_data: bytes) -> str:
        """스트림 데이터에서 텍스트 추출 (개선된 버전)"""
        extracted_texts = []
        
        # HWP 특화 텍스트 패턴 검색
        try:
            # CP949로 우선 시도 (HWP 기본 인코딩)
            text = stream_data.decode('cp949', errors='replace')
            
            # 정상적인 한글 문장 패턴만 추출
            # 최소 3글자 이상의 한글 단어로 구성된 문장
            korean_sentences = re.findall(r'[가-힣]{2,}(?:\s+[가-힣]{2,})*(?:[.\s]|$)', text)
            
            if korean_sentences:
                # 의미있는 문장만 필터링
                valid_sentences = []
                for sentence in korean_sentences:
                    sentence = sentence.strip()
                    # 최소 길이와 한글 비율 체크
                    if len(sentence) >= 5:
                        hangul_count = len(re.findall(r'[가-힣]', sentence))
                        if hangul_count >= len(sentence) * 0.7:  # 한글이 70% 이상
                            valid_sentences.append(sentence)
                
                if valid_sentences:
                    result = ' '.join(valid_sentences[:100])  # 최대 100개 문장
                    # 연속 공백 정리
                    result = re.sub(r'\s+', ' ', result)
                    return result[:3000]  # 최대 3000자
        
        except Exception:
            pass
        
        # 대체 방법: UTF-8로 시도
        try:
            text = stream_data.decode('utf-8', errors='ignore')
            korean_words = re.findall(r'[가-힣]{2,}', text)
            if korean_words and len(korean_words) >= 5:
                result = ' '.join(korean_words[:200])
                return result[:2000]
        except Exception:
            pass
        
        return ""
    
    def _extract_text_from_binary(self, file_path: str) -> str:
        """바이너리 파일에서 직접 텍스트 패턴 추출 (개선된 버전)"""
        try:
            with open(file_path, 'rb') as f:
                # 전체 파일 읽기 (너무 크면 일부만)
                file_data = f.read(1024 * 1024)  # 최대 1MB
                
                extracted_sentences = []
                
                # CP949 디코딩으로 텍스트 추출
                try:
                    text = file_data.decode('cp949', errors='replace')
                    
                    # 완전한 한글 문장 패턴 찾기
                    sentence_patterns = [
                        r'[가-힣]{2,}(?:\s+[가-힣]{1,}){2,}',  # 한글 단어 3개 이상
                        r'[가-힣]+(?:\s+[가-힣]+)*\s*[.:!?]',   # 문장 부호로 끝나는 문장
                        r'제\d+[조항목]\s+[가-힣]{3,}',         # 법규 조항
                        r'[가-힣]{3,}\s+[가-힣]{3,}\s+[가-힣]{3,}',  # 연속된 단어
                    ]
                    
                    for pattern in sentence_patterns:
                        matches = re.findall(pattern, text)
                        for match in matches:
                            # 품질 체크
                            if len(match) >= 6 and len(match) <= 100:
                                hangul_ratio = len(re.findall(r'[가-힣]', match)) / len(match)
                                if hangul_ratio >= 0.6:  # 한글 60% 이상
                                    extracted_sentences.append(match.strip())
                    
                    if extracted_sentences:
                        # 중복 제거하고 품질순 정렬
                        unique_sentences = list(set(extracted_sentences))
                        unique_sentences.sort(key=len, reverse=True)
                        
                        result = ' '.join(unique_sentences[:30])  # 최대 30개 문장
                        result = re.sub(r'\s+', ' ', result)  # 공백 정리
                        
                        logger.info(f"바이너리 추출 성공: {len(result)}자")
                        return result[:2000]  # 최대 2000자
                
                except Exception as e:
                    logger.debug(f"CP949 디코딩 실패: {e}")
                
                # 대체 방법: EUC-KR 시도
                try:
                    text = file_data.decode('euc-kr', errors='replace')
                    korean_words = re.findall(r'[가-힣]{3,}', text)
                    if korean_words:
                        result = ' '.join(korean_words[:100])
                        logger.info(f"EUC-KR 추출 성공: {len(result)}자")
                        return result[:1500]
                except Exception:
                    pass
                
        except Exception as e:
            logger.debug(f"바이너리 추출 실패: {e}")
        
        return ""


class HWP5Extractor(BaseTextExtractor):
    """hwp5 라이브러리 기반 HWP 텍스트 추출기"""
    
    def __init__(self):
        super().__init__("hwp5")
    
    def is_available(self) -> bool:
        return HWP5_AVAILABLE
    
    def extract_text(self, file_path: str) -> str:
        if not self.is_available():
            raise ImportError("hwp5가 설치되지 않았습니다")
        
        try:
            from hwp5.binmodel import Document
            from hwp5.xmlmodel import Text
            
            doc = Document(file_path)
            text_content = []
            
            # 문서의 모든 텍스트 추출
            for section in doc.bodytext.sections:
                for paragraph in section.paragraphs:
                    for text_run in paragraph.text_runs:
                        if hasattr(text_run, 'text'):
                            text_content.append(text_run.text)
            
            return '\n'.join(text_content)
        
        except Exception as e:
            logger.warning(f"hwp5를 사용한 HWP 추출 실패: {e}")
            return ""


class PyHWPExtractor(BaseTextExtractor):
    """pyhwp 라이브러리 기반 HWP 텍스트 추출기"""
    
    def __init__(self):
        super().__init__("pyhwp")
    
    def is_available(self) -> bool:
        return PYHWP_AVAILABLE
    
    def extract_text(self, file_path: str) -> str:
        if not self.is_available():
            raise ImportError("pyhwp가 설치되지 않았습니다")
        
        try:
            # pyhwp를 사용한 텍스트 추출 (라이브러리 구조에 따라 조정 필요)
            import pyhwp
            
            # 임시 구현 - 실제 라이브러리 API에 맞게 수정 필요
            text = pyhwp.extract_text(file_path)
            return text if text else ""
        
        except Exception as e:
            logger.warning(f"pyhwp를 사용한 HWP 추출 실패: {e}")
            return ""


# =========================================
# 텍스트 추출 비교 시스템
# =========================================

class TextExtractionComparison:
    """텍스트 추출 방법 비교 시스템"""
    
    def __init__(self):
        """텍스트 추출 비교 시스템 초기화"""
        
        # PDF 추출기들
        self.pdf_extractors = [
            PyPDF2Extractor(),
            PDFPlumberExtractor(),
            PyMuPDFExtractor(),
            PDFMinerExtractor()
        ]
        
        # HWP 추출기들
        self.hwp_extractors = [
            OleFileHWPExtractor(),
            HWP5Extractor(),
            PyHWPExtractor()
        ]
        
        # 사용 가능한 추출기만 필터링
        self.available_pdf_extractors = [e for e in self.pdf_extractors if e.is_available()]
        self.available_hwp_extractors = [e for e in self.hwp_extractors if e.is_available()]
        
        logger.info(f"사용 가능한 PDF 추출기: {[e.name for e in self.available_pdf_extractors]}")
        logger.info(f"사용 가능한 HWP 추출기: {[e.name for e in self.available_hwp_extractors]}")
    
    def compare_pdf_extractors(self, pdf_files: List[str]) -> Dict[str, Any]:
        """PDF 추출기들 성능 비교"""
        
        if not self.available_pdf_extractors:
            logger.warning("사용 가능한 PDF 추출기가 없습니다")
            return {"error": "사용 가능한 PDF 추출기가 없습니다"}
        
        results = []
        
        for pdf_file in pdf_files:
            if not os.path.exists(pdf_file):
                logger.warning(f"PDF 파일이 존재하지 않습니다: {pdf_file}")
                continue
            
            logger.info(f"PDF 파일 처리 중: {pdf_file}")
            
            for extractor in self.available_pdf_extractors:
                result = extractor.extract_with_metrics(pdf_file)
                # metrics 부분만 추출하고 추가 정보 추가
                if "metrics" in result:
                    metric_result = result["metrics"].copy()
                    metric_result["file_name"] = os.path.basename(pdf_file)
                    metric_result["extractor"] = extractor.name
                    results.append(metric_result)
                else:
                    # 이전 형식과의 호환성
                    result["file_name"] = os.path.basename(pdf_file)
                    result["extractor"] = extractor.name
                    results.append(result)
        
        return self._analyze_extraction_results(results, "PDF")
    
    def compare_hwp_extractors(self, hwp_files: List[str]) -> Dict[str, Any]:
        """HWP 추출기들 성능 비교"""
        
        if not self.available_hwp_extractors:
            logger.warning("사용 가능한 HWP 추출기가 없습니다")
            return {"error": "사용 가능한 HWP 추출기가 없습니다"}
        
        results = []
        
        for hwp_file in hwp_files:
            if not os.path.exists(hwp_file):
                logger.warning(f"HWP 파일이 존재하지 않습니다: {hwp_file}")
                continue
            
            logger.info(f"HWP 파일 처리 중: {hwp_file}")
            
            for extractor in self.available_hwp_extractors:
                result = extractor.extract_with_metrics(hwp_file)
                # metrics 부분만 추출하고 추가 정보 추가
                if "metrics" in result:
                    metric_result = result["metrics"].copy()
                    metric_result["file_name"] = os.path.basename(hwp_file)
                    metric_result["extractor"] = extractor.name
                    results.append(metric_result)
                else:
                    # 이전 형식과의 호환성
                    result["file_name"] = os.path.basename(hwp_file)
                    result["extractor"] = extractor.name
                    results.append(result)
        
        return self._analyze_extraction_results(results, "HWP")
    
    def simple_compare(self, file_path: str = None) -> Dict[str, Any]:
        """간단한 비교 메서드 - 메트릭 오류 방지"""
        if file_path and os.path.exists(file_path):
            file_ext = Path(file_path).suffix.lower()
            if file_ext == '.pdf':
                extractors = self.available_pdf_extractors
            elif file_ext == '.hwp':
                extractors = self.available_hwp_extractors
            else:
                return {"error": "지원하지 않는 파일 형식입니다"}
        else:
            # 기본 추출기 정보 반환
            return {
                "extractors": {
                    "pdf": [e.name for e in self.available_pdf_extractors],
                    "hwp": [e.name for e in self.available_hwp_extractors]
                },
                "total_extractors": len(self.available_pdf_extractors) + len(self.available_hwp_extractors)
            }
        
        # 실제 파일 처리
        detailed_results = []
        
        for extractor in extractors:
            try:
                result = extractor.extract_with_metrics(file_path)
                
                # 메트릭 구조 정리
                if "metrics" in result:
                    metrics = result["metrics"]
                    detailed_result = {
                        "extractor": extractor.name,
                        "success": metrics.get("success", False),
                        "extraction_time": metrics.get("extraction_time", 0),
                        "text_length": metrics.get("text_length", 0),
                        "text_preview": metrics.get("text_preview", ""),
                        "error": metrics.get("error") if not metrics.get("success", False) else None
                    }
                else:
                    # 호환성을 위한 기본 처리
                    detailed_result = {
                        "extractor": extractor.name,
                        "success": result.get("success", False),
                        "extraction_time": result.get("extraction_time", 0),
                        "text_length": result.get("text_length", 0),
                        "text_preview": result.get("text_preview", ""),
                        "error": result.get("error") if not result.get("success", False) else None
                    }
                
                detailed_results.append(detailed_result)
                
            except Exception as e:
                detailed_results.append({
                    "extractor": extractor.name,
                    "success": False,
                    "extraction_time": 0,
                    "text_length": 0,
                    "text_preview": "",
                    "error": str(e)
                })
        
        # 최고 성능 추출기 선정
        successful_results = [r for r in detailed_results if r["success"]]
        best_extractor = None
        
        if successful_results:
            # 단순한 점수 계산 (텍스트 길이 / 시간)
            for result in successful_results:
                time_taken = max(result["extraction_time"], 0.001)  # 0으로 나누기 방지
                result["score"] = result["text_length"] / time_taken
            
            best_result = max(successful_results, key=lambda x: x["score"])
            best_extractor = {
                "name": best_result["extractor"],
                "score": best_result["score"]
            }
        
        return {
            "results": {
                "detailed_results": detailed_results,
                "best_extractor": best_extractor,
                "file_path": file_path,
                "successful_extractors": len(successful_results),
                "total_extractors": len(detailed_results)
            }
        }
    
    def _analyze_extraction_results(self, results: List[Dict], file_type: str) -> Dict[str, Any]:
        """추출 결과 분석"""
        
        if not results:
            return {"error": f"{file_type} 추출 결과가 없습니다"}
        
        # 결과 정리 - 메트릭 구조에 맞춰 조정
        processed_results = []
        for result in results:
            # 이미 메트릭 형태인 경우와 전체 결과 형태인 경우 모두 처리
            if "extractor_name" in result:
                # 이미 메트릭 형태
                processed_results.append(result)
            elif "metrics" in result:
                # 전체 결과에서 메트릭 추출
                metrics = result["metrics"].copy()
                if "text" in result:
                    metrics["text_content"] = result["text"]
                processed_results.append(metrics)
            else:
                # 기본 결과 형태
                processed_results.append(result)
        
        if not processed_results:
            return {"error": f"{file_type} 처리 가능한 결과가 없습니다"}
        
        # 추출기별 성능 분석 (pandas 없이)
        extractor_performance = {}
        
        # 추출기별로 결과 그룹화
        extractor_groups = {}
        for result in processed_results:
            extractor_name = result.get('extractor_name', result.get('extractor', 'unknown'))
            if extractor_name not in extractor_groups:
                extractor_groups[extractor_name] = []
            extractor_groups[extractor_name].append(result)
        
        for extractor_name, extractor_results in extractor_groups.items():
            successful_results = [r for r in extractor_results if r.get('success', False)]
            
            success_rate = len(successful_results) / len(extractor_results) if extractor_results else 0
            
            if successful_results:
                avg_time = sum(r.get('extraction_time', 0) for r in successful_results) / len(successful_results)
                avg_text_length = sum(r.get('text_length', 0) for r in successful_results) / len(successful_results)
                avg_word_count = sum(r.get('word_count', 0) for r in successful_results) / len(successful_results)
                
                # 텍스트 품질 평가 (간단한 버전)
                text_contents = [r.get('text_content', '') for r in successful_results if r.get('text_content')]
                quality_score = self._evaluate_text_quality_simple(text_contents)
            else:
                avg_time = 0
                avg_text_length = 0
                avg_word_count = 0
                quality_score = 0
            
            extractor_performance[extractor_name] = {
                "success_rate": success_rate,
                "avg_extraction_time": avg_time,
                "avg_text_length": avg_text_length,
                "avg_word_count": avg_word_count,
                "text_quality_score": quality_score,
                "processed_files": len(extractor_results)
            }
        
        # 최적 추출기 선정
        best_extractor = self._select_best_extractor(extractor_performance)
        
    def _evaluate_text_quality_simple(self, text_contents: List[str]) -> float:
        """간단한 텍스트 품질 평가"""
        if not text_contents:
            return 0.0
        
        quality_scores = []
        for text in text_contents:
            if not text:
                quality_scores.append(0.0)
                continue
                
            score = 0.0
            # 한글 포함 여부
            if re.search(r'[가-힣]', text):
                score += 0.4
            # 적절한 길이
            if len(text) > 100:
                score += 0.3
            # 특수문자 비율 확인
            special_ratio = len(re.findall(r'[^\w\s가-힣]', text)) / len(text)
            if special_ratio < 0.2:
                score += 0.3
                
            quality_scores.append(score)
        
        return sum(quality_scores) / len(quality_scores)
        
        # 상세 결과
        detailed_results = []
        for result in processed_results:
            detailed_results.append({
                "file_name": result.get("file_name"),
                "extractor": result["metrics"]["extractor_name"],
                "success": result["metrics"]["success"],
                "extraction_time": result["metrics"]["extraction_time"],
                "text_length": result["metrics"]["text_length"],
                "word_count": result["metrics"]["word_count"],
                "error": result["metrics"]["error"],
                "text_preview": result["metrics"]["text_preview"]
            })
        
        return {
            "file_type": file_type,
            "total_files": len(set(r["file_name"] for r in results)),
            "total_extractions": len(results),
            "extractor_performance": extractor_performance,
            "best_extractor": best_extractor,
            "detailed_results": detailed_results,
            "summary": self._generate_summary(extractor_performance, file_type)
        }
    
    def _evaluate_text_quality(self, texts: List[str]) -> float:
        """텍스트 품질 평가"""
        
        if not texts:
            return 0.0
        
        quality_scores = []
        
        for text in texts:
            if not text:
                quality_scores.append(0.0)
                continue
            
            # 기본 품질 지표들
            score = 0.0
            
            # 1. 텍스트 길이 (적절한 길이)
            if 100 <= len(text) <= 10000:
                score += 0.2
            elif len(text) > 50:
                score += 0.1
            
            # 2. 한글 비율
            korean_chars = len(re.findall(r'[가-힣]', text))
            if korean_chars > 0:
                korean_ratio = korean_chars / len(text)
                score += min(korean_ratio * 0.3, 0.3)
            
            # 3. 단어 구조 (공백으로 구분된 단어들)
            words = text.split()
            if len(words) > 10:
                score += 0.2
            elif len(words) > 5:
                score += 0.1
            
            # 4. 문장 구조 (마침표, 줄바꿈 등)
            sentences = re.split(r'[.!?]\s*', text)
            if len(sentences) > 3:
                score += 0.2
            elif len(sentences) > 1:
                score += 0.1
            
            # 5. 특수문자 비율 (너무 많으면 감점)
            special_chars = len(re.findall(r'[^\w\s가-힣.,!?]', text))
            special_ratio = special_chars / len(text) if len(text) > 0 else 0
            if special_ratio < 0.1:
                score += 0.1
            
            quality_scores.append(min(score, 1.0))
        
        return sum(quality_scores) / len(quality_scores)
    
    def _select_best_extractor(self, performance: Dict[str, Dict]) -> Dict[str, Any]:
        """최적 추출기 선정"""
        
        if not performance:
            return {"name": None, "score": 0.0}
        
        extractor_scores = {}
        
        for name, metrics in performance.items():
            # 종합 점수 계산 (가중평균)
            score = (
                metrics["success_rate"] * 0.4 +           # 성공률 40%
                metrics["text_quality_score"] * 0.3 +     # 텍스트 품질 30%
                (1 / (1 + metrics["avg_extraction_time"])) * 0.2 +  # 속도 20%
                min(metrics["avg_text_length"] / 1000, 1.0) * 0.1   # 텍스트 길이 10%
            )
            
            extractor_scores[name] = score
        
        best_name = max(extractor_scores.keys(), key=lambda k: extractor_scores[k])
        best_score = extractor_scores[best_name]
        
        return {
            "name": best_name,
            "score": best_score,
            "metrics": performance[best_name],
            "all_scores": extractor_scores
        }
    
    def _generate_summary(self, performance: Dict, file_type: str) -> str:
        """성능 비교 요약 생성"""
        
        if not performance:
            return f"{file_type} 추출기 성능 데이터가 없습니다."
        
        summary_lines = [f"\n=== {file_type} 텍스트 추출기 성능 비교 ===\n"]
        
        # 각 추출기별 요약
        for name, metrics in performance.items():
            summary_lines.append(f"📄 {name}:")
            summary_lines.append(f"  - 성공률: {metrics['success_rate']:.1%}")
            summary_lines.append(f"  - 평균 처리 시간: {metrics['avg_extraction_time']:.2f}초")
            summary_lines.append(f"  - 평균 텍스트 길이: {metrics['avg_text_length']:.0f}자")
            summary_lines.append(f"  - 텍스트 품질: {metrics['text_quality_score']:.2f}/1.0")
            summary_lines.append("")
        
        return "\n".join(summary_lines)
    
    def get_best_extractor_for_file(self, file_path: str) -> Optional[BaseTextExtractor]:
        """파일에 대한 최적 추출기 반환"""
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext == '.pdf':
            if self.available_pdf_extractors:
                # 간단한 테스트로 최적 추출기 선정
                test_results = []
                for extractor in self.available_pdf_extractors[:2]:  # 처음 2개만 테스트
                    try:
                        result = extractor.extract_with_metrics(file_path)
                        if result["metrics"]["success"]:
                            test_results.append((extractor, result["metrics"]["text_length"]))
                    except:
                        continue
                
                if test_results:
                    # 가장 많은 텍스트를 추출한 추출기 선택
                    return max(test_results, key=lambda x: x[1])[0]
                else:
                    return self.available_pdf_extractors[0]
        
        elif file_ext == '.hwp':
            if self.available_hwp_extractors:
                return self.available_hwp_extractors[0]
        
        return None


def main():
    """텍스트 추출 비교 시스템 테스트"""
    
    logging.basicConfig(level=logging.INFO)
    
    print("📄 텍스트 추출 방법 비교 시스템 테스트")
    print("=" * 50)
    
    # 비교 시스템 생성
    comparison = TextExtractionComparison()
    
    # 사용 가능한 추출기 확인
    print(f"사용 가능한 PDF 추출기: {[e.name for e in comparison.available_pdf_extractors]}")
    print(f"사용 가능한 HWP 추출기: {[e.name for e in comparison.available_hwp_extractors]}")
    
    # 샘플 파일로 테스트 (실제 파일이 있는 경우)
    test_pdf_files = []
    test_hwp_files = []
    
    # data 디렉토리에서 테스트 파일 찾기
    data_dir = Path("../data/복지로")
    if data_dir.exists():
        test_pdf_files = list(data_dir.rglob("*.pdf"))[:3]  # 최대 3개
        test_hwp_files = list(data_dir.rglob("*.hwp"))[:3]  # 최대 3개
    
    # PDF 추출기 비교
    if test_pdf_files and comparison.available_pdf_extractors:
        print(f"\n🔍 PDF 추출기 비교 테스트 ({len(test_pdf_files)}개 파일)")
        pdf_results = comparison.compare_pdf_extractors([str(f) for f in test_pdf_files])
        
        if "error" not in pdf_results:
            print(pdf_results["summary"])
            best_pdf = pdf_results["best_extractor"]
            print(f"🏆 최적 PDF 추출기: {best_pdf['name']} (점수: {best_pdf['score']:.3f})")
    
    # HWP 추출기 비교  
    if test_hwp_files and comparison.available_hwp_extractors:
        print(f"\n🔍 HWP 추출기 비교 테스트 ({len(test_hwp_files)}개 파일)")
        hwp_results = comparison.compare_hwp_extractors([str(f) for f in test_hwp_files])
        
        if "error" not in hwp_results:
            print(hwp_results["summary"])
            best_hwp = hwp_results["best_extractor"]
            print(f"🏆 최적 HWP 추출기: {best_hwp['name']} (점수: {best_hwp['score']:.3f})")
    
    print(f"\n✅ 텍스트 추출 비교 시스템 테스트 완료!")


if __name__ == "__main__":
    main()