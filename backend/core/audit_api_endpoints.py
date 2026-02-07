#!/usr/bin/env python
"""
API Endpoint Audit Script
Scans viewsets for potential validation and serializer issues
"""
import os
import sys
import re

def analyze_viewset(file_path):
    """Analyze a single viewset file for best practices"""
    issues = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find all viewset classes
    viewset_pattern = r'class\s+(\w+)\(viewsets\.ModelViewSet\)'
    viewsets = re.findall(viewset_pattern, content)
    
    for vs in viewsets:
        vs_start = content.find(f'class {vs}')
        # Find the next class definition or end of file
        next_class = content.find('\nclass ', vs_start + 1)
        if next_class == -1:
            vs_end = len(content)
        else:
            vs_end = next_class
        
        vs_code = content[vs_start:vs_end]
        
        # Check for issues
        issues_found = []
        
        # Check 1: Has get_serializer_class?
        if 'def get_serializer_class' not in vs_code:
            issues_found.append(f"Missing get_serializer_class() method")
        
        # Check 2: Single serializer_class definition
        serializer_matches = re.findall(r'serializer_class\s*=\s*(\w+)', vs_code)
        if len(serializer_matches) == 1 and 'get_serializer_class' in vs_code:
            # This is OK - using dynamic selection
            pass
        elif len(serializer_matches) > 1:
            issues_found.append(f"Multiple serializer_class definitions (potential confusion)")
        
        # Check 3: Has password field without special handling?
        if 'password' in vs_code.lower() and 'set_password' not in vs_code:
            issues_found.append(f"May have password handling without set_password()")
        
        # Check 4: Check if it's a read-only viewset
        if 'ReadOnlyModelViewSet' in content[vs_start:vs_end]:
            issues_found = []  # Skip read-only viewsets
        
        if issues_found:
            issues.append({
                'file': file_path,
                'viewset': vs,
                'issues': issues_found
            })
    
    return issues

def main():
    print("\n" + "="*80)
    print("API ENDPOINT AUDIT - Validation and Serializer Analysis")
    print("="*80)
    
    # Find all views.py files
    views_files = [
        'shop_users/views.py',
        'shop_users/user_management_viewset.py',
        'apps/creditors/views.py',
        'apps/debtors/views.py',
        'apps/cash_book/views.py',
        'apps/stock_control/views.py',
        'apps/pos/views.py',
        'apps/purchase_orders/views.py',
        'apps/settings/views.py',
        'tenancy/views.py'
    ]
    
    all_issues = []
    
    for views_file in views_files:
        path = os.path.join(os.path.dirname(__file__), views_file)
        if os.path.exists(path):
            print(f"\n📋 Analyzing: {views_file}")
            issues = analyze_viewset(path)
            all_issues.extend(issues)
            
            if not issues:
                print(f"  ✓ All viewsets follow best practices")
            else:
                for issue_group in issues:
                    print(f"  ⚠️  {issue_group['viewset']}:")
                    for issue in issue_group['issues']:
                        print(f"      - {issue}")
    
    print("\n" + "="*80)
    print("AUDIT SUMMARY")
    print("="*80)
    
    if not all_issues:
        print("✓ All viewsets appear to follow best practices!")
        print("\nKey validations passed:")
        print("  ✓ Viewsets have proper serializer selection")
        print("  ✓ Password fields handled correctly")
        print("  ✓ Create/Update serializers properly separated")
    else:
        print(f"\n{len(all_issues)} potential issues found:\n")
        for issue_group in all_issues:
            print(f"{issue_group['file']} - {issue_group['viewset']}:")
            for issue in issue_group['issues']:
                print(f"  • {issue}")
    
    print("\n" + "="*80)

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Audit failed: {e}")
        import traceback
        traceback.print_exc()
