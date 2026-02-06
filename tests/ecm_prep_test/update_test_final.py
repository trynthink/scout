#!/usr/bin/env python3

"""Final update script with correct line ranges"""

with open('tests/ecm_prep_test/market_updates_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Original file: {len(lines)} lines')

# From final_extraction.py - these are 1-indexed inclusive start and end lines
# Need to convert to Python slice notation: [start-1:end]
vars_to_remove = [
    ('ok_fmeth_measures_in', 158, 245),
    ('ok_frefr_measures_in', 609, 824),
    ('frefr_fug_emissions', 954, 1092),
    ('ok_measures_in', 1418, 2185),
    ('ok_distmeas_in', 2234, 2328),
    ('compete_choice_val', 2864, 2890),  # Ends at line 2890, not 2891
    ('failmeas_in', 2379, 2585),
    ('warnmeas_in', 2593, 2748),
    ('ok_hp_measures_in', 2753, 2844),
    ('ok_tpmeas_fullchk_competechoiceout', 2891, 3013),
    ('ok_tpmeas_fullchk_supplydemandout', 3056, 3208),
    ('ok_mapmas_partchck_msegout', 3209, 3304),
    ('ok_partialmeas_out', 3362, 3453),
    ('ok_map_frefr_mkts_out', 3518, 3619),
]

# Sort by start line in REVERSE order (remove from bottom to top)
vars_to_remove.sort(key=lambda x: x[1], reverse=True)

# Remove variables from bottom to top
new_lines = lines.copy()
for var_name, start_1idx, end_1idx in vars_to_remove:
    # Convert to 0-indexed Python slice: [start-1:end]
    start_0idx = start_1idx - 1
    end_slice = end_1idx  # Python slice end is exclusive, so we use end_1idx directly
    
    num_lines = end_slice - start_0idx
    print(f'Removing {var_name:45s} lines {start_1idx:4d}-{end_1idx:4d} ({num_lines} lines)')
    del new_lines[start_0idx:end_slice]

print(f'\nAfter removals: {len(new_lines)} lines (removed {len(lines) - len(new_lines)} lines)')

# Update imports - find the line with ok_tpmeas_partchk_msegout_state and add new imports after it
new_import_lines = [
    "    ok_fmeth_measures_in,\n",
    "    ok_frefr_measures_in,\n",
    "    frefr_fug_emissions,\n",
    "    ok_measures_in,\n",
    "    ok_distmeas_in,\n",
    "    failmeas_in,\n",
    "    warnmeas_in,\n",
    "    ok_hp_measures_in,\n",
    "    ok_tpmeas_fullchk_competechoiceout,\n",
    "    ok_tpmeas_fullchk_supplydemandout,\n",
    "    ok_mapmas_partchck_msegout,\n",
    "    ok_partialmeas_out,\n",
    "    ok_map_frefr_mkts_out,\n",
]

# Find insertion point
for i, line in enumerate(new_lines):
    if 'ok_tpmeas_partchk_msegout_state,' in line:
        # Insert after this line
        for j, new_import in enumerate(new_import_lines):
            new_lines.insert(i + 1 + j, new_import)
        print(f'Inserted {len(new_import_lines)} new import lines at line {i+2}')
        break

print(f'Final file: {len(new_lines)} lines')

# Write updated file
with open('tests/ecm_prep_test/market_updates_test.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Update complete!')
