import os
import sys
import json
import requests
import numpy as np
import numpy.testing as npt
import logging
from scipy import stats
import datetime

class Useful_json_translators(object):
    """Dict translators for building class, end use, and fuel type found on in the EIA data """
    def __init__(self):
        # Dict of building class
        self.bldg_class_translator = {'residential': 'RESD', 'commercial': 'COMM'}

        #Dict of end uses
        self.end_use_translator = {'clothes washing': 'CLW', 'clothes dryers': 'CDR', 'computers': 'CMPR', 'cooking': 'CGR', 'computing': 'OTHEQPPC' ,
        'delivered energy':'DELE', 'dishwashers': 'DSW', 'fans and pumps': 'FPR', 'freezers': 'FRZ', 'lighting': 'LGHTNG', 'office equipment': 'OTHEQPNPC',
        'other uses': 'OTHU','refrigeration': 'REFR', 'cooling': 'SPC', 'heating': 'SPH', 'TVs': 'TVR', 'ventilation': 'VNTC', 'water heating': 'WTHT' }
        
        #Dict of fuel type, electricity is residential
        # purchased electricity is for commercial
        self.fuel_type_translator = {'electricity': 'ELC', 'Purchased Electricity': 'PRC', 'natural gas': 'NG'}

class Set_Up_Real_Data(object):
    """ Test downstream functions by importing real data """
    @classmethod
    def import_real_data(self):
        with open('supporting_data/stock_energy_tech_data/mseg_res_com_cz.json') as f:
            self.data_dict = json.load(f)
            return self.data_dict

## Initialize class
real_data = Set_Up_Real_Data()

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
            

def recur(data_dict, JSON_years_list=[]):
    """Recursively traverse dict and store leaf node keys in list
    """
    for key, item in data_dict.items():
        if isinstance(item, dict):
            recur(item, JSON_years_list)
        else:
            JSON_years_list.append(key)
            #breakpoint()
    return JSON_years_list

## Create a another function to use ordered key_list and create a boolean array for comparsion of EIA years
def extract_EIA_years_for_comparsion(filter_strings):    
    ## Call construct EIA series ID function, if 2 tuples enter, stops here, triggers IndexError
    eia_str_series_ID = construct_EIA_series_ID(filter_strings)

    ## Grab list of EIA years from calling api query function, copy lines from data comparsion function
    eia_data_array, eia_data_years = data_processor(api_query(os.environ['EIA_API_KEY'], eia_str_series_ID))

    ## Grabs current year automatically
    current_time = datetime.datetime.now()

    ## Current comparison year is 2019 or the starting year of the EIA data.. can use this as a validation step or a test
    ## Write a test that the comparsion_year = to first year in the EIA np array
    comparison_year = (current_time.year - 2)
    
    ## De-bugging purposes
    #breakpoint()
    ## Convert JSON_years_np elements from str to int for indexing with boolean array
    EIA_years = eia_data_years.astype(np.int)

    ## Create a boolean array using EIA years list 
    ## Use boolean array to drop unneccessary energy values
    EIA_boolean_array = EIA_years >= comparison_year
    #print(EIA_boolean_array)

    ## Output boolean array with True and False
    return EIA_boolean_array
 

