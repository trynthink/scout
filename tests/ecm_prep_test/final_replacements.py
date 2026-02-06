#!/usr/bin/env python3
"""Final batch of replacements."""

with open('market_updates_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f"Initial line count: {len(lines)}")

replacements = []

# Find ok_measures_in (very large, should be around line 1000-1800)
for i, line in enumerate(lines):
    if 'ok_measures_in = [{' in line and i > 800:
        for j in range(i+1, min(i+850, len(lines))):
            if '"technology": "ASHP"}]' in lines[j]:
                replacements.append((i, j, '    # Sample measures definitions (imported from test_data)\n'))
                print(f"Found ok_measures_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find failmeas_in
for i, line in enumerate(lines):
    if 'failmeas_in = [{' in line:
        for j in range(i+1, min(i+250, len(lines))):
            if '"technology": [None, "distribution transformers"]}]' in lines[j]:
                replacements.append((i, j, '    # Fail measures raw data (imported from test_data)\n'))
                print(f"Found failmeas_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find warnmeas_in 
for i, line in enumerate(lines):
    if 'warnmeas_in = [{' in line and '"warn measure' in lines[i+1]:
        for j in range(i+1, min(i+200, len(lines))):
            if '"external (LED)"]}]' in lines[j]:
                # Make sure this is the end of warnmeas_in, not another variable
                if 'warnmeas_in = [' in lines[j+1] or 'Measure(' in lines[j+1]:
                    replacements.append((i, j, '    # Warning measures raw data (imported from test_data)\n'))
                    print(f"Found warnmeas_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                    break
        break

# Find ok_hp_measures_in
for i, line in enumerate(lines):
    if 'ok_hp_measures_in = [{' in line:
        for j in range(i+1, min(i+200, len(lines))):
            if 'b2.*2010.*-0.12.*}}]' in ''.join(lines[j:min(j+5, len(lines))]).replace(' ', '').replace('\n', ''):
                replacements.append((i, j, '    # HP measures raw data (imported from test_data)\n'))
                print(f"Found ok_hp_measures_in: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find ok_tpmeas_fullchk_competechoiceout
for i, line in enumerate(lines):
    if 'ok_tpmeas_fullchk_competechoiceout = [{' in line:
        for j in range(i+1, min(i+200, len(lines))):
            if 'compete_choice_val[1]' in lines[j] and lines[j+1].strip().startswith('}'):
                # Find the actual end
                for k in range(j+1, min(j+5, len(lines))):
                    if lines[k].strip() == '}]':
                        replacements.append((i, k, '    # Compete choice output data (imported from test_data)\n'))
                        print(f"Found ok_tpmeas_fullchk_competechoiceout: lines {i+1} to {k+1} ({k-i+1} lines)")
                        break
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
            if '"measure": 1}}]' in lines[j] and 'lifetime' in lines[j-5:j+1]:
                replacements.append((i, j, '    # Partial measures output data (imported from test_data)\n'))
                print(f"Found ok_partialmeas_out: lines {i+1} to {j+1} ({j-i+1} lines)")
                break
        break

# Find ok_map_frefr_mkts_out
for i, line in enumerate(lines):
    if 'ok_map_frefr_mkts_out = [' in line:
        for j in range(i+1, min(i+150, len(lines))):
            if '0.0000058703}}}' in lines[j] and ']' in lines[j+1]:
                replacements.append((i, j+1, '    # Refrigerant emissions map markets output (imported from test_data)\n'))
                print(f"Found ok_map_frefr_mkts_out: lines {i+1} to {j+2} ({j+1-i+1} lines)")
                break
        break

# Sort and apply
replacements.sort(key=lambda x: x[0], reverse=True)

for start, end, replacement in replacements:
    print(f"Removing lines {start+1} to {end+1}")
    del lines[start:end+1]
    lines.insert(start, replacement)

print(f"Final line count: {len(lines)}")
print(f"Lines removed: {3806 - len(lines)}")

with open('market_updates_test.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Done!")
