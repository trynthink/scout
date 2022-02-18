""" Python script for automatically comparing aggregated yearly energy values obtained from EIA API and mseg_res_com_cz.json data file.

This script recursively traverses through the nested structure of mseg_res_com_cz.json data file
and aggregates all energy values for a given year based on building class, fuel type, and end use specification. 
This script uses the EIA API to automatically pull the corresponding data series using the seriesID for the AEO data tables. This seriesID is
constructed based on identifying characteristics such as building class, fuel type, and end use. 

Both energy values, EIA API and JSON, are compared based on whether their corresponding energy values have a percent error of 1% or less. 
"""

import os
import sys
import json
from numpy.core.records import array
import requests
import numpy as np
import numpy.testing as npt
import logging
from scipy import stats
import datetime
from converter import data_processor
import argparse 
import numpy.lib.recfunctions as recfunctions



class Useful_json_translators(object):
    """Dict translators used to match the syntax of building classes, end uses, and fuel types found in the mseg_res_com_cz.json data file to the seriesID abbreviations used in an EIA API query call.  
    
    Attributes:
        bldg_class_translator (dict): Dict structure for types of building classes.   
        end_use_translator (dict): Dict structure for all end uses.
        fuel_type_translator (dict):  Dict structure for fuel types of interest. 
        In the EIA API, residential building classes mainly use electricity whereas and commercial building classes use Purchased Electricity. 
        Both building classes use natural gas as a fuel type.  
        """
    def __init__(self):
        """ Initializes three dict translators (JSON: EIA). """

        # Building class
        self.bldg_class_translator = {'residential': 'RESD', 'commercial': 'COMM'}

        # End Use
        self.end_use_translator = {'clothes washing': 'CLW', 'drying': 'CDR', 'computers': 'CMPR', 'cooking': 'CGR',
        'dishwasher': 'DSW', 'fans and pumps': 'FPR', 'freezers': 'FRZ', 'lighting': 'LGHTNG', 'non-PC office equipment': 'OTHEQPNPC',  'PCs': 'OTHEQPPC',
        'other': 'OTHU', 'refrigeration': 'REFR', 'cooling': 'SPC', 'heating': 'SPH', 'TVs': 'TVR', 'ventilation': 'VNTC', 'water heating': 'WTHT' } # 
        
        # Fuel type
        # Should , 'Purchased Electricity': 'PRC'
        self.fuel_type_translator = {'electricity': 'ELC', 'natural gas': 'NG', 'Purchased Electricity': 'PRC'}

class Set_Up_Real_Data(object):
    """ Import mseg_res_com_cz.json data file for testing downstream functions.
    
    Attributes:
        data_dict (dict): JSON data file as a dict structure.
    """
    @classmethod
    def import_real_data(self):
        """ Initializes function to import JSON data file.
        
        Returns: The mseg_res_com_cz.json data file as a dict structure to be used in other functions as an agrument.
        """
        with open('supporting_data/stock_energy_tech_data/mseg_res_com_cz.json') as f:
            self.data_dict = json.load(f)
            return self.data_dict

class Set_Up_Test_Data(object):
    """ Tests downstream functions by importing test data """
    # Read in test data
    # Reads json file and puts file information into dict form 
    # May decide later to hardcode all the data in instead of importing like below
    @classmethod
    def importing_test_data(self):
        with open('test_json_traverse_v2.json') as f:
            self.data_dict = json.load(f)
            return self.data_dict


def api_query(api_key, series_id, options):
    """Execute an EIA API query and extract the data returned

    Execute a query of the EIA API and extract the data from the
    structure returned by the API.

    Args:
        api_key (str): EIA API key.
        series_id (str): Identifying string for a specific data series.
        options (object): Stores user-specified execution options.

    Returns:
        A nested list of data with inner lists structured as
        [year string, data value].
    """

    query_str = ('http://api.eia.gov/series/?api_key=' + api_key +
                 '&series_id=' + series_id)
    data = requests.get(query_str).json()
    try:
        data = data['series'][0]['data']

    # If an invalid series_id is used, the 'series' key will not be present
    except KeyError:
        if options is not None and options.verbose is True:
            print('\nSeries ID not available from API: ' + series_id)

        ## De-bugging purposes
        #breakpoint()
    return data


