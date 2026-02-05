# Test Data Directory

This directory is designed to store large test data structures extracted from test files to improve readability and maintainability.

## Purpose

Some test files (particularly `test_market_updates_test.py`, `test_time_sensitive_valuation_test.py`, and `test_update_measures_test.py`) contain very large data dictionaries in their `setUpClass` methods. These data structures can be extracted into separate Python modules here.

## How to Extract Large Test Data

If a test file becomes too large due to embedded data, follow this pattern:

### Step 1: Create a data module

Create a new Python file in this directory, e.g., `market_update_data.py`:

```python
#!/usr/bin/env python3

"""Test data for Market Updates tests."""

# Sample microsegment input data
sample_mseg_in = {
    "AIA_CZ1": {
        "assembly": {
            # ... large nested dictionary ...
        }
    }
}

# Sample cost/performance/lifetime input data
sample_cpl_in = {
    "AIA_CZ1": {
        "assembly": {
            # ... large nested dictionary ...
        }
    }
}

# Other large data structures
ok_tpmeas_fullchk_in = [
    # ... large list of measures ...
]
```

### Step 2: Update the test file to import the data

In your test file (e.g., `test_market_updates_test.py`), import the data:

```python
# Import test data
from tests.ecm_prep_test.test_data.market_update_data import (
    sample_mseg_in,
    sample_cpl_in,
    ok_tpmeas_fullchk_in
)

class MarketUpdatesTest(unittest.TestCase, CommonMethods):
    @classmethod
    def setUpClass(cls):
        # Use imported data
        cls.sample_mseg_in = sample_mseg_in
        cls.sample_cpl_in = sample_cpl_in
        cls.ok_tpmeas_fullchk_in = ok_tpmeas_fullchk_in
        # ... rest of setup
```

### Step 3: Remove the data from the test file

Delete the large data structure definitions from the test file's `setUpClass` method, keeping only the assignment from imported data.

## Benefits

- **Improved readability**: Test logic is separated from test data
- **Easier maintenance**: Data can be updated independently
- **Better version control**: Data changes don't clutter test diffs
- **Modularity**: Data can be reused across multiple test files if needed

## When to Extract Data

Consider extracting data structures when:

- A single data structure is > 100 lines
- The `setUpClass` method is > 1000 lines
- Multiple large data structures are defined inline
- The same data is used across multiple test classes

## Current Status

The test files have been successfully refactored, and large data structures have been extracted:

### Extracted Data Modules

- ✅ **time_sensitive_valuation_test_data.py** (~79K lines): Contains `sample_tsv_data`, `sample_tsv_data_update_measures`, TSV measure definitions, and expected output data
- ✅ **market_updates_test_data.py** (~900 lines): Contains microsegment data, choice parameters, and market test fixtures
- ✅ **update_measures_test_data.py** (~3K lines): Contains measure lists, package definitions, and expected outputs

### Result

- `time_sensitive_valuation_test.py` reduced from 44,698 to 225 lines (99.5% reduction)
- `market_updates_test.py` reduced from 19,425 to 4,395 lines (77.4% reduction)
- `update_measures_test.py` reduced from 55,717 to 18,360 lines (67.0% reduction)

All data has been properly extracted and all 45 tests are passing.
