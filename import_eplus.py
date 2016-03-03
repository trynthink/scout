#!/usr/bin/env python3
import xlrd
import numpy
import re
import itertools
import json
from os import listdir
from os.path import isfile, join
import copy
import sys

# Define input file containing valid baseline microsegment information
# (to check against in developing key chains for a measure
# performance dictionary that will store EnergyPlus-generated data)
mseg_in = "microsegments_out_eplus_sample.json"
# Define measures input file
measures_in = "measures_eplus_sample.json"
# Define CBECS square footage file
CBECS_in = "b34.xlsx"
# Set up a series of dictionaries used to map EnergyPlus climate zone,
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
    'food service': ['Supermarket'],
    'health care': ['Hospital'],
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
    'warehouse': ['Warehouse'],
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
    'ventilation': ['Fan Electricity'],
    'cooking': [
        'Interior Equipment Gas',
        'Interior Equipment Other Fuel'],
    'lighting': ['Interior Lighting Electricity'],
    'refrigeration': ['Refrigeration Electricity'],
    'PCs': ['Interior Equipment Electricity'],
    'non-PC office equipment': ['Interior Equipment Electricity'],
    'MELs': ['Interior Equipment Electricity']}

# Vintage (year range corresponding to each shown in key value lists)
structure_type = {
    "new": '90.1-2013',
    "retrofit": {
        '90.1-2004': [2004, 2006],
        '90.1-2007': [2007, 2009],
        '90.1-2010': [2010, 2012],
        'DOE Ref 1980-2004': [1980, 2003],
        'DOE Ref Pre-1980': [0, 1979]}}


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


def find_vintage_weights(vintage_sf, EPlus_vintages, structure_type):
    """ Use CBECS building vintage square footage data to derive weighting
    factors that will map the EnergyPlus building vintages to the 'new'
    and 'retrofit' building structure types of Scout """

    # Set the expected names of the EnergyPlus building vintages and the
    # low and high year limits of each building vintage category
    expected_EPlus_vintage_yr_bins = [structure_type['new']] + \
        list(structure_type['retrofit'].keys())
    # Initialize a variable meant to translate the summed square footages of
    # of multiple 'retrofit' building vintages into weights that sum to 1; also
    # initialize a variable used to check that these weights indeed sum to 1
    total_retro_sf, retro_weight_sum = (0 for n in range(2))

    # Check for expected EnergyPlus vintage names; if there are unexpected
    # vintage names, raise an error
    if sorted(EPlus_vintages) == sorted(expected_EPlus_vintage_yr_bins):
        # Initialize a dictionary with the EnergyPlus vintages as keys and
        # associated square footage values starting at zero
        eplus_vintage_weights = dict.fromkeys(EPlus_vintages, 0)

        # Loop through the EnergyPlus vintages and assign associated weights
        # by mapping to CBECS square footage data
        for k in eplus_vintage_weights.keys():
            # If looping through the EnergyPlus vintage associated with the
            # 'new' Scout structure type, set vintage weight to 1 (only one
            # vintage category will be associated with this structure type)
            if k == structure_type['new']:
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
                    if cbecs_yr >= structure_type['retrofit'][k][0] and \
                       cbecs_yr < structure_type['retrofit'][k][1]:
                        eplus_vintage_weights[k] += vintage_sf[k2]
                        total_retro_sf += vintage_sf[k2]

        # Run through all EnergyPlus vintage weights, normalizing the square
        # footage-based weights for each 'retrofit' vintage to the total square
        # footage across all 'retrofit' vintage categories
        for k in eplus_vintage_weights.keys():
            # If running through the 'new' EnergyPlus vintage bin, register
            # the value of its weight (should be 1)
            if k == structure_type['new']:
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

    # Remove any rows in array that measure does not apply to
    EPlus_perf_array = EPlus_perf_array[numpy.where(
        EPlus_perf_array['Status'] != 'Measure Not Applicable')].copy()

    # Return the resultant structured array
    return EPlus_perf_array


