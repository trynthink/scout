from unittest.mock import patch, call
import baseline_calculator_code_2a 
import unittest
import json
import numpy as np
import collections
import os
import sys


class Useful_json_translators(object):
    def __init__(self):
        ## Dict translators for building class, end use, and fuel type found on in the EIA data
        # Dict of building class
        self.bldg_class_translator = {'residential': 'RESD', 'commercial': 'COMM'}

        #Dict of end uses
        self.end_use_translator = {'clothes washers': 'CLW', 'clothes dryers': 'CDR', 'computers': 'CMPR', 'cooking': 'CGR', 'computing': 'OTHEQPPC' ,
        'delivered energy':'DELE', 'dishwashers': 'DSW', 'fans and pumps': 'FPR', 'freezers': 'FRZ', 'lighting': 'LGHTNG', 'office equipment': 'OTHEQPNPC',
        'other uses': 'OTHU','refrigeration': 'REFR', 'cooling': 'SPC', 'heating': 'SPH', 'TVs': 'TVR', 'ventilation': 'VNTC', 'water Heating': 'WTHT' }
        
        #Dict of fuel type, electricity is residential
        # purchased electricity is for commercial
        self.fuel_type_translator = {'electricity': 'ELC', 'Purchased Electricity': 'PRC', 'natural gas': 'NG'}


class Set_Up_Test_Data(unittest.TestCase):
    """ Test downstream functions by importing test data """
    ## Read in test data
    ## Reads json file and puts file information into dict form 
    ## May decide later to hardcode all the data in instead of importing like below
    @classmethod
    def importing_test_data(self):
        with open('test_json_traverse.json') as f:
            data_dict = json.load(f)

## Patching information from the test data
class test_refrig_data(unittest.TestCase):
    # Define variables that will be used often in functions below
    json_dicts = Useful_json_translators()

    # Specify dummy data name list as input to data_getter function
    # Similar to filter strings 
    refrig_strings =  ['refrigeration'] 

    # Test#1: Refrigeration values ; later can combine both test for refrig and heating into a for loop
    # Specify expected output for refigeration data name; should be output to data_getter function
    expected_refrig_years = np.array(['2015', '2016'])

    # Desired format : dict of aggregated energy values as np array
    expected_refrig_array = np.array([68, 74])

    # Patching in refrigeration test data instead of calling EIA API
    # Process:  Patch EIA API function call (api_query); return data set to test data;
    @patch('baseline_calculator_code_2a.api_query')
    def test_mock_refrig_EIA_API(self, mock_refrig_test_data):
        # Set return value from mocked function 
        # to summed refrigeration values from test data
        mock_refrig_test_data.return_value = [['2016', 74], ['2015', 68]]

        # Call function inside which mock is applied; includes patch at the api query
        # Output_dict_refrig_data (y) is {'residential': array([228, 258])}  <class 'dict'>
        # mock_refrig_years is ['2015' '2016'] <class 'numpy.ndarray'>
        output_dict_refrig_data, mock_refrig_years = baseline_calculator_code_2a.data_getter('',self.refrig_strings, [''])
        
        # Debugging: view output aggregated data and desired data
        #print(output_dict_refrig_data, type(output_dict_refrig_data))
        
        # Debugging: view output years and desired years
        #print(mock_refrig_years, type(mock_refrig_years))

        # Test if patched output from EIA API api query function is the 
        # same as aggregated refrigeration test year
        np.testing.assert_array_equal(self.expected_refrig_years, mock_refrig_years)

        # Test if patched output from EIA API api query is the same as
        # aggeregated refrigeration test data 
        # instead of the interacting with the data on the EIA API
        mock_data_getter_array = output_dict_refrig_data['refrigeration']
        np.testing.assert_almost_equal(mock_data_getter_array, self.expected_refrig_array)

class test_sum_electr_heat_data(unittest.TestCase):
    # Define variables that will be used often in functions below

    # Specify dummy data name list as input to data_getter function
    # Similar to filter strings 
    heating_strings =  ['heating'] 

    # Test#1: Refrigeration values ; later can combine both test for refrig and heating into a for loop
    # Specify expected output for refigeration data name; should be output to data_getter function
    expected_heating_years = np.array(['2015', '2016'])

    # Desired format : dict of aggregated energy values as np array
    expected_heating_array = np.array([160, 184])

    # Patching in electric heating test data instead of calling EIA API
    # Process:  Patch EIA API function call (api_query); return data set to test data;
    @patch('baseline_calculator_code_2a.api_query')
    def test_electr_heat_mock_EIA_API(self, mock_heating_test_data):
        # Set return value from mocked function 
        # to summed refrigeration values from test data
        mock_heating_test_data.return_value = [['2016',184 ], ['2015', 160]]

        ## Call function inside which mock is applied; includes patch at the api query
        # Output_dict_refrig_data (y) is {'residential': array([228, 258])}  <class 'dict'>
        # mock_refrig_years is ['2015' '2016'] <class 'numpy.ndarray'>
        output_dict_heating_data, mock_heating_years = baseline_calculator_code_2a.data_getter('',self.heating_strings, [''])
        
        ## Debugging: view output aggregated data and desired data
        #print(output_dict_heating_data, type(output_dict_heating_data))
        
        # Debugging: view output years and desired years
        #print(mock_refrig_years, type(mock_refrig_years))

        # Test if patched output from EIA API api query function is the 
        # same as aggregated refrigeration test year
        np.testing.assert_array_equal(self.expected_heating_years, mock_heating_years)

        # Test if patched output from EIA API api query is the same as
        # aggeregated refrigeration test data 
        # instead of the interacting with the data on the EIA API
        mock_heat_data_getter_array = output_dict_heating_data['heating']
        np.testing.assert_almost_equal(mock_heat_data_getter_array, self.expected_heating_array)

