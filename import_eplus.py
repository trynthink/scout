#!/usr/bin/env python3
import xlrd
import numpy
import re

# Define CBECS square footage file
CBECS_in = "b34.xlsx"
# Define EnergyPlus data file
EPlus_perf_in = "advanced_hybrid_rtus.xlsx"


def CBECS_vintage_sf(CBECS_sh):
    """ Import commercial floorspace data by vintage from CBECS
    'b34.xlsx' raw data file """

    # Initialize a dictionary for the CBECS vintage square footages
    vintage_sf = {}
    # Initialize a flag for the first relevant row in the CBECS Excel sheet
    start_row_flag = 0

    # Loop through all rows in the Excel sheet, and pull out sq.ft. data
    for i in range(CBECS_sh.nrows):
        # Check for a string that indicates the start of the sq.ft. data rows
        if CBECS_sh.cell(i, 0).value == "Year constructed":
            start_row_flag = 1
        # Check for a string that indicates the end of sq.ft. data rows (break)
        elif CBECS_sh.cell(i, 0).value == "Census region and division":
            break
        # If start row flag hasn't been raised, skip row
        elif start_row_flag == 0:
            continue
        # If start row flag has been raised, read in sq.ft. data from row
        else:
            vintage_bin = CBECS_sh.cell(i, 0).value
            sf_val = CBECS_sh.cell(i, 6).value
            vintage_sf[vintage_bin] = sf_val

    # If the start row flag was never raised, yield an error
    if start_row_flag == 0:
        raise ValueError('Problem reading in the CBECS sq.ft. data!')

    # Return the square footage information
    return vintage_sf


def find_vintage_weights(vintage_sf, EPlus_vintages):
    """ Use CBECS building vintage square footage data to derive weighting
    factors that will map the EnergyPlus building vintages to the 'new'
    and 'retrofit' building structure types of Scout """

    # Set the expected names of the EnergyPlus building vintages and the
    # low and high year limits of each building vintage category
    expected_EPlus_vintage_yr_bins = {
        '90.1-2004': [2004, 2006], '90.1-2007': [2007, 2009],
        '90.1-2010': [2010, 2012], '90.1-2013': [2013, 2016],
        'DOE Ref 1980-2004': [1980, 2003], 'DOE Ref Pre-1980': [0, 1979]}
    # Set the expected EnergyPlus building vintage year that will correspond
    # to a 'new' (as opposed to 'retrofit') building structure type in Scout
    expected_EPlus_new_vintage = '90.1-2013'
    # Initialize a variable meant to translate the summed square footages of
    # of multiple 'retrofit' building vintages into weights that sum to 1; also
    # initialize a variable used to check that these weights indeed sum to 1
    total_retro_sf, retro_weight_sum = (0 for n in range(2))

    # Check for expected EnergyPlus vintage names; if there are unexpected
    # vintage names, raise an error
    if sorted(EPlus_vintages) == sorted(expected_EPlus_vintage_yr_bins.keys()):
        # Initialize a dictionary with the EnergyPlus vintages as keys and
        # associated square footage values starting at zero
        eplus_vintage_weights = dict.fromkeys(EPlus_vintages, 0)

        # Loop through the EnergyPlus vintages and assign associated weights
        # by mapping to CBECS square footage data
        for k in eplus_vintage_weights.keys():
            # If looping through the EnergyPlus vintage associated with the
            # 'new' Scout structure type, set vintage weight to 1 (only one
            # vintage category will be associated with this structure type)
            if k == expected_EPlus_new_vintage:
                eplus_vintage_weights[k] = 1
            # Otherwise, set EnergyPlus vintage weight initially to the
            # square footage that corresponds to that vintage in CBECS
            else:
                # Loop through all CBECS vintage bins
                for k2 in vintage_sf.keys():
                    # Find the limits of the CBECS vintage bin
                    cbecs_match = re.search(
                        '(\D*)(\d*)(\s*)(\D*)(\s*)(\d*)', k2)
                    cbecs_t1 = cbecs_match.group(2)
                    cbecs_t2 = cbecs_match.group(6)
                    # Handle a 'Before Year X' case in CBECS (e.g., 'Before
                    # 1920'),  setting the lower year limit to zero
                    if cbecs_t2 == '':
                        cbecs_t2 = 0
                    # Determine a single average year that represents the
                    # current CBECS vintage bin
                    cbecs_yr = (int(cbecs_t1) + int(cbecs_t2)) / 2
                    # If the CBECS bin year falls within the year limits of the
                    # current EnergyPlus vintage bin, add the associated
                    # CBECS sq.ft. data to the EnergyPlus vintage weight value
                    if cbecs_yr >= expected_EPlus_vintage_yr_bins[k][0] and \
                       cbecs_yr < expected_EPlus_vintage_yr_bins[k][1]:
                        eplus_vintage_weights[k] += vintage_sf[k2]
                        total_retro_sf += vintage_sf[k2]

        # Run through all EnergyPlus vintage weights, normalizing the square
        # footage-based weights for each 'retrofit' vintage to the total square
        # footage across all 'retrofit' vintage categories
        for k in eplus_vintage_weights.keys():
            # If running through the 'new' EnergyPlus vintage bin, register
            # the value of its weight (should be 1)
            if k == expected_EPlus_new_vintage:
                new_weight_sum = eplus_vintage_weights[k]
            # If running through a 'retrofit' EnergyPlus vintage bin,
            # normalize the square footage for that vintage by total
            # square footages across 'retrofit' vintages to arrive at the
            # final weight for that EnergyPlus vintage
            else:
                eplus_vintage_weights[k] /= total_retro_sf
                retro_weight_sum += eplus_vintage_weights[k]

        # Check that the 'new' EnergyPlus vintage weight equals 1 and that
        # all 'retrofit' EnergyPlus vintage weights sum to 1
        if new_weight_sum != 1:
            raise ValueError('Incorrect new vintage weight total!')
        elif retro_weight_sum != 1:
            raise ValueError('Incorrect retrofit vintage weight total!')

    else:
        raise KeyError((
            'Unexpected EPlus vintage(s)! '
            'Adjust EPlus vintage assumptions in find_vintage_weights'))

    # Return the weights needed to map each EnergyPlus vintage category to the
    # 'new' and 'retrofit' structure types defined in Scout
    return eplus_vintage_weights


