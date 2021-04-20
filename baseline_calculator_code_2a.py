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
import requests
import numpy as np
import numpy.testing as npt
import logging
from scipy import stats
import datetime
from converter import data_processor
from argparse import ArgumentParser



class Useful_json_translators(object):
    """Dict translators used to match the syntax of building classes, end uses, and fuel types found on in the mseg_res_com_cz.json data file to the seriesID abbreviations used in an EIA API query call.  
    
    Attributes:
        bldg_class_translator (dict): Dict structure for building classes.   
        end_use_translator (dict): Dict structure for all end uses.
        fuel_type_translator (dict):  Dict structure for fuel types of interest. 
        In the EIA API, residential building classes mainly use electricity whereas and commercial building classes use Purchased Electricity. 
        Both building classes use natural gas as a fuel type.  
        """
    def __init__(self):
        """ Initializes three dict translators. """

        # Building class
        self.bldg_class_translator = {'residential': 'RESD', 'commercial': 'COMM'}

        # End Use
        self.end_use_translator = {'clothes washing': 'CLW', 'clothes dryers': 'CDR', 'computers': 'CMPR', 'cooking': 'CGR',
        'delivered energy':'DELE', 'dishwasher': 'DSW', 'fans and pumps': 'FPR', 'freezers': 'FRZ', 'lighting': 'LGHTNG', 'non-PC office equipment': 'OTHEQPNPC',
        'other uses': 'OTHU','refrigeration': 'REFR', 'cooling': 'SPC', 'heating': 'SPH', 'TVs': 'TVR', 'ventilation': 'VNTC', 'water heating': 'WTHT' }
        
        # Fuel type
        self.fuel_type_translator = {'electricity': 'ELC', 'Purchased Electricity': 'PRC', 'natural gas': 'NG'}

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
        with open('test_json_traverse.json') as f:
            self.data_dict = json.load(f)
            return self.data_dict