def recursive(data_dict, filter_strings ,energy_vals, position_list=[]):
    """ OPERATION: Recursive function traverses the json structure
    Grabs energy values per year as numpy array
    Test against test data first, then real data""" 

    for key, value in data_dict.items():
        if isinstance(value, dict): 
            #breakpoint() 
            recursive(value, filter_strings, energy_vals, position_list+[key])    
        
        ## At the endpoint/leaf node, use relevant fuel type and end use combination to filter neccessary energy values, aggregate energy value by year
        else:
            
            ## Store different key iterations (climate zone, bldg class, fuel type, end use, year) as a list
            years_as_keys_list = position_list+[key]
            
            ## Convert list into numpy array
            #years_as_keys_array = np.array(years_as_keys_list)
            #years_as_keys_array = np.array(years+[key])

            ## Create a dict for residential and commercial bldg types 
            ## Check format in EIA for proper syntax matching, 
            all_bldg_types = {'residential': ['single family home', 'multi family home', 'mobile homes'], 
            'commercial': ['assembly', 'education', 'food sales','food service', 'health care', 'lodging',
            'small office','large office','mercantile/serice', 'warehouse', 'other']}
    
            ## De-bugging purposes
            breakpoint()
          
            ## Add in additional conditional, to take into account bldg class + end use combinations
            ## If all_bldg_types[filter_strings[0]] is a list of tuple then 
            ## if any all_bldg_types[filter_strings[0]] == years_as_keys_list[1]
            ## Make the new conditional more dynamic 
            #num_bldg_class = len(all_bldg_types[filter_strings[0]])
            if filter_strings[1] == years_as_keys_list[2] and filter_strings[2] == years_as_keys_list[4] and 'energy' in years_as_keys_list:
                ## De-bugging purposes 
                #breakpoint()

                ## Sort by keys in year order and grab values in the order of the years as numpy array
                energy_vals+=np.array([data_dict[key] for key,value in sorted(data_dict.items())]) 

                ## Stores year and energy val as a tuple np array
                energy_years_values_np = np.array(sorted(data_dict.items()))


                ## Convert JSON_years_np elements from str to int for indexing with boolean array
                #JSON_years_np = JSON_years_np.astype(np.int)

                ## De-bugging purposes
                #breakpoint()

                #print(energy_vals)
                
    return energy_vals #(truncated_JSON_energy_vals, truncated_JSON_energy_years)  


def construct_EIA_series_ID(filter_strings):
    ## Initialize json translators
    json_dicts = Useful_json_translators()

    ## this statement will run if outcome is true
    if filter_strings[0] == 'residential':
        condition_1 = json_dicts.end_use_translator[filter_strings[2]]
        condition_2 = 'NA'

    ## Will run when 1st if block is false
    elif filter_strings[0] == 'commercial':
        condition_1 = 'NA'
        condition_2 = json_dicts.end_use_translator[filter_strings[2]]

    ## EIA series ID string
    eia_series_ID = 'AEO.2020.REF2020.CNSM_NA_'+json_dicts.bldg_class_translator[filter_strings[0]]+'_'+condition_1+'_'+json_dicts.fuel_type_translator[filter_strings[1]]+'_'+condition_2+'_USA_QBTU.A'
    ## De-bugging purposes
    #print(eia_series_ID)
    return (eia_series_ID)

## Grab list of traversed JSON years, use the output of the recur function
JSON_years_list = recur(real_data.import_real_data())

