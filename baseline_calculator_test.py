#!/usr/bin/env python3

"""Import code to be tested"""
import baseline_calculator_code_2 as code

"""Import packages"""

import json
import unittest

## Mock the EIA API
from nose.tools import assert_true
import requests

## Import standard + third-party libraries
from unittest.mock import patch
from nose.tools import assert_is_not_none

"""Read in the test JSON"""
#with open('test_json_traverse.json', 'r') as f:
    #test_file = json.load(f)

# Define different test with hard coded values ( heating, years, sum of values)
class Test(unittest.TestCase):

    """ Defines valid query options to pull down EIA data API
    Attributes:
    years (list): A list of valid report years for this script to evaluate.

    """
    def __init__(self):
        ## Matches data in json file for Scout, fix format error
        self.json_data_translator_dict = {'residential': ['single family home', 'multi family home', 'mobile homes'],
                                 'electricity': ['heating','secondary heating' ,'cooling' ,'cooking','computers',
                                                 'drying','lighting', 'refrigeration','ceiling fan','fans and pumps',
                                                 'water heating','other', 'all'],
                                 'natural gas': ['heating','secondary heating', 'cooling', 'cooking', 'drying',
                                                 'water heating','other', 'all'],
                                 'distillate': ['heating', 'secondary heating', 'water heating', 'other', 'all'],
                                 'other fuel': ['heating', 'secondary heating','water heating', 'cooking', 'drying',
                                               'other', 'all'],
                                 'commercial': ['assembly', 'education', 'food sales','food service', 'health care',
                                                'lodging','small office','large office','mercantile/serice',
                                                'warehouse', 'other'], 
                                 'electricity': ['heating', 'cooling', 'ventilation', 'water heating','lighting',
                                                'refrigeration', 'cooking','PCs', 'non-PC office equipment', 'MELs','all'],
                                 'natural gas':['heating', 'cooling', 'water heating', 'cooking', 'all'],
                                 'distillate': ['heating', 'water heating', 'all']}

        ## Dict translators for building class, end use, and fuel type found on in the EIA data
        # Dict of building class
        self.bld_class_translator = {'residential': 'RESD', 'commercial': 'COMM'}

        #Dict of end uses
        self.end_use_translator = {'clothes washers': 'CLW', 'clothes dryers': 'CDR', 'computers': 'CMPR', 'cooking': 'CGR', 'computing': 'OTHEQPPC' ,
        'delivered energy':'DELE', 'dishwashers': 'DSW', 'fans and pumps': 'FPR', 'freezers': 'FRZ', 'lighting': 'LGHTNG', 'office equipment': 'OTHEQPNPC',
        'other uses': 'OTHU','refrigeration': 'REFR', 'cooling': 'SPC', 'heating': 'SPH', 'TVs': 'TVR', 'ventilation': 'VNTC', 'water Heating': 'WTHT' }
        
        #Dict of fuel type, purchased electricity is for commercial
        self.fuel_type_translator = {'electricity': 'ELC', 'Purchased Electricity': 'PRC', 'natural gas': 'NG'}





    """ Class of variables present in the test_json_traverse.json for now. 
    Currently, these are variables used globally in functions below.
    In future, these variables will be extended to those required for selection
    in the baseline calculator. """

## Mock EIA API,patch function = patcher ; find source to path, start mock, stop patch 

## Import standard + third-party libraries
from unittest.mock import patch
from nose.tools import assert_is_not_none
import baseline_calculator_code_2 as code

## Reads test data json file and stores as a dict
with open('test_json_traverse.json') as f:
  test_data_dict = json.load(f)

