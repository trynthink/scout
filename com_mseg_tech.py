#!/usr/bin/env python3

# Import commercial microsegments code to use some of its data
# reading and processing functions
import com_mseg as cm

import numpy as np


def cost_extractor(tech_array, years):
    """ From a numpy structured array of data for a single technology
    with several rows corresponding to different performance levels,
    this function converts the reported capital costs for all of the
    different performance levels into a mean (called 'typical' in the
    output dict) and a maximum ('best') for this technology class.
    A unique value is calculated and reported for each year in the
    years vector, which specifies the range of years over which the
    final data are to be output to the cost/performance/lifetime JSON. """

    # Store the number of rows (different technologies) in tech_array
    # and the number of years in the desired range for the final data
    n_entries = np.shape(tech_array)[0]
    n_years = len(years)

    # Create a temporary array in which the cost data will be stored
    tmp = np.zeros([n_entries, n_years])

    for idx, row in enumerate(tech_array):
        # Determine the starting and ending column indices for the
        # capital cost of the technology for this row
        idx_st = row['y1'] - min(years)
        # Calculate end index using the smaller of either the last year
        # of 'years' or the final year of availability for that technology
        idx_en = min(max(years), row['y2']) - min(years) + 1

        # If the indices calculated above are in range, record the
        # capital cost in the calculated location(s)
        if idx_en > 0:
            if idx_st < 0:
                idx_st = 0
            tmp[idx, idx_st:idx_en] = row['c1']

    # Calculate the mean cost for each column, excluding 0 values
    cost = np.apply_along_axis(lambda v: np.mean(v[np.nonzero(v)]), 0, tmp)

    # Calculate the maximum cost in each column
    cost_max = np.amax(tmp, 0)

    # Build complete structured dict with 'typical' and 'best' data
    # converted into dicts themselves, indexed by year
    final_dict = {'typical': dict(zip(map(str, years), cost)),
                  'best': dict(zip(map(str, years), cost_max))}

    return final_dict


def tech_data_selector(tech_data, sel):
    """ From the full structured array of cost, performance, and
    lifetime data from the AEO, extract a group of data using numeric
    indices generated from the text indices at the leaf nodes of the
    input microsegments JSON. Each group of data extracted by this
    function should correspond to all of the performance levels given
    for a single technology, and (crucially) no other technologies. """

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

if __name__ == '__main__':
    main()
