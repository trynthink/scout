#!/usr/bin/env python3

import numpy as np
import re
import csv
import json
import mseg

# Set the pivot year (i.e., the year that should be added to the data
# reported to convert the values to actual calendar years) for KDBOUT
pivot_year = 1989

# Identify files to import for conversion
serv_dmd = 'KSDOUT.txt'
catg_dmd = 'KDBOUT.txt'
json_in = 'microsegments.json'
json_out = 'microsegments_out.json'
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
                   'equipment gain': 'EQUIP_ELEC',
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

    # Initialize list of rows to remove from 'filtered' based on a
    # regex search of the 'Description' text
    rows_to_remove = []

    # Replace technology descriptions in the array 'filtered' with
    # generalized names, removing any text describing the vintage or
    # efficiency level and preparing to delete placeholder rows
    # (placeholder rows are in the data as imported)
    for idx, row in enumerate(filtered):

        # Identify the technology name from the 'Description' column in
        # the data using a regex set up to match any text '.+?' that
        # appears before the first occurrence of a space followed by a
        # 2 and three other numbers (i.e., 2009 or 2035)
        tech_name = re.search('.+?(?=\s2[0-9]{3})', row['Description'])

        # If the regex matched, overwrite the original description with
        # the matching text, which describes the technology without
        # scenario-specific text like '2003 installed base'
        if tech_name:
            filtered['Description'][idx] = tech_name.group(0)
        # Else check to see if the description indicates a placeholder
        # row, which should be deleted before the technologies are
        # summarized and returned from this function
        elif re.search('placeholder', row['Description']):
            rows_to_remove.append(idx)
        # Implicitly, if the text does not match either regex, it
        # is assumed that it does not need to be edited or removed

    # Delete the placeholder rows from the filtered array
    filtered = np.delete(filtered, rows_to_remove, 0)

    # Because different technologies are sometimes coded with the same
    # technology type number (especially in lighting, where lighting
    # types are often differentiated by vintage and technology type
    # numbers), technologies must be identified using the simplified
    # names now recorded in the 'Description' field
    technames = list(np.unique(filtered['Description']))

    # Set up numpy array to store restructured data, in which each row
    # will correspond to a single technology
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

    # If at least one entry in tval is non-zero (tval.any() == True),
    # suppress any divide by zero warnings and calculate the percentage
    # contribution of each technology by year (since tval is initially
    # a measure of absolute energy use)
    if tval.any():
        with np.errstate(divide='ignore', invalid='ignore'):
            tval = tval/np.sum(tval, axis=0)
            tval = np.nan_to_num(tval)  # Replace nan from 0/0 with 0

    # Note that each row in tval corresponds to a single technology and
    # the rows are in the same order as the technames list
    return (tval, technames)


def catg_data_selector(db_array, sel, section_label):
    """ This function generally extracts a subset of the data available
    in the array that contains data from the commercial building energy
    data file ('catg_dmd'). The subset is based on the type of data,
    indicated in the 'Label' column of the array and specified in the
    variable 'section_label'. The 'sel' variable specifies the desired
    census division, building type, end use, and fuel type. """

    # Filter main EIA commercial data array based on the relevant
    # section label, and then filter further based on the specified
    # division, building type, end use, and fuel type
    filtered = db_array[np.all([db_array['Label'] == section_label,
                                db_array['Division'] == sel[0],
                                db_array['BldgType'] == sel[1],
                                db_array['EndUse'] == sel[2],
                                db_array['Fuel'] == sel[3]], axis=0)]

    # Adjust years reported based on the pivot year
    filtered['Year'] = filtered['Year'] + pivot_year

    # From the filtered data, select only the two needed columns,
    # the year and the data
    desired_cols = filtered[['Year', 'Amount']]

    # Recast the year column as string type instead of integer, since
    # the years will become keys in the dicts output to the JSON, and
    # valid JSON cannot have integers are keys
    desired_cols = desired_cols.astype([('Year', 'U4'), ('Amount', '<f8')])

    return desired_cols


