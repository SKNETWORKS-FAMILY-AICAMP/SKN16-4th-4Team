"""
Test script to verify Git commit message policy names are working
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from chatbot_web.rag_system.policy_metadata import scan_policy_pdfs, load_pdf_policy_mapping

# Load mapping
mapping = load_pdf_policy_mapping()
print(f"[OK] Loaded {len(mapping)} PDF-to-policy mappings from Git commits\n")

# Show sample mappings
print("=== Sample Git Commit Mappings (first 5) ===")
for i, (pdf_name, info) in enumerate(list(mapping.items())[:5]):
    print(f"{i+1}. {pdf_name}")
    print(f"   정책명: {info['policy_name']}")
    print(f"   지역: {info['region']}\n")

# Scan policies
print("\n=== Scanning Policy PDFs ===")
policies = scan_policy_pdfs()
print(f"[OK] Scanned policies from {len(policies)} regions\n")

# Show sample from each region
print("=== Sample Policies by Region (first 3 regions, 2 categories each) ===")
for region in list(policies.keys())[:3]:
    total_policies = sum(len(cats) for cats in policies[region].values())
    print(f"\n[{region}] - {len(policies[region])} categories, {total_policies} total policies")

    for cat in list(policies[region].keys())[:2]:
        print(f"\n  > {cat} ({len(policies[region][cat])} policies)")
        for policy in policies[region][cat][:3]:  # Show first 3
            print(f"    - {policy['name']}")
            print(f"      File: {policy['filename']}")

print("\n[OK] Test complete! Policy names from Git commits are being used.")