class test_recursive_func(unittest.TestCase):

    # Set known inputs to recursive function 
    recursive_refrig_input = ['residential','electricity', 'refrigeration']

    # Set expected output to recursive function
    # Should be aggregated values from 2015, 2016
    expected_recursive_output = np.array([68, 74])

    # Testing the operation of the recursive function
    def test_recursive_refrig(self):
        # Test output of recursive function with hardcore value
        recursive_output = baseline_calculator_code_2a.recursive(Set_Up_Test_Data.importing_test_data(), self.recursive_refrig_input, np.zeros(2), np.zeros(2))

        # Verify if outputs are the same
        np.testing.assert_array_equal(recursive_output, self.expected_recursive_output)

class test_data_comparsion_try_else_block(unittest.TestCase):
    # Test the try block cases
    try_block_input = ['residential','electricity','refrigeration']

    # Test expected output to try block
    # Expected output is the output of the recursive function
    # Output of the recursive function calls the else block
    # Else block calls the EIA API with try_block_input
    # Currently, not using try_block_input
    expected_array_try_data = np.array([68, 74])
    expected_array_try_years = np.array(['2015', '2016'])


    # Testing the operation of try block, if successful ,calls else block
    @patch('baseline_calculator_code_2a.api_query')
    def test_else_block(self, mock_try_data):
        mock_try_data.return_value = [['2016', 74], ['2015', 68]]

        # Call EIA API, output arrays are aggregated energy values and years
        output_array_eia_data, output_array_eia_years = baseline_calculator_code_2a.data_getter('',self.try_block_input, [''])
    
        # De-bugging 
        #print(output_array_eia_data)
        
        # Test if np array output from try/else block equals mock EIA API data
        # Matches expected array
        mock_try_array = output_array_eia_data['residential']
        np.testing.assert_almost_equal(mock_try_array, self.expected_array_try_data)

        # Test if years are equal
        np.testing.assert_array_equal(output_array_eia_years, self.expected_array_try_years)

class test_data_comparsion_expect_block(unittest.TestCase):
    # Purposely input only bldg class and end use for input into
    # recursive function to trigger exception
    filter_str_exception = ['residential','refrigeration']
    
    # Text expected to be printed to the stdout by the except block
    expected_except_print = None #('Incorrect number of index, check:', filter_str_exception)

    def test_except_print(self):
        json_dicts = Useful_json_translators()
        import_test_data = Set_Up_Test_Data()

        mock_print = baseline_calculator_code_2a.data_comparsion(Set_Up_Test_Data.importing_test_data(), self.filter_str_exception, (np.zeros(2), np.zeros(2)))

        ## De-bugging purposes, if an error is triggered, this print will output None
        #print(mock_print)

        ## Test that printed output from the except block matches the expected string
        ## Only catches raised error if its located inside its corresponding try block
        self.assertEqual(mock_print, self.expected_except_print)
        #self.assertEqual(mock_print.mock_calls[0][1][0], self.expected_except_print)

class test_differ_EIA_series_IDs(unittest.TestCase):
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

    ## Residental,freezer, electricity
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
        self.assertEqual(resd_frz_eia_series_ID,self.expected_resd_frz_series_id)


# class test_real_data_recursive_func(unittest.TestCase):
#     ## Initialize real data
#     json_dicts = Useful_json_translators()
#     # Set known inputs to recursive function 
#     recursive_refrig_input = ['residential','electricity', 'refrigeration']

#     # Set expected output to recursive function
#     # Should be aggregated values from 2015, 2016
#     expected_recursive_output = np.array([68, 74])

#     # Testing the operation of the recursive function
#     def test_real_data_refrig(self):
#         # Test output of recursive function with hardcore value
#         real_data_recursive_output = baseline_calculator_code_2a.recursive(self.data_dict, self.recursive_refrig_input, np.zeros(2))

#         # Verify if outputs are the same
#         np.testing.assert_array_equal(real_data_recursive_output, self.expected_recursive_output)

if __name__ == '__main__':
    unittest.main()

