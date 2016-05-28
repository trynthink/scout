#!/usr/bin/env python3

import numpy as np
import re
import csv
import json


class UsefulVars(object):
    """Class of variables that would otherwise be global.

    Args:
        pivot_year (int): The pivot year is the value that should be
            added to the year numbers reported in KDBOUT to convert
            the values to actual calendar years.
        serv_dmd (str): Filename for the commercial service demand data.
        catg_dmd (str): Filename for the commercial energy and stock data.
        com_tloads (str): Filename for the commercial thermal load components.
        json_in (str): Filename for input JSON that has only residential data.
        json_out (str): Filename for JSON with commercial building data added.
    """

    def __init__(self):
        self.pivot_year = 1989
        self.serv_dmd = 'KSDOUT.txt'
        self.catg_dmd = 'KDBOUT.txt'
        self.com_tloads = 'Com_TLoads_Final.txt'
        self.json_in = 'mseg_res_cdiv.json'
        self.json_out = 'mseg_res_com_cdiv.json'


class CommercialTranslationDicts(object):
    """Class of dicts that relate the JSON strings with numeric indices.

    For each set defining a microsegment, e.g., census divisions,
    climate zones, building types, the members of that set are recorded
    using human-readable strings in the microsegments JSON files and
    indexed numerically (in general) in the EIA AEO data files. Each
    dict here provides the translation between the string and numeric
    indices for a single set of indices. Demand data are the exception;
    those data use short string indices instead of numbers.

    Args:
        cdivdict (dict): Translation for census divisions.
        bldgtypedict (dict): Translation for commercial building types.
        endusedict (dict): Translation for commercial building end uses.
        mels_techdict (dict): Translation for miscellaneous electric loads.
        fueldict (dict): Translation for fuel types.
        demand_typedict (dict): Translation for components of thermal load.
    """

    def __init__(self):
        self.cdivdict = {'new england': 1,
                         'mid atlantic': 2,
                         'east north central': 3,
                         'west north central': 4,
                         'south atlantic': 5,
                         'east south central': 6,
                         'west south central': 7,
                         'mountain': 8,
                         'pacific': 9
                         }

        self.bldgtypedict = {'assembly': 1,
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

        self.endusedict = {'heating': 1,
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

        self.mels_techdict = {'distribution transformers': 1,
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

        self.fueldict = {'electricity': 1,
                         'natural gas': 2,
                         'distillate': 3,
                         'liquefied petroleum gas (LPG)': 5,
                         'other fuel': (4, 6, 7, 8)
                         }
        # Other fuel includes residual oil (4), steam from coal (6),
        # motor gasoline (7), and kerosene (8)

        self.demand_typedict = {'windows conduction': 'WIND_COND',
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
    """Convert strings in JSON database into codes for data extraction.

    From a list of strings acquired from the JSON database, this
    function converts them into a format that can be used to extract
    data from the applicable array.

    This function is configured with the assumption that the keys are
    provided in the order: census division, building type, fuel type,
    and end use (and optionally MEL type or 'demand' and demand type).
    This function reverses fuel type and end use to be in the order
    used in the EIA data files.

    Args:
        key_series (list): A list of strings assembled by the walk
            function representing the definition of a leaf node in
            the microsegments JSON data structure.

    Returns:
        A list of numbers and (sometimes) strings that are used to
        extract data from the relevant files. There may be up to four
        numeric entries in the first four positions in the list,
        specifying the census division, building type, fuel type,
        and end use, with a fifth position occupied by a string or
        number in the case of demand or MELs data, respectively.
    """

    # Create an instance of the commercial data translation dicts object
    # to be able to use the translation dicts
    cd = CommercialTranslationDicts()

    # Separate handling for key_series for square footage data, where
    # key_series has only three entries, and complete microsegments,
    # which have at least four entries
    if 'total square footage' in key_series or \
       'new square footage' in key_series:
        # Set up a list of dict names for the square footage data,
        # which are only specified on a census division and building
        # type basis
        dict_names = [cd.cdivdict, cd.bldgtypedict]

        # Replicate key_series as keys
        keys = key_series
    else:
        # Create a copy of key_series that can be modified without
        # changing the original contents in key_series
        keys = key_series.copy()

        # Since the JSON database is formatted with fuel type before
        # end use, switch the order of the end use and fuel type
        # entries in the keys list
        keys[2], keys[3] = keys[3], keys[2]

        # Set up list of dict names in the order specified in the
        # function docstring
        dict_names = [cd.cdivdict, cd.bldgtypedict, cd.endusedict, cd.fueldict]

    # Convert keys from the JSON into a new list using the translation
    # dicts defined at the top of this file
    interpreted_values = []
    for idx, dict_name in enumerate(dict_names):
        interpreted_values.append(dict_name[keys[idx]])

    # If the end use is heating or cooling, either demand or supply
    # will be specified in the 5th position in the list; if demand is
    # indicated, the demand component should be included in the output
    if 'demand' in keys:
        # Interpret the demand component specified and append to the list
        interpreted_values.append(cd.demand_typedict[keys[5]])

    # If the end use is miscellaneous electric loads ('MELs'),
    # keys will have one additional entry, which should be
    # processed against the dict 'mels_techdict'
    if 'MELs' in keys:
        # Interpret the MEL type specified and append to the list
        interpreted_values.append(cd.mels_techdict[keys[4]])

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
    """Extracts a specified subset from the commercial building data array.

    This function generally extracts a subset of the data available in
    the commercial building data file. The particular subset is based
    on type of data, indicated in the 'Label' column of the array and
    specified by the variable 'section_label', and the 'sel' variable,
    which specifies the desired census division and building type, and
    if applicable, end use/MEL type, and fuel type.

    Args:
        db_array (numpy.ndarray): An array of commercial building data,
            including total energy use by end use/fuel type and all
            MELs types, new and surviving square footage, and other
            parameters.
        sel (list): A list of integers that specifies the desired
            census division, building type, end use, and fuel type.
        section_label (str): The name of the particular data to be extracted.

    Returns:
        A numpy structured array with columns for only the year and
        magnitude of the data corresponding to 'sel' and 'section_label'.
    """

    # Filter main EIA commercial data array based on the relevant
    # section label, and then filter further based on the specified
    # division, building type, end use, and fuel type - unless the
    # section_label indicates square footage data, which are specified
    # by only census division and building type
    if 'SurvFloorTotal' in section_label or 'CMNewFloorSpace' in section_label:
        filtered = db_array[np.all([db_array['Label'] == section_label,
                                    db_array['Division'] == sel[0],
                                    db_array['BldgType'] == sel[1]], axis=0)]
    else:
        filtered = db_array[np.all([db_array['Label'] == section_label,
                                    db_array['Division'] == sel[0],
                                    db_array['BldgType'] == sel[1],
                                    db_array['EndUse'] == sel[2],
                                    db_array['Fuel'] == sel[3]], axis=0)]

    # Adjust years reported based on the pivot year
    filtered['Year'] = filtered['Year'] + UsefulVars().pivot_year

    # From the filtered data, select only the two needed columns,
    # the year and the data
    desired_cols = filtered[['Year', 'Amount']]

    # Recast the year column as string type instead of integer, since
    # the years will become keys in the dicts output to the JSON, and
    # valid JSON cannot have integers are keys
    desired_cols = desired_cols.astype([('Year', 'U4'), ('Amount', '<f8')])

    return desired_cols


def data_handler(db_array, sd_array, load_array, key_series, sd_end_uses):
    """Restructure data for each terminal node in the microsegments JSON.

    At each leaf/terminal node in the microsegments JSON, this
    function is used to convert data from the source arrays into dicts
    to be written to the microsegments database at the current node.
    The applicable data is obtained for a given semi-microsegment
    (census division and building type for square footage data, and
    end use and fuel type for energy use data) from the commercial
    building energy data and, if applicable, the thermal load
    components and technology-specific performance (i.e., service
    demand) data.

    This function also converts the units of the energy data from
    TBTU (10^12 BTU) to MMBTU (10^6 BTU.)

    Args:
        db_array (numpy.ndarray): An array of commercial building data,
            including total energy use by end use/fuel type and all
            MELs types, new and surviving square footage, and other
            parameters.
        sd_array (numpy.ndarray): Service demand data for commercial
            building equipment, given by technology and performance level.
        load_array (numpy.ndarray): Thermal load components data
            (i.e., energy exchange between buildings and their
            surroundings through walls, foundations, etc.) for
            commercial buildings, specified by census division,
            building type, and heating/cooling season.
        key_series (list): The set of strings that describe the
            current terminal node in the JSON database for which data
            should be generated.
        sd_end_uses (list): The numbers corresponding to the end uses
            that have service demand data.

    Returns:
        A dict with data appropriate for the current location in the
        JSON specified by 'key_series'.
    """

    # Convert the list of keys into a list of numeric indices that can
    # be used to select the appropriate data
    index_series = json_interpreter(key_series)

    # TEMPORARY
    to_mmbtu = 1000000  # 1e6

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
        final_dict = dict(zip(subset['Year'],
                              subset['Amount']*tl_multiplier*to_mmbtu))
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
        final_dict = dict(zip(subset['Year'],
                              subset['Amount']*to_mmbtu))
    elif 'new square footage' in key_series:
        # Extract the relevant data from KDBOUT
        subset = catg_data_selector(db_array, index_series, 'CMNewFloorSpace')

        # Convert into dict with years as keys and new square footage as values
        final_dict = dict(zip(subset['Year'],
                              subset['Amount']))
    elif 'total square footage' in key_series:
        # Extract the relevant data from KDBOUT
        sub1 = catg_data_selector(db_array, index_series, 'CMNewFloorSpace')
        sub2 = catg_data_selector(db_array, index_series, 'SurvFloorTotal')

        # Combine the surviving floor space and new floor space
        # quantities and construct into final dict
        final_dict = dict(zip(sub1['Year'],
                              sub1['Amount'] + sub2['Amount']))
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
                dict(zip(subset['Year'],
                         technology*subset['Amount']*to_mmbtu)))

        # The final dict should be {technology: {year: data, ...}, ...}
        final_dict = dict(zip(tech_names, tech_dict_list))
    else:
        # Regular case with no supply/demand separation or service demand data

        # Extract the desired data from the KDBOUT array
        subset = catg_data_selector(db_array, index_series, 'EndUseConsump')

        # Convert into dict with years as keys and energy as values
        final_dict = dict(zip(subset['Year'],
                              subset['Amount']*to_mmbtu))

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
            if key_list[1] in CommercialTranslationDicts().bldgtypedict.keys():
                leaf_node_keys = key_list + [key]

                # Extract data from original data sources
                data_dict = data_handler(db_array, sd_array, load_array,
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
        # quotechar '"' is appropriate; the skipinitialspace option
        # ensures proper reading of double-quoted text strings in the
        # AEO data that have the delimiter inside them (e.g., cooking
        # equipment descriptions)
        filecont = csv.reader(thefile, delimiter=delim_char,
                              skipinitialspace=True)

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

    # Create a UsefulVars object instance for repeated use in this function
    handyvars = UsefulVars()

    # Import EIA AEO 'KSDOUT' service demand file
    serv_dtypes = dtype_array(handyvars.serv_dmd)
    serv_data = data_import(handyvars.serv_dmd, serv_dtypes)
    serv_data = str_cleaner(serv_data, 'Description')

    # Import EIA AEO 'KDBOUT' additional data file
    catg_dtypes = dtype_array(handyvars.catg_dmd)
    catg_data = data_import(handyvars.catg_dmd, catg_dtypes)
    catg_data = str_cleaner(catg_data, 'Label')

    # Import thermal loads data
    load_dtypes = dtype_array(handyvars.com_tloads, '\t')
    load_data = data_import(handyvars.com_tloads, load_dtypes, '\t')

    # Not all end uses are broken down by equipment type and vintage in
    # KSDOUT; determine which end uses are present so that the service
    # demand data are not explored unnecessarily when they are not even
    # available for a particular end use
    serv_data_end_uses = np.unique(serv_data['s'])

    # Import empty microsegments JSON file and traverse database structure
    try:
        with open(handyvars.json_in, 'r') as jsi, open(
             handyvars.json_out, 'w') as jso:
            msjson = json.load(jsi)

            # Proceed recursively through database structure
            result = walk(catg_data, serv_data, load_data,
                          serv_data_end_uses, msjson)

            # Write the updated dict of data to a new JSON file
            json.dump(result, jso, indent=2)

    except FileNotFoundError:
        errtext = ('Confirm that the expected residential data file ' +
                   handyvars.json_in + ' has already been created and '
                   'is in the current directory.\n')
        print(errtext)

if __name__ == '__main__':
    main()
