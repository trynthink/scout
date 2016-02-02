#!/usr/bin/env python3

# Import commercial microsegments code to use some of its data
# reading and processing functions
import com_mseg as cm

import numpy as np
import re
import warnings


def units_id(sel, flag):
    """ docstring """

    # For readability, assign the end use number to a clearly named variable
    enduse = sel[2]

    # Determine units depending on whether this function was called
    # for cost or performance units
    if flag == 'cost':
        if enduse == 4:  # ventilation
            theunits = '$2013/1000 cfm'
        elif enduse == 6:  # lighting
            theunits = '$2013/1000 lm'
        else:
            theunits = '$2013/kBTU out-hr'
    elif flag == 'performance':
        if enduse == 4:  # ventilation
            theunits = 'cfm-hr/BTU'  # BTU in
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
    """ Each microsegment is comprised of multiple technologies. Cost,
    performance, and lifetime data are needed for each technology in a
    microsegment. This function separates out those data for a specific
    technology from all of the technologies in the microsegment so that
    they can be processed and further restructured for later output. """

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
        elif tech_name != specific_name:
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
    """ From a numpy structured array of data for a single technology
    with several rows corresponding to different performance levels,
    this function converts the reported capital costs or efficiencies
    for all of the different performance levels into a mean (called
    'typical' in the output dict) and a maximum ('best' in the output
    dict) for this technology class. Service demand data for each of
    the performance levels is used to calculate a service demand-
    weighted cost or efficiency for the 'typical' or mean case.
    A unique value is calculated and reported for each year in the
    years vector, which specifies the range of years over which the
    final data are to be output to the cost/performance/lifetime JSON. """

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

        # Find the matching row in service demand data by comparing
        # the row technology name to sd_names and use that index to
        # extract the service demand data and insert them into the
        # service demand array in the same row as the corresponding
        # cost data
        select_sd[idx, ] = sd_array[sd_names.index(row['technology name']), ]

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

    return final_dict


def life_extractor(single_tech_array, years):
    """ From a numpy structured array with the cost, performance, and
    lifetime data for a specific technology, calculate the arithmetic
    mean lifetime and 'range', which is calculated for the residential
    data as the difference between the maximum and the mean for each
    year. This function accounts for cases where the performance levels
    for a given technology exit the market before another level enters
    with the assumption that the previous lifetime should persist until
    the next performance level enters the market. """

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

    # In the special case where there were years with no performance
    # level indicated in the 'life' array, the mean will be 'nan'; it
    # is assumed that the previous technology's lifetime persists until
    # the next performance level enters the market
    if np.any(np.isnan(life_mean)):
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

if __name__ == '__main__':
    main()
