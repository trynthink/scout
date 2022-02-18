""" Tests for processing automated baseline calculator. """

from unittest.mock import patch, call
import baseline_calculator_code_2e
from baseline_calculator_code_2e import Useful_json_translators, fuzzy_dict_equal
import converter
from converter import data_processor
import unittest
import json
import numpy as np
import collections
import os
import sys


class test_Set_Up_Test_Data_func(unittest.TestCase):
    """ Tests downstream functions by importing test data """
    # Read in test data
    # Reads json file and puts file information into dict form 
    # May decide later to hardcode all the data in instead of importing like below
    @classmethod
    def importing_test_data(self):
        with open('test_json_traverse_v2.json') as f:
            self.data_dict = json.load(f)
            return self.data_dict


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


class test_data_getter_func(unittest.TestCase):
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
    @patch('baseline_calculator_code_2e.api_query')
    def test_mock_refrig_data(self, mock_refrig_test_data):
        """ Tests the function and output of patching in refrigeration test data instead of executing a EIA API query call. """
        
        # Set return value to expected output of aggregated refrigeration values in test data 
        mock_refrig_test_data.return_value = [['2016', 37], ['2015', 34]]

        # Call function inside which mock is applied; includes patch at the api query
        output_dict_refrig_data, mock_refrig_years = baseline_calculator_code_2e.data_getter('', self.refrig_strings, [''])
        
        # Test if patched output from EIA API api query function is the 
        # same as aggregated refrigeration test year
        np.testing.assert_array_equal(self.expected_refrig_years, mock_refrig_years)

        # Test if patched output from EIA API api query is the same as
        # aggeregated refrigeration test data 
        # instead of the interacting with the data on the EIA API
        mock_data_getter_array = output_dict_refrig_data['refrigeration']
        np.testing.assert_almost_equal(mock_data_getter_array, self.expected_refrig_array)

    # Patching in electric heating test data instead of calling EIA API
    @patch('baseline_calculator_code_2e.api_query')
    def test_mock_electr_heat_data(self, mock_heating_test_data):
        """ Tests the function and output of patching in heating test data instead of executing a EIA API query call. """

        # Set return value from mocked function 
        # to summed refrigeration values from test data
        mock_heating_test_data.return_value = [['2016',92 ], ['2015', 80]]

        # Call api query function to test patch
        output_dict_heating_data, mock_heating_years = baseline_calculator_code_2e.data_getter('', self.heating_strings, [''])

        # Test if patched output from EIA API api query function is the 
        # same as aggregated refrigeration test year
        np.testing.assert_array_equal(self.expected_heating_years, mock_heating_years)

        # Test if patched output from EIA API api query is the same as
        # aggeregated refrigeration test data 
        # instead of the interacting with the data on the EIA API
        mock_heat_data_getter_array = output_dict_heating_data['heating']
        np.testing.assert_almost_equal(mock_heat_data_getter_array, self.expected_heating_array)


class test_recursive_func(unittest.TestCase):
    """ Tests operation of the recursive function."""
    
    # Inputs for commercial and resdential test cases
    nested_inputs = [['commercial', 'electricity', 'lighting'], ['commercial', 'electricity', 'ventilation'], ['commercial', 'electricity', 'cooling'], ['residential', 'electricity', 'clothes washing'], ['residential', 'electricity', 'other']]

    # Change to a list of np arrays or make bigger with rows and cols of each test case
    expected_nested_recursive_outputs = [({'2016': 104, '2017': 104}), ({'2016': 60, '2017': 48}), ({'2016': 188, '2017': 296}), ({'2015': 14, '2016': 32, '2017': 44}), ({'2015': 111, '2016': 98, '2017': 102})]

    # Testing the operation of the recursive function
    def testing_recursive_func(self):
        """ 
        """
        # Test multiple outputs of filter strings tuple
        for index, filter_strings in enumerate(self.nested_inputs):
            # Call recursive function
            recursive_output = baseline_calculator_code_2e.recursive(test_Set_Up_Test_Data_func.importing_test_data(), filter_strings) 

            # Verify if outputs are the same
            self.assertDictEqual(recursive_output, self.expected_nested_recursive_outputs[index])


