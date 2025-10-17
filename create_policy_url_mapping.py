"""
Git commit message를 기반으로 PDF 파일과 정책명 매핑을 생성하는 스크립트
"""
import os
import json
from pathlib import Path

# Git 로그에서 추출한 데이터 파싱
def parse_git_commits(git_log_file):
    """
    Git commit 로그 파일을 파싱하여 PDF와 정책명 매핑 생성
    """
    pdf_to_policy = {}

    with open(git_log_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_policy_name = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Commit message 라인 (정책명)
        if '|' in line and not line.startswith('data/'):
            parts = line.split('|')
            if len(parts) >= 2:
                current_policy_name = parts[1].strip()

        # PDF 파일 경로 라인
        elif line.startswith('data/복지로/') and line.endswith('.pdf'):
            if current_policy_name and current_policy_name != 'Merge branch':
                # 파일명만 추출
                pdf_filename = Path(line).name
                # 지역 추출
                region = line.split('/')[1]

                pdf_to_policy[pdf_filename] = {
                    'policy_name': current_policy_name,
                    'region': region,
                    'full_path': line
                }

    return pdf_to_policy


def main():
    # Git 로그 파일 경로
    git_log_file = Path(__file__).parent.parent / 'git_commits_pdfs.txt'

    if not git_log_file.exists():
        print(f"Git log file not found: {git_log_file}")
        return

    # PDF와 정책명 매핑 생성
    pdf_to_policy = parse_git_commits(git_log_file)

    print(f"\n총 {len(pdf_to_policy)}개의 PDF-정책 매핑 생성됨\n")

    # 샘플 출력
    print("=== 샘플 매핑 (처음 20개) ===")
    for i, (pdf_name, info) in enumerate(list(pdf_to_policy.items())[:20]):
        print(f"{i+1}. [{info['region']}] {pdf_name}")
        print(f"   정책명: {info['policy_name']}\n")

    # JSON 파일로 저장
    output_file = Path(__file__).parent / 'chatbot_web' / 'rag_system' / 'policy_pdf_mapping.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pdf_to_policy, f, ensure_ascii=False, indent=2)

    print(f"\n매핑 데이터 저장 완료: {output_file}")

    # 통계 출력
    regions = {}
    for info in pdf_to_policy.values():
        region = info['region']
        regions[region] = regions.get(region, 0) + 1

    print("\n=== 지역별 통계 ===")
    for region, count in sorted(regions.items()):
        print(f"{region}: {count}개")

    print("\n다음 단계:")
    print("1. policy_pdf_mapping.json 파일을 확인하세요")
    print("2. 복지로 사이트에서 정책 ID를 찾아서 URL을 매핑하려면")
    print("   복지로 Open API를 사용하거나 수동으로 매핑해야 합니다")
    print("3. 주요 정책만 먼저 URL을 매핑하고, 나머지는 검색 페이지로 연결하세요")


if __name__ == '__main__':
    main()
