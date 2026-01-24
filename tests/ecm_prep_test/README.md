# ECM Prep Test Suite

This directory contains the refactored and modernized test suite for ECM (Energy Conservation Measure) preparation functionality. The tests were converted from a single 129,354-line unittest file to a modular pytest-based suite with a **97.2% reduction in code size**.

## Project Summary

### What Was Done

The original `ecm_prep_test.py` file (129,354 lines) was:
1. **Split** into 15 separate test files, one per test class
2. **Converted** from unittest to pytest framework
3. **Optimized** using pickle-based data externalization for large test classes
4. **Archived** to `archive/ecm_prep_test_ORIGINAL.py` for reference and pickle regeneration

### Results

| Metric | Value |
|--------|-------|
| **Original Total** | 129,354 lines |
| **New Total** | 3,592 lines |
| **Overall Reduction** | **-97.2%** |
| **Lines Saved** | 125,762 lines |
| **Test Files** | 15 files |
| **All Tests Passing** | ✅ 45/45 tests |
| **Test Execution Time** | ~7 seconds |

## Directory Structure

```
ecm_prep_test/
├── README.md                              # This file
├── COMPLETION_SUMMARY.md                  # Detailed conversion report
├── QUICK_REFERENCE.md                     # Quick conversion guide
├── convert_helper.py                      # Helper script for tracking progress
├── conftest.py                            # Shared fixtures and utilities
├── __init__.py                            # Package initialization
│
├── archive/                               # Original files
│   └── ecm_prep_test_ORIGINAL.py         # Original 129K-line unittest file
│
├── data_generators/                       # Scripts to generate pickle files
│   ├── dump_merge_test_data.py           # Generate merge_measures_test_data.pkl
│   ├── dump_partition_test_data.py       # Generate partition_test_data.pkl
│   ├── dump_market_updates_test_data.py  # Generate market_updates_test_data.pkl
│   ├── dump_tsv_test_data.py             # Generate tsv_test_data.pkl
│   └── dump_update_measures_test_data.py # Generate update_measures_test_data.pkl
│
├── test_data/                             # Pickle files with test data
│   ├── merge_measures_test_data.pkl      # 4.1 MB (20 attributes)
│   ├── partition_test_data.pkl           # 53.8 MB (8 attributes)
│   ├── market_updates_test_data.pkl      # 57.6 MB (49 attributes)
│   ├── tsv_test_data.pkl                 # 50.3 MB (15 attributes)
│   ├── update_measures_test_data.pkl     # 4.8 MB (30 attributes)
│   └── *_summary.txt files               # Human-readable summaries
│
└── Test files (pytest):
    ├── test_add_key_vals.py              # ✅ 190 lines (+52.0% from 125)
    ├── test_append_key_vals.py           # ✅ 118 lines (-1.7% from 120)
    ├── test_check_markets.py             # ✅ 112 lines (+40.0% from 80)
    ├── test_clean_up.py                  # ✅ 250 lines (+25.0% from 200)
    ├── test_cost_conversion.py           # ✅ 591 lines (+3.1% from 573)
    ├── test_create_key_chain.py          # ✅ 226 lines (+7.1% from 211)
    ├── test_div_key_vals.py              # ✅ 126 lines (+37.0% from 92)
    ├── test_div_key_vals_float.py        # ✅ 179 lines (+32.6% from 135)
    ├── test_fill_parameters.py           # ✅ 574 lines (+1.8% from 564)
    ├── test_market_updates.py            # ✅ 470 lines (-97.6% from 19,401) 🔥
    ├── test_merge_measures.py            # ✅ 170 lines (-95.2% from 3,507) 🔥
    ├── test_partition_microsegment.py    # ✅ 180 lines (-95.4% from 3,880) 🔥
    ├── test_time_sensitive_valuation.py  # ✅ 86 lines (-99.8% from 44,697) 🔥
    ├── test_update_measures.py           # ✅ 246 lines (-99.6% from 55,694) 🔥
    └── test_yr_map.py                    # ✅ 74 lines (-1.3% from 75)
```

🔥 = Uses pickle method for dramatic size reduction

## Running Tests

