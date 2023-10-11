#!/usr/bin/env python3

"""Common input data census division to custom region conversion script.

This script takes a complete input JSON database in which all of the
data are specified on a census division basis and converts those data
to a custom region basis. The conversion procedure in this script can
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
import functools as ft
import math
import gzip
import pandas as pd


class UsefulVars(object):
    """Class for useful variables to make them available to external scripts.

    This class is setup so that these variables are available, if
    necessary, to external functions for testing or other purposes.
    While this script can convert energy and stock data or cost,
    performance, and lifetime data, it cannot handle both in parallel.
    After creating an instance of the class, the appropriate method
    can be called to populate the instance with the correct file
    names for the input and output JSON databases and the census
    division to custom region conversion tables.

    It is conceivable that instead of having separate methods to
    set the values for the required variables for each case, they
    could be initialized for one case and modified using regular
    expressions, but the approach below is simple, if ham-fisted.

    The different census division to custom region conversion matrices
    are required because the correct math to combine cost, performance,
    and lifetime data is different than the math for energy and stock
    data. The '_Rev_' version of the conversion matrix has weighting
    factors scaled such that the columns (custom regions) sum to 1,
    which is required to calculate the weighted average of technology
    cost, performance, lifetime, etc. across the census divisions.
    Conversely, the energy, stock, and square footage conversion matrix
    is structured such that the census divisions sum to 1, since those
    data are originally recorded by census division, and all of the
    energy use reported must be accounted for when switching to
    custom regions.

    Currently, three custom region sets are supported: AIA climate regions,
    U.S. Energy Information Administration (EIA) National Energy Modeling
    System (NEMS) Electricity Market Module (EMM) regions, and (for stock/
    energy data only), states.

    Attributes:
        addl_cpl_data (str): File name for database of cost,
            performance, and lifetime data not found in the EIA data,
            principally for envelope components and miscellaneous
            electric loads.
        conv_factors (str): File name for database of unit conversion
            factors (principally costs) for a range of equipment types.
        aeo_metadata (str): File name for the custom AEO metadata JSON.
        geo_break (str): Indicates the intended geographical data breakdown.

    Attributes: (if a method is called)
        res_climate_convert (str): File name for the residential buildings
            census division to custom region conversion data appropriate
            for the particular data to be converted.
        com_climate_convert (str): File name for the commercial buildings
            census division to custom region conversion data appropriate
            for the particular data to be converted.
        json_in (str): File name for the expected input JSON database.
        json_out (str): File name for the output JSON database.
    """

    def __init__(self, geo_break):
        """Initialize class attributes."""
        self.addl_cpl_data = 'cpl_envelope_mels.json'
        self.conv_factors = ('supporting_data/convert_data/'
                             'ecm_cost_convert.json')
        self.aeo_metadata = 'metadata.json'
        self.geo_break = geo_break

    def configure_for_energy_square_footage_stock_data(self):
        """Reconfigure stock and energy data to custom region."""
        # Set input JSON
        self.json_in = 'mseg_res_com_cdiv.json'
        # Find appropriate conversion data for user-specified geo. breakout
        # (1=AIA climate zones, 2=NEMS EMM regions)
        if self.geo_break == '1':
            self.res_climate_convert = (
                'supporting_data/convert_data/geo_map/'
                'Res_Cdiv_Czone_RowSums.txt')
            self.com_climate_convert = (
                'supporting_data/convert_data/geo_map/'
                'Com_Cdiv_Czone_RowSums.txt')
            self.eulp_post = ""
            # Set output JSON
            self.json_out = 'mseg_res_com_cz.json'
        elif self.geo_break == '2':
            self.res_climate_convert = {
                "electricity": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_EMM_Elec_RowSums.txt'),
                "natural gas": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_EMM_NG_RowSums.txt'),
                "distillate": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_EMM_Dist_RowSums.txt'),
                "other fuel": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_EMM_Other_RowSums.txt'),
                # Use electricity splits to apportion no. building/sf data
                "building stock and square footage": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_EMM_Elec_RowSums.txt')}
            self.com_climate_convert = {
                "electricity": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_EMM_Elec_RowSums.txt'),
                "natural gas": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_EMM_NG_RowSums.txt'),
                "distillate": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_EMM_Dist_RowSums.txt'),
                # Use electricity splits to apportion no. building/sf data
                "building stock and square footage": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_EMM_Elec_RowSums.txt')}
            self.eulp_post = (
                    'supporting_data/convert_data/geo_map/'
                    'emm_eulp_shares.csv')
            # Set output JSON
            self.json_out = 'mseg_res_com_emm.json'
        elif self.geo_break == '3':
            self.res_climate_convert = {
                "electricity": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_State_Elec_RowSums.txt'),
                "natural gas": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_State_NG_RowSums.txt'),
                "distillate": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_State_Dist_RowSums.txt'),
                "other fuel": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_State_Other_RowSums.txt'),
                # Use total consumption splits to apportion no. building/sf
                "building stock and square footage": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_State_AllFuels_RowSums.txt')}
            self.com_climate_convert = {
                "electricity": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_State_Elec_RowSums.txt'),
                "natural gas": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_State_NG_RowSums.txt'),
                "distillate": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_State_Dist_RowSums.txt'),
                # Use total consumption splits to apportion no. building/sf
                "building stock and square footage": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_State_AllFuels_RowSums.txt')}
            self.eulp_post = ""
            # Set output JSON
            self.json_out = 'mseg_res_com_state.json'

    def configure_for_cost_performance_lifetime_data(self):
        """Reconfigure cost, performance, and life data to custom region."""
        # Set input JSON
        self.json_in = 'cpl_res_com_cdiv.json'
        # Find appropriate conversion data for user-specified geo. breakout
        # (1=AIA climate zones, 2=NEMS EMM regions)
        if self.geo_break == '1':
            self.res_climate_convert = (
                'supporting_data/convert_data/geo_map/'
                'Res_Cdiv_Czone_ColSums.txt')
            self.com_climate_convert = (
                'supporting_data/convert_data/geo_map/'
                'Com_Cdiv_Czone_ColSums.txt')
            # Set output JSON
            self.json_out = 'cpl_res_com_cz.json'
        elif self.geo_break == '2':
            self.res_climate_convert = {
                "electricity": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_EMM_Elec_ColSums.txt'),
                "natural gas": (
                    'supporting_data/convert_data/geo_map/'
                    'NElec_Cdiv_EMM_ColSums.txt'),
                "distillate":   (
                    'supporting_data/convert_data/geo_map/'
                    'NElec_Cdiv_EMM_ColSums.txt'),
                "other fuel": (
                    'supporting_data/convert_data/geo_map/'
                    'NElec_Cdiv_EMM_ColSums.txt'),
                # Use electricity splits to apportion no. building/sf data
                "building stock and square footage": (
                    'supporting_data/convert_data/geo_map/'
                    'Res_Cdiv_EMM_Elec_ColSums.txt')}
            self.com_climate_convert = {
                "electricity": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_EMM_Elec_ColSums.txt'),
                "natural gas": (
                    'supporting_data/convert_data/geo_map/'
                    'NElec_Cdiv_EMM_ColSums.txt'),
                "distillate": (
                    'supporting_data/convert_data/geo_map/'
                    'NElec_Cdiv_EMM_ColSums.txt'),
                # Use electricity splits to apportion no. building/sf data
                "building stock and square footage": (
                    'supporting_data/convert_data/geo_map/'
                    'Com_Cdiv_EMM_Elec_ColSums.txt')
            }
            # When breaking out to EMM regions, an additional conversion
            # between AIA climate zones in the envelope data and the EMM
            # regions is needed
            self.envelope_climate_convert = (
                'supporting_data/convert_data/geo_map/'
                'AIA_EMM_ColSums.txt')
            # Set output JSON
            self.json_out = 'cpl_res_com_emm.json'
        elif self.geo_break == '3':
            # When breaking out to census divisions, an additional conversion
            # between AIA climate zones in the envelope data and the census
            # divisions is needed
            self.envelope_climate_convert = (
                'supporting_data/convert_data/geo_map/'
                'AIA_Cdiv_ColSums.txt')
            # Set output JSON
            self.json_out = 'cpl_res_com_cdiv.json'


def merge_sum(base_dict, add_dict, cd, cz, cd_dict, cd_list,
              res_convert_array, com_convert_array, cpl, cd_to_cz_factor=0,
              fuel_flag=None):
    """Calculate values to restructure census division data to custom regions.

    Two dicts with identical structure, 'base_dict' and 'add_dict' are
    passed to this function and manipulated to effect conversion of the
    data from a census division (specified by 'cd') to a custom region
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
    modified to the current custom region using the appropriate
    conversion factor and added to 'base_dict'.

    This approach to converting the data to a custom region basis works
    because this function is called from within nested for loops that
    cover all of the census divisions for each custom region.
    Consequently, the data from each of the census divisions converted
    to their respective contributions to a single custom region can be
    added together to obtain the data in the desired final form.

    Args:
        base_dict (dict): A portion of the input JSON database
            corresponding to the current census division, modified in
            place to convert the data to a custom region basis.
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
        cz (int): The custom region to which the census division data
            are being added. Used as an array column index where the
            first (0th) column is not relevant, thus it begins at 1.
        cd_dict (dict): A dict for translating between census division
            descriptive strings and their corresponding numeric codes.
        cd_list (list): A list of the census divisions that are in the
            input data (the top level keys from the JSON structure),
            in the order in which they appear.
        res_convert_array (numpy.ndarray): Coefficients for converting
            from census divisions to custom regions for residential buildings.
        com_convert_array (numpy.ndarray): Coefficients for converting
            from census divisions to custom regions for commercial buildings.
        cpl (bool): True if cpl data are being processed
        cd_to_cz_factor (float): The numeric conversion factor to
            calculate the contribution from the current census division
            'cd' to the current custom region 'cz'.
        fuel_flag (NoneType): Flag for the fuel type currently being looped
            through (relevant only to EMM custom region cost_convert).

    Returns:
        A dict with the same form as base_dict and add_dict, with the
        values for the particular census division specified in 'cd'
        converted to the custom region 'cz'.
    """

    # Extract lists of strings corresponding to the residential and
    # commercial building types used to process these inputs
    res_bldg_types = list(mseg.bldgtypedict.keys())
    com_bldg_types = list(cm.CommercialTranslationDicts().bldgtypedict.keys())
    # Extract lists of strings corresponding to the residential and
    # commercial fuel types used to process these inputs
    res_fuel_types = list(mseg.fueldict.keys())
    com_fuel_types = list(cm.CommercialTranslationDicts().fueldict.keys())

    for (k, i), (k2, i2) in zip(sorted(base_dict.items()),
                                sorted(add_dict.items())):
        # Compare the top level/parent keys of the section of the dict
        # currently being parsed to ensure that both the base_dict
        # (census division basis) and add_dict (custom region basis)
        # are proceeding with the same structure; when cost, performance,
        # and lifetime data are being processed, skip the "unspecified"
        # building type and the "other" end use where it appears as
        # an unmodified zero in certain building and fuel type combinations
        if k == k2 and not (
            cpl and (
                (k == 'other' and not isinstance(i, dict)) or
                k == 'unspecified')):
            # Identify appropriate census division to custom region
            # conversion weighting factor array as a function of building
            # type; k and k2 correspond to the current top level/parent key,
            # thus k and k2 are equal to a building type immediately
            # prior to traversing the entire child tree for that
            # building type, for which the conversion number array
            # cd_to_cz_factor will be the same. Ensure that the walk is
            # currently at the building type level by checking keys from the
            # next level down (the fuel type level) against expected fuel types
            if ((k in res_bldg_types and
                any([x in res_fuel_types for x in base_dict[k].keys()])) or
                (k in com_bldg_types and
                 any([x in com_fuel_types for x in base_dict[k].keys()]))):
                if k in res_bldg_types:
                    cd_to_cz_factor = res_convert_array
                elif k in com_bldg_types:
                    cd_to_cz_factor = com_convert_array
            # Flag the current fuel type being updated, which is relevant
            # to ultimate selection of conversion factor from the conversion
            # array when translating to EMM region or state, in which case
            # conversion factors are different for different fuels. Use the
            # expectation that conversion arrays will be in dict format in the
            # EMM region or state case (with keys for fuel conversion factors)
            # to trigger the fuel flag update
            elif (k in res_fuel_types or k in com_fuel_types) and \
                    type(res_convert_array) is dict:
                fuel_flag = k
            # When updating total building stock or square footage data for
            # EMM regions or states, which are not keyed by fuel type, set the
            # fuel type flag accordingly; for states, this will pull in
            # mapping data based on consumption splits across all fuels; for
            # EMM regions, this will pull in mapping data based on electricity
            elif (k in ["total homes", "new homes", "total square footage",
                        "new square footage"]):
                fuel_flag = "building stock and square footage"
            # Recursively loop through both dicts
            if isinstance(i, dict):
                merge_sum(i, i2, cd, cz, cd_dict, cd_list, res_convert_array,
                          com_convert_array, cpl, cd_to_cz_factor, fuel_flag)
            elif type(base_dict[k]) is not str:
                # Check whether the conversion array needs to be further keyed
                # by fuel type, as is the case when converting to EMM region or
                # state; in such cases, the fuel flag indicates the key value
                # to use
                if fuel_flag is not None:
                    # Find conversion factor for the fuel and given
                    # combination of census division and EMM region or state;
                    # handle case where conversion data are not broken out
                    # by fuel type (AIA regions)
                    try:
                        convert_fact = cd_to_cz_factor[fuel_flag][cd][cz]
                    except ValueError:
                        convert_fact = cd_to_cz_factor[cd][cz]
                else:
                    # Find the conversion factor for the given combination of
                    # census division and AIA climate zone
                    convert_fact = cd_to_cz_factor[cd][cz]

                # Special handling of first dict (no addition of the
                # second dict, only conversion of the first dict with
                # the appropriate factor)
                if (cd == (cd_dict[cd_list[0]] - 1)):
                    # In the special case of consumer choice/time
                    # preference premium data, the data are reported
                    # as a list and must be reprocessed using a list
                    # comprehension (or comparable looping approach)
                    if isinstance(base_dict[k], list):
                        try:
                            base_dict[k] = [z * convert_fact for z
                                            in base_dict[k]]
                        except TypeError:  # one level deeper (incentives data)
                            for k_s in range(len(base_dict[k])):
                                base_dict[k][k_s] = [
                                    z_s * convert_fact for z_s
                                    in base_dict[k][k_s]]
                    else:
                        base_dict[k] = base_dict[k] * convert_fact
                else:
                    if isinstance(base_dict[k], list):
                        try:
                            base_dict[k] = [sum(y) for y
                                            in zip(base_dict[k],
                                            [z * convert_fact for z
                                             in add_dict[k2]])]
                        except TypeError:  # one level deeper (incentives data)
                            for k_s in range(len(base_dict[k])):
                                base_dict[k][k_s] = [
                                    sum(y_s) for y_s in zip(
                                        base_dict[k][k_s], [
                                            z_s * convert_fact for z_s
                                            in add_dict[k2][k_s]])]
                    else:
                        base_dict[k] = (base_dict[k] +
                                        add_dict[k2] * convert_fact)
        elif k != k2:
            raise (KeyError('Merge keys do not match!'))

    # Return a single dict representing sum of values of original two dicts
    return base_dict


def clim_converter(input_dict, res_convert_array, com_convert_array, data_in):
    """Convert input data dict from a census division to a custom region basis.

    This function principally serves to prepare the inputs for, and
    then call, a function that performs the calculations to convert
    data in the input_dict database specified for each microsegment
    from a census division to a custom region basis.

    Args:
        input_dict (dict): Data from JSON database, as imported,
            on a census division basis.
        res_convert_array (numpy.ndarray): An array of census
            division to custom region conversion factors for
            residential building types.
        com_convert_array (numpy.ndarray): Array of census
            division to custom region conversion factors for
            commercial building types.
        data_in (str): User input indicating energy and stock (1) or cost,
            performance, and lifetime data are being processed (2)

    Returns:
        A complete dict with the same structure as input_dict,
        except at the top level, where census division keys
        have been replaced by custom region keys, and the data
        have been updated to correspond to those custom regions.
    """

    # Create an instance of the CommercialTranslationDicts object from
    # com_mseg, which contains a dict that translates census division
    # strings into the corresponding integer codes
    cd = cm.CommercialTranslationDicts()

    # Set boolean for whether cost, performance, and lifetime data
    # are being processed
    if data_in == '2':
        cpl_bool = True
    else:
        cpl_bool = False

    # Obtain list of all custom region names as strings
    try:
        cz_list = res_convert_array.dtype.names[1:]
    # Handle conversion to EMM regions or states, in which custom region names
    # will be one level-deep in a dict that breaks out conv. factors by fuel
    except AttributeError:
        cz_list = res_convert_array["electricity"].dtype.names[1:]

    # Obtain list of all census divisions in the input data
    cd_list = list(input_dict.keys())

    # Set up empty dict to be updated with the results for each custom
    # region as the data are converted
    converted_dict = {}

    # Add the values from each custom region to the converted_dict
    for cz_number, cz_name in enumerate(cz_list):
        # Create a copy of the input dict at the level below a census
        # division or custom region (the structure below that level
        # should be identical); uses the first census division in
        # cd_list each time
        base_dict = copy.deepcopy(input_dict[cd_list[0]])

        # Loop through all census divisions to add their contributions
        # to each custom region
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
                # updated contents; add 1 to the custom region number
                # because it will be used as a column index for an
                # array where the first column of data are in the
                # second column (indexed as 1 in Python); this approach
                # overwrites base_dict, which is intentional because it
                # is the master dict that stores the data on a custom
                # region basis as the contribution from each census
                # division is added to the custom region by merge_sum
                base_dict = merge_sum(base_dict, add_dict, cd_number,
                                      (cz_number + 1), cd.cdivdict, cd_list,
                                      res_convert_array, com_convert_array,
                                      cpl_bool)
            else:
                raise (KeyError(
                    "Census division name not found in dict keys!"))

        # Once fully updated with the data from all census divisions,
        # write the resulting data to a new variable and update the
        # master dict with the data using the appropriate census
        # division string name as the key
        newadd = base_dict
        converted_dict.update({cz_name: newadd})

    return converted_dict


def env_cpl_data_handler(
        cpl_data, cost_convert, perf_convert, years, key_list):
    """Restructure envelope component cost, performance, and lifetime data.

    This function extracts the cost, performance, and lifetime data for
    the envelope components of residential and commercial buildings
    from the original data and restructures it into a form that is
    generally consistent with similar data originally obtained from
    the Annual Energy Outlook (AEO). These data are added to the input
    microsegments database after it is initially converted to a custom region
    basis, and these data are reported by AIA climate zone (if the data for a
    given envelope component are climate-specific).

    Args:
        cpl_data (dict): Cost, performance, and lifetime data for
            building envelope components (e.g., roofs, walls) including
            units and source information.
        cost_convert (dict): Cost unit conversions for envelope (and
            heating and cooling equipment, though those conversions are
            not used in this function) components, as well as the
            mapping from EnergyPlus building prototypes to AEO building
            types (as used in the microsegments file) to convert cost
            data from sources that use the EnergyPlus building types
            to the AEO building types.
        perf_convert (numpy ndarray): Performance value conversions for
            envelope components from AIA climate zone breakout to EMM
            region breakout (relevant only for EMM region translation).
        years (list): A list of integers representing the range of years
            in the data.
        key_list (list): Keys that specify the current location in the
            microsegments database structure and thus indicate what
            data should be returned by this function.

    Returns:
        A dict with installed cost, performance, and lifetime data
        applicable to the microsegment and envelope component specified
        by key_list, as well as units and source information for those
        data. All costs should have the units YYYY$/ft^2 floor, where
        YYYY is the year from which the data were obtained.
        These data are returned only if applicable for the envelope
        component that appears in key_list, and not for cases such as
        "people gain" for which there is no corresponding product that
        is part of the building.
    """

    # Preallocate variables for the building class (i.e., residential
    # or commercial), building type, and region
    bldg_class = ''
    bldg_type = ''
    cz_int = ''

    # Set AIA climate zone list
    aia_list = ['AIA_CZ1', 'AIA_CZ2', 'AIA_CZ3', 'AIA_CZ4', 'AIA_CZ5']
    # Set EMM region list
    emm_list = ['TRE', 'FRCC', 'MISW', 'MISC', 'MISE', 'MISS',
                'ISNE', 'NYCW', 'NYUP', 'PJME', 'PJMW', 'PJMC',
                'PJMD', 'SRCA', 'SRSE', 'SRCE', 'SPPS', 'SPPC',
                'SPPN', 'SRSG', 'CANO', 'CASO', 'NWPP', 'RMRG', 'BASN']
    # Set Census division list
    cdiv_list = ["new england", "mid atlantic", "east north central",
                 "west north central", "south atlantic", "east south central",
                 "west south central", "mountain", "pacific"]
    # Loop through the keys specifying the current microsegment to
    # determine the building type, whether the building is residential
    # or commercial, and identify the custom region
    for entry in key_list:
        # Identify the building type and thus determine the building class,
        # or region name
        if entry in mseg.bldgtypedict.keys():
            bldg_class = 'residential'
            bldg_type = entry
        elif entry in cm.CommercialTranslationDicts().bldgtypedict.keys():
            bldg_class = 'commercial'
            bldg_type = entry
        elif any([entry in y for y in [aia_list, emm_list, cdiv_list]]):
            cz_int = entry
            # Replace white spaces in Census division names with underscores
            # to match how numpy reads in the AIA->Cdiv conversions
            if entry in cdiv_list:
                cz_int = str(cz_int).replace(" ", "_")

    # Some envelope components are reported as two or more words, but
    # the first word is often the required word to select the relevant
    # cost, performance, and lifetime data, thus it is helpful to split
    # the envelope component key string into a list of words
    envelope_type = key_list[-1].split()

    # Use the first word in the list of strings for the envelope name
    # to determine whether data are available cost, performance, and
    # lifetime data and, if so, record those data (specified for the
    # correct building class) to a new variable
    specific_cpl_data = ''
    if envelope_type[0] in cpl_data['envelope'].keys():
        specific_cpl_data = cpl_data['envelope'][envelope_type[0]][bldg_class]

    # Preallocate empty dicts for the cost, performance, and lifetime
    # data, to include the data, units, and source information
    the_cost = {}
    the_perf = {}
    the_life = {}

    # If any data were found for the particular envelope type and
    # building class, extract the cost, performance, and lifetime data,
    # including units and source information, and record it to the
    # appropriate dict created for those data
    if specific_cpl_data:
        # Extract cost data units, if available (since some envelope
        # components might have costs reported without a dict structure)
        try:
            orig_cost_units = specific_cpl_data['cost']['units']
        except TypeError:
            orig_cost_units = None

        # Obtain and record the cost data in the preallocated dict,
        # starting with cases where the cost units require conversion
        # to be on the desired common basis of 'YYYY$/ft^2 floor'
        if orig_cost_units and orig_cost_units[4:] != '$/ft^2 floor':
            # Extract the current cost value
            orig_cost = specific_cpl_data['cost']['typical']

            # Handle the case where a single cost is provided or multiple
            # costs are provided in a dict structure
            if isinstance(orig_cost, dict):
                the_cost['typical'] = {}  # Preallocate 'typical' key
                for k, orig_cost_elem in orig_cost.items():
                    # Use the cost conversion function to obtain the costs
                    # for the current envelope component
                    adj_cost, adj_cost_units = cost_converter(orig_cost_elem,
                                                              orig_cost_units,
                                                              bldg_class,
                                                              bldg_type,
                                                              cost_convert)
                    # Add the cost information to the corresponding dict
                    # extending the cost values for each year
                    the_cost['typical'][k] = {
                        str(yr): adj_cost for yr in years}
            else:
                # Use the cost conversion function to obtain the costs
                # for the current envelope component
                adj_cost, adj_cost_units = cost_converter(orig_cost,
                                                          orig_cost_units,
                                                          bldg_class,
                                                          bldg_type,
                                                          cost_convert)

                # Add the cost information to the appropriate dict,
                # constructing the cost data itself into a structure with
                # a value reported for each year
                the_cost['typical'] = {str(yr): adj_cost for yr in years}

            the_cost['units'] = adj_cost_units
            the_cost['source'] = specific_cpl_data['cost']['source']

        # If cost units are reported but the units indicate that there
        # is no need for conversion, shift the data to a per year
        # basis but carry over the units and source information
        elif orig_cost_units:
            # Extract the current cost value
            orig_cost = specific_cpl_data['cost']['typical']

            # Handle the case where a single cost is provided or multiple
            # costs are provided in a dict structure
            if isinstance(orig_cost, dict):
                the_cost['typical'] = {}  # Preallocate 'typical' key
                for k, orig_cost_elem in orig_cost.items():
                    the_cost['typical'][k] = {str(yr): orig_cost_elem
                                              for yr in years}
            else:
                the_cost['typical'] = {str(yr): orig_cost
                                       for yr in years}
            the_cost['units'] = orig_cost_units
            the_cost['source'] = specific_cpl_data['cost']['source']

        # Output the cost data as-is for for cases where no cost
        # data are reported (i.e., orig_cost_units == None)
        else:
            the_cost = specific_cpl_data['cost']

        # Obtain the performance data depending on whether or not a
        # second word appears in the envelope_type list, as with
        # 'windows conduction' and 'windows solar'; other types that
        # will have two or more entries in the envelope_type list
        # include people gain, equipment gain, other heat gain, and
        # lighting gain
        if len(envelope_type) > 1:
            # For windows data, the performance data are specified by
            # 'solar' or 'conduction'; the other envelope types that
            # are not relevant will be ignored per this if statement
            if envelope_type[1] in specific_cpl_data['performance'].keys():
                # Simplify the cost, performance, lifetime dict to only
                # the relevant performance data (this step shortens later
                # lines of code to make it easier to comply with the PEP 8
                # line length requirement)
                env_s_data = specific_cpl_data['performance'][envelope_type[1]]

                # Extract the performance value, first trying for if it
                # is specified to the climate zone level. *NOTE* It is assumed
                # that all data specified to the climate zone level will have
                # uniform value formats - e.g., all climate zones will have
                # a single value reported or several values broken out by year
                try:
                    # Check whether an additional conversion of performance
                    # values is needed (from AIA regions to EMM regions)
                    if perf_convert is not None:
                        # Handle cases where performance values are and are not
                        # broken out further by year
                        try:
                            # Performance values not broken out by year
                            perf_val = sum([
                                env_s_data['typical'][y] * perf_convert[x][
                                    cz_int] for x, y in enumerate(aia_list)])
                        except TypeError:
                            # Performance values are broken out by year
                            perf_val = {str(yr): sum([
                                env_s_data['typical'][y][str(yr)] *
                                perf_convert[x][cz_int] for x, y in enumerate(
                                    aia_list)]) for yr in years}
                    else:
                        perf_val = env_s_data['typical'][cz_int]
                except KeyError:
                    perf_val = env_s_data['typical']

                # Add the units and source information to the dict
                # (note that this step can't move outside this if
                # statement because these data are in a different
                # location for this case where the performance
                # specification is more detailed)
                the_perf['units'] = env_s_data['units']
                the_perf['source'] = env_s_data['source']

        # For the cases where the performance data are accessible from
        # the existing cost, performance, and lifetime data dict without
        # providing further levels of specificity
        else:
            # Extract the performance value, first trying for if
            # the value is broken out by vintage
            try:
                perf_val = [
                    specific_cpl_data['performance']['typical']['new'],
                    specific_cpl_data['performance']['typical']['existing']]
                # Try for if the value is further broken out by climate
                try:
                    # Check whether an additional conversion of performance
                    # values is needed (from AIA regions to EMM regions)
                    if perf_convert is not None:
                        # Handle cases where performance values are and are not
                        # broken out further by year
                        perf_val = [sum([
                            x[z] * perf_convert[y][cz_int] for
                            y, z in enumerate(aia_list)]) if type(
                            x[aia_list[0]]) is not dict else {
                            str(yr): sum([x[z][str(yr)] * perf_convert[y][
                                cz_int] for y, z in enumerate(aia_list)])
                            for yr in years} for x in perf_val]
                    else:
                        perf_val = [x[cz_int] for x in perf_val]
                except TypeError:
                    pass
            except KeyError:
                # Try for if the value is broken out by climate
                try:
                    # Check whether an additional conversion of performance
                    # values is needed (from AIA regions to EMM regions)
                    if perf_convert is not None:
                        try:
                            # Handle cases where performance values are and are
                            # not broken out further by year
                            perf_val = sum([specific_cpl_data['performance'][
                                'typical'][y] * perf_convert[x][cz_int]
                                for x, y in enumerate(aia_list)])
                        except TypeError:
                            perf_val = {str(yr): sum([specific_cpl_data[
                                'performance']['typical'][y][str(yr)] *
                                perf_convert[x][cz_int] for
                                x, y in enumerate(aia_list)]) for yr in years}
                    else:
                        perf_val = specific_cpl_data[
                            'performance']['typical'][cz_int]
                except TypeError:
                    perf_val = specific_cpl_data['performance']['typical']
            the_perf['units'] = specific_cpl_data['performance']['units']
            the_perf['source'] = specific_cpl_data['performance']['source']

        # Record the performance value identified in the above rigmarole

        # Case where the performance value is not broken out by vintage
        if type(perf_val) is not list:
            # Note: the dict comprehension handles cases where the
            # performance value is further broken out by year; if the value
            # is not broken out by year, the comprehension assumes the same
            # performance value for all years in the analysis time horizon
            the_perf['typical'] = {
                str(yr): perf_val[str(yr)] if type(perf_val) is dict
                else perf_val for yr in years}
        # Case where the performance value is broken out by vintage
        else:
            # Note: the dict comprehension handles cases where the
            # performance value is further broken out by year; if the value
            # is not broken out by year, the comprehension assumes the same
            # performance value for all years in the analysis time horizon
            the_perf['typical'] = {
                'new': {
                    str(yr): perf_val[0][str(yr)] if type(perf_val[0]) is dict
                    else perf_val[0] for yr in years},
                'existing': {
                    str(yr): perf_val[1][str(yr)] if type(perf_val[1]) is dict
                    else perf_val[1] for yr in years}}

        # Transfer the lifetime data as-is (the lifetime data has a
        # uniform format across all of the envelope components) except
        # for the average, which is updated to be reported by year
        the_life['average'] = {str(yr):
                               specific_cpl_data['lifetime']['average']
                               for yr in years}
        the_life['range'] = specific_cpl_data['lifetime']['range']
        the_life['units'] = specific_cpl_data['lifetime']['units']
        the_life['source'] = specific_cpl_data['lifetime']['source']

        # Add the cost, performance, and lifetime dicts into a master dict
        # for the microsegment and envelope component specified by key_list
        tech_data_dict = {'installed cost': the_cost,
                          'performance': the_perf,
                          'lifetime': the_life}

        # If the building type is residential, add envelope component
        # consumer choice parameters for each year in the modeling time
        # horizon (these parameters are based on AEO consumer choice
        # data for the residential heating and cooling end uses in
        # 'rsmeqp.txt')
        if bldg_class == 'residential':
            tech_data_dict['consumer choice'] = {
                'competed market share': {
                    'parameters': {'b1': {str(yr): -0.003 for yr in years},
                                   'b2': {str(yr): -0.012 for yr in years}},
                    'source': ('EIA AEO choice model parameters for heating' +
                               ' and cooling equipment')
                }
            }

    # If no data were found, which is expected for envelope components
    # that are not representative of building products (e.g., people
    # gain, equipment gain), simply return 0
    else:
        tech_data_dict = 0

    return tech_data_dict


def mels_cpl_data_handler(cpl_data, conversions, years, key_list):
    """Restructure MELs component cost, performance, and lifetime data.

    This function extracts the cost, performance, and lifetime data for
    miscellaneous electric loads (MELs) technologies of residential and
    commercial buildings from the original data and restructures it into a
    form that is generally consistent with similar data originally obtained
    from the Annual Energy Outlook (AEO). These data are added to the input
    microsegments database after it is converted to a climate zone basis.

    Args:
        cpl_data (dict): Cost, performance, and lifetime data for
            MELs technologies including units and source information.
        conversions (dict): Energy, stock, and square footage data needed
            to convert cost units for MELs technologies.
        years (list): A list of integers representing the range of years
            in the data.
        key_list (list): Keys that specify the current location in the
            microsegments database structure and thus indicate what
            data should be returned by this function.

    Returns:
        A dict with installed cost, performance, and lifetime data
        applicable to the microsegment and MELs technology specified
        by key_list, as well as units and source information for those
        data. All residential costs should be in $/unit, while all commercial
        costs should be in $/ft^2 floor.
    """

    # Preallocate variable storing cost, performance, and lifetime data
    specific_cpl_data = ''
    # Preallocate variables for the building class (i.e., residential
    # or commercial) and the building type
    bldg_class = ''
    bldg_type = ''
    # Check second item in list (building type) to identify building type
    # name and associated class (residential, commercial) of the current
    # microsegment
    if key_list[1] in mseg.bldgtypedict.keys():
        bldg_type = key_list[1]
        bldg_class = 'residential'
    elif key_list[1] in cm.CommercialTranslationDicts().bldgtypedict.keys():
        bldg_type = key_list[1]
        bldg_class = 'commercial'
    # Use fourth item in list to identify end use of the current microsegment
    eu = key_list[3]
    # Pull cost, performance, and lifetime data if available, handling cases
    # where the data are found on the end use level (4 item microsegment key
    # chain) and cases where the data are found on the technology level (5 item
    # list)
    if len(key_list) == 4:
        try:
            specific_cpl_data = cpl_data['MELs'][bldg_class][eu]
        except KeyError:
            pass
    elif len(key_list) == 5:
        tech = key_list[-1]
        try:
            specific_cpl_data = cpl_data['MELs'][bldg_class][eu][tech]
        except KeyError:
            pass

    # Preallocate empty dicts for the cost, performance, and lifetime
    # data, to include the data, units, and source information
    the_cost = {}
    the_perf = {}
    the_life = {}

    # If any data were found for the particular technology, end use, and
    # building class, extract the cost, performance, and lifetime data,
    # including units and source information, and record it to the
    # appropriate dict created for those data
    if specific_cpl_data:
        # Convert year list to strings for further use in data dicts
        years_str = [str(x) for x in years]
        # Set the possible operational mode breakouts for MELs performance data
        modes = ["active", "ready", "sleep", "off"]

        # Extract cost data units
        orig_cost_units = specific_cpl_data['cost']['units']

        # Case where the commercial MELs cost data require conversion from
        # $/unit to '$/ft^2 floor'; currently, data for this conversion are
        # only available for PCs so other technologies will be ignored
        if orig_cost_units and (
            bldg_class == "commercial" and '$/ft^2 floor'
                not in orig_cost_units and '$/unit' in orig_cost_units):
            if eu == "PCs":
                # Set the unconverted cost value
                orig_cost = specific_cpl_data['cost']['typical']
                # Strip the year from the cost units (to be added back later)
                the_year = orig_cost_units[:4]
                # PC cost conversion data are split into three categories by
                # building type; find the appropriate category key to use
                # in pulling these data for the current building type
                if bldg_type in ["large office", "small office", "education"]:
                    convert_key = "office and education"
                elif bldg_type == "health care":
                    convert_key = "health care"
                else:
                    convert_key = "all other"
                # Apply the cost conversion ($/unit->$/ft^2 floor) across years
                adj_cost = {
                    key: orig_cost[key] * conversions["cost unit conversions"][
                        eu]["conversion factor"]["value"][convert_key]
                    for key in years_str}
                # Finalize adjusted cost units by adding back the year
                adj_units = the_year + "$/ft^2 floor"
                # Add the converted cost information to the appropriate dict
                the_cost['typical'] = adj_cost
                the_cost['units'] = adj_units
                the_cost['source'] = specific_cpl_data['cost']['source']
        # Case where MELs cost data are not in expected units (throw error)
        elif orig_cost_units and ('$/unit' not in orig_cost_units):
            raise ValueError("Baseline MELs technology cost units "
                             "for " + str(key_list) + " are not in $/unit")
        # Case where there is no need for cost conversion
        elif orig_cost_units:
            the_cost['typical'] = specific_cpl_data['cost']['typical']
            the_cost['units'] = orig_cost_units
            the_cost['source'] = specific_cpl_data['cost']['source']

        # Extract MELs performance data and units
        orig_perf = specific_cpl_data['performance']['typical']
        orig_perf_units = specific_cpl_data['performance']['units']

        # Ensure that all MELs performance data is in units of kWh/yr

        # Case where performance data are already in kWh/yr and no further
        # calculations are required
        if orig_perf_units == "kWh/yr" and any([
                x not in modes for x in orig_perf.keys()]):
            perf_kwh_yr = orig_perf
        # Case where performance data are in units of kWh/yr, but are
        # broken out by operational mode (e.g, active, ready, sleep, off);
        # convert to annual kWh/yr values
        elif orig_perf_units == "kWh/yr" and any([
                x in modes for x in orig_perf.keys()]):
            # Pre-allocate converted performance dict
            perf_kwh_yr = {}
            # Loop through all operational modes and sum performance values
            for mode in orig_perf.keys():
                # First item in loop; set the first kWh/yr values
                if len(perf_kwh_yr.keys()) == 0:
                    perf_kwh_yr = {key: orig_perf[mode][key]
                                   for key in years_str}
                # Subsequent items in loop; add to previous kWh/yr values
                else:
                    perf_kwh_yr = {key: perf_kwh_yr[key] + orig_perf[mode][key]
                                   for key in years_str}
        # Case where performance data are in units of W and are
        # broken out by operational mode (e.g, active, ready, sleep, off);
        # convert to annual kWh/yr values
        elif type(orig_perf_units) == list and all([
            x in orig_perf_units for x in [
                "W", "fraction annual operating hours"]]):
            # Pre-allocate converted performance dict
            perf_kwh_yr = {}
            # Loop through all operational modes and sum performance values
            for mode in orig_perf.keys():
                # First item in loop; set the first kWh/yr value
                # by multiplying W/mode by 8760 annual operational hours and
                # dividing by 1000 (to convert from Wh to kWh)
                if len(perf_kwh_yr.keys()) == 0:
                    perf_kwh_yr = {key: ((orig_perf[mode][key][0] *
                                          orig_perf[mode][key][1] * 8760) /
                                         1000)
                                   for key in orig_perf[mode].keys()}
                # Subsequent items; add to previous kWh/yr values
                else:
                    perf_kwh_yr = {key: (perf_kwh_yr[key] + (
                                   (orig_perf[mode][key][0] *
                                    orig_perf[mode][key][1] * 8760) / 1000))
                                   for key in orig_perf[mode].keys()}
        # Case where other unexpected performance units are given (throw error)
        else:
            raise ValueError("Unexpected baseline performance units for MELs "
                             "baseline segment " + str(key_list) + "")

        # Set final performance levels
        the_perf['typical'] = perf_kwh_yr
        # Set final performance units
        the_perf["units"] = "kWh/yr"
        # Set final performance source data
        the_perf['source'] = specific_cpl_data['performance']['source']

        # Extract lifetime data as-is
        the_life['average'] = specific_cpl_data['lifetime']['average']
        the_life['range'] = specific_cpl_data['lifetime']['range']
        the_life['units'] = specific_cpl_data['lifetime']['units']
        the_life['source'] = specific_cpl_data['lifetime']['source']

        # Perform a final check to ensure there are no technologies with
        # only partially complete information
        if all([len(x) > 0 for x in [
                the_cost.keys(), the_perf.keys(), the_life.keys()]]) and (
            math.isnan(the_life['average']) is False and
            the_life['average'] != 0) and all(
            [all([(math.isnan(x) is False and x != 0) for x in y.values()])
             for y in [the_cost['typical'], the_perf['typical']]]):
            # Add the cost, performance, and lifetime dicts into a master dict
            # for the microsegment and envelope component specified by key_list
            tech_data_dict = {'installed cost': the_cost,
                              'performance': the_perf,
                              'lifetime': the_life}
        # If there are missing/incomplete data, simply return 0
        else:
            tech_data_dict = 0

    # If no data were found, simply return 0
    else:
        tech_data_dict = 0

    return tech_data_dict


def cost_converter(cost, units, bldg_class, bldg_type, conversions):
    """Convert envelope cost data to uniform units of $/ft^2 floor.

    The envelope cost data are provided in the units of the
    original source of the data, To ensure that the conversion from
    the original data to the desired cost units of dollars per square
    foot floor area is always consistent across all envelope data,
    the conversion from the original units to the common and desired
    units is performed by this function. The cost in its original
    form is input to this function and the relationships between e.g.,
    window area and wall area (i.e., window-wall ratio) are used to
    convert from the original form to the final desired units.

    In some cases, the conversion data are specified for EnergyPlus
    building types, and then the conversion must incorporate both
    the units conversion and applying the appropriate weights to
    convert from EnergyPlus to Annual Energy Outlook building types.

    Additionally, some data require multiple conversions, thus this
    function might call itself again to complete the conversion
    process. For example, window data must be converted from window
    area to wall area, and then from wall area to floor area.

    Args:
        cost (float): The cost value that requires conversion.
        units (str): The units of the cost indicated.
        bldg_class (str): The applicable building class (i.e., either
            "residential" or "commercial").
        bldg_type (str): THe applicable specific building type (i.e.,
            "single family home" or "small office") from the building
            types used in the AEO.
        conversions (dict): Cost unit conversions for envelope (and
            heating and cooling equipment, though those conversions are
            not used in this function) components, as well as the
            mapping from EnergyPlus building prototypes to AEO building
            types (as used in the microsegments file) to convert cost
            data from sources that use the EnergyPlus building types
            to the AEO building types.

    Outputs:
        The updated cost in the final desired units of $/ft^2 floor and
        the revised units to verify that the conversion is complete.
    """

    # Record the year (as YYYY) in the cost units for later addition to
    # the adjusted cost units and then strip the year off the units
    the_year = units[:4]
    units = units[4:]

    # Obtain the dict of cost conversion factors for the envelope
    # components (for those components for which a conversion factor is
    # provided); note that the keys for the desired level of the dict
    # are specified separately and the functools.reduce function is
    # used to extract the dict at the specified level
    dict_keys = ['cost unit conversions', 'heating and cooling', 'demand']
    env_cost_factors = ft.reduce(dict.get, dict_keys, conversions)

    # Obtain the dict of building type conversion factors specified
    # for the particular building type passed to the function; these
    # data might be needed later contingent on the particular cost
    # being converted; note the same method as above for extracting
    # the data from a deeply nested dict
    dict_keys = ['building type conversions', 'conversion data', 'value',
                 bldg_class, bldg_type]
    bldg_type_conversions = ft.reduce(dict.get, dict_keys, conversions)

    # Loop through the cost conversion factors and compare their
    # specified "original units" with the units passed to this
    # function to determine the relevant envelope component; the
    # approach applied here yields the last match, so if multiple
    # data requiring conversion are specified with the same units,
    # this matching approach might not work as expected
    for key in env_cost_factors.keys():
        if env_cost_factors[key]['original units'] == units:
            env_component = key

    # Extract the conversion factors associated with the particular
    # envelope component identified in the previous step and for the
    # building class passed to this function; this function will
    # trigger an error if no matching envelope component was
    # identified by the previous step
    dict_keys = [env_component, 'conversion factor', 'value', bldg_class]
    bldg_specific_cost_conv = ft.reduce(dict.get, dict_keys, env_cost_factors)

    # Identify the units for the forthcoming adjusted cost
    adj_cost_units = env_cost_factors[env_component]['revised units']

    # Add the year onto the anticipated revised units from the conversion
    adj_cost_units = the_year + adj_cost_units

    # Preallocate a variable for the adjusted cost value
    adj_cost = 0

    # Explore any remaining structure in env_cost_factors based on the
    # structure of the data and the specific data provided, which
    # varies by building type, to calculate the correct adjusted cost
    # (though this function does not explicitly  use building type to
    # determine the appropriate approach for the calculation)

    # If there is any additional structure beyond the building class
    # (i.e., residential or commercial) level, calculate the adjusted
    # cost depending on whether any building type conversions (i.e.,
    # conversions from EnergyPlus to AEO building types) are specified
    if isinstance(bldg_specific_cost_conv, dict):
        # if the cost unit conversions for the current envelope
        # component are specified by building class but do not require
        # conversion from the EnergyPlus reference buildings to the AEO
        # buildings, complete the calculation accordingly
        if bldg_type_conversions is None:
            adj_cost = cost * bldg_specific_cost_conv[bldg_type]
        # If building type conversion is required, loop through the
        # EnergyPlus building types associated with the AEO building
        # type specified by 'bldg_type' and add the applicable cost
        # to the adjusted cost total
        else:
            for key in bldg_specific_cost_conv[bldg_type].keys():
                adj_cost += (cost * bldg_type_conversions[key] *
                             bldg_specific_cost_conv[bldg_type][key])
    # Specific to the case where the building type is sufficient to
    # identify the cost conversion factor
    else:
        adj_cost = cost*bldg_specific_cost_conv

    # If the units following the above conversion are still not the
    # final desired units on a per square foot floor area basis,
    # call this function again
    if adj_cost_units != the_year + '$/ft^2 floor':
        adj_cost, adj_cost_units = cost_converter(adj_cost,
                                                  adj_cost_units,
                                                  bldg_class,
                                                  bldg_type,
                                                  conversions)

    return adj_cost, adj_cost_units


def walk(cpl_data, conversions, perf_convert, years, json_db, key_list=[]):
    """Recursively explore JSON data structure to populate data at leaf nodes.

    This function recursively traverses the microsegment data structure
    (formatted as a nested dict) to each leaf/terminal node, assembling
    a list of the keys that define the location of the terminal node.
    Once a terminal node is reached (i.e., a dict is not found at the
    given location in the data structure), call the desired function to
    process the cost, performance, and lifetime (and consumer choice
    parameters for residential buildings) data for the envelope
    components. These data are added at this step because their original
    sources provide the data on a climate zone and not census division
    basis, so the data must be added to the baseline cost, performance,
    and lifetime database after the data from the EIA AEO have been
    initially converted from census division to a custom region basis.

    Args:
        cpl_data (dict): Cost, performance, and lifetime data for
            building envelope components (e.g., roofs, walls) including
            units and source information.
        conversions (dict): Cost unit conversions for envelope and PCs (and
            heating and cooling equipment, though those conversions are
            not used in this function) components, as well as the
            mapping from EnergyPlus building prototypes to AEO building
            types (as used in the microsegments file) to convert cost
            data from sources that use the EnergyPlus building types
            to the AEO building types.
        perf_convert (numpy ndarray): Performance value conversions for
            envelope components from AIA climate zone breakout to EMM
            region breakout (relevant only for EMM region translation).
        years (list): A list of integers representing the range of years
            in the data that are desired to be included in the output.
        json_db (dict): The dict structure to be modified with additional data.
        key_list (list): Keys that specify the current location in the
            microsegments database structure and thus indicate what
            data should be returned by this function. Since this
            function operates recursively, the entries in and length
            of this list will change as the function traverses the
            nested structure in json_db.

    Returns:
        An updated dict structure with additional data, described
        above, inserted in the appropriate locations, and ready for
        further updating or output as a complete JSON database.
    """

    # Explore data structure from current level
    for key, item in json_db.items():

        # If there are additional levels in the dict, call the function
        # again to advance another level deeper into the data structure
        if isinstance(item, dict):
            walk(cpl_data, conversions, perf_convert, years, item,
                 key_list + [key])

        # If a leaf node has been reached, check if the final entry in
        # the list is 'demand', indicating that the current node is an
        # envelope component with no data currently stored, and if
        # so, finish constructing the key list for the current location
        # and obtain the data to update the dict. If the final entry in the
        # list indicates a miscellaneous electric load (MELs) technology,
        # again finish constructing the key list for the current location and
        # obtain the data to update the dict.
        else:
            if key_list[-1] == 'demand':
                leaf_node_keys = key_list + [key]

                # Extract and neatly format the envelope component cost,
                # performance, and lifetime data into a complete dict
                # for the specified microsegment and envelope component
                data_dict = env_cpl_data_handler(
                    cpl_data, conversions, perf_convert, years, leaf_node_keys)
                # Set dict key to extracted data
                json_db[key] = data_dict
            elif (len(key_list) == 3) and any([
                key in cpl_data["MELs"][x].keys() for x in [
                    "residential", "commercial"]]) or \
                (len(key_list) == 4) and any([
                    key_list[-1] in cpl_data["MELs"][x].keys() for x in [
                    "residential", "commercial"]]):
                leaf_node_keys = key_list + [key]
                # Extract and neatly format the MELs cost,
                # performance, and lifetime data into a complete dict
                # for the specified microsegment and MELs technology
                data_dict = mels_cpl_data_handler(
                    cpl_data, conversions, years, leaf_node_keys)

                # Set dict key to extracted data
                json_db[key] = data_dict

    # Return filled database structure
    return json_db


def finalize_eu_shares(result, eu_pp, years):
    """Reallocate electricity data to match EULP end use shares of total.

    When EMM-resolved stock/energy data are prepared (based on total
    electricity shares within each Census Division stock/energy total from
    EIA), this function recursively traverses the microsegment data structure
    (formatted as a nested dict) to each leaf/terminal node and applies
    scaling factors as needed to calibrate final electricity end use shares
    within each EMM region to the shares in the End Use Load Profiles (EULP)
    database.

    Args:
        result (dict): EMM-resolved stock and energy use microsegments, pre-
            calibration to the EULP data.
        eu_pp (numpy array): Electricity end use shares of total electricity
            by EMM region and building type, from the EULP.

    Returns:
        An updated stock/energy dict with electricity end use totals that are
        consistent with end use shares of total electricity from each EMM
        region and res. vs. com. building type in the EULP database.
    """

    # Set Scout building types, end uses, and tech names to exclude from the
    # calibration
    excl = {
        "bldg": ["unspecified", "other"],
        "euses": ["unspecified"],
        "tech": [
            "electric other", "Commercial Beverage Merchandisers",
            "Commercial Ice Machines", "Commercial Reach-In Freezers",
            "Commercial Reach-In Refrigerators",
            "Commercial Refrigerated Vending Machines",
            "Commercial Supermarket Display Cases",
            "Commercial Walk-In Freezers",
            "Commercial Walk-In Refrigerators", "other"]
        }

    # Set Scout building types, fuel types, and end uses in the input dict

    # Anchor on data structure for first region
    first_reg_dat = result[list(result.keys())[0]]
    # Res building types from data
    res_btypes = [x for x in first_reg_dat.keys() if "home" in x]
    # Res electric end uses from data
    res_elec_eus = list(first_reg_dat[res_btypes[0]]["electricity"].keys())
    # Com building types from data
    com_btypes = [x for x in first_reg_dat.keys() if x not in res_btypes]
    # Com electric end uses from data
    com_elec_eus = list(first_reg_dat[com_btypes[0]]["electricity"].keys())
    # Fuels
    fuels = ["electricity", "natural gas", "distillate", "other fuel"]
    # Shorthand for combined building types
    all_btypes = res_btypes + com_btypes
    # Shorthand for combined end uses
    all_eus = np.unique(res_elec_eus + com_elec_eus)
    # Shorthand dict with all variables
    scout_base_defs = {"fuels": fuels, "bldg types": all_btypes,
                       "end uses": all_eus}
    # EULP calibration year is 2018 – set to first year in data range if
    # not available
    if 2018 in years:
        yr_calibrate = "2018"
    else:
        yr_calibrate = str(years[0])
    # Map building types in the EULP shares array to Scout building types
    eulp_bt_map = {
        "res": res_btypes,
        "com": com_btypes
    }
    # Map end uses in the EULP shares array to Scout building types

    # Residential EULP end uses and mapping to Scout residential end uses
    eulp_eu_res = {
        "heating": ["heating", "secondary heating"], "cooling": ["cooling"],
        "fans and pumps": ["fans and pumps"],
        "water heating": ["water heating"], "lighting": ["lighting"],
        "refrigeration": ["refrigeration", "other-freezers"],
        "plug loads": ["other-misc", "computers", "TVs"],
        "ceiling fan": ["ceiling fan"], "drying": ["drying"],
        "clothes washing": ["other-clothes washing"],
        "dishwasher": ["other-dishwashing"],
        "pool heaters": ["other-pool heaters"],
        "pool pumps": ["other-pool pumps"], "cooking": ["cooking"],
        "portable electric spas": ["other-portable electric spas"]
    }
    # Commercial EULP end uses and mapping to Scout commercial end uses
    eulp_eu_com = {
        "heating": ["heating"], "cooling": ["cooling"],
        "fans and pumps": ["ventilation"], "water heating": ["water heating"],
        "lighting": ["lighting"], "refrigeration": ["refrigeration"],
        "plug loads": ["MELs", "unspecified", "PCs", "non-PC office equipment"]
    }
    # Shorthand dict containing all mapping data
    eulp_map_dat = {
        "bldg types": eulp_bt_map, "res end uses": eulp_eu_res,
        "com end uses": eulp_eu_com
    }
    # Initialize dict to track mseg characteristics during recursive loops
    branch_dat = {"fuel": "", "bldg": "", "end use": "", "tech type": "",
                  "tech": "", "value type": ""}
    # Initalize adjustment factors by region/bldg. type/end use and
    # electricity totals by region/bldg. type
    adj_facts = {reg: {
        bldg: {eu: 0 for eu in (
            eulp_eu_res.keys() if bldg == "res" else eulp_eu_com.keys())}
        for bldg in eulp_bt_map.keys()} for reg in result.keys()}
    elec_tots = {
        reg: {bldg: 0 for bldg in eulp_bt_map.keys()} for reg in result.keys()}

    # Find total electricity and end use shares of total for the original
    # baseline data; develop adjustment factors that ensure electric end use
    # shares in the baseline data match those in the EULP; apply factors to
    # original baseline data

    # Loop through regions
    for reg in adj_facts.keys():
        # Develop electric end use and total values for each region
        process_branches(
            adj_facts[reg], elec_tots[reg], result[reg], yr_calibrate,
            eulp_map_dat, scout_base_defs, branch_dat, excl,
            operation="sum")

        # Loop through building types and end uses to find the original
        # Scout end use shares by building type and the EULP shares; divide
        # the latter by the former to get the final adjustment factors by
        # end use and building type within the currently looped region
        for bt in adj_facts[reg].keys():
            for eu in adj_facts[reg][bt].keys():
                # Find Scout end use shares (normalize end use sums by total
                # electricity sum by region and building type)
                if elec_tots[reg][bt] != 0:
                    adj_facts[reg][bt][eu] = \
                        adj_facts[reg][bt][eu] / elec_tots[reg][bt]
                else:
                    adj_facts[reg][bt][eu] = 0
                # Pull EULP value for the end use share in the given region
                # and building type
                eulp_fact = eu_pp[
                    (eu_pp["region"] == reg) &
                    (eu_pp["building type"] == bt)][eu].iloc[0]
                # Find ratio of EULP share to Scout share, to use subsequently
                # in adjusting the Scout end use data
                if adj_facts[reg][bt][eu] != 0:
                    adj_facts[reg][bt][eu] = (
                        eulp_fact / adj_facts[reg][bt][eu])

        # Apply adjustment factors to original baseline data for each region
        process_branches(
            adj_facts[reg], elec_tots[reg], result[reg], yr_calibrate,
            eulp_map_dat, scout_base_defs, branch_dat, excl,
            operation="multiply")

    # Return recalibrated dictionary
    return result


def process_branches(adj_dct, tot_dct, base_dct, yr_calibrate, eulp_map_dat,
                     scout_base_defs, branch_dat, excl, operation):
    """Find sum of electric end use estimates or apply adjustments to them.

    Recursively iterate through a dict of baseline microsegments and either
    sum the microsegments' energy use data across a given building type
    (res/com) and end use or apply a scaling factor to both the stock and
    energy use data for each microsegment to reflect calibration against EULP
    end use shares of total electricity use.

    Args:
        adj_dct (dict): Dict that will ultimately contain scaling factors
            to true up end-use shares for each region/bldg. type to EULP.
        tot_dct (dict): Regional electricity totals data by building type.
        base_dct (dict): Baseline data pre-calibration to EULP.
        yr_calibrate (str): Year of EULP calibration.
        eulp_map_dat (dict): Info. for mapping Scout building types and end
            uses to those in the EULP end use shares data.
        scout_base_defs (dict): Dict that supports identification of current
            level in microsegment hierarchy (building type, fuel, end use,
            tech.) that this function recursively loops through.
        branch_dat (dict): Data for tracking building type, fuel, end use,
            and tech. characteristics of currently looped microsegment.
        excl (dict): Building types, end uses, and technology types to exclude
            from the EULP calibration (and execution of this function).
        operation (str): Flag that determines whether this function sums
            microsegment data across end use/building type combinations or
            applies scaling factors to each microsegment to reflect EULP
            calbration.

    Returns:
        Either a) summed electric end use energy by res/com building
        type, within a given region or b) baseline data updated to reflect
        EULP end use shares of total res/com electricity within a given region.
    """

    # Shorthands for microsegment branch data
    ft, bt, eu, tt, tc, vt = [
        branch_dat["fuel"], branch_dat["bldg"], branch_dat["end use"],
        branch_dat["tech type"], branch_dat["tech"], branch_dat["value type"]]
    # Loop through microsegment branches in baseline input data
    for key, value in base_dct.items():
        # Reached terminal value: apply sum or multiplication operation

        # Ensure that full microsegment branch data exist and microsegment
        # applies to electricity only (EULP calibration for electric end uses)
        if isinstance(value, (int, float)) and all([
                x for x in [ft, bt, eu, tc]]) and ft == "electricity":
            # Handle 'other' Scout end use, which matches multiple end uses
            # in the EULP database (e.g., clothes washing, dishwasher, etc.);
            # try to match based on technology information, and if no match,
            # assign to plug loads
            if len(eu) > 1:
                eu_f = [x for x in eu if tc in x]
                if len(eu_f) == 0:
                    eu_f = "plug loads"
                else:
                    eu_f = eu_f[0]
            else:
                eu_f = eu[0]

            # Handle terminal value differently depending on operation

            # If summing for the purposes of developing calibration adjustment
            # factors, exclude envelope data from calibration (would be double
            # counted w/ HVAC) and ensure factors are based on energy use (not
            # stock) in the calibration year
            if operation == "sum" and (not tt or tt == "supply") and \
                    vt == "energy" and key == yr_calibrate:
                # Add to both end use specific and total values of electricity
                # for the given building type and region
                adj_dct[bt][eu_f] += value
                tot_dct[bt] += value
            # Second case multiplies adjustment factors calculated for the
            # current microsegment building type and end use by original
            # microsegment data
            elif operation == "multiply":
                base_dct[key] = base_dct[key] * adj_dct[bt][eu_f]
        # Did not reach terminal value: update microsegment branch data
        # and continue recursive loop
        elif isinstance(value, dict):
            # Register the fuel, building type, end use, and technology
            # of the current branch being recursively looped through
            if not ft and key in scout_base_defs["bldg types"]:
                # Map building type of current Scout microsegment to building
                # type in the EULP end use shares data; ensure that excluded
                # building types are not processed further
                bt = [b[0] for b in eulp_map_dat[
                    "bldg types"].items() if (
                        key not in excl["bldg"] and key in b[1])]
                if len(bt) != 0:
                    bt = bt[0]
                else:
                    bt = ""
            elif key in scout_base_defs["fuels"]:
                # Map fuel type of current Scout microsegment to building
                # type in the EULP end use shares data
                ft = key
            elif key in scout_base_defs["end uses"]:
                # Set Scout end use check conditionally based on building type
                if bt == "res":
                    eulp_eu_map = eulp_map_dat["res end uses"]
                else:
                    eulp_eu_map = eulp_map_dat["com end uses"]
                # Map end use of current Scout microsegment to end use
                # in the EULP end use shares data; ensure that excluded
                # end uses are not processed further
                eu = [e[0] for e in eulp_eu_map.items() if (
                    key not in excl["euses"] and (
                        (key != "other" and key in e[1]) or
                        (key == "other" and any([key in i for i in e[1]]))))]
                if len(eu) == 0:
                    eu = ""
            elif key in ["supply", "demand"]:
                # Flag envelope data ("demand" technology type)
                tt = key
            elif key in ["stock", "energy"]:
                # Flag stock vs. energy data
                vt = key
            if any([x in value.keys() for x in ["stock", "energy"]]):
                # Ensure that excluded technologies are not processed further
                if key not in excl["tech"]:
                    tc = key
            # Reset microsegment branch data to mapped information pulled above
            branch_dat = {"fuel": ft, "bldg": bt, "end use": eu,
                          "tech type": tt, "tech": tc, "value type": vt}
            # Continue the recursive loop
            process_branches(
                adj_dct, tot_dct, value, yr_calibrate, eulp_map_dat,
                scout_base_defs, branch_dat, excl, operation)


def main():
    """Import external data files, process data, and produce desired output.

    This function calls the required external data, both the data to be
    converted from a census division to a custom region basis, as well
    as the applicable conversion factors.

    Because the conversion factors for the energy, stock, and square
    footage data are slightly different than the factors for the cost,
    performance, and lifetime data, when the script is run, this
    function requests user input to determine the appropriate files
    to import.
    """

    # Obtain user input regarding what data are to be processed. Include two
    # stages of input: one determining whether stock and energy data or cost/
    # performance/lifetime data are to be converted, and another determining
    # the regional breakdown to use in converting the data
    input_var = [0, 0]
    # Determine the type of data (stock/energy (1) or cost/perf/life (2))
    while input_var[0] not in ['1', '2']:
        input_var[0] = input(
            "Enter 1 for energy, stock, and square footage" +
            " data\n or 2 for cost, performance, lifetime data: ")
        if input_var[0] not in ['1', '2']:
            print('Please try again. Enter either 1 or 2. Use ctrl-c to exit.')
    # Determine the regional breakdown to use (AIA (1) vs. NEMS EMM (2) vs.
    # state (3))

    # AIA, EMM, or state are possible for stock/energy data
    if input_var[0] == '1':
        while input_var[1] not in ['1', '2', '3']:
            input_var[1] = input(
                "Enter 1 to use an AIA climate zone geographical" +
                " breakdown,\n 2 to use an EIA Electricity Market Module "
                "geographical breakdown,\n or 3 to use a state geographical "
                "breakdown: ")
            if input_var[1] not in ['1', '2', '3']:
                print('Please try again. Enter either 1, 2, or 3. '
                      'Use ctrl-c to exit.')
    # AIA, or EMM are possible for cost/performance/lifetime data
    elif input_var[0] == '2':
        while input_var[1] not in ['1', '2', '3']:
            input_var[1] = input(
                "Enter 1 to use an AIA climate zone geographical" +
                " breakdown,\n 2 to use an EIA Electricity Market Module "
                "geographical breakdown,\n or 3 to use a state geographical "
                "breakdown: ")
            if input_var[1] not in ['1', '2', '3']:
                print('Please try again. Enter either 1, 2, or 3. '
                      'Use ctrl-c to exit.')

    # Instantiate object that contains useful variables
    handyvars = UsefulVars(input_var[1])

    # Based on the first input from the user to indicate what type of data are
    # being processed, assign the object values for its four attributes
    if input_var[0] == '1':
        handyvars.configure_for_energy_square_footage_stock_data()
    elif input_var[0] == '2':
        handyvars.configure_for_cost_performance_lifetime_data()

    # Based on the second input from the user to indicate what regional
    # breakdown to use in converting the data, import necessary conversion data
    if input_var[1] == '1':
        # Import residential census division to AIA climate conversion data
        res_cd_cz_conv = np.genfromtxt(
            handyvars.res_climate_convert, names=True,
            delimiter='\t', dtype="float64")
        # Import commercial census division to AIA climate conversion data
        com_cd_cz_conv = np.genfromtxt(
            handyvars.com_climate_convert, names=True,
            delimiter='\t', dtype="float64")
        env_perf_convert = None
    elif input_var[1] in ['2', '3']:
        # Do not prepare mapping conversions for non-envelope technology
        # characteristics data if a state-level resolution is desired (in this
        # case, these data remain with the original Census breakout)
        if input_var[0] == '1' or (
                input_var[0] == '2' and input_var[1] != '3'):
            # Import residential census division to EMM or state conversion
            # data; import data into a dict that is keyed by fuel type, since
            # separate census to EMM or state conversions are used for
            # different fuels
            res_cd_cz_conv = {
                "electricity": np.genfromtxt(
                    handyvars.res_climate_convert["electricity"], names=True,
                    delimiter='\t', dtype="float64"),
                "natural gas": np.genfromtxt(
                    handyvars.res_climate_convert["natural gas"], names=True,
                    delimiter='\t', dtype="float64"),
                "distillate": np.genfromtxt(
                    handyvars.res_climate_convert["distillate"], names=True,
                    delimiter='\t', dtype="float64"),
                "other fuel": np.genfromtxt(
                    handyvars.res_climate_convert["other fuel"], names=True,
                    delimiter='\t', dtype="float64"),
                "building stock and square footage": np.genfromtxt(
                    handyvars.res_climate_convert[
                        "building stock and square footage"], names=True,
                    delimiter='\t', dtype="float64")}
            # Import commercial census division to EMM or state conversion
            # data; import data into a dict that is keyed by fuel type, since
            # separate census to EMM or state conversions are used for
            # different fuels
            com_cd_cz_conv = {
                "electricity": np.genfromtxt(
                    handyvars.com_climate_convert["electricity"], names=True,
                    delimiter='\t', dtype="float64"),
                "natural gas": np.genfromtxt(
                    handyvars.com_climate_convert["natural gas"], names=True,
                    delimiter='\t', dtype="float64"),
                "distillate": np.genfromtxt(
                    handyvars.com_climate_convert["distillate"], names=True,
                    delimiter='\t', dtype="float64"),
                "building stock and square footage": np.genfromtxt(
                    handyvars.com_climate_convert[
                        "building stock and square footage"], names=True,
                    delimiter='\t', dtype="float64")}
        # For EMM region data only, import data used to reallocate final end
        # use shares on the basis of the End Use Load Profiles library
        if (input_var[0] == '1' and input_var[1] == '2'):
            eu_pp = pd.read_csv(handyvars.eulp_post)

        # Import data needed to convert envelope performance data from an
        # AIA climate zone to EMM region breakdown
        if input_var[0] == '2':
            env_perf_convert = np.genfromtxt(
                handyvars.envelope_climate_convert, names=True,
                delimiter='\t', dtype="float64")

    # Import metadata generated based on EIA AEO data files
    with open(handyvars.aeo_metadata, 'r') as metadata:
        metajson = json.load(metadata)

    # Define years vector using year data from metadata
    years = list(range(metajson['min year'], metajson['max year'] + 1))

    # Open the microsegments JSON file that has data on a census
    # division basis and traverse the database to convert it to
    # a custom region basis
    with open(handyvars.json_in, 'r') as jsi:
        msjson_cdiv = json.load(jsi)
        # Do not convert non-envelope technology characteristics data to a
        # state-level resolution (these data remain with the original
        # Census breakout)
        if input_var[0] == '1' or (
                input_var[0] == '2' and input_var[1] != '3'):
            # Convert data
            result = clim_converter(
                msjson_cdiv, res_cd_cz_conv, com_cd_cz_conv, input_var[0])
        else:
            result = msjson_cdiv

        # If cost, performance, and lifetime data are indicated based
        # on user input, open the envelope cost, performance, and
        # lifetime database and the cost conversion factors database,
        # then add those data to the microsegments data that were just
        # converted to a custom region basis
        if input_var[0] == '2':
            with open(handyvars.addl_cpl_data, 'r') as jscpl, open(
                    handyvars.conv_factors, 'r') as jsconv:
                jscpl_data = json.load(jscpl)
                jsconv_data = json.load(jsconv)

                # Add envelope components' cost, performance and
                # lifetime data to the result dict
                result = walk(
                    jscpl_data, jsconv_data, env_perf_convert, years, result)

    # For EMM data, run a final post-processing step on the data to
    # calibrate regional electricity end use shares to the End Use Load
    # Profiles library
    if (input_var[0] == '1' and input_var[1] == '2'):
        result = finalize_eu_shares(result, eu_pp, years)

    # Write the updated dict of data to a new JSON file
    with open(handyvars.json_out, 'w') as jso:
        json.dump(result, jso, indent=2)
        # Compress CPL file
        if handyvars.json_out.startswith('cpl'):
            zip_out_cpl = handyvars.json_out.split('.')[0] + '.gz'
            with gzip.GzipFile(zip_out_cpl, 'w') as fout_cpl:
                fout_cpl.write(json.dumps(result).encode('utf-8'))
        # Compress stock/energy EMM and state files
        if handyvars.json_out in [
                'mseg_res_com_state.json', 'mseg_res_com_emm.json']:
            zip_out_se = handyvars.json_out.split('.')[0] + '.gz'
            with gzip.GzipFile(zip_out_se, 'w') as fout_se:
                fout_se.write(json.dumps(result).encode('utf-8'))


if __name__ == '__main__':
    main()
