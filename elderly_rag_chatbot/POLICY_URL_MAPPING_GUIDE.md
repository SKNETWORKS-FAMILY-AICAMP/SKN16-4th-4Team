# 정책 URL 매핑 가이드

## 개요

이 문서는 복지로 정책 목록에서 정책별 URL을 설정하는 방법을 설명합니다.

현재 시스템은 다음 3단계로 정책 URL을 결정합니다:

1. **Git commit message에서 정책명 추출** ✅ 완료
   - `policy_pdf_mapping.json` 파일에 160개 PDF-정책명 매핑 저장
   - 정책 목록에 Git commit message의 정책명이 표시됨

2. **정책명으로 URL 찾기** (아래 우선순위 순서)
   - ① `MANUAL_POLICY_URL_MAPPING`에서 정확한 정책명 매칭
   - ② `POLICY_METADATA`에서 키워드 매칭 (11개 주요 정책 내장)
   - ③ 기본 검색 페이지 URL (매칭 실패 시)

## 현재 상태

- **총 정책 수**: 213개
- **특정 URL로 매칭된 정책**: 33개 (15.5%)
- **검색 페이지 사용 정책**: 180개 (84.5%)

## 정책 URL 추가 방법

### 1. 수동 매핑 파일 수정

파일 경로: `chatbot_web/rag_system/policy_metadata.py`

```python
# 정책명 -> URL 수동 매핑
MANUAL_POLICY_URL_MAPPING = {
    # 예시 (아래 형식으로 추가):
    '기초연금': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000156',

    # 여기에 추가하세요:
    # '정책명': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000XXX',
}
```

### 2. 복지로에서 정책 ID 찾기

복지로 사이트에서 정책을 검색한 후 URL에서 `wlfareInfoId` 파라미터를 확인하세요:

```
https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000156
                                                                                    ^^^^^^^^^^^^
                                                                                    이 부분이 정책 ID
```

### 3. 매칭 테스트

URL 매핑을 추가한 후 다음 명령어로 테스트:

```bash
cd elderly_rag_chatbot
python test_policy_urls.py
```

## 주요 정책 목록 (URL 추가 필요)

Git commit message에서 추출한 180개 정책 중 URL이 아직 매핑되지 않은 정책들입니다.
우선순위가 높은 정책부터 URL을 추가하세요.

### 지역별 주요 정책 예시

#### 경남 지역
- 2024년 장애인보조기기 및 편의설비 지원사업
- 2023년 청년기술창업수당 지원사업
- 기초생활수급자 쓰레기봉투 지원
- 화장장려금 지원
- 저소득 어르신 무료틀니 지원사업

#### 경북 지역
- 봉화군 효행장려 및 지원
- 장애인 차량용 보조기기 구입지원 사업
- 장애인 하이패스 감면단말기 보급 사업

#### 전국 정책
- 저소득틈새지원사업
- 어려운세대 밑반찬 지원사업
- 노숙인 등의 복지사업

## 내장된 정책 URL (POLICY_METADATA)

다음 11개 정책은 이미 URL이 설정되어 있으며, 키워드가 포함된 정책명은 자동으로 매칭됩니다:

1. **의료급여** (`WLF00000149`)
2. **기초연금** (`WLF00000156`)
3. **노인장기요양보험** (`WLF00000292`)
4. **경로우대 제도** (`WLF00001876`)
5. **노인일자리 및 사회활동 지원사업** (`WLF00000191`)
6. **노인복지관 운영** (`WLF00000185`)
7. **경로당 운영** (`WLF00000186`)
8. **노인맞춤돌봄서비스** (`WLF00000165`)
9. **재난적의료비 지원** (`WLF00004044`)
10. **노인 건강검진** (`WLF00000160`)
11. **국가유공자 등 예우 및 지원** (`WLF00000137`)

## 자주 묻는 질문

### Q1. URL 매핑을 추가하면 언제 반영되나요?

Django 서버를 재시작하거나, 개발 모드에서는 파일을 저장하면 자동으로 반영됩니다.

### Q2. 모든 정책에 URL을 추가해야 하나요?

아니요. 자주 사용되는 주요 정책부터 우선적으로 추가하세요.
나머지 정책은 검색 페이지로 연결되어 사용자가 직접 검색할 수 있습니다.

### Q3. 정책 ID를 어떻게 찾나요?

1. [복지로 사이트](https://www.bokjiro.go.kr)에서 정책명으로 검색
2. 검색 결과에서 해당 정책 클릭
3. 주소창의 URL에서 `wlfareInfoId=WLF00000XXX` 부분 복사

### Q4. Git commit message의 정책명이 정확하지 않으면?

`policy_pdf_mapping.json` 파일을 직접 수정하거나,
`extract_policy_name()` 함수의 정규표현식을 조정하세요.

## 관련 파일

- **정책 메타데이터**: `chatbot_web/rag_system/policy_metadata.py`
- **PDF-정책명 매핑**: `chatbot_web/rag_system/policy_pdf_mapping.json`
- **URL 매핑 생성 스크립트**: `create_policy_url_mapping.py`
- **테스트 스크립트**:
  - `test_policy_names.py` - 정책명 추출 테스트
  - `test_policy_urls.py` - URL 매칭 테스트

## 다음 단계

1. **우선순위 정책 선정**: 자주 조회되는 정책 10-20개 선정
2. **복지로에서 정책 ID 찾기**: 각 정책의 `wlfareInfoId` 확인
3. **MANUAL_POLICY_URL_MAPPING 업데이트**: 정책명-URL 쌍 추가
4. **테스트**: `python test_policy_urls.py` 실행하여 매칭률 확인
5. **반복**: 추가 정책에 대해 2-4 단계 반복

## 지원

질문이나 문제가 있으면 프로젝트 관리자에게 문의하세요.
