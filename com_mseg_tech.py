#!/usr/bin/env python3

# Import commercial microsegments code to use some of its data
# reading and processing functions
import com_mseg as cm
import mseg

import numpy as np
import re
import warnings
import json


class UsefulVars(object):
    """Set up class to contain what would otherwise be global variables.

    Attributes:
        cpl_data (str): File name for the EIA AEO technology data.
        json_in (str): File name for the input JSON database.
        com_climate_convert_rev (str): File name for the input census
            division to climate zone conversion factors for the cost,
            performance, and lifetime data.
        cpl_data_skip_lines (int): The number of lines of preamble that
            must be skipped at the beginning of the EIA AEO technology
            data file.
        columns_to_keep (list): A list of strings defining the columns
            from the EIA AEO technology data file that are required.
    """

    def __init__(self):
        # Identify files to import for processing and conversion
        self.cpl_data = 'ktek.csv'
        self.json_in = 'microsegments.json'
        self.com_climate_convert_rev = ('Com_Cdiv_Czone_ConvertTable'
                                        '_Rev_Final.txt')

        # Define the number of header lines in the ktek data file to
        # skip and the names of the columns to keep from the ktek data
        self.cpl_data_skip_lines = 100
        self.columns_to_keep = ['t', 'v', 'r', 's', 'f', 'eff', 'c1', 'c2',
                                'Life', 'y1', 'y2', 'technology name']


def units_id(sel, flag):
    """Provides a units text string for a specified microsegment.

    Depending on the end use number given in the sel list, which
    specifies the entire microsegment, this function returns the
    string that best describes the units for that end use. Using
    this function ensures that the units are consistent throughout
    the output data. The unit definitions are based on the preamble
    text in the EIA AEO commercial buildings technology data file.

    Args:
        sel (list): A list of four integers that, together, define a
            microsegment, and correspond to the climate zone, building
            type, end use, and fuel type, in that order.
        flag (str): Indicates the type of units to be returned, either
            'cost' or 'performance'.

    Returns:
        A text string of the appropriate units for the input arguments
        to the function.
    """

    # For readability, assign the end use number to a clearly named variable
    enduse = sel[2]

    # Determine units depending on whether this function was called
    # for cost or performance units
    if flag == 'cost':
        if enduse == 4:  # ventilation
            theunits = '2013$/1000 cfm'
        elif enduse == 6:  # lighting
            theunits = '2013$/1000 lm'
        else:
            theunits = '2013$/kBTU out/hr'
    elif flag == 'performance':
        if enduse == 4:  # ventilation
            theunits = 'cfm-hr/BTU in'
        elif enduse == 6:  # lighting
            theunits = 'lm/W'
        else:
            theunits = 'BTU out/BTU in'

    return theunits


def tech_data_selector(tech_data, sel):
    """ From the full structured array of cost, performance, and
    lifetime data from the AEO, extract a group of data using numeric
    indices generated from the text indices at the leaf nodes of the
    input microsegments JSON. Each group of data extracted by this
    function will correspond to multiple technologies and performance
    levels and will require further processing. """

    # Determine whether the data indicated in the 'r' column indicates
    # building type or census division based on the end use indicated
    # (building type for ventilation, lighting, and refrigeration)
    if sel[2] in [4, 6, 7]:
        tmp = sel[1]  # use building type
    else:
        tmp = sel[0]  # use census division

    # Filter technology data based on the specified census
    # division or building type, end use, and fuel type
    filtered = tech_data[np.all([tech_data['r'] == tmp,
                                 tech_data['s'] == sel[2],
                                 tech_data['f'] == sel[3]], axis=0)]

    return filtered