def data_getter(api_key, series_names, api_series_list):
    """Get data from EIA API and store in dict using an unique API key and data series.

    Call the required functions to obtain data from EIA using their
    data API, restructure the data into numpy arrays, and store in
    a dict according to the specified series names for later recall.

    Args:
        api_key (str): EIA API key.
        series_names (list): List of strings for the desired keys
            to use for the data in the dict.
        api_series_list (list): List of series strings to indicate
            the desired data from the EIA API call.

    Returns:
        Dict with keys specified in series_names for which the
        values correspond to the numpy arrays of data obtained from
        the EIA API for the series indicated in api_series_list.
    """
    mstr_data_dict = {}

    for idx, series in enumerate(api_series_list):
        try:
            prev_years = years.copy()
        except NameError:
            prev_years = None

        # Obtain data from EIA API; if the data returned is a dict,
        # there was an error with the series_id provided and that
        # output should be ignored entirely; the resulting error
        # from the missing key in the master dict will be handled
        # in the updater function
        raw_data = api_query(api_key, series)
        if isinstance(raw_data, (list,)):
            data, years = data_processor(raw_data)

            # Check against years vector from series pulled immediately
            # prior to determine if years vectors are being consistently
            # returned by the API; if so, or if there is no previous
            # years vector, record the data, otherwise raise a ValueError
            if isinstance(prev_years, np.ndarray):
                if (prev_years == years).all():
                    mstr_data_dict[series_names[idx]] = data
                else:
                    raise ValueError('Years vectors did not match.')
            else:
                mstr_data_dict[series_names[idx]] = data

    return mstr_data_dict, years
        

