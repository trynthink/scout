#!/usr/bin/env python3
"""
Helper script to assist with converting unittest test classes to pytest.

This script helps identify the line numbers where each test class starts and ends
in the original ecm_prep_test.py file, making it easier to extract and convert them.
"""

import re
from pathlib import Path


def find_test_classes(filepath):
    """Find all test classes in the file with their line numbers."""
    # Custom filename mappings for special cases
    custom_filenames = {
        'MergeMeasuresandApplyBenefitsTest': 'test_merge_measures.py',
        'MarketUpdatesTest': 'test_market_updates.py',
        'TimeSensitiveValuationTest': 'test_time_sensitive_valuation.py',
        'UpdateMeasuresTest': 'test_update_measures.py',
    }
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    classes = []
    current_class = None
    
    for line_num, line in enumerate(lines, start=1):
        # Look for class definitions
        match = re.match(r'^class (\w+Test)\(unittest\.TestCase', line)
        if match:
            # If we were tracking a previous class, save its end line
            if current_class:
                current_class['end_line'] = line_num - 1
                classes.append(current_class)
            
            # Start tracking new class
            class_name = match.group(1)
            
            # Check for custom filename mapping
            if class_name in custom_filenames:
                pytest_filename = custom_filenames[class_name]
            else:
                # Convert CamelCase to snake_case
                base_name = re.sub(r'Test$', '', class_name)
                snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', base_name).lower()
                pytest_filename = f"test_{snake_case}.py"
            
            current_class = {
                'name': class_name,
                'start_line': line_num,
                'end_line': None,
                'pytest_filename': pytest_filename
            }
    
    # Don't forget the last class
    if current_class:
        current_class['end_line'] = len(lines)
        classes.append(current_class)
    
    return classes


def convert_class_name(unittest_name):
    """Convert unittest class name to pytest convention."""
    # Remove 'Test' suffix if present, convert to PascalCase with 'Test' prefix
    base_name = re.sub(r'Test$', '', unittest_name)
    return f"Test{base_name}"


def suggest_conversion_order(classes):
    """Suggest an order for converting classes based on size."""
    # Calculate approximate sizes
    for cls in classes:
        cls['size'] = cls['end_line'] - cls['start_line']
    
    # Sort by size (smallest first)
    return sorted(classes, key=lambda x: x['size'])


def count_lines_in_file(filepath):
    """Count number of lines in a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return len(f.readlines())
    except Exception:
        return 0


def main():
    """Main function."""
    # Path to original file (now in archive)
    original_file = Path(__file__).parent / "archive" / "ecm_prep_test_ORIGINAL.py"
    
    if not original_file.exists():
        print(f"Error: Could not find {original_file}")
        return
    
    print("=" * 80)
    print("ECM Prep Test Class Conversion Helper")
    print("=" * 80)
    print()
    
    # Find all test classes
    classes = find_test_classes(original_file)
    
    print(f"Found {len(classes)} test classes in {original_file.name}")
    print()
    
    # Show conversion status
    converted_dir = Path(__file__).parent
    
    print("Conversion Status:")
    print("-" * 115)
    print(f"{'Class Name':<35} {'Line Range':<18} {'Old Lines':<12} {'New Lines':<12} {'Line Change':<12} {'Status'}")
    print("-" * 115)
    
    converted_count = 0
    total_original_lines_converted = 0
    total_new_lines = 0
    
    for cls in classes:
        original_lines = cls['end_line'] - cls['start_line']
        target_file = converted_dir / cls['pytest_filename']
        line_range = f"{cls['start_line']}-{cls['end_line']}"
        old_lines_str = str(original_lines)
        
        if target_file.exists():
            converted_count += 1
            new_lines = count_lines_in_file(target_file)
            total_new_lines += new_lines
            total_original_lines_converted += original_lines
            
            # Calculate line change percentage (positive means increase, negative means reduction)
            if original_lines > 0:
                line_change = ((new_lines - original_lines) / original_lines) * 100
                line_change_str = f"{line_change:>+6.1f}%"
            else:
                line_change_str = "N/A"
            
            status = "[DONE]"
            new_line_info = str(new_lines)
        else:
            status = "[TODO]"
            new_line_info = "-"
            line_change_str = "-"
        
        print(f"{cls['name']:<35} {line_range:<18} {old_lines_str:<12} {new_line_info:<12} {line_change_str:<12} {status}")
    
    print("-" * 115)
    
    # Calculate overall statistics
    if converted_count > 0:
        overall_change = ((total_new_lines - total_original_lines_converted) / total_original_lines_converted) * 100
        print(f"Progress: {converted_count}/{len(classes)} classes converted ({converted_count*100//len(classes)}%)")
        print(f"Converted so far: {total_original_lines_converted:,} original -> {total_new_lines:,} new (change: {overall_change:+.1f}%)")
        
        # Calculate remaining work
        remaining_lines = sum(cls['end_line'] - cls['start_line'] 
                            for cls in classes 
                            if not (Path(__file__).parent / cls['pytest_filename']).exists())
        print(f"Remaining: {remaining_lines:,} lines in {len(classes) - converted_count} classes")
    else:
        print(f"Progress: {converted_count}/{len(classes)} classes converted (0%)")
    
    print()
    
    # Show suggested order
    print("Suggested Conversion Order (smallest to largest):")
    print("-" * 80)
    ordered = suggest_conversion_order(classes)
    
    for i, cls in enumerate(ordered, 1):
        size = cls['end_line'] - cls['start_line']
        target_file = converted_dir / cls['pytest_filename']
        if not target_file.exists():
            print(f"{i:2}. {cls['name']:<40} ({size:>5} lines)")
            print(f"    Lines {cls['start_line']}-{cls['end_line']}")
            print(f"    Target: {cls['pytest_filename']}")
            print()


if __name__ == "__main__":
    main()