def sd_data_selector(sd_data, sel, years):
    """ From the full structured array of service demand data from the
    AEO, extract just the service demand data corresponding to the
    census division, building type, end use, and fuel type specified by
    each leaf node in the input microsegments JSON. Each group of data
    are converted into two outputs, 1) a numpy array of service demand
    summed across the three specified markets (column named 'd'), with
    rows for each technology and performance level combination and
    columns for each year, and 2) a list of technology names for
    each row of the service demand numpy array (the other output). """

    # Filter service demand data based on the specified census
    # division, building type, end use, and fuel type
    filtered = sd_data[np.all([sd_data['r'] == sel[0],
                               sd_data['b'] == sel[1],
                               sd_data['s'] == sel[2],
                               sd_data['f'] == sel[3]], axis=0)]

    # Identify each technology and performance level using the text
    # in the description field since the technology type and vintage
    # numeric codes are not well-matched to individual technology and
    # performance levels
    technames = list(np.unique(filtered['Description']))

    # Set up numpy array to store restructured data, in which each row
    # will correspond to a single technology
    sd = np.zeros((len(technames), len(years)))

    # Combine the service demand for the three markets ['d'] in the data
    for idx, name in enumerate(technames):

        # Extract entries for a given technology name
        entries = filtered[filtered['Description'] == name]

        # Calculate the sum of all year columns and write it to the
        # appropriate row in the sd array (note that the .view()
        # function converts the structured array into a standard
        # numpy array, which allows the use of the .sum() function)
        sd[idx, ] = np.sum(
            entries[list(map(str, years))].view(('<f8', len(years))), axis=0)

    # Note that each row in sd corresponds to a single performance
    # level for a single technology and the rows are in the same order
    # as the technames list
    return sd, technames


def single_tech_selector(tech_array, specific_name):
    """Extracts a single technology from tech data for an entire microsegment.

    Each microsegment is comprised of multiple technologies. Cost,
    performance, and lifetime data are needed for each technology in a
    microsegment. This function separates out those data for a specific
    technology from all of the technologies in the microsegment so that
    they can be processed and further restructured for later output.

    Args:
        tech_array (numpy.ndarray): EIA technology characteristics
            data available for a single microsegment, including cost,
            performance, and lifetime data for (typically multiple)
            performance scenarios for each technology applicable to
            that microsegment.
        specific_name (type): The name of the technology to be extracted.

    Returns:
        A numpy structured array with the same columns as other tech
        data, but with only the rows corresponding to the technology
        indicated by specific_name.
    """

    # Initialize a list of rows to remove from the numpy array
    # that do not correspond to the specified technology
    rows_to_remove = []

    for idx, row in enumerate(tech_array):
        # Identify the technology name from the 'technology name' column
        # in the data using a regex set up to match any text '.+?' that
        # appears before the first occurrence of a space followed by a
        # 2 and three other numbers (i.e., 2009 or 2035)
        tech_name = re.search('.+?(?=\s2[0-9]{3})', row['technology name'])

        # If the regex returned a match, and the first group of the
        # match (i.e., the part before the numeric year) is not the
        # the same as the name passed to the function, remove the row
        if tech_name:
            if tech_name.group(0) != specific_name:
                rows_to_remove.append(idx)
        # If there's no match, the technology might not have a year
        # included as part of its name, but it nonetheless should be
        # checked to see if it matches the name passed to the function
        # and removed if there is not a match
        elif row['technology name'] != specific_name:
            rows_to_remove.append(idx)
        # Else check to see if the description indicates a placeholder
        # row, which should be deleted before the technologies are
        # summarized and returned from this function
        elif re.search('placeholder', row['technology name']):
            rows_to_remove.append(idx)
        # Implicitly, if the text does not match any regex, it is
        # assumed that it does not need to be edited or removed

    # Delete the placeholder rows
    result = np.delete(tech_array, rows_to_remove, 0)

    return result


