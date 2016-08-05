#!/usr/bin/env python3

""" Develop useful metadata from the EIA data files. """

import mseg as rm
import mseg_techdata as rmt
import com_mseg as cm
import com_mseg_tech as cmt

import numpy as np
import re
import json
import types
from contextlib import suppress


def extract_year_range(data_array, colnames, min_years, max_years, pivot_yr=0):
    """Determine the minimum and maximum years of data in a given AEO file.

    For a given AEO data file that has been imported and formatted
    into a numpy structured array, this function looks in the column(s)
    specified for the minimum and maximum calendar years reported.
    Ultimately, this function produces a conservative range for the
    minimum and maximum years across those columns, taking the largest
    (latest) of the reported minimum years and the smallest (earliest)
    of the reported maximum years. The handling of column names is done
    based on whether there are one or two columns given. In the case
    where there are two columns, they are assumed to represent low
    (e.g., market entry year) and high (e.g., market exit year) year
    datasets.

    Args:
        data_array (numpy.ndarray): A numpy structured array of EIA AEO
            residential or commercial building energy and stock or
            equipment characteristic data.
        colnames (list): List of strings specifying the name(s) of the
            column(s) containing year data.
        min_years (list): The earliest years found from imported data.
        max_years (list): The latest years found from imported data.

    Returns:
        Updated lists of minimum and maximum years with the minimum
        and maximum found in data_array.
    """

    # Preallocate minimum and maximum year variables
    min_yr = 0
    max_yr = 10000

    # If there are two columns given, assume that they represent lower
    # bound and upper bound years, and obtain the min from the lower
    # bound set and the max from the upper bound set of years
    if len(colnames) == 2:
        data_array_min_years = data_array[colnames[0]]
        data_array_max_years = data_array[colnames[1]]

        min_yr = min(data_array_min_years)
        max_yr = max(data_array_max_years)

    # Otherwise, assume all the columns of year data are directly
    # comparable and run through all of them to obtain a _conservative_
    # indication of the min and max years in the data
    else:
        for name in colnames:
            data_array_years = data_array[name]

            min_yr = max(min_yr, min(data_array_years))
            max_yr = min(max_yr, max(data_array_years))

    # Circumvents the action of .append() modifying in place the lists
    # passed to the function
    new_min_years = min_years + [min_yr + pivot_yr]
    new_max_years = max_years + [max_yr + pivot_yr]

    return new_min_years, new_max_years


def dtype_ripper(the_dtype, min_years, max_years):
    """Extract the range of years from the dtype of a structured array.

    Args:
        the_dtype (list): A list of tuples with each tuple containing two
            entries, a column heading string, and a string defining the
            data type for that column. Formatted as a numpy dtype list.
        min_years (list): The earliest years found from imported data.
        max_years (list): The latest years found from imported data.

    Returns:
        Updated lists of minimum and maximum years with the minimum
        and maximum found in data_array.
        The minimum and maximum years, as integers, that were contained
        in the column headings of the dtype definition.
    """

    # Strip the dtype into its constituent lists: column names and data formats
    colnames, dtypes = zip(*the_dtype)

    # Preallocate a list for the years extracted from the column names
    year_list = []

    # Loop over the list of column names, identify entries that have
    # the format specified by a regex, and add the matches to a list
    for name in colnames:
        year = re.search('^[1|2][0-9]{3}$', name)
        if year:
            year_list.append(year.group())

    # Identify the minimum and maximum years from the list of the years
    # in the column names and record them as integers instead of strings
    min_yr = int(min(year_list))
    max_yr = int(max(year_list))

    # Circumvents the action of .append() modifying in place the lists
    # passed to the function
    new_min_years = min_years + [min_yr]
    new_max_years = max_years + [max_yr]

    return new_min_years, new_max_years


def EIA_filename_identifier():
    """Create a list of the EIA files identified in the imported modules.

    This function takes a list of all of the imported modules and looks
    within each for a class called EIAData. If such a class is found,
    the strings for the file names of the EIA data imported by that
    module are added to a list of filenames.

    Returns:
        A list of filenames from the classes that identify the EIA data
        files from all of the imported modules.
    """

    # Initialize the list of filenames
    filenames = []

    # Loop over all of the globals present in this module and check
    # each to determine if it is a module
    for name, val in globals().items():
        # Note that 'name' is the reference name for the module, but
        # 'val' is the module reference; for example, in the statement
        # 'import os as kicker', name = 'kicker' and val refers to 'os'
        if isinstance(val, types.ModuleType):
            # Ignore the AttributeError exception raised for modules
            # that do not have an EIAData attribute
            with suppress(AttributeError):
                # Create an EIAData class object for the module
                # identified by 'name'
                data_class = getattr(globals()[name], 'EIAData')
                # Extract the values in __dict__ from the EIAData class
                # and append the resulting list to the existing
                # filenames list
                filenames = filenames + list(data_class().__dict__.values())

    return filenames


