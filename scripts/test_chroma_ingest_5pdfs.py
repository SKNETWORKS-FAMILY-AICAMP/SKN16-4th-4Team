#!/usr/bin/env python3
"""
Test script: ingest up to N PDF files (default 5) into ChromaDB and run a sample similarity query.

Usage:
  - Ensure dependencies installed (see README or requirements.txt). Recommended packages:
    pip install langchain langchain-community chromadb langchain-openai openai scikit-learn python-dotenv

  - Prepare .env with OPENAI_API_KEY if using OpenAI embeddings, or set EMBEDDING_PROVIDER=huggingface

  Run (Windows cmd example):
    set OPENAI_API_KEY=sk-xxxx
    set EMBEDDING_PROVIDER=openai
    python scripts\test_chroma_ingest_5pdfs.py --data-dir data\복지로 --max-pdfs 5

This script is intentionally simple for quick local validation.
"""

from pathlib import Path
import os
import argparse
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger('test_ingest')

# Prevent Chroma telemetry capture errors (some chroma versions call telemetry capture with unexpected args).
# Set env vars to disable Chroma telemetry. These are safe and non-destructive.
os.environ.setdefault('CHROMA_TELEMETRY', 'false')
os.environ.setdefault('CHROMA_TELEMETRY_ENABLED', 'false')
os.environ.setdefault('CHROMA_ANONYMIZED_TELEMETRY', 'false')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=str, default=None, help='Path to directory containing PDFs (default: data/복지로)')
    parser.add_argument('--max-pdfs', type=int, default=5, help='Maximum number of PDF files to ingest')
    parser.add_argument('--persist-dir', type=str, default=None, help='Chroma persist directory (default: chromadb_test_5)')
    parser.add_argument('--query', type=str, default='기초연금 신청', help='Sample query for similarity search')
    parser.add_argument('--by-region', action='store_true', help='Group documents by region and ingest per-region to avoid large requests')
    parser.add_argument('--batch-size', type=int, default=50, help='Number of chunks per embedding batch')
    args = parser.parse_args()

    # Resolve directories
    base_dir = Path(__file__).resolve().parents[1]
    if args.data_dir:
        data_dir = Path(args.data_dir)
    else:
        data_dir = base_dir / 'data' / '복지로'

    if args.persist_dir:
        chroma_dir = Path(args.persist_dir)
    else:
        chroma_dir = base_dir / 'chromadb_test_5'

    logger.info(f'Data dir: {data_dir}')
    logger.info(f'Chroma persist dir: {chroma_dir}')

    if not data_dir.exists():
        logger.error('Data directory does not exist. Place test PDFs under the directory or pass --data-dir')
        return 2

    # find pdfs
    pdf_files = sorted([p for p in data_dir.rglob('*.pdf')])[: args.max_pdfs]
    if not pdf_files:
        logger.error('No PDF files found in data directory')
        return 3

    logger.info(f'Using {len(pdf_files)} PDF files for ingestion')

    # import heavy deps lazily
    try:
        from langchain_community.document_loaders import PyPDFLoader
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        from langchain_community.vectorstores import Chroma
    except Exception as e:
        logger.error(f'Missing dependencies for loaders/vectorstore: {e}')
        logger.error('Install required packages: pip install langchain langchain-community chromadb pypdf')
        return 4

    # choose embeddings
    embedding_provider = os.getenv('EMBEDDING_PROVIDER', os.getenv('EMBEDDING_PROVIDER', 'openai'))
    embedding_model = os.getenv('EMBEDDING_MODEL', os.getenv('OPENAI_EMB_MODEL', 'text-embedding-3-small'))

    embeddings = None
    if embedding_provider == 'openai':
        try:
            from langchain_openai import OpenAIEmbeddings
            openai_key = os.getenv('OPENAI_API_KEY')
            if not openai_key:
                logger.error('OPENAI_API_KEY not set in environment; cannot use OpenAI embeddings')
                return 5
            embeddings = OpenAIEmbeddings(model=embedding_model, openai_api_key=openai_key)
            logger.info(f'Using OpenAI embeddings: {embedding_model}')
        except Exception as e:
            logger.warning(f'langchain_openai not available or failed: {e} -- falling back to HuggingFace')

    if embeddings is None:
        try:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            hf_model = embedding_model if embedding_model else 'sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2'
            embeddings = HuggingFaceEmbeddings(model_name=hf_model, model_kwargs={'device': 'cpu'})
            logger.info(f'Using HuggingFace embeddings: {hf_model}')
        except Exception as e:
            logger.error(f'Failed to initialize HuggingFace embeddings: {e}')
            return 6

    # load and split documents
    all_docs = []
    for pdf in pdf_files:
        try:
            loader = PyPDFLoader(str(pdf))
            docs = loader.load()
            # attach source metadata
            for d in docs:
                d.metadata['source'] = str(pdf.relative_to(data_dir))
            all_docs.extend(docs)
            logger.info(f'Loaded {len(docs)} pages from {pdf.name}')
        except Exception as e:
            logger.warning(f'Failed to load {pdf.name}: {e}')

    if not all_docs:
        logger.error('No document pages loaded successfully')
        return 7

    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_documents(all_docs)
    logger.info(f'Created {len(chunks)} text chunks')

    # prepare chroma directory
    chroma_dir.mkdir(parents=True, exist_ok=True)

    # create or load vectorstore (we will add documents in batches)
    try:
        vectorstore = Chroma(persist_directory=str(chroma_dir), embedding_function=embeddings, collection_name='test_5_docs')
        logger.info('Vector store opened (will add documents in batches)')
    except Exception as e:
        logger.error(f'Failed to open/create vectorstore: {e}')
        return 8

    # Helper: add a list of Document objects in batches
    def add_in_batches(docs_list, batch_size=50):
        total = len(docs_list)
        for i in range(0, total, batch_size):
            batch = docs_list[i:i+batch_size]
            try:
                vectorstore.add_documents(batch)
            except Exception as e:
                logger.error(f'Failed to add batch (items {i}-{i+len(batch)-1}): {e}')
                raise

    # Ingest: by-region or global batching
    try:
        if args.by_region:
            # group chunks by metadata.region
            regions = {}
            for c in chunks:
                region = c.metadata.get('region', 'unknown')
                regions.setdefault(region, []).append(c)

            logger.info(f'Found {len(regions)} regions: {list(regions.keys())}')
            for region, region_chunks in regions.items():
                logger.info(f'Ingesting region "{region}" with {len(region_chunks)} chunks')
                add_in_batches(region_chunks, batch_size=args.batch_size)
                # persist after each region
                try:
                    vectorstore.persist()
                except Exception:
                    pass
        else:
            # global batching
            logger.info(f'Ingesting all chunks in global batches of {args.batch_size}')
            add_in_batches(chunks, batch_size=args.batch_size)
            try:
                vectorstore.persist()
            except Exception:
                pass
        logger.info('Vector store created and persisted (batches)')
    except Exception as e:
        logger.error(f'Failed during batched ingestion: {e}')
        return 9

    # verify count
    try:
        count = vectorstore._collection.count()
        logger.info(f'Vector store contains {count} embeddings')
    except Exception as e:
        logger.warning(f'Could not verify collection count: {e}')

    # sample query
    try:
        results = vectorstore.similarity_search(args.query, k=3)
        logger.info(f'Sample query "{args.query}" returned {len(results)} hits')
        for i, r in enumerate(results, 1):
            print('---')
            print(f'Hit {i}:')
            print(f'Source: {r.metadata.get("source")}')
            print(r.page_content[:400].replace('\n', ' '))
    except Exception as e:
        logger.warning(f'Sample query failed: {e}')

    logger.info('Test ingestion complete')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