def cost_perf_extractor(single_tech_array, sd_array, sd_names, years, flag):
    """Produces a dict of cost or performance data for a single technology.

    From a numpy structured array of data for a single technology
    with several rows corresponding to different performance levels,
    this function converts the reported capital costs or efficiencies
    for all of the different performance levels into a mean (called
    'typical' in the output dict) and a maximum ('best' in the output
    dict) for this technology class. Service demand data for each of
    the performance levels is used to calculate a service demand-
    weighted cost or efficiency for the 'typical' or mean case.
    A unique value is calculated and reported for each year in the
    years vector, which specifies the range of years over which the
    final data are to be output to the cost/performance/lifetime JSON.

    Args:
        single_tech_array (numpy.ndarray): Structured array of EIA
            technology characteristics data reduced to the various
            performance levels (if applicable) for a single technology
            (e.g., 'VAV_Vent' or 'comm_GSHP-heat')
        sd_array (numpy.ndarray): EIA service demand data for the entire
            microsegment associated with the specific technology that
            appears in single_tech_array
        sd_names (list): Strings describing the service demand data, with
            each entry in the list corresponding to that row in sd_array
        years (list): The range of years of interest, each as YYYY
        flag (str): String that should be either 'cost' or 'performance'
            to indicate the type of data the function is processing and
            will return

    Returns:
        A top-level dict with keys for the 'typical' and 'maximum' cost
        or performance cases, and child dicts for each case with values
        reported for each year in years. Also a list of technology
        names that didn't match between the technology cost,
        performance, and lifetime data and the service demand data.
    """

    # Using the string in the 'flag' argument, set a variable
    # for the column that contains the desired data to obtain
    # from single_tech_array
    if flag == 'cost':
        col = 'c1'
    elif flag == 'performance':
        col = 'eff'

    # Store the number of rows (different performance levels) in
    # single_tech_array and the number of years in the desired
    # range for the final data
    n_entries = np.shape(single_tech_array)[0]
    n_years = len(years)

    # Preallocate arrays for the technology cost or performance
    # and service demand data
    val = np.zeros([n_entries, n_years])
    select_sd = np.zeros([n_entries, n_years])

    # Preallocate list of non-matching technology names
    non_matching_tech_names = []

    for idx, row in enumerate(single_tech_array):
        # Determine the starting and ending column indices for the
        # desired data (cost or performance) related to the
        # technology associated with this row
        idx_st = row['y1'] - min(years)

        # Calculate end index using the smaller of either the last year
        # of 'years' or the final year of availability for that technology
        idx_en = min(max(years), row['y2']) - min(years) + 1

        # If the indices calculated above are in range, record the data
        # (cost or performance) in the calculated location(s)
        if idx_en > 0:
            if idx_st < 0:
                idx_st = 0
            val[idx, idx_st:idx_en] = row[col]

        # If the final year of availability (market exit year) for the
        # particular technology performance level corresponding to 'row'
        # is before the first year in years, do not update the service
        # demand data array used later to calculate val_mean and val_max
        if idx_en > 0:
            # The technology name from the ktek data must be updated to have
            # formatting consistent with the slightly different service
            # demand data technology names

            # Identify technology name for the current row of the ktek data
            name_from_ktek = row['technology name']

            # Check to see if either an ampersand or double-quote
            # symbol is present in the ktek technology name string
            ampersand_present = re.search('&', name_from_ktek)
            quote_present = re.search('"', name_from_ktek)

            # For matching purposes, replace the ampersand and quote
            # symbols with the HTML-like strings that appear in the
            # service demand data
            if ampersand_present:
                name_from_ktek = re.sub('&', '&amp;', name_from_ktek)
            elif quote_present:
                name_from_ktek = re.sub('"', '&quot;', name_from_ktek)

            # Truncate technology name string from technology data to
            # 44 characters since all string descriptors in the service
            # demand data are limited to that length, then remove any
            # trailing spaces that might create text matching problems
            name_from_ktek = name_from_ktek[:44].strip()

            # Find the matching row in service demand data by comparing
            # the row technology name to sd_names and use that index to
            # extract the service demand data and insert them into the
            # service demand array in the same row as the corresponding
            # cost data
            try:
                select_sd[idx, ] = sd_array[sd_names.index(name_from_ktek), ]
            except ValueError:
                # If no match is found, add the unmatched technology
                # name to a list
                non_matching_tech_names.append(name_from_ktek)

    # Normalize the service demand data to simplify the calculation of
    # the service demand-weighted arithmetic mean of the desired data
    # (but perform the calculation only if there is at least one
    # non-zero entry in select_sd)
    if select_sd.any():
        # Suppress any divide by zero warnings
        with np.errstate(divide='ignore', invalid='ignore'):
            # Calculate the normalized service demand
            select_sd = select_sd/np.sum(select_sd, 0)
            select_sd = np.nan_to_num(select_sd)  # Replace nan from 0/0 with 0

    # Using the normalized service demand as the weights, calculate the
    # weighted arithmetic mean for each year (each column)
    val_mean = np.sum(np.transpose(select_sd)*single_tech_array[col], 1)

    # Calculate the maximum cost or performance for each year (each
    # column of the technology data array), adjusting for differences
    # in the calculation method (the arithmetic mean calculation does
    # not take into account market entry and exit years, relying on the
    # service demand weights to zero out technologies that are not
    # available in a given year) that can occasionally lead to the
    # mean being greater than than the maximum
    val_max = np.fmax(np.amax(val, 0), val_mean)

    # Build complete structured dict with 'typical' and 'best' data
    # converted into dicts themselves, indexed by year
    final_dict = {'typical': dict(zip(map(str, years), val_mean)),
                  'best': dict(zip(map(str, years), val_max))}

    return final_dict, non_matching_tech_names


