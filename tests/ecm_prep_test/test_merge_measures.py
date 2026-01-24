"""Test merge_measures and apply_pkg_benefits functions for package measures.

This test module uses pre-extracted test data from the original unittest class.
The test data is stored in a pickle file (test_data/merge_measures_test_data.pkl)
which contains all the complex setup data (~3,350 lines) in a compact form.

## Pickle File Generation

The pickle file is generated from the original unittest class using a data generator script.
This allows us to preserve all the complex test data while keeping the test file readable.

### To regenerate the pickle file:

```bash
python tests/ecm_prep_test/data_generators/dump_merge_test_data.py
```

### What's in the pickle file:

- Complex Measure and MeasurePackage objects
- Sample microsegment and competition data
- Various option configurations (Namespace objects)
- Expected output dictionaries for validation
- Cost conversion data

### Source:

The original data comes from `MergeMeasuresandApplyBenefitsTest.setUpClass()` in
`tests/ecm_prep_test/archive/ecm_prep_test_ORIGINAL.py` (the archived monolithic test file).

**Note:** If you modify the source code that generates test data, you must regenerate
the pickle file to ensure tests remain accurate.
"""

import pytest
import pickle
from pathlib import Path
from .conftest import dict_check


class TestMergeMeasures:
    """Test 'merge_measures' and 'apply_pkg_benefits' functions.

    Ensure that the 'merge_measures' function correctly assembles a series of
    attributes for individual measures into attributes for a packaged measure,
    and that the 'apply_pkg_benefits' function correctly applies additional
    energy savings and installed cost benefits for a package measure.
    """

    @pytest.fixture(scope="class")
    def test_data(self):
        """Load pre-extracted test data from pickle file.
        
        The test data was extracted from the original MergeMeasuresandApplyBenefitsTest
        class using data_generators/dump_merge_test_data.py. This approach keeps the test
        file manageable while preserving all the complex test scenarios.
        
        The pickle file contains 20 attributes including Measure objects, MeasurePackage
        objects, microsegment data, competition data, and various option configurations.
        """
        pickle_file = Path(__file__).parent / "test_data" / "merge_measures_test_data.pkl"
        
        if not pickle_file.exists():
            pytest.fail(
                f"Test data file not found: {pickle_file}\n"
                "Run 'python tests/ecm_prep_test/dump_merge_test_data.py' to generate it."
            )
        
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
        
        return data

    def test_merge_measure_highlevel(self, test_data):
        """Test high-level 'merge_measures' outputs given valid inputs."""
        sample_packages = test_data['sample_package_in_test1_highlevel']
        expected_markets = test_data['markets_ok_out_test1']
        opts = test_data['opts']
        
        for ind, m in enumerate(sample_packages):
            # Check for/record any potential heating/cooling equip/env measure
            # overlaps in the package
            m.htcl_adj_rec(opts)
            # Merge packaged measure data
            m.merge_measures(opts)
            # Check for correct high-level markets for packaged measure under
            # the technical potential scenario only
            dict_check(
                m.markets["Technical potential"]["master_mseg"],
                expected_markets[ind]
            )

    def test_merge_measure_env_costs(self, test_data):
        """Test 'merge_measures' outputs given addition of envelope costs."""
        sample_package = test_data['sample_package_in_test1_env_costs']
        expected_markets = test_data['markets_ok_out_test1_env_costs']
        opts_env_costs = test_data['opts_env_costs']
        
        # Check for/record any potential heating/cooling equip/env measure
        # overlaps in the package
        sample_package.htcl_adj_rec(opts_env_costs)
        # Merge packaged measure data
        sample_package.merge_measures(opts_env_costs)
        # Check for correct high-level markets for packaged measure under
        # the technical potential scenario only, given envelope cost adder
        dict_check(
            sample_package.markets["Technical potential"]["master_mseg"],
            expected_markets
        )

    def test_merge_measure_detailed(self, test_data):
        """Test detailed 'merge_measures' outputs given valid inputs."""
        sample_package = test_data['sample_package_in_test1_attr_breaks']
        expected_attrs = test_data['genattr_ok_out_test1']
        expected_breaks = test_data['breaks_ok_out_test1']
        expected_contrib = test_data['contrib_ok_out_test1']
        opts = test_data['opts']
        
        # Check for/record any potential heating/cooling equip/env measure
        # overlaps in the package
        sample_package.htcl_adj_rec(opts)
        # Merge packaged measure data
        sample_package.merge_measures(opts)
        
        output_lists = [
            sample_package.name,
            sample_package.climate_zone,
            sample_package.bldg_type,
            sample_package.structure_type,
            sample_package.fuel_type["primary"],
            sample_package.end_use["primary"]
        ]
        
        # Test measure attributes (climate, building type, end use, etc.)
        for ind in range(0, len(output_lists)):
            assert sorted(expected_attrs[ind]) == sorted(output_lists[ind])
        
        # Test detailed output breakouts
        dict_check(
            sample_package.markets["Technical potential"]["mseg_out_break"],
            expected_breaks
        )
        
        # Test contributing microsegments
        dict_check(
            sample_package.markets["Technical potential"]["mseg_adjust"][
                "contributing mseg keys and values"],
            expected_contrib
        )

    def test_apply_pkg_benefits(self, test_data):
        """Test 'apply_pkg_benefits' function given valid inputs."""
        sample_package = test_data['sample_package_in_test2']
        mseg_input = test_data['mseg_ok_in_test2']
        expected_mseg = test_data['mseg_ok_out_test2']
        
        result = sample_package.apply_pkg_benefits(
            mseg_input,
            adopt_scheme="Technical potential",
            cm_key=""
        )
        
        dict_check(result, expected_mseg)

    def test_merge_measure_sect_shapes(self, test_data):
        """Test 'merge_measures' sector_shape outputs given valid inputs."""
        # Package without additional performance/cost benefits
        sample_package = test_data['sample_package_in_sect_shapes']
        expected_shapes = test_data['sect_shapes_ok_out']
        opts_sect_shapes = test_data['opts_sect_shapes']
        
        # Check for/record any potential heating/cooling equip/env measure
        # overlaps in the package
        sample_package.htcl_adj_rec(opts_sect_shapes)
        # Merge packaged measure data
        sample_package.merge_measures(opts_sect_shapes)
        # Check for correct sector shapes output for packaged measure under
        # the technical potential scenario only
        dict_check(
            sample_package.sector_shapes["Technical potential"],
            expected_shapes
        )
        
        # Package with additional performance/cost benefits
        sample_package_bens = test_data['sample_package_in_sect_shapes_bens']
        expected_shapes_bens = test_data['sect_shapes_ok_out_bens']
        
        # Check for/record any potential heating/cooling equip/env measure
        # overlaps in the package
        sample_package_bens.htcl_adj_rec(opts_sect_shapes)
        # Merge packaged measure data
        sample_package_bens.merge_measures(opts_sect_shapes)
        # Check for correct sector shapes output for packaged measure under
        # the technical potential scenario only
        dict_check(
            sample_package_bens.sector_shapes["Technical potential"],
            expected_shapes_bens
        )
