import os
import sys
import json
import requests
import numpy as np

class useful_variables(object):
 """ Class of variables used often in this script """
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
    
    #Dict of fuel type, electricity is residential
    # purchased electricity is for commercial
    self.fuel_type_translator = {'electricity': 'ELC', 'Purchased Electricity': 'PRC', 'natural gas': 'NG'}

    #self.eia_data_str = 'AEO.2020.REF2020.CNSM_NA_'+bld_class_translator[filter_strings[0]]+'_'+end_use_translator[filter_strings[2]]+'_'+fuel_type_translator[filter_strings[1]]+'_NA_USA_QBTU.A'

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
    return data

def data_processor(data):
    """Restructure the data obtained from the API into numpy arrays

    Args:
        data (list): A list of data, with each value a list where
            the first value is the year as a string and the second
            value is the number for that year for the data requested.

    Returns:
        Two numpy arrays, one containing the data and one containing
        the years corresponding to those data. Both arrays are sorted
        according to ascending year order.
    """
    years, data = zip(*data)
    years = np.array(years)
    data = np.array(data)[years.argsort()]  # Re-sort in ascending year order
    years = years[years.argsort()]  # Re-sort to be in ascending year order
    return data, years


def data_getter(api_key, series_names, api_series_list):
    """Get data from EIA using their data API and store in dict

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

    
## Recursive function to traverse the json structure and grab energy values per year as numpy array
def recursive(test_data_dict, filter_strings , energy_vals, position_list=[]):
    for key, value in test_data_dict.items():
        if isinstance(value, dict):  
            recursive(value, filter_strings , energy_vals, position_list+[key]) 
            
        else:
        ## At the endpoint/leaf node, use relevant fuel type and end use combination to filter neccessary energy values, aggregate energy value by year
            
            ## Store each year as a list
            years_as_keys_list = (position_list+[key])
            
            ## Convert list into numpy array
            years_as_keys_array = np.array(years_as_keys_list)

            ## Create a dict for residential and commercial bldg types 
            ## Check format in EIA for proper syntax matching, 
            all_bldg_types ={'residential': ['single family home', 'multi family home', 'mobile homes'], 
            'commercial': ['assembly', 'education', 'food sales','food service', 'health care', 'lodging',
            'small office','large office','mercantile/serice', 'warehouse', 'other']}
            
            if filter_strings[1] and filter_strings[2] and all_bldg_types[filter_strings[0]] and 'energy' in years_as_keys_list:
                ## Sort by keys in year order and grab values in the order of the years as numpy array
                energy_vals+=np.array([test_data_dict[key] for key,value in sorted(test_data_dict.items())])
                ## De-bugging purposes
                #print(type(energy_vals))

    return (energy_vals)

# example data_descr_list [ 'residential', 'electricity' , 'clothes washers'], should be the same format as filter_strings
def data_comparsion(real_data_dict,filter_strings, np_array):
    # Use json_data_translator_dict to obtain the same data contained in 'val'
    # for the other climate zones and add it to the values for climate zone 1
    # to get a single list/dict/array of values by year
    try:
        # call recursive function, get energy values, change filter string to match the fiter string combo you call from recursive
        recursive(real_data_dict, filter_strings, np.zeros(2))

        # IF string combo(i.e eia_data_str and json_data_translator) is present in the test_json and EIA
        # for all combos of json_data_translator and test_data; call eia for some str combos 
        #if all(value in test_data_dict for value in json_data_translator_dict.items()) and any(value in test_data_dict for value in json_data_translator_dict[eia_data_str]): 
        #eia_energy_vals+= np.array([json_data_translator_dict[key]] for key in sorted(json_data_translator_dict.items()))

    ## Only runs if try block is unsuccessful
    ## Use expection and print error, but continue until a combo is found
    
    #except AssertionError:
        #print(['First sequence is not a list, check filter_strings'])
        #pass
    except IndexError:
        print(['list index out of range, check filter_strings'])
        pass

    ## If try block successful, then this runs
    else:
        # use json_data_translator_dict to determine the data to call from the EIA API, this is series ID
        eia_data_str = 'AEO.2020.REF2020.CNSM_NA_'+self.bld_class_translator[filter_strings[0]]+'_'+self.end_use_translator[filter_strings[2]]+'_'+self.fuel_type_translator[filter_strings[1]]+'_NA_USA_QBTU.A'

        ## call EIA API and grab EIA energy values based on years
        eia_data_array, eia_data_years = data_getter('96b976d56566570e0292b914bdef21d6', filter_strings, eia_data_str)

        ## sum EIA values, compare to json energy value
        eia_energy_sum = sum(eia_data_array)

        ## Compare EIA and json energy values 
        ## Test if arrays have same shape and same element values
        if np.array_almost_equal(eia_data_array, energy_vals):
        #if np.array_equal(eia_data_array, energy_vals):
            print('True')
        #if eia_energy_sum == energy_vals.any():
            #print('EIA and json data are equal')
        #if eia_energy_sum != energy_vals:
            #print('EIA and json data not equal') 

        return eia_data_array, eia_data_years
        pass

    ## Close EIA API
    finally:
        print("Closing EIA API")
        pass
        

## Runs on the command line
if __name__ == '__main__':
    ## Global variable, can use throughout the file
    # Reads json file and puts file information into dict form i.e. test data
    with open('supporting_data/stock_energy_tech_data/mseg_res_com_cz.json') as f:
        real_data_dict = json.load(f)

    ## Start with residential or commercial, then fuel type then end use
    ## For each combination of 3, call data comparsion function

    ## All possible data combinations for bldg class, fuel type and end use
    bldg_class = ['residential', 'commercial']
    fuel_type = ['electricity', 'Purchased Electricity', 'natural gas']
    end_use = ['clothes washers', 'clothes dryers', 'computers', 'cooking', 'computing',
    'delivered energy', 'dishwashers','fans and pumps', 'freezers', 'lighting', 'office equipment',
    'other uses','refrigeration', 'cooling', 'heating', 'TVs', 'ventilation', 'water heating']

    ## Construct filter strings combination to be used to call functions
    for bldg in bldg_class:
        #print(str(bldg), type(bldg))
        for fuel in fuel_type:
            #print(fuel, type(fuel))
            for use in end_use:
                #print(use)
                ## Concatenate filter strings combination
                ## Pass this filter string list to 
                ## Specify bldg class, fuel type and end use
                filter_strings = [bldg, fuel, use]
                #print(filter_strings, type(filter_strings))
                
                ## Call data comparsion function, try on test data first
                #data_comparsion(test_data_dict, filter_strings, (np.zeros(2), np.zeros(2))) 

                ## Call data comparsion function on real json data
                #data_comparsion(real_data_dict, filter_strings, (np.zeros(2), np.zeros(2))) 


    


 