def life_extractor(single_tech_array, years):
    """Produces a nested dict of lifetime data for a single technology.

    From a numpy structured array with the cost, performance, and
    lifetime data for a specific technology, calculate the arithmetic
    mean lifetime and 'range', which is calculated for the residential
    data as the difference between the maximum and the mean for each
    year. This function accounts for cases where the performance levels
    for a given technology exit the market before another level enters
    with the assumption that the previous lifetime should persist until
    the next performance level enters the market.

    Args:
        single_tech_array (numpy.ndarray): Structured array of EIA
            technology characteristics data reduced to the various
            performance levels (if applicable) for a single technology
            (e.g., 'VAV_Vent' or 'comm_GSHP-heat')
        years (list): The range of years of interest, each as YYYY

    Returns:
        A top-level dict with keys for the 'typical' and 'maximum'
        lifetime cases, and child dicts for each case with values
        reported for each year in years.
    """

    # Store the number of rows (different performance levels) in
    # single_tech_array and the number of years in the desired
    # range for the final data
    n_entries = np.shape(single_tech_array)[0]
    n_years = len(years)

    # Preallocate arrays for the lifetime data
    life = np.zeros([n_entries, n_years])

    for idx, row in enumerate(single_tech_array):
        # Determine the starting and ending column indices for the
        # lifetime of the technology performance level in this row
        idx_st = row['y1'] - min(years)

        # Calculate end index using the smaller of either the last year
        # of 'years' or the final year of availability for that technology
        idx_en = min(max(years), row['y2']) - min(years) + 1

        # If the indices calculated above are in range, record the
        # lifetime in the calculated location(s)
        if idx_en > 0:
            if idx_st < 0:
                idx_st = 0
            life[idx, idx_st:idx_en] = row['Life']

    # Calculate the mean lifetime for each column, excluding 0 values
    with warnings.catch_warnings():
        # In cases where a particular technology does not have a
        # performance level defined as available for a given year,
        # excluding 0 values leaves nothing on which to calculate a
        # mean, which triggers a RuntimeWarning that is suppressed
        # here using the warnings package
        warnings.simplefilter("ignore", category=RuntimeWarning)
        life_mean = np.apply_along_axis(
            lambda v: np.mean(v[np.nonzero(v)]), 0, life)

    # In the special case where no performance level is given because
    # the product exits the market before the first year in the 'years'
    # vector, make the entire reported mean lifetime equal to 0 in each
    # year using the life array, which should still be populated with
    # only zeros
    if np.all(np.isnan(life_mean)):
        life_mean = np.mean(life, 0)
    # In the special case where there were years with no performance
    # level indicated in the 'life' array, the mean will be 'nan'; it
    # is assumed that the previous technology's lifetime persists until
    # the next performance level enters the market
    elif np.any(np.isnan(life_mean)):
        # First, identify the numeric values reported
        numbers = life_mean[~np.isnan(life_mean)]

        # Then, generate a vector that, for each entry in the final
        # life_mean vector, has the index for the appropriate number
        # to be pulled from the 'numbers' vector
        indices = np.cumsum(~np.isnan(life_mean)) - 1

        # Use the indices and the numbers to adjust life_mean
        life_mean = numbers[indices]

    # Calculate the lifetime range in each column using the same method
    # as mseg_techdata.py (note that this quantity is not related to
    # any statistical definitions of range) and account for any cases
    # where life_mean was just adjusted to be non-zero in some years
    life_range = np.fmax(np.amax(life, 0), life_mean) - life_mean

    # Build complete structured dict with 'average' and 'range' data
    # converted into dicts that are indexed by year
    final_dict = {'average': dict(zip(map(str, years), life_mean)),
                  'range': dict(zip(map(str, years), life_range))}

    return final_dict


