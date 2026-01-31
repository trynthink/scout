# ECM Prep Test Suite

This directory contains the refactored and modernized test suite for ECM (Energy Conservation Measure) preparation functionality. The tests were converted from a single 129,354-line unittest file to a modular pytest-based suite with a **97.2% reduction in code size**.

## Directory Structure

```
ecm_prep_test/
├── README.md                              # This file
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

## Regenerating Pickle Files

### When to Regenerate:

Regenerate pickle files if:
- You modify the source code that generates test data
- The original test data definitions change
- Tests fail due to data structure changes
- You need to update test scenarios

### How to Regenerate:

```bash
# IMPORTANT: Run from the project root directory!
# (Scripts need access to inputs/ folder)

# Set PYTHONPATH
export PYTHONPATH=.  # On Windows: $env:PYTHONPATH = "."

# Regenerate any test data
python tests/ecm_prep_test/data_generators/dump_merge_test_data.py
python tests/ecm_prep_test/data_generators/dump_partition_test_data.py
python tests/ecm_prep_test/data_generators/dump_market_updates_test_data.py
python tests/ecm_prep_test/data_generators/dump_tsv_test_data.py
python tests/ecm_prep_test/data_generators/dump_update_measures_test_data.py
```

### Important Notes:

1. **Run from repo root**: Scripts must be run from repository root to access `inputs/metadata.json` and other required files
2. **Archive file required**: All dump scripts load data from `archive/ecm_prep_test_ORIGINAL.py`. Do NOT delete this file!
3. **Test files required**: Dump scripts use test data from `tests/test_files/` directory
4. **All scripts working**: All 5 dump scripts can now be regenerated successfully
5. **Generation time**: Large classes (TSV, Market Updates) may take 60-120 seconds
6. **File size**: Pickle files range from 4 MB to 58 MB

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
