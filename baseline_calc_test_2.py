### My adapted version of Chioke's EX#1
from unittest.mock import patch
import baseline_calculator_code_2
import unittest
import json
import numpy as np
import collections

## Reads json file and puts file information into dict form i.e. test data
## May decide later to hardcode all the data in instead of importing like below
with open('test_json_traverse.json') as f:
    test_data_dict = json.load(f)


class test_refrig_data(unittest.TestCase):
    ## Define variables that will be used often in functions below

    ## Specify dummy data name list as input to data_getter function
    ## Similar to filter strings 
    refrig_strings =  ['refrigeration'] 

    ## Test#1: Refrigeration values ; later can combine both test for refrig and heating into a for loop
    ## Specify expected output for refigeration data name; should be output to data_getter function
    expected_refrig_years = np.array(['2015', '2016'])
    ## Past: Data type = List of tuples, int
    ## Desired format : dict of aggregated energy values as np array
    expected_refrig_array = np.array([228, 258])


    ## Using Chioke's example #1, my attempt at
    ## mocking requests.get inside api_query from my code file
    @patch('baseline_calculator_code_2.requests.get')
    def test_api_query_from_code(self, mock_code_api):
        ## Set return value from mock_api_response
        mock_code_api.return_value.json.return_value = {'series': [{'data': ['success']}]} #test_data_dict
        
        ## Call function from inside mock
        mock_code_output = baseline_calculator_code_2.api_query('','')
        
        ## View 
        # print(mock_code_api.return_value())
        
        ## Define expected output from test function; might actually be the test data
        test_output = ['success']
        
        ## Compare output from api query function inside code using mocked response with desired output
        self.assertListEqual(mock_code_output, test_output)

    ## My Attempt: Patching in refrigeration test data instead of calling EIA API
    ## Process:  Patch EIA API function call (api_query); return data set to test data;
    @patch('baseline_calculator_code_2.api_query')
    def test_mock_refrig_EIA_API(self, mock_refrig_test_data):
        ## Set return value from mocked function 
        ## to summed refrigeration values from test data
        mock_refrig_test_data.return_value = [['2016', 258], ['2015', 228]]

        ## Call function inside which mock is applied; includes patch at the api query
        ## Output_dict_refrig_data (y) is {'residential': array([228, 258])}  <class 'dict'>
        ## mock_refrig_years is ['2015' '2016'] <class 'numpy.ndarray'>
        output_dict_refrig_data, mock_refrig_years = baseline_calculator_code_2.data_getter('',self.refrig_strings, [''])
        
        ## Debugging: view output aggregated data and desired data
        #print(output_dict_refrig_data, type(output_dict_refrig_data))
        
        ## Debugging: view output years and desired years
        #print(mock_refrig_years, type(mock_refrig_years))

        ## Test if patched output from EIA API api query function is the 
        ## same as aggregated refrigeration test year
        np.testing.assert_array_equal(self.expected_refrig_years, mock_refrig_years)

        ## Test if patched output from EIA API api query is the same as
        ## aggeregated refrigeration test data 
        ## instead of the interacting with the data on the EIA API
        mock_data_getter_array = output_dict_refrig_data['refrigeration']
        np.testing.assert_almost_equal(mock_data_getter_array, self.expected_refrig_array)

class test_recursive_func(unittest.TestCase):
    ## Set known inputs to recursive function 
    recursive_refrig_input = ['residential','electricity', 'refrigeration']

    ## Set expected output to recursive function
    ## Should be aggregated values from 2015, 2016
    expected_recursive_output = np.array([228, 258])

    ## Testing the operation of the recursive function
    def test_recursive_refrig(self):
        ## Test output of recursive function with hardcore value
        recursive_output = baseline_calculator_code_2.recursive(test_data_dict, self.recursive_refrig_input, np.zeros(2))

        ## Verify if outputs are the same
        np.testing.assert_array_equal(recursive_output, self.expected_recursive_output)

class test_data_comparsion_try_else_block(unittest.TestCase):
    ## Test the try block cases
    try_block_input = ['residential','electricity','refrigeration']

    ## Test expected output to try block
    ## Expected output is the output of the recursive function
    ## Output of the recursive function calls the else block
    ## Else block calls the EIA API with try_block_input
    ## Currently, not using try_block_input
    expected_array_try_data = np.array([228, 258])
    expected_array_try_years = np.array(['2015', '2016'])

    ## Expected years array
    #expected_array_years = 

    ## Testing the operation of try block, if successful ,calls else block
    @patch('baseline_calculator_code_2.api_query')
    def test_else_block(self, mock_try_data):
        mock_try_data.return_value = [['2016', 258], ['2015', 228]]

        ## Call EIA API, output arrays are aggregated energy values and years
        output_array_eia_data, output_array_eia_years = baseline_calculator_code_2.data_getter('',self.try_block_input, [''])
        
        ## De-bugging 
        #print(output_array_eia_data)
        
        ## Test if np array output from try/else block equals mock EIA API data
        ## Matches expected array
        mock_try_array = output_array_eia_data['residential']
        np.testing.assert_almost_equal(mock_try_array, self.expected_array_try_data)

        ## Test if years are equal
        np.testing.assert_array_equal(output_array_eia_years, self.expected_array_try_years)

class test_data_comparsion_expect_block(unittest.TestCase):
    ## create an error that triggers the expect block and 
    ## Purposely input only bldg class and end use for input into recursive function
    trigger_else_block_error = ['residential','refrigeration']

    ## Expected output of else block
    expected_list_else_block = ['whatever']

    ## Testing the operation of the else block
    
    ### CURRENT ISSUE: TypeError: test_else_block_error() missing 1 required positional argument: 'patch_else_block'
    ### Despite adding a patch decorator with self, I need to find a way to initialize the variable 'patch_else_block'
    ### 'patch_else_block' is currently an unbound object

    # RESOLUTION: The function had one patch but two arguments, 
    #             patch_else_block and recursive_error. That was the cause of
    #             the TypeError. expected_list_else_block (now renamed) also
    #             needed to be changed to self.expected_list_else_block for
    #             the test to run without errors.

    @patch('baseline_calculator_code_2.data_comparsion')
    def test_else_block_error(self, patch_else_block):  # recursive_error
        patch_else_block.return_value = ['whatever']
        #recursive_error.side_effect = IndexError()

        ## Call data comparison function,
        ## Replace filter_strings with trigger_else_block_error
        output_array_else_block = baseline_calculator_code_2.data_comparsion(test_data_dict, self.trigger_else_block_error, np.zeros(2))
        
        ## Compare output from data comparison function with desired output
        self.assertEqual(output_array_else_block, self.expected_list_else_block)
        
        #with self.assertRaises(AssertionError):
            #print('Filter strings is not a list, assertion error caught')

        #with self.assertRaises(IndexError):


            #print('Filter strings is not long enough, index error caught')

# class test_electric_heating(unittest.TestCase):
#     ## Specify dummy data name list as input to data_getter function
#     ## Similar to filter strings 
#     electr_heat_strings =  ['heating'] 

#     ## Test#1: Refrigeration values ; later can combine both test for refrig and heating into a for loop
#     ## Specify expected output for refigeration data name; should be output to data_getter function
#     expected_electr_heat_years = np.array(['2015', '2016'])
#     ## Past: Data type = List of tuples, int
#     ## Desired format : dict of aggregated energy values as np array
#     expected_electr_heat_array = np.array([228, 258])


if __name__ == '__main__':
    unittest.main()