def data_comparsion(data_dict,filter_strings, np_array, mismatched_data=[], position_list=[]):
    """OPERATION: Data comparsion function attempts to run recursive function 
    Traverses real data, calls EIA API, with filter strings list comprehension
    If succesful, compares energy values from traversed real data and EIA API
    If unsuccessful, has IndexError, prints message """

    ## If no exception occurs, then except is skipped
    ## If exception occurs, then rest of try block is skipped
    try:
        ## call recursive function, get energy values, change filter string to match the fiter string combo you call from recursive
        ## first arg should be the full json structure, returns json structure, problem is in recursive function
        #  energy_vals, JSON_years_np  = recursive(real_data.import_real_data(), filter_strings, np.zeros(36),np.zeros(36))

        ## Might have to change the truncated preallocated arrays to np.zeros(32) instead np.zeros(36)
        energy_vals = recursive(real_data.import_real_data(), filter_strings, np.zeros(36))
        
        ## Obtain boolean array for EIA years
        EIA_boolean_array = extract_EIA_years_for_comparsion(filter_strings)

        #energy_vals = recursive(data_dict, filter_strings, np.zeros(32))
        #recursive(real_data.import_real_data(), filter_strings, np.zeros(2))
        #years_as_keys_array = np.array(position_list+[key])


        ## Call construct EIA series ID function, if 2 tuples enter, stops here, triggers IndexError
        #eia_str_series_ID = construct_EIA_series_ID(filter_strings)

        ## call EIA API and grab EIA energy values based on years
        #eia_data_array, eia_data_years = data_processor(api_query(os.environ['EIA_API_KEY'], eia_str_series_ID))
        
        ## De-bugging purposes
        breakpoint()


    ## Only runs if try block is unsuccessful
    except IndexError:
        #breakpoint()
        print('Incorrect number of index, check:', filter_strings)
    except AttributeError:
        #breakpoint()
        print('check filter strings list', filter_strings)
    except KeyError:
        #breakpoint()
        print('Data not present in json, EIA API not accessed. Review filter strings:', filter_strings)
    except ValueError as e:
        ## this ValueError is triggered when seriesID (or eia_str_series_ID) doesn't access the EIA API
        ## What should I do with this data?
        ## Plan 1: Store filter_strings combination in a nunpy array ??; No longer doing
        #filter_strings_np = np.array(filter_strings)
        #missing_EIA_data+=np.array(filter_strings)

        ## Plan 2: Look for two error messages: 
        ## (1) Series ID not available from API: AEO.2020.REF2020.CNSM_NA_RESD_OTHEQPPC_ELC_NA_USA_QBTU.A
        ## or should print "Series ID not available from API:" + eia_str_series_ID 
        ## (2) 'Data not present in EIA API', filter_strings, print message
        print('Data not present in EIA API', filter_strings)
        
        #De-bugging
        #breakpoint()
    ## Using bare except to catch all errors
    #except:
        #print('Some other error occurred')y
    
    ## If try block successful, then this runs
    else:
        ##De-bugging   
        breakpoint()

        ## Probably a better way to do this-ask
        ## Re-format boolean array from output of recursive function
        JSON_boolean_array = JSON_boolean_array >539

        ## Truncated JSON energy_vals to use for comparison with EIA API energy vals
        truncated_JSON_energy_vals = energy_vals[JSON_boolean_array]
        
        ## Conversion factors from 2019-2050 to convert EIA site energy to EIA source energy to compare to traversed JSON energy vals
        site_to_source_conversion_vals_array = np.array([
        (2.924462),
        (2.899339), 
        (2.859119),
        (2.823338),
        (2.794036), 
        (2.778606), 
        (2.756023), 
        (2.736274),
        (2.719988), 
        (2.706263), 
        (2.700045), 
        (2.691213),
        (2.679883),
        (2.660015),
        (2.649401),
        (2.636529),
        (2.628546),
        (2.623239),
        (2.614512),
        (2.607262),
        (2.601466),
        (2.594899),
        (2.587528),
        (2.57968),
        (2.572619),
        (2.565959),
        (2.559463),
        (2.553774),
        (2.550256),
        (2.545495),
        (2.541934),
        (2.537156)
        ])

        ## Use site to source conversion values to convert EIA values from site to source energy values
        eia_source_energy_vals_array = (eia_data_array*10E9) * site_to_source_conversion_vals_array

        ## Compare source EIA energy values to source JSON energy values
        compare_soure_energy_arrays = np.array_equal(eia_source_energy_vals_array ,truncated_JSON_energy_vals)


        #### START HERE
        # Start working on why comparison is not equal, look into these reasons:                     
        # - Aggregation might not be working correctly.. aggregation = JSON values = are lower
        # - Not comparing the right thing or what I thinking to get is not work… JSON = look at the filter strings, eia str for recursive and data comaprsion
        # - Data pulled is not correct
        # - Or data is not right

        ## Calculate percent difference between EIA and JSON energy values
        ## In percent_differ equation, New_number= = JSON energy vals and Original_number = = EIA energy value so outcome is positive
        ## Percent difference energy = ((New_number-Original_number)/Original_number) x 100
        #percent_increase_vals = (filtered_JSON_energy_vals-eia_source_energy_vals_array)
       # percent_differ_energy_vals = (percent_increase_vals/eia_source_energy_vals_array)*100

        ## Calcualte percent error between EIA converted source energy values and orginal value
        ## Look at 1% percent error , see what clears this threshold, step down to 0.01%.. find the optiomal percent erorr threshold
        ## (1)Find difference method Look at another difference method , find on that works on large number, set compartive 1% error threshold
        ## (2) See which dont fit the threshold, is there a pattern in filter strings in which ones don't pass threshold? 
        #percent_error_energy_vals = (abs(eia_data_array-eia_source_energy_vals_array)/eia_data_array)* 100
        
        ## Better statistical approach: 
        ## Perform a t-test between EIA and JSON energy values if p>0.05 then reject the null hypothesis and values are significantly difference
        #t_test_energy_vals = stats.ttest_ind(filtered_JSON_energy_vals, eia_source_energy_vals_array)

        # # Might not need both nested if statements below
        ## Might be able to remove the first one since known a prior values won't match due to mix of site and source energy values
        ## Currently need a percent difference of <50 for the np. arrays to be equal
        if (compare_soure_energy_arrays == False) :#and (t_test_energy_vals.pvalue<0.05== True):
            ## De-bugging purposes
            #breakpoint() 

            ## Print converted EIA energy value and traversed and aggregated JSON energy value in the form of np arrays
            print('EIA source converted energy values:', eia_source_energy_vals_array, 'JSON source energy values:',truncated_JSON_energy_vals)
            
            ## Store filter string combination of unequal energy values between EIA and JSON
            unequal_energy_arrays= ['1st']
            
            ## Append filter strings combination to empty list
            unequal_energy_arrays.append(filter_strings+['NEXT'])
            
            ## Output warning messages
            logging.warning('Filter string combinations with unequal EIA and JSON energy values:', unequal_energy_arrays)

            ## De-bugging purposes
            #breakpoint()
            
                ## Re- compare EIA and JSON energy values to see why values arent equal
                ## If the np arrays of EIA and JSON differ by more than 50% (percent difference greater than 50%)
                ## One thought use assert almost equal..if max relative difference less than 35%, then say they are equal
                ## Current max relative difference = 0.3177
                #npt.assert_almost_equal(eia_source_energy_vals_array ,filtered_JSON_energy_vals)

        ## Logic for setting up scenario when data not present in EIA or JSON
        ## These cases are valid and have been vetted for errors
        ## To set up cases when both error messages present
        ## This should remove error messages printing to terminal window
        ## Wait for this to dicuss the command toggle option

        ## Chioke's advice: Command line option- use package = argparse, check out the documentation
        # Look at these code for some examples using run.py and  ecm_prep.py
        # set up at the bottom of code, use in the code
        ## set up verbose option--> all warning messages wont print, set up on verbose instead
        ## objective: give the user an option to print and if they dont want it then they dont print and if they choose to , then the messages will print

        # if Series ID not available from API and Data not present in json, EIA API not accessed. Review filter strings:' present
        # then store filter_string combination
        # invalid_energy_data = []
        # invalid_energy_data+= filter_strings
        # logging.info('Invalid filter_string combination, data does not exist')
        return (eia_data_array, energy_vals)

            
def main():
    ## Import json here
    real_data = Set_Up_Real_Data()

    ## All possible data combinations for bldg class, fuel type and end use
    bldg_class = ['residential', 'commercial']
    fuel_type = ['electricity', 'Purchased Electricity', 'natural gas']
    end_use = ['clothes washing', 'clothes dryers', 'computers', 'cooking', 'computing',
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
                filter_strings = [bldg, fuel, use]
                ## could add some logic here to skip the filter_strings 
                # that have ['residential', 'Purchased Electricity'] and ['commercial','electricity']

                ## Call recursive function
                #recursive(real_data.import_real_data(), filter_strings, np.zeros(32))

                ## Call data comparsion function, attempt on real data
                ## Added in  np.zeros(3) to account for storing the filter string combinations of the missing EIA data
                data_comparsion(real_data.import_real_data(), filter_strings, (np.zeros(36), np.zeros(36)))
                
                ## Call new recursive function
                #recur(real_data.import_real_data())

                ## Call function
                #extract_EIA_years_for_comparsion([],filter_strings)


## Runs on the command line
if __name__ == '__main__':
    main()

    


 
