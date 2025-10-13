# 🏥 노인복지 정책 RAG 챗봇 시스템

## 📋 프로젝트 개요

노인복지 관련 정책 문서를 활용하여 사용자 질문에 정확하고 유용한 답변을 제공하는 **Retrieval-Augmented Generation (RAG)** 기반 챗봇 시스템입니다.

### 🎯 주요 기능

- **📄 다양한 문서 형식 지원**: PDF, HWP, TXT 파일 처리
- **🔧 텍스트 추출 방법 비교**: PyPDF2, pdfplumber, PyMuPDF, pdfminer 등 다양한 추출기 성능 비교
- **✂️ 지능형 문서 청킹**: 여러 청킹 전략 비교 및 최적화
- **🔢 임베딩 모델 최적화**: OpenAI, SentenceTransformer, KoBERT 모델 비교
- **🗄️ 벡터 데이터베이스**: ChromaDB 기반 효율적 문서 검색
- **🔍 하이브리드 검색**: 키워드, 의미, 하이브리드 검색 방식
- **🤖 고급 RAG 시스템**: LangChain 기반 대화형 AI
- **🔄 워크플로우 관리**: LangGraph를 활용한 복잡한 쿼리 처리
- **💬 사용자 친화적 인터페이스**: Gradio/Streamlit 웹 인터페이스
- **🎯 AutoRAG 자동 최적화**: 전체 파이프라인 자동 최적화 시스템
- **📊 성능 평가**: 각 컴포넌트별 비교 분석 및 최적화

## 🏗️ 시스템 아키텍처

```
📁 elderly_rag_chatbot/
├── 📁 src/                           # 핵심 모듈
│   ├── 📄 text_extractor.py          # 문서 추출 (PDF/HWP/TXT)
│   ├── 🔧 text_extraction_comparison.py # 텍스트 추출 방법 비교
│   ├── ✂️ chunk_strategy.py          # 청킹 전략 비교
│   ├── 🔢 embedding_models.py        # 임베딩 모델 비교
│   ├── 🗄️ vector_store.py            # ChromaDB 벡터 저장소
│   ├── 🔍 retriever.py               # 다중 검색기 시스템
│   ├── 🤖 rag_system.py              # RAG 체인 구현
│   ├── 🔄 langgraph_workflow.py      # 워크플로우 관리
│   ├── 🎯 autorag_optimizer.py       # AutoRAG 자동 최적화
│   └── 💬 chatbot_interface.py       # 웹 인터페이스
├── 📁 config/                        # 설정 파일
│   └── ⚙️ settings.py               # 시스템 설정
├── 📁 data/                          # 데이터 디렉토리
│   └── 📂 복지로/                    # 복지 정책 문서
├── 📁 logs/                          # 로그 파일
├── 📄 requirements.txt               # 의존성 패키지
├── 🚀 main.py                        # 메인 실행 스크립트
└── 📖 README.md                      # 프로젝트 문서
```

## 🛠️ 설치 및 설정

### 1. 환경 요구사항

- Python 3.8+
- 최소 8GB RAM 권장
- 10GB 이상 디스크 여유 공간

### 2. 패키지 설치

```bash
# 저장소 클론
git clone <repository_url>
cd elderly_rag_chatbot

# 가상 환경 생성 (권장)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 의존성 패키지 설치
pip install -r requirements.txt
```

### 3. 환경 변수 설정

`.env` 파일을 생성하고 다음 내용을 추가:

```bash
# OpenAI API 키 (선택사항)
OPENAI_API_KEY=your_openai_api_key_here

# 실행 환경
ELDERLY_RAG_ENV=development

# 데이터 디렉토리
DATA_DIRECTORY=./data/복지로

# 로그 레벨
LOG_LEVEL=INFO
```

### 4. 데이터 준비

복지 정책 문서를 `data/복지로/` 디렉토리에 배치:

```
data/복지로/
├── 전국/
├── 경북/
├── 대구/
├── 부산/
├── 전남/
└── 전북/
```

## 🚀 실행 방법

### 기본 실행

```bash
# Gradio 웹 인터페이스로 실행
python main.py

# Streamlit 인터페이스로 실행
python main.py --interface streamlit

# 특정 포트로 실행
python main.py --port 8080
```

### 🎯 AutoRAG 자동 최적화

```bash
# 완전 자동 최적화 (권장)
python main.py --autorag

# 속도 우선 최적화
python main.py --autorag --autorag-target speed

# 품질 우선 최적화  
python main.py --autorag --autorag-target quality

# 균형 최적화 (기본값)
python main.py --autorag --autorag-target balanced
```

### 고급 옵션

```bash
# 벡터 데이터베이스 재구성
python main.py --rebuild

# 성능 평가 포함 실행
python main.py --evaluate

# 커스텀 설정 파일 사용
python main.py --config config/custom_settings.json

# 인터페이스 없이 시스템만 초기화
python main.py --interface none

# 텍스트 추출 비교 테스트
python -m src.text_extraction_comparison

# AutoRAG 시스템 테스트
python -m src.autorag_optimizer
```

