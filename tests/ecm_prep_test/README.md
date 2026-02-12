# ECM Prep Test Suite

This directory contains pytest-based tests for the Scout ECM preparation module, refactored from the original monolithic `ecm_prep_test.py` file (129,528 lines).

## Test Status Summary

**✅ All Tests Passing: 45 passed, 0 xfailed**

### Test Files (45 total tests)

- `market_updates_test.py` - **17 passed** - 1,359 lines (Market fill_mkts function) - **25% reduction**
- `merge_measuresand_apply_benefits_test.py` - **5 passed** - 518 lines (Measure merging and packaging) - **85% reduction**
- `update_measures_test.py` - **4 passed** - 832 lines (Update results function) - **98.5% reduction**
- `partition_microsegment_test.py` - **2 passed** - 904 lines (Microsegment partitioning) - **76.6% reduction**
- `time_sensitive_valuation_test.py` - **1 passed** - 225 lines (TSV calculations) - **99.5% reduction**
- `add_key_vals_test.py` - **3 passed** (Add key values function)
- `cost_conversion_test.py` - **3 passed** (Cost conversion)
- `create_key_chain_test.py` - **2 passed** (Key chain creation)
- `div_key_vals_float_test.py` - **2 passed** (Divide key values float)
- `append_key_vals_test.py` - **1 passed** (Append key values function)
- `check_markets_test.py` - **1 passed** (Market validation)
- `clean_up_test.py` - **1 passed** (Result cleanup)
- `div_key_vals_test.py` - **1 passed** (Divide key values)
- `fill_parameters_test.py` - **1 passed** (Parameter filling)
- `yr_map_test.py` - **1 passed** (Year mapping)

## Directory Structure

