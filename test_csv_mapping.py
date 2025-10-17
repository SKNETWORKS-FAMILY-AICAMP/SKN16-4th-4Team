"""
CSV 매핑 파일 테스트
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from chatbot_web.rag_system.policy_metadata import load_policy_csv_mapping, scan_policy_pdfs

# CSV 로드 테스트
print("=== CSV 매핑 로드 테스트 ===")
csv_mapping = load_policy_csv_mapping()

if csv_mapping:
    total_policies = sum(len(pdfs) for pdfs in csv_mapping.values())
    print(f"[OK] {len(csv_mapping)}개 지역의 {total_policies}개 정책 로드 성공\n")

    # 샘플 출력
    for region in list(csv_mapping.keys())[:2]:
        print(f"[{region}] 지역:")
        for pdf_name in list(csv_mapping[region].keys())[:3]:
            info = csv_mapping[region][pdf_name]
            print(f"  - PDF: {pdf_name}")
            print(f"    정책명: {info['policy_name']}")
            print(f"    주제(1단계): {info['category_1']}")
            print(f"    주제(2단계): {info['category_2']}")
            print(f"    URL: {info['url'][:60]}...")
        print()
else:
    print("[ERROR] CSV 파일이 없거나 로드에 실패했습니다.\n")

# scan_policy_pdfs 테스트
print("\n=== scan_policy_pdfs() 테스트 ===")
policies = scan_policy_pdfs()

if policies:
    total = sum(sum(len(cats) for cats in region.values()) for region in policies.values())
    print(f"[OK] {len(policies)}개 지역의 {total}개 정책 스캔 완료\n")

    # 샘플 출력
    for region in list(policies.keys())[:2]:
        print(f"[{region}] - {len(policies[region])} categories")
        for category in list(policies[region].keys())[:2]:
            print(f"  > {category}: {len(policies[region][category])}개")
            for policy in policies[region][category][:2]:
                print(f"    - {policy['name']}")
                if policy['category_2']:
                    print(f"      주제(2단계): {policy['category_2']}")
                print(f"      URL: {policy['url'][:60]}...")
        print()
else:
    print("[ERROR] 정책 스캔 실패\n")

print("\n=== 완료 ===")
print("CSV 파일을 Excel로 열어 정책명, 주제, URL을 수정하세요:")
print("  - policy_mapping.csv")
print("\n수정 후 Django 서버를 재시작하면 자동으로 반영됩니다.")