### 명령줄 옵션

| 옵션 | 설명 | 기본값 |
|------|------|--------|
| `--config, -c` | 설정 파일 경로 | None |
| `--interface, -i` | 인터페이스 타입 (gradio/streamlit/none) | gradio |
| `--rebuild, -r` | 벡터 데이터베이스 재구성 | False |
| `--evaluate, -e` | 성능 평가 실행 | False |
| `--port, -p` | 인터페이스 포트 번호 | 7860 |

## 📊 시스템 컴포넌트

### 1. 문서 추출기 (`text_extractor.py`)

- **지원 형식**: PDF, HWP, TXT
- **특징**: 메타데이터 추출, 캐싱, 오류 처리
- **성능**: 대용량 문서 배치 처리
- **최적화**: 자동 최적 추출기 선택

```python
from src.text_extractor import WelfareDocumentExtractor

extractor = WelfareDocumentExtractor("./data/복지로")
documents = extractor.extract_all_documents(use_best_extractor=True)
```

### 1-1. 텍스트 추출 비교 (`text_extraction_comparison.py`)

- **PDF 추출기**: PyPDF2, pdfplumber, PyMuPDF, pdfminer
- **HWP 추출기**: olefile, hwp5, pyhwp
- **성능 평가**: 성공률, 속도, 텍스트 품질
- **자동 선택**: 최적 추출기 자동 선정

```python
from src.text_extraction_comparison import TextExtractionComparison

comparison = TextExtractionComparison()
pdf_results = comparison.compare_pdf_extractors(pdf_files)
best_pdf_extractor = pdf_results["best_extractor"]
```

### 2. 청킹 전략 (`chunk_strategy.py`)

- **전략**: 재귀적, 문단, 의미, 토큰 기반
- **평가**: 일관성, 커버리지, 다양성 메트릭
- **최적화**: 자동 최적 전략 선택

```python
from src.chunk_strategy import ChunkStrategyComparison

chunker = ChunkStrategyComparison()
evaluation = chunker.evaluate_strategies(texts)
best_strategy = chunker.get_best_strategy(evaluation)
```

### 3. 임베딩 모델 (`embedding_models.py`)

- **모델**: OpenAI, SentenceTransformer, KoBERT
- **평가**: 유사도 품질, 속도, 메모리 사용량
- **한국어**: 특화 모델 지원

```python
from src.embedding_models import EmbeddingModelComparison

embedder = EmbeddingModelComparison()
comparison = embedder.compare_models(texts)
best_model = embedder.get_best_model()
```

### 4. 벡터 저장소 (`vector_store.py`)

- **데이터베이스**: ChromaDB
- **기능**: 메타데이터 필터링, 문서 분류
- **검색**: 유사도 기반 효율적 검색

```python
from src.vector_store import WelfareVectorStore

vector_store = WelfareVectorStore(
    persist_directory="./data/chroma_db",
    embedding_model=best_embedding_model
)
vector_store.add_documents(documents)
```

### 5. 검색기 (`retriever.py`)

- **방식**: 키워드, 의미, 하이브리드
- **최적화**: BM25, TF-IDF, 벡터 검색 조합
- **평가**: 정확도, 재현율 메트릭

```python
from src.retriever import RetrieverComparison

retriever_comp = RetrieverComparison(vector_store)
evaluation = retriever_comp.evaluate_retrievers(queries)
best_retriever = retriever_comp.get_best_retriever()
```

### 6. RAG 시스템 (`rag_system.py`)

- **체인**: LangChain 기반 대화형 체인
- **메모리**: 대화 기록 유지
- **평가**: 답변 품질, 신뢰도 측정

```python
from src.rag_system import ElderlyWelfareRAGChain

rag_chain = ElderlyWelfareRAGChain(
    retriever=best_retriever,
    llm_model="gpt-3.5-turbo"
)
response = rag_chain.ask("노인 의료비 지원 방법은?")
```

### 7. 워크플로우 (`langgraph_workflow.py`)

- **관리**: LangGraph 상태 기반 워크플로우
- **단계**: 의도 분류 → 검색 → 평가 → 답변 생성
- **조건부**: 복잡한 쿼리 처리 로직

```python
from src.langgraph_workflow import ElderlyWelfareWorkflow

workflow = ElderlyWelfareWorkflow(rag_chain)
result = workflow.process_query("복잡한 질문...")
```

### 8. 챗봇 인터페이스 (`chatbot_interface.py`)

- **인터페이스**: Gradio, Streamlit 지원
- **기능**: 실시간 채팅, 피드백 수집, 통계
- **사용자 경험**: 직관적 웹 UI

```python
from src.chatbot_interface import ElderlyWelfareChatbot, GradioInterface

chatbot = ElderlyWelfareChatbot(rag_system, workflow_system)
interface = GradioInterface(chatbot)
interface.launch()
```

### 9. AutoRAG 자동 최적화 (`autorag_optimizer.py`)

