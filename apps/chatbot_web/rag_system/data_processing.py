"""
데이터 처리 모듈

복지 정책 문서 로딩, 임베딩, 벡터 저장소 관리
"""

import os

# ChromaDB 텔레메트리 완전 비활성화 (import 전에 먼저 설정)
os.environ['CHROMA_TELEMETRY'] = '0'
os.environ['ANONYMIZED_TELEMETRY'] = 'False'
os.environ['CHROMA_ANONYMIZED_TELEMETRY'] = 'False'

import logging
import hashlib
from typing import List, Dict, Any, Optional
from pathlib import Path
import pickle

try:
    import PyPDF2
    from PyPDF2 import PdfReader
except ImportError:
    PyPDF2 = None
    PdfReader = None

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None

try:
    import pdfplumber
except ImportError:
    pdfplumber = None

try:
    from PIL import Image
    import io
except ImportError:
    Image = None
    io = None

try:
    import pytesseract
    # Windows에서 Tesseract 경로 설정
    import platform
    if platform.system() == 'Windows':
        tesseract_paths = [
            r'C:\Program Files\Tesseract-OCR\tesseract.exe',
            r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
        ]
        for path in tesseract_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                print(f"[INFO] Tesseract 경로 설정: {path}")
                break
except ImportError:
    pytesseract = None

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    chromadb = None

try:
    import openai
except ImportError:
    openai = None

# Django 호환을 위해 rag_config 사용
from . import rag_config

DATA_DIR = str(rag_config.MAIN_DATA_DIR.parent)  # data 폴더
EMBEDDING_CACHE_DIR = str(rag_config.BASE_DIR / 'embeddings_cache')
CHROMA_DB_DIR = str(rag_config.MAIN_CHROMA_DB_DIR)
CHUNK_SIZE = rag_config.CHUNK_SIZE
CHUNK_OVERLAP = rag_config.CHUNK_OVERLAP
OPENAI_EMB_MODEL = rag_config.OPENAI_EMB_MODEL
get_openai_api_key = rag_config.get_openai_api_key

logger = logging.getLogger(__name__)

