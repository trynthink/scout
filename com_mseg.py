#!/usr/bin/env python3

import numpy as np
import re
import csv

# Identify files to import for conversion
serv_dmd = 'KDBOUT.txt'
catg_dmd = 'KDBOUT.txt'
# json_in = 'microsegments.json'
# json_out = 'microsegments_out.json'
# res_tloads = 'Res_TLoads_Final.txt'
# res_climate_convert = 'Res_Cdiv_Czone_ConvertTable_Final.txt'
com_tloads = 'Com_TLoads_Final.txt'
com_climate_convert = 'Com_Cdiv_Czone_ConvertTable_Final.txt'

# Define a series of dicts that will translate imported JSON
# microsegment names to AEO microsegment(s)

# Census division (identical to residential)
cdivdict = {'new england': 1,
            'mid atlantic': 2,
            'east north central': 3,
            'west north central': 4,
            'south atlantic': 5,
            'east south central': 6,
            'west south central': 7,
            'mountain': 8,
            'pacific': 9
            }

# Building type
bldgtypedict = {'assembly': 1,
                'education': 2,
                'food sales': 3,
                'food service': 4,
                'health care': 5,
                'lodging': 6,
                'large office': 7,
                'small office': 8,
                'mercantile/service': 9,
                'warehouse': 10,
                'other': 11,
                'FIGURE THIS ONE OUT': 12
                }

# End use
endusedict = {'heating': 1,
              'cooling': 2,
              'water heating': 3,
              'ventilation': 4,
              'cooking': 5,
              'lighting': 6,
              'refrigeration': 7,
              'PCs': 8,
              'non-PC office equipment': 9,
              'MELs': 10
              }

# Miscellaneous electric load end uses
mels_techdict = {'distribution transformers': 1,
                 'security systems': 2,
                 'elevators': 3,
                 'escalators': 4,
                 'non-road electric vehicles': 5,
                 'coffee brewers': 6,
                 'kitchen ventilation': 7,
                 'laundry': 8,
                 'lab fridges and freezers': 9,
                 'fume hoods': 10,
                 'medical imaging': 11,
                 'video displays': 15,
                 'large video displays': 16,
                 'municipal water services': 17
                 }

# Fuel types
fueldict = {'electricity': 1,
            'natural gas': 2,
            'distillate': 3,
            'liquefied petroleum gas (LPG)': 5,
            'other fuel': (4, 6, 7, 8)
            }
# Other fuel includes residual oil (4), steam from coal (6),
# motor gasoline (7), and kerosene (8)

# Demand components dict
demand_typedict = {'windows conduction': 'WIND_COND',
                   'windows solar': 'WIND_SOL',
                   'wall': 'WALL',
                   'roof': 'ROOF',
                   'ground': 'GRND',
                   'floor': 'FLOOR',
                   'infiltration': 'INFIL',
                   'ventilation': 'VENT',
                   'people gain': 'PEOPLE',
                   'equipment gain': 'EQUIP',
                   'lighting gain': 'LIGHTS',
                   'other heat gain': 'EQUIP_NELEC'
                   }


def json_interpreter(key_series):
    """ Change the list of strings acquired from the JSON database into
    a format that can be used to extract data from the applicable array.

    This function is fairly brittle and assumes that when it is called,
    the input data are already correctly formatted as a list of strings
    in the order [census division, building type, end use, fuel type] """

    # Since the JSON database is formatted with fuel type before end
    # use, switch the order of the end use and fuel type entries in the
    # key_series list
    key_series[2], key_series[3] = key_series[3], key_series[2]

    # Set up list of dict names in the order specified above
    dict_names = [cdivdict, bldgtypedict, endusedict, fueldict]

    # Convert keys from the JSON into a new list using the translation
    # dicts defined at the top of this file
    interpreted_values = []
    for idx, dict_name in enumerate(dict_names):
        interpreted_values.append(dict_name[key_series[idx]])

    # If the end use is heating or cooling, either demand or supply
    # will be specified in the 5th position in the list; if demand is
    # indicated, the demand component should be included in the output
    if 'demand' in key_series:
        # Interpret the demand component specified and append to the list
        interpreted_values.append(demand_typedict[key_series[5]])

    # If the end use is miscellaneous electric loads ('MELs'),
    # key_series will have one additional entry, which should be
    # processed against the dict 'mels_techdict'
    if 'MELs' in key_series:
        # Interpret the MEL type specified and append to the list
        interpreted_values.append(mels_techdict[key_series[4]])

    # interpreted_values is a list in the order r,b,s,f with an
    # additional optional entry for the demand component or MEL type
    return interpreted_values


