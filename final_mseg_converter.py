#!/usr/bin/env python3

"""Common input data census division to climate zone conversion script.

This script takes a complete input JSON database in which all of the
data are specified on a census division basis and converts those data
to a climate zone basis. The conversion procedure in this script can
modify any complete (i.e., both residential and commercial data added)
or partially complete JSON database, so long as the structure of each
microsegment is identical for all census divisions, but is default
configured to look for files that have complete residential and
commercial data.

The approach employed here relies on the user to run the input data
processing scripts in the correct order prior to running this script.
This approach was taken instead of creating a master script that
calls those other scripts itself to simplify debugging and modification
of the individual data import scripts and also to reduce the need to
re-run potentially slow code when it or another script encounters an
error when the master script calls them.

To help ensure that the scripts are run in the correct order, each
script checks for the correct input file and produces an instructive
error message if the file is missing.
"""

import copy
import numpy as np
import json
import mseg
import com_mseg as cm


class UsefulVars(object):
    """Class for useful variables to make them available to external scripts.

    This class is setup so that these variables are available, if
    necessary, to external functions for testing or other purposes.
    While this script can convert energy and stock data or cost,
    performance, and lifetime data, it cannot handle both in parallel.
    After creating an instance of the class, the appropriate method
    can be called to populate the instance with the correct file
    names for the input and output JSON databases and the census
    division to climate zone conversion tables.

    It is conceivable that instead of having separate methods to
    set the values for the required variables for each case, they
    could be initialized for one case and modified using regular
    expressions, but the approach below is simple, if ham-fisted.

    The different census division to climate zone conversion matrices
    are required because the correct math to combine cost, performance,
    and lifetime data is different than the math for energy and stock
    data. The '_Rev_' version of the conversion matrix has weighting
    factors scaled such that the columns (climate zones) sum to 1,
    which is required to calculate the weighted average of technology
    cost, performance, lifetime, etc. across the census divisions.
    Conversely, the energy, stock, and square footage conversion matrix
    is structured such that the census divisions sum to 1, since those
    data are originally recorded by census division, and all of the
    energy use reported must be accounted for when switching to
    climate zones.

    Attributes: (if a method is called)
        res_climate_convert (str): File name for the residential buildings
            census division to climate zone conversion data appropriate
            for the particular data to be converted.
        com_climate_convert (str): File name for the commercial buildings
            census division to climate zone conversion data appropriate
            for the particular data to be converted.
        json_in (str): File name for the expected input JSON database.
        json_out (str): File name for the output JSON database.
    """

    def configure_for_energy_square_footage_stock_data(self):
        self.res_climate_convert = 'Res_Cdiv_Czone_ConvertTable_Final.txt'
        self.com_climate_convert = 'Com_Cdiv_Czone_ConvertTable_Final.txt'
        self.json_in = 'mseg_res_com_cdiv.json'
        self.json_out = 'mseg_res_com_cz.json'

    def configure_for_cost_performance_lifetime_data(self):
        self.res_climate_convert = 'Res_Cdiv_Czone_ConvertTable_Rev_Final.txt'
        self.com_climate_convert = 'Com_Cdiv_Czone_ConvertTable_Rev_Final.txt'
        self.json_in = 'costperflife_res_com_cdiv.json'
        self.json_out = 'costperflife_res_com_cz.json'


