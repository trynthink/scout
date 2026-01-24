# Quick Reference Guide - unittest to pytest Conversion

## 🚀 Quick Start

### Step 1: Find Your Class
```bash
python tests/ecm_prep_test/convert_helper.py
```

### Step 2: Extract the Class Code
1. Open `tests/ecm_prep_test.py`
2. Go to the line numbers shown by helper script
3. Copy from `class XyzTest(unittest.TestCase...` to just before next class

### Step 3: Create New File
Create `tests/ecm_prep_test/test_xyz.py` with this template:

```python
"""Test description from original class docstring."""

import pytest
from .conftest import dict_check  # if needed
# Add other imports as needed


class TestXyz:
    """Test description."""
    
    @pytest.fixture(scope="class")
    def test_data(self):
        """Setup test data - replaces setUpClass."""
        # Move setUpClass code here
        data = {
            # your setup data
        }
        return data
    
    def test_something(self, test_data):
        """Test description."""
        # Your test code here
        result = function_to_test(test_data['something'])
        assert result == expected
```

## 📝 Conversion Cheat Sheet

### Class Structure
```python
# BEFORE (unittest)
class XyzTest(unittest.TestCase, CommonMethods):
    pass

# AFTER (pytest)
class TestXyz:
    pass
```

### Setup/Teardown
```python
# BEFORE (unittest)
@classmethod
def setUpClass(cls):
    cls.data = load()

def setUp(self):
    self.temp = create()

def tearDown(self):
    cleanup()

# AFTER (pytest)
@pytest.fixture(scope="class")
def class_data(self):
    return {'data': load()}

@pytest.fixture(autouse=True)
def setup_method(self):
    self.temp = create()
    yield
    cleanup()
```

### Assertions (Most Common)
| unittest | pytest |
|----------|--------|
| `self.assertEqual(a, b)` | `assert a == b` |
| `self.assertNotEqual(a, b)` | `assert a != b` |
| `self.assertTrue(x)` | `assert x` |
| `self.assertFalse(x)` | `assert not x` |
| `self.assertIsNone(x)` | `assert x is None` |
| `self.assertIsNotNone(x)` | `assert x is not None` |
| `self.assertIn(a, b)` | `assert a in b` |
| `self.assertNotIn(a, b)` | `assert a not in b` |
| `self.assertDictEqual(d1, d2)` | `assert d1 == d2` |
| `self.dict_check(d1, d2)` | `dict_check(d1, d2)` |

### Approximate Equality
| unittest | pytest |
|----------|--------|
| `self.assertAlmostEqual(a, b, places=2)` | `assert a == pytest.approx(b, abs=0.01)` |
| `self.assertAlmostEqual(a, b, places=5)` | `assert a == pytest.approx(b, abs=1e-5)` |
| `self.assertAlmostEqual(a, b, places=10)` | `assert a == pytest.approx(b, abs=1e-10)` |

### Exception Testing
```python
# BEFORE (unittest)
with self.assertRaises(ValueError):
    function_that_raises()

# AFTER (pytest)
with pytest.raises(ValueError):
    function_that_raises()
```

## 🔧 Common Imports

```python
# Always needed
import pytest

# If using dict_check helper
from .conftest import dict_check

# If creating Measure objects
from scout.ecm_prep import Measure, MeasurePackage, ECMPrepHelper
from .conftest import NullOpts

# If need UsefulVars or UsefulInputFiles
from scout.ecm_prep_vars import UsefulVars, UsefulInputFiles

# Common standard library
import os
import copy
import json
import numpy
import pandas as pd
```

## 🎯 Example Conversions

### Example 1: Simple Test
```python
# BEFORE
class SimpleTest(unittest.TestCase):
    def test_basic(self):
        result = 2 + 2
        self.assertEqual(result, 4)

# AFTER
class TestSimple:
    def test_basic(self):
        result = 2 + 2
        assert result == 4
```