- **자동 최적화**: 전체 파이프라인 구성 요소 자동 선택
- **성능 지향**: 속도, 품질, 균형 중 목표 선택 가능
- **단계별 평가**: 각 컴포넌트별 최적 옵션 선정
- **결과 저장**: 최적화 과정과 결과 자동 저장

```python
from src.autorag_optimizer import AutoRAGInterface, AutoRAGConfig

# 자동 최적화 설정
config = AutoRAGConfig(
    evaluation_queries=["질문1", "질문2"],
    optimization_target="balanced"
)

# AutoRAG 실행
autorag = AutoRAGInterface()
results = await autorag.run_optimization(config)
optimized_chatbot = autorag.get_optimized_chatbot()
```

## ⚙️ 설정 옵션

### 주요 설정 파일: `config/settings.py`

```python
# 임베딩 모델 설정
embedding:
  default_model: "sentence_transformer"
  openai_model: "text-embedding-ada-002"

# RAG 시스템 설정
rag:
  llm_model: "gpt-3.5-turbo"
  temperature: 0.1
  max_tokens: 1000

# 인터페이스 설정
interface:
  gradio_server_port: 7860
  max_conversation_history: 20
```

### 환경별 설정

- **개발 환경**: 디버그 모드, 상세 로깅
- **운영 환경**: 최적화된 성능, 에러 로깅

## 📈 성능 평가

### 자동 평가 시스템

시스템은 각 컴포넌트별 성능을 자동으로 평가합니다:

1. **청킹 전략**: 일관성, 커버리지, 다양성
2. **임베딩 모델**: 유사도 품질, 처리 속도
3. **검색기**: 정확도, 재현율, 응답 시간
4. **RAG 시스템**: 답변 품질, 관련성

### 평가 실행

```bash
# 전체 시스템 성능 평가
python main.py --evaluate

# 개별 컴포넌트 평가
python -m src.chunk_strategy
python -m src.embedding_models
python -m src.retriever
```

## 🔧 개발 및 확장

### 새로운 컴포넌트 추가

1. **새로운 임베딩 모델**:
   ```python
   # src/embedding_models.py에 새 클래스 추가
   class NewEmbeddingModel(BaseEmbeddingModel):
       def embed_text(self, text: str) -> List[float]:
           # 구현
   ```

2. **새로운 청킹 전략**:
   ```python
   # src/chunk_strategy.py에 새 전략 추가
   class NewChunkStrategy(BaseChunkStrategy):
       def chunk_text(self, text: str) -> List[str]:
           # 구현
   ```

3. **새로운 검색기**:
   ```python
   # src/retriever.py에 새 검색기 추가
   class NewRetriever(BaseRetriever):
       def retrieve(self, query: str) -> List[Document]:
           # 구현
   ```

### 커스터마이징

- **프롬프트 수정**: `src/rag_system.py`의 프롬프트 템플릿
- **UI 커스터마이징**: `src/chatbot_interface.py`의 인터페이스
- **설정 변경**: `config/settings.py`의 각종 파라미터

## 🐛 문제 해결

### 일반적인 문제

1. **메모리 부족**:
   - 청크 크기 감소: `chunk_size=500`
   - 배치 크기 감소: `batch_size=10`

2. **느린 응답 속도**:
   - 경량 임베딩 모델 사용
   - 검색 결과 수 제한: `top_k=3`

3. **답변 품질 저하**:
   - 더 큰 청크 크기 사용
   - 임베딩 모델 업그레이드
   - 프롬프트 엔지니어링

### 로그 확인

```bash
# 실시간 로그 확인
tail -f logs/elderly_rag_chatbot.log

# 에러 로그만 확인
grep "ERROR" logs/elderly_rag_chatbot.log
```

## 📝 API 문서

### 프로그래밍 인터페이스

```python
from main import ElderlyRAGChatbotSystem

# 시스템 초기화
system = ElderlyRAGChatbotSystem()
await system.initialize_system()

# 질문 처리
response = system.chatbot.process_message("질문...")

# 성능 평가
evaluation = system.run_evaluation()

# 시스템 상태
status = system.get_system_status()
```

## 🤝 기여 방법

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 라이선스

이 프로젝트는 MIT 라이선스 하에 제공됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

## 📞 지원 및 문의

- **이슈 리포트**: [GitHub Issues](https://github.com/your-repo/issues)
- **기능 요청**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **문서**: 이 README 파일과 각 모듈의 독스트링

## 🙏 감사의 말

이 프로젝트는 다음 오픈소스 라이브러리들을 기반으로 만들어졌습니다:

- [LangChain](https://github.com/hwchase17/langchain)
- [LangGraph](https://github.com/langchain-ai/langgraph)
- [ChromaDB](https://github.com/chroma-core/chroma)
- [SentenceTransformers](https://github.com/UKPLab/sentence-transformers)
- [Gradio](https://github.com/gradio-app/gradio)
- [Streamlit](https://github.com/streamlit/streamlit)

---

**🏥 노인복지 정책 RAG 챗봇 시스템** - 더 나은 복지 서비스 접근성을 위하여