def sd_mseg_percent(sd_array, sel):
    """ Convert technology type, vintage, and construction status/type
    reported in KSDOUT into percentage energy use each year associated
    with each technology type. Technology type is determined not using
    the technology type numbers but rather using a regex search of the
    'Description' field in the data, since the technology type numbers
    are sometimes used for multiple technologies (this is especially
    true with lighting). This function is run for unique combinations
    of census divisions, building types, end uses, and fuel types. """

    # Assume as input the dict strings converted to numbers in
    # a list called 'sel'

    # Filter service demand data based on the specified census
    # division, building type, end use, and fuel type
    filtered = sd_array[np.all([sd_array['r'] == sel[0],
                                sd_array['b'] == sel[1],
                                sd_array['s'] == sel[2],
                                sd_array['f'] == sel[3]], axis=0)]

    # Identify column names that correspond to years
    # THIS LIST SHOULD PERHAPS BE PASSED THROUGH TO THIS FUNCTION,
    # NOT REDONE ALL THE TIME
    years = [a for a in sd_array.dtype.names if re.search('^2[0-9]{3}$', a)]

    # Replace technology descriptions in the array 'filtered' with
    # generalized names, removing any text describing the vintage or
    # efficiency level
    for idx, row in enumerate(filtered):

        # Identify the technology name using a regex match on the first
        # part of the technology description
        filtered['Description'][idx] = re.search(
            '.+?(?=\s2[0-9]{3})', row['Description']).group(0)
        # The regex is set up to match any text '.+?' that appears
        # before the first occurrence of a space followed by a 2 and
        # three other numbers (i.e., 2009 or 2035)

    # Because different technologies are sometimes coded with the same
    # technology type number (especially in lighting, where lighting
    # types are often differentiated by vintage and technology type
    # numbers), technologies must be identified using the simplified
    # names now recorded in the 'Description' field
    technames = list(np.unique(filtered['Description']))

    # Set up numpy array to store restructured data
    tval = np.zeros((len(technames), len(years)))

    # Combine the data recorded for each unique technology
    for idx, name in enumerate(technames):

        # Extract entries for a given technology type number
        entries = filtered[filtered['Description'] == name]

        # Calculate the sum of all year columns and write it to the
        # appropriate row in the tval array (note that the .view()
        # function converts the structured array into a standard
        # numpy array, which allows the use of the .sum() function)
        tval[idx, ] = np.sum(entries[years].view(('<f8', len(years))), axis=0)

    # Calculate the percentages for each technology type by year
    # (tval is initially a measure of absolute energy use)
    tval = tval/np.sum(tval, axis=0)

    return (tval, technames)


def dtype_eval(entry):
    """ Takes as input an entry from a standard line (row) of a text
    or CSV file and determines its type (only string, float, or
    integer), returning the specified type, which can be added to a
    list to be used in creating a numpy structured array of the data """

    # Strip leading and trailing spaces off of string
    entry = entry.strip()

    if '.' in entry:
        dtype = 'f8'
    elif 'NA'.lower() in entry.lower():
        dtype = 'f8'
    elif re.search('[a-zA-Z]+', entry):  # At least one letter somewhere
        dtype = '<U50'  # Assumed to be no more than 50 characters
    else:
        dtype = 'i4'

    return dtype


def dtype_array(data_file_path, delim_char=','):
    """ Use the csv module to read the first two lines of a text data
    file to determine the column names and data types for each column
    and construct a list of tuples that can be used to define the dtype
    of a numpy structured array """

    # This approach is most useful when there is a header row in the
    # file, the data are not of the same type in every column, and
    # them, as this last bit will cause np.genfromtxt to fail

    # Open the target CSV formatted data file
    with open(data_file_path) as thefile:

        # This use of csv.reader assumes that the default setting of
        # quotechar '"' is appropriate
        filecont = csv.reader(thefile, delimiter=delim_char)

        # Extract header (first) row and remove leading and trailing
        # spaces from all entries
        header_names = [entry.strip() for entry in next(filecont)]

        # Determine dtype using the second line of the file (since the
        # first line is a header row)
        dtypes = [dtype_eval(col) for col in next(filecont)]

        # Combine data types and header names into list of tuples
        comb_dtypes = list(zip(header_names, dtypes))

        return comb_dtypes