class WelfareDocumentLoader:
    """복지 정책 문서 로더"""

    def __init__(self, welfare_dir: str = None):
        """
        Args:
            welfare_dir: 복지 데이터 디렉토리 (예: data/복지로 또는 data/복지로 - 복사본)
        """
        if welfare_dir:
            self.welfare_dir = welfare_dir
        else:
            self.welfare_dir = os.path.join(DATA_DIR, "복지로")
        self.data_dir = os.path.dirname(self.welfare_dir)

        # 사용할 데이터 디렉토리 로그
        logger.info(f"WelfareDocumentLoader 초기화: {self.welfare_dir}")
        
    def load_welfare_documents(self) -> List[Dict[str, Any]]:
        """복지 정책 문서 로드"""
        logger.info("복지 정책 문서 로딩 시작")
        documents = []
        
        if not os.path.exists(self.welfare_dir):
            logger.error(f"복지 데이터 디렉토리가 없습니다: {self.welfare_dir}")
            return documents
        
        # 지역별 문서 로딩
        regions = ['경남', '경북', '대구', '부산', '전국', '전남', '전북']
        
        for region in regions:
            region_path = os.path.join(self.welfare_dir, region)
            if os.path.exists(region_path):
                logger.info(f"지역 '{region}' 문서 로딩 중...")
                region_docs = self._load_region_documents(region, region_path)
                documents.extend(region_docs)
                logger.info(f"지역 '{region}': {len(region_docs)}개 문서 로드")
        
        logger.info(f"총 {len(documents)}개 문서 로드 완료")
        return documents
    
    def _load_region_documents(self, region: str, region_path: str) -> List[Dict[str, Any]]:
        """지역별 문서 로딩 (PDF만)"""
        documents = []

        # PDF 파일 로딩
        pdf_files = list(Path(region_path).glob("*.pdf"))
        # pdf 하위폴더도 확인
        pdf_dir = os.path.join(region_path, "pdf")
        if os.path.exists(pdf_dir):
            pdf_files.extend(list(Path(pdf_dir).glob("*.pdf")))

        if pdf_files:
            pdf_docs = self._load_pdf_files(region, pdf_files)
            documents.extend(pdf_docs)

        return documents
    
    def _load_pdf_files(self, region: str, pdf_files: List[Path]) -> List[Dict[str, Any]]:
        """PDF 파일 로딩 (OCR 포함)"""
        documents = []

        if not fitz and not pdfplumber and not PdfReader:
            logger.warning("PDF 라이브러리가 설치되지 않음 - PDF 파일 건너뜀")
            return documents

        for file_path in pdf_files:
            try:
                # 파일 크기 확인 (0 바이트 또는 너무 작은 파일 스킵)
                file_size = file_path.stat().st_size
                if file_size < 100:
                    logger.warning(f"⊘ PDF 파일 너무 작음: {file_path.name} ({file_size} bytes) - 건너뜀")
                    continue

                text = self._extract_pdf_text_with_ocr(str(file_path))
                if text and len(text.strip()) > 50:
                    doc = {
                        'content': text,
                        'metadata': {
                            'source': str(file_path),
                            'filename': file_path.name,
                            'region': region,
                            'file_type': 'pdf'
                        }
                    }
                    documents.append(doc)
                    logger.info(f"✓ PDF 로드 성공: {file_path.name} ({len(text)} 문자)")
                else:
                    logger.warning(f"⊘ PDF 텍스트 부족 (손상 가능): {file_path.name} ({len(text) if text else 0} 문자) - 건너뜀")
            except Exception as e:
                logger.warning(f"⊘ PDF 파일 로딩 실패 (건너뜀): {file_path.name} - {str(e)[:100]}")
                continue  # 에러 발생 시 다음 파일로 계속

        return documents

    def _extract_pdf_text_with_ocr(self, pdf_path: str) -> str:
        """PDF 텍스트 추출 (텍스트 추출 → OCR 폴백)"""

        # 1단계: 일반 텍스트 추출 시도 (PyMuPDF → pdfplumber → PyPDF2)
        text = self._extract_pdf_text(pdf_path)

        # 텍스트가 충분히 추출되었으면 반환
        if text and len(text.strip()) > 100:
            return text

        # 2단계: OCR 시도 (텍스트가 부족하거나 없으면)
        logger.info(f"일반 추출 실패 ({len(text) if text else 0}자), OCR 시도: {Path(pdf_path).name}")
        ocr_text = self._extract_pdf_with_ocr(pdf_path)

        if ocr_text and len(ocr_text.strip()) > len(text if text else ""):
            return ocr_text

        return text if text else ""

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """PDF 일반 텍스트 추출 (PyMuPDF → pdfplumber → PyPDF2)"""

        # 방법 1: PyMuPDF (fitz) - 가장 강력하고 빠름
        if fitz:
            try:
                text = ""
                doc = fitz.open(pdf_path)
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    page_text = page.get_text()
                    if page_text and page_text.strip():
                        text += f"\n--- 페이지 {page_num + 1} ---\n{page_text}"
                doc.close()

                if text.strip():
                    return text.strip()
            except Exception as e:
                logger.warning(f"PyMuPDF 추출 실패: {e}")

        # 방법 2: pdfplumber - 표 추출에 강함
        if pdfplumber:
            try:
                text = ""
                with pdfplumber.open(pdf_path) as pdf:
                    for page_num, page in enumerate(pdf.pages):
                        page_text = page.extract_text()
                        if page_text and page_text.strip():
                            text += f"\n--- 페이지 {page_num + 1} ---\n{page_text}"

                if text.strip():
                    return text.strip()
            except Exception as e:
                logger.warning(f"pdfplumber 추출 실패: {e}")

        # 방법 3: PyPDF2 - 폴백
        if PdfReader:
            try:
                with open(pdf_path, 'rb') as file:
                    reader = PdfReader(file, strict=False)
                    text = ""

                    for page_num, page in enumerate(reader.pages):
                        try:
                            page_text = page.extract_text()
                            if page_text and page_text.strip():
                                text += f"\n--- 페이지 {page_num + 1} ---\n{page_text}"
                        except Exception as e:
                            logger.warning(f"페이지 {page_num + 1} 추출 실패: {e}")
                            continue

                    if text.strip():
                        return text.strip()
            except Exception as e:
                logger.warning(f"PyPDF2 추출 실패: {e}")

        return ""

    def _extract_pdf_with_ocr(self, pdf_path: str) -> str:
        """PDF OCR 추출 (이미지 기반 PDF용)"""

        if not fitz or not pytesseract or not Image:
            logger.warning("OCR 라이브러리 없음 (pymupdf, pytesseract, Pillow 필요)")
            return ""

        try:
            text = ""
            doc = fitz.open(pdf_path)

            for page_num in range(len(doc)):
                page = doc[page_num]

                # 페이지를 이미지로 변환 (200 DPI로 낮춤 - 속도 향상)
                pix = page.get_pixmap(dpi=200)
                img_data = pix.tobytes("png")

                # PIL Image로 변환
                image = Image.open(io.BytesIO(img_data))

                # Tesseract OCR (한국어 + 영어)
                try:
                    # timeout 설정 및 임시 파일 처리 개선
                    page_text = pytesseract.image_to_string(
                        image,
                        lang='kor+eng',
                        timeout=30  # 30초 타임아웃
                    )
                    if page_text and page_text.strip():
                        text += f"\n--- 페이지 {page_num + 1} (OCR) ---\n{page_text}"
                        logger.info(f"  OCR 성공: 페이지 {page_num + 1} ({len(page_text)}자)")
                except Exception as e:
                    logger.warning(f"  OCR 실패: 페이지 {page_num + 1} - {e}")
                finally:
                    # 이미지 메모리 해제
                    image.close()
                    del image
                    del pix

            doc.close()
            return text.strip()

        except Exception as e:
            logger.error(f"OCR 전체 실패: {e}")
            return ""
    
    def chunk_document(self, document: Dict[str, Any]) -> List[Dict[str, Any]]:
        """문서 청킹 - 문장 단위로 스마트하게 분할"""
        content = document['content']
        metadata = document['metadata']

        chunks = []

        # 1단계: 문장 단위로 분리 (줄바꿈 기준)
        import re
        sentences = re.split(r'[\n]+', content)

        current_chunk = ""
        chunk_sentences = []

        for sentence in sentences:
            sentence = sentence.strip()

            # 너무 짧은 문장 건너뛰기
            if len(sentence) < 10:
                continue

            # 현재 청크에 문장 추가
            potential_chunk = current_chunk + "\n" + sentence if current_chunk else sentence

            # 청크 크기 확인
            if len(potential_chunk) <= CHUNK_SIZE:
                # 아직 여유 있음 - 문장 추가
                current_chunk = potential_chunk
                chunk_sentences.append(sentence)
            else:
                # 청크가 너무 커짐 - 현재 청크 저장
                if current_chunk and len(current_chunk.strip()) >= 50:
                    chunk = {
                        'content': current_chunk.strip(),
                        'metadata': {
                            **metadata,
                            'chunk_id': len(chunks),
                            'sentence_count': len(chunk_sentences)
                        }
                    }
                    chunks.append(chunk)

                # 새로운 청크 시작
                current_chunk = sentence
                chunk_sentences = [sentence]

        # 마지막 청크 저장
        if current_chunk and len(current_chunk.strip()) >= 50:
            chunk = {
                'content': current_chunk.strip(),
                'metadata': {
                    **metadata,
                    'chunk_id': len(chunks),
                    'sentence_count': len(chunk_sentences)
                }
            }
            chunks.append(chunk)

        return chunks