def recursive(data_dict, filter_strings, energy_vals={}, position_list=[]):
    """ Recursive function traverses the json structure based on building class, fuel type, and end use and aggregates energy values per year as numpy array. 
    
    Args:
        data_dict (dict):  mseg_res_com_cz.json data file as a dict structure.
        filter_strings (list):  A 3-element list representing building class, fuel type, and end use.
        energy_vals (numpy array): A pre-allocated empty array used for the aggregated energy values calculated from the JSON data file. 
        position_list (list): An empty list used to store leaf node keys as the JSON data file is recursively traversed. 
    
    Returns:
        An ordered numpy array containing the aggregated energy values per year found
        in the traversed JSON data file based on a given building class, fuel type, and end use combination. 
    """ 

    for key, value in data_dict.items():
        # Enters this condiitonal and recursively goes through JSON when
        # isinstance(value, dict) == True and (key!= 'energy') == True
        if isinstance(value, dict) and (key!= 'energy'): 
            energy_vals = recursive(value, filter_strings, energy_vals, position_list+[key])
   
        ## At the endpoint/leaf node, use relevant fuel type and end use combination to filter neccessary energy values, aggregate energy value by year
        ## Enters here when isinstance(value, dict) == False and (key!= 'energy') == True
        else:
            # breakpoint()
            # Store different key iterations (climate zone, bldg class, fuel type, end use, year) as a list
            years_as_keys_list = position_list+[key]

            # Dict filter for building class and their corresponding building types
            all_bldg_types = {'residential': ['single family home', 'multi family home', 'mobile home'], 
            'commercial': ['assembly', 'education', 'food sales','food service', 'health care', 'lodging', 'small office','large office','mercantile/service', 'warehouse', 'other']}

            # List of other end use categories in JSON data file, excluding clothes washing, freezers, dishwashers 
            other_end_uses_list = ['rechargeables', 'coffee maker', 'dehumidifier', 'electric other', 'microwave', 'pool heaters and pumps', 'security system', 'portable electric spas', 'wine coolers']

            # List of other end use by name
            excluded_end_uses_by_name_list = ['clothes washing', 'freezers', 'dishwasher']

            # List of residential heating end uses
            heating_resd_end_use_list = ['heating', 'secondary heating']

            # List of residential cooling end uses
            cooling_resd_end_use_list = ['cooling']

            # List of remaining end uses
            remaining_end_uses_list = ['drying', 'computers', 'cooking', 'lighting', 'non-PC office equipment','refrigeration', 'TVs', 'ventilation', 'water heating']
           
            # Filter traversed JSON file by building class (RESD or COMM) and fuel type
            # Enters this conditional statement when isinstance(value, dict) == True and (key!= 'energy')== False)
            if (years_as_keys_list[1] in all_bldg_types[filter_strings[0]]) and (filter_strings[1] == years_as_keys_list[2]) and ('energy' in years_as_keys_list):
                
                # Isolate end-uses in JSON represented by 'true' other category
                # End uses are (i.e. rechargeables, dehumidifier, microwave, etc) and filter_strings = 'other'
                if (years_as_keys_list[3] == 'other') and (years_as_keys_list[4] in other_end_uses_list):
                    # Isolate when end-use = 'true' other
                    if (filter_strings[2]== 'other'):
                        # Aggregate energy value via dict comprehension based on year
                        energy_vals = {k: value.get(k, 0) + energy_vals.get(k, 0) for k in set(value) | set(energy_vals)}

                # Filter by end uses in the 'excluded' other category + aggregate by name 
                # End uses : clothes washing, dishwasher, freezers ; and filter_strings = clothes washes
                elif (years_as_keys_list[3] == 'other') and (years_as_keys_list[4] in excluded_end_uses_by_name_list):
                    # Isolate position in JSON for 'excluded' other end-uses
                    if (filter_strings[2] == years_as_keys_list[4]):
                        # Aggregate energy value via dict comprehension based on year
                        energy_vals = {k: value.get(k, 0) + energy_vals.get(k, 0) for k in set(value) | set(energy_vals)}

                # Isolate position in JSON of heating end-use
                elif (years_as_keys_list[3] in heating_resd_end_use_list):
                    # Filter out residential heating end-use, supply-side
                    if (filter_strings[2] == 'heating') and (years_as_keys_list[4] == 'supply'):
                        # breakpoint()
                        # Aggregate energy value via dict comprehension based on year
                        energy_vals = {k: value.get(k, 0) + energy_vals.get(k, 0) for k in set(value) | set(energy_vals)}
                        # print(value['2025'])

                # Isolate position in JSON of cooling end-use
                elif (years_as_keys_list[3] in cooling_resd_end_use_list):
                    # Filter out residential cooling end-use, supply-side
                    if (filter_strings[2] == years_as_keys_list[3]) and (years_as_keys_list[4] == 'supply'):

                        # Aggregate energy value via dict comprehension based on year
                        energy_vals = {k: value.get(k, 0) + energy_vals.get(k, 0) for k in set(value) | set(energy_vals)}
                        # print(years_as_keys_list)
                #  Filter out remaining end-uses by name
                elif (years_as_keys_list[3] in remaining_end_uses_list):
                    
                    if (filter_strings[2]== years_as_keys_list[3]):
                        # Aggregate energy value via dict comprehension based on year
                        # breakpoint()
                        energy_vals = {k: value.get(k, 0) + energy_vals.get(k, 0) for k in set(value) | set(energy_vals)}
                     
    return energy_vals 


