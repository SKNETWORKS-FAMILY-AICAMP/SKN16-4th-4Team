"""
노인 정책 안내 챗봇 - 설정 스크립트
이 스크립트는 문서 로드, 임베딩, ChromaDB 저장을 수행합니다.
"""

import os
import sys
from pathlib import Path

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'elderly_policy.settings')

import django
django.setup()

from documents.loader import DocumentLoader
from documents.embedder import DocumentEmbedder
from documents.vectorstore import VectorStore


def main():
    print("=" * 60)
    print("노인 정책 안내 챗봇 - 초기 설정")
    print("=" * 60)

    # OCR 사용 여부 확인
    use_ocr = input("\nOCR을 사용하시겠습니까? (이미지 PDF 처리 가능, 시간 오래 걸림) (y/n): ").lower() == 'y'

    # 1. 문서 로드
    print("\n[1/3] 문서 로딩 중...")
    data_dir = Path("data")
    if not data_dir.exists():
        print("오류: data 폴더가 존재하지 않습니다.")
        return

    loader = DocumentLoader(str(data_dir), use_ocr=use_ocr)
    documents = loader.load_all_documents()

    if not documents:
        print("오류: 로드된 문서가 없습니다.")
        return

    print(f"✓ {len(documents)}개의 문서를 로드했습니다.")

    # 2. 임베딩 및 청킹
    print("\n[2/3] 문서 청킹 및 임베딩 중...")
    embedder = DocumentEmbedder(chunk_size=1000, chunk_overlap=200)
    chunks = embedder.chunk_documents(documents)

    print(f"✓ {len(chunks)}개의 청크로 분할되었습니다.")

    print("임베딩 생성 중... (시간이 걸릴 수 있습니다)")
    embeddings = embedder.embed_texts([chunk["text"] for chunk in chunks])

    print(f"✓ 임베딩 생성 완료 (차원: {len(embeddings[0])})")

    # 3. ChromaDB에 저장
    print("\n[3/3] ChromaDB에 저장 중...")
    vectorstore = VectorStore()

    # 기존 데이터 확인
    existing_count = vectorstore.count()
    if existing_count > 0:
        response = input(f"\n기존 데이터 {existing_count}개가 있습니다. 삭제하고 다시 저장하시겠습니까? (y/n): ")
        if response.lower() == 'y':
            vectorstore.delete_collection()
            vectorstore = VectorStore()

    vectorstore.add_documents(chunks, embeddings)

    print("\n" + "=" * 60)
    print("✓ 설정 완료!")
    print("=" * 60)
    print("\n이제 Django 서버를 실행하세요:")
    print("  python manage.py migrate")
    print("  python manage.py createsuperuser")
    print("  python manage.py runserver")


if __name__ == "__main__":
    main()
