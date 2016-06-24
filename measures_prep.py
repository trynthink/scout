#!/usr/bin/env python3
import xlrd
import numpy
import re
import itertools
import json
from collections import OrderedDict
from os import listdir, getcwd
from os.path import isfile, join
import copy
import sys


class UsefulInputFiles(object):
    """Class of input files to be opened by this routine.

    Attributes:
        measures_in (JSON): A database of initial measure definitions.
        msegs_in (JSON): A database of baseline microsegment stock/energy.
        msegs_cpl_in (JSON): A database of baseline technology characteristics.
        packages_in (JSON): A database of measure names to package.
    """

    def __init__(self):
        self.measures_in = "measures_test.json"
        self.msegs_in = "mseg_res_com_cz.json"
        self.msegs_cpl_in = "cpl_res_com_cz.json"
        self.packages_in = "measure_packages_test.json"


class UsefulVars(object):
    """Class of variables that are used globally across functions.

    Attributes:
        discount_rate (float): Rate to use in discounting costs/savings.
        retro_rate (float): Rate at which existing stock is retrofitted.
        aeo_years (list) = Modeling time horizon.
        inverted_relperf_list (list) = Performance units that require
            an inverted relative performance calculation (e.g., an air change
            rate where lower numbers indicate higher performance).
        valid_submkt_urls (list) = Valid URLs for sub-market scaling fractions.
        ss_conv (dict): Site-source conversion factors by fuel type.
        carb_int (dict): Carbon intensities by fuel type.
        ecosts (dict): Energy costs by building and fuel type.
        ccosts (dict): Carbon costs.
        com_timeprefs (dict): Commercial adoption time preference premiums.
        out_break_in (dict): Breakouts of measure energy/carbon markets/savings
            for eventual use in plotting of analysis results.
    """

    def __init__(self):
        self.discount_rate = 0.07
        self.retro_rate = 0.02
        # Set minimum AEO modeling year
        aeo_min = 2009
        # Set maximum AEO modeling year
        aeo_max = 2040
        # Derive time horizon from min/max years
        self.aeo_years = [
            str(i) for i in range(aeo_min, aeo_max + 1)]
        self.inverted_relperf_list = [
            "ACH50", "CFM/sf floor", "kWh/yr", "kWh/day", "SHGC", "HP/CFM"]
        self.valid_submkt_urls = [
            '.eia.gov', '.doe.gov', '.energy.gov', '.data.gov',
            '.energystar.gov', '.epa.gov', '.census.gov', '.pnnl.gov',
            '.lbl.gov', '.nrel.gov', 'www.sciencedirect.com', 'www.costar.com',
            'www.navigantresearch.com']
        #######################################################################
        # MAKE RES/COM MSEG ELECTRICITY DEFINITIONS CONSISTENT
        cost_ss_carb = numpy.genfromtxt(
            "Cost_S-S_CO2.txt", names=True, delimiter='\t', dtype=None)
        self.ss_conv = {
            "electricity (grid)": cost_ss_carb[7],
            "electricity": cost_ss_carb[7], "natural gas": cost_ss_carb[8],
            "distillate": cost_ss_carb[9], "other fuel": cost_ss_carb[9]}
        self.carb_int = {
            "electricity (grid)": cost_ss_carb[10],
            "electricity": cost_ss_carb[10], "natural gas": cost_ss_carb[11],
            "distillate": cost_ss_carb[12], "other fuel": cost_ss_carb[12]}
        self.ecosts = {
            "residential": {
                "electricity (grid)": cost_ss_carb[0],
                "natural gas": cost_ss_carb[1], "distillate": cost_ss_carb[2],
                "other fuel": cost_ss_carb[2]},
            "commercial": {
                "electricity": cost_ss_carb[3],
                "natural gas": cost_ss_carb[4], "distillate": cost_ss_carb[5],
                "other fuel": cost_ss_carb[5]}}
        ######################################################################
        self.ccosts = cost_ss_carb[6]
        self.com_timeprefs = {
            "rates": [10.0, 1.0, 0.45, 0.25, 0.15, 0.065, 0.0],
            "distributions": {
                "heating": {
                    key: [0.265, 0.226, 0.196, 0.192, 0.105, 0.013, 0.003]
                    for key in self.aeo_years},
                "cooling": {
                    key: [0.264, 0.225, 0.193, 0.192, 0.106, 0.016, 0.004]
                    for key in self.aeo_years},
                "water heating": {
                    key: [0.263, 0.249, 0.212, 0.169, 0.097, 0.006, 0.004]
                    for key in self.aeo_years},
                "ventilation": {
                    key: [0.265, 0.226, 0.196, 0.192, 0.105, 0.013, 0.003]
                    for key in self.aeo_years},
                "cooking": {
                    key: [0.261, 0.248, 0.214, 0.171, 0.097, 0.005, 0.004]
                    for key in self.aeo_years},
                "lighting": {
                    key: [0.264, 0.225, 0.193, 0.193, 0.085, 0.013, 0.027]
                    for key in self.aeo_years},
                "refrigeration": {
                    key: [0.262, 0.248, 0.213, 0.170, 0.097, 0.006, 0.004]
                    for key in self.aeo_years}}}
        # Climate zone breakout mapping
        out_break_czones = OrderedDict([
            ('AIA CZ1', 'AIA_CZ1'), ('AIA CZ2', 'AIA_CZ2'),
            ('AIA CZ3', 'AIA_CZ3'), ('AIA CZ4', 'AIA_CZ4'),
            ('AIA CZ5', 'AIA_CZ5')])
        # Building type breakout mapping
        out_break_bldgtypes = OrderedDict([
            ('Residential', [
                'single family home', 'multi family home', 'mobile home']),
            ('Commercial', [
                'assembly', 'education', 'food sales', 'food service',
                'health care', 'mercantile/service', 'lodging', 'large office',
                'small office', 'warehouse', 'other'])])
        # End use breakout mapping
        out_break_enduses = OrderedDict([
            ('Heating', ["heating", "secondary heating"]),
            ('Cooling', ["cooling"]),
            ('Ventilation', ["ventilation"]),
            ('Lighting', ["lighting"]),
            ('Water Heating', ["water heating"]),
            ('Refrigeration', ["refrigeration", "other (grid electric)"]),
            ('Computers and Electronics', [
                "PCs", "non-PC office equipment", "TVs", "computers"]),
            ('Other', ["cooking", "drying", "MELs", "other (grid electric)"])])
        # Use the above output categories to establish a dictionary with blank
        # values at terminal leaf nodes; this dict will eventually store
        # partitioning fractions needed to breakout the measure results
        # Determine all possible outcome category combinations
        out_levels = [out_break_czones.keys(), out_break_bldgtypes.keys(),
                      out_break_enduses.keys()]
        out_levels_keys = list(itertools.product(*out_levels))
        # Create dictionary using outcome category combinations as key chains
        self.out_break_in = OrderedDict()
        for kc in out_levels_keys:
            current_level = self.out_break_in
            for ind, elem in enumerate(kc):
                if elem not in current_level:
                    current_level[elem] = OrderedDict()
                current_level = current_level[elem]


