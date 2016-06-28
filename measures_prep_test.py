#!/usr/bin/env python3

""" Tests for running the EnergyPlus data import """

# Import code to be tested
import measures_prep
# Import needed packages
import unittest
import xlrd
import numpy
import os
from collections import OrderedDict


class CommonMethods(object):
    """Define common methods for use in all tests below."""

    def dict_check(self, dict1, dict2):
        """Check the equality of two dicts.

        Args:
            dict1 (dict): First dictionary to be compared
            dict2 (dict): Second dictionary to be compared

        Raises:
            AssertionError: If dictionaries are not equal.
        """
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)


# Skip this test if running on Travis-CI and print the given skip statement
@unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
                 'External File Dependency Unavailable on Travis-CI')
class EPlusGlobalsTest(unittest.TestCase, CommonMethods):
    """Test 'cbecs_vintage_sf' and 'find_vintage_weights' functions.

    Ensure building vintage square footages are read in properly from a
    cbecs data file and that the proper weights are derived for mapping
    EnergyPlus building vintages to Scout's 'new' and 'retrofit' building
    structure types.

    Attributes:
        eplus_globals_ok (object): EPlusGlobals object with square footage and
            vintage weights attributes to test against expected outputs.
        cbecs_failpath (string): Path to invalid CBECs data file that should
            cause EPlusGlobals object instantiation to fail.
        cbecs_failpath (string): Path to invalid EnergyPlus simulation data
            file that should cause EPlusGlobals object instantiation to fail.
        ok_out_sf (dict): Correct square footage outputs for
            'cbecs_vintage_sf' function given valid inputs.
        ok_out_weights (dict): Correct vintage weights output for
            'find_vintage_weights'function given valid inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables for use across all class functions."""
        base_dir = os.getcwd()
        cls.eplus_globals_ok = measures_prep.EPlusGlobals(
            base_dir + "/ePlus_test_ok")
        cls.cbecs_failpath = base_dir + "/ePlus_test_fail/vintagessf_fail"
        cls.eplus_failpath = base_dir + "/ePlus_test_fail/vintageweights_fail"
        cls.ok_out_sf = {
            '2004 to 2007': 6524.0, '1960 to 1969': 10362.0,
            '1946 to 1959': 7381.0, '1970 to 1979': 10846.0,
            '1990 to 1999': 13803.0, '2000 to 2003': 7215.0,
            'Before 1920': 3980.0, '2008 to 2012': 5726.0,
            '1920 to 1945': 6020.0, '1980 to 1989': 15185.0}
        cls.ok_out_weights = {
            'DOE Ref 1980-2004': 0.42, '90.1-2004': 0.07,
            '90.1-2007': 0.0, '90.1-2010': 0.07,
            'DOE Ref Pre-1980': 0.44, '90.1-2013': 1}

    def test_vintagessf(self):
        """Test cbecs_vintage_sf function given valid inputs.

        Note:
            Ensure correct determination of CBECs square footages by building
            vintage.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.dict_check(
            self.eplus_globals_ok.cbecs_vintage_sf(), self.ok_out_sf)

    def test_vintagessf_fail(self):
        """Test cbecs_vintage_sf function given invalid inputs.

        Note:
            Ensure that a ValueError is raised when no CBECs data are read in.

        Raises:
            AssertionError: If ValueError is not raised.
        """
        with self.assertRaises(ValueError):
            measures_prep.EPlusGlobals(
                self.cbecs_failpath).cbecs_vintage_sf()

    def test_vintageweights(self):
        """Test find_vintage_weights function given valid inputs.

        Note:
            Ensure EnergyPlus building vintage type data are correctly weighted
            by their square footages (derived from CBECs data).

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.dict_check(
            self.eplus_globals_ok.find_vintage_weights(),
            self.ok_out_weights)

    # Test that an error is raised when unexpected eplus vintages are present
    def test_vintageweights_fail(self):
        """Test find_vintage_weights function given invalid inputs.

        Note:
            Ensure that KeyError is raised when an unexpected EnergyPlus
            building vintage is present.

        Raises:
            AssertionError: If KeyError is not raised.
        """
        with self.assertRaises(KeyError):
            measures_prep.EPlusGlobals(
                self.eplus_failpath).find_vintage_weights()


