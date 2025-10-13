# =========================================
# 📄 텍스트 추출 모듈
# =========================================

import os
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
import pandas as pd
from datetime import datetime

# PDF 처리 라이브러리
try:
    import PyPDF2
    import pdfplumber
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

# HWP 처리 라이브러리
try:
    import olefile
    HWP_AVAILABLE = True
except ImportError:
    HWP_AVAILABLE = False

# 텍스트 추출 비교 시스템
try:
    from .text_extraction_comparison import TextExtractionComparison
    COMPARISON_AVAILABLE = True
except ImportError:
    COMPARISON_AVAILABLE = False

logger = logging.getLogger(__name__)


class WelfareDocumentExtractor:
    """노인복지 정책 문서 텍스트 추출 클래스"""
    
    def __init__(self, 
                 data_directory: str = None, 
                 cache_enabled: bool = True, 
                 cache_directory: str = "./cache"):
        """
        Args:
            data_directory: 복지로 데이터 디렉토리 경로
            cache_enabled: 캐시 사용 여부
            cache_directory: 캐시 디렉토리 경로
        """
        if data_directory is None:
            # 기본 경로: 프로젝트 루트의 data/복지로
            # 현재 위치에서 상위로 가서 data 디렉토리를 찾음
            current_dir = Path(__file__).parent
            self.data_dir = current_dir.parent / "data" / "복지로"
        else:
            self.data_dir = Path(data_directory)
        
        self.cache_enabled = cache_enabled
        self.cache_directory = Path(cache_directory)
        
        if self.cache_enabled:
            self.cache_directory.mkdir(exist_ok=True)
        
        self.supported_formats = ['.pdf', '.hwp', '.txt']
        self.extracted_texts = []
        
        # 텍스트 추출 비교 시스템 초기화
        self.extraction_comparison = None
        if COMPARISON_AVAILABLE:
            self.extraction_comparison = TextExtractionComparison()
        
    def check_dependencies(self) -> Dict[str, bool]:
        """필요한 라이브러리 설치 상태 확인"""
        dependencies = {
            'PDF': PDF_AVAILABLE,
            'HWP': HWP_AVAILABLE
        }
        
        missing = [name for name, available in dependencies.items() if not available]
        if missing:
            logger.warning(f"누락된 라이브러리: {', '.join(missing)}")
            logger.info("설치 명령어:")
            if 'PDF' in missing:
                logger.info("  pip install PyPDF2 pdfplumber")
            if 'HWP' in missing:
                logger.info("  pip install olefile")
        
        return dependencies
    
    def extract_text_from_pdf(self, file_path: Path) -> Tuple[str, Dict]:
        """PDF 파일에서 텍스트 추출"""
        if not PDF_AVAILABLE:
            return "", {"error": "PDF 라이브러리가 설치되지 않음"}
        
        text = ""
        metadata = {
            "file_type": "PDF",
            "pages": 0,
            "extraction_method": "pdfplumber"
        }
        
        try:
            # pdfplumber 우선 시도 (더 정확함)
            with pdfplumber.open(file_path) as pdf:
                pages_text = []
                for page_num, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        pages_text.append(f"[페이지 {page_num + 1}]\n{page_text}")
                
                text = "\n\n".join(pages_text)
                metadata["pages"] = len(pdf.pages)
                
        except Exception as e:
            logger.warning(f"pdfplumber 실패, PyPDF2로 재시도: {e}")
            
            # PyPDF2로 백업 시도
            try:
                with open(file_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    pages_text = []
                    
                    for page_num, page in enumerate(pdf_reader.pages):
                        page_text = page.extract_text()
                        if page_text:
                            pages_text.append(f"[페이지 {page_num + 1}]\n{page_text}")
                    
                    text = "\n\n".join(pages_text)
                    metadata["pages"] = len(pdf_reader.pages)
                    metadata["extraction_method"] = "PyPDF2"
                    
            except Exception as e2:
                logger.error(f"PDF 추출 실패 {file_path}: {e2}")
                metadata["error"] = str(e2)
        
        return text, metadata
    
    def extract_text_from_hwp(self, file_path: Path) -> Tuple[str, Dict]:
        """HWP 파일에서 텍스트 추출 (기본 구현)"""
        if not HWP_AVAILABLE:
            return "", {"error": "HWP 라이브러리가 설치되지 않음"}
        
        metadata = {
            "file_type": "HWP",
            "extraction_method": "olefile"
        }
        
        try:
            # HWP 파일은 복합 문서 형태이므로 olefile로 구조 분석
            if olefile.isOleFile(file_path):
                with olefile.OleFileIO(file_path) as ole:
                    # HWP 파일 구조에서 텍스트 스트림 찾기
                    text = self._extract_hwp_text_streams(ole)
                    metadata["streams_found"] = True
            else:
                logger.warning(f"올바른 HWP 파일이 아님: {file_path}")
                text = ""
                metadata["error"] = "올바른 HWP 파일 형식이 아님"
                
        except Exception as e:
            logger.error(f"HWP 추출 실패 {file_path}: {e}")
            # HWP 파일을 바이너리로 읽어 간단한 텍스트 추출 시도
            text = self._extract_hwp_fallback(file_path)
            metadata["error"] = str(e)
            metadata["extraction_method"] = "fallback"
        
        return text, metadata
    
    def _extract_hwp_text_streams(self, ole) -> str:
        """HWP OLE 파일에서 텍스트 스트림 추출"""
        text_parts = []
        
        try:
            # HWP 파일의 일반적인 텍스트 스트림들
            text_streams = [
                'PrvText',
                'DocInfo/HwpSummaryInformation',
                'BodyText/Section0',
                'ViewText/Section0'
            ]
            
            for stream_name in text_streams:
                try:
                    if ole._olestream_size.get(stream_name, 0) > 0:
                        stream = ole.opendir(stream_name)
                        data = stream.read()
                        # 한글 문자 인코딩 처리
                        text_part = self._decode_hwp_text(data)
                        if text_part:
                            text_parts.append(text_part)
                except:
                    continue
        
        except Exception as e:
            logger.debug(f"HWP 스트림 추출 중 오류: {e}")
        
        return "\n\n".join(text_parts) if text_parts else ""
    
    def _decode_hwp_text(self, data: bytes) -> str:
        """HWP 바이너리 데이터에서 텍스트 디코딩"""
        # HWP 파일의 텍스트는 UTF-16LE 또는 CP949로 인코딩되어 있을 수 있음
        encodings = ['utf-16le', 'cp949', 'utf-8', 'euc-kr']
        
        for encoding in encodings:
            try:
                text = data.decode(encoding, errors='ignore')
                # 의미있는 한글 텍스트가 포함되어 있는지 확인
                if any(ord(c) >= 0xAC00 and ord(c) <= 0xD7A3 for c in text):
                    return text
            except:
                continue
        
        return ""
    
    def _extract_hwp_fallback(self, file_path: Path) -> str:
        """HWP 파일 폴백 텍스트 추출 (단순 바이너리 읽기)"""
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                # 바이너리에서 한글 텍스트 패턴 찾기
                text = self._decode_hwp_text(data)
                # 불필요한 제어 문자 제거
                text = ''.join(c for c in text if c.isprintable() or c in '\n\t ')
                return text
        except Exception as e:
            logger.error(f"HWP 폴백 추출 실패: {e}")
            return ""
    
    def extract_text_from_txt(self, file_path: Path) -> Tuple[str, Dict]:
        """TXT 파일에서 텍스트 추출"""
        metadata = {
            "file_type": "TXT",
            "extraction_method": "direct"
        }
        
        encodings = ['utf-8', 'cp949', 'euc-kr', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read()
                    metadata["encoding"] = encoding
                    return text, metadata
            except UnicodeDecodeError:
                continue
        
        # 모든 인코딩 실패시 바이너리로 읽고 에러 무시
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
                text = data.decode('utf-8', errors='ignore')
                metadata["encoding"] = "utf-8 (errors ignored)"
                return text, metadata
        except Exception as e:
            logger.error(f"TXT 파일 읽기 실패 {file_path}: {e}")
            return "", {"error": str(e)}
    
    def extract_from_file(self, file_path: Path) -> Dict:
        """단일 파일에서 텍스트 추출"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return {
                "file_path": str(file_path),
                "error": "파일이 존재하지 않음",
                "text": "",
                "metadata": {}
            }
        
        suffix = file_path.suffix.lower()
        
        # 파일 형식별 처리
        if suffix == '.pdf':
            text, metadata = self.extract_text_from_pdf(file_path)
        elif suffix == '.hwp':
            text, metadata = self.extract_text_from_hwp(file_path)
        elif suffix == '.txt':
            text, metadata = self.extract_text_from_txt(file_path)
        else:
            return {
                "file_path": str(file_path),
                "error": f"지원되지 않는 파일 형식: {suffix}",
                "text": "",
                "metadata": {}
            }
        
        # 기본 메타데이터 추가
        metadata.update({
            "file_name": file_path.name,
            "file_size": file_path.stat().st_size,
            "extraction_time": datetime.now().isoformat(),
            "text_length": len(text)
        })
        
        return {
            "file_path": str(file_path),
            "text": text,
            "metadata": metadata,
            "success": len(text) > 0
        }
    
    def scan_welfare_directory(self) -> List[Path]:
        """복지로 디렉토리에서 지원되는 파일들 스캔"""
        files = []
        
        if not self.data_dir.exists():
            logger.error(f"데이터 디렉토리가 존재하지 않음: {self.data_dir}")
            return files
        
        # 재귀적으로 지원 파일 형식 찾기
        for suffix in self.supported_formats:
            pattern = f"**/*{suffix}"
            found_files = list(self.data_dir.glob(pattern))
            files.extend(found_files)
            logger.info(f"{suffix} 파일 {len(found_files)}개 발견")
        
        logger.info(f"총 {len(files)}개 파일 발견")
        return files
    
    def compare_extraction_methods(self, sample_files: List[str] = None, max_files: int = 5) -> Dict[str, Any]:
        """텍스트 추출 방법 성능 비교"""
        
        if not COMPARISON_AVAILABLE:
            logger.warning("텍스트 추출 비교 시스템을 사용할 수 없습니다")
            return {"error": "comparison system not available"}
        
        logger.info("📊 텍스트 추출 방법 성능 비교 시작")
        
        # 샘플 파일 준비
        if sample_files is None:
            files = self.scan_welfare_directory()
            pdf_files = [str(f) for f in files if f.suffix.lower() == '.pdf'][:max_files]
            hwp_files = [str(f) for f in files if f.suffix.lower() == '.hwp'][:max_files]
        else:
            pdf_files = [f for f in sample_files if f.endswith('.pdf')]
            hwp_files = [f for f in sample_files if f.endswith('.hwp')]
        
        comparison_results = {}
        
        # PDF 추출기 비교
        if pdf_files:
            logger.info(f"PDF 추출 방법 비교 ({len(pdf_files)}개 파일)")
            pdf_comparison = self.extraction_comparison.compare_pdf_extractors(pdf_files)
            comparison_results["pdf_comparison"] = pdf_comparison
        
        # HWP 추출기 비교
        if hwp_files:
            logger.info(f"HWP 추출 방법 비교 ({len(hwp_files)}개 파일)")
            hwp_comparison = self.extraction_comparison.compare_hwp_extractors(hwp_files)
            comparison_results["hwp_comparison"] = hwp_comparison
        
        # 추천 추출기 설정
        recommended_extractors = {}
        
        if "pdf_comparison" in comparison_results and "best_extractor" in comparison_results["pdf_comparison"]:
            recommended_extractors["pdf"] = comparison_results["pdf_comparison"]["best_extractor"]["name"]
        
        if "hwp_comparison" in comparison_results and "best_extractor" in comparison_results["hwp_comparison"]:
            recommended_extractors["hwp"] = comparison_results["hwp_comparison"]["best_extractor"]["name"]
        
        comparison_results["recommended_extractors"] = recommended_extractors
        comparison_results["comparison_summary"] = self._generate_comparison_summary(comparison_results)
        
        logger.info("✅ 텍스트 추출 방법 비교 완료")
        return comparison_results
    
    def _generate_comparison_summary(self, comparison_results: Dict[str, Any]) -> str:
        """비교 결과 요약 생성"""
        
        summary_lines = ["📊 텍스트 추출 방법 비교 결과", "=" * 40]
        
        if "pdf_comparison" in comparison_results:
            pdf_result = comparison_results["pdf_comparison"]
            if "best_extractor" in pdf_result:
                best_pdf = pdf_result["best_extractor"]
                summary_lines.extend([
                    "",
                    f"🏆 최적 PDF 추출기: {best_pdf['name']}",
                    f"  - 성능 점수: {best_pdf['score']:.3f}",
                    f"  - 성공률: {best_pdf['metrics']['success_rate']:.1%}",
                    f"  - 평균 처리 시간: {best_pdf['metrics']['avg_extraction_time']:.2f}초"
                ])
        
        if "hwp_comparison" in comparison_results:
            hwp_result = comparison_results["hwp_comparison"]
            if "best_extractor" in hwp_result:
                best_hwp = hwp_result["best_extractor"]
                summary_lines.extend([
                    "",
                    f"🏆 최적 HWP 추출기: {best_hwp['name']}",
                    f"  - 성능 점수: {best_hwp['score']:.3f}",
                    f"  - 성공률: {best_hwp['metrics']['success_rate']:.1%}",
                    f"  - 평균 처리 시간: {best_hwp['metrics']['avg_extraction_time']:.2f}초"
                ])
        
        if comparison_results.get("recommended_extractors"):
            summary_lines.extend([
                "",
                "💡 추천 설정:",
                f"  - PDF: {comparison_results['recommended_extractors'].get('pdf', 'N/A')}",
                f"  - HWP: {comparison_results['recommended_extractors'].get('hwp', 'N/A')}"
            ])
        
        return "\n".join(summary_lines)
    
    def extract_all_documents(self, max_files: Optional[int] = None, use_best_extractor: bool = False) -> List[Dict]:
        """모든 복지 문서에서 텍스트 추출"""
        logger.info("복지로 문서 텍스트 추출 시작")
        
        # 최적 추출기 사용 옵션
        best_extractors = {}
        if use_best_extractor and self.extraction_comparison:
            logger.info("최적 추출기 결정을 위한 샘플 비교 실행...")
            comparison_result = self.compare_extraction_methods(max_files=3)
            best_extractors = comparison_result.get("recommended_extractors", {})
            logger.info(f"선택된 최적 추출기: {best_extractors}")
        
        files = self.scan_welfare_directory()
        
        if max_files:
            files = files[:max_files]
            logger.info(f"처리할 파일 수를 {max_files}개로 제한")
        
        results = []
        
        for i, file_path in enumerate(files, 1):
            logger.info(f"[{i}/{len(files)}] 처리 중: {file_path.name}")
            
            try:
                # 최적 추출기 사용
                if use_best_extractor and best_extractors:
                    result = self._extract_with_best_method(file_path, best_extractors)
                else:
                    result = self.extract_from_file(file_path)
                
                # 지역 정보 추출 (파일 경로에서)
                region_info = self._extract_region_from_path(file_path)
                result["metadata"].update(region_info)
                
                results.append(result)
                
                if result["success"]:
                    logger.debug(f"  ✅ 성공: {result['metadata']['text_length']} 글자")
                else:
                    logger.warning(f"  ❌ 실패: {result.get('error', '알 수 없는 오류')}")
                    
            except Exception as e:
                logger.error(f"  ❌ 처리 중 오류: {e}")
                results.append({
                    "file_path": str(file_path),
                    "error": str(e),
                    "text": "",
                    "metadata": {},
                    "success": False
                })
        
        # 결과 요약
        successful = sum(1 for r in results if r["success"])
        logger.info(f"텍스트 추출 완료: {successful}/{len(results)} 성공")
        
        return results
    
    def _extract_with_best_method(self, file_path: Path, best_extractors: Dict[str, str]) -> Dict[str, Any]:
        """최적 추출기를 사용한 텍스트 추출"""
        
        file_ext = file_path.suffix.lower()
        
        if file_ext == '.pdf' and 'pdf' in best_extractors and self.extraction_comparison:
            # 지정된 최적 PDF 추출기 사용
            best_extractor = self.extraction_comparison.get_best_extractor_for_file(str(file_path))
            if best_extractor:
                try:
                    extraction_result = best_extractor.extract_with_metrics(str(file_path))
                    return {
                        "file_path": str(file_path),
                        "content": extraction_result["text"],
                        "source": file_path.name,
                        "metadata": {
                            **extraction_result["metrics"],
                            "extraction_method": f"best_{best_extractor.name}",
                            "text_length": len(extraction_result["text"])
                        },
                        "success": extraction_result["metrics"]["success"]
                    }
                except Exception as e:
                    logger.warning(f"최적 PDF 추출기 실패, 기본 방법 사용: {e}")
        
        elif file_ext == '.hwp' and 'hwp' in best_extractors and self.extraction_comparison:
            # 지정된 최적 HWP 추출기 사용
            best_extractor = self.extraction_comparison.get_best_extractor_for_file(str(file_path))
            if best_extractor:
                try:
                    extraction_result = best_extractor.extract_with_metrics(str(file_path))
                    return {
                        "file_path": str(file_path),
                        "content": extraction_result["text"],
                        "source": file_path.name,
                        "metadata": {
                            **extraction_result["metrics"],
                            "extraction_method": f"best_{best_extractor.name}",
                            "text_length": len(extraction_result["text"])
                        },
                        "success": extraction_result["metrics"]["success"]
                    }
                except Exception as e:
                    logger.warning(f"최적 HWP 추출기 실패, 기본 방법 사용: {e}")
        
        # 기본 방법 사용
        return self.extract_from_file(file_path)
    
    def _extract_region_from_path(self, file_path: Path) -> Dict[str, str]:
        """파일 경로에서 지역 정보 추출"""
        path_parts = file_path.parts
        region_info = {}
        
        # 경로에서 지역명 찾기
        regions = ["경북", "대구", "부산", "전국", "전남", "전북"]
        for part in path_parts:
            if part in regions:
                region_info["region"] = part
                break
        
        # 파일 형식
        if "hwp" in path_parts:
            region_info["file_format"] = "hwp"
        elif "pdf" in path_parts:
            region_info["file_format"] = "pdf"
        
        return region_info
    
    def save_extraction_results(self, results: List[Dict], output_path: str = None) -> str:
        """추출 결과를 CSV로 저장"""
        if output_path is None:
            output_path = f"welfare_documents_extracted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        # DataFrame으로 변환
        data = []
        for result in results:
            row = {
                "file_path": result["file_path"],
                "file_name": result.get("metadata", {}).get("file_name", ""),
                "region": result.get("metadata", {}).get("region", ""),
                "file_format": result.get("metadata", {}).get("file_format", ""),
                "file_type": result.get("metadata", {}).get("file_type", ""),
                "text_length": result.get("metadata", {}).get("text_length", 0),
                "success": result["success"],
                "error": result.get("error", ""),
                "text": result["text"]
            }
            data.append(row)
        
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        logger.info(f"추출 결과 저장: {output_path}")
        return output_path
    
    def get_extraction_summary(self, results: List[Dict]) -> Dict:
        """추출 결과 요약 통계"""
        total_files = len(results)
        successful = sum(1 for r in results if r["success"])
        
        # 파일 형식별 통계
        format_stats = {}
        region_stats = {}
        
        for result in results:
            # 파일 형식
            file_type = result.get("metadata", {}).get("file_type", "Unknown")
            format_stats[file_type] = format_stats.get(file_type, 0) + 1
            
            # 지역별
            region = result.get("metadata", {}).get("region", "Unknown")
            region_stats[region] = region_stats.get(region, 0) + 1
        
        return {
            "total_files": total_files,
            "successful_extractions": successful,
            "success_rate": successful / total_files if total_files > 0 else 0,
            "format_statistics": format_stats,
            "region_statistics": region_stats,
            "total_text_length": sum(r.get("metadata", {}).get("text_length", 0) for r in results)
        }


def main():
    """텍스트 추출 테스트 실행"""
    import sys
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 테스트 실행
    extractor = WelfareDocumentExtractor()
    
    # 의존성 확인
    dependencies = extractor.check_dependencies()
    print("의존성 확인:", dependencies)
    
    # 파일 스캔
    files = extractor.scan_welfare_directory()
    print(f"발견된 파일 수: {len(files)}")
    
    if len(files) > 0:
        # 최대 5개 파일만 테스트
        print("\n샘플 파일 텍스트 추출 테스트...")
        results = extractor.extract_all_documents(max_files=5)
        
        # 결과 출력
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] {result['file_path']}")
            print(f"  성공: {result['success']}")
            if result['success']:
                text_preview = result['text'][:200] + "..." if len(result['text']) > 200 else result['text']
                print(f"  텍스트 미리보기: {text_preview}")
            else:
                print(f"  오류: {result.get('error', '알 수 없음')}")
        
        # 요약 통계
        summary = extractor.get_extraction_summary(results)
        print(f"\n📊 추출 결과 요약:")
        print(f"  총 파일 수: {summary['total_files']}")
        print(f"  성공 추출: {summary['successful_extractions']}")
        print(f"  성공률: {summary['success_rate']:.1%}")
        print(f"  총 텍스트 길이: {summary['total_text_length']:,} 글자")


if __name__ == "__main__":
    main()