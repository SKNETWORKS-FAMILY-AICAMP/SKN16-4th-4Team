from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings


class DocumentEmbedder:
    """문서를 청킹하고 임베딩하는 클래스"""

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Args:
            chunk_size: 청크 크기 (기본 1000자)
            chunk_overlap: 청크 간 겹침 크기 (기본 200자)
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # 텍스트 분할기 초기화
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        # 한국어 지원 임베딩 모델 초기화
        self.embeddings = HuggingFaceEmbeddings(
            model_name="jhgan/ko-sroberta-multitask",
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )

    def chunk_documents(self, documents: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        문서들을 청크로 분할

        Args:
            documents: 로드된 문서 리스트

        Returns:
            청크 리스트 (각 청크는 메타데이터 포함)
        """
        chunks = []

        for doc in documents:
            # 텍스트 분할
            text_chunks = self.text_splitter.split_text(doc["content"])

            # 각 청크에 메타데이터 추가
            for i, chunk in enumerate(text_chunks):
                chunks.append({
                    "text": chunk,
                    "file_path": doc["file_path"],
                    "file_name": doc["file_name"],
                    "file_type": doc["file_type"],
                    "chunk_index": i,
                    "total_chunks": len(text_chunks)
                })

        print(f"\n총 {len(chunks)}개의 청크로 분할되었습니다.")
        return chunks

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        텍스트 리스트를 임베딩 벡터로 변환

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            임베딩 벡터 리스트
        """
        return self.embeddings.embed_documents(texts)

    def embed_query(self, query: str) -> List[float]:
        """
        쿼리 텍스트를 임베딩 벡터로 변환

        Args:
            query: 임베딩할 쿼리 텍스트

        Returns:
            임베딩 벡터
        """
        return self.embeddings.embed_query(query)


if __name__ == "__main__":
    # 테스트
    from loader import DocumentLoader

    loader = DocumentLoader("data")
    docs = loader.load_all_documents()

    embedder = DocumentEmbedder(chunk_size=500, chunk_overlap=100)
    chunks = embedder.chunk_documents(docs)

    print(f"\n처음 3개 청크:")
    for chunk in chunks[:3]:
        print(f"\n파일: {chunk['file_name']}")
        print(f"청크 인덱스: {chunk['chunk_index']}/{chunk['total_chunks']}")
        print(f"텍스트 미리보기: {chunk['text'][:200]}...")

    # 임베딩 테스트
    print("\n임베딩 테스트...")
    sample_embedding = embedder.embed_query("노인 복지 정책")
    print(f"임베딩 벡터 차원: {len(sample_embedding)}")
