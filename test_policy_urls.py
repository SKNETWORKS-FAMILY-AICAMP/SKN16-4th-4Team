"""
Test script to verify policy URL matching system
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from chatbot_web.rag_system.policy_metadata import find_policy_url, scan_policy_pdfs

# Test policy names and their expected URL matching
test_policies = [
    '기초연금',
    '의료급여',
    '노인장기요양보험',
    '노인일자리',
    '경로우대',
    '노인맞춤돌봄서비스',
    '재난적의료비',
    '보훈수당',
    '화장장려금 지원',  # Not in POLICY_METADATA, should use search page
    '저소득틈새지원사업',  # Not in POLICY_METADATA, should use search page
]

print("=== URL Matching Test ===\n")
for policy_name in test_policies:
    url = find_policy_url(policy_name)
    is_specific = 'wlfareInfoId' in url
    url_type = "[SPECIFIC URL]" if is_specific else "[SEARCH PAGE]"
    print(f"{url_type} {policy_name}")
    print(f"  -> {url[:80]}..." if len(url) > 80 else f"  -> {url}")
    print()

print("\n=== Scanning All Policies and Checking URL Distribution ===\n")
policies = scan_policy_pdfs()

specific_count = 0
search_count = 0
policy_examples = {'specific': [], 'search': []}

for region in policies:
    for category in policies[region]:
        for policy in policies[region][category]:
            if 'wlfareInfoId' in policy['url']:
                specific_count += 1
                if len(policy_examples['specific']) < 5:
                    policy_examples['specific'].append((policy['name'], policy['url']))
            else:
                search_count += 1
                if len(policy_examples['search']) < 5:
                    policy_examples['search'].append((policy['name'], policy['url']))

total = specific_count + search_count
print(f"Total policies: {total}")
print(f"  - Matched to specific URLs: {specific_count} ({specific_count/total*100:.1f}%)")
print(f"  - Using search page: {search_count} ({search_count/total*100:.1f}%)")

print("\n=== Examples of Matched Policies ===")
for name, url in policy_examples['specific']:
    print(f"  - {name}")
    print(f"    {url[:80]}...")

print("\n=== Examples of Unmatched Policies (using search page) ===")
for name, url in policy_examples['search'][:3]:
    print(f"  - {name}")

print("\n[INFO] To add specific URLs for unmatched policies:")
print("1. Add them to MANUAL_POLICY_URL_MAPPING in policy_metadata.py")
print("2. Format: 'Policy Name': 'https://www.bokjiro.go.kr/...?wlfareInfoId=WLF00000XXX'")
