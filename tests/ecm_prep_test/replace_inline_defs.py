#!/usr/bin/env python3
"""Script to replace inline definitions with imported variables."""

import re

# Read the file
with open('market_updates_test.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Define the replacements (0-indexed line numbers)
# Format: (start_line, end_line, comment_to_insert)
replacements = [
    (171, 259, "    # Fugitive emissions data (imported from test_data)\n"),
    (608, 823, "    # Refrigerant emissions measures (imported from test_data)\n"),
    (841, 932, "    # Exogenous HP switching rates (imported from test_data)\n"),
    (953, 1089, "    # Fugitive refrigerant emissions data (imported)\n    # Set fug_emissions for each measure\n"),
    (1417, 2185, "    # Sample measures definitions (imported from test_data)\n"),
    (2233, 2327, "    # Distribution measures raw data (imported)\n"),
    (2378, 2584, "    # Fail measures raw data (imported)\n"),
    (2592, 2747, "    # Warning measures raw data (imported)\n"),
    (2752, 2889, "    # HP measures raw data (imported)\n"),
    (2890, 3054, "    # Compete choice output data (imported)\n"),
    (3055, 3207, "    # Supply-demand output data (imported)\n"),
    (3208, 3360, "    # Map measures partial check output (imported)\n"),
    (3361, 3516, "    # Partial measures output data (imported)\n"),
    (3517, 3618, "    # Refrigerant emissions map markets output (imported)\n"),
]

# Apply replacements in reverse order to maintain line numbers
for start, end, comment in reversed(replacements):
    # Remove lines from start to end (inclusive, 0-indexed)
    del lines[start:end+1]
    # Insert the comment
    lines.insert(start, comment)

# Write the modified file
with open('market_updates_test.py', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("Replacements completed successfully!")
print(f"Original line count: 4410")
print(f"New line count: {len(lines)}")
print(f"Lines removed: {4410 - len(lines)}")