### Run all tests:
```bash
pytest tests/ecm_prep_test/
```

### Run with verbose output:
```bash
pytest tests/ecm_prep_test/ -v
```

### Run specific test file:
```bash
pytest tests/ecm_prep_test/test_market_updates.py -v
```

### Run specific test method:
```bash
pytest tests/ecm_prep_test/test_market_updates.py::TestMarketUpdates::test_mseg_ok_full_tp -v
```

### Run with PYTHONPATH set (if needed):
```bash
# PowerShell
$env:PYTHONPATH = "."; pytest tests/ecm_prep_test/ -v

# Bash
PYTHONPATH=. pytest tests/ecm_prep_test/ -v
```

## Understanding the Pickle Method

### What is the Pickle Method?

For test classes with massive amounts of setup data (thousands of lines of hardcoded test data), we use **data externalization via pickle files**:

1. **Extract**: A `dump_*.py` script loads the original unittest class, executes its `setUpClass()` method, and serializes all class attributes to a `.pkl` file
2. **Load**: The pytest test file loads the pickle file via a class-scoped fixture
3. **Test**: Tests run using the pre-loaded data

### Benefits:

- **Massive size reduction**: 95-99.8% reduction for large test classes
- **Faster loading**: Data is pre-processed and quickly deserialized
- **Readable tests**: Test files focus on test logic, not data
- **Maintainable**: Changes to data only require regenerating pickle files

### Which Tests Use Pickle?

| Test File | Original Lines | New Lines | Reduction | Pickle Size |
|-----------|----------------|-----------|-----------|-------------|
| test_merge_measures.py | 3,507 | 170 | -95.2% | 4.1 MB |
| test_partition_microsegment.py | 3,880 | 180 | -95.4% | 53.8 MB |
| test_market_updates.py | 19,401 | 470 | -97.6% | 57.6 MB |
| test_time_sensitive_valuation.py | 44,697 | 86 | -99.8% | 50.3 MB |
| test_update_measures.py | 55,694 | 246 | -99.6% | 4.8 MB |

## Regenerating Pickle Files

### When to Regenerate:

Regenerate pickle files if:
- You modify the source code that generates test data
- The original test data definitions change
- Tests fail due to data structure changes
- You need to update test scenarios

### How to Regenerate:

```bash
# From the project root directory:

# Regenerate merge measures data
python tests/ecm_prep_test/data_generators/dump_merge_test_data.py

# Regenerate partition data
python tests/ecm_prep_test/data_generators/dump_partition_test_data.py

# Regenerate market updates data
python tests/ecm_prep_test/data_generators/dump_market_updates_test_data.py

# Regenerate TSV data
python tests/ecm_prep_test/data_generators/dump_tsv_test_data.py

# Regenerate update measures data
python tests/ecm_prep_test/data_generators/dump_update_measures_test_data.py
```

### Important Notes:

1. **Archive file required**: All dump scripts load data from `archive/ecm_prep_test_ORIGINAL.py`. Do NOT delete this file!
2. **Test files folder required**: Some test data comes from `tests/test_files/` directory
3. **Generation time**: Large classes (UpdateMeasuresTest, TimeSensitiveValuationTest) may take 5-10 seconds to generate
4. **File size**: Pickle files range from 4 MB to 58 MB

## Key Conversion Patterns

### 1. Small Test Classes (inline data)

**Approach**: Keep test data inline, convert assertions
**Examples**: `test_yr_map.py`, `test_check_markets.py`

```python
class TestYrMap:
    @pytest.fixture(scope="class")
    def test_data(self):
        return {
            'opts': NullOpts().opts,
            'data': create_test_data()
        }
    
    def test_something(self, test_data):
        assert function(test_data['data']) == expected
```

### 2. Large Test Classes (pickle method)

**Approach**: Externalize data to pickle, load via fixture
**Examples**: `test_market_updates.py`, `test_update_measures.py`

```python
class TestMarketUpdates:
    @pytest.fixture(scope="class")
    def test_data(self):
        pickle_file = Path(__file__).parent / "test_data" / "market_updates_test_data.pkl"
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
        return data
    
    def test_something(self, test_data):
        measure = test_data['measures'][0]
        assert measure.function() == test_data['expected'][0]
```