```
tests/ecm_prep_test/
├── README.md                                  # This file
├── common.py                                  # Shared fixtures and helpers (dict_check, NullOpts)
│
├── # Test Files (pytest format, 45 tests - all passing!)
├── market_updates_test.py                    # 17 tests passing - 1,553 lines (92% reduction)
├── merge_measuresand_apply_benefits_test.py  # 5 tests passing - 524 lines (85% reduction!)
├── update_measures_test.py                   # 4 tests passing - 832 lines (98.5% reduction!)
├── partition_microsegment_test.py            # 2 tests passing - 910 lines (76.6% reduction!)
├── time_sensitive_valuation_test.py          # 1 test passing - 225 lines (99.5% reduction!)
├── add_key_vals_test.py                      # 3 tests passing
├── cost_conversion_test.py                   # 3 tests passing
├── create_key_chain_test.py                  # 2 tests passing
├── div_key_vals_float_test.py                # 2 tests passing
├── append_key_vals_test.py                   # 1 test passing
├── check_markets_test.py                     # 1 test passing
├── clean_up_test.py                          # 1 test passing
├── div_key_vals_test.py                      # 1 test passing
├── fill_parameters_test.py                   # 1 test passing
├── yr_map_test.py                            # 1 test passing
│
└── test_data/                                 # Refactored test data (modular structure)
    ├── README.md                              # Documentation for data structure
    ├── REFACTORING_SUMMARY.md                 # Details on data refactoring
    ├── __init__.py                            # Package marker
    │
    ├── time_sensitive_valuation_test_data/    # TSV test data (~79K lines split into 8 files)
    │   ├── __init__.py                        # Auto-imports all variables
    │   ├── _helpers.py                        # Helper functions
    │   ├── sample_tsv_data.py                 # Main TSV load shape data
    │   ├── sample_cost_convert.py             # Building type conversions
    │   ├── sample_tsv_measures_in_features.py # Feature test measures
    │   ├── sample_tsv_measure_in_metrics.py   # Metrics test measures
    │   ├── sample_tsv_metric_settings.py      # TSV metrics config
    │   ├── ok_tsv_facts_out_features_raw.py   # Expected features output
    │   ├── ok_tsv_facts_out_metrics_raw.py    # Expected metrics output
    │   └── sample_tsv_data_update_measures.py # Update measures TSV data
    │
    ├── market_updates_test_data/              # Market updates test data (31 variables)
    │   ├── __init__.py                        # Auto-imports all variables
    │   ├── _helpers.py                        # Helper functions
    │   ├── ok_tpmeas_fullchk_break_out.py     # Tech potential full check breakout
    │   ├── sample_cpl_in.py                   # Competition data
    │   ├── ok_tpmeas_partchk_msegout.py       # Partial check microseg output
    │   ├── sample_cpl_in_state.py             # State-level competition data
    │   ├── sample_cpl_in_emm.py               # EMM region competition data
    │   ├── sample_mseg_in.py                  # Microsegment input data
    │   ├── ok_hpmeas_rates_breakouts.py       # Heat pump rates breakouts
    │   ├── ok_partialmeas_in.py               # Partial measure inputs
    │   ├── ok_hpmeas_rates_mkts_out.py        # HP rates market outputs
    │   ├── ok_tpmeas_fullchk_msegout.py       # Full check microseg output
    │   ├── sample_mseg_in_emm.py              # EMM microsegment data
    │   ├── sample_mseg_in_state.py            # State microsegment data
    │   ├── ok_tpmeas_partchk_msegout_emm.py   # EMM partial check output
    │   ├── ok_tpmeas_partchk_msegout_state.py # State partial check output
    │   ├── ok_fmeth_measures_in.py            # Methane fugitive emissions measures
    │   ├── ok_frefr_measures_in.py            # Refrigerant fugitive emissions measures
    │   ├── frefr_fug_emissions.py             # Refrigerant emissions data
    │   ├── fmeth_fug_emissions.py             # Methane fugitive emissions data
    │   ├── frefr_hp_rates.py                  # Refrigerant HP rates
    │   ├── carb_int_data.py                   # Carbon intensity data
    │   ├── ecosts_data.py                     # Energy costs data
    │   ├── ok_measures_in.py                  # Standard measure inputs (768 lines!)
    │   ├── ok_distmeas_in.py                  # Distribution measures
    │   ├── failmeas_in.py                     # Failure test measures
    │   ├── warnmeas_in.py                     # Warning test measures
    │   ├── ok_hp_measures_in.py               # Heat pump measures
    │   ├── ok_tpmeas_fullchk_competechoiceout.py  # Consumer choice output
    │   ├── ok_tpmeas_fullchk_supplydemandout.py   # Supply/demand output
    │   ├── ok_mapmas_partchck_msegout.py      # Partial check microseg adjustment
    │   ├── ok_partialmeas_out.py              # Partial measure outputs
    │   └── ok_map_frefr_mkts_out.py           # Refrigerant market outputs
    │
    ├── merge_measuresand_apply_benefits_test_data/  # Merge measures test data (6 variables)
    │   ├── __init__.py                        # Auto-imports all variables
    │   ├── sample_measures_in_mkts.py         # Sample measures for market testing (~1,065 lines)
    │   ├── sample_measures_in_env_costs.py    # Sample measures for envelope costs (~345 lines)
    │   ├── sample_measures_in_sect_shapes.py  # Sample measures for sector shapes (~1,081 lines)
    │   ├── breaks_ok_out_test1.py             # Expected output breaks data (~149 lines)
    │   ├── contrib_ok_out_test1.py            # Expected contributing measures data (~200 lines)
    │   └── markets_ok_out_test1.py            # Expected markets output data (~143 lines)
    │
    ├── partition_microsegment_test_data/      # Partition microsegment test data (8 variables)
    │   ├── __init__.py                        # Auto-imports all variables
    │   ├── ok_out_fraction.py                 # Fraction retrofit rate output
    │   ├── ok_out_bass.py                     # Bass diffusion output
    │   ├── ok_out_fraction_string.py          # Fraction string output
    │   ├── ok_out_bass_string.py              # Bass string output
    │   ├── ok_out_bad_string.py               # Bad string test output
    │   ├── ok_out_bad_values.py               # Bad values test output
    │   ├── ok_out_wrong_name.py               # Wrong name test output
    │   └── ok_out.py                          # Standard output
    │
    └── update_measures_test_data/             # Update measures test data (8 variables)
        ├── __init__.py                        # Auto-imports all variables
        ├── _helpers.py                        # Helper functions
        ├── sample_cpl_in_aia.py               # AIA competition data
        ├── sample_cpl_in_emm.py               # EMM competition data
        ├── ok_out_emm_features.py             # EMM features expected output
        ├── sample_mseg_in_emm.py              # EMM microsegment data
        ├── ok_out_emm_metrics_mkts.py         # EMM metrics market output
        ├── sample_mseg_in_aia.py              # AIA microsegment data
        ├── base_out_2009.py                   # 8,760 hourly baseline values for 2009
        └── base_out_2010.py                   # 8,760 hourly baseline values for 2010
```

## Achievements

### Successful Migration & Refactoring

- ✅ **100% test coverage maintained** - All 45 functional tests passing
- ✅ **Converted from unittest to pytest** - Modern testing framework
- ✅ **Fixed numpy string handling** - Resolved all type mismatch issues in production code
- ✅ **Refactored test data structure** - Modular folder-based organization

### File Size Reductions

