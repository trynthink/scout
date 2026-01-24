"""Test year mapping for TSV cost/carbon data."""

import pytest
from scout.ecm_prep import ECMPrepHelper
from .conftest import dict_check


class TestYrMap:
    """Test 'tsv_cost_carb_yrmap' function.

    Ensure that years available from input 8760 TSV data on cost/carbon are
    correctly mapped to full AEO year set.
    """

    @pytest.fixture(scope="class")
    def test_data(self):
        """Define test data for all tests in this class."""
        data = {
            'test_tsv_data_in': [
                {yr: {} for yr in [str(x) for x in range(2018, 2051, 4)]},
                {yr: {} for yr in [str(x) for x in range(2018, 2047, 4)]},
                {yr: {} for yr in [str(x) for x in range(2014, 2055, 4)]}
            ],
            'test_aeo_years_in': [str(x) for x in range(2015, 2051)],
            'test_out_map': [
                {
                    "2018": [str(x) for x in range(2015, 2022)],
                    "2022": [str(x) for x in range(2022, 2026)],
                    "2026": [str(x) for x in range(2026, 2030)],
                    "2030": [str(x) for x in range(2030, 2034)],
                    "2034": [str(x) for x in range(2034, 2038)],
                    "2038": [str(x) for x in range(2038, 2042)],
                    "2042": [str(x) for x in range(2042, 2046)],
                    "2046": [str(x) for x in range(2046, 2050)],
                    "2050": [str(x) for x in range(2050, 2051)]
                },
                {
                    "2018": [str(x) for x in range(2015, 2022)],
                    "2022": [str(x) for x in range(2022, 2026)],
                    "2026": [str(x) for x in range(2026, 2030)],
                    "2030": [str(x) for x in range(2030, 2034)],
                    "2034": [str(x) for x in range(2034, 2038)],
                    "2038": [str(x) for x in range(2038, 2042)],
                    "2042": [str(x) for x in range(2042, 2046)],
                    "2046": [str(x) for x in range(2046, 2051)]
                },
                {
                    "2014": [str(x) for x in range(2014, 2018)],
                    "2018": [str(x) for x in range(2018, 2022)],
                    "2022": [str(x) for x in range(2022, 2026)],
                    "2026": [str(x) for x in range(2026, 2030)],
                    "2030": [str(x) for x in range(2030, 2034)],
                    "2034": [str(x) for x in range(2034, 2038)],
                    "2038": [str(x) for x in range(2038, 2042)],
                    "2042": [str(x) for x in range(2042, 2046)],
                    "2046": [str(x) for x in range(2046, 2050)],
                    "2050": [str(x) for x in range(2050, 2054)],
                    "2054": []
                }
            ]
        }
        return data

    def test_yrmap(self, test_data):
        """Test 'tsv_cost_carb_yrmap' function given valid inputs."""
        # Loop across all tested year input scenarios
        for ind in range(0, len(test_data['test_tsv_data_in'])):
            # Execute the function
            out_map = ECMPrepHelper.tsv_cost_carb_yrmap(
                test_data['test_tsv_data_in'][ind],
                test_data['test_aeo_years_in']
            )
            # Check function outputs
            dict_check(out_map, test_data['test_out_map'][ind])
