"""Dump the MergeMeasuresandApplyBenefitsTest data to pickle files for reuse in pytest."""

import pickle
import sys
import os
import importlib.util
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the original unittest class from the archived monolithic file
import importlib.util
spec = importlib.util.spec_from_file_location(
    "ecm_prep_test_original",
    Path(__file__).parent.parent / "archive" / "ecm_prep_test_ORIGINAL.py"
)
orig_tests = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orig_tests)

MergeMeasuresandApplyBenefitsTest = orig_tests.MergeMeasuresandApplyBenefitsTest


def main():
    """Extract and save test data to pickle files."""
    print("Setting up MergeMeasuresandApplyBenefitsTest class...")
    
    # Call setUpClass to initialize all class variables
    MergeMeasuresandApplyBenefitsTest.setUpClass()
    
    # Create test_data directory
    test_data_dir = Path(__file__).parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)
    
    # Dictionary to store all the data we need
    test_data = {}
    
    # Extract class-level data
    class_attrs = [
        'cost_convert_data',
        'opts',
        'opts_env_costs',
        'opts_sect_shapes',
        'sample_package_in_test1_highlevel',
        'sample_package_in_test1_env_costs',
        'sample_package_in_test1_attr_breaks',
        'sample_package_in_test2',
        'sample_package_in_sect_shapes',
        'sample_package_in_sect_shapes_bens',
        'markets_ok_out_test1',
        'markets_ok_out_test1_env_costs',
        'genattr_ok_out_test1',
        'breaks_ok_out_test1',
        'contrib_ok_out_test1',
        'sect_shapes_ok_out',
        'sect_shapes_ok_out_bens',
        'mseg_ok_in_test2',
        'mseg_ok_out_test2'
    ]
    
    print("\nExtracting data...")
    for attr_name in class_attrs:
        if hasattr(MergeMeasuresandApplyBenefitsTest, attr_name):
            attr_value = getattr(MergeMeasuresandApplyBenefitsTest, attr_name)
            test_data[attr_name] = attr_value
            print(f"  [OK] {attr_name}")
        else:
            print(f"  [MISSING] {attr_name}")
    
    # Save to pickle file
    pickle_file = test_data_dir / "merge_measures_test_data.pkl"
    with open(pickle_file, 'wb') as f:
        pickle.dump(test_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    
    print(f"\n[SUCCESS] Saved test data to: {pickle_file}")
    print(f"  File size: {pickle_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Also save a summary
    summary_file = test_data_dir / "merge_measures_test_data_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("MergeMeasures Test Data Summary\n")
        f.write("=" * 80 + "\n\n")
        for attr_name, attr_value in test_data.items():
            f.write(f"{attr_name}:\n")
            f.write(f"  Type: {type(attr_value).__name__}\n")
            if isinstance(attr_value, (list, tuple)):
                f.write(f"  Length: {len(attr_value)}\n")
            elif isinstance(attr_value, dict):
                f.write(f"  Keys: {len(attr_value)} keys\n")
            f.write("\n")
    
    print(f"[SUCCESS] Saved summary to: {summary_file}")
    print("\nDone!")


if __name__ == "__main__":
    main()