def create_perf_dict(measure, mseg_in):
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
    tech_type_primary = measure["technology_type"]["primary"]
    tech_type_secondary = measure["technology_type"]["secondary"]
    tech_primary = measure["technology"]["primary"]
    tech_secondary = measure["technology"]["secondary"]
    # Create primary dict structure from baseline market properties
    perf_dict_empty["primary"] = create_dict(
        czone_list, bldg_list, structure_type_list, fuel_list_primary,
        enduse_list_primary, tech_type_primary, tech_primary, mseg_in)

    # Create secondary dict structure from baseline market properties
    # (if needed)
    if all([x is not None for x in [fuel_list_secondary, enduse_list_secondary,
                                    tech_type_secondary, tech_secondary]]):
        perf_dict_empty["secondary"] = create_dict(
            czone_list, bldg_list, structure_type_list, fuel_list_secondary,
            enduse_list_secondary, tech_type_secondary, tech_secondary,
            mseg_in)

    # Return resultant dict, to be filled with EnergyPlus performance data
    return perf_dict_empty


def create_dict(
        czone, bldg, structure_type, fuel, enduse, tech_type, tech, msegs):
    """ Create a nested dictionary with a structure that is defined by a
    measure's applicable baseline market, with end leaf node values set
    to zero """
    # Initialize output dictionary
    output_dict = {}
    # Establish levels of the dictionary key hierarchy from measure's
    # applicable baseline market information
    keylevels = [czone, bldg, fuel, enduse, structure_type]
    # Find all possible dictionary key chains from the above key level info.
    dict_keys = list(itertools.product(*keylevels))

    # Use an input dictionary with valid baseline microsegment information to
    # check that each of the microsegment key chains generated above is valid
    # for the current measure; if not, remove each invalid key chain from
    # further operations

    # Initialize a list of valid baseline microsegment key chains for the
    # measure
    dict_keys_fin = []
    # Loop through the initial set of candidate key chains generated above
    for kc in dict_keys:
        # Copy the input dictionary containing valid key chains
        dict_check = copy.deepcopy(msegs)
        # Loop through all keys in the candidate key chain and move down
        # successive levels of the input dict until either the
        # end of the key chain is reached or a key is not found in the
        # list of valid keys for the current input dict level. In the
        # former case, the resultant dict will point to all technologies
        # associated with the current key chain (e.g., ASHP, LFL, etc.)
        # If none of these technologies are found in the list of technologies
        # covered by the measure, the key chain is deemed invalid
        for ind, key in enumerate(kc):
            # If key is found in the list of valid keys for the current
            # input microsegment dict level, move on to next level in the dict;
            # otherwise, break the current loop
            if key in dict_check.keys():
                dict_check = dict_check[key]
                # In the case of heating or cooling end uses, an additional
                # 'technology type' key must be accounted for ('supply' or
                # 'demand')
                if key in ['heating', 'cooling']:
                    dict_check = dict_check[tech_type]
            else:
                break

        # If any of the technology types listed in the measure definition
        # are found in the keys of the dictionary yielded by the above loop,
        # add the key chain to the list that is used to define the final
        # nested dictionary output (e.g., the key chain is valid)
        if any([x in tech for x in dict_check.keys()]):
            dict_keys_fin.append(kc)

    # Loop through each of the valid key chains and create an
    # associated path in the dictionary, terminating with a zero value
    # to be updated in a subsequent routine with EnergyPlus output data
    for kc in dict_keys_fin:
        current_level = output_dict
        for ind, elem in enumerate(kc):
            if elem not in current_level and (ind + 1) != len(kc):
                current_level[elem] = {}
            elif elem not in current_level and (ind + 1) == len(kc):
                current_level[elem] = 0
            current_level = current_level[elem]

    # Return nested dictionary
    return output_dict