class EPlusMapDicts(object):
    """Class of dicts used to map Scout measure definitions to EnergyPlus.

    Attributes:
        czone (dict): Scout-EnergyPlus climate zone mapping.
        bldgtype (dict): Scout-EnergyPlus building type mapping.
        fuel (dict): Scout-EnergyPlus fuel type mapping.
        enduse (dict): Scout-EnergyPlus end use mapping.
        structure_type (dict): Scout-EnergyPlus structure type mapping.
    """

    def __init__(self):
        self.czone = {
            "sub arctic": "BA-SubArctic",
            "very cold": "BA-VeryCold",
            "cold": "BA-Cold",
            "marine": "BA-Marine",
            "mixed humid": "BA-MixedHumid",
            "mixed dry": "BA-MixedDry",
            "hot dry": "BA-HotDry",
            "hot humid": "BA-HotHumid"}
        self.bldgtype = {
            'assembly': [
                'PrimarySchool', 'RetailStandalone', 'RetailStripmall',
                'SecondarySchool', 'SmallOffice'],
            'education': ['PrimarySchool', 'SecondarySchool'],
            'food sales': [
                'FullServiceRestaurant', 'QuickServiceRestaurant'],
            'food service': ['Supermarket'],
            'health care': ['Hospital'],
            'mercantile/service': ['RetailStandalone', 'RetailStripmall'],
            'lodging': ['LargeHotel', 'SmallHotel'],
            'multi family home': ['HighRiseApartment', 'MidriseApartment'],
            'large office': ['LargeOffice', 'MediumOffice'],
            'small office': ['MediumOffice', 'SmallOffice'],
            'warehouse': ['Warehouse'],
            'other': ['LargeOffice', 'SmallHotel', 'Warehouse']}
        self.fuel = {
            'electricity': 'Electricity',
            'natural gas': 'Gas',
            'distillate': 'Other Fuel'}
        self.enduse = {
            'heating': [
                'Heating Electricity', 'Heat Recovery Electricity',
                'Pump Electricity', 'Heating Gas',
                'Heating Other Fuel'],
            'cooling': [
                'Cooling Electricity', 'Humidification Electricity',
                'Heat Recovery Electricity', 'Heat Rejection Electricity',
                'Pump Electricity'],
            'water heating': [
                'Service Water Heating Electricity',
                'Service Water Heating Gas',
                'Service Water Heating Other Fuel'],
            'ventilation': ['Fan Electricity'],
            'cooking': [
                'Interior Equipment Gas', 'Interior Equipment Other Fuel'],
            'lighting': ['Interior Lighting Electricity'],
            'refrigeration': ['Refrigeration Electricity'],
            'PCs': ['Interior Equipment Electricity'],
            'non-PC office equipment': ['Interior Equipment Electricity'],
            'MELs': ['Interior Equipment Electricity']}
        # Note: assumed year range for each structure vintage shown in lists
        self.structure_type = {
            "new": '90.1-2013',
            "retrofit": {
                '90.1-2004': [2004, 2006],
                '90.1-2007': [2007, 2009],
                '90.1-2010': [2010, 2012],
                'DOE Ref 1980-2004': [1980, 2003],
                'DOE Ref Pre-1980': [0, 1979]}}