def data_import(data_file_path, dtype_list, delim_char=','):
    """ Read the contents of a data file with a header line and convert
    it into a numpy structured array using the provided dtype definition,
    skipping any non-conforming informational lines at the end of the file """

    # This method is most useful when the end of the file has lines
    # that provide background information, since those data can't be
    # inserted into the same array as the main data

    # Open the target CSV formatted data file
    with open(data_file_path) as thefile:

        # This use of csv.reader assumes that the default setting of
        # quotechar '"' is appropriate
        filecont = csv.reader(thefile, delimiter=delim_char)

        # Create list to be populated with tuples of each row of data
        # from the data file
        data = []

        # Skip first line of the file
        next(filecont)

        # Import the data, skipping lines that are not the correct length
        for row in filecont:
            if len(tuple(row)) == len(dtype_list):
                data.append(tuple(row))

        # Convert data into numpy structured array, using the
        # try/catch in the case where the data include the string 'NA',
        # which has to be changed to an 'nan' to be able to be coerced
        # to a float or integer by np.array
        try:
            final_struct = np.array(data, dtype=dtype_list)
        # Targeted error "ValueError: could not convert string to float: 'NA'"
        except ValueError:
            for i, row in enumerate(data):
                row = list(row)  # Make row mutable
                for k, entry in enumerate(row):
                    # Replace 'NA' with 'nan'
                    if entry == 'NA':
                        row[k] = 'nan'
                # Overwrite existing tuple with new tuple
                data[i] = tuple(row)
            # With the 'NA' strings replaced, create the numpy array as
            # originally desired
            final_struct = np.array(data, dtype=dtype_list)

        return final_struct


def str_cleaner(data_array, column_name):
    """ Fix improperly formatted strings with extra leading and/or
    trailing spaces in the specified column of a numpy structured
    array and remove any extraneous double quotes, if present """

    # Check for double quotes in the first entry in the specified column
    # and, assuming all entries in the column are the same, revise all
    # of the entries using the appropriate procedure for the formatting
    if re.search('(?<=\")([^\"]+)', data_array[column_name][0]):
        # Operate on each row in the specified column of the structured array
        for row_idx, entry in enumerate(data_array[column_name]):

            # Delete leading and trailing spaces
            entry = entry.strip()

            # Delete quotes (should now be first and last characters of string)
            entry = entry[1:-1]

            # Delete any newly "apparent" (no longer enclosed by the double
            # quotes) trailing or (unlikely) leading spaces and replace the
            # original entry
            data_array[column_name][row_idx] = entry.strip()

    else:
        # Operate on each row in the specified column of the structured array
        for row_idx, entry in enumerate(data_array[column_name]):

            # Delete any leading and trailing spaces
            data_array[column_name][row_idx] = entry = entry.strip()

    return data_array


def main():
    """ Import input data files and do other things """

    # Import EIA AEO 'KSDOUT' service demand file
    serv_dtypes = dtype_array(serv_dmd)
    serv_data = data_import(serv_dmd, serv_dtypes)
    serv_data = str_cleaner(serv_data, 'Description')

    # Import EIA AEO 'KDBOUT' additional data file
    catg_dtypes = dtype_array(catg_dmd)
    catg_data = data_import(catg_dmd, catg_dtypes)
    catg_data = str_cleaner(catg_data, 'Label')

    # Import thermal loads data
    load_dtypes = cm.dtype_array(com_tloads, '\t')
    load_data = cm.data_import(com_tloads, load_dtypes, '\t')

    # Import census division to climate zone conversion data
    czone_cdiv_conversion = np.genfromtxt(com_climate_convert, names=True,
                                          delimiter='\t', dtype=None)

if __name__ == '__main__':
    main()