def fill_perf_dict(perf_dict, EPlus_perf_array, EPlus_bldg_type_weight,
                   EPlus_bldg_vintage_weights):
    """ Use data from an EnergyPlus output file and building type/vintage
    weighting data to fill a dictionary of final measure performance
    information """

    # Set the header of the EnergyPlus input array (used when reducing columns
    # of the array to the specific performance categories being updated below)
    EPlus_header = list(EPlus_perf_array.dtype.names)

    # Loop through zeroed out measure performance dictionary input and update
    # the values with data from the EnergyPlus input array
    for key, item in perf_dict.items():
        # If current dict item is itself a dict, reduce the EnergyPlus array
        # based on the current dict key and proceed further down the dict
        # levels
        if isinstance(item, dict):
            # Microsegment type level (no update to EnergyPlus array required)
            if key in ['primary', 'secondary']:
                updated_perf_array = EPlus_perf_array
            # Climate zone level
            elif key in czone.keys():
                # Reduce EnergyPlus array to only rows with climate zone
                # currently being updated in the performance dictionary
                updated_perf_array = EPlus_perf_array[numpy.where(
                    EPlus_perf_array[
                        'Climate Zone'] == czone[key])].copy()
                if len(updated_perf_array) == 0:
                    raise ValueError('EPlus climate zone name not found!')
            # Building type level
            elif key in bldgtype.keys():
                # Reduce EnergyPlus array to only rows with building type
                # currently being updated in the performance dictionary
                updated_perf_array = EPlus_perf_array[numpy.in1d(
                    EPlus_perf_array[
                        'Building Type'], bldgtype[key])].copy()
                if len(updated_perf_array) == 0:
                    raise ValueError('EPlus building type name not found!')
            # Fuel type level
            elif key in fuel.keys():
                # Reduce EnergyPlus array to only columns with fuel type
                # currently being updated in the performance dictionary.
                colnames = EPlus_header[0:3]
                colnames.extend([
                    x for x in EPlus_header if fuel[key] in x])
                if len(colnames) == 3:
                    raise ValueError('EPlus fuel type name not found!')
                updated_perf_array = EPlus_perf_array[colnames].copy()
            # End use level
            elif key in enduse.keys():
                # Reduce EnergyPlus array to only columns with end use
                # currently being updated in the performance dictionary.
                colnames = EPlus_header[0:3]
                colnames.extend([
                    x for x in EPlus_header if x in enduse[key]])
                if len(colnames) == 3:
                    raise ValueError('EPlus end use name not found!')
                updated_perf_array = EPlus_perf_array[colnames].copy()
            else:
                raise KeyError('Invalid measure performance dictionary key!')

            # Given updated EnergyPlus array, proceed further down the
            # dict level hierarchy
            fill_perf_dict(item, updated_perf_array,
                           EPlus_bldg_type_weight, EPlus_bldg_vintage_weights)
        else:
            # Reduce EnergyPlus array to only rows with structure type
            # currently being updated in the performance dictionary
            # ('new' or 'retrofit')
            if key in structure_type.keys():
                # A 'new' structure type will match only one of the EnergyPlus
                # building vintage names
                if key == "new":
                    updated_perf_array = EPlus_perf_array[numpy.where(
                        EPlus_perf_array['Template'] ==
                        structure_type['new'])].copy()
                # A 'retrofit' structure type will match multiple EnergyPlus
                # building vintage names
                else:
                    updated_perf_array = EPlus_perf_array[numpy.in1d(
                        EPlus_perf_array['Template'],
                        list(structure_type['retrofit'].keys()))].copy()
                if len(updated_perf_array) == 0 or \
                   (key == "new" and
                    len(numpy.unique(updated_perf_array['Template'])) != 1 or
                    key == "retrofit" and
                    len(numpy.unique(updated_perf_array['Template'])) !=
                        len(structure_type["retrofit"].keys())):
                    raise ValueError(
                        'EPlus vintage name not found in data file!')
            else:
                raise KeyError('Invalid measure performance dictionary key!')

            # Initialize the final relative savings value for the current
            # measure performance dictionary branch as 0
            end_key_val = 0

            # Update building type weight to account for cases where
            # multiple EPlus building types map to one Scout building type
            # (for now, weight each EPlus type evenly)
            EPlus_bldg_type_weight = 1 / \
                len(numpy.unique(updated_perf_array['Building Type']))

            # Weight and combine the relative savings values left in the
            # EnergyPlus array to arrive at the final measure relative
            # savings value for the current dictionary branch
            for r in updated_perf_array:
                for n in EPlus_header:
                    if r[n].dtype.char != 'S' and r[n].dtype.char != 'U':
                        r[n] = r[n] * EPlus_bldg_type_weight * \
                            EPlus_bldg_vintage_weights[
                            r['Template'].copy()]
                        end_key_val += r[n]

            # Update the current dictionary branch value to the final
            # relative savings value derived above
            perf_dict[key] = end_key_val

    # Return the filled in measure performance dict
    return perf_dict


