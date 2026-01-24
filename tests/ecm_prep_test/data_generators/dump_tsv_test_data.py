"""Extract test data from TimeSensitiveValuationTest to pickle file.

This script dynamically loads the original ecm_prep_test.py file,
executes the TimeSensitiveValuationTest.setUpClass() method, and serializes
all class attributes to a pickle file for use in the pytest version.

Usage:
    python tests/ecm_prep_test/dump_tsv_test_data.py
"""

import pickle
import importlib.util
import sys
from pathlib import Path

def main():
    print("=" * 80)
    print("TimeSensitiveValuationTest Data Extraction")
    print("=" * 80)
    
    # Add the workspace root to sys.path so imports work
    workspace_root = Path(__file__).parent.parent.parent
    if str(workspace_root) not in sys.path:
        sys.path.insert(0, str(workspace_root))
    
    # Load the original ecm_prep_test.py module from archive
    print("\n[1/4] Loading original ecm_prep_test_ORIGINAL.py from archive...")
    ecm_prep_test_path = Path(__file__).parent.parent / "archive" / "ecm_prep_test_ORIGINAL.py"
    
    if not ecm_prep_test_path.exists():
        print(f"[ERROR] File not found: {ecm_prep_test_path}")
        sys.exit(1)
    
    spec = importlib.util.spec_from_file_location(
        "ecm_prep_test_original",
        ecm_prep_test_path
    )
    orig_tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(orig_tests)
    
    TimeSensitiveValuationTest = orig_tests.TimeSensitiveValuationTest
    print("   [OK] Module loaded")
    
    # Execute setUpClass to initialize all test data
    print("\n[2/4] Executing TimeSensitiveValuationTest.setUpClass()...")
    print("   (This may take a while due to complex setup...)")
    
    try:
        TimeSensitiveValuationTest.setUpClass()
        print("   [OK] setUpClass completed")
    except Exception as e:
        print(f"   [ERROR] setUpClass failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    # Extract all class attributes
    print("\n[3/4] Extracting test data...")
    
    test_data = {}
    
    # Get all non-private class attributes
    for attr_name in dir(TimeSensitiveValuationTest):
        if not attr_name.startswith('_') and attr_name not in ['setUpClass', 'tearDownClass']:
            try:
                attr_value = getattr(TimeSensitiveValuationTest, attr_name)
                # Skip methods
                if not callable(attr_value):
                    test_data[attr_name] = attr_value
            except Exception as e:
                print(f"   [WARNING] Could not extract {attr_name}: {e}")
    
    print(f"   [OK] Extracted {len(test_data)} attributes")
    
    # Show some key attributes
    print("\n   Key attributes extracted:")
    key_attrs = ['opts_tsv_features', 'opts_tsv_metrics', 'sample_tsv_data',
                 'ok_tsv_measures_in_features', 'ok_tsv_measures_in_metrics']
    for attr in key_attrs:
        if attr in test_data:
            print(f"      - {attr}: {type(test_data[attr])}")
    
    # Save to pickle file
    print("\n[4/4] Saving to pickle file...")
    output_dir = Path(__file__).parent / "test_data"
    output_dir.mkdir(exist_ok=True)
    
    pickle_file = output_dir / "tsv_test_data.pkl"
    
    try:
        with open(pickle_file, 'wb') as f:
            pickle.dump(test_data, f, protocol=pickle.HIGHEST_PROTOCOL)
        
        file_size = pickle_file.stat().st_size
        file_size_mb = file_size / (1024 * 1024)
        
        print(f"   [OK] Saved to: {pickle_file}")
        print(f"   [OK] File size: {file_size_mb:.2f} MB")
    except Exception as e:
        print(f"   [ERROR] Failed to save pickle: {e}")
        sys.exit(1)
    
    # Create summary file
    print("\n[5/4] Creating summary file...")
    summary_file = output_dir / "tsv_test_data_summary.txt"
    
    with open(summary_file, 'w') as f:
        f.write("TimeSensitiveValuationTest Data Summary\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"Total attributes: {len(test_data)}\n")
        f.write(f"Pickle file size: {file_size_mb:.2f} MB\n\n")
        f.write("Attributes:\n")
        f.write("-" * 80 + "\n")
        
        for attr_name in sorted(test_data.keys()):
            attr_value = test_data[attr_name]
            attr_type = type(attr_value).__name__
            
            # Add size info for containers
            size_info = ""
            if isinstance(attr_value, (list, tuple)):
                size_info = f" (length: {len(attr_value)})"
            elif isinstance(attr_value, dict):
                size_info = f" (keys: {len(attr_value)})"
            
            f.write(f"{attr_name:40s} {attr_type:20s} {size_info}\n")
    
    print(f"   [OK] Summary saved to: {summary_file}")
    
    print("\n" + "=" * 80)
    print("[SUCCESS] Data extraction complete!")
    print("=" * 80)
    print(f"\nPickle file: {pickle_file}")
    print(f"Summary file: {summary_file}")
    print(f"\nYou can now run: pytest tests/ecm_prep_test/test_time_sensitive_valuation.py")

if __name__ == "__main__":
    main()