def api_query(api_key, series_id):
    """Execute an EIA API query and extract the data returned

    Execute a query of the EIA API and extract the data from the
    structure returned by the API.

    Args:
        api_key (str): EIA API key.
        series_id (str): Identifying string for a specific data series.

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
            

def recur(data_dict, JSON_years_list=[]):
    """Recursively traverses a JSON data file and stores the last leaf node keys in a list.

    Args: 
        data_dict (dict): Data structure from mseg_res_com_cz.json data file.
        JSON_years_list (list): Preallocated empty list used to save the last leaf node key
        after each iteration. The key represents the all years found in the mseg_res_com_cz.json data file. 

    Returns:
        A list corresponding to all years found each time the mseg_res_com_cz.json data file was traversed. 
        Repetitive set of years will be saved that matches the number of recursive iterations. 
    """

    for key, item in data_dict.items():
        if isinstance(item, dict):
            recur(item, JSON_years_list)
        else:
            ## Might need to clean this up and only have it set where if key!=stock append
            if (key!= 'stock'):
                JSON_years_list.append(key) 
    return JSON_years_list


def extract_EIA_years_for_comparison(data_dict, filter_strings):
    """ Uses an ordered list of available years found in the JSON data file to create a boolean array of years demonstrated in EIA API data. 
    
    Args:
        filter_strings (list): A 3-element list representing building class, fuel type, and end use. 
        This list constructs the identifying string(seriesID) needed to execute the EIA API query call.
    
    Returns:
        A boolean array to determine which years are present in both the JSON data file and EIA API query call.
    
        """

    try:
             
        # Call function to construct seriesID for EIA API query call
        #breakpoint()
        eia_str_series_ID = construct_EIA_series_ID(filter_strings)
       
        # Execute EIA API query call and obtain energy values with their associated years 
        eia_data_array, eia_data_years = data_processor(api_query(os.environ['EIA_API_KEY'], eia_str_series_ID))

        # Ordered list of all unique years found in JSON data file
        JSON_years_ordered = sorted(list(set(recur(data_dict))))
        # De-bugging purposes
        #breakpoint()

    except IndexError:
        print('Incorrect element length inside', filter_strings )
    except ValueError:
        print('API query function fails, data not present in EIA API for:', filter_strings)
    else:
        #breakpoint()
        ## Need to figure out how to connect JSON_years_ordered variable 
        # Convert JSON_years_ordered from list to numpy array
        JSON_years_np = np.array(JSON_years_ordered)

        # Convert JSON and EIA year elements from str to int for indexing with boolean array
        # EIA API years
        EIA_years_np = eia_data_years.astype(np.int)

        # Years from JSON data file
        JSON_years_np_int = JSON_years_np.astype(np.int)

        # Use first year in EIA API as comparison year
        EIA_1st_year = EIA_years_np[0]
        
        # Boolean array to use as data comparison metric 
        EIA_boolean_array = JSON_years_np_int >= EIA_1st_year

        return EIA_boolean_array


def recursive(data_dict, filter_strings, energy_vals, position_list=[]):
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
        
        ## Enters this condiitonal and recursively goes through JSON when
        ## isinstance(value, dict) == True and (key!= 'energy') == True
        if isinstance(value, dict) and (key!= 'energy'): 
            #breakpoint() 
            recursive(value, filter_strings, energy_vals, position_list+[key])
              
        
        ## At the endpoint/leaf node, use relevant fuel type and end use combination to filter neccessary energy values, aggregate energy value by year
        ## Enters here when isinstance(value, dict) == False and (key!= 'energy') == True
        else:
            ## Store different key iterations (climate zone, bldg class, fuel type, end use, year) as a list
            years_as_keys_list = position_list+[key]
            #breakpoint()

            # Need to add bldg class filter that matches filter_strings[0]
            all_bldg_types = {'residential': ['single family home', 'multi family home', 'mobile homes'], 
            'commercial': ['assembly', 'education', 'food sales','food service', 'health care', 'lodging', 'small office','large office','mercantile/serice', 'warehouse', 'other']}

            ## Enters this conditional statement when isinstance(value, dict) == True and (key!= 'energy')== False)
            if (filter_strings[1] == years_as_keys_list[2] and 'energy' in years_as_keys_list) and (filter_strings[2] == years_as_keys_list[3] or filter_strings[2] == years_as_keys_list[4]):
                ## De-bugging purposes 
                breakpoint()

                ## Sort by keys in year order and grab values in the order of the years as numpy array
                #energy_vals+=np.array([data_dict[key] for key, value in sorted(data_dict.items())])
                energy_vals+=np.array([energy_yr_vals[1] for energy_yr_vals in sorted(value.items())])
                #breakpoint()
                #print(energy_vals)

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
        condition_2 = json_dicts.end_use_translator[filter_strings[2]]
        
        # Constructed EIA series ID string
        eia_series_ID = ('AEO.2020.REF2020.CNSM_NA_'+json_dicts.bldg_class_translator[filter_strings[0]]+'_'+condition_1+'_'+
        json_dicts.fuel_type_translator[filter_strings[1]]+'_'+condition_2+'_USA_QBTU.A')

    return eia_series_ID


# Determine which exceptions are most valid, 
# turn off except handling and phase one in at a time to see what is causing each error
# then meet with Chioke
def data_comparison(data_dict, filter_strings):
    """ Compares aggregagted energy values from two data sources by attemptting to run a recursive function, traverse JSON data file, and execute an EIA API query.
    
    If successful, aggregated energy values from traversed JSON data file are compared to EIA API per year basis. 
    using the filter strings combinations for building class, fuel type and end use. 
    If unsuccessful, see print message for more details on error(s).
    
    Args:
        data_dict (dict): mseg_res_com_cz.json data file as a dict structure.
        filter_strings (list): A 3-element identifiying list representing building class, fuel type, and end use which determines a particular data series. 
         
    
    Returns:
        Two numpy arrays, one for aggregated EIA API energy values of a particular data series
        and one for JSON energy values aggregated and truncated (based on years demonstrated in EIA API data series). 
    
    """

    try:
        # Testing ValueError
        breakpoint()

        # Call recur function to get list of all years found in JSON data file 
        JSON_years_as_list = recur(data_dict)

        # Ordered list of all unique years found in JSON data file
        JSON_years_ordered = sorted(list(set(JSON_years_as_list)))

        # Get length of JSON years and use as preallocated np array length to call recursiv function
        # Call recursive function to obtain aggregated energy values found in the traversed JSON data file 
        energy_vals = recursive(data_dict, filter_strings, (np.zeros(len(JSON_years_ordered))))

        # Call function to obtain boolean array used to compare years found in JSON to available years in EIA API data series
        EIA_boolean_array = extract_EIA_years_for_comparison(data_dict, filter_strings)

        #breakpoint()
        # Call function to construct seriesID neccessary to identify a particular data series in a EIA API query call
        eia_str_series_ID = construct_EIA_series_ID(filter_strings)

        ## call EIA API and grab EIA energy values based on years
        eia_data_array, eia_data_years = data_processor(api_query(os.environ['EIA_API_KEY'], eia_str_series_ID))
        
        ## De-bugging purposes
        #breakpoint()

    # Exceptions triggered if any function call inside the try block is unsuccessful
    except IndexError:
        #breakpoint()
        print('Incorrect number of index, check:', filter_strings)
    #except AttributeError:
        #breakpoint()
        #print('check filter strings list', filter_strings)
    #except KeyError:
        #breakpoint()
        #print('Data not present in json, EIA API not accessed. Review filter strings:', filter_strings)
    except ValueError:
        #breakpoint
        print('Operand and broadcast issue', filter_strings)

    # Else block runs if all function calls inside try block are successful
    else:
        ##De-bugging   
        #breakpoint()

        # Truncate energy values located in JSON where the years is not present in an EIA API data series
        truncated_JSON_energy_vals = energy_vals[EIA_boolean_array]
        
        # Convert units of EIA API data series to match units in JSON data file
        eia_energy_vals_array = (eia_data_array*1E9)

        # Compare EIA API and JSON aggregated energy values 
        compare_energy_arrays = np.allclose(eia_energy_vals_array, truncated_JSON_energy_vals)
        
        # Calculate percent error between EIA API and JSON energy numpy arrays, acceptable error threshold is 1%
        percent_error_energy_vals = (abs(eia_energy_vals_array-truncated_JSON_energy_vals)/eia_energy_vals_array)* 100

        if (compare_energy_arrays == False) and (((percent_error_energy_vals<=0.01).any())== False):
            #breakpoint()             
            
            # Print both numpy arrays for EIA API and JSON energy values
            print('EIA energy values:', eia_energy_vals_array, 'JSON energy values:', truncated_JSON_energy_vals)

            # Store filter string combinations where EIA API data series and JSON traversed energy values are unequal 
            unequal_energy_arrays= []
            
            # Append filter strings combination to empty list
            unequal_energy_arrays.append(filter_strings+['NEXT'])
            
            # Output warning messages
            #logging.warning('Filter string combinations with unequal EIA and JSON energy values:', unequal_energy_arrays)

        return eia_energy_vals_array, truncated_JSON_energy_vals

            
def main():
    """ Iteratively constructs filter_strings argument and calls functions on command line. """

    #Initialize class to read in
    mseg_JSON = Set_Up_Real_Data()
    test_JSON = Set_Up_Test_Data()
    
    # All possible data combinations for building class, fuel type and end use
    bldg_class = ['residential', 'commercial']
    fuel_type = ['electricity', 'Purchased Electricity', 'natural gas']
    end_use = ['clothes washing', 'clothes dryers', 'computers', 'cooking',
    'delivered energy', 'dishwasher', 'fans and pumps', 'freezers', 'lighting', 'non-PC office equipment',
    'other uses', 'refrigeration', 'cooling', 'heating', 'TVs', 'ventilation', 'water heating']

    # Construct filter strings list used to call functions
    for bldg in bldg_class:
        for fuel in fuel_type:
            for use in end_use:
                # Concatenate filter strings combination
                filter_strings = [bldg, fuel, use]

                # Call comparison function, which also indirectly calls recursive function
                #data_comparison(mseg_JSON.import_real_data(), filter_strings)
                
                # Testing ValueError for discussion
                data_comparison(mseg_JSON.import_real_data(), filter_strings=['residential', 'electricity', 'cooking'])  
                #recursive(mseg_JSON.import_real_data(), ['residential', 'electricity', 'cooking'], np.zeros(36))


# Runs on the command line
if __name__ == '__main__':
    main()

    # Handle option user-specified execution arguments
    parser = ArgumentParser()
    parser.add_argument("--verbose", action="store_true", dest="verbose",
                        help="print all warnings to stdout")

    # Handle cases when no seriesID avalilable for given filter strings combination
    parser.add_argument("Series ID not available from API" + series_id,  action="store_true", dest="weird_series_ID_combo",
                    help="SeriesID combination could not access EIA API")
    
    #Handle cases where weird filter string combinations are generated and used to call EIA API query 
    parser.add_argument("API query function fails, data not present in EIA API for", filter_strings,  action="store_true", dest="weird_bldg_fuel_end_use_combo",
                    help="Failed EIA API query call")   
                         
    options = parser.parse_args(['--verbose', 'Series ID not available from API', 'API query function fails, data not present in EIA API for'])
    


 
