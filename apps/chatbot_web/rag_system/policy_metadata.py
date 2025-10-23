"""
정책 메타데이터 - 정책명, URL 매핑

복지로(www.bokjiro.go.kr)의 정책 정보와 PDF 파일명을 매핑
"""

# 정책 메타데이터: 파일명 키워드 -> 정책 정보
POLICY_METADATA = {
    # 의료급여
    '의료급여': {
        'name': '의료급여',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000149',
        'category': '건강',
        'keywords': ['의료급여', '의료지원', '의료비']
    },

    # 기초연금
    '기초연금': {
        'name': '기초연금',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000156',
        'category': '노령',
        'keywords': ['기초연금', '노령연금']
    },

    # 노인장기요양보험
    '장기요양': {
        'name': '노인장기요양보험',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000292',
        'category': '돌봄',
        'keywords': ['장기요양', '요양보험', '장기요양보험']
    },

    # 경로우대
    '경로우대': {
        'name': '경로우대 제도',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00001876',
        'category': '문화',
        'keywords': ['경로우대', '교통', '할인', '무료']
    },

    # 노인일자리
    '노인일자리': {
        'name': '노인일자리 및 사회활동 지원사업',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000191',
        'category': '고용',
        'keywords': ['노인일자리', '사회활동', '일자리']
    },

    # 노인복지관
    '노인복지관': {
        'name': '노인복지관 운영',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000185',
        'category': '여가',
        'keywords': ['노인복지관', '복지관', '여가']
    },

    # 경로당
    '경로당': {
        'name': '경로당 운영',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000186',
        'category': '여가',
        'keywords': ['경로당']
    },

    # 노인돌봄서비스
    '노인돌봄': {
        'name': '노인맞춤돌봄서비스',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000165',
        'category': '돌봄',
        'keywords': ['노인돌봄', '돌봄서비스', '맞춤돌봄']
    },

    # 재난적의료비
    '재난적의료비': {
        'name': '재난적의료비 지원',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00004044',
        'category': '건강',
        'keywords': ['재난적의료비', '의료비지원']
    },

    # 노인건강진단
    '노인건강': {
        'name': '노인 건강검진',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000160',
        'category': '건강',
        'keywords': ['건강검진', '건강진단']
    },

    # 보훈수당
    '보훈': {
        'name': '국가유공자 등 예우 및 지원',
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000137',
        'category': '보상',
        'keywords': ['보훈', '국가유공자', '보훈수당']
    }
}


# 정책명 -> URL 수동 매핑 (Git commit message에서 추출한 정책명에 대해 URL 매핑)
# 사용자가 제공한 정책 URL을 여기에 추가
MANUAL_POLICY_URL_MAPPING = {
    # 예시: '기초연금': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000156',
    # 아래에 사용자가 제공한 정책명-URL 쌍을 추가하세요
}


def find_policy_metadata(text: str, filename: str = "") -> dict:
    """
    텍스트와 파일명에서 정책 정보를 찾아 반환

    Args:
        text: PDF 내용
        filename: 파일명

    Returns:
        정책 메타데이터 또는 기본값
    """
    # 파일명에서 먼저 검색
    filename_lower = filename.lower()
    for key, metadata in POLICY_METADATA.items():
        if key in filename_lower:
            return metadata

    # 텍스트 내용에서 키워드 검색
    text_lower = text.lower()
    for key, metadata in POLICY_METADATA.items():
        for keyword in metadata['keywords']:
            if keyword in text_lower:
                return metadata

    # 기본값 반환
    return {
        'name': None,  # 정책명 없음
        'url': 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52005M.do',  # 정책 목록 페이지
        'category': '복지',
        'keywords': []
    }


def get_all_policies() -> list:
    """
    모든 정책 목록 반환 (정책 목록 탭용)

    Returns:
        정책 정보 리스트
    """
    policies = []
    for key, metadata in POLICY_METADATA.items():
        policies.append({
            'name': metadata['name'],
            'url': metadata['url'],
            'category': metadata['category']
        })

    # 카테고리별 정렬
    policies.sort(key=lambda x: (x['category'], x['name']))
    return policies


