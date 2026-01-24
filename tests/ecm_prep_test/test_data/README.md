# Test Data Directory

This directory contains extracted test data for large test classes.

## Files

### merge_measures_test_data.pkl
Pickled test data extracted from `MergeMeasuresandApplyBenefitsTest`.
- **Size**: ~3.5 MB
- **Purpose**: Contains all test fixtures, sample measures, and expected outputs
- **Used by**: `test_merge_measures.py`

### merge_measures_test_data_summary.txt
Human-readable summary of the pickle file contents.

## Regenerating Test Data

If you need to regenerate the test data (e.g., after changes to the source code):

```bash
cd tests/ecm_prep_test
python dump_merge_test_data.py
```

This will:
1. Load the original `MergeMeasuresandApplyBenefitsTest` unittest class
2. Execute the `setUpClass` method to generate all test data
3. Extract and save the data to `merge_measures_test_data.pkl`

## Why Use Pickle Files?

The original `MergeMeasuresandApplyBenefitsTest` class had **3,350 lines of setup code** 
defining complex nested data structures. Extracting this to a pickle file:

- ✅ Reduces test file from 3,507 lines to 158 lines (95% reduction!)
- ✅ Makes tests more maintainable and readable
- ✅ Preserves exact data structures without manual JSON conversion
- ✅ Keeps all test scenarios while dramatically improving clarity

## Alternative: JSON Files

For even more transparency, the data could be converted to JSON format, but:
- JSON doesn't support all Python types (like custom objects)
- Would require manual serialization/deserialization logic
- Pickle is faster and maintains exact Python object structure

For test data that's primarily dicts/lists, JSON is preferable. For complex
objects like `MeasurePackage` instances, pickle is more practical.