def merge_sum(base_dict, add_dict, cd, cz, cd_dict, cd_list,
              res_convert_array, com_convert_array, cd_to_cz_factor=0):
    """Calculate values to restructure census division data to climate zones.

    Two dicts with identical structure, 'base_dict' and 'add_dict' are
    passed to this function and manipulated to effect conversion of the
    data from a census division (specified by 'cd') to a climate zone
    (specified by 'cz') basis.

    This function operates recursively, traversing the structure of
    the input dicts until a list of years is reached. At that point,
    if the census division specified corresponds to the first census
    division in the original data (the order is obtained from
    'cd_list'), the entries in 'base_dict' are overwritten by the same
    data multiplied by the appropriate conversion factor. If the census
    division is not the first to appear in the original data,
    'base_dict' has already been modified, and data from subsequent
    census divisions should be added to 'base_dict', thus 'add_dict' is
    modified to the current climate zone using the appropriate
    conversion factor and added to 'base_dict'.

    This approach to converting the data to a climate zone basis works
    because this function is called from within nested for loops that
    cover all of the census divisions for each climate zone.
    Consequently, the data from each of the census divisions converted
    to their respective contributions to a single climate zone can be
    added together to obtain the data in the desired final form.

    Args:
        base_dict (dict): A portion of the input JSON database
            corresponding to the current census division, modified in
            place to convert the data to a climate zone basis.
        add_dict (dict): A portion of the input JSON database
            corresponding to the current census division, copied from
            the original input data each time this function is called
            by the clim_converter function. This portion of the data
            should be structurally identical to 'base_dict', and
            (generally) corresponds to the data that should be updated
            and then added to 'base_dict'.
        cd (int): The census division (1-9) currently being processed.
            Used as an array row index, so the actual values begin
            with 0, not 1.
        cz (int): The climate zone to which the census division data
            are being added. Used as an array column index where the
            first (0th) column is not relevant, thus it begins at 1.
        cd_dict (dict): A dict for translating between census division
            descriptive strings and their corresponding numeric codes.
        cd_list (list): A list of the census divisions that are in the
            input data (the top level keys from the JSON structure),
            in the order in which they appear.
        res_convert_array (numpy.ndarray): Coefficients for converting
            from census divisions to climate zones for residential buildings.
        com_convert_array (numpy.ndarray): Coefficients for converting
            from census divisions to climate zones for commercial buildings.
        cd_to_cz_factor (float): The numeric conversion factor to
            calculate the contribution from the current census division
            'cd' to the current climate zone 'cz'.

    Returns:
        A dict with the same form as base_dict and add_dict, with the
        values for the particular census division specified in 'cd'
        converted to the climate zone 'cz'.
    """

    # Extract lists of strings corresponding to the residential and
    # commercial building types used to process these inputs
    res_bldg_types = list(mseg.bldgtypedict.keys())
    com_bldg_types = list(cm.CommercialTranslationDicts().bldgtypedict.keys())

    for (k, i), (k2, i2) in zip(sorted(base_dict.items()),
                                sorted(add_dict.items())):
        # Compare the top level/parent keys of the section of the dict
        # currently being parsed to ensure that both the base_dict
        # (census division basis) and add_dict (climate zone basis)
        # are proceeding with the same structure
        if k == k2:
            # Identify appropriate census division to climate zone
            # conversion weighting factor as a function of building type;
            # k and k2 correspond to the current top level/parent key,
            # thus k and k2 are equal to a building type immediately
            # prior to traversing the entire child tree for that
            # building type, for which the conversion number
            # cd_to_cz_factor will be the same
            if k in res_bldg_types or k in com_bldg_types:
                if k in res_bldg_types:
                    cd_to_cz_factor = res_convert_array[cd][cz]
                elif k in com_bldg_types:
                    cd_to_cz_factor = com_convert_array[cd][cz]

            # Recursively loop through both dicts
            if isinstance(i, dict):
                merge_sum(i, i2, cd, cz, cd_dict, cd_list, res_convert_array,
                          com_convert_array, cd_to_cz_factor)
            elif type(base_dict[k]) is not str:
                # Special handling of first dict (no addition of the
                # second dict, only conversion of the first dict with
                # the appropriate factor)
                if (cd == (cd_dict[cd_list[0]] - 1)):
                    # In the special case of consumer choice/time
                    # preference premium data, the data are reported
                    # as a list and must be reprocessed using a list
                    # comprehension (or comparable looping approach)
                    if isinstance(base_dict[k], list):
                        base_dict[k] = [z*cd_to_cz_factor for z
                                        in base_dict[k]]
                    else:
                        base_dict[k] = base_dict[k]*cd_to_cz_factor
                else:
                    if isinstance(base_dict[k], list):
                        base_dict[k] = [sum(y) for y
                                        in zip(base_dict[k],
                                        [z*cd_to_cz_factor for z
                                         in add_dict[k2]])]
                    else:
                        base_dict[k] = (base_dict[k] +
                                        add_dict[k2]*cd_to_cz_factor)
        else:
            raise(KeyError('Merge keys do not match!'))

    # Return a single dict representing sum of values of original two dicts
    return base_dict