## Using a decorator patch to identify the source of my patch as the output data from EIA API server
#@patch('baseline_calculator_code_2.eia_data_str')
@patch('code.(api_query(96b976d56566570e0292b914bdef21d6, eia_data_str))')
def test_access_EIA_API():
    ## Set up mock patch structure as the test data; should replace the output data of the EIA API server
    mock_patcher = patch(test_data_dict)
    
    #eia_data_str = 'AEO.2020.REF2020.CNSM_NA_'+bld_class_translator[filter_strings[0]]+'_'+end_use_translator[filter_strings[2]]+'_'+fuel_type_translator[filter_strings[1]]+'_NA_USA_QBTU.A'
    #api_key = '96b976d56566570e0292b914bdef21d6'
    #series_id = eia_data_str
    #query_str = ('http://api.eia.gov/series/?api_key=' + api_key +
                 #'&series_id=' + series_id)
    #mock_patcher = patch(data_processor(api_query('96b976d56566570e0292b914bdef21d6', eia_data_str)))
    
    ## Start patching EIA API structure
    mock_start_patch = mock_patcher.start()
    
    ## Configure mock to return response with OK status
    mock_start_patch.return_value.ok = True
    
    ## Configure mock to return json method of results
    mock_start_patch.return_value.json.return_value = test_mock_data_list
    
    ## Call EIA API service, sends request to server; should replace data with test data?
    ## Might need to check to see if it actually is
    eia_data_array, eia_data_years = data_processor(api_query('96b976d56566570e0292b914bdef21d6', eia_data_str))

    ## Stop patching EIA API structure
    mock_patcher.stop()
    
    ## If request is sent successfully, response should be returned
    response = assert_is_not_none(eia_data_array, eia_data_years)
    return response
    

    """Attributes:
    res_bldg_types (list) = Residential building types
    climate_zone (list) = Two of the five AIA climate zones
    end_uses (list) = Two end uses 
    fuel_type = One fuel type used in the test json file
    """

def mock_EIA_API(self):
## Send request to API server; store answer
    eia_response = code.data_processor(api_query('96b976d56566570e0292b914bdef21d6', eia_data_str))

    ## Confirm request-response cycle successfully completed
    assert_true(eia_response.ok)

