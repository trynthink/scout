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

The test files have been successfully refactored, and large data structures have been extracted into modular folder structures:

### Refactored Data Modules (Folder Structure)

Each large test data file has been converted into a folder with individual files for each variable:

- ✅ **time_sensitive_valuation_test_data/** (8 variables)
  - `sample_tsv_data.py`
  - `sample_cost_convert.py`
  - `sample_tsv_measures_in_features.py`
  - `sample_tsv_measure_in_metrics.py`
  - `sample_tsv_metric_settings.py`
  - `ok_tsv_facts_out_features_raw.py`
  - `ok_tsv_facts_out_metrics_raw.py`
  - `sample_tsv_data_update_measures.py`
  - `_helpers.py` (helper functions)
  - `__init__.py` (imports all variables)

- ✅ **market_updates_test_data/** (14 variables)
  - `ok_tpmeas_fullchk_break_out.py`
  - `sample_cpl_in.py`
  - `ok_tpmeas_partchk_msegout.py`
  - `sample_cpl_in_state.py`
  - `sample_cpl_in_emm.py`
  - `sample_mseg_in.py`
  - `ok_hpmeas_rates_breakouts.py`
  - `ok_partialmeas_in.py`
  - `ok_hpmeas_rates_mkts_out.py`
  - `ok_tpmeas_fullchk_msegout.py`
  - `sample_mseg_in_emm.py`
  - `sample_mseg_in_state.py`
  - `ok_tpmeas_partchk_msegout_emm.py`
  - `ok_tpmeas_partchk_msegout_state.py`
  - `_helpers.py` (helper functions)
  - `__init__.py` (imports all variables)

- ✅ **update_measures_test_data/** (6 variables)
  - `sample_cpl_in_aia.py`
  - `sample_cpl_in_emm.py`
  - `ok_out_emm_features.py`
  - `sample_mseg_in_emm.py`
  - `ok_out_emm_metrics_mkts.py`
  - `sample_mseg_in_aia.py`
  - `_helpers.py` (helper functions)
  - `__init__.py` (imports all variables)

- ✅ **partition_microsegment_test_data/** (8 variables)
  - `ok_out_fraction.py`
  - `ok_out_bass.py`
  - `ok_out_fraction_string.py`
  - `ok_out_bass_string.py`
  - `ok_out_bad_string.py`
  - `ok_out_bad_values.py`
  - `ok_out_wrong_name.py`
  - `ok_out.py`
  - `__init__.py` (imports all variables)

### Benefits of Folder Structure

- Each variable is in its own file, making it easier to locate and modify specific test data
- Helper functions are isolated in `_helpers.py` files
- The `__init__.py` handles imports and any necessary data transformations
- Reduces file size and improves maintainability
- Import statements in test files remain unchanged

### Usage

Import from these modules as before:

```python
from tests.ecm_prep_test.test_data.time_sensitive_valuation_test_data import sample_tsv_data
```

The folder structure is transparent to the importing code - Python treats the folders as packages.