## Shared Utilities (conftest.py)

The `conftest.py` file provides shared fixtures and utilities:

### Fixtures:
- `null_opts()`: Provides NullOpts object for tests
- `useful_vars()`: Provides UsefulVars object
- `useful_files()`: Provides UsefulInputFiles object

### Utilities:
- `dict_check(dict1, dict2)`: Deep equality check for nested dictionaries
- `NullOpts`: Mock options object
- `UserOptions`: User-specified options
- `UsefulVars`: Global variables for ECM preparation
- `UsefulInputFiles`: Input file data structures
- `Measure`, `MeasurePackage`: ECM measure classes

## Benefits of This Refactoring

### 1. **Maintainability**
- Each test class in its own file
- Easy to locate and modify specific tests
- Clear separation of concerns

### 2. **Performance**
- Faster test discovery
- Parallel execution possible
- Quick pickle loading

### 3. **Readability**
- Pytest syntax is more concise
- Better error messages
- Clearer test intent

### 4. **Modern Tooling**
- Better IDE integration
- Rich plugin ecosystem
- Fixtures are more powerful than setUp/tearDown

### 5. **Scalability**
- Pickle method works for any size test class
- Easy to add new tests
- Modular structure supports growth

## Migration from unittest to pytest

### Key Changes:

| Aspect | unittest | pytest |
|--------|----------|--------|
| **Test discovery** | `unittest.main()` | Automatic |
| **Assertions** | `self.assertEqual(a, b)` | `assert a == b` |
| **Setup** | `setUp()`, `setUpClass()` | `@pytest.fixture` |
| **Exceptions** | `self.assertRaises(E)` | `with pytest.raises(E):` |
| **Approx equality** | `assertAlmostEqual(a, b, places=2)` | `assert a == pytest.approx(b, abs=0.01)` |
| **Skipping** | `@unittest.skip(reason)` | `@pytest.mark.skip(reason=...)` |
| **Parametrization** | Multiple methods | `@pytest.mark.parametrize` |

### Common Assertion Conversions:

```python
# unittest → pytest

self.assertEqual(a, b)              → assert a == b
self.assertNotEqual(a, b)           → assert a != b
self.assertTrue(x)                  → assert x
self.assertFalse(x)                 → assert not x
self.assertIsNone(x)                → assert x is None
self.assertIn(a, b)                 → assert a in b
self.assertIsInstance(a, B)         → assert isinstance(a, B)
self.assertRaises(ValueError)       → with pytest.raises(ValueError):
self.assertCountEqual(a, b)         → assert set(a) == set(b)
self.assertAlmostEqual(a, b, 5)     → assert a == pytest.approx(b, abs=1e-5)
```

## Troubleshooting

### ImportError: No module named 'scout'

**Solution**: Set PYTHONPATH before running tests:
```bash
# PowerShell
$env:PYTHONPATH = "."
pytest tests/ecm_prep_test/

# Bash
PYTHONPATH=. pytest tests/ecm_prep_test/
```

### Pickle file not found

**Solution**: Run the corresponding dump script to generate it:
```bash
python tests/ecm_prep_test/data_generators/dump_<name>_test_data.py
```

### Test failures after code changes

**Solution**: Regenerate affected pickle files to sync with code changes

### Cannot import from conftest

**Solution**: Use relative imports:
```python
from .conftest import dict_check  # ✅ Correct
from conftest import dict_check   # ❌ Wrong
```

## Additional Resources

- **Detailed Conversion Report**: See `COMPLETION_SUMMARY.md`
- **Quick Reference Guide**: See `QUICK_REFERENCE.md`
- **Progress Tracking**: Run `python convert_helper.py`
- **pytest Documentation**: https://docs.pytest.org/

## Project Status

✅ **COMPLETE**: All 15 test classes converted successfully
- 129,354 lines → 3,592 lines (97.2% reduction)
- All 45 tests passing
- Fast execution (~7 seconds)
- Well-documented and maintainable

## Contributors

This refactoring was completed as part of the Scout ECM test suite modernization project.

---

**Last Updated**: January 2026
**Status**: Production Ready ✅
