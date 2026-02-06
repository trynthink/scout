#!/usr/bin/env python3
"""Remove the last 4 variables."""

with open('market_updates_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Initial line count: {len(lines)}")

replacements = []

# Manually specify the line ranges based on grep results
# ok_hp_measures_in starts at 1021 (0-indexed: 1020)
for i in range(1020, min(1200, len(lines))):
    if lines[i].strip().startswith('ok_hp_measures_in = [{'):
        for j in range(i+1, min(i+150, len(lines))):
            if '"2010": -0.12}}]' in lines[j]:
                replacements.append((i, j, '    # HP measures raw data (imported from test_data)\n'))
                print(f"Found ok_hp_measures_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# ok_tpmeas_fullchk_competechoiceout starts at 1159 (0-indexed: 1158)
for i in range(1155, min(1200, len(lines))):
    if lines[i].strip().startswith('ok_tpmeas_fullchk_competechoiceout = [{'):
        for j in range(i+1, min(i+180, len(lines))):
            if 'compete_choice_val[1]}]' in lines[j]:
                replacements.append((i, j, '    # Compete choice output data (imported from test_data)\n'))
                print(f"Found ok_tpmeas_fullchk_competechoiceout: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# ok_tpmeas_fullchk_supplydemandout starts at 1324 (0-indexed: 1323)
for i in range(1320, min(1400, len(lines))):
    if lines[i].strip().startswith('ok_tpmeas_fullchk_supplydemandout = [{'):
        for j in range(i+1, min(i+160, len(lines))):
            if '"adjusted energy (competed and captured)": {}}}]' in lines[j]:
                replacements.append((i, j, '    # Supply-demand output data (imported from test_data)\n'))
                print(f"Found ok_tpmeas_fullchk_supplydemandout: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# ok_mapmas_partchck_msegout starts at 1477 (0-indexed: 1476)
for i in range(1470, min(1550, len(lines))):
    if lines[i].strip().startswith('ok_mapmas_partchck_msegout = [{'):
        for j in range(i+1, min(i+160, len(lines))):
            if '{"savings": {}, "total": {}}]' in lines[j]:
                replacements.append((i, j, '    # Map measures partial check output (imported from test_data)\n'))
                print(f"Found ok_mapmas_partchck_msegout: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Sort and apply
replacements.sort(key=lambda x: x[0], reverse=True)

for start, end, replacement in replacements:
    print(f"Removing lines {start+1} to {end+1}")
    del lines[start:end+1]
    lines.insert(start, replacement)

print(f"Final line count: {len(lines)}")
print(f"Lines removed: {2486 - len(lines)}")
print(f"Total reduction from original 4410: {4410 - len(lines)} lines ({((4410 - len(lines))/4410*100):.1f}% reduction)")

with open('market_updates_test.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("All replacements complete!")
