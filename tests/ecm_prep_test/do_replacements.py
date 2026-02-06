#!/usr/bin/env python3
"""Replace inline variable definitions with imports."""

# Read the file
with open('market_updates_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Initial line count: {len(lines)}")

# Define replacements as (start_line_0indexed, end_line_0indexed, replacement_text)
replacements = []

# Find and mark ok_frefr_measures_in (around lines 534-750)
for i, line in enumerate(lines):
    if i >= 533 and '# Sample refrigerant emissions measures to initialize below' in line:
        # Find the end
        for j in range(i+1, min(i+250, len(lines))):
            if '"low_gwp_refrigerant": "default"}]' in lines[j]:
                replacements.append((i, j, '    # Sample refrigerant emissions measures (imported from test_data)\n'))
                print(f"Found ok_frefr_measures_in: lines {i+1} to {j+1}")
                break
        break

# Find ok_measures_in (should be a large block around 1300+)
for i, line in enumerate(lines):
    if 'ok_measures_in = [{' in line and i > 1000:
        # Find the end - looking for the last closing bracket before ok_tpmeas_fullchk_in
        for j in range(i+1, min(i+900, len(lines))):
            if '"technology": ["resistance heat", "ASHP", "GSHP", "room AC"]}]' in lines[j]:
                replacements.append((i, j, '    # Sample measures definitions (imported from test_data)\n'))
                print(f"Found ok_measures_in: lines {i+1} to {j+1}")
                break
        break

# Find frefr_hp_rates
for i, line in enumerate(lines):
    if 'frefr_hp_rates = {' in line:
        for j in range(i+1, min(i+150, len(lines))):
            if lines[j].strip() == '}' and 'data (by scenario)' in lines[i:j]:
                replacements.append((i-1, j, '    # Exogenous HP switching rates (imported from test_data)\n'))
                print(f"Found frefr_hp_rates: lines {i} to {j+1}")
                break
        break

# Find frefr_fug_emissions
for i, line in enumerate(lines):
    if 'frefr_fug_emissions = {' in line:
        for j in range(i+1, min(i+200, len(lines))):
            if '"refrigerants": {}' in lines[j] and lines[j+1].strip() == '}':
                replacements.append((i-1, j+1, '    # Fugitive refrigerant emissions data (imported from test_data)\n'))
                print(f"Found frefr_fug_emissions: lines {i} to {j+2}")
                break
        break

# Sort replacements by start line (descending) to maintain line numbers
replacements.sort(key=lambda x: x[0], reverse=True)

# Apply replacements
for start, end, replacement in replacements:
    print(f"Removing lines {start+1} to {end+1}, replacing with comment")
    del lines[start:end+1]
    lines.insert(start, replacement)

print(f"Final line count: {len(lines)}")
print(f"Lines removed: {4336 - len(lines)}")

# Write back
with open('market_updates_test.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done!")
