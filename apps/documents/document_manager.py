"""
문서 관리 시스템 - ChromaDB 자동 동기화
"""

from pathlib import Path
from typing import List, Dict
from .loader import DocumentLoader
from .embedder import DocumentEmbedder
from .vectorstore import VectorStore


class DocumentManager:
    """문서 추가/수정/삭제 및 ChromaDB 동기화 관리"""

    def __init__(self):
        self.loader = DocumentLoader(".", use_ocr=False)
        self.embedder = DocumentEmbedder()
        self.vectorstore = VectorStore()

    def process_document(self, file_path: str, doc_id: str, metadata: Dict = None) -> Dict:
        """
        문서 처리 및 ChromaDB에 추가

        Args:
            file_path: 문서 파일 경로
            doc_id: 문서 고유 ID (Document 모델의 ID)
            metadata: 추가 메타데이터

        Returns:
            처리 결과 (chunk_count, success)
        """
        try:
            # 1. 파일 타입 확인
            file_ext = Path(file_path).suffix.lower()

            # 2. 텍스트 추출
            if file_ext == '.pdf':
                text = self.loader.load_pdf(file_path)
            elif file_ext in ['.hwp']:
                text = self.loader.load_hwp(file_path)
            elif file_ext in ['.hwpx']:
                text = self.loader.load_hwpx(file_path)
            else:
                return {'success': False, 'error': f'지원하지 않는 파일 형식: {file_ext}'}

            if not text or len(text.strip()) < 10:
                return {'success': False, 'error': '텍스트를 추출할 수 없습니다.'}

            # 3. 문서 청킹
            doc_data = {
                'file_path': file_path,
                'file_name': Path(file_path).name,
                'content': text,
                'file_type': file_ext[1:]  # . 제거
            }

            if metadata:
                doc_data.update(metadata)

            chunks = self.embedder.chunk_documents([doc_data])

            # 4. 임베딩 생성
            embeddings = self.embedder.embed_texts([chunk["text"] for chunk in chunks])

            # 5. ChromaDB에 추가 (문서 ID를 prefix로 사용)
            ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]

            # 메타데이터에 document_id 추가
            for chunk in chunks:
                chunk['document_id'] = str(doc_id)

            # 기존 청크 삭제 (업데이트인 경우)
            try:
                self.delete_document_from_vectorstore(doc_id)
            except:
                pass  # 없으면 무시

            # 새로운 청크 추가
            self.vectorstore.collection.add(
                ids=ids,
                documents=[chunk["text"] for chunk in chunks],
                embeddings=embeddings,
                metadatas=[{
                    "file_path": chunk["file_path"],
                    "file_name": chunk["file_name"],
                    "file_type": chunk["file_type"],
                    "document_id": chunk['document_id'],
                    "chunk_index": chunk["chunk_index"],
                } for chunk in chunks]
            )

            return {
                'success': True,
                'chunk_count': len(chunks),
                'extracted_text': text[:1000]  # 처음 1000자만 저장
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def delete_document_from_vectorstore(self, doc_id: str):
        """
        ChromaDB에서 특정 문서의 모든 청크 삭제

        Args:
            doc_id: 문서 ID
        """
        try:
            # document_id가 일치하는 모든 청크 검색
            results = self.vectorstore.collection.get(
                where={"document_id": str(doc_id)}
            )

            if results and results['ids']:
                # 해당 청크들 삭제
                self.vectorstore.collection.delete(ids=results['ids'])
                print(f"문서 {doc_id}의 {len(results['ids'])}개 청크를 삭제했습니다.")
                return len(results['ids'])

            return 0
        except Exception as e:
            print(f"문서 삭제 오류: {e}")
            raise

    def sync_all_documents(self, documents: List[Dict]) -> Dict:
        """
        여러 문서를 일괄 동기화

        Args:
            documents: [{id, file_path, metadata}, ...]

        Returns:
            동기화 결과 통계
        """
        success_count = 0
        fail_count = 0
        total_chunks = 0

        for doc in documents:
            result = self.process_document(
                file_path=doc['file_path'],
                doc_id=doc['id'],
                metadata=doc.get('metadata', {})
            )

            if result['success']:
                success_count += 1
                total_chunks += result['chunk_count']
            else:
                fail_count += 1
                print(f"실패: {doc['file_path']} - {result.get('error')}")

        return {
            'success_count': success_count,
            'fail_count': fail_count,
            'total_chunks': total_chunks
        }