def main(argv):

    # Import CBECS XLSX
    CBECS = xlrd.open_workbook(CBECS_in)
    CBECS_sh = CBECS.sheet_by_index(0)
    # Pull out building vintage square footage data
    vintage_sf = CBECS_vintage_sf(CBECS_sh)

    # Set local directory for EnergyPlus measure performance files
    eplus_dir = argv
    # Set EnergyPlus data file name list, given local directory
    EPlus_perf_files = [
        f for f in listdir(eplus_dir) if isfile(join(eplus_dir, f))]

    # Import EnergyPlus measure performance XLSX
    EPlus_file = xlrd.open_workbook(eplus_dir + '/' + EPlus_perf_files[0])
    EPlus_file_sh = EPlus_file.sheet_by_index(2)
    # Determine appropriate weights for mapping EnergyPlus vintages to the
    # 'new' and 'retrofit' building structure types of Scout
    EPlus_vintages = numpy.unique([EPlus_file_sh.cell(x, 2).value for
                                  x in range(1, EPlus_file_sh.nrows)])
    EPlus_vintage_weights = find_vintage_weights(
        vintage_sf, EPlus_vintages, structure_type)
    # Initialize weight for mapping each EnergyPlus building types to a Scout
    # building type
    EPlus_bldg_type_weight = 1

    # Import baseline microsegments JSON
    with open(mseg_in, 'r') as msi:
        msegs = json.load(msi)

    # Import measures JSON
    with open(measures_in, 'r') as mjs:
        measures = json.load(mjs)

    # Loop through all measures and updated with EPlus performance data
    # (where applicable)
    for m in measures:
        if 'EnergyPlus file' in m['energy_efficiency'].keys():
            # Determine the appropriate EnergyPlus input XLSX file name
            EPlus_perf_in = [x for x in EPlus_perf_files if
                             m['energy_efficiency']['EnergyPlus file'] in x]
            # Import EnergyPlus input XLSX and translate to structured array
            # for future operations
            if len(EPlus_perf_in) == 1:
                # Create a measure performance dictionary, zeroed out, to
                # be updated with information from EnergyPlus outputs
                perf_dict_empty = create_perf_dict(m, msegs)
                # Import EnergyPlus measure performance XLSX
                EPlus_perf = xlrd.open_workbook(
                    eplus_dir + '/' + EPlus_perf_in[0])
                EPlus_perf_sh = EPlus_perf.sheet_by_index(2)
                # Convert Excel sheet data into numpy array
                EPlus_perf_array = convert_to_array(EPlus_perf_sh)

                # Update measure performance based on EnergyPlus data
                # (* Note: only update efficiency information for
                # secondary microsegments if applicable)
                if perf_dict_empty['secondary'] is not None:
                    m['energy_efficiency'] = fill_perf_dict(
                        perf_dict_empty, EPlus_perf_array,
                        EPlus_bldg_type_weight, EPlus_vintage_weights)
                else:
                    m['energy_efficiency'] = fill_perf_dict(
                        perf_dict_empty['primary'], EPlus_perf_array,
                        EPlus_bldg_type_weight, EPlus_vintage_weights)
                # Set the energy efficiency source for the measure to
                # EnergyPlus and set to highest quality rating
                m['energy_efficiency_source'] = 'EnergyPlus/OpenStudio'
                m['energy_efficiency_source_quality'] = 5
            elif len(EPlus_perf_in) > 1:
                raise ValueError('> 1 applicable EPlus file for measure!')
            else:
                raise ValueError(
                    'Failure to match measure name to EPlus files!')

    # Write the updated dict of measure performance data over the existing
    # measures JSON file
    with open(measures_in, "w") as jso:
        json.dump(measures, jso, indent=4)

if __name__ == "__main__":
    main(sys.argv[1])
