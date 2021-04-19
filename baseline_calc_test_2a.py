""" Tests for processing automated baseline calculator. """

from unittest.mock import patch, call
import baseline_calculator_code_2a
from baseline_calculator_code_2a import Useful_json_translators
import converter
from converter import data_processor
import unittest
import json
import numpy as np
import collections
import os
import sys

# Revist this later, Chioke will investigate data import
class Set_Up_Test_Data(unittest.TestCase):
    """ Tests downstream functions by importing test data """
    # Read in test data
    # Reads json file and puts file information into dict form 
    # May decide later to hardcode all the data in instead of importing like below
    @classmethod
    def importing_test_data(self):
        with open('test_json_traverse.json') as f:
            self.data_dict = json.load(f)
            return self.data_dict

class test_data_getter_fun(unittest.TestCase):
    """ Tests operation of data getter function using the output of aggregated electric refrigeration and heating data.
    
    Data getter calls api query function which executes an EIA API call query using a data series string or seriesID and patching in test data from a JSON data file.
    
    """
    
    # Define variables that will be used often in functions below
    json_dicts = Useful_json_translators()

    # Refrigeration
    # Specify dummy data name list as input to data_getter function 
    refrig_strings =  ['refrigeration'] 
    # Heating
    heating_strings =  ['heating']

    # Specify expected output for refigeration data name; output of data_getter function
    # Refigeration years
    expected_refrig_years = np.array(['2015', '2016'])

    # Heating years
    expected_heating_years = np.array(['2015', '2016'])

    # Desired format : dict of aggregated energy values as np array
    # Refigeration energy values
    expected_refrig_array = np.array([34, 37])

    # Heating energy values
    expected_heating_array = np.array([80, 92])

    # Patching in electric refrigeration test data instead of calling EIA API
    @patch('baseline_calculator_code_2a.api_query')
    def test_mock_refrig_data(self, mock_refrig_test_data):
        """ Tests the function and output of patching in refrigeration test data instead of executing a EIA API query call. """
        
        # Set return value to expected output of aggregated refrigeration values in test data 
        mock_refrig_test_data.return_value = [['2016', 37], ['2015', 34]]

        # Call function inside which mock is applied; includes patch at the api query
        output_dict_refrig_data, mock_refrig_years = baseline_calculator_code_2a.data_getter('', self.refrig_strings, [''])
        
        # Test if patched output from EIA API api query function is the 
        # same as aggregated refrigeration test year
        np.testing.assert_array_equal(self.expected_refrig_years, mock_refrig_years)

        # Test if patched output from EIA API api query is the same as
        # aggeregated refrigeration test data 
        # instead of the interacting with the data on the EIA API
        mock_data_getter_array = output_dict_refrig_data['refrigeration']
        np.testing.assert_almost_equal(mock_data_getter_array, self.expected_refrig_array)

    # Patching in electric heating test data instead of calling EIA API
    @patch('baseline_calculator_code_2a.api_query')
    def test_mock_electr_heat_data(self, mock_heating_test_data):
        """ Tests the function and output of patching in heating test data instead of executing a EIA API query call. """

        # Set return value from mocked function 
        # to summed refrigeration values from test data
        mock_heating_test_data.return_value = [['2016',92 ], ['2015', 80]]

        # Call api query function to test patch
        output_dict_heating_data, mock_heating_years = baseline_calculator_code_2a.data_getter('', self.heating_strings, [''])

        # Test if patched output from EIA API api query function is the 
        # same as aggregated refrigeration test year
        np.testing.assert_array_equal(self.expected_heating_years, mock_heating_years)

        # Test if patched output from EIA API api query is the same as
        # aggeregated refrigeration test data 
        # instead of the interacting with the data on the EIA API
        mock_heat_data_getter_array = output_dict_heating_data['heating']
        np.testing.assert_almost_equal(mock_heat_data_getter_array, self.expected_heating_array)

class test_data_processor_func(unittest.TestCase):
    # Expected mocked years numy array from output of data processor function
    expected_output_mock_years_np = np.array(['2015', '2016'])

    # Expected mocked aggregated energy values numy array from output of data processor function
    expected_output_mock_energy_np = np.array([80, 92])

    # Use patche test electric heating data and corresponding years
    mock_API_query_heat_data = [['2016',92 ], ['2015', 80]]

    # Patch in electric heating test data
    def test_mock_API_query(self):
        """ Tests the data processor function by using the output of the mocked api query function with test data.
        """

        # Call data processor function 
        mocked_heating_data_np, mocked_heating_years_np = converter.data_processor(self.mock_API_query_heat_data)

        # Test if output of data processor is what was expectde
        # Years
        np.testing.assert_array_equal(self.expected_output_mock_years_np, mocked_heating_years_np)

        # Aggregated energy values
        np.testing.assert_array_equal(self.expected_output_mock_energy_np, mocked_heating_data_np)


class test_recursive_func(unittest.TestCase):
    """ Tests operation of the recursive function."""

    # Set known inputs to recursive function 
    recursive_refrig_input = ['residential','electricity', 'refrigeration']

    # Set expected output to recursive function
    # Should be aggregated values from 2015, 2016
    expected_recursive_output = np.array([34, 37])
  
    # Testing the operation of the recursive function
    def test_recursive_refrig(self):
        """ 
        """
        
        # Test output of recursive function with hardcore value
        recursive_output = baseline_calculator_code_2a.recursive(Set_Up_Test_Data.importing_test_data(), self.recursive_refrig_input, np.zeros(2))

        # Verify if outputs are the same
        np.testing.assert_array_equal(recursive_output, self.expected_recursive_output)