def energy_select(db_array, sd_array, load_array, key_series, sd_end_uses):
    """ At each leaf/terminal node in the microsegments JSON, this
    function is used to convert data from the source arrays into dicts
    to be written to the microsegments database at that location. The
    applicable data is obtained for a given semi-microsegment (i.e.,
    census division, building type, end use, and fuel type) from the
    commercial building energy (and other) data ('db_array') and, if
    applicable, the thermal load factors ('load_array') or technology-
    specific data ('sd_array'). """

    # Convert the list of keys into a list of numeric indices that can
    # be used to select the appropriate data
    index_series = json_interpreter(key_series)

    # Call the appropriate functions depending on the keys associated
    # with a given leaf node in the JSON database; each of the four
    # cases in this if/else structure require slightly different
    # handling due either to differences in the source array or post-
    # data-subset additional manipulation for the data to be in the
    # desired final format
    if 'demand' in key_series:
        # Get the data from KDBOUT
        subset = catg_data_selector(db_array, index_series, 'EndUseConsump')

        # The thermal load data end uses are coded as text strings 'HT'
        # and 'CL' instead of numbers; the numbers in index_series are
        # thus converted to the appropriate strings
        if index_series[2] == 1:
            index_series[2] = 'HT'
        elif index_series[2] == 2:
            index_series[2] = 'CL'
        else:
            raise ValueError(
                'No thermal load data for end use ' + str(index_series[2]))

        # Get the contribution of the particular thermal load component
        # for the current end use (heating or cooling), census division,
        # and building type (note that in the case of these thermal
        # load microsegments, the final field in index_series has the
        # text to select the correct thermal load component column)
        tl_multiplier = load_array[np.all([
            load_array['CDIV'] == index_series[0],
            load_array['BLDG'] == index_series[1],
            load_array['ENDUSE'] == index_series[2]],
                                 axis=0)][index_series[-1]]
        # N.B. tl_multiplier is a 1x1 numpy array

        # Multiply together the thermal load multiplier and energy use
        # data and construct the dict with years as keys
        final_dict = dict(zip(subset['Year'], subset['Amount']*tl_multiplier))
    elif 'MELs' in key_series:
        # Miscellaneous Electric Loads (MELs) energy use data are
        # stored in db_array in a separate section with a different
        # label 'MiscElConsump' and with the MEL technology number
        # coded in the 'EndUse' column. Since the MEL end use number
        # in the 'EndUseConsump' section is 10, but technology specific
        # in the 'MiscElConsump' section, the MEL-specific number is
        # written over the 10 in the 'EndUse' position in index_series
        index_series[2] = index_series[4]

        # Extract the data from KDBOUT
        subset = catg_data_selector(db_array, index_series, 'MiscElConsump')

        # Convert into dict with years as keys and energy as values
        final_dict = dict(zip(subset['Year'], subset['Amount']))
    elif index_series[2] in sd_end_uses:
        # Extract the relevant data from KDBOUT
        subset = catg_data_selector(db_array, index_series, 'EndUseConsump')

        # Get percentage contributions for each equipment type that
        # appears in the service demand data
        [tech_pct, tech_names] = sd_mseg_percent(sd_array, index_series)

        # Declare empty list to store dicts generated for each technology
        tech_dict_list = []

        # For each technology extracted from the service demand data,
        # multiply the corresponding row of data in tech_pct with the
        # total consumption for that end use and fuel type reported in
        # the 'Amount' column in subset, and in the same step, convert
        # the years and calculated technology-specific energy use data
        # into a dict
        for technology in tech_pct:
            tech_dict_list.append(
                dict(zip(subset['Year'], technology*subset['Amount'])))

        # The final dict should be {technology: {year: data, ...}, ...}
        final_dict = dict(zip(tech_names, tech_dict_list))
    else:
        # Regular case with no supply/demand separation or service demand data

        # Extract the desired data from the KDBOUT array
        subset = catg_data_selector(db_array, index_series, 'EndUseConsump')

        # Convert into dict with years as keys and energy as values
        final_dict = dict(zip(subset['Year'], subset['Amount']))

    # Return the dict that should end up at the leaf node in the exported JSON
    return final_dict


def walk(db_array, sd_array, load_array, sd_end_uses, json_db, key_list=[]):
    """ Proceed recursively through the microsegment data structure
    (formatted as a nested dict) to each leaf/terminal node in the
    structure, constructing a list of the applicable keys that define
    the location of the terminal node and then call the appropriate
    functions to process the imported data. """

    # Explore data structure from current level
    for key, item in json_db.items():

        # If there are additional levels in the dict, call the function
        # again to advance another level deeper into the data structure
        if isinstance(item, dict):
            walk(db_array, sd_array, load_array,
                 sd_end_uses, item, key_list + [key])

        # If a leaf node has been reached, check if the second entry in
        # the key list is one of the recognized building types, and if
        # so, finish constructing the key list for the current location
        # and obtain the data to update the dict
        else:
            if key_list[1] in bldgtypedict.keys():
                leaf_node_keys = key_list + [key]

                # Extract data from original data sources
                data_dict = energy_select(db_array, sd_array, load_array,
                                          leaf_node_keys, sd_end_uses)

                # Set dict key to extracted data
                json_db[key] = data_dict

    # Return filled database structure
    return json_db


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


