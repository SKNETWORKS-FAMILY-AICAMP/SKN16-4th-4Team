# =========================================
# 🗄️ ChromaDB 벡터스토어 모듈
# =========================================

import os
import uuid
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime
import pandas as pd
import numpy as np

# ChromaDB 임포트
try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

# LangChain 임포트 (선택적)
try:
    from langchain_community.vectorstores import Chroma
    from langchain.schema import Document
    LANGCHAIN_CHROMA_AVAILABLE = True
except ImportError:
    LANGCHAIN_CHROMA_AVAILABLE = False

logger = logging.getLogger(__name__)


class WelfareVectorStore:
    """노인복지 정책 전용 ChromaDB 벡터스토어"""
    
    def __init__(self, 
                 collection_name: str = "elderly_welfare_policies",
                 persist_directory: str = None,
                 embedding_function=None):
        """
        Args:
            collection_name: 컬렉션 이름
            persist_directory: 데이터 저장 디렉토리
            embedding_function: 임베딩 함수
        """
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB가 설치되지 않았습니다. pip install chromadb")
        
        self.collection_name = collection_name
        self.persist_directory = persist_directory or "./chroma_db"
        self.embedding_function = embedding_function
        
        # ChromaDB 클라이언트 설정
        self.client = None
        self.collection = None
        
        # 메타데이터 관리
        self.document_metadata = {}
        
        # 초기화
        self._initialize_client()
    
    def _initialize_client(self):
        """ChromaDB 클라이언트 초기화"""
        try:
            # 저장 디렉토리 생성
            os.makedirs(self.persist_directory, exist_ok=True)
            
            # ChromaDB 클라이언트 생성
            self.client = chromadb.PersistentClient(path=self.persist_directory)
            
            # 컬렉션 생성 또는 로드
            try:
                self.collection = self.client.get_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function
                )
                logger.info(f"기존 컬렉션 로드: {self.collection_name}")
            except Exception:
                # 컬렉션이 존재하지 않으면 새로 생성
                self.collection = self.client.create_collection(
                    name=self.collection_name,
                    embedding_function=self.embedding_function,
                    metadata={"description": "노인복지 정책 문서 컬렉션"}
                )
                logger.info(f"새 컬렉션 생성: {self.collection_name}")
            
            # 기존 메타데이터 로드
            self._load_metadata()
            
        except Exception as e:
            logger.error(f"ChromaDB 초기화 실패: {e}")
            raise
    
    def _load_metadata(self):
        """저장된 메타데이터 로드"""
        metadata_path = Path(self.persist_directory) / "document_metadata.json"
        
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    self.document_metadata = json.load(f)
                logger.info(f"메타데이터 로드 완료: {len(self.document_metadata)}개 문서")
            except Exception as e:
                logger.warning(f"메타데이터 로드 실패: {e}")
                self.document_metadata = {}
        else:
            self.document_metadata = {}
    
    def _save_metadata(self):
        """메타데이터 저장"""
        metadata_path = Path(self.persist_directory) / "document_metadata.json"
        
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(self.document_metadata, f, ensure_ascii=False, indent=2)
            logger.debug("메타데이터 저장 완료")
        except Exception as e:
            logger.warning(f"메타데이터 저장 실패: {e}")
    
    def add_documents(self, 
                     texts: List[str], 
                     metadatas: List[Dict] = None,
                     embeddings: List[List[float]] = None,
                     ids: List[str] = None) -> List[str]:
        """문서들을 벡터스토어에 추가"""
        
        if not texts:
            logger.warning("추가할 텍스트가 없습니다.")
            return []
        
        # ID 생성
        if ids is None:
            ids = [str(uuid.uuid4()) for _ in texts]
        
        # 메타데이터 기본값 설정
        if metadatas is None:
            metadatas = [{} for _ in texts]
        
        # 메타데이터에 추가 정보 포함
        enhanced_metadatas = []
        for i, metadata in enumerate(metadatas):
            enhanced_metadata = {
                **metadata,
                "document_id": ids[i],
                "text_length": len(texts[i]),
                "created_at": datetime.now().isoformat(),
                "collection": self.collection_name
            }
            
            # 복지 정책 관련 분류
            enhanced_metadata.update(self._classify_welfare_document(texts[i]))
            enhanced_metadatas.append(enhanced_metadata)
        
        try:
            # ChromaDB에 문서 추가
            if embeddings is not None:
                self.collection.add(
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=enhanced_metadatas,
                    ids=ids
                )
            else:
                self.collection.add(
                    documents=texts,
                    metadatas=enhanced_metadatas,
                    ids=ids
                )
            
            # 로컬 메타데이터 업데이트
            for i, doc_id in enumerate(ids):
                self.document_metadata[doc_id] = {
                    "text": texts[i],
                    "metadata": enhanced_metadatas[i]
                }
            
            self._save_metadata()
            
            logger.info(f"{len(texts)}개 문서 추가 완료")
            return ids
            
        except Exception as e:
            logger.error(f"문서 추가 실패: {e}")
            raise
    
    def _classify_welfare_document(self, text: str) -> Dict[str, Any]:
        """복지 문서 자동 분류"""
        classification = {
            "welfare_category": "기타",
            "target_age": None,
            "support_type": [],
            "keywords": []
        }
        
        text_lower = text.lower()
        
        # 복지 카테고리 분류
        if any(keyword in text for keyword in ["의료", "건강", "치료", "진료"]):
            classification["welfare_category"] = "의료지원"
        elif any(keyword in text for keyword in ["돌봄", "간병", "요양", "케어"]):
            classification["welfare_category"] = "돌봄서비스"
        elif any(keyword in text for keyword in ["생활비", "수당", "연금", "급여"]):
            classification["welfare_category"] = "생활지원"
        elif any(keyword in text for keyword in ["주거", "임대", "주택", "거주"]):
            classification["welfare_category"] = "주거지원"
        elif any(keyword in text for keyword in ["교통", "이동", "차량", "버스"]):
            classification["welfare_category"] = "교통지원"
        
        # 대상 연령 추출
        import re
        age_patterns = [
            r'(\d+)세 이상',
            r'만\s*(\d+)세',
            r'(\d+)세 노인'
        ]
        
        for pattern in age_patterns:
            match = re.search(pattern, text)
            if match:
                classification["target_age"] = int(match.group(1))
                break
        
        # 지원 유형
        support_types = []
        if "신청" in text:
            support_types.append("신청필요")
        if any(word in text for word in ["무료", "지원", "급여"]):
            support_types.append("정부지원")
        if "소득" in text or "기초생활" in text:
            support_types.append("소득기반")
        
        classification["support_type"] = support_types
        
        # 주요 키워드 추출
        welfare_keywords = [
            "노인", "어르신", "고령자", "복지", "지원", "혜택",
            "의료비", "간병", "요양", "돌봄", "생활지원", "수당"
        ]
        
        found_keywords = [kw for kw in welfare_keywords if kw in text]
        classification["keywords"] = found_keywords
        
        return classification
    
    def similarity_search(self, 
                         query: str, 
                         k: int = 5,
                         filter_dict: Dict = None,
                         include_embeddings: bool = False) -> List[Dict]:
        """유사도 검색"""
        try:
            # 검색 수행
            results = self.collection.query(
                query_texts=[query],
                n_results=k,
                where=filter_dict,
                include=["documents", "metadatas", "distances"] + 
                       (["embeddings"] if include_embeddings else [])
            )
            
            # 결과 포맷팅
            formatted_results = []
            for i in range(len(results['documents'][0])):
                result = {
                    'document': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i],
                    'distance': results['distances'][0][i],
                    'similarity_score': 1 - results['distances'][0][i]  # 거리를 유사도로 변환
                }
                
                if include_embeddings and 'embeddings' in results:
                    result['embedding'] = results['embeddings'][0][i]
                
                formatted_results.append(result)
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"유사도 검색 실패: {e}")
            return []
    
    def search_by_metadata(self, 
                          filter_dict: Dict, 
                          limit: int = 10) -> List[Dict]:
        """메타데이터 기반 검색"""
        try:
            results = self.collection.get(
                where=filter_dict,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            formatted_results = []
            for i in range(len(results['documents'])):
                formatted_results.append({
                    'document': results['documents'][i],
                    'metadata': results['metadatas'][i],
                    'id': results['ids'][i]
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"메타데이터 검색 실패: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """컬렉션 통계 정보"""
        try:
            count = self.collection.count()
            
            # 카테고리별 통계
            category_stats = {}
            support_type_stats = {}
            region_stats = {}
            
            # 전체 문서 조회 (샘플링)
            sample_size = min(1000, count)
            if count > 0:
                results = self.collection.get(
                    limit=sample_size,
                    include=["metadatas"]
                )
                
                for metadata in results['metadatas']:
                    # 카테고리 통계
                    category = metadata.get('welfare_category', '기타')
                    category_stats[category] = category_stats.get(category, 0) + 1
                    
                    # 지원 유형 통계
                    support_types = metadata.get('support_type', [])
                    for support_type in support_types:
                        support_type_stats[support_type] = support_type_stats.get(support_type, 0) + 1
                    
                    # 지역 통계
                    region = metadata.get('region', '전국')
                    region_stats[region] = region_stats.get(region, 0) + 1
            
            return {
                'total_documents': count,
                'collection_name': self.collection_name,
                'category_distribution': category_stats,
                'support_type_distribution': support_type_stats,
                'region_distribution': region_stats,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"통계 조회 실패: {e}")
            return {}
    
    def delete_documents(self, ids: List[str]) -> bool:
        """문서 삭제"""
        try:
            self.collection.delete(ids=ids)
            
            # 로컬 메타데이터에서도 삭제
            for doc_id in ids:
                if doc_id in self.document_metadata:
                    del self.document_metadata[doc_id]
            
            self._save_metadata()
            
            logger.info(f"{len(ids)}개 문서 삭제 완료")
            return True
            
        except Exception as e:
            logger.error(f"문서 삭제 실패: {e}")
            return False
    
    def update_document(self, doc_id: str, text: str = None, metadata: Dict = None) -> bool:
        """문서 업데이트"""
        try:
            update_data = {"ids": [doc_id]}
            
            if text is not None:
                update_data["documents"] = [text]
                
            if metadata is not None:
                # 메타데이터 업데이트 시 분류 재수행
                if text:
                    metadata.update(self._classify_welfare_document(text))
                metadata["updated_at"] = datetime.now().isoformat()
                update_data["metadatas"] = [metadata]
            
            self.collection.update(**update_data)
            
            # 로컬 메타데이터 업데이트
            if doc_id in self.document_metadata:
                if text is not None:
                    self.document_metadata[doc_id]["text"] = text
                if metadata is not None:
                    self.document_metadata[doc_id]["metadata"].update(metadata)
            
            self._save_metadata()
            
            logger.info(f"문서 업데이트 완료: {doc_id}")
            return True
            
        except Exception as e:
            logger.error(f"문서 업데이트 실패: {e}")
            return False
    
    def export_collection(self, output_path: str = None) -> str:
        """컬렉션 내용을 CSV로 내보내기"""
        if output_path is None:
            output_path = f"{self.collection_name}_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        
        try:
            # 모든 문서 조회
            results = self.collection.get(include=["documents", "metadatas"])
            
            # DataFrame 생성
            data = []
            for i, doc in enumerate(results['documents']):
                metadata = results['metadatas'][i]
                row = {
                    'id': results['ids'][i],
                    'document': doc,
                    'text_length': len(doc),
                    'welfare_category': metadata.get('welfare_category', ''),
                    'target_age': metadata.get('target_age', ''),
                    'support_type': ', '.join(metadata.get('support_type', [])),
                    'keywords': ', '.join(metadata.get('keywords', [])),
                    'region': metadata.get('region', ''),
                    'created_at': metadata.get('created_at', ''),
                    'updated_at': metadata.get('updated_at', '')
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            df.to_csv(output_path, index=False, encoding='utf-8-sig')
            
            logger.info(f"컬렉션 내보내기 완료: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"컬렉션 내보내기 실패: {e}")
            raise
    
    def backup_collection(self, backup_path: str = None) -> str:
        """컬렉션 백업"""
        if backup_path is None:
            backup_path = f"backup_{self.collection_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            import shutil
            
            # 전체 디렉토리 백업
            shutil.copytree(self.persist_directory, backup_path)
            
            logger.info(f"컬렉션 백업 완료: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"컬렉션 백업 실패: {e}")
            raise


class LangChainChromaWrapper:
    """LangChain과 호환되는 ChromaDB 래퍼"""
    
    def __init__(self, welfare_vector_store: WelfareVectorStore, embedding_function):
        """
        Args:
            welfare_vector_store: WelfareVectorStore 인스턴스
            embedding_function: LangChain 임베딩 함수
        """
        if not LANGCHAIN_CHROMA_AVAILABLE:
            logger.warning("LangChain Chroma 지원이 없습니다. 기본 기능만 사용 가능합니다.")
        
        self.welfare_store = welfare_vector_store
        self.embedding_function = embedding_function
        self._langchain_store = None
        
        # LangChain Chroma 초기화 시도
        if LANGCHAIN_CHROMA_AVAILABLE:
            try:
                self._langchain_store = Chroma(
                    collection_name=welfare_vector_store.collection_name,
                    persist_directory=welfare_vector_store.persist_directory,
                    embedding_function=embedding_function
                )
            except Exception as e:
                logger.warning(f"LangChain Chroma 초기화 실패: {e}")
    
    def add_documents(self, documents: List[Document]) -> List[str]:
        """LangChain Document 객체들을 추가"""
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]
        
        return self.welfare_store.add_documents(texts, metadatas)
    
    def similarity_search(self, query: str, k: int = 4, **kwargs) -> List[Document]:
        """LangChain 호환 유사도 검색"""
        results = self.welfare_store.similarity_search(query, k, **kwargs)
        
        documents = []
        for result in results:
            doc = Document(
                page_content=result['document'],
                metadata=result['metadata']
            )
            documents.append(doc)
        
        return documents
    
    def as_retriever(self, **kwargs):
        """LangChain Retriever로 변환"""
        if self._langchain_store:
            return self._langchain_store.as_retriever(**kwargs)
        else:
            # 사용자 정의 리트리버 구현
            from langchain.schema.retriever import BaseRetriever
            
            class CustomWelfareRetriever(BaseRetriever):
                def __init__(self, wrapper):
                    self.wrapper = wrapper
                
                def _get_relevant_documents(self, query: str) -> List[Document]:
                    return self.wrapper.similarity_search(query)
            
            return CustomWelfareRetriever(self)


def main():
    """벡터스토어 테스트"""
    
    # 로깅 설정
    logging.basicConfig(level=logging.INFO)
    
    print("🗄️ ChromaDB 벡터스토어 테스트")
    print("=" * 50)
    
    # 테스트 데이터
    test_documents = [
        {
            "text": "만 65세 이상 노인을 대상으로 의료비를 월 최대 30만원까지 지원합니다.",
            "metadata": {"region": "전국", "file_format": "pdf", "source": "의료비지원안내.pdf"}
        },
        {
            "text": "기초생활수급자 어르신에게 생활비를 월 50만원씩 지원하는 제도입니다.",
            "metadata": {"region": "서울", "file_format": "hwp", "source": "생활비지원.hwp"}
        },
        {
            "text": "요양보호사가 주 3회 방문하여 돌봄서비스를 제공합니다.",
            "metadata": {"region": "부산", "file_format": "pdf", "source": "돌봄서비스.pdf"}
        },
        {
            "text": "치매 어르신을 위한 인지기능 향상 프로그램을 운영합니다.",
            "metadata": {"region": "대구", "file_format": "txt", "source": "치매예방.txt"}
        }
    ]
    
    try:
        # 벡터스토어 초기화
        vector_store = WelfareVectorStore(
            collection_name="test_welfare_collection",
            persist_directory="./test_chroma_db"
        )
        
        print(f"✅ 벡터스토어 초기화 완료")
        
        # 문서 추가
        texts = [doc["text"] for doc in test_documents]
        metadatas = [doc["metadata"] for doc in test_documents]
        
        doc_ids = vector_store.add_documents(texts, metadatas)
        print(f"📝 {len(doc_ids)}개 문서 추가 완료")
        
        # 통계 확인
        stats = vector_store.get_collection_stats()
        print(f"\n📊 컬렉션 통계:")
        print(f"  총 문서 수: {stats['total_documents']}")
        print(f"  카테고리 분포: {stats['category_distribution']}")
        print(f"  지역 분포: {stats['region_distribution']}")
        
        # 유사도 검색 테스트
        print(f"\n🔍 유사도 검색 테스트:")
        query = "노인 의료비 지원"
        results = vector_store.similarity_search(query, k=3)
        
        for i, result in enumerate(results, 1):
            print(f"  [{i}] 유사도: {result['similarity_score']:.3f}")
            print(f"      내용: {result['document'][:50]}...")
            print(f"      카테고리: {result['metadata'].get('welfare_category', 'N/A')}")
        
        # 메타데이터 검색 테스트
        print(f"\n🏷️ 메타데이터 검색 테스트:")
        filter_results = vector_store.search_by_metadata(
            {"welfare_category": "의료지원"}
        )
        
        for result in filter_results:
            print(f"  의료지원 문서: {result['document'][:50]}...")
        
        # 내보내기 테스트
        export_path = vector_store.export_collection("test_export.csv")
        print(f"\n💾 컬렉션 내보내기: {export_path}")
        
        print(f"\n✅ 모든 테스트 완료!")
        
    except Exception as e:
        print(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()