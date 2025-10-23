"""
Django Management Command: Load Welfare Documents into ChromaDB
================================================================
This command loads PDF documents from data/documents/복지로 into ChromaDB vector store
for RAG-based chatbot functionality.

Usage:
    python manage.py load_welfare_documents
    python manage.py load_welfare_documents --clear  # Clear existing data first
"""

import os
import sys
import time
import random
try:
    import tiktoken
    TIKTOKEN_AVAILABLE = True
except Exception:
    TIKTOKEN_AVAILABLE = False
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings


class Command(BaseCommand):
    help = 'Load welfare PDF documents into ChromaDB vector store'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing ChromaDB data before loading',
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            default=None,
            help='Custom data directory path (default: data/documents/복지로)',
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=500,
            help='Chunk size for text splitting (default: 500)',
        )
        parser.add_argument(
            '--chunk-overlap',
            type=int,
            default=50,
            help='Chunk overlap for text splitting (default: 50)',
        )
        parser.add_argument(
            '--by-region',
            action='store_true',
            help='Group documents by region and ingest per-region to avoid large requests',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of chunks per embedding batch (default: 50)',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Starting document loading process...'))

        # Import required libraries
        try:
            from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            from langchain_community.embeddings import HuggingFaceEmbeddings
            from langchain_community.vectorstores import Chroma
        except ImportError as e:
            raise CommandError(
                f'Required libraries not installed: {e}\n'
                'Please install: pip install langchain langchain-community chromadb pypdf sentence-transformers'
            )

        # Determine data directory
        if options['data_dir']:
            data_dir = Path(options['data_dir'])
        else:
            # Check for DATA_DIRECTORY environment variable first
            data_directory = os.getenv('DATA_DIRECTORY')
            if data_directory:
                data_dir = Path(data_directory) / '복지로'
            else:
                data_dir = Path(settings.BASE_DIR) / 'data' / '복지로'

        if not data_dir.exists():
            raise CommandError(f'Data directory not found: {data_dir}')

        self.stdout.write(f'📁 Data directory: {data_dir}')

        # Find all PDF files
        pdf_files = list(data_dir.rglob('*.pdf'))
        if not pdf_files:
            raise CommandError(f'No PDF files found in {data_dir}')

        self.stdout.write(f'📄 Found {len(pdf_files)} PDF files')

        # Load documents
        self.stdout.write('📚 Loading PDF documents...')
        documents = []

        for pdf_file in pdf_files:
            try:
                loader = PyPDFLoader(str(pdf_file))
                docs = loader.load()

                # Add metadata with region information
                for doc in docs:
                    doc.metadata['source'] = str(pdf_file.relative_to(data_dir))
                    # Extract region from path: data/복지로/전북/pdf/filename.pdf -> region='전북'
                    relative_path = pdf_file.relative_to(data_dir)
                    if len(relative_path.parts) >= 2:
                        doc.metadata['region'] = relative_path.parts[0]  # 전북, 대구, 전국 등
                    else:
                        doc.metadata['region'] = 'unknown'

                documents.extend(docs)
                self.stdout.write(f'  ✅ Loaded: {pdf_file.name} ({len(docs)} pages)')
            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️ Failed to load {pdf_file.name}: {e}')
                )

        if not documents:
            raise CommandError('No documents were loaded successfully')

        self.stdout.write(self.style.SUCCESS(f'✅ Loaded {len(documents)} document pages'))

        # Split documents into chunks
        self.stdout.write('✂️  Splitting documents into chunks...')
        # Allow environment variables to override defaults when CLI flags are not provided
        # CLI flags take precedence; we only replace values if the user left the default.
        try:
            # chunk size
            if options.get('chunk_size') == 500:
                env_chunk = os.getenv('CHUNK_SIZE')
                if env_chunk:
                    options['chunk_size'] = int(env_chunk)
            # chunk overlap
            if options.get('chunk_overlap') == 50:
                env_overlap = os.getenv('CHUNK_OVERLAP')
                if env_overlap:
                    options['chunk_overlap'] = int(env_overlap)
            # batch size
            if options.get('batch_size') == 50:
                env_batch = os.getenv('BATCH_SIZE') or os.getenv('RAG_BATCH_SIZE')
                if env_batch:
                    options['batch_size'] = int(env_batch)
            # by-region boolean
            if not options.get('by_region'):
                env_by_region = os.getenv('BY_REGION') or os.getenv('LOAD_BY_REGION')
                if env_by_region and str(env_by_region).lower() in ('1', 'true', 'yes', 'on'):
                    options['by_region'] = True
        except Exception:
            # if any env parse fails, continue with CLI/default values
            pass

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=options['chunk_size'],
            chunk_overlap=options['chunk_overlap'],
            length_function=len,
        )

        chunks = text_splitter.split_documents(documents)
        self.stdout.write(self.style.SUCCESS(f'✅ Created {len(chunks)} text chunks'))

        # --- Token counting and dynamic batch size calculation (tiktoken if available) ---
        def count_tokens_text(text: str) -> int:
            if TIKTOKEN_AVAILABLE:
                try:
                    enc = tiktoken.get_encoding("cl100k_base")
                    return len(enc.encode(text))
                except Exception:
                    pass
            # fallback heuristic: characters / 4
            return max(1, len(text) // 4)

        try:
            sample_n = min(200, len(chunks))
            sample_chunks = chunks[:sample_n]
            sample_tokens = [count_tokens_text(c.page_content) for c in sample_chunks]
            avg_tokens = int(sum(sample_tokens) / len(sample_tokens)) if sample_tokens else 0
        except Exception:
            avg_tokens = 0

        # Read target tokens per request from env, fallback to 80000
        try:
            target_tokens = int(os.getenv('TARGET_TOKENS_PER_REQUEST', '80000'))
        except Exception:
            target_tokens = 80000

        suggested_batch = 50
        if avg_tokens > 0:
            suggested_batch = max(1, int(target_tokens // avg_tokens))

        # If user provided batch size is larger than suggested and it wasn't explicitly set via CLI env, override
        # We assume options['batch_size'] contains final batch size (may have been overridden by env earlier)
        if options.get('batch_size') and options.get('batch_size') > suggested_batch:
            self.stdout.write(self.style.WARNING(f'⚠️ Adjusting batch_size {options.get("batch_size")} -> suggested {suggested_batch} based on avg tokens ({avg_tokens}) and TARGET_TOKENS_PER_REQUEST={target_tokens}'))
            options['batch_size'] = suggested_batch

        # Cost estimate (optional): price per 1k tokens
        try:
            price_per_1k = float(os.getenv('EMBEDDING_PRICE_PER_1K', '0.02'))
        except Exception:
            price_per_1k = 0.02

        try:
            total_chunks = len(chunks)
            estimated_total_tokens = avg_tokens * total_chunks if avg_tokens else 0
            est_cost = estimated_total_tokens / 1000.0 * price_per_1k
            self.stdout.write(self.style.SUCCESS(f'🔢 Token estimate: avg_tokens_per_chunk={avg_tokens}, estimated_total_tokens={estimated_total_tokens}, estimated_cost=${est_cost:.2f}'))
        except Exception:
            pass

        # Initialize embeddings
        self.stdout.write('🔤 Initializing embedding model...')
        embedding_model = os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small')
        embedding_provider = os.getenv('EMBEDDING_PROVIDER', 'openai')

        if embedding_provider == 'openai':
            # Use OpenAI Embeddings
            try:
                from langchain_openai import OpenAIEmbeddings

                openai_api_key = os.getenv('OPENAI_API_KEY')
                if not openai_api_key:
                    raise CommandError('OPENAI_API_KEY environment variable is required for OpenAI embeddings')

                embeddings = OpenAIEmbeddings(
                    model=embedding_model,
                    openai_api_key=openai_api_key
                )
                self.stdout.write(f'✅ Using OpenAI embedding model: {embedding_model}')
            except ImportError:
                raise CommandError(
                    'langchain-openai not installed. Please install: pip install langchain-openai'
                )
        else:
            # Use HuggingFace Embeddings (fallback)
            embeddings = HuggingFaceEmbeddings(
                model_name=embedding_model,
                model_kwargs={'device': 'cpu'},
                encode_kwargs={'normalize_embeddings': True}
            )
            self.stdout.write(f'✅ Using HuggingFace embedding model: {embedding_model}')

        # ChromaDB storage path
        # Allow CHROMA_PERSIST_DIR env override so plain `manage.py load_welfare_documents` respects .env
        chroma_env = os.getenv('CHROMA_PERSIST_DIR')
        if chroma_env:
            chroma_dir = Path(chroma_env)
        else:
            chroma_dir = Path(settings.BASE_DIR) / 'chromadb_storage'
        chroma_dir.mkdir(parents=True, exist_ok=True)

        self.stdout.write(f'💾 ChromaDB storage: {chroma_dir}')

        # Clear existing data if requested
        if options['clear']:
            self.stdout.write(self.style.WARNING('🗑️  Clearing existing ChromaDB data...'))
            import shutil
            if chroma_dir.exists():
                shutil.rmtree(chroma_dir)
                chroma_dir.mkdir(parents=True)
            self.stdout.write('✅ Existing data cleared')

        # Create or open vector store and add documents in batches to avoid large single requests
        self.stdout.write('🔮 Creating/opening vector store (batched ingestion)...')
        try:
            vectorstore = Chroma(
                persist_directory=str(chroma_dir),
                embedding_function=embeddings,
                collection_name='elderly_welfare_docs'
            )
            self.stdout.write(self.style.SUCCESS('✅ Vector store opened (will add documents in batches)'))
        except Exception as e:
            raise CommandError(f'Failed to open/create vectorstore: {e}')

        # helper to add docs in batches
        def add_in_batches(docs_list, batch_size=50):
            """Add documents in batches with retry/backoff to handle rate limits and token errors.

            Reads env vars when available:
              RAG_RETRY_MAX (int, default 6)
              RAG_RETRY_BASE_SLEEP (float seconds, default 1.0)
              RAG_BATCH_SLEEP_SECONDS (float seconds between batches, default 0.5)
            """
            total = len(docs_list)
            # config from env (defaults)
            try:
                max_retries = int(os.getenv('RAG_RETRY_MAX', '6'))
            except Exception:
                max_retries = 6
            try:
                base_sleep = float(os.getenv('RAG_RETRY_BASE_SLEEP', '1.0'))
            except Exception:
                base_sleep = 1.0
            try:
                inter_batch_sleep = float(os.getenv('RAG_BATCH_SLEEP_SECONDS', '0.5'))
            except Exception:
                inter_batch_sleep = 0.5

            for i in range(0, total, batch_size):
                batch = docs_list[i:i+batch_size]

                attempt = 0
                while True:
                    try:
                        vectorstore.add_documents(batch)
                        # success: small pause before next batch to avoid bursts
                        time.sleep(inter_batch_sleep)
                        break
                    except Exception as e:
                        # detect rate-limit / token errors from message
                        msg = str(e).lower()
                        is_rate = 'rate limit' in msg or 'rate_limit_exceeded' in msg or 'tokens per min' in msg or 'tpm' in msg or 'too many requests' in msg or 'tokens' in msg and 'limit' in msg
                        is_token = 'max_tokens_per_request' in msg or 'max tokens' in msg or 'requested' in msg and 'tokens' in msg

                        attempt += 1
                        if attempt > max_retries or not (is_rate or is_token):
                            # give up and re-raise
                            raise

                        # exponential backoff with jitter
                        sleep_for = base_sleep * (2 ** (attempt - 1)) + random.uniform(0, 1)
                        # cap sleep to a reasonable value (e.g., 60s)
                        sleep_for = min(sleep_for, 60.0)
                        self.stdout.write(self.style.WARNING(f'⚠️ Batch {i}-{i+len(batch)-1} attempt {attempt} failed with: {e}. Retrying after {sleep_for:.1f}s'))
                        time.sleep(sleep_for)

        # Ingest documents either grouped by region or globally in batches
        try:
            if options.get('by_region'):
                regions = {}
                for c in chunks:
                    region = c.metadata.get('region', 'unknown')
                    regions.setdefault(region, []).append(c)

                self.stdout.write(self.style.SUCCESS(f'Found {len(regions)} regions: {list(regions.keys())}'))
                for region, region_chunks in regions.items():
                    self.stdout.write(f'📥 Ingesting region "{region}" with {len(region_chunks)} chunks')
                    add_in_batches(region_chunks, batch_size=options.get('batch_size', 50))
                    try:
                        vectorstore.persist()
                    except Exception:
                        pass
            else:
                self.stdout.write(f'📥 Ingesting all chunks in global batches of {options.get("batch_size", 50)}')
                add_in_batches(chunks, batch_size=options.get('batch_size', 50))
                try:
                    vectorstore.persist()
                except Exception:
                    pass

            self.stdout.write(self.style.SUCCESS('✅ Vector store created and persisted (batches)'))
        except Exception as e:
            raise CommandError(f'Failed during batched ingestion: {e}')

        # Verify the vector store
        self.stdout.write('🔍 Verifying vector store...')
        try:
            collection_count = vectorstore._collection.count()
            self.stdout.write(f'✅ Vector store contains {collection_count} embeddings')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Could not verify count: {e}'))

        # Test query
        self.stdout.write('🧪 Testing vector store with sample query...')
        try:
            test_results = vectorstore.similarity_search('기초연금', k=3)
            self.stdout.write(f'✅ Test query returned {len(test_results)} results')

            if test_results:
                self.stdout.write('\n📝 Sample result:')
                sample = test_results[0]
                self.stdout.write(f'  Content: {sample.page_content[:200]}...')
                self.stdout.write(f'  Metadata: {sample.metadata}')
        except Exception as e:
            self.stdout.write(self.style.WARNING(f'⚠️ Test query failed: {e}'))

        # Summary
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(self.style.SUCCESS('🎉 Document loading complete!'))
        self.stdout.write(self.style.SUCCESS('=' * 80))
        self.stdout.write(f'📊 Statistics:')
        self.stdout.write(f'  - PDF files processed: {len(pdf_files)}')
        self.stdout.write(f'  - Document pages loaded: {len(documents)}')
        self.stdout.write(f'  - Text chunks created: {len(chunks)}')
        self.stdout.write(f'  - Vector embeddings: {collection_count if "collection_count" in locals() else "Unknown"}')
        self.stdout.write(f'  - Storage location: {chroma_dir}')
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ RAG system is ready for chatbot queries!'))