class test_construct_EIA_series_ID(unittest.TestCase):
    """ Tests constructing EIA seriesID function.  """

    # Test four different filter string combinations
    
    # Different bldg class and fuel type, same end use
    # Commercial cooking series name and expected series id, natural gas
    comm_cook_series_name = ['commercial', 'natural gas', 'cooking']
    expected_comm_cook_series_id = 'AEO.2020.REF2020.CNSM_NA_COMM_NA_NG_CGR_USA_QBTU.A'

    # Residential cooking series name, electricity
    # https://www.eia.gov/opendata/qb.php?category=3604376&sdid=AEO.2020.REF2020.CNSM_NA_RESD_CGR_ELC_NA_USA_QBTU.A
    resd_cook_series_name = ['residential', 'electricity', 'cooking']
    expected_resd_cook_series_id = 'AEO.2020.REF2020.CNSM_NA_RESD_CGR_ELC_NA_USA_QBTU.A'

    # Residental, freezer, electricity
    # https://www.eia.gov/opendata/qb.php?category=3604376&sdid=AEO.2020.REF2020.CNSM_NA_RESD_FRZ_ELC_NA_USA_QBTU.A
    resd_frz_series_name = ['residential', 'electricity', 'freezers']
    expected_resd_frz_series_id = 'AEO.2020.REF2020.CNSM_NA_RESD_FRZ_ELC_NA_USA_QBTU.A'


    def test_eia_filter_strings(self):
        # Call the construct series ID fun; testing different filter string combos
        comm_cook_eia_series_ID = baseline_calculator_code_2e.construct_EIA_series_ID(self.comm_cook_series_name)
        # COMM cooking
        self.assertEqual(comm_cook_eia_series_ID, self.expected_comm_cook_series_id)

        # RESD cooking
        resd_cook_eia_series_ID = baseline_calculator_code_2e.construct_EIA_series_ID(self.resd_cook_series_name)
        self.assertEqual(resd_cook_eia_series_ID, self.expected_resd_cook_series_id)

        # Test one unusual/different end uses 
        # Combination triggers api query stating not available from API 
        # Freezers
        resd_frz_eia_series_ID = baseline_calculator_code_2e.construct_EIA_series_ID(self.resd_frz_series_name)
        self.assertEqual(resd_frz_eia_series_ID, self.expected_resd_frz_series_id)


class test_fuzzy_dict_equal_func(unittest.TestCase):
    """ 
    """
    # Test Case 1 - Same years + same values
    # Expected output of JSON energy values which comes from mocking EIA API 
    JSON_values_same_yrs_vals = {'2015': 76, '2016': 95, '2017': 111}
    # Expected output of EIA energy values, scaled as in code
    EIA_values_same_yrs_vals = {'2015': 76, '2016': 95, '2017': 111}
    
    def testing_same_vals(self):
        # Call fuzzy_dict_equal function, same years + same values
        # breakpoint()
        output_same_yrs_vals = baseline_calculator_code_2e.fuzzy_dict_equal(self.EIA_values_same_yrs_vals, self.JSON_values_same_yrs_vals, 0.01)
        self.assertTrue(output_same_yrs_vals)

    # Test Case 2 - Same years + differ values w/n precision 
    # Expected output of JSON energy values which comes from mocking EIA API 
    JSON_values_same_yrs_diff_vals_in_prec = {'2015': 76, '2016': 95, '2017': 111}
    # Expected output of EIA energy values, scaled as in code
    EIA_values_same_yrs_diff_vals_in_prec = {'2015': 75.995, '2016': 94.995, '2017': 110.995}
    
    def testing_same_yrs_diff_vals_in_precision(self):
        # Call fuzzy_dict_equal function, same years + differ values w/n precision 
        # breakpoint()
        output_same_yrs_diff_vals = baseline_calculator_code_2e.fuzzy_dict_equal(self.EIA_values_same_yrs_diff_vals_in_prec, self.JSON_values_same_yrs_diff_vals_in_prec, 0.01)
        self.assertTrue(output_same_yrs_diff_vals)

    # Test Case 3 - Same years + differ values outside precision 
    # Expected output of JSON energy values which comes from mocking EIA API 
    JSON_values_same_yrs_diff_vals_no_prec = {'2015': 76, '2016': 95, '2017': 111}
    # Expected output of EIA energy values, scaled as in code
    EIA_values_same_yrs_diff_vals_no_prec = {'2015': 60, '2016': 70, '2017': 200}
    
    def testing_same_yrs_diff_vals_no_precision(self):
        # Call fuzzy_dict_equal function, same years + differ values w/n precision 
        # breakpoint()
        output_same_yrs_diff_vals_outside_prec = baseline_calculator_code_2e.fuzzy_dict_equal(self.EIA_values_same_yrs_diff_vals_no_prec, self.JSON_values_same_yrs_diff_vals_no_prec, 0.01)
        self.assertFalse(output_same_yrs_diff_vals_outside_prec[0])


    # Test Case 4 - Diff years + differ values w/n precision/same values
    # Expected output of JSON energy values which comes from mocking EIA API 
    JSON_values_diff_yrs_n_vals_in_prec = {'2015': 76, '2016': 95, '2017': 111}
    # Expected output of EIA energy values, scaled as in code
    EIA_values_diff_yrs_n_vals_in_prec = {'2016': 95, '2017': 111, '2018': 200}
    
    def testing_diff_vals_n_yrs_in_precision(self):
        # Call fuzzy_dict_equal function, same years + differ values w/n precision 
        # breakpoint()
        output_diff_yrs_diff_vals_in_prec = baseline_calculator_code_2e.fuzzy_dict_equal(self.EIA_values_diff_yrs_n_vals_in_prec, self.JSON_values_diff_yrs_n_vals_in_prec, 0.01)
        self.assertTrue(output_diff_yrs_diff_vals_in_prec)

    # Test Case 5 - Diff years + differ values outside precision 
    # Expected output of JSON energy values which comes from mocking EIA API 
    JSON_values_diff_yrs_n_vals_no_prec = {'2015': 76, '2016': 95, '2017': 111}
    # Expected output of EIA energy values, scaled as in code
    EIA_values_diff_yrs_n_vals_no_prec = {'2016': 200, '2017': 300, '2018': 80}
    
    def testing_diff_vals_n_yrs_no_precision(self):
        # Call fuzzy_dict_equal function, same years + differ values w/n precision 
        # breakpoint()
        output_diff_yrs_n_vals_no_prec = baseline_calculator_code_2e.fuzzy_dict_equal(self.EIA_values_diff_yrs_n_vals_no_prec, self.JSON_values_diff_yrs_n_vals_no_prec, 0.01)
        self.assertFalse(output_diff_yrs_n_vals_no_prec[0])
    
    