def main():
    """ Each of the AEO data files includes data reported over a range
    of calendar years. These data should ultimately be reported over a
    common range of years. To determine the common range across all of
    the AEO data, the major files are imported here and the minimum and
    maximum years from each file are compared to determine the range
    that is common for all of those files. """

    # Instantiate lists to store minimum and maximum years identified
    # from the data
    min_yrs = []
    max_yrs = []

    # Generate the list of EIA data filenames from all of the imported modules
    files_ = EIA_filename_identifier()

    # Remove rsclass.txt if it is present, since that file does not
    # have any data reported by year
    files_ = [file_ for file_ in files_ if file_ != 'rsclass.txt']

    # # Import residential stock and energy data
    # supply = np.genfromtxt(rm.EIAData().res_energy, names=True,
    #                        delimiter='\t', dtype=None)
    # supply = rm.array_row_remover(supply, rm.UsefulVars().unused_supply_re)

    # # Extract years from imported residential stock and energy data
    # # and remove the name of the file with those data from the list
    # min_yrs, max_yrs = extract_year_range(supply, ['YEAR'], min_yrs, max_yrs)
    # files_.remove(rm.EIAData().res_energy)

    # TEMPORARY
    # IS THERE A WAY TO MODULARIZE THIS SO THAT THE FUNCTION CALL TO IMPORT
    # AND UPDATE THE DATA CAN BE PASSED TO THAT FUNCTION AND THE FILE CAN
    # BE REMOVED FROM THE LIST AT THE SAME TIME?
    def file_remover(file_name, col_index, func_name, files_list,
                     min_yrs, max_yrs):
        data_object = func_name(file_name)
        # Extract years from imported residential stock and energy data
        # and remove the name of the file with those data from the list
        min_yrs, max_yrs = extract_year_range(data_object, col_index,
                                              min_yrs, max_yrs)

        files_.remove(file_name)

        return min_yrs, max_yrs

    def residential(file_name):
        # Import residential stock and energy data
        supply = np.genfromtxt(file_name, names=True,
                               delimiter='\t', dtype=None)
        supply = rm.array_row_remover(supply, rm.UsefulVars().unused_supply_re)

        return supply

    min_yrs, max_yrs = file_remover(rm.EIAData().res_energy, ['YEAR'],
                                    residential, files_, min_yrs, max_yrs)

    # mseg_techdata (res_mseg_tech) -----------------------------------

    # Import EIA non-lighting residential cost and performance data
    eia_nlt_cp = np.genfromtxt(rmt.EIAData().r_nlt_costperf,
                               names=rmt.r_nlt_cp_names,
                               dtype=None, skip_header=20, comments=None)

    min_yrs, max_yrs = extract_year_range(eia_nlt_cp,
                                          ['START_EQUIP_YR', 'END_EQUIP_YR'],
                                          min_yrs, max_yrs)

    # Import EIA lighting residential cost, performance and lifetime data
    eia_lt = np.genfromtxt(rmt.EIAData().r_lt_all,
                           names=rmt.r_lt_names, dtype=None,
                           skip_header=35, skip_footer=54, comments=None)

    min_yrs, max_yrs = extract_year_range(eia_lt,
                                          ['START_EQUIP_YR', 'END_EQUIP_YR'],
                                          min_yrs, max_yrs)

    # com_mseg --------------------------------------------------------

    # Import EIA AEO 'KSDOUT' service demand file
    serv_dtypes = cm.dtype_array(cm.EIAData().serv_dmd)

    # A different thing entirely because the years are in the header TEMPORARY
    min_yrs, max_yrs = dtype_ripper(serv_dtypes, min_yrs, max_yrs)

    # Import EIA AEO 'KDBOUT' additional data file
    catg_dtypes = cm.dtype_array(cm.EIAData().catg_dmd)
    catg_data = cm.data_import(cm.EIAData().catg_dmd, catg_dtypes)

    min_yrs, max_yrs = extract_year_range(catg_data, ['Year'],
                                          min_yrs, max_yrs,
                                          cm.UsefulVars().pivot_year)

    # com_mseg_tech ---------------------------------------------------

    # Import technology cost, performance, and lifetime data in
    # EIA AEO 'KTEK' data file
    tech_dtypes = cm.dtype_array(cmt.EIAData().cpl_data, ',',
                                 cmt.UsefulVars().cpl_data_skip_lines)
    col_indices, tech_dtypes = cmt.dtype_reducer(
                                    tech_dtypes,
                                    cmt.UsefulVars().columns_to_keep)
    tech_dtypes[8] = ('Life', 'f8')  # Manual correction of lifetime data type
    tech_data = cm.data_import(cmt.EIAData().cpl_data, tech_dtypes, ',',
                               cmt.UsefulVars().cpl_data_skip_lines,
                               col_indices)

    min_yrs, max_yrs = extract_year_range(tech_data, ['y1', 'y2'],
                                          min_yrs, max_yrs)

    # Import EIA AEO 'kprem' time preference premium data
    tpp_data = cmt.kprem_import(cmt.EIAData().tpp_data,
                                cmt.UsefulVars().tpp_dtypes,
                                cmt.UsefulVars().tpp_data_skip_lines)

    min_yrs, max_yrs = extract_year_range(tpp_data, ['Year'], min_yrs, max_yrs)

    # Check that all of the expected files have been imported, and if
    # any files remain, print the filenames to the console
    if files_:
        # Generate a neatly formatted file string
        files_str = ''
        for file_ in files_:
            if file_ != files_[-1]:
                files_str = files_str + file_ + ', '
            elif len(files_) == 1:
                files_str = files_str + file_
            else:
                files_str = files_str + 'and ' + file_

        # Print the unused file names to the console
        print('Some EIA residential and/or commercial data files were '
              'not imported. These files were: ' + files_str)

    # Construct a dict with the minimum and maximum years recorded as integers
    year_range_result = {'min year': int(max(min_yrs)),
                         'max year': int(min(max_yrs))}

    # Output a tiny JSON file with two integer values
    with open('metadata.json', 'w') as jso:
        json.dump(year_range_result, jso, indent=2)

if __name__ == '__main__':
    main()
