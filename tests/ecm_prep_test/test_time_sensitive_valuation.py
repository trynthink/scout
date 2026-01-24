"""Test time-sensitive valuation functions.

This test module uses pre-extracted test data from the original unittest class.
The test data is stored in a pickle file (test_data/tsv_test_data.pkl)
which contains all the complex setup data in a compact form.

## Pickle File Generation

To regenerate the pickle file:
```bash
python tests/ecm_prep_test/data_generators/dump_tsv_test_data.py
```

Source: `TimeSensitiveValuationTest.setUpClass()` in
`tests/ecm_prep_test/archive/ecm_prep_test_ORIGINAL.py`

The original TimeSensitiveValuationTest class had 44,697 lines, with the vast majority
being setup data. This version verifies that the gen_tsv_facts and apply_tsv functions
work correctly with various measure configurations.
"""

import pytest
import pickle
from pathlib import Path

from .conftest import dict_check


class TestTimeSensitiveValuation:
    """Test the 'gen_tsv_facts' and 'apply_tsv' functions.

    Ensure that these functions properly generate a set of factors used
    to reweight energy, cost, and carbon data to reflect time sensitive
    valuation of energy efficiency.
    """

    @pytest.fixture(scope="class")
    def test_data(self):
        """Load pre-extracted test data from pickle file.
        
        The test data was extracted from the original unittest class using
        dump_tsv_test_data.py. This approach keeps the test file manageable
        while preserving all the complex test scenarios.
        """
        pickle_file = Path(__file__).parent / "test_data" / "tsv_test_data.pkl"
        
        if not pickle_file.exists():
            pytest.fail(
                f"Test data file not found: {pickle_file}\n"
                "Run 'python tests/ecm_prep_test/dump_tsv_test_data.py' to generate it."
            )
        
        with open(pickle_file, 'rb') as f:
            data = pickle.load(f)
        
        return data

    def test_load_modification(self, test_data):
        """Test 'gen_tsv_facts' and nested 'apply_tsv' given valid inputs.
        
        This test covers both TSV features and TSV metrics functionality.
        """
        # Tests for measures with time sensitive valuation features
        for idx, measure in enumerate(test_data['ok_tsv_measures_in_features']):
            # Generate and test re-weighting factors against expected values
            gen_tsv_facts_out_features = measure.gen_tsv_facts(
                test_data['sample_tsv_data'],
                test_data['sample_mskeys_features'],
                test_data['sample_bldg_sect'],
                test_data['sample_cost_convert'],
                test_data['opts_tsv_features'],
                test_data['sample_cost_energy_meas']
            )
            dict_check(
                gen_tsv_facts_out_features[0],
                test_data['ok_tsv_facts_out_features'][idx]
            )
        
        # Test for measure with time sensitive valuation metrics
        for idx in range(len(test_data['ok_tsv_measures_in_metrics'])):
            measure = test_data['ok_tsv_measures_in_metrics'][idx]
            # Generate and test re-weighting factors against expected values
            gen_tsv_facts_out_metrics = measure.gen_tsv_facts(
                test_data['sample_tsv_data'],
                test_data['sample_mskeys_metrics'][idx],
                test_data['sample_bldg_sect'],
                test_data['sample_cost_convert'],
                test_data['opts_tsv_metrics'][idx],
                test_data['sample_cost_energy_meas']
            )
            dict_check(
                gen_tsv_facts_out_metrics[0],
                test_data['ok_tsv_facts_out_metrics'][idx]
            )