class EPlusGlobals(object):
    """Class of global variables used in parsing EnergyPlus results file.

    Attributes:
        eplus_dir (string): Directory for EnergyPlus simulation output files.
        cbecs_sh (xlrd sheet object): CBECs square footages Excel sheet.
        vintage_sf (dict): Summary of CBECs square footages by vintage.
        eplus_perf_files (list): EnergyPlus simulation output file names.
        eplus_vintages (list): EnergyPlus building vintage types.
        eplus_vintage_weights (dicts): Square-footage-based weighting factors
            for EnergyPlus vintages.
    """

    def __init__(self, argv):
        # Set local directory for EnergyPlus measure performance files
        self.eplus_dir = argv
        # Import CBECs XLSX
        cbecs_in = "b34.xlsx"
        cbecs = xlrd.open_workbook(self.eplus_dir + '/' + cbecs_in)
        self.cbecs_sh = cbecs.sheet_by_index(0)
        # Pull out building vintage square footage data
        self.vintage_sf = self.cbecs_vintage_sf()
        # Set EnergyPlus data file name list, given local directory
        self.eplus_perf_files = [
            f for f in listdir(self.eplus_dir) if
            isfile(join(self.eplus_dir, f)) and f != cbecs_in and 'xlsx' in f]
        # Import first EnergyPlus measure performance XLSX
        eplus_file = xlrd.open_workbook(
            self.eplus_dir + '/' + self.eplus_perf_files[0])
        eplus_file_sh = eplus_file.sheet_by_index(2)
        # Determine appropriate weights for mapping EnergyPlus vintages to the
        # 'new' and 'retrofit' building structure types of Scout
        self.eplus_vintages = numpy.unique(
            [eplus_file_sh.cell(x, 2).value for x in range(
                1, eplus_file_sh.nrows)])
        self.eplus_vintage_weights = self.find_vintage_weights()

    def cbecs_vintage_sf(self):
        """Import commercial floorspace data from CBECs raw data file.

        Note:
            The name of the CBECs file used is 'b34.xlsx'. This file
            includes floorspace data broken down by building vintage bin.

        Returns:
            Square footages by CBECs building vintage group.

        Raises:
            ValueError: If no rows from CBECs sheet are read in.
        """
        # Initialize a dictionary for the cbecs vintage square footages
        vintage_sf = {}
        # Initialize a flag for the first relevant row in the cbecs Excel sheet
        start_row_flag = 0

        # Loop through all rows in the Excel sheet, and pull out sq.ft. data
        for i in range(self.cbecs_sh.nrows):
            # Check for a string that indicates the start of the sq.ft. data
            # rows
            if self.cbecs_sh.cell(i, 0).value == "Year constructed":
                start_row_flag = 1
            # Check for a string that indicates the end of sq.ft. data rows
            # (break)
            elif self.cbecs_sh.cell(i, 0).value == \
                    "Census region and division":
                break
            # If start row flag hasn't been raised, skip row
            elif start_row_flag == 0:
                continue
            # If start row flag has been raised, read in sq.ft. data from row
            else:
                vintage_bin = self.cbecs_sh.cell(i, 0).value
                sf_val = self.cbecs_sh.cell(i, 6).value
                vintage_sf[vintage_bin] = sf_val

        if start_row_flag == 0:
            raise ValueError('Problem reading in the cbecs sq.ft. data!')

        return vintage_sf

    def find_vintage_weights(self):
        """Find square-footage-based weighting factors for building vintages.

        Note:
            Use CBECs building vintage square footage data to derive weighting
            factors that will map the EnergyPlus building vintages to the 'new'
            and 'retrofit' building structure types of Scout.

        Returns:
            Weights needed to map each EnergyPlus vintage category to the 'new'
            and 'retrofit' structure types defined in Scout.

        Raises:
            ValueError: If vintage weights do not sum to 1.
            KeyError: If unexpected vintage names are discovered in the
                EnergyPlus file.
        """
        eplsdicts = EPlusMapDicts()

        # Set the expected names of the EnergyPlus building vintages and the
        # low and high year limits of each building vintage category
        expected_eplus_vintage_yr_bins = [
            eplsdicts.structure_type['new']] + \
            list(eplsdicts.structure_type['retrofit'].keys())
        # Initialize a variable meant to translate the summed square footages
        # of multiple 'retrofit' building vintages into weights that sum to 1;
        # also initialize a variable used to check that these weights indeed
        # sum to 1
        total_retro_sf, retro_weight_sum = (0 for n in range(2))

        # Check for expected EnergyPlus vintage names
        if sorted(self.eplus_vintages) == sorted(
                expected_eplus_vintage_yr_bins):
            # Initialize a dictionary with the EnergyPlus vintages as keys and
            # associated square footage values starting at zero
            eplus_vintage_weights = dict.fromkeys(self.eplus_vintages, 0)

            # Loop through the EnergyPlus vintages and assign associated
            # weights by mapping to cbecs square footage data
            for k in eplus_vintage_weights.keys():
                # If looping through the EnergyPlus vintage associated with the
                # 'new' Scout structure type, set vintage weight to 1 (only one
                # vintage category will be associated with this structure type)
                if k == eplsdicts.structure_type['new']:
                    eplus_vintage_weights[k] = 1
                # Otherwise, set EnergyPlus vintage weight initially to the
                # square footage that corresponds to that vintage in cbecs
                else:
                    # Loop through all cbecs vintage bins
                    for k2 in self.vintage_sf.keys():
                        # Find the limits of the cbecs vintage bin
                        cbecs_match = re.search(
                            '(\D*)(\d*)(\s*)(\D*)(\s*)(\d*)', k2)
                        cbecs_t1 = cbecs_match.group(2)
                        cbecs_t2 = cbecs_match.group(6)
                        # Handle a 'Before Year X' case in cbecs (e.g., 'Before
                        # 1920'),  setting the lower year limit to zero
                        if cbecs_t2 == '':
                            cbecs_t2 = 0
                        # Determine a single average year that represents the
                        # current cbecs vintage bin
                        cbecs_yr = (int(cbecs_t1) + int(cbecs_t2)) / 2
                        # If the cbecs bin year falls within the year limits of
                        # the current EnergyPlus vintage bin, add the
                        # associated cbecs sq.ft. data to the EnergyPlus
                        # vintage weight value
                        if cbecs_yr >= eplsdicts.structure_type[
                            'retrofit'][k][0] and \
                           cbecs_yr < eplsdicts.structure_type[
                           'retrofit'][k][1]:
                            eplus_vintage_weights[k] += self.vintage_sf[k2]
                            total_retro_sf += self.vintage_sf[k2]

            # Run through all EnergyPlus vintage weights, normalizing the
            # square footage-based weights for each 'retrofit' vintage to the
            # total square footage across all 'retrofit' vintage categories
            for k in eplus_vintage_weights.keys():
                # If running through the 'new' EnergyPlus vintage bin, register
                # the value of its weight (should be 1)
                if k == eplsdicts.structure_type['new']:
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
            raise KeyError(
                'Unexpected EnergyPlus vintage(s)! '
                'Check EnergyPlus vintage assumptions in structure_type '
                'attribute of EPlusMapDict object.')

        return eplus_vintage_weights