class test_data_comparison_func(unittest.TestCase):
    """ Tests the expect block in data comparison function by purposely triggering an IndexError. 
    
    Tests the successful operation of the data comparsion function as if no errors were triggered for a given filter strings.
    """
    
    # Electric heating filter strings
    heat_try_filter_strings = ['residential', 'electricity', 'heating']

    # Expected output of JSON energy values which comes from mocking EIA API 
    expected_JSON_values = {'2015': 76E9, '2016': 95E9, '2017':111E9} 

    # Expected output of EIA energy values, scaled as in code
    expected_EIA_values = {'2015': 76E9, '2016': 95E9, '2017':111E9}


    @patch('baseline_calculator_code_2e.api_query')
    @patch('baseline_calculator_code_2e.recursive')
    def test_try_block(self, mock_JSON, mock_API_EIA):
        # Patch in value in recursive function
        mock_JSON.return_value = {'2015': 76E9, '2016': 95E9, '2017':111E9} 

        # Patch electric heating test data as output of api query function
        mock_API_EIA.return_value = [['2017', 111] ,['2016', 95], ['2015', 76]]

        # Set up parser for command line interface 
        options = baseline_calculator_code_2e.parse_args()

        # Call data comparison function
        # breakpoint()
        EIA_dict_str, EIA_mock_heating_dict, JSON_dict_str, JSON_heating_dict = baseline_calculator_code_2e.data_comparison(test_Set_Up_Test_Data_func().importing_test_data(), self.heat_try_filter_strings, options)
        
        # Verify outputs
        # JSON, expect to pass as mocked recursive function, already testing recursive function in previous test, don't need duplicate test
        np.testing.assert_array_equal(self.expected_JSON_values, JSON_heating_dict)

        #EIA
        np.testing.assert_array_equal(self.expected_EIA_values, EIA_mock_heating_dict)


    # def test_IndexError(self):
    #     # Purposely input only bldg class and end use for input into
    #     # recursive function to trigger exception
    #     filter_str_exception = ['residential','refrigeration']
        
    #     # Set up parser for command line interface 
    #     options = baseline_calculator_code_2e.parse_args()

    #     # Text expected to be printed to the stdout by the except block
    #     expected_except_print = None #('Incorrect number of index, check:', filter_str_exception)

    #     mock_print = baseline_calculator_code_2e.data_comparison(test_Set_Up_Test_Data_func().importing_test_data(), filter_str_exception, options)
    #     #breakpoint()

    #     # Test that printed output from the except block matches the expected string
    #     # Only catches raised error if its located inside its corresponding try block
    #     self.assertEqual(mock_print, expected_except_print)
        #self.assertEqual(mock_print.mock_calls[0][1][0], self.expected_except_print)

class test_parser_args_func(unittest.TestCase):
    # Expected output when user doesn't select verbose 
    expected_output_verbose_off = False

    # Test Case 1: Verbose mode off
    def testing_verbose_mode_off(self):
        # Verbose is False
        options_parsed = baseline_calculator_code_2e.parse_args()
        
        # Convert namespace to a dict
        argparse_dict = vars(options_parsed)
        # Get values from argparse
        output_argparse = argparse_dict.get('verbose')
        # Compare argparse output from expected output
        self.assertEqual(output_argparse, self.expected_output_verbose_off)

    # Expected output when user selects verbose to be on
    expected_output_verbose_on = True
   
    # Test Case 2: Verbose mode on 
    def testing_verbose_mode_on(self):
        # Verbose is True
        options_parsed = baseline_calculator_code_2e.parse_args()
        # breakpoint()
        # Convert namespace to a dict
        argparse_dict = vars(options_parsed)
        # Get values from argparse
        output_argparse = argparse_dict.get('verbose')
        # Compare argparse output from expected output
        self.assertTrue(output_argparse, self.expected_output_verbose_on)


if __name__ == '__main__':
    unittest.main()