def dtype_array(data_file_path, delim_char=',', hl=None):
    """Use the first two lines (generally) of a file to assess the data type.

    Using the csv module, read the first two lines of a text data file
    or, if specified, the first and third lines after skipping the
    header lines specified by variable 'hl'. These two lines are used
    to determine the column names and data types for each column, and
    are then converted into a list of tuples that can be used to
    specify the dtype parameter of a numpy structured array.

    This function expects that the data file provided has a header
    row, and works only when the data in the first row (after the
    header) is exemplary of the type of data in the entirety of each
    column. Columns with data of varying types will not always be
    handled properly by this function.

    Args:
        data_file_path (str): The full path to the data file to be imported.
        delim_char (str, optional): The delimiting character, defaults to ','.
        hl (int, optional): The number of header lines to skip from the
            top of the file before reading data.

    Returns:
        A numpy structured array dtype definition, which takes the form
        of a list of tuples, where each tuple containing two entries, a
        column heading string, and a string specifying the data type
        for that column.
    """

    # Open the target CSV formatted data file
    with open(data_file_path) as thefile:

        # This use of csv.reader assumes that the default setting of
        # quotechar '"' is appropriate
        filecont = csv.reader(thefile, delimiter=delim_char)

        # Skip the specified number of extraneous leading lines in
        # the file that do not include the column headers
        if hl:
            for i in range(0, hl):
                next(filecont)

        # Extract header (first) row and remove leading and trailing
        # spaces from all entries
        header_names = [entry.strip() for entry in next(filecont)]

        # Skip the blank line between the header and the first row
        # of data in the ktek data file
        if hl:
            next(filecont)

        # Determine dtype using the second line of the file (since the
        # first line is a header row)
        dtypes = [dtype_eval(col) for col in next(filecont)]

        # Combine data types and header names into list of tuples
        comb_dtypes = list(zip(header_names, dtypes))

        return comb_dtypes


def data_import(data_file_path, dtype_list, delim_char=',', hl=None, cols=[]):
    """Import data and convert to a numpy structured array.

    Read the contents of a data file with a header line and convert
    it into a numpy structured array using the provided dtype definition,
    skipping any non-conforming informational lines at the end of the
    file. If specified, skip lines at the beginning of the file, for the
    case where informational content appears there instead. Also support
    capture of only the specified columns from the original data file.

    Args:
        data_file_path (str): The full path to the data file to be imported.
        dtype_list (list): A list of tuples with each tuple containing two
            entries, a column heading string, and a string defining the
            data type for that column. Formatted as a numpy dtype list.
        delim_char (str, optional): The delimiting character, defaults to ','.
        hl (int, optional): The number of header lines to skip from the
            top of the file before reading data.
        cols (list): A list of numbers representing the indices for the
            positions of the columns retained in the dtype definition
            (and thus the columns to include from each row of the data).

    Returns:
        A numpy structured array of the imported data file with the
        columns specified by dtype_list.
    """

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

        # If a number of header lines to skip (variable 'hl') is
        # specified, skip those lines, plus one to accommodate
        # the empty line between the header line and the first
        # row of data in the ktek file (which is the intended
        # target for these lines of code).
        if hl:
            for i in range(0, hl+1):
                next(filecont)

        # Import the data, skipping lines that are not the correct length
        for row in filecont:
            if len(tuple(row)) == len(dtype_list):
                data.append(tuple(row))
            # If there are specific columns of interest specified, select
            # only those columns from the row of data and append the result
            elif cols:
                shorter = [row[i] for i in cols]
                data.append(tuple(shorter))

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
    load_dtypes = dtype_array(com_tloads, '\t')
    load_data = data_import(com_tloads, load_dtypes, '\t')

    # Import census division to climate zone conversion data
    czone_cdiv_conversion = np.genfromtxt(com_climate_convert, names=True,
                                          delimiter='\t', dtype=None)

    # Not all end uses are broken down by equipment type and vintage in
    # KSDOUT; determine which end uses are present so that the service
    # demand data are not explored unnecessarily when they are not even
    # available for a particular end use
    serv_data_end_uses = np.unique(serv_data['s'])

    # Import empty microsegments JSON file and traverse database structure
    with open(json_in, 'r') as jsi:
        msjson = json.load(jsi)

        # Proceed recursively through database structure
        result = walk(catg_data, serv_data, load_data,
                      serv_data_end_uses, msjson)

        # Convert the updated data from census division to climate breakdown
        result = mseg.clim_converter(result, czone_cdiv_conversion)

    # Write the updated dict of data to a new JSON file
    with open(json_out, 'w') as jso:
        json.dump(result, jso, indent=2)

if __name__ == '__main__':
    main()
