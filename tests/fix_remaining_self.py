#!/usr/bin/env python3
"""Fix remaining self. references in test files."""

import re
from pathlib import Path

files_to_fix = [
    'tests/ecm_prep_test/test_clean_up_test.py',
    'tests/ecm_prep_test/test_fill_parameters_test.py',
    'tests/ecm_prep_test/test_partition_microsegment_test.py',
]

def fix_file(filepath):
    """Fix self. references in a test file."""
    path = Path(filepath)
    content = path.read_text(encoding='utf-8')
    
    # Find the test function and its parameter name
    test_func_match = re.search(r'def test_\w+\((\w+)\):', content)
    if not test_func_match:
        print(f"No test function found in {filepath}")
        return False
    
    param_name = test_func_match.group(1)
    print(f"{path.name}: Using parameter '{param_name}'")
    
    # Replace self.assertEqual
    content = re.sub(r'self\.assertEqual\(', r'assert ', content)
    content = re.sub(r'self\.assertDictEqual\(', r'assert ', content)
    
    # Fix the pattern: assert x, y) -> assert x == y
    # This is tricky because assertEqual takes 2 args
    # Let me just replace more carefully
    content = path.read_text(encoding='utf-8')  # Re-read
    
    # Replace self.assertEqual(a, b) with assert a == b
    content = re.sub(
        r'self\.assertEqual\((.*?),\s*(.*?)\)(?!\))',
        r'assert \1 == \2',
        content
    )
    content = re.sub(
        r'self\.assertDictEqual\((.*?),\s*(.*?)\)(?!\))',
        r'assert \1 == \2',
        content
    )
    
    # Replace self.variable with param_name["variable"]
    content = re.sub(rf'\bself\.(\w+)', rf'{param_name}["\1"]', content)
    
    path.write_text(content, encoding='utf-8')
    print(f"  ✓ Fixed {path.name}")
    return True

if __name__ == '__main__':
    for filepath in files_to_fix:
        fix_file(filepath)
    print("\nDone!")