## Mock EIA API,patch function = patcher ; find source to path, start mock, stop patch 
## Test only patcher style of mocking
import requests
import json
## Import syntax from the EIA API call function, api_query
def test_2_access_EIA_API(api_key, series_id):
    query_str = ('http://api.eia.gov/series/?api_key=' + api_key +
                 '&series_id=' + series_id)
    mock_get_patcher = patch('requests.get(query_str).json()')

    ## Start patching 'request.get' of EIA API
    mock_get = mock_get_patcher.start()

    ## Configure mock with ok status
    mock.get.return_value.ok = True

    ## Call EIA API request to server
    eia_data_array, eia_data_years = data_processor(mock_get_patcher)
    #eia_data_array, eia_data_years = data_processor(api_query('96b976d56566570e0292b914bdef21d6', eia_data_str))

    ## Stop patching 'request.get'
    mock_get_patcher.stop()

    ## Response expected if request is successfu]
    assert_is_not_none(eia_data_array, eia_data_years)

    ## Grab data from EIA API, 
    ## might not be needed, came from api query function
    try:
        data = data['series'][0]['data']
    # If an invalid series_id is used, the 'series' key will not be present
    except KeyError:
        print('\nSeries ID not available from API: ' + series_id)
    return data

    
   


    ## Computes the single family electric heating sum for 2015
    #def test_runner_sfam_heating(self):

        ## Resistance heating values , commented out stock values because not needed
        
        #resist_heat_stock_2015 = 1
        #resist_heat_energy_2015 = 2
        #ASHP values 
        #ASHP_stock_2015 = 1
        #ASHP_energy_2015 = 5
        #GSHP values 
        #GSHP_stock_2015 = 1
        #GSHP_energy_2015 = 3

        ## Calculate sum of electric heating for 2015 
        #electric_sum_output = code.sum_electric_heating(resist_heat_energy_2015, ASHP_energy_2015, GSHP_energy_2015)
        #expected_electric_sum_output = 10

        # Test if expected and actual outputs match
        #self.assertEqual(electric_sum_output, expected_electric_sum_output)

    #def test_runner_mfam_refrig(self):
        """Values from AIA_CZ2 and mutli family home, comment out stock values because not needed"""
        
        #refrig_stock_2015 = 1
        #refrig_CZ1_energy_2015 = 7
        #refrig_CZ2_energy_2015 = 4

       # refrig_stock_2016 = 1
        #efrig_CZ1_energy_2016 = 7
        #refrig_CZ2_energy_2016 = 7

        ## Calculate sum of electric refrigeration for 2016
        #refrig_sum_output = code.sum_refrig(refrig_CZ1_energy_2016,refrig_CZ2_energy_2016)
        #expected_refrig_sum_output = 14

        ## Test if expected and actual ouputs match
        #self.assertEqual(refrig_sum_output, expected_refrig_sum_output)

    #def test_runner_aggregate_refrig(self):
        """Aggregate refrigeration energy values for 2015 for all building types"""
        #refrig_CZ1_sfam_energy_2015 = 3
        #refrig_CZ1_mfam_energy_2015 = 7
        #refrig_CZ2_sfam_energy_2015 = 5
        #refrig_CZ2_mfam_energy_2015 = 4
        #refrig_CZ2_mobile_energy_2015 = 9

        
        ## Values from function in code.py
        #refrig_sum_aggre_output = code.aggregate_refrig(refrig_CZ1_sfam_energy_2015, refrig_CZ1_mfam_energy_2015
        #,refrig_CZ1_mobile_energy_2015,refrig_CZ2_sfam_energy_2015 ,refrig_CZ2_mfam_energy_2015, refrig_CZ2_mobile_energy_2015)
        #Expected sum of 2015 refrigeration energy values
        #expected_refrig_aggre_sum = 34

        #Test if expected and actual ouputs match
        #self.assertEqual(refrig_sum_aggre_output,expected_refrig_aggre_sum)

   # def test_runner_aggregate_heat(self):
        """ Aggregate electric heating energy values for 2016 for all heating technology types"""
        #Values from CZ1, single family
        #resist_energy_1 = 3
       #GSHP_energy_1 = 9

        #Values from CZ2, single family
        #ASHP_energy_2 = 2
       # GSHP_energy_2 = 9

        #Values from CZ1, multi family
        #resist_energy_3 = 7
       # ASHP_energy_3 = 8
       # GSHP_energy_3 = 4

        #Values from CZ2, multi family
       # resist_energy_4 = 7
       # ASHP_energy_4 = 8
       #GSHP_energy_4 = 4

        #Values from CZ1, mobile home
       # ASHP_energy_5 = 6
        #GSHP_energy_5 = 4

        #Values from CZ2, mobile home
        #esist_energy_6 = 3
        #ASHP_energy_6 = 6
        #GSHP_energy_6 = 4

        #Sum all values for each electric heating technology
       # resist_energy = (resist_energy_1 + resist_energy_2 + resist_energy_3 + resist_energy_4 + resist_energy_5 + resist_energy_6)
        #ASHP_energy = (ASHP_energy_1 + ASHP_energy_2 + ASHP_energy_3 + ASHP_energy_4 + ASHP_energy_5 + ASHP_energy_6)
        #GSHP_energy = (GSHP_energy_1 + GSHP_energy_2 + GSHP_energy_3 + GSHP_energy_4 + GSHP_energy_5 + GSHP_energy_6)

        #Aggregate values
       # heat_sum_aggre_output = code.aggregate_heating(resist_energy, ASHP_energy, GSHP_energy)
        #Expected sum of 2015 refrigeration energy values
        #expected_heat_aggre_sum = 92

        #Test if expected and actual ouputs match
        #self.assertEqual(heat_sum_aggre_output,expected_heat_aggre_sum)

    # Will need a test to ensure the stock data is present or not as a verification step

    # Write test to check EIA data read in properly 







#Runs on the command line
if __name__ == '__main__':
    unittest.main()