class Measure(object):
    """Set up a class representing efficiency measures as objects.

    Attributes:
        **kwargs: Arbitrary keyword arguments used to fill measure attributes.
        mkts_savings (dict): Measure total stock, stock cost, energy/carbon
            markets, and associated energy, carbon, and cost savings.
    """

    def __init__(self, **kwargs):
        # Read Measure object attributes from measures input JSON.
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.mkts_savings = {
            "master_mseg": {}, "mseg_adjust": {}, "mseg_out_break": {},
            "master_savings": {}}

    def translate_costs_res(self):
        """Convert residential measure cost input to the proper units.

        Returns:
            Updated measure costs in either $/unit or $/sf floor.
        """
        # Set dummy variable values to check for execution of this function
        self.installed_cost = 999
        self.cost_units = "2013$/sf floor"

    def translate_costs_com(self):
        """Convert commercial measure cost input to the proper units.

        Returns:
            Updated measure costs in $/sf floor.
        """
        # Set dummy variable values to check for execution of this function
        self.installed_cost = 9999
        self.cost_units = "2013$/sf floor"

    def fill_eplus(self, msegs, eplus_dir, eplus_files, vintage_weights):
        """Fill in measure performance with EnergyPlus simulation results.

        Note:
            Find the appropriate set of EnergyPlus simulation results for
            the current measure, and use the relative savings percentages
            in these results to determine the measure performance attribute.

        Args:
            msegs (dict): Dictionary of baseline microsegments to use in
                validating categorization of measure performance information.
            eplus_dir (string): Directory of EnergyPlus performance files.
            eplus_files (list): EnergyPlus performance file names.
            vintage_weights (dict): Square-footage-derived weighting factors
                for each EnergyPlus building vintage type.

        Returns:
            Updated Measure energy_efficiency, energy_efficiency_source, and
            energy_efficiency_source attribute values.

        Raises:
            ValueError: If EnergyPlus file is not matched to Measure
                definition or more than one EnergyPlus file matches the
                Measure definition.
        """
        # Determine the appropriate EnergyPlus input XLSX file name
        eplus_perf_in = [x for x in eplus_files if
                         x == self.energy_efficiency['EnergyPlus file']]
        # Import EnergyPlus input XLSX and translate to structured
        # array for future operations
        if len(eplus_perf_in) == 1:
            eplus_file = xlrd.open_workbook(
                eplus_dir + '/' + eplus_perf_in[0])
            eplus_file_sh = eplus_file.sheet_by_index(2)
            # Convert Excel sheet data into numpy array
            eplus_perf_array = self.convert_to_array(eplus_file_sh)
            # Create a measure performance dictionary, zeroed out, to
            # be updated with information from EnergyPlus outputs
            perf_dict_empty = self.create_perf_dict(msegs)

            # Update measure performance based on EnergyPlus data
            # (* Note: only update efficiency information for
            # secondary microsegments if applicable)
            if perf_dict_empty['secondary'] is not None:
                self.energy_efficiency = self.fill_perf_dict(
                    perf_dict_empty, eplus_perf_array,
                    vintage_weights)
            else:
                self.energy_efficiency = self.fill_perf_dict(
                    perf_dict_empty['primary'], eplus_perf_array,
                    vintage_weights)
            # Set the energy efficiency data source for the measure to
            # EnergyPlus and set to highest data quality rating
            self.energy_efficiency_source = 'EnergyPlus/OpenStudio'
            self.energy_efficiency_source_quality = 5
        elif len(eplus_perf_in) > 1:
            raise ValueError('> 1 applicable eplus file for measure!')
        else:
            raise ValueError(
                'Failure to match measure name to eplus files!')

    def fill_mkts(self, msegs, msegs_cpl):
        """Fill in measure markets/savings using EIA baseline data.

        Args:
            msegs (dict): Dictionary of baseline microsegment stock
                and energy use information.
            msegs_cpl (dict): Dictionary of baseline technology cost,
                performance, and lifetime information.

        Returns:
            Updated measure total stock, stock cost, and energy/carbon market
            information, as stored in the 'mkts_savings' attribute.
        """
        # Set dummy variable values to check for execution of this function
        self.mkts_savings["master_mseg"] = 999
        self.mkts_savings["mseg_adjust"] = 999
        self.mkts_savings["mseg_out_break"] = 999
        self.status['update'] = False

    def fill_perf_dict(
            self, perf_dict, eplus_perf_array, vintage_weights):
        """Fill an empty dict with updated measure performance information.

        Note:
            Use data from an EnergyPlus output file and building type/vintage
            weighting data to fill a dictionary of final measure performance
            information.

        Args:
            perf_dict (dict): Empty dictionary to fill with EnergyPlus-based
                performance information broken down by climate zone, building
                type/vintage, fuel type, and end use.
            eplus_perf_array (numpy recarray): Structured array of EnergyPlus
                energy savings information for the Measure.
            vintage_weights (dict): Square-footage-derived weighting factors
                for each EnergyPlus building vintage type.

        Returns:
            A measure performance dictionary filled with relative energy
            savings values from an EnergyPlus simulation output file.

        Raises:
            KeyError: If an EnergyPlus category name cannot be mapped to the
                input perf_dict keys.
        """
        # Copy eplus_perf_array
        reduce_array = copy.deepcopy(eplus_perf_array)

        # Instantiate useful EnergyPlus-Scout mapping dicts
        handydicts = EPlusMapDicts()

        # Set the header of the EnergyPlus input array (used when reducing
        # columns of the array to the specific performance categories being
        # updated below)
        eplus_header = list(reduce_array.dtype.names)

        # Loop through zeroed out measure performance dictionary input and
        # update the values with data from the EnergyPlus input array
        for key, item in perf_dict.items():
            # If current dict item is itself a dict, reduce EnergyPlus array
            # based on the current dict key and proceed further down the dict
            # levels
            if isinstance(item, dict):
                # Microsegment type level (no update to EnergyPlus array
                # required)
                if key in ['primary', 'secondary']:
                    updated_perf_array = reduce_array
                # Climate zone level
                elif key in handydicts.czone.keys():
                    # Reduce EnergyPlus array to only rows with climate zone
                    # currently being updated in the performance dictionary
                    updated_perf_array = reduce_array[numpy.where(
                        reduce_array[
                            'Climate Zone'] == handydicts.czone[key])].copy()
                    if len(updated_perf_array) == 0:
                        raise ValueError('eplus climate zone name not found!')
                # Building type level
                elif key in handydicts.bldgtype.keys():
                    # Reduce EnergyPlus array to only rows with building type
                    # currently being updated in the performance dictionary
                    updated_perf_array = reduce_array[numpy.in1d(
                        reduce_array[
                            'Building Type'], handydicts.bldgtype[key])].copy()
                    if len(updated_perf_array) == 0:
                        raise ValueError('eplus building type name not found!')
                # Fuel type level
                elif key in handydicts.fuel.keys():
                    # Reduce EnergyPlus array to only columns with fuel type
                    # currently being updated in the performance dictionary.
                    colnames = eplus_header[0:3]
                    colnames.extend([
                        x for x in eplus_header if handydicts.fuel[key] in x])
                    if len(colnames) == 3:
                        raise ValueError('eplus fuel type name not found!')
                    updated_perf_array = reduce_array[colnames].copy()
                # End use level
                elif key in handydicts.enduse.keys():
                    # Reduce EnergyPlus array to only columns with end use
                    # currently being updated in the performance dictionary.
                    colnames = eplus_header[0:3]
                    colnames.extend([
                        x for x in eplus_header if x in handydicts.enduse[
                            key]])
                    if len(colnames) == 3:
                        raise ValueError('eplus end use name not found!')
                    updated_perf_array = reduce_array[colnames].copy()
                else:
                    raise KeyError(
                        'Invalid measure performance dictionary key!')

                # Given updated EnergyPlus array, proceed further down the
                # dict level hierarchy
                self.fill_perf_dict(
                    item, updated_perf_array, vintage_weights)
            else:
                # Reduce EnergyPlus array to only rows with structure type
                # currently being updated in the performance dictionary
                # ('new' or 'retrofit')
                if key in handydicts.structure_type.keys():
                    # A 'new' structure type will match only one of the
                    # EnergyPlus building vintage names
                    if key == "new":
                        updated_perf_array = reduce_array[numpy.where(
                            reduce_array['Template'] ==
                            handydicts.structure_type['new'])].copy()
                    # A 'retrofit' structure type will match multiple
                    # EnergyPlus building vintage names
                    else:
                        updated_perf_array = reduce_array[numpy.in1d(
                            reduce_array['Template'], list(
                                handydicts.structure_type[
                                    'retrofit'].keys()))].copy()
                    if len(updated_perf_array) == 0 or \
                       (key == "new" and
                        len(numpy.unique(updated_perf_array[
                            'Template'])) != 1 or key == "retrofit" and
                        len(numpy.unique(updated_perf_array[
                            'Template'])) != len(
                            handydicts.structure_type["retrofit"].keys())):
                        raise ValueError(
                            'eplus vintage name not found in data file!')
                else:
                    raise KeyError(
                        'Invalid measure performance dictionary key!')

                # Initialize the final relative savings value for the current
                # measure performance dictionary branch as 0
                end_key_val = 0

                # Update building type weight to account for cases where
                # multiple eplus building types map to one Scout building type
                # (for now, weight each eplus type evenly)
                eplus_bldg_type_weight = 1 / \
                    len(numpy.unique(updated_perf_array['Building Type']))

                # Weight and combine the relative savings values left in the
                # EnergyPlus array to arrive at the final measure relative
                # savings value for the current dictionary branch
                for r in updated_perf_array:
                    for n in eplus_header:
                        if r[n].dtype.char != 'S' and r[n].dtype.char != 'U':
                            r[n] = r[n] * eplus_bldg_type_weight * \
                                vintage_weights[
                                r['Template'].copy()]
                            end_key_val += r[n]

                # Update the current dictionary branch value to the final
                # relative savings value derived above
                perf_dict[key] = round(end_key_val, 3)

        return perf_dict

    def create_perf_dict(self, msegs):
        """Create dict to fill with updated measure performance information.

        Note:
            Given a measure's applicable climate zone, building type,
            structure type, fuel type, and end use, create a dict of zeros
            with a hierarchy that is defined by these measure properties.

        Args:
            msegs (dict): Dictionary of baseline microsegment stock and
                energy use information to use in validating categorization of
                measure performance information.

        Returns:
            Empty dictionary to fill with EnergyPlus-based performance
            information broken down by climate zone, building type/vintage,
            fuel type, and end use.
        """
        # Initialize performance dict
        perf_dict_empty = {"primary": None, "secondary": None}
        # Create primary dict structure from baseline market properties
        perf_dict_empty["primary"] = self.create_nested_dict(
            msegs, "primary")

        # Create secondary dict structure from baseline market properties
        # (if needed)
        if all([x is not None for x in [
                self.fuel_type["secondary"], self.end_use["secondary"],
                self.technology_type["secondary"],
                self.technology["secondary"]]]):
            perf_dict_empty["secondary"] = self.create_nested_dict(
                msegs, "secondary")

        return perf_dict_empty

    def create_nested_dict(self, msegs, mseg_type):
        """Create a nested dictionary based on a pre-defined branch structure.

        Note:
            Create a nested dictionary with a structure that is defined by a
            measure's applicable baseline market, with end leaf node values set
            to zero.

        Args:
            msegs (dict): Dictionary of baseline microsegment stock and
                energy use information to use in validating categorization of
                measure performance information.
            mseg_type (string): Primary or secondary microsegment type flag.

        Returns:
            Nested dictionary of zeros with desired branch structure.
        """
        # Initialize output dictionary
        output_dict = {}
        # Establish levels of the dictionary key hierarchy from measure's
        # applicable baseline market information
        keylevels = [
            self.climate_zone, self.bldg_type, self.fuel_type[mseg_type],
            self.end_use[mseg_type], self.structure_type]
        # Find all possible dictionary key chains from the above key level
        # info.
        dict_keys = list(itertools.product(*keylevels))
        # Remove all natural gas cooling key chains (EnergyPlus output
        # files do not include a column for natural gas cooling)
        dict_keys = [x for x in dict_keys if not(
            'natural gas' in x and 'cooling' in x)]

        # Use an input dictionary with valid baseline microsegment information
        # to check that each of the microsegment key chains generated above is
        # valid for the current measure; if not, remove each invalid key chain
        # from further operations

        # Initialize a list of valid baseline microsegment key chains for the
        # measure
        dict_keys_fin = []
        # Loop through the initial set of candidate key chains generated above
        for kc in dict_keys:
            # Copy the input dictionary containing valid key chains
            dict_check = copy.deepcopy(msegs)
            # Loop through all keys in the candidate key chain and move down
            # successive levels of the input dict until either the end of the
            # key chain is reached or a key is not found in the list of valid
            # keys for the current input dict level. In the former case, the
            # resultant dict will point to all technologies associated with the
            # current key chain (e.g., ASHP, LFL, etc.) If none of these
            # technologies are found in the list of technologies covered by the
            # measure, the key chain is deemed invalid
            for ind, key in enumerate(kc):
                # If key is found in the list of valid keys for the current
                # input microsegment dict level, move on to next level in the
                # dict; otherwise, break the current loop
                if key in dict_check.keys():
                    dict_check = dict_check[key]
                    # In the case of heating or cooling end uses, an additional
                    # 'technology type' key must be accounted for ('supply' or
                    # 'demand')
                    if key in ['heating', 'cooling']:
                        dict_check = \
                            dict_check[self.technology_type[mseg_type]]
                else:
                    break

            # If any of the technology types listed in the measure definition
            # are found in the keys of the dictionary yielded by the above
            # loop, add the key chain to the list that is used to define the
            # final nested dictionary output (e.g., the key chain is valid)
            if any([x in self.technology[mseg_type]
                   for x in dict_check.keys()]):
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

        return output_dict

    def convert_to_array(self, eplus_perf_sh):
        """Convert a sheet from an XLSX file to a structured array.

        Args:
            eplus_perf_sh (xlrd sheet object): XLSX sheet of EnergyPlus
                measure relative savings information.

        Returns:
            Structured array of EnergyPlus energy savings information for the
            Measure.
        """
        # Set the XLSX sheet headers
        headers = [str(cell.value) for cell in eplus_perf_sh.row(0)]
        # Initialize list to be converted to structured array
        arr = []

        # Loop through all the rows in the Excel file and append to the
        # list to be converted to the structured array
        for r in range(eplus_perf_sh.nrows)[1:]:
            arr.append([cell.value for cell in eplus_perf_sh.row(r)])

        # Convert the list to the structured array, using column headers
        # as the variable names
        eplus_perf_array = numpy.rec.fromrecords(arr, names=headers)
        # Remove any rows in array that measure does not apply to
        eplus_perf_array = eplus_perf_array[numpy.where(
            eplus_perf_array['Status'] != 'Measure Not Applicable')]

        return eplus_perf_array


