#!/usr/bin/env python3

import numpy as np
import re
import csv

# Identify files to import for conversion
serv_dmd = 'KDBOUT.txt'
catg_dmd = 'KDBOUT.txt'
# json_in = 'microsegments.json'
# json_out = 'microsegments_out.json'
res_tloads = 'Res_TLoads_Final.txt'
res_climate_convert = 'Res_Cdiv_Czone_ConvertTable_Final.txt'
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
endusedict = {'space heating': 1,
              'space cooling': 2,
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


def dtype_eval(entry):
    """ Takes as input an entry from a standard line (row) of a text
    or CSV file and determines its type (only string, float, or
    integer), returning the specified type, which can be added to a
    list to be used in creating a numpy structured array of the data """

    # Strip leading and trailing spaces off of string
    entry = entry.strip()

    if '.' in entry:
        dtype = 'f8'
    elif re.search('[a-zA-Z]+', entry):  # At least one letter somewhere
        dtype = '<U50'  # Assumed to be no more than 50 characters
    else:
        dtype = 'i4'

    return dtype


def dtype_array(data_file_path):
    """ Use the csv module to read the first two lines of a text data
    file to determine the column names and data types for each column
    and construct a list of tuples that can be used to define the dtype
    of a numpy structured array """

    # This approach is most useful when there is a header row in the
    # file, the data are not of the same type in every column, and
    # them, as this last bit will cause np.genfromtxt to fail

    # Open the target CSV formatted data file
    with open(data_file_path) as thefile:

        # This use of csv.reader assumes that the default settings of
        # delimiter ',' and quotechar '"' are appropriate
        filecont = csv.reader(thefile)

        # Extract header (first) row and remove leading and trailing
        # spaces from all entries
        header_names = [entry.strip() for entry in next(filecont)]

        # Determine dtype using the second line of the file (since the
        # first line is a header row)
        dtypes = [dtype_eval(col) for col in next(filecont)]

        # Combine data types and header names into list of tuples
        comb_dtypes = list(zip(header_names, dtypes))

        return comb_dtypes


def data_import(data_file_path, dtype_list):
    """ Read the contents of a data file with a header line and convert
    it into a numpy structured array using the provided dtype definition,
    skipping any non-conforming informational lines at the end of the file """

    # This method is most useful when the end of the file has lines
    # that provide background information, since those data can't be
    # inserted into the same array as the main data

    # Open the target CSV formatted data file
    with open(data_file_path) as thefile:

        # This use of csv.reader assumes that the default settings of
        # delimiter ',' and quotechar '"' are appropriate
        filecont = csv.reader(thefile)

        # Create list to be populated with tuples of each row of data
        # from the data file
        data = []

        # Skip first line of the file
        next(filecont)

        # Import the data, skipping lines that are not the correct length
        for row in filecont:
            if len(tuple(row)) == len(dtype_list):
                data.append(tuple(row))

        # Convert data into numpy structured array
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


if __name__ == '__main__':
    main()
