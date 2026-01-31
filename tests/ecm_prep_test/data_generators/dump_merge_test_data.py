"""Dump the MergeMeasuresandApplyBenefitsTest data to pickle files for reuse in pytest."""

import pickle
import sys
import importlib.util
from pathlib import Path

# Add parent directories to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import the original unittest class from the archived monolithic file
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

    # Create test_data directory (parent of data_generators)
    test_data_dir = Path(__file__).parent.parent / "test_data"
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

    file_size = pickle_file.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    print(f"\n[SUCCESS] Saved test data to: {pickle_file}")
    print(f"  File size: {file_size_mb:.2f} MB")

    # Also save a summary with enhanced format
    summary_file = test_data_dir / "merge_measures_test_data_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("MergeMeasuresandApplyBenefitsTest Data Summary\n")
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

            f.write(f"{attr_name:45s} {attr_type:25s} {size_info}\n")

        # Add detailed examples for key attributes
        f.write("\n")
        f.write("=" * 80 + "\n")
        f.write("Detailed Examples\n")
        f.write("=" * 80 + "\n\n")

        # Show structure of some key attributes
        examples = {
            'opts': ['Namespace with configuration options'],
            'sample_package_in_test1_highlevel': ['List of MeasurePackage instances', 'Contains 3 packages for testing high-level merge operations'],
            'markets_ok_out_test1': ['Expected market data outputs', 'List of 3 market dicts with keys: year, climate_zone, region'],
            'mseg_ok_in_test2': ['Microsegment input data', 'Dict with keys: stock, energy, carbon, cost, lifetime'],
        }

        for attr_name, description in examples.items():
            if attr_name in test_data:
                f.write(f"{attr_name}:\n")
                for line in description:
                    f.write(f"  {line}\n")
                
                # Show first-level structure for dicts
                attr_value = test_data[attr_name]
                if isinstance(attr_value, dict) and len(attr_value) <= 10:
                    f.write(f"  Keys: {list(attr_value.keys())}\n")
                elif isinstance(attr_value, list) and len(attr_value) > 0:
                    f.write(f"  First item type: {type(attr_value[0]).__name__}\n")
                
                f.write("\n")

    print(f"[SUCCESS] Saved summary to: {summary_file}")
    print("\nDone!")


if __name__ == "__main__":
    main()