def tech_names_extractor(tech_array):
    """Creates a list of unique technology "names" for a microsegment.

    Text strings are used to identify which cost, performance, and
    lifetime data are associated with what technologies. This function
    identifies appropriate text strings to use for each of the
    technologies in a single microsegment.

    Args:
        tech_array (numpy.ndarray): EIA technology characteristics
            data available for a single microsegment, including cost,
            performance, and lifetime data for (typically multiple)
            performance scenarios for each technology applicable to
            that microsegment.

    Returns:
        A list of strings, where each string represents a technology
        "name" or descriptor that does not include scenario-specific
        details like "2020 high" or "2009 installed base".
    """

    # Create empty list to be populated with technology names
    technames = []

    for row in tech_array:
        # Identify the technology name from the 'technology name' column
        # in the data using a regex set up to match any text '.+?' that
        # appears before the first occurrence of a space followed by a
        # 2 and three other numbers (e.g., 2009 or 2035)
        tech_name = re.search('.+?(?=\s2[0-9]{3})', row['technology name'])

        # If the regex matched, add the matching text, which describes
        # the technology without scenario-specific text like '2003
        # installed base', to the technames list
        if tech_name:
            technames.append(tech_name.group(0))
        # Else, if the technology name is not from a placeholder row,
        # add the entire name text to the technames list
        else:
            if not re.search('placeholder', row['technology name']):
                technames.append(row['technology name'])

    # Reduce the list to only the unique entries
    technames = list(np.unique(technames))

    return technames


def mseg_technology_handler(tech_data, sd_data, sel, years):
    """Reformats cost, performance, and lifetime data into a dict.

    Using external functions that process and reformat specific
    categories of data from the EIA source data arrays, this function
    converts the cost, performance, and lifetime data for each
    technology within a particular microsegment to a dict format that
    is consistent with the residential technology data. Those data for
    each technology are then added to a master dict that ultimately
    includes all of the technologies in the microsegment.

    This function is called for each terminal, or leaf, node in the
    microsegments JSON database that governs the structure of the major
    project input files that are based on EIA Annual Energy Outlook
    data. Each of those leaf nodes corresponds to a single, unique
    microsegment. The dict returned by this function to be placed at
    the leaf node includes the data for all of the technologies
    applicable to that microsegment.

    This function is relevant to all microsegments with a numeric end
    use code <= 7 (i.e., all end uses except for PCs, non-PC office
    electronics, and "other").

    Args:
        tech_data (numpy.ndarray): Imported EIA technology characteristics
            data, with multiple efficiency levels for each technology,
            including technology cost, performance, and service lifetime.
        sd_data (numpy.ndarray): Imported EIA service demand data specified
            over the same efficiency levels for each technology.
        sel (list): A list of integers indicating the microsegment.
        years (list): A list of integers representing the range of years
            in the data, precalculated for speed.

    Returns:
        A dict that specifies the cost, performance, and lifetime on
        a technology-specific basis for all of the technologies in the
        microsegment indicated by the 'sel' argument. Also a list of
        the technology names in the microsegment that did not match
        between the cost, performance, and lifetime data and the
        service demand data.
    """

    # Instantiate a master dict for this microsegment
    complete_mseg_tech_data = {}

    # From the imported EIA data, extract the technology and service
    # demand data for the microsegment identified by 'sel'
    filtered_tech_data = tech_data_selector(tech_data, sel)
    (filtered_sd_data, sd_names_list) = sd_data_selector(sd_data, sel, years)

    # Use the 'units_id' function to extract the cost and performance
    # units for the microsegment specified by 'sel'
    the_cost_units = units_id(sel, 'cost')
    the_performance_units = units_id(sel, 'performance')

    # Identify the names (as strings) of all of the technologies
    # included in this microsegment
    tech_names_list = tech_names_extractor(filtered_tech_data)

    # Preallocate a list of non-matching technology names for this microsegment
    mseg_non_matching_names = []

    # Extract the cost, performance, and lifetime data for each
    # technology in this microsegment, insert those data into a dict
    # with the correct structure, and append that dict to the master
    # dict for this microsegment
    for tech in tech_names_list:
        # Extract the cost, performance, and lifetime data specific
        # to a single technology, given by 'tech'
        single_tech_data = single_tech_selector(filtered_tech_data, tech)

        # Extract the cost data, restructure into the appropriate dict
        # format, and append the units and data source
        the_cost, cost_non_matching_names = cost_perf_extractor(
            single_tech_data,
            filtered_sd_data,
            sd_names_list,
            years, 'cost')
        the_cost['units'] = the_cost_units
        the_cost['source'] = 'EIA AEO'

        # Extract the performance data, restructure into the appropriate
        # dict format, and append the units and data source
        the_perf, _ = cost_perf_extractor(
            single_tech_data,
            filtered_sd_data,
            sd_names_list,
            years, 'performance')
        the_perf['units'] = the_performance_units
        the_perf['source'] = 'EIA AEO'

        # Extract the lifetime data, restructure into the appropriate
        # dict format, and append the units and data source
        the_life = life_extractor(single_tech_data, years)
        the_life['units'] = 'years'
        the_life['source'] = 'EIA AEO'

        # Following the format used for the residential data, combine
        # the cost, performance, and lifetime data for the technology
        # identified by the variable 'tech' into a single dict
        tech_data_dict = {'installed cost': the_cost,
                          'performance': the_perf,
                          'lifetime': the_life}

        # Add the data for this technology to the master dict for the
        # entire microsegment
        complete_mseg_tech_data[tech] = tech_data_dict

        # If there were any non-matching names identified, replace the
        # preallocated empty list with the list of non-matching names;
        # note that only the non-matching names from the cost case are
        # included here since the list of names will be the same for
        # either the cost or performance data extraction
        if cost_non_matching_names:
            mseg_non_matching_names = cost_non_matching_names

    return complete_mseg_tech_data, mseg_non_matching_names


