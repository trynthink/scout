#!/usr/bin/env python3

"""Final script to update market_updates_test.py with imports and remove inline definitions"""

with open('tests/ecm_prep_test/market_updates_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print(f'Original file: {len(lines)} lines')

# Variables to remove with their exact line ranges (1-indexed inclusive, from final_extraction.py)
#  ok_fmeth_measures_in                          L 158- 245
#  ok_frefr_measures_in                          L 609- 824
# frefr_fug_emissions                           L 954-1092
#  ok_measures_in                                L1418-2185
#  ok_distmeas_in                                L2234-2328
#  failmeas_in                                   L2379-2585
#  warnmeas_in                                   L2593-2748
#  ok_hp_measures_in                             L2753-2844
#  compete_choice_val starts at L2864 (need to find end)
#  ok_tpmeas_fullchk_competechoiceout            L2891-3013
#  ok_tpmeas_fullchk_supplydemandout             L3056-3208
#  ok_mapmas_partchck_msegout                    L3209-3304
#  ok_partialmeas_out                            L3362-3453
#  ok_map_frefr_mkts_out                         L3518-3619

# Convert to 0-indexed and subtract 1 from end (inclusive range to Python slice)
removals = [
    ('ok_fmeth_measures_in', 157, 245),
    ('ok_frefr_measures_in', 608, 824),
    ('frefr_fug_emissions', 953, 1092),
    ('ok_measures_in', 1417, 2185),
    ('ok_distmeas_in', 2233, 2328),
    ('compete_choice_val', 2863, 2891),  # Includes compete_choice_val (lines 2864-2890)
    ('failmeas_in', 2378, 2585),
    ('warnmeas_in', 2592, 2748),
    ('ok_hp_measures_in', 2752, 2844),
    ('ok_tpmeas_fullchk_competechoiceout', 2890, 3013),
    ('ok_tpmeas_fullchk_supplydemandout', 3055, 3208),
    ('ok_mapmas_partchck_msegout', 3208, 3304),
    ('ok_partialmeas_out', 3361, 3453),
    ('ok_map_frefr_mkts_out', 3517, 3619),
]

# Sort by start line in reverse order (remove from bottom to top)
removals.sort(key=lambda x: x[1], reverse=True)

# Remove variables from bottom to top
new_lines = lines.copy()
for var_name, start, end in removals:
    print(f'Removing {var_name:45s} L{start+1:4d}-{end:4d} ({end-start} lines)')
    del new_lines[start:end]

print(f'After removals: {len(new_lines)} lines')

# Now update the imports (at line 18, after the existing imports)
new_import_block = """    ok_fmeth_measures_in,
    ok_frefr_measures_in,
    frefr_fug_emissions,
    ok_measures_in,
    ok_distmeas_in,
    failmeas_in,
    warnmeas_in,
    ok_hp_measures_in,
    ok_tpmeas_fullchk_competechoiceout,
    ok_tpmeas_fullchk_supplydemandout,
    ok_mapmas_partchck_msegout,
    ok_partialmeas_out,
    ok_map_frefr_mkts_out,
"""

# Find the import block and add new imports
for i, line in enumerate(new_lines):
    if 'ok_tpmeas_partchk_msegout_state,' in line:
        # Insert new imports after this line
        new_lines.insert(i + 1, new_import_block)
        break

# Write the updated file
with open('tests/ecm_prep_test/market_updates_test.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'Final file: {len(new_lines)} lines')
print(f'Removed: {len(lines) - len(new_lines)} lines')
print('Update complete!')
