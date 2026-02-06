#!/usr/bin/env python3
"""Continue replacing inline variable definitions."""

with open('market_updates_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Initial line count: {len(lines)}")

replacements = []

# Find frefr_hp_rates
for i, line in enumerate(lines):
    if 'frefr_hp_rates = {' in line and i > 500:
        for j in range(i+1, min(i+150, len(lines))):
            if lines[j].strip() == '}' and j > i + 80:  # Should be around 90-100 lines
                # Include the preceding comment line if it exists
                start_line = i-1 if '# Sample exogenous HP switching rates' in lines[i-1] else i
                replacements.append((start_line, j, '    # Exogenous HP switching rates (imported from test_data)\n'))
                print(f"Found frefr_hp_rates: lines {start_line+1} to {j+1} ({j-start_line+1} lines)")
                break
        break

# Find frefr_fug_emissions
for i, line in enumerate(lines):
    if 'frefr_fug_emissions = {' in line and i > 500:
        for j in range(i+1, min(i+200, len(lines))):
            if '"R-134a": 1430.0' in lines[j]:
                # Find the closing braces
                for k in range(j+1, min(j+5, len(lines))):
                    if lines[k].strip() == '}' and lines[k+1].strip() == '}':
                        start_line = i-1 if '# Hard code sample fugitive refrigerant emissions' in lines[i-1] else i
                        replacements.append((start_line, k+1, '    # Fugitive refrigerant emissions data (imported from test_data)\n'))
                        print(f"Found frefr_fug_emissions: lines {start_line+1} to {k+2} ({k+1-start_line+1} lines)")
                        break
                break
        break

# Find ok_measures_in (large, around 700-800 lines)
for i, line in enumerate(lines):
    if 'ok_measures_in = [{' in line and i > 1000:
        for j in range(i+1, min(i+900, len(lines))):
            if '"technology": "ASHP"}]' in lines[j] and '"climate_zone": ["CT", "NH"]' in lines[j-5:j]:
                replacements.append((i, j, '    # Sample measures definitions (imported from test_data)\n'))
                print(f"Found ok_measures_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find ok_distmeas_in
for i, line in enumerate(lines):
    if 'ok_distmeas_in = [{' in line and 'distrib measure' in lines[i+1]:
        for j in range(i+1, min(i+150, len(lines))):
            if '"retro_rate": ["uniform", 0.01, 0.1]}]' in lines[j]:
                replacements.append((i, j, '    # Distribution measures raw data (imported from test_data)\n'))
                print(f"Found ok_distmeas_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find failmeas_in
for i, line in enumerate(lines):
    if 'failmeas_in = [{' in line and 'fail measure mkts' in lines[i+1]:
        for j in range(i+1, min(i+250, len(lines))):
            if '"technology": [None, "distribution transformers"]}]' in lines[j] and 'fail measure missing data' in lines[j-10:j]:
                replacements.append((i, j, '    # Fail measures raw data (imported from test_data)\n'))
                print(f"Found failmeas_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find warnmeas_in
for i, line in enumerate(lines):
    if 'warnmeas_in = [{' in line and 'warn measure' in lines[i+1]:
        for j in range(i+1, min(i+200, len(lines))):
            if '"external (LED)"]}]' in lines[j] and 'warn measure 3' in lines[j-50:j]:
                replacements.append((i, j, '    # Warning measures raw data (imported from test_data)\n'))
                print(f"Found warnmeas_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Sort and apply
replacements.sort(key=lambda x: x[0], reverse=True)

for start, end, replacement in replacements:
    print(f"Removing lines {start+1} to {end+1}")
    del lines[start:end+1]
    lines.insert(start, replacement)

print(f"Final line count: {len(lines)}")
print(f"Lines removed: {4120 - len(lines)}")

with open('market_updates_test.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done!")