def construct_EIA_series_ID(filter_strings):
    """ Contructs seriesID string based on building class, fuel type, and end use neccessary to execute the EIA API query call for a particular data series.
    
    Args:
        filter_strings (list): A 3-element list representing building class, fuel type, and end use.
    
    Returns:
        An identifying string or seriesID information neccessary to call an EIA API query for a particular data series. 
    """

    # Initialize json translators
    json_dicts = Useful_json_translators()

    # Constructing conditions for residential building class seriesID string
    if filter_strings[0] == 'residential':
        condition_1 = json_dicts.end_use_translator[filter_strings[2]]
        condition_2 = 'NA'
        condition_3 = ['NA', 'HHD']

        # Constructed EIA series ID string
        eia_series_ID = ('AEO.2020.REF2020.CNSM_'+condition_3[0]+'_'+json_dicts.bldg_class_translator[filter_strings[0]]+'_'+
        condition_1+'_'+json_dicts.fuel_type_translator[filter_strings[1]]+'_'+condition_2+'_USA_QBTU.A')

        if filter_strings[2] == 'heating':
            # Constructed EIA series ID string
            
            eia_series_ID = ('AEO.2020.REF2020.CNSM_'+condition_3[1]+'_'+json_dicts.bldg_class_translator[filter_strings[0]]+'_'+
            condition_1+'_'+json_dicts.fuel_type_translator[filter_strings[1]]+'_'+condition_2+'_USA_QBTU.A')

    # Constructing conditions for commercial building class seriesID string
    elif filter_strings[0] == 'commercial':
        condition_1 = 'NA'
        
        if filter_strings[1] == 'electricity':
            # breakpoint()
            # Insert Purchased Electricity for commercial electricity fuel type
            filter_strings[1] = 'Purchased Electricity'

            # if filter_strings[2] == 'non-PC office equipment':
            #     breakpoint()
            #     # Insert Purchased Electricity for commercial electricity fuel type
            #     filter_strings[2] = 'office equipment'

        # Add computing option for commercial computers
        condition_2 = json_dicts.end_use_translator[filter_strings[2]]
        
        # Constructed EIA series ID string
        eia_series_ID = ('AEO.2020.REF2020.CNSM_NA_'+json_dicts.bldg_class_translator[filter_strings[0]]+'_'+condition_1+'_'+
        json_dicts.fuel_type_translator[filter_strings[1]]+'_'+condition_2+'_USA_QBTU.A')
    
    return eia_series_ID

def fuzzy_dict_equal(EIA_dict, JSON_dict, precision): # set precision to 1% for now 
    """
    Compare two dicts recursively (just as standard '==' except floating point
    values are compared within given precision.
    """
 
    all_keys = []

    # Get master list of keys as set for both EIA and JSON
    for key in EIA_dict.keys() and JSON_dict.keys():
        all_keys.append(key)
    # breakpoint()
    
    # Iterate over master list of keys
    for k in sorted(all_keys): 
        # Check that year keys are present in both dicts
        if k in EIA_dict and k in JSON_dict:
            # Fuzzy float comparison
            if isinstance(EIA_dict[k], (float, int, complex)) and isinstance(JSON_dict[k], (float, int, complex)):
                # Calculate percent error between EIA and JSON dict
                dict_percent_error = (abs(EIA_dict[k] - JSON_dict[k])/EIA_dict[k])* 100
                # Compare whether percent error is less than 1%
                if not dict_percent_error < precision:
                    return False, dict_percent_error
            # Recursive compare if there are nested dicts
            elif isinstance(EIA_dict[k], dict):
                # breakpoint()
                if not fuzzy_dict_equal(EIA_dict[k], JSON_dict[k], precision):
                    return False
            # Fall back to default
            elif EIA_dict[k] != JSON_dict[k]:
                return False
    # breakpoint()
    return True, None

