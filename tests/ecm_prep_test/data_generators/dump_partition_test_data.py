"""Dump the PartitionMicrosegmentTest data to pickle files for reuse in pytest."""

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

PartitionMicrosegmentTest = orig_tests.PartitionMicrosegmentTest


def main():
    """Extract and save test data to pickle files."""
    print("Setting up PartitionMicrosegmentTest class...")

    # Call setUpClass to initialize all class variables
    PartitionMicrosegmentTest.setUpClass()

    # Create test_data directory (parent of data_generators)
    test_data_dir = Path(__file__).parent.parent / "test_data"
    test_data_dir.mkdir(exist_ok=True)

    # Dictionary to store all the data we need
    test_data = {}

    # Extract class-level data
    class_attrs = [
        'opts',
        'time_horizons',
        'handyfiles',
        'handyvars',
        'ok_diffuse_params_in',
        'ok_mskeys_in',
        'ok_mskeys_swtch_in',
        'ok_bldg_sect_in',
        'ok_sqft_subst_in',
        'ok_mkt_scale_frac_in',
        'ok_new_bldg_constr',
        'ok_stock_in',
        'ok_energy_in',
        'ok_energy_scnd_in',
        'ok_carb_in',
        'ok_fcarb_in',
        'ok_f_refr_in',
        'ok_base_cost_in',
        'ok_cost_meas_in',
        'ok_cost_energy_base_in',
        'ok_cost_energy_meas_in',
        'ok_relperf_in',
        'ok_life_base_in',
        'ok_life_meas_in',
        'ok_ssconv_base_in',
        'ok_ssconv_meas_in',
        'ok_carbint_base_in',
        'ok_carbint_meas_in',
        'ok_tsv_scale_fracs_in',
        'ok_tsv_shapes_in',
        'ok_out',
        'ok_out_fraction',
        'measure_instance_fraction',
        'measure_instance_bass',
        'measure_instance_fraction_string',
        'measure_instance_bass_string',
        'measure_instance_bad_string',
        'measure_instance_bad_values',
        'measure_instance_wrong_name'
    ]

    print("\nExtracting data...")
    for attr_name in class_attrs:
        if hasattr(PartitionMicrosegmentTest, attr_name):
            attr_value = getattr(PartitionMicrosegmentTest, attr_name)
            test_data[attr_name] = attr_value
            print(f"  [OK] {attr_name}")
        else:
            print(f"  [MISSING] {attr_name}")

    # Save to pickle file
    pickle_file = test_data_dir / "partition_microsegment_test_data.pkl"
    with open(pickle_file, 'wb') as f:
        pickle.dump(test_data, f, protocol=pickle.HIGHEST_PROTOCOL)

    file_size = pickle_file.stat().st_size
    file_size_mb = file_size / (1024 * 1024)

    print(f"\n[SUCCESS] Saved test data to: {pickle_file}")
    print(f"  File size: {file_size_mb:.2f} MB")

    # Also save a summary with enhanced format
    summary_file = test_data_dir / "partition_microsegment_test_data_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("PartitionMicrosegmentTest Data Summary\n")
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
            'opts': ['Namespace with configuration options for partitioning'],
            'handyfiles': ['UsefulInputFiles instance with paths to input data'],
            'handyvars': ['UsefulVars instance with common variables'],
            'ok_stock_in': ['Stock data input for testing', 'Dict with nested climate zone and technology data'],
            'ok_energy_in': ['Energy consumption data', 'Dict with regional breakdowns'],
            'ok_out': ['Expected output after partitioning', 'List of 2 partitioned measure instances'],
            'measure_instance_fraction': ['Measure instance with fraction adoption', 'Uses fractional market penetration model'],
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