class test_data_comparison_func(unittest.TestCase):
    """ Tests the expect block in data comparison function by purposely triggering an IndexError. 
    
    Tests the successful operation of the data comparsion function as if no errors were triggered for a given filter strings.
    """
    # Electric heating filter strings
    heat_try_filter_strings = ['residential', 'electricity', 'heating']

    # Expected output of JSON energy values which comes from mocking EIA API 
    expected_JSON_values = np.array([80., 92.])

    # Expected output of EIA energy values, scaled as in code
    expected_EIA_values =  np.multiply((np.array([80, 92])), 1E9)

    @patch('baseline_calculator_code_2a.api_query')
    def test_try_block(self, mock_API_EIA):
        # Patch electric heating test data as output of api query function
        mock_API_EIA.return_value = [['2016',92 ], ['2015', 80]]

        #  Call data comparison function
        EIA_mock_heating_energy_vals, JSON_heating_energy_vals = baseline_calculator_code_2a.data_comparison(Set_Up_Test_Data().importing_test_data(), self.heat_try_filter_strings)
        #breakpoint()
        
        # Verify outputs
        # JSON, expect to pass as mocked recursive function, already testing recursive function in previous test, don't need duplicate test
        np.testing.assert_array_equal(self.expected_JSON_values, JSON_heating_energy_vals)

        #EIA
        np.testing.assert_array_equal(self.expected_EIA_values, EIA_mock_heating_energy_vals)


    def test_IndexError(self):
        json_dicts = Useful_json_translators()
        import_test_data = Set_Up_Test_Data()

        # Purposely input only bldg class and end use for input into
        # recursive function to trigger exception
        filter_str_exception = ['residential','refrigeration']
        
        # Text expected to be printed to the stdout by the except block
        expected_except_print = None #('Incorrect number of index, check:', filter_str_exception)

        mock_print = baseline_calculator_code_2a.data_comparison(Set_Up_Test_Data().importing_test_data(), filter_str_exception)
        #breakpoint()

        ## Test that printed output from the except block matches the expected string
        ## Only catches raised error if its located inside its corresponding try block
        self.assertEqual(mock_print, expected_except_print)
        #self.assertEqual(mock_print.mock_calls[0][1][0], self.expected_except_print)

class test_differ_EIA_series_IDs(unittest.TestCase):
    """ Tests constructing EIA seriesID function.  """

    ## Test four different filter string combinations
    
    ## Different bldg class and fuel type, same end use
    ## Commercial cooking series name and expected series id, natural gas
    comm_cook_series_name = ['commercial', 'natural gas', 'cooking']
    expected_comm_cook_series_id = 'AEO.2020.REF2020.CNSM_NA_COMM_NA_NG_CGR_USA_QBTU.A'

    ## Residential cooking series name, electricity
    ## https://www.eia.gov/opendata/qb.php?category=3604376&sdid=AEO.2020.REF2020.CNSM_NA_RESD_CGR_ELC_NA_USA_QBTU.A
    resd_cook_series_name = ['residential', 'electricity', 'cooking']
    expected_resd_cook_series_id = 'AEO.2020.REF2020.CNSM_NA_RESD_CGR_ELC_NA_USA_QBTU.A'

    ## Commercial ventilation series name and expected series id, purchased electricity
    ## https://www.eia.gov/opendata/qb.php?category=3604377&sdid=AEO.2020.REF2020.CNSM_NA_COMM_NA_PRC_VNTC_USA_QBTU.A
    comm_vent_series_name = ['commercial', 'Purchased Electricity', 'ventilation']
    expected_comm_vent_series_id = 'AEO.2020.REF2020.CNSM_NA_COMM_NA_PRC_VNTC_USA_QBTU.A'

    ## Residental, freezer, electricity
    ## https://www.eia.gov/opendata/qb.php?category=3604376&sdid=AEO.2020.REF2020.CNSM_NA_RESD_FRZ_ELC_NA_USA_QBTU.A
    resd_frz_series_name = ['residential', 'electricity', 'freezers']
    expected_resd_frz_series_id = 'AEO.2020.REF2020.CNSM_NA_RESD_FRZ_ELC_NA_USA_QBTU.A'

    def test_eia_filter_strings(self):
        ## Call the construct series ID fun; testing different filter string combos
        comm_cook_eia_series_ID = baseline_calculator_code_2a.construct_EIA_series_ID(self.comm_cook_series_name)
        ## COMM cooking
        self.assertEqual(comm_cook_eia_series_ID, self.expected_comm_cook_series_id)

        ## RESD cooking
        resd_cook_eia_series_ID = baseline_calculator_code_2a.construct_EIA_series_ID(self.resd_cook_series_name)
        self.assertEqual(resd_cook_eia_series_ID, self.expected_resd_cook_series_id)

        ## Testing two unusual/different end uses ; these combinations triggered api query stating not available from API
        ## Want to test if the series ID was constructed accurately, if so then truly not present
        ## Ventilation
        comm_vent_eia_series_ID = baseline_calculator_code_2a.construct_EIA_series_ID(self.comm_vent_series_name)
        self.assertEqual(comm_vent_eia_series_ID, self.expected_comm_vent_series_id)

        ## Freezers
        resd_frz_eia_series_ID = baseline_calculator_code_2a.construct_EIA_series_ID(self.resd_frz_series_name)
        self.assertEqual(resd_frz_eia_series_ID, self.expected_resd_frz_series_id)





if __name__ == '__main__':
    unittest.main()

