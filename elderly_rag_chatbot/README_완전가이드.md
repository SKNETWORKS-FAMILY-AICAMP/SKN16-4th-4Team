# 🏥 노인 복지 정책 RAG 챗봇 시스템 - 완전 가이드

> **처음 보는 사람도 쉽게 따라할 수 있는 친절한 설명서**

## 📋 목차
1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 구조](#시스템-구조)
3. [설치 및 환경설정](#설치-및-환경설정)
4. [핵심 기능 사용법](#핵심-기능-사용법)
5. [파일별 상세 설명](#파일별-상세-설명)
6. [문제해결 가이드](#문제해결-가이드)
7. [고급 활용법](#고급-활용법)

---

## 🎯 프로젝트 개요

### 무엇을 하는 시스템인가요?
이 시스템은 **노인 복지 정책에 관한 질문에 답변하는 AI 챗봇**입니다.

**예시 질문들:**
- "65세 이상 기초연금은 얼마나 받을 수 있나요?"
- "장애인 활동지원 서비스는 어떻게 신청하나요?"
- "저소득층 의료비 지원 조건이 궁금합니다"
- "한부모가족 지원 정책에 대해 알려주세요"

### 주요 특징
✅ **실제 복지 정책 데이터** 기반 답변  
✅ **무관한 질문 필터링** (음식, 게임 등은 차단)  
✅ **서브웨이 스타일** 커스텀 챗봇 구성 기능  
✅ **리모컨 방식** 시스템 제어  
✅ **상세한 성능 분석** 도구  

---

## 🏗️ 시스템 구조

```
elderly_rag_chatbot/
├── 🤖 챗봇 핵심 파일
│   ├── smart_custom_chatbot.py      # ⭐ 메인 챗봇 (가드 기능 포함)
│   └── main.py                      # 기본 실행 파일
│
├── 🎮 제어 시스템 (리모컨)
│   ├── rag_remote_control.py        # ⭐ 마스터 리모컨
│   ├── rag_launcher.py              # 통합 런처 (19개 메뉴)
│   └── final_analyzer.py            # ⭐ 완전한 분석 시스템
│
├── 📁 핵심 모듈 (src/)
│   ├── text_extractor.py            # PDF/HWP 텍스트 추출
│   ├── chunk_strategy.py            # 텍스트 청킹 전략
│   ├── embedding_models.py          # 임베딩 모델
│   ├── retrieval_strategies.py      # 검색 전략
│   ├── rag_system.py               # RAG 파이프라인
│   └── text_extraction_comparison.py # 추출기 성능 비교
│
├── ⚙️ 설정 및 구성 (config/)
│   ├── remote_config.json           # 리모컨 설정
│   ├── autorag_config.json          # AutoRAG 설정
│   ├── comparison_config.json       # 비교평가 설정
│   └── custom_chatbot_*.json        # 커스텀 챗봇 구성
│
├── 📊 결과 저장소 (results/)
│   └── comprehensive_report_*.json  # 분석 결과
│
├── 📄 테스트 데이터 (data/)
│   └── 복지로/                     # 실제 복지 정책 문서들
│
└── 🚀 실행 스크립트
    ├── run.bat                      # 윈도우 실행
    ├── run.sh                       # 리눅스 실행
    └── run_comparison.bat           # 비교평가 실행
```

---

## 🔧 설치 및 환경설정

### 1단계: Python 환경 준비
```bash
# Python 3.8+ 필요
python --version

# 가상환경 생성 (권장)
python -m venv venv

# 가상환경 활성화
# 윈도우:
venv\Scripts\activate
# 맥/리눅스:
source venv/bin/activate
```

### 2단계: 필요 라이브러리 설치
```bash
# 기본 설치
pip install -r requirements.txt

# 개별 설치 (문제 발생 시)
pip install sentence-transformers
pip install langchain
pip install faiss-cpu
pip install pymupdf
pip install pdfplumber
```

### 3단계: 환경 확인
```bash
# 시스템 상태 확인
cd elderly_rag_chatbot
python rag_launcher.py
# 메뉴에서 "18. 시스템 상태" 선택
```

---

## 🚀 핵심 기능 사용법

### A. 💬 챗봇 질의응답 (가장 중요!)

**바로 시작하기:**
```bash
cd elderly_rag_chatbot
python smart_custom_chatbot.py
```

**사용 예시:**
```
🤖 복지정책 상담 챗봇에 오신 것을 환영합니다!

질문을 입력하세요: 65세 이상 기초연금이 궁금해요

🔍 검색 중... (가드 기능 & 커스텀 구성 적용)

🤖 답변 #1 (응답시간: 0.15초)
======================================================================
📝 ** 📋 노인 복지 **

**기초연금 지급 정책**

65세 이상 어르신을 대상으로 하는 기초연금은 소득하위 70% 어르신께 
월 최대 334,810원(2024년 기준)을 지급합니다. 
신청은 만 65세 생일이 속하는 달의 1개월 전부터 주민센터나 
국민연금공단 지사에서 가능합니다...

🎯 신뢰도: ★★★★★ (95%)
📂 분류: 노인 복지
📊 답변 수준: 상세
======================================================================
```

**가드 기능 테스트:**
```
질문: 치킨 맛집 추천해줘

📝 😅 죄송하지만 복지 정책과 무관한 질문에는 답변해드릴 수 없습니다.

저는 노인복지, 장애인복지, 아동복지 등 복지 정책 관련 질문에만 답변 가능합니다.

복지 정책에 대해 궁금하신 점이 있으시면 언제든 물어보세요!
```

### B. 🎮 리모컨 시스템 사용법

**통합 런처 실행:**
```bash
python rag_launcher.py
```

**주요 메뉴 설명:**
- `1. 궁극의 리모컨`: 모든 기능을 명령어로 제어
- `4. 텍스트 추출 비교`: PDF/HWP 파일 추출 성능 테스트
- `8. 통합 비교평가`: 전체 시스템 성능 분석
- `18. 시스템 상태`: 현재 상태 확인

**마스터 리모컨 직접 실행:**
```bash
python rag_remote_control.py
```

### C. 🏗️ 서브웨이 스타일 커스텀 챗봇 만들기

**커스텀 챗봇 구성하기:**
```bash
python final_analyzer.py
# 메뉴에서 "11. 서브웨이 스타일 커스텀 챗봇 만들기" 선택
```

**5단계 구성 과정:**
1. **🍞 빵 선택 (텍스트 추출)**: PyPDF2, pdfplumber, PyMuPDF 중 선택
2. **🧀 치즈 선택 (청킹 전략)**: recursive, fixed_size, semantic 중 선택  
3. **🥬 야채 선택 (임베딩 모델)**: sentence-transformers, openai 중 선택
4. **🥄 소스 선택 (검색 전략)**: similarity, mmr, diversity 중 선택
5. **🍟 사이드 선택 (기타 옵션)**: 성능 최적화, 로깅 등

구성 완료 후 자동으로 `config/custom_chatbot_*.json`에 저장됩니다.

### D. 📊 성능 분석 및 벤치마크

**전체 시스템 분석:**
```bash
python final_analyzer.py
# 메뉴에서 원하는 분석 선택:
# 1. 실제 파일 텍스트 추출 분석
# 5. 청킹 전략 상세 분석
# 9. AutoRAG 상세 최적화
# 10. 성능 종합 리포트 생성
```

---

## 📖 파일별 상세 설명

### 🤖 메인 챗봇 파일들

#### `smart_custom_chatbot.py` ⭐
- **기능**: 가드 기능이 포함된 메인 챗봇
- **특징**: 
  - 복지 정책 질문 필터링
  - 커스텀 구성 지원
  - 실제 복지 정책 데이터베이스 내장
  - 신뢰도 점수 제공
- **실행**: `python smart_custom_chatbot.py`

#### `main.py`
- **기능**: 기본 챗봇 실행 파일
- **용도**: 단순한 질의응답 테스트

### 🎮 제어 시스템 파일들

#### `rag_remote_control.py` ⭐
- **기능**: RAG 시스템 마스터 리모컨
- **클래스들**:
  - `RAGMasterRemote`: 전체 시스템 제어
  - `TextExtractionRemote`: 텍스트 추출 제어
  - `ChunkingRemote`: 청킹 전략 제어
  - `EmbeddingRemote`: 임베딩 모델 제어
  - `RetrievalRemote`: 검색 전략 제어

#### `rag_launcher.py`
- **기능**: 19개 메뉴가 있는 통합 런처
- **메뉴 구성**:
  - 리모컨 시스템 (1-3)
  - 비교평가 시스템 (4-7)
  - 통합 도구 (8-10)
  - 결과 및 리포팅 (11-13)
  - 고급 기능 (14-16)
  - 도움말 및 정보 (17-19)

#### `final_analyzer.py` ⭐
- **기능**: 완전한 RAG 분석 시스템
- **주요 기능**:
  - 실제 파일 텍스트 추출 분석
  - HWP 파일 전문 분석
  - AutoRAG 포괄적 최적화
  - 서브웨이 스타일 커스텀 챗봇 빌더
  - 성능 종합 리포트 생성

### 📁 핵심 모듈 (src/)

#### `text_extractor.py`
- **기능**: PDF/HWP 텍스트 추출
- **지원 형식**: PyPDF2, pdfplumber, PyMuPDF, pdfminer, olefile(HWP)

#### `chunk_strategy.py`
- **기능**: 텍스트 청킹 전략
- **전략들**: recursive_character, fixed_size, semantic, sentence

#### `embedding_models.py`
- **기능**: 임베딩 모델 관리
- **모델들**: sentence-transformers, openai, huggingface

#### `retrieval_strategies.py`
- **기능**: 검색 전략 구현
- **전략들**: similarity, mmr(최대 한계 관련성), diversity

#### `rag_system.py`
- **기능**: 전체 RAG 파이프라인 구현
- **클래스**: `RAGSystem` - 텍스트 처리부터 답변 생성까지

### ⚙️ 설정 파일들 (config/)

#### `remote_config.json`
```json
{
    "auto_initialize": true,
    "parallel_execution": false,
    "result_storage": true,
    "benchmark_settings": {
        "max_files": 5,
        "max_texts": 3,
        "timeout": 30
    }
}
```

#### `custom_chatbot_*.json`
서브웨이 스타일로 구성된 커스텀 챗봇 설정이 저장됩니다.

---

## 🆘 문제해결 가이드

### 자주 발생하는 문제들

#### 1. 모듈 import 오류
```
ModuleNotFoundError: No module named 'sentence_transformers'
```
**해결방법:**
```bash
pip install sentence-transformers
# 또는
pip install -r requirements.txt
```

#### 2. HWP 파일 처리 오류
```
Error: HWP 파일을 읽을 수 없습니다
```
**해결방법:**
- HWP는 제한적으로 지원됩니다
- PDF로 변환해서 사용하는 것을 권장
- 또는 `olefile` 라이브러리 설치: `pip install olefile`

#### 3. 메모리 부족 오류
```
OutOfMemoryError: CUDA out of memory
```
**해결방법:**
- `embedding_models.py`에서 `device='cpu'` 설정
- 청킹 크기를 줄이기 (1024 → 512)
- 배치 크기 줄이기

#### 4. 한국어 처리 문제
**해결방법:**
```bash
pip install konlpy
# 윈도우에서는 추가로:
pip install pywin32
```

#### 5. 챗봇이 "정보가 없다"고만 답변
**원인**: 데이터가 제대로 로드되지 않음  
**해결방법:**
1. `data/복지로/` 폴더에 문서가 있는지 확인
2. 권한 문제 확인
3. 파일 경로 문제 확인

### 시스템 상태 확인 방법
```bash
python rag_launcher.py
# 메뉴에서 "18. 시스템 상태" 선택
```

### 로그 확인 방법
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🎓 고급 활용법

### 1. 새로운 복지 문서 추가하기

**1단계: 문서 준비**
```bash
# data/복지로/ 폴더에 PDF 또는 HWP 파일 추가
data/복지로/새로운지역/pdf/새로운정책.pdf
```

**2단계: 텍스트 추출 테스트**
```bash
python rag_launcher.py
# "4. 텍스트 추출 비교" 선택하여 새 문서 테스트
```

**3단계: 챗봇 재시작**
```bash
python smart_custom_chatbot.py
# 새로운 문서 내용으로 질문 테스트
```

### 2. 성능 최적화하기

**AutoRAG 자동 최적화:**
```bash
python final_analyzer.py
# "9. AutoRAG 상세 최적화" 선택
```

**수동 최적화:**
1. **텍스트 추출**: `final_analyzer.py` → "1. 실제 파일 텍스트 추출 분석"
2. **청킹 전략**: `final_analyzer.py` → "5. 청킹 전략 상세 분석"  
3. **임베딩 모델**: `final_analyzer.py` → "6. 임베딩 모델 성능 분석"
4. **검색 전략**: `final_analyzer.py` → "7. 검색 전략 비교 분석"

### 3. 커스텀 필터링 규칙 추가

`smart_custom_chatbot.py`의 `_is_valid_welfare_query` 함수를 수정:
```python
def _is_valid_welfare_query(self, query: str) -> bool:
    welfare_keywords = [
        # 기존 키워드들...
        '새로운키워드1', '새로운키워드2'  # 추가
    ]
    
    irrelevant_keywords = [
        # 기존 키워드들...
        '차단할키워드1', '차단할키워드2'  # 추가
    ]
```

### 4. 새로운 지역 데이터 추가

**폴더 구조:**
```
data/복지로/새로운지역/
├── hwp/
│   └── 정책문서.hwp
└── pdf/
    └── 정책문서.pdf
```

### 5. 배치 처리로 대량 문서 처리

```bash
# 전체 문서 일괄 분석
python final_analyzer.py
# "4. 텍스트 추출 종합 벤치마크" 선택
```

### 6. 성능 리포트 생성 및 분석

```bash
python final_analyzer.py
# "10. 성능 종합 리포트 생성" 선택
# results/ 폴더에 JSON 리포트 생성됨
```

---

## 🔧 개발자를 위한 확장 가이드

### 새로운 텍스트 추출기 추가
```python
# src/text_extractor.py에 추가
class 새로운Extractor:
    def extract_text(self, file_path: str) -> str:
        # 구현
        pass
```

### 새로운 청킹 전략 추가
```python
# src/chunk_strategy.py에 추가
class 새로운ChunkStrategy:
    def chunk_text(self, text: str, chunk_size: int) -> List[str]:
        # 구현
        pass
```

### 새로운 검색 전략 추가
```python
# src/retrieval_strategies.py에 추가
class 새로운RetrievalStrategy:
    def search(self, query: str, documents: List[str]) -> List[Dict]:
        # 구현
        pass
```

---

## 📞 지원 및 연락처

### 문제 신고
- 이슈 발생 시 GitHub Issues에 보고
- 로그와 함께 구체적인 오류 상황 기술

### 기여하기
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

### 라이선스
이 프로젝트는 MIT 라이선스 하에 배포됩니다.

---

## 🎉 마무리

이 가이드를 따라하시면 복지 정책 RAG 챗봇 시스템을 완전히 이해하고 활용할 수 있습니다!

**시작 권장 순서:**
1. 환경 설정 완료
2. `python smart_custom_chatbot.py` 실행해서 챗봇 테스트
3. `python rag_launcher.py` 실행해서 전체 기능 둘러보기
4. `python final_analyzer.py` 실행해서 커스텀 챗봇 만들기
5. 성능 분석 및 최적화

**궁금한 점이 있으면:**
- 먼저 이 가이드의 "문제해결" 섹션 확인
- 시스템 상태 확인 (`rag_launcher.py` → 18번)
- 그래도 안 되면 개발팀에 문의

**즐거운 챗봇 개발 되세요! 🚀**