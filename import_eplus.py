#!/usr/bin/env python3
import xlrd
import numpy
import re
import itertools
import json
from os import listdir
from os.path import isfile, join

# Define measures input file
measures_in = "measures.json"
# Define CBECS square footage file
CBECS_in = "b34.xlsx"
# Define Energy Plus measure performance output file directory
# eplus_dir = '/Users/jtlangevin/Desktop/scout'
# # Define Energy Plus data file name list
# EPlus_perf_files = [
#     f for f in listdir(eplus_dir) if isfile(join(eplus_dir, f))]
EPlus_perf_files = []
# Set the expected Energy Plus building vintage year that will correspond
# to a 'new' (as opposed to 'retrofit') building structure type in Scout
expected_EPlus_new = '90.1-2013'

# Set up a series of dictionaries used to map Energy Plus climate zone,
# building type, fuel type, and end use names to the names for these
# variables in Scout

# Climate zone
czone = {
    "sub arctic": "BA-SubArctic",
    "very cold": "BA-VeryCold",
    "cold": "BA-Cold",
    "marine": "BA-Marine",
    "mixed humid": "BA-MixedHumid",
    "mixed dry": "BA-MixedDry",
    "hot dry": "BA-HotDry",
    "hot humid": "BA-HotHumid"}

# Building type
bldgtype = {
    'assembly': [
        'PrimarySchool',
        'RetailStandalone',
        'RetailStripmall',
        'SecondarySchool',
        'SmallOffice'],
    'education': [
        'PrimarySchool',
        'SecondarySchool'],
    'food sales': [
        'FullServiceRestaurant',
        'QuickServiceRestaurant'],
    'food service': 'Supermarket',
    'health care': 'Hospital',
    'mercantile/service': [
        'RetailStandalone',
        'RetailStripmall'],
    'lodging': [
        'LargeHotel',
        'SmallHotel'],
    'multi family home': [
        'HighRiseApartment',
        'MidriseApartment'],
    'large office': [
        'LargeOffice',
        'MediumOffice'],
    'small office': [
        'MediumOffice',
        'SmallOffice'],
    'warehouse': 'Warehouse',
    'other': [
        'LargeOffice',
        'SmallHotel',
        'Warehouse']}

# Fuel types
fuel = {
    'electricity (grid)': 'Electricity',
    'natural gas': 'Gas',
    'other fuel': 'Other Fuel'}

# End uses
enduse = {
    'heating': [
        'Heating Electricity',
        'Heat Recovery Electricity',
        'Pump Electricity',
        'Heating Gas'],
    'cooling': [
        'Cooling Electricity',
        'Humidification Electricity',
        'Heat Recovery Electricity',
        'Heat Rejection Electricity',
        'Pump Electricity'],
    'water heating': [
        'Service Water Heating Electricity',
        'Service Water Heating Gas',
        'Service Water Heating Other Fuel'],
    'ventilation': 'Fan Electricity',
    'cooking': [
        'Interior Equipment Gas',
        'Interior Equipment Other Fuel'],
    'lighting': 'Interior Lighting Electricity',
    'refrigeration': 'Refrigeration Electricity',
    'PCs': 'Interior Equipment Electricity',
    'non-PC office equipment': 'Interior Equipment Electricity',
    'MELs': 'Interior Equipment Electricity'}


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


def find_vintage_weights(vintage_sf, EPlus_vintages, expected_EPlus_new):
    """ Use CBECS building vintage square footage data to derive weighting
    factors that will map the EnergyPlus building vintages to the 'new'
    and 'retrofit' building structure types of Scout """

    # Set the expected names of the EnergyPlus building vintages and the
    # low and high year limits of each building vintage category
    expected_EPlus_vintage_yr_bins = {
        '90.1-2004': [2004, 2006], '90.1-2007': [2007, 2009],
        '90.1-2010': [2010, 2012], '90.1-2013': [2013, 2016],
        'DOE Ref 1980-2004': [1980, 2003], 'DOE Ref Pre-1980': [0, 1979]}
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
            if k == expected_EPlus_new:
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
            if k == expected_EPlus_new:
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