| File | Original Lines | After Refactor | Reduction |
|------|----------------|----------------|-----------|
| time_sensitive_valuation_test.py | 44,698 | 225 | **99.5%** |
| update_measures_test.py | 55,717 | 832 | **98.5%** |
| merge_measuresand_apply_benefits_test.py | 3,506 | 524 | **85.0%** |
| partition_microsegment_test.py | 3,883 | 910 | **76.6%** |
| market_updates_test.py | 2,072 | 1,553 | **25.0%** |

### Test Data Refactoring (2024)

**Before:**
- Hard to navigate and maintain
- Large files difficult to load in editors

**After:**
- **individual variable files** organized in 5 folders
- Easy navigation and maintenance
- Clear separation of concerns
- Backward compatible imports (no test changes needed!)

**Refactored files:**
- `time_sensitive_valuation_test_data/` - ~79,568 lines → 8 files + helpers
- `update_measures_test_data/` - ~19,844 lines → 8 files + helpers (includes 17,528 lines of hourly baseline data)
- `market_updates_test_data/` - ~519 lines → 31 files + helpers (includes large emissions and cost data)
- `merge_measuresand_apply_benefits_test_data/` - ~2,983 lines → 6 files
- `partition_microsegment_test_data/` - ~2,973 lines → 8 files

## Running Tests

### Run all tests
```bash
pytest tests/ecm_prep_test/ -v
```

Expected output: `45 passed` ✅

### Run specific test file
```bash
pytest tests/ecm_prep_test/market_updates_test.py -v
pytest tests/ecm_prep_test/time_sensitive_valuation_test.py -v
```

### Run with coverage
```bash
pytest tests/ecm_prep_test/ --cov=scout.ecm_prep --cov-report=html
```

### Quick summary
```bash
pytest tests/ecm_prep_test/ -v --tb=no -q
```

## Resolved Issues

### Numpy String Handling

Previously, some tests were marked as expected failures (`@pytest.mark.xfail`) due to numpy string handling issues. These have all been resolved:

#### 1. test_mseg_ok_full_tp (market_updates_test.py) - ✅ Fixed

**Issue**: Type mismatch when comparing `numpy.str_` with native Python `str` in dictionary keys/tuple elements

**Solution**: Modified `scout/ecm_prep.py` to convert numpy strings to Python strings when creating contributing microsegment key strings. The fix ensures that tuples containing numpy strings are properly converted before being stringified for dictionary keys.

**Code Change**: In the `fill_mkts` function, added conversion logic:
```python
contrib_mseg_key_clean = tuple(
    str(k) if hasattr(k, 'item') else k for k in contrib_mseg_key)
contrib_mseg_key_str = str(contrib_mseg_key_clean)
```

#### 2. test_fillmeas_ok (update_measures_test.py) - ✅ Fixed

**Issue**: Numpy string keys in TSV (time-sensitive valuation) data structures causing `KeyError` when used as dictionary keys

**Solution**: Multi-part fix:
1. Modified `scout/ecm_prep.py` to convert `eu` (end-use) variable to Python string before using as dictionary key
2. Extracted the correct comprehensive TSV data structure (including residential heating data) from the original test file
3. Applied recursive numpy string to Python string conversion to all test data
4. Fixed `assertEqual` reference that was incompatible with pytest

**Code Changes**: 
- In `gen_tsv_facts` function at lines 5676 and 5732, added type conversion for dictionary key lookups
- Added `_convert_numpy_strings_to_python` utility function to test data files
- Updated test to use correct `sample_tsv_data_update_measures` dataset

## Migration from unittest to pytest

### Key Changes

1. **Test Classes → Functions**: Converted class-based tests to function-based tests
2. **setUpClass → Fixtures**: Module-scoped pytest fixtures replace class setup
3. **Assertions**: `self.assertEqual()` → `assert ==`, `self.assertTrue()` → `assert`
4. **Data Extraction**: Large inline data moved to separate modules in `test_data/`
5. **Removed unittest imports**: No longer depend on `unittest.TestCase`

### Common Patterns

**Before (unittest):**
```python
class MyTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = {...}

    def test_something(self):
        self.assertEqual(result, self.data)
```

**After (pytest):**
```python
@pytest.fixture(scope="module")
def test_data():
    data = {...}
    return {"data": data}

def test_something(test_data):
    assert result == test_data["data"]
```

## Test Data Organization

Test data has been refactored into a **modular folder structure** for improved maintainability. Each test data module is now a folder containing individual variable files.

### Structure

Each test data folder follows this pattern:
```
test_data_folder/
├── __init__.py          # Auto-imports all variables for backward compatibility
├── _helpers.py          # Shared helper functions (if needed)
├── variable1.py         # Individual variable definition
├── variable2.py
└── ...
```

## References

- Original file: `tests/ecm_prep_test.py` (retained for reference)
- pytest documentation: https://docs.pytest.org/
- Scout ECM module: `scout/ecm_prep.py`