def fill_measures(measures, msegs, msegs_cpl, eplus_dir):
    """Fill in any missing efficiency measure attributes.

    Note:
        Given a dict of measure information, determine which measures are
        missing certain attributes; instantiate these measures as Measure
        objects; and fill in the missing attribute information for each
        object.

    Args:
        measures (dict): Attributes for individual efficiency measures.
        msegs (dict): Dictionary of baseline microsegment stock and energy use
            information.
        msegs_cpl (dict): Dictionary of baseline technology cost, performance,
            and lifetime information.
        eplus_dir (string): Directory for EnergyPlus simulation output files to
            use in updating measure performance inputs.

    Returns:
        A list of dicts, each including a finalized set of measure attributes.

    Raises:
        ValueError: If more than one Measure object matches the name of a
            given input efficiency measure.
    """
    # Set a variable to use in determining measure building sector below
    res_bldg = ["single family home", "multi family home", "mobile home"]

    # Determine the subset of measures that are missing certain attribute
    # information and thus need updating
    measures_update = [
        Measure(**m) for m in measures if m['status']['update'] is True or
        'EnergyPlus file' in m['energy_efficiency'].keys() or
        (all([x in res_bldg for x in m['bldg_type']]) and
         all(x not in m['cost_units'] for x in ['$/sf floor', '$/unit'])) or
        (all([x not in res_bldg for x in m['bldg_type']]) and
         '$/sf floor' not in m['cost_units']) or m['mkts_savings'] is None]

    # Determine the subset of above measures in need of updated EnergyPlus-
    # derived relative performance information, and execute the update
    if any(['EnergyPlus file' in m.energy_efficiency.keys() for
            m in measures_update]):
        # Set EnergyPlus global variables
        handyeplusvars = EPlusGlobals(eplus_dir)
        [m.fill_eplus(
            msegs, handyeplusvars.eplus_dir, handyeplusvars.eplus_files,
            handyeplusvars.eplus_vintage_weights) for m in
         measures_update if 'EnergyPlus file' in m.energy_efficiency.keys()]
    # Determine the subset of above measures in need of updated residential
    # cost information, and execute the update
    [m.translate_costs_res() for m in measures_update if (
        all([x in res_bldg for x in m.bldg_type]) and
        all(x not in m.cost_units for x in ['$/sf floor', '$/unit']))]
    # Determine the subset of above measures in need of updated commercial
    # cost information, and execute the update
    [m.translate_costs_com() for m in measures_update if (
        all([x not in res_bldg for x in m.bldg_type]) and
        '$/sf floor' not in m.cost_units)]
    # Update markets/savings information for all objects in 'measures_update'
    [m.fill_mkts(msegs, msegs_cpl) for m in measures_update]

    # Add all updated information to original list of measure dictionaries
    for m in [x for x in measures if x["name"] in [
            y.name for y in measures_update]]:
        m_new = [mn for mn in measures_update if mn.name == m["name"]]
        if len(m_new) == 1:
            m.update(m_new[0].__dict__)
        else:
            raise ValueError('Unique Measures object needed for updates!')

    return measures


