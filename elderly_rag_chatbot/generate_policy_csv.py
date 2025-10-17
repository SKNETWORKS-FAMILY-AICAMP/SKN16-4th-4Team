"""
PDF-정책명-주제(1단계)-주제(2단계)-링크 CSV 파일 생성
사용자가 직접 수정할 수 있는 매핑 파일
"""
import sys
import csv
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')

from chatbot_web.rag_system.policy_metadata import load_pdf_policy_mapping, extract_policy_name, categorize_policy
from chatbot_web.rag_system.rag_config import MAIN_DATA_DIR

# Git commit message에서 추출한 정책명 매핑 로드
pdf_mapping = load_pdf_policy_mapping()

# CSV 데이터 수집
csv_data = []

# 각 지역 폴더 순회
for region_dir in MAIN_DATA_DIR.iterdir():
    if not region_dir.is_dir():
        continue

    region_name = region_dir.name

    # PDF 파일 찾기
    pdf_dir = region_dir / 'pdf'
    if not pdf_dir.exists():
        continue

    for pdf_file in sorted(pdf_dir.glob('*.pdf')):
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

        # 기본 URL (복지로 검색 페이지)
        default_url = 'https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52005M.do?page=1&orderBy=date&tabId=1&period=%EB%85%B8%EB%85%84'

        csv_data.append({
            'region': region_name,
            'pdf_filename': pdf_filename,
            'policy_name': policy_name,
            'category_1': category,
            'category_2': '',  # 사용자가 직접 입력
            'url': default_url,
            'notes': ''  # 메모 필드
        })

# CSV 파일로 저장
csv_file = Path(__file__).parent / 'policy_mapping.csv'

with open(csv_file, 'w', encoding='utf-8-sig', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'region', 'pdf_filename', 'policy_name',
        'category_1', 'category_2', 'url', 'notes'
    ])
    writer.writeheader()
    writer.writerows(csv_data)

print(f"[완료] {len(csv_data)}개 정책을 CSV 파일로 저장했습니다: {csv_file}")
print(f"\n다음 단계:")
print(f"1. {csv_file.name} 파일을 Excel로 열기")
print(f"2. 각 행의 정책명, 주제(1단계), 주제(2단계), URL을 수정")
print(f"3. 저장 (반드시 UTF-8 인코딩 유지)")
print(f"4. Django 서버 재시작하면 자동으로 반영됨")
print(f"\nCSV 파일 컬럼 설명:")
print(f"  - region: 지역명")
print(f"  - pdf_filename: PDF 파일명")
print(f"  - policy_name: 정책명 (수정 가능)")
print(f"  - category_1: 주제(1단계) - 대분류 (수정 가능)")
print(f"  - category_2: 주제(2단계) - 소분류 (직접 입력)")
print(f"  - url: 복지로 URL (수정 가능)")
print(f"  - notes: 메모 (선택사항)")
