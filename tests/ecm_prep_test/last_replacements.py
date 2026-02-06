#!/usr/bin/env python3
"""Last batch of replacements."""

with open('market_updates_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Initial line count: {len(lines)}")

replacements = []

# Find ok_hp_measures_in (should have b1/b2 dictionaries)
for i, line in enumerate(lines):
    if 'ok_hp_measures_in = [{' in line:
        for j in range(i+1, min(i+200, len(lines))):
            if '"2010": -0.12}}]' in lines[j] and '"b2"' in lines[j-5:j+1]:
                replacements.append((i, j, '    # HP measures raw data (imported from test_data)\n'))
                print(f"Found ok_hp_measures_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find ok_tpmeas_fullchk_competechoiceout 
for i, line in enumerate(lines):
    if 'ok_tpmeas_fullchk_competechoiceout = [{' in line:
        # This has compete_choice_val references
        for j in range(i+1, min(i+200, len(lines))):
            if 'compete_choice_val[1]}]' in lines[j]:
                replacements.append((i, j, '    # Compete choice output data (imported from test_data)\n'))
                print(f"Found ok_tpmeas_fullchk_competechoiceout: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find ok_tpmeas_fullchk_supplydemandout
for i, line in enumerate(lines):
    if 'ok_tpmeas_fullchk_supplydemandout = [{' in line:
        for j in range(i+1, min(i+200, len(lines))):
            if '"adjusted energy (competed and captured)": {}}}]' in lines[j]:
                replacements.append((i, j, '    # Supply-demand output data (imported from test_data)\n'))
                print(f"Found ok_tpmeas_fullchk_supplydemandout: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find ok_mapmas_partchck_msegout
for i, line in enumerate(lines):
    if 'ok_mapmas_partchck_msegout = [{' in line:
        for j in range(i+1, min(i+200, len(lines))):
            if '{"savings": {}, "total": {}}]' in lines[j]:
                replacements.append((i, j, '    # Map measures partial check output (imported from test_data)\n'))
                print(f"Found ok_mapmas_partchck_msegout: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find ok_partialmeas_out
for i, line in enumerate(lines):
    if 'ok_partialmeas_out = [{' in line:
        for j in range(i+1, min(i+200, len(lines))):
            if '"measure": 1}}]' in lines[j]:
                replacements.append((i, j, '    # Partial measures output data (imported from test_data)\n'))
                print(f"Found ok_partialmeas_out: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Sort and apply
replacements.sort(key=lambda x: x[0], reverse=True)

for start, end, replacement in replacements:
    print(f"Removing lines {start+1} to {end+1}")
    del lines[start:end+1]
    lines.insert(start, replacement)

print(f"Final line count: {len(lines)}")
print(f"Lines removed: {2577 - len(lines)}")
print(f"Total reduction from original 4410: {4410 - len(lines)} lines")

with open('market_updates_test.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done!")