def add_packages(packages, measures):
    """Combine multiple measures into a single packaged measure.

    Args:
        packages (dict): Names of packages and measures that comprise them.
        measures (dict): Attributes of individual efficiency measures.

    Returns:
        A dict with packaged measure attributes that can be added to the
        existing measures database.
    """
    pass


def main(argv):
    """Import and finalize measures input data for analysis engine.

    Note:
        Import measures from a JSON, determine which measures
        are in need of an update, and finalize measure cost, performance,
        and markets/savings attributes for those measures.

    Args:
        argv (string): Directory for EnergyPlus simulation data files.

    Returns:
        An finalized measures JSON for use in analysis engine.
    """
    # Instantiate useful input files object
    handyfiles = UsefulInputFiles()

    # Import measures
    with open(handyfiles.measures_in, 'r') as mjs:
        measures = json.load(mjs, object_pairs_hook=OrderedDict)
    # Import measure packages
    with open(handyfiles.packages_in, 'r') as pkg:
        packages = json.load(pkg)
    # Import baseline microsegments
    with open(handyfiles.msegs_in, 'r') as msi:
        msegs = json.load(msi)
    # Import baseline cost, performance, and lifetime data
    with open(handyfiles.msegs_cpl_in, 'r') as bjs:
        msegs_cpl = json.load(bjs)

    # Run through each measure and fill in any missing attributes
    measures = fill_measures(measures, msegs, msegs_cpl, argv)
    # Add measure packages
    if packages:
        measures = add_packages(packages, measures)

    # Write the updated dict of measure performance data over the existing
    # measures JSON file
    with open(handyfiles.measures_in, "w") as jso:
        json.dump(measures, jso, indent=4)

if __name__ == "__main__":
    # Allow either user-defined or standard EnergyPlus performance file
    # directory
    if len(sys.argv) == 2:
        main(sys.argv[1])
    else:
        base_dir = getcwd()
        main(base_dir + "/eplus")