def clim_converter(input_dict, res_convert_array, com_convert_array):
    """Convert input data dict from a census division to a climate zone basis.

    This function principally serves to prepare the inputs for, and
    then call, a function that performs the calculations to convert
    data in the input_dict database specified for each microsegment
    from a census division to climate zone basis.

    Args:
        input_dict (dict): Data from JSON database, as imported,
            on a census division basis.
        res_convert_array (numpy.ndarray): An array of census
            division to climate zone conversion factors for
            residential building types.
        com_convert_array (numpy.ndarray): Array of census
            division to climate zone conversion factors for
            commercial building types.

    Returns:
        A complete dict with the same structure as input_dict,
        except at the top level, where census division keys
        have been replaced by climate zone keys, and the data
        have been updated to correspond to those climate zones.
    """

    # Create an instance of the CommercialTranslationDicts object from
    # com_mseg, which contains a dict that translates census division
    # strings into the corresponding integer codes
    cd = cm.CommercialTranslationDicts()

    # Obtain list of all climate zone names as strings
    cz_list = res_convert_array.dtype.names[1:]

    # Obtain list of all census divisions in the input data
    cd_list = list(input_dict.keys())

    # Set up empty dict to be updated with the results for each climate
    # zone as the data are converted
    converted_dict = {}

    # Add the values from each climate zone to the converted_dict
    for cz_number, cz_name in enumerate(cz_list):
        # Create a copy of the input dict at the level below a census
        # division or climate zone (the structure below that level
        # should be identical); uses the first census division in
        # cd_list each time
        base_dict = copy.deepcopy(input_dict[cd_list[0]])

        # Loop through all census divisions to add their contributions
        # to each climate zone
        for cd_name in cd_list:
            # Proceed only if the census division name is found in
            # the dict specified in this function, otherwise raise
            # a KeyError
            if cd_name in cd.cdivdict.keys():
                # Obtain the census division number from the dict
                # and subtract 1 to make the number usable as a list
                # index (1st list element is indexed by 0 in Python)
                cd_number = cd.cdivdict[cd_name] - 1

                # Make a copy of the portion of the input dict
                # corresponding to the current census division
                add_dict = copy.deepcopy(input_dict[cd_name])

                # Call the merge_sum function to replace base_dict with
                # updated contents; add 1 to the climate zone number
                # because it will be used as a column index for an
                # array where the first column of data are in the
                # second column (indexed as 1 in Python); this approach
                # overwrites base_dict, which is intentional because it
                # is the master dict that stores the data on a climate
                # zone basis as the contribution from each census
                # division is added to the climate zone by merge_sum
                base_dict = merge_sum(base_dict, add_dict, cd_number,
                                      (cz_number + 1), cd.cdivdict, cd_list,
                                      res_convert_array, com_convert_array)
            else:
                raise(KeyError("Census division name not found in dict keys!"))

        # Once fully updated with the data from all census divisions,
        # write the resulting data to a new variable and update the
        # master dict with the data using the appropriate census
        # division string name as the key
        newadd = base_dict
        converted_dict.update({cz_name: newadd})

    return converted_dict


def main():
    """Import external data files, process data, and produce desired output.

    This function calls the required external data, both the data to be
    converted from a census division to a climate zone basis, as well
    as the applicable conversion factors.

    Because the conversion factors for the energy, stock, and square
    footage data are slightly different than the factors for the cost,
    performance, and lifetime data, when the script is run, this
    function requests user input to determine the appropriate files
    to import.
    """

    # Instantiate object that contains useful variables
    handyvars = UsefulVars()

    # Obtain user input regarding what data are to be processed
    input_var = 0
    while input_var not in ['1', '2']:
        input_var = input(
            "Enter 1 for energy data or 2 for cost, performance, lifetime data: ")
        if input_var not in ['1', '2']:
            print('Please try again. Enter either 1 or 2. Use ctrl-c to exit.')

    # Based on input from the user to indicate what type of data are
    # being processed, assign the object values for its four attributes
    if input_var is '1':
        handyvars.configure_for_energy_square_footage_stock_data()
    elif input_var is '2':
        handyvars.configure_for_cost_performance_lifetime_data()

    # Import the residential census division to climate zone conversion data
    res_cd_cz_conv = np.genfromtxt(handyvars.res_climate_convert, names=True,
                                   delimiter='\t', dtype=None)

    # Import the commercial census division to climate zone conversion data
    com_cd_cz_conv = np.genfromtxt(handyvars.com_climate_convert, names=True,
                                   delimiter='\t', dtype=None)

    # Import microsegments JSON file with and traverse database structure
    with open(handyvars.json_in, 'r') as jsi:
        msjson_cdiv = json.load(jsi)

        # Convert data
        result = clim_converter(msjson_cdiv, res_cd_cz_conv, com_cd_cz_conv)

    # Write the updated dict of data to a new JSON file
    with open(handyvars.json_out, 'w') as jso:
        json.dump(result, jso, indent=2)

if __name__ == '__main__':
    main()
