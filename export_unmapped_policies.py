"""
Export list of policies that don't have specific URLs yet
User can fill in the URLs and use this to update MANUAL_POLICY_URL_MAPPING
"""
import sys
import json
sys.stdout.reconfigure(encoding='utf-8')

from chatbot_web.rag_system.policy_metadata import scan_policy_pdfs

print("Scanning all policies...")
policies = scan_policy_pdfs()

# Collect all unique unmapped policies
unmapped = {}

for region in policies:
    for category in policies[region]:
        for policy in policies[region][category]:
            # If URL doesn't contain wlfareInfoId, it's using the default search page
            if 'wlfareInfoId' not in policy['url']:
                policy_name = policy['name']
                if policy_name not in unmapped:
                    unmapped[policy_name] = {
                        'regions': [region],
                        'categories': [category],
                        'example_file': policy['filename']
                    }
                else:
                    if region not in unmapped[policy_name]['regions']:
                        unmapped[policy_name]['regions'].append(region)
                    if category not in unmapped[policy_name]['categories']:
                        unmapped[policy_name]['categories'].append(category)

print(f"\nFound {len(unmapped)} unique unmapped policies\n")

# Export to text file for user to fill in
output_file = 'unmapped_policies.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write("="*80 + "\n")
    f.write("정책 URL 매핑이 필요한 정책 목록\n")
    f.write("="*80 + "\n\n")
    f.write("각 정책에 대해 복지로 사이트에서 URL을 찾아 아래 형식으로 추가하세요:\n")
    f.write("'정책명': 'https://www.bokjiro.go.kr/.../moveTWAT52011M.do?wlfareInfoId=WLF00000XXX',\n\n")
    f.write("="*80 + "\n\n")

    # Sort by number of regions (more common policies first)
    sorted_policies = sorted(
        unmapped.items(),
        key=lambda x: len(x[1]['regions']),
        reverse=True
    )

    for i, (policy_name, info) in enumerate(sorted_policies, 1):
        regions_str = ', '.join(info['regions'])
        categories_str = ', '.join(info['categories'])

        f.write(f"{i}. {policy_name}\n")
        f.write(f"   지역: {regions_str}\n")
        f.write(f"   카테고리: {categories_str}\n")
        f.write(f"   예시 파일: {info['example_file']}\n")
        f.write(f"   URL: [복지로에서 찾아서 입력]\n")
        f.write(f"\n")

print(f"[OK] Exported to {output_file}")
print(f"\n다음 단계:")
print(f"1. {output_file} 파일을 열어서 각 정책의 URL을 찾아 입력하세요")
print(f"2. 복지로 사이트(www.bokjiro.go.kr)에서 정책을 검색하세요")
print(f"3. URL의 wlfareInfoId 파라미터를 복사하세요")
print(f"4. chatbot_web/rag_system/policy_metadata.py의 MANUAL_POLICY_URL_MAPPING에 추가하세요")

# Also export as JSON template for easy copy-paste
json_output = {}
for policy_name in sorted(unmapped.keys()):
    json_output[policy_name] = "https://www.bokjiro.go.kr/ssis-tbu/twataa/wlfareInfo/moveTWAT52011M.do?wlfareInfoId=WLF00000XXX"

json_file = 'unmapped_policies_template.json'
with open(json_file, 'w', encoding='utf-8') as f:
    json.dump(json_output, f, ensure_ascii=False, indent=2)

print(f"\n[OK] Also exported JSON template to {json_file}")
print(f"     (복지로에서 wlfareInfoId를 찾아서 WLF00000XXX 부분을 교체하세요)")