# Skip this test if running on Travis-CI and print the given skip statement
@unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
                 'External File Dependency Unavailable on Travis-CI')
class EPlusUpdateTest(unittest.TestCase, CommonMethods):
    """Test the 'fill_eplus' function and its supporting functions.

    Ensure that the 'convert_to_array' function properly converts an input
    XLSX sheet to a structured array and that the 'create_perf_dict' and
    'fill_perf_dict' functions properly initialize and fill a measure
    performance dictionary with results from an EnergyPlus simulation output
    file.

    Attributes:
        meas (object): Measure object instantiated based on sample_measure_in
            attributes.
        eplus_dir (string): EnergyPlus simulation output file directory.
        mseg_in (dict): Sample baseline microsegment stock/energy data.
        ok_eplus_vintagewts (dict): Sample EnergyPlus vintage weights.
        ok_eplusfiles_in (list): List of EnergyPlus simulation file names.
        ok_perfarray_in (numpy recarray): Valid structured array of
            EnergyPlus-based relative savings data.
        fail_perfarray_in (numpy recarray): Invalid structured array of
            EnergyPlus-based relative savings data (missing certain climate
            zones, building types, and building vintages).
        fail_perfdictempty_in (dict): Invalid empty dictionary to fill with
            EnergyPlus-based performance information broken down by climate
            zone, building type/vintage, fuel type, and end use (dictionary
            includes invalid climate zone key).
        ok_array_type_out (string): The array type that should be yielded by
            'convert_to_array' given valid input.
        ok_array_length_out (int): The array length that should be yielded by
            'convert_to_array' given valid input.
        ok_array_names_out (tuple): Tuple of column names for the recarray that
            should be yielded by 'convert_to_array' given valid input.
        ok_perfdictempty_out (dict): The empty dictionary that should be
            yielded by 'create_perf_dict' given valid inputs.
        ok_perfdictfill_out (dict): The dictionary filled with EnergyPlus-based
            measure performance information that should be yielded by
            'fill_perf_dict' and 'fill_eplus' given valid inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        # Sample measure attributes to use in instantiating Measure object.
        sample_measure_in = OrderedDict([
            ("name", "eplus sample measure 1"),
            ("status", OrderedDict([
                ("active", 1), ("updated", 1)])),
            ("installed_cost", 25),
            ("cost_units", "2014$/unit"),
            ("energy_efficiency", OrderedDict([
                ("EnergyPlus file", "EPlus_test_ok.xlsx")])),
            ("energy_efficiency_units", OrderedDict([
                ("primary", "relative savings (constant)"),
                ("secondary", "relative savings (constant)")])),
            ("market_entry_year", None),
            ("market_exit_year", None),
            ("product_lifetime", 10),
            ("structure_type", ["new", "retrofit"]),
            ("bldg_type", ["assembly", "education"]),
            ("climate_zone", ["hot dry", "mixed humid"]),
            ("fuel_type", OrderedDict([
                ("primary", ["electricity"]),
                ("secondary", [
                    "electricity", "natural gas", "distillate"])])),
            ("fuel_switch_to", None),
            ("end_use", OrderedDict([
                ("primary", ["lighting"]),
                ("secondary", ["heating", "cooling"])])),
            ("technology_type", OrderedDict([
                ("primary", "supply"),
                ("secondary", "demand")])),
            ("technology", OrderedDict([
                ("primary", [
                    "technology A", "technology B", "technology C"]),
                ("secondary", ["windows conduction", "windows solar"])]))])
        cls.meas = measures_prep.Measure(**sample_measure_in)
        # Base directory for EnergyPlus files
        base_dir = os.getcwd()
        cls.eplus_dir = base_dir + "/ePlus_test_ok"
        cls.mseg_in = {
            'hot dry': {
                'education': {
                    'electricity': {
                        'lighting': {
                            "technology A": 0,
                            "technology B": 0,
                            "technology C": 0},
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}},
                        'cooling': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}},
                    'natural gas': {
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}},
                        'cooling': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}},
                    'distillate': {
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}}},
                'assembly': {
                    'electricity': {
                        'lighting': {
                            "technology A": 0,
                            "technology B": 0,
                            "technology C": 0},
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}},
                        'cooling': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}},
                    'natural gas': {
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}},
                        'cooling': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}},
                    'distillate': {
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}}}},
            'mixed humid': {
                'education': {
                    'electricity': {
                        'lighting': {
                            "technology A": 0,
                            "technology B": 0,
                            "technology C": 0},
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}},
                        'cooling': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}},
                    'natural gas': {
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}},
                        'cooling': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}},
                    'distillate': {
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}}},
                'assembly': {
                    'electricity': {
                        'lighting': {
                            "technology A": 0,
                            "technology B": 0,
                            "technology C": 0},
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}},
                        'cooling': {
                            'supply': {
                                'ASHP': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}},
                    'natural gas': {
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}},
                        'cooling': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}},
                    'distillate': {
                        'heating': {
                            'supply': {
                                'technology A': 0},
                            'demand': {
                                'windows conduction': 0,
                                'windows solar': 0}}}}}}
        # Set EnergyPlus building vintage weights (based on square footage)
        cls.ok_eplus_vintagewts = {
            'DOE Ref Pre-1980': 0.44, '90.1-2004': 0.07, '90.1-2010': 0.07,
            '90.1-2013': 1, 'DOE Ref 1980-2004': 0.42, '90.1-2007': 0}
        cls.ok_eplusfiles_in = [
            "EPlus_test_ok.xlsx", "samplefile2.xlsx", "samplefile3.xlsx"]
        # Set the name of the EnergyPlus file associated with sample measure
        eplus_file = xlrd.open_workbook(
            cls.eplus_dir + '/' +
            cls.meas.energy_efficiency["EnergyPlus file"])
        eplus_file_sh = eplus_file.sheet_by_index(2)
        cls.ok_perfarray_in = cls.meas.convert_to_array(eplus_file_sh)
        cls.fail_perfarray_in = numpy.rec.array([
            ('BA-MixedHumid', 'SecondarySchool', '90.1-2013', 'Success',
             0, 0.5, 0.5, 0.25, 0.25, 0, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
            ('BA-HotDry', 'PrimarySchool', 'DOE Ref 1980-2004', 'Success',
             0, 0.5, 0.5, 0.25, 0.25, 0, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2)],
            dtype=[('Climate Zone', '<U13'), ('Building Type', '<U22'),
                   ('Template', '<U17'), ('Status', 'U7'),
                   ('Floor Area', '<f8'),
                   ('Total Site Electricity', '<f8'),
                   ('Net Site Electricity', '<f8'),
                   ('Total Gas', '<f8'), ('Total Other Fuel', '<f8'),
                   ('Total Water', '<f8'), ('Net Water', '<f8'),
                   ('Interior Lighting Electricity', '<f8'),
                   ('Interior Equipment Electricity', '<f8'),
                   ('Heating Electricity', '<f8'),
                   ('Cooling Electricity', '<f8'),
                   ('Heating Gas', '<f8'),
                   ('Heat Recovery Electricity', '<f8')])
        cls.fail_perfdictempty_in = {
            "primary": {
                'blazing hot': {
                    'education': {
                        'electricity': {
                            'lighting': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'lighting': {'retrofit': 0, 'new': 0}}}},
                'mixed humid': {
                    'education': {
                        'electricity': {
                            'lighting': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'lighting': {'retrofit': 0, 'new': 0}}}}},
            "secondary": {
                'blazing hot': {
                    'education': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0, 'new': 0}},
                        'natural gas': {
                            'heating': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0, 'new': 0}},
                        'natural gas': {
                            'heating': {'retrofit': 0, 'new': 0}}}},
                'mixed humid': {
                    'education': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0, 'new': 0}},
                        'natural gas': {
                            'heating': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0, 'new': 0}},
                        'natural gas': {
                            'heating': {'retrofit': 0, 'new': 0}}}}}}
        cls.ok_array_type_out = numpy.ndarray
        cls.ok_array_length_out = 192
        cls.ok_arraynames_out = (
            'Climate Zone', 'Building Type', 'Template', 'Status',
            'Floor Area', 'Total Site Electricity', 'Net Site Electricity',
            'Total Gas', 'Total Other Fuel', 'Total Water', 'Net Water',
            'Interior Lighting Electricity', 'Exterior Lighting Electricity',
            'Interior Equipment Electricity', 'Exterior Equipment Electricity',
            'Heating Electricity', 'Cooling Electricity',
            'Service Water Heating Electricity', 'Fan Electricity',
            'Pump Electricity', 'Heat Recovery Electricity',
            'Heat Rejection Electricity', 'Humidification Electricity',
            'Refrigeration Electricity', 'Generated Electricity',
            'Interior Equipment Gas', 'Exterior Equipment Gas', 'Heating Gas',
            'Service Water Heating Gas', 'Interior Equipment Other Fuel',
            'Exterior Equipment Other Fuel', 'Heating Other Fuel',
            'Service Water Heating Other Fuel', 'District Hot Water Heating',
            'District Hot Water Service Hot Water', 'District Chilled Water',
            'Interior Equipment Water', 'Exterior Equipment Water',
            'Service Water', 'Cooling Water', 'Heating Water',
            'Humidifcation Water', 'Collected Water')
        cls.ok_perfdictempty_out = {
            "primary": {
                'hot dry': {
                    'education': {
                        'electricity': {
                            'lighting': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'lighting': {'retrofit': 0, 'new': 0}}}},
                'mixed humid': {
                    'education': {
                        'electricity': {
                            'lighting': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'lighting': {'retrofit': 0, 'new': 0}}}}},
            "secondary": {
                'hot dry': {
                    'education': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0, 'new': 0}},
                        'natural gas': {
                            'heating': {'retrofit': 0, 'new': 0}},
                        'distillate': {
                            'heating': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0, 'new': 0}},
                        'natural gas': {
                            'heating': {'retrofit': 0, 'new': 0}},
                        'distillate': {
                            'heating': {'retrofit': 0, 'new': 0}}}},
                'mixed humid': {
                    'education': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0, 'new': 0}},
                        'natural gas': {
                            'heating': {'retrofit': 0, 'new': 0}},
                        'distillate': {
                            'heating': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0, 'new': 0}},
                        'natural gas': {
                            'heating': {'retrofit': 0, 'new': 0}},
                        'distillate': {
                            'heating': {'retrofit': 0, 'new': 0}}}}}}
        cls.ok_perfdictfill_out = {
            "primary": {
                'hot dry': {
                    'education': {
                        'electricity': {
                            'lighting': {'retrofit': 0.5, 'new': 0.5}}},
                    'assembly': {
                        'electricity': {
                            'lighting': {'retrofit': 0.5, 'new': 0.5}}}},
                'mixed humid': {
                    'education': {
                        'electricity': {
                            'lighting': {
                                'retrofit': 0.25, 'new': 0.065}}},
                    'assembly': {
                        'electricity': {
                            'lighting': {
                                'retrofit': 0.25, 'new': 0}}}}},
            "secondary": {
                'hot dry': {
                    'education': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0.25, 'new': 0.25}},
                        'natural gas': {
                            'heating': {
                                'retrofit': -0.25, 'new': -0.25}},
                        'distillate': {
                            'heating': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0.25, 'new': 0.25}},
                        'natural gas': {
                            'heating': {
                                'retrofit': -0.25, 'new': -0.25}},
                        'distillate': {
                            'heating': {'retrofit': 0, 'new': 0}}}},
                'mixed humid': {
                    'education': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0.5, 'new': 0.13}},
                        'natural gas': {
                            'heating': {
                                'retrofit': -0.5, 'new': -0.13}},
                        'distillate': {
                            'heating': {'retrofit': 0, 'new': 0}}},
                    'assembly': {
                        'electricity': {
                            'heating': {'retrofit': 0, 'new': 0},
                            'cooling': {'retrofit': 0.5, 'new': 0}},
                        'natural gas': {
                            'heating': {
                                'retrofit': -0.5, 'new': 0}},
                        'distillate': {
                            'heating': {'retrofit': 0, 'new': 0}}}}}}

    def test_array_conversion(self):
        """Test 'convert_to_array' function given valid inputs.

        Note:
            Ensure correct conversion of an input Excel sheet to structured
            array.
        """
        # Check for correct type of converted array
        self.assertIsInstance(self.ok_perfarray_in, self.ok_array_type_out)
        # Check for correct column names and length of the converted array
        self.assertEqual(
            [self.ok_perfarray_in.dtype.names, len(self.ok_perfarray_in)],
            [self.ok_arraynames_out, self.ok_array_length_out])

    def test_dict_creation(self):
        """Test 'create_perf_dict' function given valid inputs.

        Note:
            Ensure correct generation of measure performance dictionary.
        """
        self.dict_check(self.meas.create_perf_dict(
            self.mseg_in), self.ok_perfdictempty_out)

    def test_dict_fill(self):
        """Test 'fill_perf_dict' function given valid inputs.

        Note:
            Ensure correct updating of measure performance dictionary
            with EnergyPlus simulation results.
        """
        self.dict_check(
            self.meas.fill_perf_dict(
                self.ok_perfdictempty_out, self.ok_perfarray_in,
                self.ok_eplus_vintagewts, eplus_bldg_types={}),
            self.ok_perfdictfill_out)

    def test_dict_fill_fail(self):
        """Test 'fill_perf_dict' function given invalid inputs.

        Note:
            Ensure function fails when given either invalid blank
            performance dictionary to fill or invalid input array of
            EnergyPlus simulation information to fill the dict with.
        """
        with self.assertRaises(KeyError):
            # Case with invalid input dictionary
            self.meas.fill_perf_dict(
                self.fail_perfdictempty_in, self.ok_perfarray_in,
                self.ok_eplus_vintagewts, eplus_bldg_types={})
            # Case with invalid input array of EnergyPlus information
            self.meas.fill_perf_dict(
                self.ok_perfdictempty_out, self.fail_perfarray_in,
                self.ok_eplus_vintagewts, eplus_bldg_types={})

    def test_fill_eplus(self):
        """Test 'fill_eplus' function given valid inputs.

        Note:
            Ensure proper updating of measure performance with
            EnergyPlus simulation results from start ('convert_to_array')
            to finish ('fill_perf_dict').
        """
        self.meas.fill_eplus(
            self.mseg_in, self.eplus_dir, self.ok_eplusfiles_in,
            self.ok_eplus_vintagewts)
        # Check for properly updated measure energy_efficiency,
        # energy_efficiency_source, and energy_efficiency_source_quality
        # attributes.
        self.dict_check(
            self.meas.energy_efficiency, self.ok_perfdictfill_out)
        self.assertEqual(
            [self.meas.energy_efficiency_source,
             self.meas.energy_efficiency_source_quality],
            ['EnergyPlus/OpenStudio', 5])


class FillMeasuresTest(unittest.TestCase, CommonMethods):
    """Test 'fill_measures' function.

    Ensure that function properly identifies which measures need performance,
    cost, and/or markets/savings updates and executes these updates.

    Attributes:
        measures_in (list): List of dictionaries that each contain sample
            measure information to update via 'fill_measures'.
        ok_out (list): List of dictionaries that should be generated by
            'fill_measures' given sample input measure information to update.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables to initialize before each test in the class."""
        cls.measures_in = [{
            # Measure needs mkts_savings update
            "name": "fill measure 1",
            "status": {
                "active": True, "update": True},
            "installed_cost": 25,
            "cost_units": "2013$/ft^2 floor",
            "energy_efficiency": {
                "primary": 0.5, "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings",
                "secondary": None},
            "bldg_type": ["single family home"],
            "mkts_savings": None},
            {
            # Measure needs residential cost and mkts_savings update
            "name": "fill measure 2",
            "status": {
                "active": True, "update": False},
            "installed_cost": 25,
            "cost_units": "2013$/ft^2 glazing",
            "energy_efficiency": {
                "primary": 0.5, "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings",
                "secondary": None},
            "bldg_type": ["single family home"],
            "mkts_savings": None},
            {
            # Measure needs commercial cost and mkts_savings update
            "name": "fill measure 3",
            "status": {
                "active": True, "update": True},
            "installed_cost": 25,
            "cost_units": "2013$/unit",
            "energy_efficiency": {
                "primary": 0.5, "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings",
                "secondary": None},
            "bldg_type": ["assembly"],
            "mkts_savings": None},
            {
            # Measure does not require any updates
            "name": "fill measure 4",
            "status": {
                "active": True, "update": False},
            "installed_cost": 25,
            "cost_units": "2013$/ft^2 floor",
            "energy_efficiency": {
                "primary": 0.5, "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings",
                "secondary": None},
            "bldg_type": ["assembly"],
            "mkts_savings": {
                "master_mseg": {"dummy data": 0},
                "master_savings": {"dummy data": 0},
                "mseg_adjust": {"dummy data": 0},
                "mseg_out_break": {"dummy data": 0}}}]
        cls.ok_out = [{
            "name": "fill measure 1",
            "status": {
                "active": True, "update": False},
            "installed_cost": 25,
            "cost_units": "2013$/ft^2 floor",
            "energy_efficiency": {
                "primary": 0.5, "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings",
                "secondary": None},
            "bldg_type": ["single family home"],
            "mkts_savings": {
                "master_mseg": 999,
                "mseg_adjust": 999,
                "mseg_out_break": 999,
                "master_savings": {}}},
            {
            "name": "fill measure 2",
            "status": {
                "active": True, "update": False},
            "installed_cost": 999,
            "cost_units": "2013$/ft^2 floor",
            "energy_efficiency": {
                "primary": 0.5, "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings",
                "secondary": None},
            "bldg_type": ["single family home"],
            "mkts_savings": {
                "master_mseg": 999,
                "mseg_adjust": 999,
                "mseg_out_break": 999,
                "master_savings": {}}},
            {
            "name": "fill measure 3",
            "status": {
                "active": True, "update": False},
            "installed_cost": 9999,
            "cost_units": "2013$/ft^2 floor",
            "energy_efficiency": {
                "primary": 0.5, "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings",
                "secondary": None},
            "bldg_type": ["assembly"],
            "mkts_savings": {
                "master_mseg": 999,
                "mseg_adjust": 999,
                "mseg_out_break": 999,
                "master_savings": {}}},
            {
            "name": "fill measure 4",
            "status": {
                "active": True, "update": False},
            "installed_cost": 25,
            "cost_units": "2013$/ft^2 floor",
            "energy_efficiency": {
                "primary": 0.5, "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings",
                "secondary": None},
            "bldg_type": ["assembly"],
            "mkts_savings": {
                "master_mseg": {"dummy data": 0},
                "mseg_adjust": {"dummy data": 0},
                "mseg_out_break": {"dummy data": 0},
                "master_savings": {"dummy data": 0}}}]

    def test_measure_updates(self):
        """Test 'fill_measures' function.

        Note:
            Ensure that function properly identifies which input measures
            require updating and that the updates are performed correctly.
        """
        measures_out = measures_prep.fill_measures(
            self.measures_in, msegs={}, msegs_cpl={}, eplus_dir=None,
            meas_costconvert={})
        for oc in range(0, len(measures_out)):
            self.dict_check(measures_out[oc], self.ok_out[oc])


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    """Trigger default behavior of running all test fixtures in the file."""
    unittest.main()

if __name__ == "__main__":
    main()