def categorize_policy(filename: str) -> str:
    """
    PDF 파일명에서 정책 카테고리 추론

    Args:
        filename: PDF 파일명

    Returns:
        카테고리명
    """
    filename_lower = filename.lower()

    # 키워드 기반 카테고리 분류
    categories = {
        '건강': ['의료', '건강', '검진', '치료', '병원', '심뇌혈관', '암', '질환', '예방접종'],
        '돌봄': ['돌봄', '요양', '장기요양', '간호', '케어', '목욕', '간병'],
        '노령': ['연금', '기초연금', '노령', '노후'],
        '주거': ['주택', '주거', '임대', '매입', '전세', '월세', '주택개량'],
        '일자리': ['일자리', '취업', '고용', '근로', '공공근로', '사회활동'],
        '경제': ['생계', '생활보장', '긴급복지', '자활', '저소득', '차상위', '기초생활', '수당', '지원금'],
        '문화': ['문화', '여가', '관광', '교통', '경로우대', '할인'],
        '시설': ['복지관', '경로당', '노인', '센터', '시설'],
        '식생활': ['식사', '급식', '경로식당', '밑반찬', '결식'],
        '교육': ['교육', '평생교육', '배움', '학습'],
        '보훈': ['보훈', '유공자', '국가유공']
    }

    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in filename_lower:
                return category

    return '기타'


def extract_policy_name(filename: str) -> str:
    """
    PDF 파일명에서 정책명 추출

    Args:
        filename: PDF 파일명 (확장자 제외)

    Returns:
        정리된 정책명
    """
    import re

    # 원본 파일명 저장
    policy_name = filename

    # 앞의 숫자 ID만 있는 경우
    if policy_name.replace('.', '').replace(' ', '').replace('(', '').replace(')', '').isdigit():
        return f"정책 {policy_name}"

    # 괄호 및 특수문자 정리
    policy_name = re.sub(r'\(외부용\)_?', '', policy_name)
    policy_name = re.sub(r'_?최종$', '', policy_name)
    policy_name = re.sub(r'\(최종\)', '', policy_name)
    policy_name = re.sub(r'_?안내$', '', policy_name)
    policy_name = re.sub(r'\(\d{6}\)', '', policy_name)  # (250123) 같은 날짜 제거

    # 사업안내, 운영안내 등 제거
    policy_name = re.sub(r'_?사업안내.*$', '', policy_name)
    policy_name = re.sub(r'_?운영안내.*$', '', policy_name)
    policy_name = re.sub(r'_?지침.*$', '', policy_name)
    policy_name = re.sub(r'_?표준실무지침.*$', '', policy_name)
    policy_name = re.sub(r'_?관리지침.*$', '', policy_name)
    policy_name = re.sub(r'\s*\(보건소용\s*\d*권?\)', '', policy_name)
    policy_name = re.sub(r'\s*\(의료기관용\s*\d*권?\)', '', policy_name)

    # 언더스코어를 공백으로
    policy_name = policy_name.replace('_', ' ')

    # 다중 공백을 하나로
    policy_name = re.sub(r'\s+', ' ', policy_name)

    # 앞뒤 공백 제거
    policy_name = policy_name.strip()

    # 최종적으로 비어있으면 원본 반환
    if not policy_name:
        return filename

    return policy_name