### Example 2: With Setup
```python
# BEFORE
class SetupTest(unittest.TestCase, CommonMethods):
    @classmethod
    def setUpClass(cls):
        cls.data = load_data()
    
    def test_process(self):
        result = process(self.data)
        self.assertEqual(result['status'], 'ok')
        self.dict_check(result['details'], expected)

# AFTER
from .conftest import dict_check

class TestSetup:
    @pytest.fixture(scope="class")
    def test_data(self):
        return {'data': load_data()}
    
    def test_process(self, test_data):
        result = process(test_data['data'])
        assert result['status'] == 'ok'
        dict_check(result['details'], expected)
```

### Example 3: Multiple Tests
```python
# BEFORE
class MultiTest(unittest.TestCase):
    def setUp(self):
        self.value = 10
    
    def test_increment(self):
        self.value += 1
        self.assertEqual(self.value, 11)
    
    def test_decrement(self):
        self.value -= 1
        self.assertEqual(self.value, 9)

# AFTER
class TestMulti:
    @pytest.fixture(autouse=True)
    def setup_method(self):
        self.value = 10
    
    def test_increment(self):
        self.value += 1
        assert self.value == 11
    
    def test_decrement(self):
        self.value -= 1
        assert self.value == 9
```

## 🏃 Running Tests

```bash
# Run all converted tests
pytest tests/ecm_prep_test/

# Run specific file
pytest tests/ecm_prep_test/test_yr_map.py

# Run specific test
pytest tests/ecm_prep_test/test_yr_map.py::TestYrMap::test_yrmap

# Run with verbose output
pytest tests/ecm_prep_test/ -v

# Run with output captured
pytest tests/ecm_prep_test/ -v -s

# Run with short traceback
pytest tests/ecm_prep_test/ -v --tb=short

# Stop on first failure
pytest tests/ecm_prep_test/ -x

# Run in parallel (if pytest-xdist installed)
pytest tests/ecm_prep_test/ -n auto
```

## ✅ Testing Your Conversion

After converting a test file, verify it works:

```bash
# 1. Check syntax
python -m py_compile tests/ecm_prep_test/test_xyz.py

# 2. Run the test
pytest tests/ecm_prep_test/test_xyz.py -v

# 3. If it passes, run all tests together
pytest tests/ecm_prep_test/ -v
```

## 🐛 Common Issues & Fixes

### Issue: ModuleNotFoundError: No module named 'conftest'
**Fix:** Use relative import
```python
# Wrong
from conftest import dict_check

# Correct
from .conftest import dict_check
```

### Issue: fixture 'test_data' not found
**Fix:** Make sure fixture is defined in same class or conftest.py
```python
@pytest.fixture(scope="class")  # Don't forget this decorator!
def test_data(self):
    return {'key': 'value'}
```

### Issue: AttributeError: 'TestXyz' object has no attribute 'assertEqual'
**Fix:** You forgot to convert an assertion
```python
# Find and replace
self.assertEqual(a, b)  # Old
assert a == b           # New
```

### Issue: Test data is None
**Fix:** Make sure you're returning data from fixture
```python
# Wrong
@pytest.fixture(scope="class")
def test_data(self):
    data = load_data()
    # Missing return!

# Correct
@pytest.fixture(scope="class")
def test_data(self):
    data = load_data()
    return data  # Don't forget!
```

## 📚 More Examples

See these converted files for real examples:
- `test_yr_map.py` - Simple test with class fixture
- `test_append_key_vals.py` - Using shared fixtures from conftest
- `test_clean_up.py` - Complex setup with multiple objects

## 🎓 Tips

1. **Start small**: Convert smallest classes first
2. **Test often**: Run tests after each conversion
3. **Use helper script**: Track your progress
4. **Copy examples**: Use converted files as templates
5. **Read errors carefully**: pytest gives good error messages
6. **One class at a time**: Don't rush, be systematic

## 📞 Need More Help?

1. Check `README.md` for detailed guide
2. Check `CONVERSION_SUMMARY.md` for progress tracking
3. Look at converted examples in this folder
4. Review pytest docs: https://docs.pytest.org/