def convert_to_array(EPlus_perf_sh):
    """ Convert a sheet from an XLSX file to a structured array """

    # Set the XLSX sheet headers
    headers = [str(cell.value) for cell in EPlus_perf_sh.row(0)]
    # Initialize list to be converted to structured array
    arr = []

    # Loop through all the rows in the Excel file and append to the
    # list to be converted to the structured array
    for r in range(EPlus_perf_sh.nrows)[1:]:
        arr.append([cell.value for cell in EPlus_perf_sh.row(r)])

    # Convert the list to the structured array, using column headers
    # as the variable names
    EPlus_perf_array = numpy.rec.fromrecords(arr, names=headers)

    # Return the resultant structured array
    return EPlus_perf_array


def main():

    # Import CBECS XLSX
    CBECS = xlrd.open_workbook(CBECS_in)
    CBECS_sh = CBECS.sheet_by_index(0)
    # Pull out building vintage square footage data
    vintage_sf = CBECS_vintage_sf(CBECS_sh)

    # Import EnergyPlus measure performance XLSX
    EPlus_perf = xlrd.open_workbook(EPlus_perf_in)
    EPlus_perf_sh = EPlus_perf.sheet_by_index(2)
    # Determine appropriate weights for mapping EnergyPlus vintages to the
    # 'new' and 'retrofit' building structure types of Scout
    EPlus_vintages = numpy.unique([EPlus_perf_sh.cell(x, 2).value for
                                  x in range(1, EPlus_perf_sh.nrows)])
    EPlus_vintage_weights = find_vintage_weights(vintage_sf, EPlus_vintages)

    # Convert Excel sheet data into structured array
    EPlus_perf_array = convert_to_array(EPlus_perf_sh)


if __name__ == "__main__":
    main()