class WelfareEmbedder:
    """임베딩 생성기"""
    
    def __init__(self):
        self.model_name = OPENAI_EMB_MODEL
        self.api_key = get_openai_api_key()
        self.client = None
        
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
        
        # 임베딩 캐시
        self.cache_dir = EMBEDDING_CACHE_DIR
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def embed_text(self, text: str) -> Optional[List[float]]:
        """텍스트 임베딩 생성"""
        if not self.client:
            logger.warning("OpenAI 클라이언트가 초기화되지 않음")
            return None
        
        # 캐시 확인
        cache_key = self._get_cache_key(text)
        cached_embedding = self._load_from_cache(cache_key)
        if cached_embedding is not None:
            return cached_embedding
        
        try:
            response = self.client.embeddings.create(
                model=self.model_name,
                input=text
            )
            embedding = response.data[0].embedding
            
            # 캐시에 저장
            self._save_to_cache(cache_key, embedding)
            
            return embedding
        except Exception as e:
            logger.error(f"임베딩 생성 실패: {e}")
            return None
    
    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """문서 목록 임베딩"""
        embedded_docs = []
        
        for doc in documents:
            embedding = self.embed_text(doc['content'])
            if embedding:
                doc['embedding'] = embedding
                embedded_docs.append(doc)
        
        return embedded_docs
    
    def _get_cache_key(self, text: str) -> str:
        """캐시 키 생성"""
        return hashlib.md5(f"{self.model_name}:{text}".encode()).hexdigest()
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[float]]:
        """캐시에서 로드"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                logger.warning(f"캐시 로드 실패 {cache_key}: {e}")
        return None
    
    def _save_to_cache(self, cache_key: str, embedding: List[float]):
        """캐시에 저장"""
        cache_file = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump(embedding, f)
        except Exception as e:
            logger.warning(f"캐시 저장 실패 {cache_key}: {e}")

class WelfareVectorStore:
    """벡터 저장소"""

    def __init__(self, chroma_db_dir: str = None):
        """
        Args:
            chroma_db_dir: ChromaDB 디렉토리 (예: chroma_db/main 또는 chroma_db/validation)
        """
        self.db_dir = chroma_db_dir if chroma_db_dir else CHROMA_DB_DIR
        self.collection_name = "welfare_documents"
        self.client = None
        self.collection = None

        logger.info(f"WelfareVectorStore 초기화: {self.db_dir}")

        if chromadb:
            self._initialize_chroma()
    
    def _initialize_chroma(self):
        """ChromaDB 초기화 (순수 SQLite 벡터 저장소로 대체)"""
        try:
            # 순수 SQLite로 자체 벡터 DB 구현
            os.makedirs(self.db_dir, exist_ok=True)
            self.db_path = os.path.join(self.db_dir, 'vector_store.db')

            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 테이블 생성
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    content TEXT NOT NULL,
                    metadata TEXT,
                    embedding BLOB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # 인덱스 생성
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_id ON documents(id)')

            conn.commit()
            conn.close()

            logger.info(f"✅ 순수 SQLite 벡터 저장소 초기화: {self.db_path}")
            self.collection = True  # Flag로 사용

        except Exception as e:
            logger.error(f"벡터 저장소 초기화 실패: {e}")
    
    def add_documents(self, documents: List[Dict[str, Any]], embedder: WelfareEmbedder):
        """문서 추가"""
        if not self.collection:
            logger.error("벡터 저장소가 초기화되지 않음")
            return

        logger.info("문서를 벡터 저장소에 추가 중...")

        # 문서 청킹
        all_chunks = []
        # 임시 로더 생성 (청킹은 경로 무관)
        temp_loader = WelfareDocumentLoader()

        for doc in documents:
            chunks = temp_loader.chunk_document(doc)
            all_chunks.extend(chunks)
        
        # 배치 처리
        batch_size = 100
        for i in range(0, len(all_chunks), batch_size):
            batch = all_chunks[i:i + batch_size]
            self._add_batch(batch, embedder)
        
        logger.info(f"총 {len(all_chunks)}개 청크 추가 완료")
    
    def _add_batch(self, batch: List[Dict[str, Any]], embedder: WelfareEmbedder):
        """배치 추가 (순수 SQLite)"""
        import sqlite3
        import json

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for chunk in batch:
                # 고유 ID 생성
                filename = chunk['metadata'].get('filename', 'unknown')
                chunk_id = chunk['metadata'].get('chunk_id', 0)
                content_hash = hashlib.md5(chunk['content'].encode()).hexdigest()[:8]
                unique_id = f"{filename}_{chunk_id}_{content_hash}"

                # 임베딩 생성
                embedding = embedder.embed_text(chunk['content'])
                if not embedding:
                    logger.warning(f"임베딩 생성 실패: {unique_id}")
                    continue

                # 임베딩을 pickle로 직렬화
                embedding_blob = pickle.dumps(embedding)

                # 메타데이터를 JSON으로 직렬화
                metadata_json = json.dumps(chunk['metadata'], ensure_ascii=False)

                # INSERT OR REPLACE
                cursor.execute('''
                    INSERT OR REPLACE INTO documents (id, content, metadata, embedding)
                    VALUES (?, ?, ?, ?)
                ''', (unique_id, chunk['content'], metadata_json, embedding_blob))

            conn.commit()
            conn.close()

        except Exception as e:
            logger.error(f"배치 추가 실패: {e}", exc_info=True)
    
    def similarity_search(self, query: str, embedder: WelfareEmbedder, k: int = 5) -> List[Dict[str, Any]]:
        """유사도 검색 (순수 SQLite 벡터 저장소)"""
        # 쿼리 임베딩
        logger.info(f"🔍 쿼리 임베딩 생성 중: '{query}'")
        query_embedding = embedder.embed_text(query)

        if not query_embedding:
            logger.error("❌ 쿼리 임베딩 생성 실패")
            return []

        logger.info(f"✅ 쿼리 임베딩 생성 완료 (차원: {len(query_embedding)})")

        try:
            import sqlite3
            import json
            import numpy as np

            logger.info(f"🔎 SQLite에서 데이터 읽기: {self.db_path}")

            if not os.path.exists(self.db_path):
                logger.error(f"❌ SQLite 파일 없음: {self.db_path}")
                return []

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # 모든 문서 가져오기
            cursor.execute("SELECT id, content, metadata, embedding FROM documents")
            rows = cursor.fetchall()
            conn.close()

            logger.info(f"💾 가져온 문서 수: {len(rows)}")

            if not rows:
                logger.warning("⚠️ 문서 데이터 없음")
                return []

            # 코사인 유사도 계산
            query_vec = np.array(query_embedding)
            similarities = []

            for row in rows:
                doc_id, content, metadata_json, embedding_blob = row

                if embedding_blob:
                    try:
                        # pickle에서 임베딩 복원
                        doc_embedding = pickle.loads(embedding_blob)
                        doc_vec = np.array(doc_embedding)

                        # 코사인 유사도
                        cosine_sim = np.dot(query_vec, doc_vec) / (
                            np.linalg.norm(query_vec) * np.linalg.norm(doc_vec)
                        )

                        # 메타데이터 파싱
                        try:
                            metadata = json.loads(metadata_json) if metadata_json else {}
                        except:
                            metadata = {}

                        similarities.append({
                            'content': content if content else '',
                            'metadata': metadata,
                            'distance': 1.0 - cosine_sim,
                            'similarity': cosine_sim
                        })
                    except Exception as parse_error:
                        logger.warning(f"임베딩 파싱 실패 ({doc_id}): {parse_error}")
                        continue

            # 유사도순 정렬
            similarities.sort(key=lambda x: x['similarity'], reverse=True)

            # 상위 k개
            top_results = similarities[:k]

            logger.info(f"📊 검색 결과: {len(top_results)}개")

            # 상위 3개 로깅
            for i, result in enumerate(top_results[:3]):
                filename = result['metadata'].get('filename', 'unknown')
                region = result['metadata'].get('region', 'unknown')
                sim = result['similarity']
                logger.info(f"  결과 {i+1}: {filename} (지역: {region}, 유사도: {sim:.4f})")

            logger.info(f"✅ 총 {len(top_results)}개 문서 반환")
            return top_results

        except Exception as e:
            logger.error(f"❌ 유사도 검색 실패: {e}", exc_info=True)
            return []
    
    def get_document_count(self) -> int:
        """저장된 문서 수 반환"""
        try:
            if not os.path.exists(self.db_path):
                return 0

            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM documents")
            count = cursor.fetchone()[0]
            conn.close()
            return count
        except:
            return 0


class DataProcessor:
    """데이터 프로세서 - 전체 파이프라인 관리"""

    def __init__(self, data_dir: str, chroma_db_dir: str = None):
        """
        Args:
            data_dir: 데이터 디렉토리 (예: data/복지로 또는 data/복지로 - 복사본)
            chroma_db_dir: ChromaDB 디렉토리 (예: chroma_db/main 또는 chroma_db/validation)
        """
        self.data_dir = data_dir
        self.loader = WelfareDocumentLoader(welfare_dir=data_dir)  # 경로 전달
        self.embedder = WelfareEmbedder()
        self.vector_store = WelfareVectorStore(chroma_db_dir=chroma_db_dir)  # ChromaDB 경로 전달

        logger.info(f"DataProcessor initialized with data_dir: {data_dir}, chroma_db_dir: {chroma_db_dir}")

    def build_vector_store(self) -> Dict[str, Any]:
        """벡터 스토어 구축"""
        logger.info("=== 벡터 스토어 구축 시작 ===")

        # 문서 로드
        documents = self.loader.load_welfare_documents()
        if not documents:
            logger.error("문서를 로드하지 못했습니다")
            return {
                "status": "error",
                "message": "문서 로드 실패"
            }

        logger.info(f"총 {len(documents)}개 문서 로드 완료")

        # 벡터 스토어에 추가
        self.vector_store.add_documents(documents, self.embedder)

        final_count = self.vector_store.get_document_count()
        logger.info(f"=== 벡터 스토어 구축 완료: {final_count}개 청크 ===")

        return {
            "status": "success",
            "documents_loaded": len(documents),
            "chunks_created": final_count,
            "message": "데이터베이스 구축 완료"
        }