def data_comparison(data_dict, filter_strings, options):
    """ Compares aggregagted energy values from two data sources by attemptting to run a recursive function,
     traverse JSON data file, and execute an EIA API query.
    
    If successful, aggregated energy values from traversed JSON data file are compared to EIA API per year basis. 
    using the filter strings combinations for building class, fuel type and end use. 
    If unsuccessful, see print message for more details on error(s).
    
    Args:
        data_dict (dict): mseg_res_com_cz.json data file as a dict structure.
        filter_strings (list): A 3-element identifiying list representing building class,
        fuel type, and end use which determines a particular data series. 
         
    
    Returns:
        Two numpy arrays, one for aggregated EIA API energy values of a particular data series
        and one for JSON energy values aggregated and truncated (based on years demonstrated in EIA API data series). 
    
    """

    try:
        # breakpoint()
        # Call recursive function to obtain aggregated energy values found in the traversed JSON data file 
        JSON_dict = recursive(data_dict, filter_strings) 

        # Call function to construct seriesID neccessary to identify a particular data series in a EIA API query call
        eia_str_series_ID = construct_EIA_series_ID(filter_strings)

        # Move this into its own try/except block
        # Call EIA API, add this to os environment EIA_API_KEY b0b1c9b27ea4e3a25aa3ec0dc9f7addd
        EIA_yrs_energy_vals_list = api_query('b0b1c9b27ea4e3a25aa3ec0dc9f7addd', eia_str_series_ID, options)
        # breakpoint()

        # Convert dict
        EIA_dict = dict(EIA_yrs_energy_vals_list)

        # Convert units of EIA API data series to match units in JSON data file 
        for key in EIA_dict:    
            EIA_dict[key] *=  1E9

    except TypeError:
        #breakpoint()
        if options is not None and options.verbose is True:
            # breakpoint()
            print('Filter strings:', filter_strings, 'SeriesID is:', eia_str_series_ID)


    # Else block runs if all function calls inside try block are successful
    else:
        # Compare floats based on years in EIA
       # breakpoint()
        compare_dict, dict_percent_error = fuzzy_dict_equal(EIA_dict, JSON_dict, 0.01)

        # CHIOKE: Do I need to do [0] or can I leave as it without [0]?
        # if (compare_dict[0] == False):
        if (compare_dict == False):
            
            # If EIA and JSON dicts are not equal, outputs percent error between dicts and corresponding filter string combination
            logging.warning('EIA and JSON dicts are not equal. {percent_error}%, is greater than 1 percent acceptable error for {current} combination.'
            .format(percent_error = round(dict_percent_error, 5), current=filter_strings)) # If {percent_error} = NONE,...
            
            # Print EIA + JSON output started on new lines
            print('DICT FROM EIA API', dict(sorted(EIA_dict.items())))
            print('DICT FROM JSON FILE', dict(sorted(JSON_dict.items())))
        
        return ('Dict from EIA API', dict(sorted(EIA_dict.items())), 'Dict from JSON file', dict(sorted(JSON_dict.items()))) 

# Function to set up parser for command line interface 
def parse_args():
    # Set up parser for command line interface 
    parser = argparse.ArgumentParser()
    # Define how command line arg is parse
    parser.add_argument('--verbose', action='store_true', help='Prints all messages to the CLI')
    # Store all user-specified execution arguments
    options = parser.parse_args()
    return options

def main():
    """ Iteratively constructs filter_strings argument and calls functions on command line. """

    #Initialize class to import in mseg_res_com_cz.json file
    mseg_JSON = Set_Up_Real_Data().import_real_data()
    # test_JSON = Set_Up_Test_Data()
    
    # Set up parser for command line interface 
    options = parse_args()

    # All possible data combinations for building class, fuel type and end use in JSON
    bldg_class = ['residential', 'commercial']
    fuel_type = ['electricity', 'natural gas'] 
    end_use = ['clothes washing', 'cooking', 'cooling', 'computers', 'dishwasher', 'drying', 'fans and pumps', 'freezers', 'lighting', 'non-PC office equipment', 'PCs',
    'other', 'refrigeration', 'heating', 'TVs', 'ventilation', 'water heating'] # 

    # Construct filter strings list used to call functions
    for bldg in bldg_class:
        for fuel in fuel_type:
            for use in end_use:
                # Concatenate filter strings combination
                filter_strings = [bldg, fuel, use]

                # Call comparison function, which also indirectly calls recursive function
                data_comparison(mseg_JSON, filter_strings, options)
    # Testing
    # data_comparison(mseg_JSON, ['commercial', 'electricity', 'PCs'], options) 
    # data_comparison(mseg_JSON, ['residential', 'electricity', 'non-PC office equipment'], options) 

# Runs on the command line
if __name__ == '__main__':
    # Iteratively select filter string combinations and call all functions
    main() 
    
                         
   
    


 