def walk(tech_data, serv_data, years, json_db, key_list=[], no_match_names=[]):
    """Recursively explore the JSON structure and add the appropriate data.

    Note that this walk function and the data processing function
    ('mseg_techology_handler') are set up slightly differently than in
    com_mseg. Here, the json_interpreter function is called before the
    data processing function and the numeric indices are passed to the
    function, rather than sending the list of keys from the JSON to
    that function and calling json_interpreter within the function.

    Args:
        tech_data (numpy.ndarray): A numpy structured array of the
            EIA technology data, including the cost, performance,
            and lifetime of individual technologies.
        serv_data (numpy.ndarray): A numpy structured array of the
            EIA service demand data.
        years (list): A list of the years (YYYY) of data to be converted.
        json_db (dict): The nested dict structure of the empty or
            partially complete database to be populated with new data.
        key_list (list): The list of keys that define the current
            location in the database structure.
        no_match_names (list): A list of names of technologies found in
             the cost, performance, and lifetime data, but not in the
             service demand data.

    Returns:
        A complete and populated dict structure for the JSON database,
        and a list of all technology names that did not find a match.
    """

    # Explore data structure from current level
    for key, item in json_db.items():

        # If there are additional levels in the dict, call the function
        # again to advance another level deeper into the data structure
        if isinstance(item, dict):
            walk(tech_data, serv_data, years, item, key_list + [key])

        # If a leaf node has been reached, check if the second entry in
        # the key list is one of the recognized building types and that
        # there are more than two total keys present (to exclude square
        # footage leaf nodes), and if so, finish constructing the key
        # list for the current location and obtain the data to update
        # the dict
        else:
            if key_list[1] in cm.bldgtypedict.keys() and len(key_list) > 2:
                leaf_node_keys = key_list + [key]

                # Convert keys into integers that define the microsegment
                mseg_codes = cm.json_interpreter(leaf_node_keys)

                # Skip all demand microsegments and end uses coded > 7
                if 'demand' not in leaf_node_keys and mseg_codes[2] <= 7:

                    # Extract data from original data sources
                    data_dict, non_matching_names = mseg_technology_handler(
                        tech_data, serv_data, mseg_codes, years)

                    # Set dict key to extracted data
                    json_db[key] = data_dict

                    # If non-matching names are identified, add them to
                    # the existing list of non-matched technology names
                    if non_matching_names:
                        no_match_names.extend(non_matching_names)

    return json_db, no_match_names


