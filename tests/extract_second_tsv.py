#!/usr/bin/env python3
"""Extract the SECOND sample_tsv_data (for update_measures) from original ecm_prep_test.py"""

# Read the original file
with open('tests/ecm_prep_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the SECOND occurrence of "cls.sample_tsv_data = {"
occurrences = []
for i, line in enumerate(lines):
    if 'cls.sample_tsv_data = {' in line:
        occurrences.append(i)

if len(occurrences) < 2:
    print(f"Only found {len(occurrences)} occurrence(s) of sample_tsv_data")
    exit(1)

start_idx = occurrences[1]  # Use the second occurrence
print(f"Found second sample_tsv_data at line {start_idx + 1}")

# Count braces to find the end
brace_count = 0
end_idx = None
for i in range(start_idx, len(lines)):
    line = lines[i]
    brace_count += line.count('{')
    brace_count -= line.count('}')
    if brace_count == 0 and i > start_idx:
        end_idx = i
        break

if end_idx is None:
    print("Could not find end of sample_tsv_data")
    exit(1)

print(f"End at line {end_idx + 1}, total lines: {end_idx - start_idx + 1}")

# Extract the data (remove the "cls." part)
tsv_lines = lines[start_idx:end_idx+1]
tsv_lines[0] = tsv_lines[0].replace('cls.sample_tsv_data', 'sample_tsv_data_update_measures')

# Remove leading spaces (the cls. line has 8 spaces, we want 0)
cleaned_lines = []
for line in tsv_lines:
    if line.startswith('        '):
        cleaned_lines.append(line[8:])
    else:
        cleaned_lines.append(line)

tsv_data_str = ''.join(cleaned_lines)

# Read the current time_sensitive_valuation_test_data.py to find where to insert
with open('tests/ecm_prep_test/test_data/time_sensitive_valuation_test_data.py', 'r', encoding='utf-8') as f:
    current_content = f.read()

# Find the location of the conversion function
insert_marker = '\n\ndef _convert_numpy_strings_to_python(obj):'
parts = current_content.split(insert_marker)

if len(parts) == 2:
    # Insert the new data before the conversion function
    new_content = parts[0] + '\n\n' + tsv_data_str + '\n' + insert_marker + parts[1]
    
    # Also update the conversion to include the new variable
    new_content = new_content.replace(
        '# Apply conversion to sample_tsv_data to ensure all numpy strings are converted to Python strings\nsample_tsv_data = _convert_numpy_strings_to_python(sample_tsv_data)',
        '''# Apply conversion to sample_tsv_data to ensure all numpy strings are converted to Python strings
sample_tsv_data = _convert_numpy_strings_to_python(sample_tsv_data)
sample_tsv_data_update_measures = _convert_numpy_strings_to_python(sample_tsv_data_update_measures)'''
    )
else:
    print("Could not find insertion point")
    exit(1)

# Write back
with open('tests/ecm_prep_test/test_data/time_sensitive_valuation_test_data.py', 'w', encoding='utf-8') as f:
    f.write(new_content)

print(f"Successfully added sample_tsv_data_update_measures")
