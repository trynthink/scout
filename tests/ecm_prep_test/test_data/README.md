# Test Data Directory

This directory contains externalized test data for the `ecm_prep` test suite. Test
data has been extracted from the original large unittest classes to improve test
maintainability, reduce file sizes, and enhance code readability.

## Overview

The original `ecm_prep_test.py` file was **129,529 lines** with extensive setup code
defining complex nested data structures. By extracting test data to pickle files,
we've achieved:

- **95-99% reduction** in individual test file sizes
- **Improved maintainability** - test logic separated from test data
- **Preserved accuracy** - exact Python objects maintained via pickle serialization
- **Enhanced readability** - tests focus on behavior, not data construction

## Files in This Directory

### Test Data Files (Pickle Format)

| File | Size | Used By | Description |
|------|------|---------|-------------|
| `merge_measures_test_data.pkl` | ~3.5 MB | `test_merge_measures.py` | Test fixtures for `MergeMeasuresandApplyBenefitsTest` |
| `tsv_test_data.pkl` | ~50.3 MB | `test_tsv.py` | Test data for `TimeSensitiveValuationTest` |
| `market_updates_test_data.pkl` | ~57.6 MB | `test_market_updates.py` | Test data for `MarketUpdatesTest` |
| `partition_microsegment_test_data.pkl` | ~2-5 MB | `test_partition_microsegment.py` | Test data for microsegment partitioning tests |
| `update_measures_test_data.pkl` | ~4.8 MB | `test_update_measures.py` | Test data for `UpdateMeasuresTest` |

### Summary Files

Each `.pkl` file has a corresponding `*_summary.txt` file that provides:
- **Header**: Total attribute count and pickle file size
- **Attributes table**: Alphabetically sorted list with types and sizes (length for lists, keys for dicts)
- **Detailed Examples**: Key attributes with descriptions, structure previews, and usage context
- **Format**: Unified columnar layout across all summary files for consistency

## Regenerating Test Data

If you need to regenerate test data (e.g., after changes to source code or test
requirements), use the corresponding dump script from the `data_generators/` directory:

```bash
# From the repository root (IMPORTANT: Don't cd into data_generators!)
# Set PYTHONPATH (required for scout module imports)
export PYTHONPATH=.  # On Windows: $env:PYTHONPATH = "."

# Run dump scripts from repo root 
python tests/ecm_prep_test/data_generators/dump_merge_test_data.py
python tests/ecm_prep_test/data_generators/dump_partition_test_data.py
python tests/ecm_prep_test/data_generators/dump_update_measures_test_data.py
python tests/ecm_prep_test/data_generators/dump_tsv_test_data.py
python tests/ecm_prep_test/data_generators/dump_market_updates_test_data.py

```

Each dump script:
1. Loads the original unittest class from `archive/ecm_prep_test_ORIGINAL.py`
2. Monkey-patches the `__file__` attribute to resolve test files correctly
3. Executes the `setUpClass` method to generate all test data (uses `tests/test_files/`)
4. Extracts class attributes and saves to `../test_data/*.pkl`
5. Generates an enhanced summary file with:
   - Total attribute count and file size
   - Alphabetically sorted attribute table
   - Detailed examples with descriptions and structure previews

## Why Use Pickle Files?

- **Preserves Python objects**: Maintains exact structure of complex objects
  (e.g., `Measure`, `MeasurePackage` instances)
- **Fast serialization**: Faster than JSON for large datasets
- **No conversion logic**: No need for custom serialization/deserialization
- **Type preservation**: Maintains numpy arrays, custom classes, etc.


## Alternative: JSON Files

For simpler test data (primarily dicts/lists), JSON would be preferable because:
- Human-readable and editable
- Language-agnostic
- Easy to inspect with standard tools

However, for complex objects like `Measure` instances, `Namespace` objects, and
numpy arrays, pickle is more practical.

## Maintenance

When updating test data:
1. Modify the original test class in `archive/ecm_prep_test_ORIGINAL.py` (if needed)
2. Run the appropriate `data_generators/dump_*_test_data.py` script
3. Review the generated `*_summary.txt` to verify structure and detailed examples
4. Run the corresponding pytest file to validate