def load_pdf_policy_mapping() -> dict:
    """Git commit message에서 추출한 PDF-정책명 매핑 로드"""
    import json
    from pathlib import Path

    mapping_file = Path(__file__).parent / 'policy_pdf_mapping.json'
    if mapping_file.exists():
        with open(mapping_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def find_policy_url(policy_name: str) -> str:
    """
    정책명으로 복지로 URL을 찾음

    우선순위:
    1. MANUAL_POLICY_URL_MAPPING에서 정확한 정책명 매칭
    2. POLICY_METADATA에서 키워드 매칭
    3. 기본 검색 페이지 URL

    Args:
        policy_name: 정책명

    Returns:
        복지로 정책 URL
    """
    # 1. 수동 매핑에서 정확한 이름 찾기
    if policy_name in MANUAL_POLICY_URL_MAPPING:
        return MANUAL_POLICY_URL_MAPPING[policy_name]

    # 2. POLICY_METADATA에서 키워드로 찾기
    policy_name_lower = policy_name.lower()
    for key, metadata in POLICY_METADATA.items():
        # 정책명 완전 일치
        if metadata['name'].lower() == policy_name_lower:
            return metadata['url']

        # 키워드 포함 여부 확인
        for keyword in metadata['keywords']:
            if keyword in policy_name_lower:
                return metadata['url']

    # 3. 기본 검색 페이지 (노년 필터 적용)
    return 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52005M.do?page=1&orderBy=date&tabId=1&period=%EB%85%B8%EB%85%84'


def load_policy_csv_mapping() -> dict:
    """
    CSV 파일에서 PDF-정책명-주제-URL 매핑 로드

    Returns:
        {
            'region': {
                'pdf_filename': {
                    'policy_name': '...',
                    'category_1': '...',
                    'category_2': '...',
                    'url': '...'
                }
            }
        }
    """
    import csv
    from pathlib import Path

    csv_file = Path(__file__).parent.parent.parent / 'policy_mapping.csv'

    if not csv_file.exists():
        return {}

    mapping = {}

    try:
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            for row in reader:
                region = row['region']
                pdf_filename = row['pdf_filename']

                if region not in mapping:
                    mapping[region] = {}

                mapping[region][pdf_filename] = {
                    'policy_name': row['policy_name'],
                    'category_1': row['category_1'],
                    'category_2': row['category_2'],
                    'url': row['url']
                }
    except Exception as e:
        print(f"CSV 파일 로드 실패: {e}")
        return {}

    return mapping


def scan_policy_pdfs() -> dict:
    """
    CSV 매핑 파일을 기반으로 정책 목록 생성
    CSV 파일이 없으면 기존 방식으로 동작

    Returns:
        {
            '지역명': {
                '카테고리': [
                    {'name': '정책명', 'filename': 'xxx.pdf', 'url': '...', 'category_2': '...'},
                    ...
                ]
            }
        }
    """
    import os
    from pathlib import Path
    from .rag_config import MAIN_DATA_DIR

    result = {}

    # CSV 매핑 파일 로드 (우선)
    csv_mapping = load_policy_csv_mapping()

    # CSV 파일이 있으면 CSV 기반으로 동작
    if csv_mapping:
        print("[INFO] CSV 매핑 파일을 사용합니다.")

        for region, pdf_dict in csv_mapping.items():
            if region not in result:
                result[region] = {}

            for pdf_filename, info in pdf_dict.items():
                category_1 = info['category_1'] or '기타'

                if category_1 not in result[region]:
                    result[region][category_1] = []

                result[region][category_1].append({
                    'name': info['policy_name'],
                    'filename': pdf_filename,
                    'url': info['url'],
                    'category': category_1,
                    'category_2': info['category_2']
                })

    else:
        # CSV 파일이 없으면 기존 방식으로 동작
        print("[INFO] CSV 파일이 없습니다. 기존 방식으로 스캔합니다.")

        # 데이터 디렉토리 확인
        if not MAIN_DATA_DIR.exists():
            return result

        # Git commit message에서 추출한 정책명 매핑 로드
        pdf_mapping = load_pdf_policy_mapping()

        # 각 지역 폴더 순회
        for region_dir in MAIN_DATA_DIR.iterdir():
            if not region_dir.is_dir():
                continue

            region_name = region_dir.name
            result[region_name] = {}

            # PDF 파일 찾기
            pdf_dir = region_dir / 'pdf'
            if not pdf_dir.exists():
                continue

            for pdf_file in pdf_dir.glob('*.pdf'):
                pdf_filename = pdf_file.name
                file_stem = pdf_file.stem

                # Git commit message에서 정책명 찾기
                if pdf_filename in pdf_mapping:
                    policy_name = pdf_mapping[pdf_filename]['policy_name']
                    if len(policy_name) < 5:
                        policy_name = extract_policy_name(file_stem)
                else:
                    policy_name = extract_policy_name(file_stem)

                # 카테고리 추론
                category = categorize_policy(policy_name)

                if category not in result[region_name]:
                    result[region_name][category] = []

                # 정책명으로 URL 찾기
                policy_url = find_policy_url(policy_name)

                result[region_name][category].append({
                    'name': policy_name,
                    'filename': pdf_filename,
                    'url': policy_url,
                    'category': category,
                    'category_2': ''
                })

    # 각 카테고리 내에서 정책명 정렬
    for region in result:
        for category in result[region]:
            result[region][category].sort(key=lambda x: x['name'])

    return result
