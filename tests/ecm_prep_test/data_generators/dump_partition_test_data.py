"""Dump the PartitionMicrosegmentTest data to pickle files for reuse in pytest."""

import pickle
import sys
import os
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
    
    # Create test_data directory
    test_data_dir = Path(__file__).parent / "test_data"
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
    
    print(f"\n[SUCCESS] Saved test data to: {pickle_file}")
    print(f"  File size: {pickle_file.stat().st_size / 1024 / 1024:.2f} MB")
    
    # Also save a summary
    summary_file = test_data_dir / "partition_microsegment_test_data_summary.txt"
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("PartitionMicrosegment Test Data Summary\n")
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