def dtype_reducer(the_dtype, wanted_cols):
    """Remove extraneous columns from the dtype definition.

    In cases where a data file includes some columns of data that are
    not of particular interest or relevance, this function can remove
    those columns that are not needed (or more accurately, retain only
    the columns that are desired). This function was originally created
    for the purpose of importing the EIA ktek data, which may include
    some columns with mixed data types that are difficult to import and
    not relevant to this analysis anyway. Avoiding those columns
    entirely is easier than developing far more sophisticated functions
    to import the data.

    Args:
        the_dtype (list): A list of tuples with each tuple containing two
            entries, a column heading string, and a string defining the
            data type for that column. Formatted as a numpy dtype list.
        wanted_cols (list): A list of strings that represent the names of
            the columns from the ktek data that should be kept.

    Returns:
        col_loc is a list of the numeric indices for the positions of
        the columns retained in the dtype definition (and thus which
        columns should be retained when importing the full data file).
        shortened_dtype is the dtype definition (in numpy dtype format)
        that includes only the desired columns.
    """

    # Strip apart the dtype definition
    headers, dtypes = zip(*the_dtype)

    # Preallocate list for the numeric column indices of the wanted_cols
    col_loc = []

    # Make a list of the numeric index positions of the desired columns
    for entry in wanted_cols:
        try:
            col_loc.append(headers.index(entry))
        except ValueError:
            print('desired column ' + entry + ' not found in the ktek data')

    # Update the headers and dtypes by building them as new lists with
    # only the desired columns and then recombining them into the numpy
    # dtype definition format
    headers = [headers[i] for i in col_loc]
    dtypes = [dtypes[i] for i in col_loc]
    shortened_dtype = list(zip(headers, dtypes))

    return col_loc, shortened_dtype


def main():
    """Import external data files, process contents, and generate output data.

    This function imports the required EIA data files with the relevant
    cost, performance, and equipment lifetime data and calls the
    appropriate functions to convert their contents into the JSON file
    format and nested structure expected. After extracting the data
    from the original EIA source files, they are converted from a
    census division to a climate zone basis.

    The census division to climate zone conversion data file appropriate
    for the cost, performance, and lifetime data is formatted such that
    the translation factors act as weights to compute a weighted average
    of the cost, performance, and lifetime values reported. This file is
    different from the file used for the conversion for the energy data
    and is specific to commercial buildings.
    """

    # Instantiate object that contains useful variables
    handyvars = UsefulVars()

    # Import technology cost, performance, and lifetime data in
    # EIA AEO 'KTEK' data file
    tech_dtypes = cm.dtype_array(handyvars.cpl_data, ',',
                                 handyvars.cpl_data_skip_lines)
    col_indices, tech_dtypes = dtype_reducer(tech_dtypes,
                                             handyvars.columns_to_keep)
    tech_dtypes[8] = ('Life', 'f8')  # Manual correction of lifetime data type
    tech_data = cm.data_import(handyvars.cpl_data, tech_dtypes, ',',
                               handyvars.cpl_data_skip_lines, col_indices)

    # Import EIA AEO 'KSDOUT' service demand data
    serv_dtypes = cm.dtype_array(cm.serv_dmd)
    serv_data = cm.data_import(cm.serv_dmd, serv_dtypes)
    serv_data = cm.str_cleaner(serv_data, 'Description')

    # Define years vector
    years = list(range(2009, 2041))

    # Import census division to climate zone conversion data, using
    # the appropriate file for weighting the cost, performance, and
    # lifetime data
    czone_cdiv_conversion = np.genfromtxt(handyvars.com_climate_convert_rev,
                                          names=True,
                                          delimiter='\t',
                                          dtype=None)

    # Import empty microsegments JSON file and traverse database structure
    with open(handyvars.json_in, 'r') as jsi:
        msjson = json.load(jsi)

        # Proceed recursively through database structure
        result, stuff = walk(tech_data, serv_data, years, msjson)

        # Print warning message to the standard out with a unique
        # (i.e., non-repeating) list of technologies that didn't have
        # a match between the two data sets and thus were not added
        # to the aggregated cost or performance data in the output JSON
        if stuff:
            text = ('Warning: some technologies reported in the '
                    'technology characteristics data were not found to '
                    'have corresponding service demand data and were '
                    'thus excluded from the reported technology cost: '
                    'and performance:')
            print(text)
            for item in sorted(list(set(stuff))):
                print('   ' + item)

        # Convert the updated data from census division to climate breakdown
        result = mseg.clim_converter(result, czone_cdiv_conversion)

    # Write the updated dict of data to a new JSON file
    with open(cm.json_out, 'w') as jso:
        json.dump(result, jso, indent=2)

if __name__ == '__main__':
    main()
