import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
import os


class VectorStore:
    """ChromaDB를 사용한 벡터 저장소 클래스"""

    def __init__(self, collection_name: str = "elderly_policy_docs", persist_directory: str = "./chroma_db"):
        """
        Args:
            collection_name: 컬렉션 이름
            persist_directory: ChromaDB 저장 디렉토리
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory

        # ChromaDB 클라이언트 초기화
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )

        # 컬렉션 가져오기 또는 생성
        try:
            self.collection = self.client.get_collection(name=collection_name)
            print(f"기존 컬렉션 '{collection_name}'을 불러왔습니다.")
        except:
            self.collection = self.client.create_collection(
                name=collection_name,
                metadata={"description": "노인 정책 문서 벡터 저장소"}
            )
            print(f"새 컬렉션 '{collection_name}'을 생성했습니다.")

    def add_documents(self, chunks: List[Dict[str, str]], embeddings: List[List[float]]):
        """
        문서 청크와 임베딩을 벡터 저장소에 추가

        Args:
            chunks: 청크 리스트 (메타데이터 포함)
            embeddings: 임베딩 벡터 리스트
        """
        # ID 생성
        ids = [f"{chunk['file_name']}_{chunk['chunk_index']}" for chunk in chunks]

        # 텍스트 추출
        documents = [chunk["text"] for chunk in chunks]

        # 메타데이터 추출
        metadatas = [
            {
                "file_path": chunk["file_path"],
                "file_name": chunk["file_name"],
                "file_type": chunk["file_type"],
                "chunk_index": chunk["chunk_index"],
                "total_chunks": chunk["total_chunks"]
            }
            for chunk in chunks
        ]

        # 배치 단위로 추가 (ChromaDB는 한 번에 너무 많은 문서를 추가하면 오류 발생)
        batch_size = 100
        for i in range(0, len(documents), batch_size):
            end_idx = min(i + batch_size, len(documents))

            self.collection.add(
                ids=ids[i:end_idx],
                documents=documents[i:end_idx],
                embeddings=embeddings[i:end_idx],
                metadatas=metadatas[i:end_idx]
            )

            print(f"추가됨: {end_idx}/{len(documents)} 청크")

        print(f"\n총 {len(documents)}개의 청크를 벡터 저장소에 추가했습니다.")

    def search(
        self,
        query_embedding: List[float],
        n_results: int = 5,
        filter_dict: Optional[Dict] = None
    ) -> Dict:
        """
        쿼리 임베딩과 유사한 문서 검색

        Args:
            query_embedding: 쿼리 임베딩 벡터
            n_results: 반환할 결과 수
            filter_dict: 메타데이터 필터

        Returns:
            검색 결과 (documents, metadatas, distances)
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter_dict
        )

        return {
            "documents": results["documents"][0],
            "metadatas": results["metadatas"][0],
            "distances": results["distances"][0]
        }

    def count(self) -> int:
        """저장된 문서 수 반환"""
        return self.collection.count()

    def delete_collection(self):
        """컬렉션 삭제"""
        self.client.delete_collection(name=self.collection_name)
        print(f"컬렉션 '{self.collection_name}'이 삭제되었습니다.")


class RAGSystem:
    """RAG (Retrieval-Augmented Generation) 시스템"""

    def __init__(self, vectorstore: VectorStore, embedder):
        """
        Args:
            vectorstore: 벡터 저장소 인스턴스
            embedder: 임베더 인스턴스
        """
        self.vectorstore = vectorstore
        self.embedder = embedder

    def retrieve_relevant_docs(self, query: str, n_results: int = 5, user_profile: Optional[Dict] = None) -> List[Dict]:
        """
        쿼리에 관련된 문서 검색

        Args:
            query: 사용자 쿼리
            n_results: 반환할 결과 수
            user_profile: 사용자 프로필 (지역, 나이, 성별 등)

        Returns:
            관련 문서 리스트
        """
        # 사용자 프로필 정보를 쿼리에 추가
        enhanced_query = query
        if user_profile:
            profile_info = []
            if user_profile.get("region"):
                profile_info.append(f"지역: {user_profile['region']}")
            if user_profile.get("age"):
                profile_info.append(f"나이: {user_profile['age']}세")
            if user_profile.get("gender"):
                profile_info.append(f"성별: {user_profile['gender']}")

            if profile_info:
                enhanced_query = f"{query}\n사용자 정보: {', '.join(profile_info)}"

        # 쿼리 임베딩
        query_embedding = self.embedder.embed_query(enhanced_query)

        # 벡터 저장소에서 검색
        results = self.vectorstore.search(query_embedding, n_results=n_results)

        # 결과 포맷팅
        relevant_docs = []
        for i, (doc, metadata, distance) in enumerate(zip(
            results["documents"],
            results["metadatas"],
            results["distances"]
        )):
            relevant_docs.append({
                "rank": i + 1,
                "content": doc,
                "file_name": metadata["file_name"],
                "file_type": metadata["file_type"],
                "similarity_score": 1 - distance  # 거리를 유사도로 변환
            })

        return relevant_docs


if __name__ == "__main__":
    # 테스트
    from loader import DocumentLoader
    from embedder import DocumentEmbedder

    # 문서 로드
    loader = DocumentLoader("data")
    docs = loader.load_all_documents()

    # 임베딩
    embedder = DocumentEmbedder()
    chunks = embedder.chunk_documents(docs)
    embeddings = embedder.embed_texts([chunk["text"] for chunk in chunks])

    # 벡터 저장소에 추가
    vectorstore = VectorStore()
    vectorstore.add_documents(chunks, embeddings)

    # RAG 시스템 테스트
    rag = RAGSystem(vectorstore, embedder)
    results = rag.retrieve_relevant_docs("기초연금 신청 방법", n_results=3)

    print("\n검색 결과:")
    for result in results:
        print(f"\n순위: {result['rank']}")
        print(f"파일: {result['file_name']}")
        print(f"유사도: {result['similarity_score']:.4f}")
        print(f"내용: {result['content'][:200]}...")