def create_perf_dict(measure):
    """ Given a measure's applicable climate zone, building type,
    structure type, fuel type, and end use, create a dict of zeros
    with a hierarchy that is defined by these measure properties """
    # Initialize performance dict
    perf_dict_empty = {"primary": None, "secondary": None}
    # Establish applicable baseline market properties
    czone_list = measure["climate_zone"]
    bldg_list = measure["bldg_type"]
    structure_type_list = measure["structure_type"]
    fuel_list_primary = measure["fuel_type"]["primary"]
    fuel_list_secondary = measure["fuel_type"]["secondary"]
    enduse_list_primary = measure["end_use"]["primary"]
    enduse_list_secondary = measure["end_use"]["secondary"]
    # Create primary dict structure from baseline market properties
    perf_dict_empty["primary"] = create_dict(
        czone_list, bldg_list, structure_type_list,
        fuel_list_primary, enduse_list_primary)

    # Create secondary dict structure from baseline market properties
    # (if needed)
    if len(fuel_list_secondary) > 0 and len(enduse_list_secondary) > 0:
        perf_dict_empty["secondary"] = create_dict(
            czone_list, bldg_list, structure_type_list,
            fuel_list_secondary, enduse_list_secondary)

    # Return resultant dict, to be filled with Energy Plus performance data
    return perf_dict_empty


def create_dict(czone, bldg, structure_type, fuel, enduse):
    """ Create a nested dictionary with a structure that is defined by a
    measure's applicable baseline market, with end leaf node values set
    to zero """
    # Initialize output dictionary
    output_dict = {}
    # Establish levels of the dictionary key hierarchy from measure's
    # applicable baseline market information
    key_levels = [czone, bldg, fuel, enduse, structure_type]
    # Find all possible dictionary key chains from the above key level info.
    dict_keys = list(itertools.product(*key_levels))

    # Loop through each of the possible key chains and create an
    # associated path in the dictionary, terminating with a zero value
    # to be updated in a subsequent routine with Energy Plus output data
    for kc in dict_keys:
        current_level = output_dict
        for ind, elem in enumerate(kc):
            if elem not in current_level and (ind + 1) != len(kc):
                current_level[elem] = {}
            elif elem not in current_level and (ind + 1) == len(kc):
                current_level[elem] = 0
            current_level = current_level[elem]

    # Return nested dictionary
    return output_dict


def main():

    # Import CBECS XLSX
    CBECS = xlrd.open_workbook(CBECS_in)
    CBECS_sh = CBECS.sheet_by_index(0)
    # Pull out building vintage square footage data
    vintage_sf = CBECS_vintage_sf(CBECS_sh)

    # Import EnergyPlus measure performance XLSX
    EPlus_file = xlrd.open_workbook(EPlus_perf_files[0])
    EPlus_file_sh = EPlus_file.sheet_by_index(2)
    # Determine appropriate weights for mapping EnergyPlus vintages to the
    # 'new' and 'retrofit' building structure types of Scout
    EPlus_vintages = numpy.unique([EPlus_file_sh.cell(x, 2).value for
                                  x in range(1, EPlus_file_sh.nrows)])
    EPlus_vintage_weights = find_vintage_weights(
        vintage_sf, EPlus_vintages, expected_EPlus_new)

    # Import measures JSON
    with open(measures_in, 'r') as mjs:
        measures = json.load(mjs)

    # Determine subset of measures where an Energy Plus simulation output file
    # is required to determine the measure performance input
    measures_eplus = [
        m for m in measures if m['energy efficiency'] == 'Energy Plus file']

    # Loop through all measures in need of performance data from Energy Plus
    for m in measures_eplus:
        # Determine the appropriate Energy Plus input XLSX file name
        EPlus_perf_in = [x for x in EPlus_perf_files if
                         m['energy_efficiency']['Energy Plus file'] in x]
        # Import Energy Plus input XLSX and translate to structured array for
        # future operations
        if len(EPlus_perf_in) == 1:
            # Create a measure performance dictionary, zeroed out, to
            # be updated with information from Energy Plus outputs
            perf_dict_empty = create_perf_dict(m)
            # Import EnergyPlus measure performance XLSX
            EPlus_perf = xlrd.open_workbook(EPlus_perf_in)
            EPlus_perf_sh = EPlus_perf.sheet_by_index(2)
            # Convert Excel sheet data into numpy array
            EPlus_perf_array = convert_to_array(EPlus_perf_sh)
        elif len(EPlus_perf_in) > 1:
            raise ValueError('> 1 applicable EPlus file for measure!')
        else:
            raise ValueError('Failure to match measure name to EPlus files!')

if __name__ == "__main__":
    main()