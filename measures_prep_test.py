#!/usr/bin/env python3

""" Tests for running the measure preparation routine """

# Import code to be tested
import measures_prep
# Import needed packages
import unittest
import xlrd
import numpy
import os
from collections import OrderedDict
import warnings
import copy


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

    Raises:
        AssertionError: If function yields unexpected results or does not
            raise a KeyError when it should.
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
        # Useful global variables for the sample measure object
        handyvars = measures_prep.UsefulVars()
        cls.meas = measures_prep.Measure(handyvars, **sample_measure_in)
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

        Raises:
            AssertionError: If function yields unexpected results.
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

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.dict_check(self.meas.create_perf_dict(
            self.mseg_in), self.ok_perfdictempty_out)

    def test_dict_fill(self):
        """Test 'fill_perf_dict' function given valid inputs.

        Note:
            Ensure correct updating of measure performance dictionary
            with EnergyPlus simulation results.

        Raises:
            AssertionError: If function yields unexpected results.
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

        Raises:
            AssertionError: If KeyError is not raised
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

        Raises:
            AssertionError: If function yields unexpected results.
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


class MarketUpdatesTest(unittest.TestCase, CommonMethods):
    """Test 'fill_mkts' function.

    Ensure that the function properly fills in market microsegment data
    for a series of sample measures.

    Attributes:
        sample_mseg_in (dict): Sample baseline microsegment stock/energy.
        sample_cpl_in (dict): Sample baseline technology cost, performance,
            and lifetime.
        ok_tpmeas_fullchk_in (list): Valid sample measure information
            to update with markets data; measure cost, performance, and life
            attributes are given as point estimates. Used to check the full
            measure 'markets' attribute under a 'Technical potential scenario.
        ok_tpmeas_partchk_in (list): Valid sample measure information to update
            with markets data; measure cost, performance, and lifetime
            attributes are given as point estimates. Used to check the
            'master_mseg' branch of measure 'markets' attribute under a
            'Technical potential scenario.
        ok_mapmeas_partchk_in (list): Valid sample measure information
            to update with markets data; measure cost, performance, and life
            attributes are given as point estimates. Used to check the
            'master_mseg' branch of measure 'markets' attribute under a 'Max
            adoption potential scenario.
        ok_distmeas_in (list): Valid sample measure information to
            update with markets data; measure cost, performance, and lifetime
            attributes are given as probability distributions.
        ok_partialmeas_in (list): Partially valid measure information to update
            with markets data.
        failmeas_in (list): Invalid sample measure information that should
            yield error when entered into function.
        warnmeas_in (list): Incomplete sample measure information that
            should yield warnings when entered into function (measure
            sub-market scaling fraction source attributions are invalid).
        ok_tpmeas_fullchk_msegout (list): Master market microsegments
            information that should be yielded given 'ok_tpmeas_fullchk_in'.
        ok_tpmeas_fullchk_competechoiceout (list): Consumer choice information
            that should be yielded given 'ok_tpmeas_fullchk_in'.
        ok_tpmeas_fullchk_msegadjout (list): Secondary microsegment adjustment
            information that should be yielded given 'ok_tpmeas_fullchk_in'.
        ok_tpmeas_fullchk_supplydemandout (list): Supply-demand adjustment
            information that should be yielded given 'ok_tpmeas_fullchk_in'.
        ok_tpmeas_fullchk_break_out (list): Output breakout information that
            should be yielded given 'ok_tpmeas_fullchk_in'.
        ok_tpmeas_partchk_msegout (list): Master market microsegments
            information that should be yielded given 'ok_tpmeas_partchk_in'.
        ok_mapmas_partchck_msegout (list): Master market microsegments
            information that should be yielded given 'ok_mapmeas_partchk_in'.
        ok_distmeas_out (list): Means and sampling Ns for measure energy/cost
            markets and lifetime that should be yielded given 'ok_distmeas_in'.
        ok_partialmeas_out (list): Master market microsegments information
            that should be yielded given 'ok_partialmeas_in'.
        ok_warnmeas_out (list): Warning messages that should be yielded
            given 'warnmeas_in'.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        handyvars = measures_prep.UsefulVars()
        handyvars.aeo_years = ["2009", "2010"]
        # Adjust carbon intensity data to reflect units originally used for
        # tests (* Note: test outcome units to be adjusted later)
        for k in handyvars.carb_int.keys():
            handyvars.carb_int[k] = {
                yr_key: (handyvars.carb_int[k][yr_key] * 1000000000) for
                yr_key in handyvars.aeo_years}
        cls.sample_mseg_in = {
            "AIA_CZ1": {
                "assembly": {
                    "total square footage": {"2009": 11, "2010": 11},
                    "new square footage": {"2009": 0, "2010": 0},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 0, "2010": 0}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 1, "2010": 1}},
                                "lighting gain": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": -7, "2010": -7}}}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 5, "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 6, "2010": 6}},
                                "lighting gain": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 6, "2010": 6}}}},
                        "lighting": {
                            "commercial light type X": {
                                "stock": "NA",
                                "energy": {
                                    "2009": 11, "2010": 11}}}}},
                "single family home": {
                    "total square footage": {"2009": 100, "2010": 200},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 100, "2010": 50},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 0, "2010": 0}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 1, "2010": 1}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {
                                "boiler (electric)": {
                                    "stock": {"2009": 2, "2010": 2},
                                    "energy": {"2009": 2, "2010": 2}},
                                "ASHP": {
                                    "stock": {"2009": 3, "2010": 3},
                                    "energy": {"2009": 3, "2010": 3}},
                                "GSHP": {
                                    "stock": {"2009": 4, "2010": 4},
                                    "energy": {"2009": 4, "2010": 4}}}},
                        "secondary heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 5, "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 6, "2010": 6}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {"non-specific": 7}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 5, "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 6, "2010": 6}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {
                                "central AC": {
                                    "stock": {"2009": 7, "2010": 7},
                                    "energy": {"2009": 7, "2010": 7}},
                                "room AC": {
                                    "stock": {"2009": 8, "2010": 8},
                                    "energy": {"2009": 8, "2010": 8}},
                                "ASHP": {
                                    "stock": {"2009": 9, "2010": 9},
                                    "energy": {"2009": 9, "2010": 9}},
                                "GSHP": {
                                    "stock": {"2009": 10, "2010": 10},
                                    "energy": {"2009": 10, "2010": 10}}}},
                        "lighting": {
                            "linear fluorescent (LED)": {
                                "stock": {"2009": 11, "2010": 11},
                                "energy": {"2009": 11, "2010": 11}},
                            "general service (LED)": {
                                "stock": {"2009": 12, "2010": 12},
                                "energy": {"2009": 12, "2010": 12}},
                            "reflector (LED)": {
                                "stock": {"2009": 13, "2010": 13},
                                "energy": {"2009": 13, "2010": 13}},
                            "external (LED)": {
                                "stock": {"2009": 14, "2010": 14},
                                "energy": {"2009": 14, "2010": 14}}},
                        "refrigeration": {
                            "stock": {"2009": 111, "2010": 111},
                            "energy": {"2009": 111, "2010": 111}},
                        "other (grid electric)": {
                            "freezers": {
                                "stock": {"2009": 222, "2010": 222},
                                "energy": {"2009": 222, "2010": 222}},
                            "other MELs": {
                                "stock": {"2009": 333, "2010": 333},
                                "energy": {"2009": 333, "2010": 333}}}},
                    "natural gas": {
                        "water heating": {
                            "stock": {"2009": 15, "2010": 15},
                            "energy": {"2009": 15, "2010": 15}},
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 0,
                                               "2010": 0}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 1,
                                               "2010": 1}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 10, "2010": 10}}}},
                        "secondary heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 5,
                                               "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 6,
                                               "2010": 6}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 10, "2010": 10}}}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 5, "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 6, "2010": 6}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {
                                        "2009": 10, "2010": 10}}}}}},
                "multi family home": {
                    "total square footage": {"2009": 300, "2010": 400},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 100, "2010": 50},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 0, "2010": 0}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 1, "2010": 1}}},
                            "supply": {
                                "boiler (electric)": {
                                    "stock": {"2009": 2, "2010": 2},
                                    "energy": {"2009": 2, "2010": 2}},
                                "ASHP": {
                                    "stock": {"2009": 3, "2010": 3},
                                    "energy": {"2009": 3, "2010": 3}},
                                "GSHP": {
                                    "stock": {"2009": 4, "2010": 4},
                                    "energy": {"2009": 4, "2010": 4}}}},
                        "lighting": {
                            "linear fluorescent (LED)": {
                                "stock": {"2009": 11, "2010": 11},
                                "energy": {"2009": 11, "2010": 11}},
                            "general service (LED)": {
                                "stock": {"2009": 12, "2010": 12},
                                "energy": {"2009": 12, "2010": 12}},
                            "reflector (LED)": {
                                "stock": {"2009": 13, "2010": 13},
                                "energy": {"2009": 13, "2010": 13}},
                            "external (LED)": {
                                "stock": {"2009": 14, "2010": 14},
                                "energy": {"2009": 14, "2010": 14}}}}}},
            "AIA_CZ2": {
                "single family home": {
                    "total square footage": {"2009": 500, "2010": 600},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 100, "2010": 50},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 0, "2010": 0}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 1, "2010": 1}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {
                                "boiler (electric)": {
                                    "stock": {"2009": 2, "2010": 2},
                                    "energy": {"2009": 2, "2010": 2}},
                                "ASHP": {
                                    "stock": {"2009": 3, "2010": 3},
                                    "energy": {"2009": 3, "2010": 3}},
                                "GSHP": {
                                    "stock": {"2009": 4, "2010": 4},
                                    "energy": {"2009": 4, "2010": 4}}}},
                        "secondary heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 5, "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 6, "2010": 6}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {"non-specific": 7}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 5, "2010": 5}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 6, "2010": 6}},
                                "infiltration": {
                                    "stock": "NA",
                                    "energy": {"2009": 10, "2010": 10}}},
                            "supply": {
                                "central AC": {
                                    "stock": {"2009": 7, "2010": 7},
                                    "energy": {"2009": 7, "2010": 7}},
                                "room AC": {
                                    "stock": {"2009": 8, "2010": 8},
                                    "energy": {"2009": 8, "2010": 8}},
                                "ASHP": {
                                    "stock": {"2009": 9, "2010": 9},
                                    "energy": {"2009": 9, "2010": 9}},
                                "GSHP": {
                                    "stock": {"2009": 10, "2010": 10},
                                    "energy": {"2009": 10, "2010": 10}}}},
                        "lighting": {
                            "linear fluorescent (LED)": {
                                "stock": {"2009": 11, "2010": 11},
                                "energy": {"2009": 11, "2010": 11}},
                            "general service (LED)": {
                                "stock": {"2009": 12, "2010": 12},
                                "energy": {"2009": 12, "2010": 12}},
                            "reflector (LED)": {
                                "stock": {"2009": 13, "2010": 13},
                                "energy": {"2009": 13, "2010": 13}},
                            "external (LED)": {
                                "stock": {"2009": 14, "2010": 14},
                                "energy": {"2009": 14, "2010": 14}}}},
                    "natural gas": {"water heating": {
                                    "stock": {"2009": 15, "2010": 15},
                                    "energy": {"2009": 15, "2010": 15}}}},
                "multi family home": {
                    "total square footage": {"2009": 700, "2010": 800},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 100, "2010": 50},
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "stock": "NA",
                                    "energy": {"2009": 0, "2010": 0}},
                                "windows solar": {
                                    "stock": "NA",
                                    "energy": {"2009": 1, "2010": 1}}},
                            "supply": {
                                "boiler (electric)": {
                                    "stock": {"2009": 2, "2010": 2},
                                    "energy": {"2009": 2, "2010": 2}},
                                "ASHP": {
                                    "stock": {"2009": 3, "2010": 3},
                                    "energy": {"2009": 3, "2010": 3}},
                                "GSHP": {
                                    "stock": {"2009": 4, "2010": 4}}}},
                        "lighting": {
                            "linear fluorescent (LED)": {
                                "stock": {"2009": 11, "2010": 11},
                                "energy": {"2009": 11, "2010": 11}},
                            "general service (LED)": {
                                "stock": {"2009": 12, "2010": 12},
                                "energy": {"2009": 12, "2010": 12}},
                            "reflector (LED)": {
                                "stock": {"2009": 13, "2010": 13},
                                "energy": {"2009": 13, "2010": 13}},
                            "external (LED)": {
                                "stock": {"2009": 14, "2010": 14},
                                "energy": {"2009": 14, "2010": 14}}}}}},
            "AIA_CZ4": {
                "multi family home": {
                    "total square footage": {"2009": 900, "2010": 1000},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 100, "2010": 50},
                    "electricity": {
                        "lighting": {
                            "linear fluorescent (LED)": {
                                "stock": {"2009": 11, "2010": 11},
                                "energy": {"2009": 11, "2010": 11}},
                            "general service (LED)": {
                                "stock": {"2009": 12, "2010": 12},
                                "energy": {"2009": 12, "2010": 12}},
                            "reflector (LED)": {
                                "stock": {"2009": 13, "2010": 13},
                                "energy": {"2009": 13, "2010": 13}},
                            "external (LED)": {
                                "stock": {"2009": 14, "2010": 14},
                                "energy": {"2009": 14, "2010": 14}}}}}}}
        cls.sample_cpl_in = {
            "AIA_CZ1": {
                "assembly": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "lighting gain": 0}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "lighting gain": {
                                    "performance": {
                                        "typical": 0,
                                        "best": 0,
                                        "units": "NA",
                                        "source":
                                        "NA"},
                                    "installed cost": {
                                        "typical": 0,
                                        "best": 0,
                                        "units": "NA",
                                        "source": "NA"},
                                    "lifetime": {
                                        "average": 0,
                                        "range": 0,
                                        "units": "NA",
                                        "source": "NA"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "lighting": {
                            "commercial light type X": {
                                "performance": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "lm/W",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 14, "2010": 14},
                                    "best": {"2009": 14, "2010": 14},
                                    "units": "2014$/ft^2 floor",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 140, "2010": 140},
                                    "range": {"2009": 14, "2010": 14},
                                    "units": "years",
                                    "source": "EIA AEO"},
                                "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}},
                "single family home": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "boiler (electric)": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 3, "2010": 3},
                                        "best": {"2009": 3, "2010": 3},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 3, "2010": 3},
                                        "best": {"2009": 3, "2010": 3},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 30, "2010": 30},
                                        "range": {"2009": 3, "2010": 3},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 4, "2010": 4},
                                        "best": {"2009": 4, "2010": 4},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 4, "2010": 4},
                                        "best": {"2009": 4, "2010": 4},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 40, "2010": 40},
                                        "range": {"2009": 4, "2010": 4},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "secondary heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 5, "2010": 5},
                                        "best": {"2009": 5, "2010": 5},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 5, "2010": 5},
                                        "best": {"2009": 5, "2010": 5},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 50, "2010": 50},
                                        "range": {"2009": 5, "2010": 5},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 6, "2010": 6},
                                        "best": {"2009": 6, "2010": 6},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 6, "2010": 6},
                                        "best": {"2009": 6, "2010": 6},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 60, "2010": 60},
                                        "range": {"2009": 6, "2010": 6},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "non-specific": {
                                    "performance": {
                                        "typical": {"2009": 7, "2010": 7},
                                        "best": {"2009": 7, "2010": 7},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 7, "2010": 7},
                                        "best": {"2009": 7, "2010": 7},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 70, "2010": 70},
                                        "range": {"2009": 7, "2010": 7},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 80, "2010": 80},
                                        "range": {"2009": 8, "2010": 8},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 90, "2010": 90},
                                        "range": {"2009": 9, "2010": 9},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "central AC": {
                                    "performance": {
                                        "typical": {"2009": 10, "2010": 10},
                                        "best": {"2009": 10, "2010": 10},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 10, "2010": 10},
                                        "best": {"2009": 10, "2010": 10},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 100, "2010": 100},
                                        "range": {"2009": 10, "2010": 10},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "room AC": {
                                    "performance": {
                                        "typical": {"2009": 11, "2010": 11},
                                        "best": {"2009": 11, "2010": 11},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 11, "2010": 11},
                                        "best": {"2009": 11, "2010": 11},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 110, "2010": 110},
                                        "range": {"2009": 11, "2010": 11},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 12, "2010": 12},
                                        "best": {"2009": 12, "2010": 12},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 12, "2010": 12},
                                        "best": {"2009": 12, "2010": 12},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 120, "2010": 120},
                                        "range": {"2009": 12, "2010": 12},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 13, "2010": 13},
                                        "best": {"2009": 13, "2010": 13},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 13, "2010": 13},
                                        "best": {"2009": 13, "2010": 13},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 130, "2010": 130},
                                        "range": {"2009": 13, "2010": 13},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "lighting": {
                            "linear fluorescent (LED)": {
                                    "performance": {
                                        "typical": {"2009": 14, "2010": 14},
                                        "best": {"2009": 14, "2010": 14},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 14, "2010": 14},
                                        "best": {"2009": 14, "2010": 14},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 140, "2010": 140},
                                        "range": {"2009": 14, "2010": 14},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "general service (LED)": {
                                    "performance": {
                                        "typical": {"2009": 15, "2010": 15},
                                        "best": {"2009": 15, "2010": 15},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 15, "2010": 15},
                                        "best": {"2009": 15, "2010": 15},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 150, "2010": 150},
                                        "range": {"2009": 15, "2010": 15},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "reflector (LED)": {
                                    "performance": {
                                        "typical": {"2009": 16, "2010": 16},
                                        "best": {"2009": 16, "2010": 16},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 16, "2010": 16},
                                        "best": {"2009": 16, "2010": 16},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 160, "2010": 160},
                                        "range": {"2009": 16, "2010": 16},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "external (LED)": {
                                    "performance": {
                                        "typical": {"2009": 17, "2010": 17},
                                        "best": {"2009": 17, "2010": 17},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 17, "2010": 17},
                                        "best": {"2009": 17, "2010": 17},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 170, "2010": 170},
                                        "range": {"2009": 17, "2010": 17},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                        "refrigeration": {
                            "performance": {
                                "typical": {"2009": 550, "2010": 550},
                                "best": {"2009": 450, "2010": 450},
                                "units": "kWh/yr",
                                "source":
                                "EIA AEO"},
                            "installed cost": {
                                "typical": {"2009": 300, "2010": 300},
                                "best": {"2009": 600, "2010": 600},
                                "units": "2010$/unit",
                                "source": "EIA AEO"},
                            "lifetime": {
                                "average": {"2009": 17, "2010": 17},
                                "range": {"2009": 6, "2010": 6},
                                "units": "years",
                                "source": "EIA AEO"},
                            "consumer choice": {
                                "competed market share": {
                                    "source": "EIA AEO",
                                    "model type": "logistic regression",
                                    "parameters": {
                                        "b1": {"2009": None, "2010": None},
                                        "b2": {"2009": None,
                                               "2010": None}}},
                                "competed market": {
                                    "source": "COBAM",
                                    "model type": "bass diffusion",
                                    "parameters": {
                                        "p": "NA",
                                        "q": "NA"}}}},
                        "other (grid electric)": {
                            "freezers": {
                                    "performance": {
                                        "typical": {"2009": 550, "2010": 550},
                                        "best": {"2009": 450, "2010": 450},
                                        "units": "kWh/yr",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 100, "2010": 100},
                                        "best": {"2009": 200, "2010": 200},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 15, "2010": 15},
                                        "range": {"2009": 3, "2010": 3},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "other MELs": {
                                    "performance": {
                                        "typical": {"2009": 550, "2010": 550},
                                        "best": {"2009": 450, "2010": 450},
                                        "units": "kWh/yr",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 100, "2010": 100},
                                        "best": {"2009": 200, "2010": 200},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 15, "2010": 15},
                                        "range": {"2009": 3, "2010": 3},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                    "natural gas": {
                        "water heating": {
                            "performance": {
                                "typical": {"2009": 18, "2010": 18},
                                "best": {"2009": 18, "2010": 18},
                                "units": "EF",
                                "source":
                                "EIA AEO"},
                            "installed cost": {
                                "typical": {"2009": 18, "2010": 18},
                                "best": {"2009": 18, "2010": 18},
                                "units": "2014$/unit",
                                "source": "EIA AEO"},
                            "lifetime": {
                                "average": {"2009": 180, "2010": 180},
                                "range": {"2009": 18, "2010": 18},
                                "units": "years",
                                "source": "EIA AEO"},
                            "consumer choice": {
                                "competed market share": {
                                    "source": "EIA AEO",
                                    "model type": "logistic regression",
                                    "parameters": {
                                        "b1": {"2009": None, "2010": None},
                                        "b2": {"2009": None,
                                               "2010": None}}},
                                "competed market": {
                                    "source": "COBAM",
                                    "model type": "bass diffusion",
                                    "parameters": {
                                        "p": "NA",
                                        "q": "NA"}}}},
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "secondary heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 5, "2010": 5},
                                        "best": {"2009": 5, "2010": 5},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 5, "2010": 5},
                                        "best": {"2009": 5, "2010": 5},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 50, "2010": 50},
                                        "range": {"2009": 5, "2010": 5},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 6, "2010": 6},
                                        "best": {"2009": 6, "2010": 6},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 6, "2010": 6},
                                        "best": {"2009": 6, "2010": 6},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 60, "2010": 60},
                                        "range": {"2009": 6, "2010": 6},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 80, "2010": 80},
                                        "range": {"2009": 8, "2010": 8},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 90, "2010": 90},
                                        "range": {"2009": 9, "2010": 9},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}}},
                "multi family home": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 19, "2010": 19},
                                        "best": {"2009": 19, "2010": 19},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 19, "2010": 19},
                                        "best": {"2009": 19, "2010": 19},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 190, "2010": 190},
                                        "range": {"2009": 19, "2010": 19},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 20, "2010": 20},
                                        "best": {"2009": 20, "2010": 20},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 20, "2010": 20},
                                        "best": {"2009": 20, "2010": 20},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 200, "2010": 200},
                                        "range": {"2009": 20, "2010": 20},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "boiler (electric)": {
                                    "performance": {
                                        "typical": {"2009": 21, "2010": 21},
                                        "best": {"2009": 21, "2010": 21},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 21, "2010": 21},
                                        "best": {"2009": 21, "2010": 21},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 210, "2010": 210},
                                        "range": {"2009": 21, "2010": 21},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 22, "2010": 22},
                                        "best": {"2009": 22, "2010": 22},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 22, "2010": 22},
                                        "best": {"2009": 22, "2010": 22},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 220, "2010": 220},
                                        "range": {"2009": 22, "2010": 22},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 23, "2010": 23},
                                        "best": {"2009": 23, "2010": 23},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 23, "2010": 23},
                                        "best": {"2009": 23, "2010": 23},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 230, "2010": 230},
                                        "range": {"2009": 23, "2010": 23},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "lighting": {
                            "linear fluorescent (LED)": {
                                    "performance": {
                                        "typical": {"2009": 24, "2010": 24},
                                        "best": {"2009": 24, "2010": 24},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 24, "2010": 24},
                                        "best": {"2009": 24, "2010": 24},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 240, "2010": 240},
                                        "range": {"2009": 24, "2010": 24},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "general service (LED)": {
                                    "performance": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 250, "2010": 250},
                                        "range": {"2009": 25, "2010": 25},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "reflector (LED)": {
                                    "performance": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 250, "2010": 250},
                                        "range": {"2009": 25, "2010": 25},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "external (LED)": {
                                    "performance": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 250, "2010": 250},
                                        "range": {"2009": 25, "2010": 25},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}}},
            "AIA_CZ2": {
                "single family home": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 1, "2010": 1},
                                        "best": {"2009": 1, "2010": 1},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 10, "2010": 10},
                                        "range": {"2009": 1, "2010": 1},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "boiler (electric)": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 3, "2010": 3},
                                        "best": {"2009": 3, "2010": 3},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 3, "2010": 3},
                                        "best": {"2009": 3, "2010": 3},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 30, "2010": 30},
                                        "range": {"2009": 3, "2010": 3},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 4, "2010": 4},
                                        "best": {"2009": 4, "2010": 4},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 4, "2010": 4},
                                        "best": {"2009": 4, "2010": 4},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 40, "2010": 40},
                                        "range": {"2009": 4, "2010": 4},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "secondary heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 5, "2010": 5},
                                        "best": {"2009": 5, "2010": 5},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 5, "2010": 5},
                                        "best": {"2009": 5, "2010": 5},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 50, "2010": 50},
                                        "range": {"2009": 5, "2010": 5},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 6, "2010": 6},
                                        "best": {"2009": 6, "2010": 6},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 6, "2010": 6},
                                        "best": {"2009": 6, "2010": 6},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 60, "2010": 60},
                                        "range": {"2009": 6, "2010": 6},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "non-specific": {
                                    "performance": {
                                        "typical": {"2009": 7, "2010": 7},
                                        "best": {"2009": 7, "2010": 7},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 7, "2010": 7},
                                        "best": {"2009": 7, "2010": 7},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 70, "2010": 70},
                                        "range": {"2009": 7, "2010": 7},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "cooling": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 8, "2010": 8},
                                        "best": {"2009": 8, "2010": 8},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 80, "2010": 80},
                                        "range": {"2009": 8, "2010": 8},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 9, "2010": 9},
                                        "best": {"2009": 9, "2010": 9},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 90, "2010": 90},
                                        "range": {"2009": 9, "2010": 9},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "infiltration": {
                                    "performance": {
                                        "typical": {"2009": 2, "2010": 3},
                                        "best": {"2009": 2, "2010": 3},
                                        "units": "ACH50",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 2, "2010": 2},
                                        "best": {"2009": 2, "2010": 2},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 20, "2010": 20},
                                        "range": {"2009": 2, "2010": 2},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "central AC": {
                                    "performance": {
                                        "typical": {"2009": 10, "2010": 10},
                                        "best": {"2009": 10, "2010": 10},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 10, "2010": 10},
                                        "best": {"2009": 10, "2010": 10},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 100, "2010": 100},
                                        "range": {"2009": 10, "2010": 10},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "room AC": {
                                    "performance": {
                                        "typical": {"2009": 11, "2010": 11},
                                        "best": {"2009": 11, "2010": 11},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 11, "2010": 11},
                                        "best": {"2009": 11, "2010": 11},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 110, "2010": 110},
                                        "range": {"2009": 11, "2010": 11},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 12, "2010": 12},
                                        "best": {"2009": 12, "2010": 12},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 12, "2010": 12},
                                        "best": {"2009": 12, "2010": 12},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 120, "2010": 120},
                                        "range": {"2009": 12, "2010": 12},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 13, "2010": 13},
                                        "best": {"2009": 13, "2010": 13},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 13, "2010": 13},
                                        "best": {"2009": 13, "2010": 13},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 130, "2010": 130},
                                        "range": {"2009": 13, "2010": 13},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "lighting": {
                            "linear fluorescent (LED)": {
                                    "performance": {
                                        "typical": {"2009": 14, "2010": 14},
                                        "best": {"2009": 14, "2010": 14},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 14, "2010": 14},
                                        "best": {"2009": 14, "2010": 14},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 140, "2010": 140},
                                        "range": {"2009": 14, "2010": 14},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "general service (LED)": {
                                    "performance": {
                                        "typical": {"2009": 15, "2010": 15},
                                        "best": {"2009": 15, "2010": 15},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 15, "2010": 15},
                                        "best": {"2009": 15, "2010": 15},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 150, "2010": 150},
                                        "range": {"2009": 15, "2010": 15},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "reflector (LED)": {
                                    "performance": {
                                        "typical": {"2009": 16, "2010": 16},
                                        "best": {"2009": 16, "2010": 16},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 16, "2010": 16},
                                        "best": {"2009": 16, "2010": 16},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 160, "2010": 160},
                                        "range": {"2009": 16, "2010": 16},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "external (LED)": {
                                    "performance": {
                                        "typical": {"2009": 17, "2010": 17},
                                        "best": {"2009": 17, "2010": 17},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 17, "2010": 17},
                                        "best": {"2009": 17, "2010": 17},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 170, "2010": 170},
                                        "range": {"2009": 17, "2010": 17},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                    "natural gas": {
                        "water heating": {
                                "performance": {
                                    "typical": {"2009": 18, "2010": 18},
                                    "best": {"2009": 18, "2010": 18},
                                    "units": "EF",
                                    "source":
                                    "EIA AEO"},
                                "installed cost": {
                                    "typical": {"2009": 18, "2010": 18},
                                    "best": {"2009": 18, "2010": 18},
                                    "units": "2014$/unit",
                                    "source": "EIA AEO"},
                                "lifetime": {
                                    "average": {"2009": 180, "2010": 180},
                                    "range": {"2009": 18, "2010": 18},
                                    "units": "years",
                                    "source": "EIA AEO"},
                                "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                "multi family home": {
                    "electricity": {
                        "heating": {
                            "demand": {
                                "windows conduction": {
                                    "performance": {
                                        "typical": {"2009": 19, "2010": 19},
                                        "best": {"2009": 19, "2010": 19},
                                        "units": "R Value",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 19, "2010": 19},
                                        "best": {"2009": 19, "2010": 19},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 190, "2010": 190},
                                        "range": {"2009": 19, "2010": 19},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "windows solar": {
                                    "performance": {
                                        "typical": {"2009": 20, "2010": 20},
                                        "best": {"2009": 20, "2010": 20},
                                        "units": "SHGC",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 20, "2010": 20},
                                        "best": {"2009": 20, "2010": 20},
                                        "units": "2014$/ft^2 floor",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 200, "2010": 200},
                                        "range": {"2009": 20, "2010": 20},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}},
                            "supply": {
                                "boiler (electric)": {
                                    "performance": {
                                        "typical": {"2009": 21, "2010": 21},
                                        "best": {"2009": 21, "2010": 21},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 21, "2010": 21},
                                        "best": {"2009": 21, "2010": 21},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 210, "2010": 210},
                                        "range": {"2009": 21, "2010": 21},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "ASHP": {
                                    "performance": {
                                        "typical": {"2009": 22, "2010": 22},
                                        "best": {"2009": 22, "2010": 22},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 22, "2010": 22},
                                        "best": {"2009": 22, "2010": 22},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 220, "2010": 220},
                                        "range": {"2009": 22, "2010": 22},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                                "GSHP": {
                                    "performance": {
                                        "typical": {"2009": 23, "2010": 23},
                                        "best": {"2009": 23, "2010": 23},
                                        "units": "COP",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 23, "2010": 23},
                                        "best": {"2009": 23, "2010": 23},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 230, "2010": 230},
                                        "range": {"2009": 23, "2010": 23},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}},
                        "lighting": {
                            "linear fluorescent (LED)": {
                                    "performance": {
                                        "typical": {"2009": 24, "2010": 24},
                                        "best": {"2009": 24, "2010": 24},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 24, "2010": 24},
                                        "best": {"2009": 24, "2010": 24},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 240, "2010": 240},
                                        "range": {"2009": 24, "2010": 24},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "general service (LED)": {
                                    "performance": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 250, "2010": 250},
                                        "range": {"2009": 25, "2010": 25},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "reflector (LED)": {
                                    "performance": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 250, "2010": 250},
                                        "range": {"2009": 25, "2010": 25},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "external (LED)": {
                                    "performance": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 250, "2010": 250},
                                        "range": {"2009": 25, "2010": 25},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}}},
            "AIA_CZ4": {
                "multi family home": {
                    "electricity": {
                        "lighting": {
                            "linear fluorescent (LED)": {
                                    "performance": {
                                        "typical": {"2009": 24, "2010": 24},
                                        "best": {"2009": 24, "2010": 24},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 24, "2010": 24},
                                        "best": {"2009": 24, "2010": 24},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 240, "2010": 240},
                                        "range": {"2009": 24, "2010": 24},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "general service (LED)": {
                                    "performance": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 25, "2010": 25},
                                        "best": {"2009": 25, "2010": 25},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 250, "2010": 250},
                                        "range": {"2009": 25, "2010": 25},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "reflector (LED)": {
                                    "performance": {
                                        "typical": {"2009": 26, "2010": 26},
                                        "best": {"2009": 26, "2010": 26},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 26, "2010": 26},
                                        "best": {"2009": 26, "2010": 26},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 260, "2010": 260},
                                        "range": {"2009": 26, "2010": 26},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}},
                            "external (LED)": {
                                    "performance": {
                                        "typical": {"2009": 27, "2010": 27},
                                        "best": {"2009": 27, "2010": 27},
                                        "units": "lm/W",
                                        "source":
                                        "EIA AEO"},
                                    "installed cost": {
                                        "typical": {"2009": 27, "2010": 27},
                                        "best": {"2009": 27, "2010": 27},
                                        "units": "2014$/unit",
                                        "source": "EIA AEO"},
                                    "lifetime": {
                                        "average": {"2009": 270, "2010": 270},
                                        "range": {"2009": 27, "2010": 27},
                                        "units": "years",
                                        "source": "EIA AEO"},
                                    "consumer choice": {
                                        "competed market share": {
                                            "source": "EIA AEO",
                                            "model type":
                                                "logistic regression",
                                            "parameters": {
                                                "b1": {"2009": None,
                                                       "2010": None},
                                                "b2": {"2009": None,
                                                       "2010": None}}},
                                        "competed market": {
                                            "source": "COBAM",
                                            "model type": "bass diffusion",
                                            "parameters": {
                                                "p": "NA",
                                                "q": "NA"}}}}}}}}}
        ok_measures_in = [{
            "name": "sample measure 1",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {"primary":
                                  {"AIA_CZ1": {"heating": 30,
                                               "cooling": 25},
                                   "AIA_CZ2": {"heating": 30,
                                               "cooling": 15}},
                                  "secondary": None},
            "energy_efficiency_units": {"primary": "COP",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["heating", "cooling"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": ["boiler (electric)",
                           "ASHP", "GSHP", "room AC"],
                           "secondary": None}},
            {
            "name": "sample measure 2",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {"new": 25, "existing": 25},
                "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}},
            {
            "name": "sample measure 15",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 500,
            "cost_units": {
                "refrigeration": "2010$/unit",
                "other (grid electric)": "2014$/unit"},
            "energy_efficiency": {
                "primary": 0.1,
                "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings (constant)",
                "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["refrigeration", "other (grid electric)"],
                "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": [None, "freezers"],
                           "secondary": None}},
            {
            "name": "sample measure 3",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {"primary": 25,
                                  "secondary": {
                                      "heating": 0.4,
                                      "secondary heating": 0.4,
                                      "cooling": -0.4}},
            "energy_efficiency_units": {"primary": "lm/W",
                                        "secondary":
                                        "relative savings (constant)"},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home",
                          "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": ["electricity",
                                        "natural gas"]},
            "fuel_switch_to": None,
            "end_use": {"primary": ["lighting"],
                        "secondary": ["heating", "secondary heating",
                                      "cooling"]},
            "technology_type": {"primary": "supply",
                                "secondary": "demand"},
            "technology": {"primary":
                           ["linear fluorescent (LED)",
                            "general service (LED)",
                            "external (LED)"],
                           "secondary":
                           ["windows conduction",
                            "windows solar"]}},
            {
            "name": "sample measure 4",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 10,
            "cost_units": "2014$/ft^2 floor",
            "energy_efficiency": {"primary":
                                  {"windows conduction": 20,
                                   "windows solar": 1},
                                  "secondary": None},
            "energy_efficiency_units": {"primary":
                                        {"windows conduction":
                                         "R Value",
                                         "windows solar": "SHGC"},
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home",
                          "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["heating"],
                        "secondary": None},
            "technology_type": {"primary": "demand",
                                "secondary": None},
            "technology": {"primary": ["windows conduction",
                           "windows solar"],
                           "secondary": None}},
            {
            "name": "sample measure 5",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 10,
            "cost_units": "2014$/ft^2 floor",
            "energy_efficiency": {"primary": 1, "secondary": None},
            "energy_efficiency_units": {"primary": "SHGC",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["heating"],
                        "secondary": None},
            "technology_type": {"primary": "demand",
                                "secondary": None},
            "technology": {"primary": ["windows solar"],
                           "secondary": None}},
            {
            "name": "sample measure 6",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 10,
            "cost_units": "2014$/ft^2 floor",
            "energy_efficiency": {"primary": {"windows conduction": 10,
                                              "windows solar": 1},
                                  "secondary": None},
            "energy_efficiency_units": {"primary":
                                        {"windows conduction":
                                         "R Value",
                                         "windows solar": "SHGC"},
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["heating", "secondary heating",
                                    "cooling"],
                        "secondary": None},
            "technology_type": {"primary": "demand",
                                "secondary": None},
            "technology": {"primary": ["windows conduction",
                                       "windows solar"],
                           "secondary": None}},
            {
            "name": "sample measure 7",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 10,
            "cost_units": "2014$/ft^2 floor",
            "energy_efficiency": {"primary":
                                  {"windows conduction": 0.4,
                                   "windows solar": 1},
                                  "secondary": None},
            "energy_efficiency_units": {"primary":
                                        {"windows conduction":
                                         "relative savings (constant)",
                                         "windows solar": "SHGC"},
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["heating", "secondary heating",
                                    "cooling"],
                        "secondary": None},
            "technology_type": {"primary": "demand",
                                "secondary": None},
            "technology": {"primary": ["windows conduction",
                                       "windows solar"],
                           "secondary": None}},
            {
            "name": "sample measure 8",  # Add heat/cool end uses later
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/ft^2 floor",
            "energy_efficiency": {"primary": 25,
                                  "secondary": None},
            "energy_efficiency_units": {"primary": "lm/W",
                                        "secondary": None},
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["assembly"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["lighting"],
                "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {
                "primary": [
                    "commercial light type X"],
                "secondary": None}},
            {
            "name": "sample measure 9",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {"primary": 25,
                                  "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}},
            {
            "name": "sample measure 10",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {"primary": 25,
                                  "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}},
            {
            "name": "sample measure 11",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {"primary": 25,
                                  "secondary": {
                                      "heating": 0.4,
                                      "secondary heating": 0.4,
                                      "cooling": -0.4}},
            "energy_efficiency_units": {"primary": "lm/W",
                                        "secondary":
                                        "relative savings (constant)"},
            "market_entry_year": 2010,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home",
                          "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": ["electricity",
                                        "natural gas"]},
            "fuel_switch_to": None,
            "end_use": {"primary": ["lighting"],
                        "secondary": ["heating", "secondary heating",
                                      "cooling"]},
            "technology_type": {"primary": "supply",
                                "secondary": "demand"},
            "technology": {"primary":
                           ["linear fluorescent (LED)",
                            "general service (LED)",
                            "external (LED)"],
                           "secondary":
                           ["windows conduction",
                            "windows solar"]}},
            {
            "name": "sample measure 12",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {"primary": 25,
                                  "secondary": {
                                      "heating": 0.4,
                                      "secondary heating": 0.4,
                                      "cooling": -0.4}},
            "energy_efficiency_units": {"primary": "lm/W",
                                        "secondary":
                                        "relative savings (constant)"},
            "market_entry_year": None,
            "market_exit_year": 2010,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home",
                          "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": ["electricity",
                                        "natural gas"]},
            "fuel_switch_to": None,
            "end_use": {"primary": ["lighting"],
                        "secondary": ["heating", "secondary heating",
                                      "cooling"]},
            "technology_type": {"primary": "supply",
                                "secondary": "demand"},
            "technology": {"primary":
                           ["linear fluorescent (LED)",
                            "general service (LED)",
                            "external (LED)"],
                           "secondary":
                           ["windows conduction",
                            "windows solar"]}},
            {
            "name": "sample measure 13",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {"primary": 25,
                                  "secondary": {
                                      "heating": 0.4,
                                      "secondary heating": 0.4,
                                      "cooling": -0.4}},
            "energy_efficiency_units": {"primary": "lm/W",
                                        "secondary":
                                        ["relative savings (dynamic)",
                                         2009]},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home",
                          "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": ["electricity",
                                        "natural gas"]},
            "fuel_switch_to": None,
            "end_use": {"primary": ["lighting"],
                        "secondary": ["heating", "secondary heating",
                                      "cooling"]},
            "technology_type": {"primary": "supply",
                                "secondary": "demand"},
            "technology": {"primary":
                           ["linear fluorescent (LED)",
                            "general service (LED)",
                            "external (LED)"],
                           "secondary":
                           ["windows conduction",
                            "windows solar",
                            "infiltration"]}},
            {
            "name": "sample measure 14",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {"new": 25, "existing": 25},
                "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": "electricity",
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}},
            {
            "name": "sample measure 16 (lighting S&C)",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 11,
            "cost_units": "2014$/ft^2 floor",
            "energy_efficiency": {
                "primary": 0.44,
                "secondary": None},
            "energy_efficiency_units": {
                "primary": "relative savings (constant)",
                "secondary": None},
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "add-on",
            "structure_type": ["new", "existing"],
            "bldg_type": ["assembly"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["lighting"],
                "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {
                "primary": [
                    "commercial light type X"],
                "secondary": None}},
            {
            "name": "sample measure 17",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {"new": 25, "existing": 25},
                "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": {
                "new": 0.25,
                "existing": 0.5},
            "market_scaling_fractions_source": {
                "new": {
                    "title": 'Sample title 1',
                    "author": 'Sample author 1',
                    "organization": 'Sample org 1',
                    "year": 'Sample year 1',
                    "URL": ('http://www.eia.gov/consumption/'
                            'commercial/data/2012/'),
                    "fraction_derivation": "Divide X by Y"},
                "existing": {
                    "title": 'Sample title 1',
                    "author": 'Sample author 1',
                    "organization": 'Sample org 1',
                    "year": 'Sample year 1',
                    "URL": ('http://www.eia.gov/consumption/'
                            'commercial/data/2012/'),
                    "fraction_derivation": "Divide X by Y"}},
            "product_lifetime": 1,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}},
            {
            "name": "sample measure 18",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {"primary": 25,
                                  "secondary": {
                                      "heating": 0.4,
                                      "secondary heating": 0.4,
                                      "cooling": -0.4}},
            "energy_efficiency_units": {"primary": "lm/W",
                                        "secondary":
                                        "relative savings (constant)"},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": {
                "new": 0.25,
                "existing": 0.5},
            "market_scaling_fractions_source": {
                "new": {
                    "title": 'Sample title 2',
                    "author": 'Sample author 2',
                    "organization": 'Sample org 2',
                    "year": 'Sample year 2',
                    "URL": ('http://www.eia.gov/consumption/'
                            'commercial/data/2012/'),
                    "fraction_derivation": "Divide X by Y"},
                "existing": {
                    "title": 'Sample title 2',
                    "author": 'Sample author 2',
                    "organization": 'Sample org 2',
                    "year": 'Sample year 2',
                    "URL": ('http://www.eia.gov/consumption/'
                            'residential/data/2009/'),
                    "fraction_derivation": "Divide X by Y"}},
            "product_lifetime": 1,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home",
                          "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": ["electricity",
                                        "natural gas"]},
            "fuel_switch_to": None,
            "end_use": {"primary": ["lighting"],
                        "secondary": ["heating", "secondary heating",
                                      "cooling"]},
            "technology_type": {"primary": "supply",
                                "secondary": "demand"},
            "technology": {"primary":
                           ["linear fluorescent (LED)",
                            "general service (LED)",
                            "external (LED)"],
                           "secondary":
                           ["windows conduction",
                            "windows solar"]}},
            {
            "name": "sample measure 19",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/ft^2 floor",
            "energy_efficiency": {"primary": 25,
                                  "secondary": None},
            "energy_efficiency_units": {"primary": "lm/W",
                                        "secondary": None},
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["assembly"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["lighting"],
                "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {
                "primary": [
                    "commercial light type X"],
                "secondary": None}}]
        cls.ok_tpmeas_fullchk_in = [
            measures_prep.Measure(
                handyvars, **x) for x in ok_measures_in[0:3]]
        cls.ok_tpmeas_partchk_in = [
            measures_prep.Measure(
                handyvars, **x) for x in ok_measures_in[3:18]]
        cls.ok_mapmeas_partchk_in = [
            measures_prep.Measure(
                handyvars, **x) for x in ok_measures_in[18:]]
        ok_distmeas_in = [{
            "name": "distrib measure 1",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": ["normal", 25, 5],
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {
                    "AIA_CZ1": {
                        "heating": ["normal", 30, 1],
                        "cooling": ["normal", 25, 2]},
                    "AIA_CZ2": {
                        "heating": 30,
                        "cooling": ["normal", 15, 4]}},
                "secondary": None},
            "energy_efficiency_units": {
                "primary": "COP", "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "supply",
                "secondary": None},
            "technology": {
                "primary": [
                    "boiler (electric)", "ASHP", "GSHP",
                    "room AC"],
                "secondary": None}},
            {
            "name": "distrib measure 2",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": ["lognormal", 3.22, 0.06],
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": ["normal", 25, 5],
                "secondary": None},
            "energy_efficiency_units": {
                "primary": "EF", "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": ["normal", 1, 1],
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {
                "primary": ["natural gas"], "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["water heating"],
                "secondary": None},
            "technology_type": {
                "primary": "supply", "secondary": None},
            "technology": {
                "primary": None, "secondary": None}},
            {
            "name": "distrib measure 3",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": ["normal", 10, 5],
            "cost_units": "2014$/ft^2 floor",
            "energy_efficiency": {
                "primary": {
                    "windows conduction": [
                        "lognormal", 2.29, 0.14],
                    "windows solar": [
                        "normal", 1, 0.1]},
                "secondary": None},
            "energy_efficiency_units": {
                "primary": {
                    "windows conduction": "R Value",
                    "windows solar": "SHGC"},
                "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": [
                    "heating", "secondary heating", "cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "demand", "secondary": None},
            "technology": {
                "primary": [
                    "windows conduction", "windows solar"],
                "secondary": None}}]
        cls.ok_distmeas_in = [
            measures_prep.Measure(
                handyvars, **x) for x in ok_distmeas_in]
        ok_partialmeas_in = [{
            "name": "partial measure 1",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": 25, "secondary": None},
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "energy_efficiency_units": {
                "primary": "COP", "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "supply",
                "secondary": None},
            "technology": {
                "primary": [
                    "boiler (electric)", "ASHP"],
                "secondary": None}},
            {
            "name": "partial measure 2",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": 25, "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "energy_efficiency_units": {
                "primary": "COP", "secondary": None},
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "supply",
                "secondary": None},
            "technology": {
                "primary": [
                    "linear fluorescent (LED)",
                    "general service (LED)",
                    "external (LED)", "GSHP", "ASHP"],
                "secondary": None}}]
        cls.ok_partialmeas_in = [
            measures_prep.Measure(
                handyvars, **x) for x in ok_partialmeas_in]
        failmeas_in = [{
            "name": "blank measure 1",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 10,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": 10, "secondary": None},
            "energy_efficiency_units": {
                "primary": "COP", "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["cooling"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": ["boiler (electric)"],
                           "secondary": None}},
            {
            "name": "blank measure 2",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 10,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {
                    "AIA_CZ1": {
                        "heating": 30, "cooling": 25},
                    "AIA_CZ2": {
                        "heating": 30, "cooling": 15}},
                "secondary": None},
            "energy_efficiency_units": {
                "primary": "COP", "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "supply",
                "secondary": None},
            "technology": {
                "primary": [
                    "linear fluorescent (LED)",
                    "general service (LED)",
                    "external (LED)"],
                "secondary": None}},
            {
            "name": "blank measure 3",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": 25, "secondary": None},
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "energy_efficiency_units": {
                "primary": "lm/W", "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["lighting"],
                "secondary": [
                    "heating", "secondary heating",
                    "cooling"]},
            "technology_type": {
                "primary": "supply",
                "secondary": "demand"},
            "technology": {
                "primary": [
                    "linear fluorescent (LED)",
                    "general service (LED)",
                    "external (LED)"],
                "secondary": [
                    "windows conduction",
                    "windows solar"]}},
            {
            "name": "blank measure 4",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": 25, "secondary": None},
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "energy_efficiency_units": {
                "primary": "lm/W", "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "bldg_type": ["single family home"],
            "climate_zone": "AIA_CZ1",
            "fuel_type": {
                "primary": ["solar"], "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["lighting"],
                "secondary": [
                    "heating", "secondary heating",
                    "cooling"]},
            "technology_type": {
                "primary": "supply", "secondary": "demand"},
            "technology": {
                "primary": [
                    "linear fluorescent (LED)",
                    "general service (LED)",
                    "external (LED)"],
                "secondary": [
                    "windows conduction",
                    "windows solar"]}}]
        cls.failmeas_in = [
            measures_prep.Measure(
                handyvars, **x) for x in failmeas_in]
        warnmeas_in = [{
            "name": "warn measure 1",
            "active": 1,
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": 25,
                "secondary": {
                    "heating": 0.4,
                    "secondary heating": 0.4,
                    "cooling": -0.4}},
            "energy_efficiency_units": {
                "primary": "lm/W",
                "secondary": "relative savings (constant)"},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": {
                "new": 0.25,
                "existing": 0.5},
            "market_scaling_fractions_source": {
                "new": {
                    "title": None,
                    "author": None,
                    "organization": None,
                    "year": None,
                    "URL": None,
                    "fraction_derivation": None},
                "existing": {
                    "title": None,
                    "author": None,
                    "organization": None,
                    "year": None,
                    "URL": None,
                    "fraction_derivation": None}},
            "product_lifetime": 1,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": [
                "single family home",
                "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": [
                    "electricity",
                    "natural gas"]},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["lighting"],
                "secondary": [
                    "heating", "secondary heating",
                    "cooling"]},
            "technology_type": {"primary": "supply",
                                "secondary": "demand"},
            "technology": {
                "primary": [
                    "linear fluorescent (LED)",
                    "general service (LED)",
                    "external (LED)"],
                "secondary":[
                    "windows conduction",
                    "windows solar"]}},
            {
            "name": "warn measure 2",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "active": 1,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": 25,
                "secondary": {
                    "heating": 0.4,
                    "secondary heating": 0.4,
                    "cooling": -0.4}},
            "energy_efficiency_units": {
                "primary": "lm/W",
                "secondary": "relative savings (constant)"},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": {
                "new": 0.25,
                "existing": 0.5},
            "market_scaling_fractions_source": {
                "new": {
                    "title": "Sample title",
                    "author": "Sample author",
                    "organization": "Sample organization",
                    "year": "http://www.sciencedirectcom",
                    "URL": "some BS",
                    "fraction_derivation": None},
                "existing": {
                    "title": "Sample title",
                    "author": "Sample author",
                    "organization": "Sample organization",
                    "year": "Sample year",
                    "URL": "http://www.sciencedirect.com",
                    "fraction_derivation": None}},
            "product_lifetime": 1,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": [
                "single family home",
                "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": [
                    "electricity",
                    "natural gas"]},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["lighting"],
                "secondary": [
                    "heating", "secondary heating",
                    "cooling"]},
            "technology_type": {"primary": "supply",
                                "secondary": "demand"},
            "technology": {
                "primary": [
                    "linear fluorescent (LED)",
                    "general service (LED)",
                    "external (LED)"],
                "secondary":[
                    "windows conduction",
                    "windows solar"]}},
            {
            "name": "warn measure 3",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "active": 1,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": 25,
                "secondary": {
                    "heating": 0.4,
                    "secondary heating": 0.4,
                    "cooling": -0.4}},
            "energy_efficiency_units": {
                "primary": "lm/W",
                "secondary": "relative savings (constant)"},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": {
                "new": 0.25,
                "existing": 0.5},
            "market_scaling_fractions_source": {
                "new": {
                    "title": "Sample title",
                    "author": None,
                    "organization": "Sample organization",
                    "year": "Sample year",
                    "URL": "https://bpd.lbl.gov/",
                    "fraction_derivation": "Divide X by Y"},
                "existing": {
                    "title": "Sample title",
                    "author": None,
                    "organization": "Sample organization",
                    "year": "Sample year",
                    "URL": "https://cms.doe.gov/data/green-button",
                    "fraction_derivation": "Divide X by Y"}},
            "product_lifetime": 1,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": [
                "single family home",
                "multi family home"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": [
                    "electricity",
                    "natural gas"]},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["lighting"],
                "secondary": [
                    "heating", "secondary heating",
                    "cooling"]},
            "technology_type": {"primary": "supply",
                                "secondary": "demand"},
            "technology": {
                "primary": [
                    "linear fluorescent (LED)",
                    "general service (LED)",
                    "external (LED)"],
                "secondary":[
                    "windows conduction",
                    "windows solar"]}}]
        cls.warnmeas_in = [
            measures_prep.Measure(
                handyvars, **x) for x in warnmeas_in]
        cls.ok_tpmeas_fullchk_msegout = [{
            "stock": {
                "total": {
                    "all": {"2009": 72, "2010": 72},
                    "measure": {"2009": 72, "2010": 72}},
                "competed": {
                    "all": {"2009": 72, "2010": 72},
                    "measure": {"2009": 72, "2010": 72}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 229.68, "2010": 230.4},
                    "efficient": {"2009": 117.0943, "2010": 117.4613}},
                "competed": {
                    "baseline": {"2009": 229.68, "2010": 230.4},
                    "efficient": {"2009": 117.0943, "2010": 117.4613}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 13056.63, "2010": 12941.16},
                    "efficient": {"2009": 6656.461, "2010": 6597.595}},
                "competed": {
                    "baseline": {"2009": 13056.63, "2010": 12941.16},
                    "efficient": {"2009": 6656.461, "2010": 6597.595}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 710, "2010": 710},
                        "efficient": {"2009": 1800, "2010": 1800}},
                    "competed": {
                        "baseline": {"2009": 710, "2010": 710},
                        "efficient": {"2009": 1800, "2010": 1800}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 2328.955, "2010": 2227.968},
                        "efficient": {"2009": 1187.336, "2010": 1135.851}},
                    "competed": {
                        "baseline": {"2009": 2328.955, "2010": 2227.968},
                        "efficient": {"2009": 1187.336, "2010": 1135.851}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 430868.63, "2010": 427058.3},
                        "efficient": {"2009": 219663.21, "2010": 217720.65}},
                    "competed": {
                        "baseline": {"2009": 430868.63, "2010": 427058.3},
                        "efficient": {"2009": 219663.21, "2010": 217720.65}}}},
            "lifetime": {"baseline": {"2009": 75, "2010": 75},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 15, "2010": 15},
                    "measure": {"2009": 15, "2010": 15}},
                "competed": {
                    "all": {"2009": 15, "2010": 15},
                    "measure": {"2009": 15, "2010": 15}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 15.15, "2010": 15.15},
                    "efficient": {"2009": 10.908, "2010": 10.908}},
                "competed": {
                    "baseline": {"2009": 15.15, "2010": 15.15},
                    "efficient": {"2009": 10.908, "2010": 10.908}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 856.2139, "2010": 832.0021},
                    "efficient": {"2009": 616.474, "2010": 599.0415}},
                "competed": {
                    "baseline": {"2009": 856.2139, "2010": 832.0021},
                    "efficient": {"2009": 616.474, "2010": 599.0415}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 270, "2010": 270},
                        "efficient": {"2009": 375, "2010": 375}},
                    "competed": {
                        "baseline": {"2009": 270, "2010": 270},
                        "efficient": {"2009": 375, "2010": 375}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 170.892, "2010": 163.317},
                        "efficient": {"2009": 123.0422, "2010": 117.5882}},
                    "competed": {
                        "baseline": {"2009": 170.892, "2010": 163.317},
                        "efficient": {"2009": 123.0422, "2010": 117.5882}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 28255.06, "2010": 27456.07},
                        "efficient": {"2009": 20343.64, "2010": 19768.37}},
                    "competed": {
                        "baseline": {"2009": 28255.06, "2010": 27456.07},
                        "efficient": {"2009": 20343.64, "2010": 19768.37}}}},
            "lifetime": {"baseline": {"2009": 180, "2010": 180},
                         "measure": 1}},
                        {
            "stock": {
                "total": {
                    "all": {"2009": 333, "2010": 333},
                    "measure": {"2009": 333, "2010": 333}},
                "competed": {
                    "all": {"2009": 333, "2010": 333},
                    "measure": {"2009": 333, "2010": 333}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 1062.27, "2010": 1065.6},
                    "efficient": {"2009": 956.043, "2010": 959.04}},
                "competed": {
                    "baseline": {"2009": 1062.27, "2010": 1065.6},
                    "efficient": {"2009": 956.043, "2010": 959.04}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 60386.89, "2010": 59852.87},
                    "efficient": {"2009": 54348.2, "2010": 53867.58}},
                "competed": {
                    "baseline": {"2009": 60386.89, "2010": 59852.87},
                    "efficient": {"2009": 54348.2, "2010": 53867.58}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 55500, "2010": 55500},
                        "efficient": {"2009": 166500, "2010": 166500}},
                    "competed": {
                        "baseline": {"2009": 55500, "2010": 55500},
                        "efficient": {"2009": 166500, "2010": 166500}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 10771.42, "2010": 10304.35},
                        "efficient": {"2009": 9694.276, "2010": 9273.917}},
                    "competed": {
                        "baseline": {"2009": 10771.42, "2010": 10304.35},
                        "efficient": {"2009": 9694.276, "2010": 9273.917}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 1992767.41, "2010": 1975144.64},
                        "efficient": {"2009": 1793490.67, "2010": 1777630.18}},
                    "competed": {
                        "baseline": {"2009": 1992767.41, "2010": 1975144.64},
                        "efficient": {
                            "2009": 1793490.67, "2010": 1777630.18}}}},
            "lifetime": {"baseline": {"2009": 16, "2010": 16},
                         "measure": 1}}]
        # Correct consumer choice dict outputs
        compete_choice_val = {
            "b1": {"2009": None, "2010": None},
            "b2": {"2009": None, "2010": None}}
        cls.ok_tpmeas_fullchk_competechoiceout = [{
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'boiler (electric)', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'boiler (electric)', 'new'"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity',   'heating', 'supply', "
             "'boiler (electric)',existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', heating', 'supply', "
             "'ASHP', 'existing'"): compete_choice_val,
            ("'primary', 'AIA_CZ1 'single family home', "
             "'electricity', heating', 'supply', "
             "'GSHP', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ1 'single family home', "
             "'electricity', cooling', 'supply', "
             "'ASHP', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ1 'single family home', "
             "'electricity', cooling', 'supply', "
             "'GSHP', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ1 'single family home', "
             "'electricity', cooling', 'supply', "
             "'room AC', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'boiler (electric)', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'ASHP', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'heating', 'supply', "
             "'GSHP', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'ASHP', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'GSHP', 'existing'"): compete_choice_val,
            ("('primary', 'AIA_CZ2', 'single family home', "
             "'electricity', 'cooling', 'supply', "
             "'room AC', 'existing'"): compete_choice_val},
            {
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'natural gas', 'water heating', 'supply', "
             "'','new'"): compete_choice_val},
            {
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'other (grid electric)', "
             "'freezers', 'new')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'other (grid electric)', "
             "'freezers', 'existing')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'refrigeration', None, "
             "'existing')"): compete_choice_val,
            ("('primary', 'AIA_CZ1', 'single family home', "
             "'electricity', 'refrigeration', None, "
             "'new')"): compete_choice_val}]
        cls.ok_tpmeas_fullchk_msegadjout = [{
            "stock-and-flow": {
                "original stock (total)": {},
                "adjusted stock (previously captured)": {},
                "adjusted stock (competed)": {},
                "adjusted stock (competed and captured)": {}},
            "market share": {
                "original stock (total captured)": {},
                "original stock (competed and captured)": {},
                "adjusted stock (total captured)": {},
                "adjusted stock (competed and captured)": {}}},
            {
            "stock-and-flow": {
                "original stock (total)": {},
                "adjusted stock (previously captured)": {},
                "adjusted stock (competed)": {},
                "adjusted stock (competed and captured)": {}},
            "market share": {
                "original stock (total captured)": {},
                "original stock (competed and captured)": {},
                "adjusted stock (total captured)": {},
                "adjusted stock (competed and captured)": {}}},
            {
            "stock-and-flow": {
                "original stock (total)": {},
                "adjusted stock (previously captured)": {},
                "adjusted stock (competed)": {},
                "adjusted stock (competed and captured)": {}},
            "market share": {
                "original stock (total captured)": {},
                "original stock (competed and captured)": {},
                "adjusted stock (total captured)": {},
                "adjusted stock (competed and captured)": {}}}]
        cls.ok_tpmeas_fullchk_supplydemandout = [{
            "savings": {
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'boiler (electric)', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'ASHP', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'GSHP', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'ASHP', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'GSHP', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'room AC', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'boiler (electric)', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'ASHP', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'GSHP', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'ASHP', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'GSHP', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'room AC', 'new')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'boiler (electric)', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'ASHP', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'GSHP', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'ASHP', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'GSHP', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'room AC', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'boiler (electric)', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'ASHP', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'GSHP', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'ASHP', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'GSHP', 'existing')"): {"2009": 0, "2010": 0},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'room AC', 'existing')"): {"2009": 0, "2010": 0}},
            "total": {
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'boiler (electric)', 'new')"): {
                    "2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'ASHP', 'new')"): {"2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'GSHP', 'new')"): {"2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'ASHP', 'new')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'GSHP', 'new')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'room AC', 'new')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'boiler (electric)', 'new')"): {
                    "2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'ASHP', 'new')"): {"2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'GSHP', 'new')"): {"2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'ASHP', 'new')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'GSHP', 'new')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'room AC', 'new')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'boiler (electric)', 'existing')"): {
                    "2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'ASHP', 'existing')"): {"2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'GSHP', 'existing')"): {"2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'ASHP', 'existing')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'GSHP', 'existing')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ1', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'room AC', 'existing')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'boiler (electric)', 'existing')"): {
                    "2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'ASHP', 'existing')"): {"2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'heating', 'supply', "
                 "'GSHP', 'existing')"): {"2009": 28.71, "2010": 28.80},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'ASHP', 'existing')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'GSHP', 'existing')"): {"2009": 108.46, "2010": 108.8},
                ("('primary', 'AIA_CZ2', 'single family home', "
                 "'electricity', 'cooling', 'supply', "
                 "'room AC', 'existing')"): {"2009": 108.46, "2010": 108.8}}},
            {"savings": {}, "total": {}},
            {"savings": {}, "total": {}}]
        cls.ok_tpmeas_fullchk_break_out = [{
            'AIA CZ1': {
                'Residential': {
                    'Cooling': {"2009": 0.375, "2010": 0.374},
                    'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {},
                    'Heating': {"2009": 0.125, "2010": 0.124}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ2': {
                'Residential': {
                    'Cooling': {"2009": 0.375, "2010": 0.374},
                    'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {},
                    'Heating': {"2009": 0.125, "2010": 0.124}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ3': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ4': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ5': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}}},
            {
            'AIA CZ1': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {},
                    'Water Heating': {"2009": 1, "2010": 1},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ2': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ3': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ4': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ5': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}}},
            {
            'AIA CZ1': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {"2009": 1, "2010": 1},
                    'Other': {},
                    'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ2': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ3': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ4': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}},
            'AIA CZ5': {
                'Residential': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}},
                'Commercial': {
                    'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                    'Refrigeration': {}, 'Other': {}, 'Water Heating': {},
                    'Computers and Electronics': {}, 'Heating': {}}}}]
        cls.ok_tpmeas_partchk_msegout = [{
            "stock": {
                "total": {
                    "all": {"2009": 148, "2010": 148},
                    "measure": {"2009": 148, "2010": 148}},
                "competed": {
                    "all": {"2009": 148, "2010": 148},
                    "measure": {"2009": 148, "2010": 148}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 648.47, "2010": 650.43},
                    "efficient": {"2009": 550.0692, "2010": 551.722}},
                "competed": {
                    "baseline": {"2009": 648.47, "2010": 650.43},
                    "efficient": {"2009": 550.0692, "2010": 551.722}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 36855.9, "2010": 36504.45},
                    "efficient": {"2009": 31262.24, "2010": 30960.7}},
                "competed": {
                    "baseline": {"2009": 36855.9, "2010": 36504.45},
                    "efficient": {"2009": 31262.24, "2010": 30960.7}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 2972, "2010": 2972},
                        "efficient": {"2009": 3700, "2010": 3700}},
                    "competed": {
                        "baseline": {"2009": 2972, "2010": 2972},
                        "efficient": {"2009": 3700, "2010": 3700}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 6601.968, "2010": 6315.443},
                        "efficient": {"2009": 5603.723, "2010": 5360.489}},
                    "competed": {
                        "baseline": {"2009": 6601.968, "2010": 6315.443},
                        "efficient": {"2009": 5603.723, "2010": 5360.489}}},
                "carbon": {
                    "total": {
                        "baseline": {
                            "2009": 1216244.58, "2010": 1204646.90},
                        "efficient": {
                            "2009": 1031653.83, "2010": 1021703.20}},
                    "competed": {
                        "baseline": {
                            "2009": 1216244.58, "2010": 1204646.90},
                        "efficient": {
                            "2009": 1031653.83, "2010": 1021703.20}}}},
            "lifetime": {"baseline": {"2009": 200, "2010": 200},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 1600000000, "2010": 2000000000},
                    "measure": {"2009": 1600000000, "2010": 2000000000}},
                "competed": {
                    "all": {"2009": 1600000000, "2010": 2000000000},
                    "measure": {"2009": 1600000000, "2010": 2000000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 12.76, "2010": 12.8},
                    "efficient": {"2009": 3.509, "2010": 3.52}},
                "competed": {
                    "baseline": {"2009": 12.76, "2010": 12.8},
                    "efficient": {"2009": 3.509, "2010": 3.52}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 725.3681, "2010": 718.9534},
                    "efficient": {"2009": 199.4762, "2010": 197.7122}},
                "competed": {
                    "baseline": {"2009": 725.3681, "2010": 718.9534},
                    "efficient": {"2009": 199.4762, "2010": 197.7122}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {
                            "2009": 20400000000, "2010": 24600000000},
                        "efficient": {
                            "2009": 16000000000, "2010": 20000000000}},
                    "competed": {
                        "baseline": {
                            "2009": 20400000000, "2010": 24600000000},
                        "efficient": {
                            "2009": 16000000000, "2010": 20000000000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 129.3864, "2010": 123.776},
                        "efficient": {"2009": 35.58126, "2010": 34.0384}},
                    "competed": {
                        "baseline": {"2009": 129.3864, "2010": 123.776},
                        "efficient": {"2009": 35.58126, "2010": 34.0384}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 23937.15, "2010": 23725.46},
                        "efficient": {"2009": 6582.715, "2010": 6524.502}},
                    "competed": {
                        "baseline": {"2009": 23937.15, "2010": 23725.46},
                        "efficient": {"2009": 6582.715, "2010": 6524.502}}}},
            "lifetime": {"baseline": {"2009": 105, "2010": 105},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 600000000, "2010": 800000000},
                    "measure": {"2009": 600000000, "2010": 800000000}},
                "competed": {
                    "all": {"2009": 600000000, "2010": 800000000},
                    "measure": {"2009": 600000000, "2010": 800000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 6.38, "2010": 6.4},
                    "efficient": {"2009": 3.19, "2010": 3.2}},
                "competed": {
                    "baseline": {"2009": 6.38, "2010": 6.4},
                    "efficient": {"2009": 3.19, "2010": 3.2}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 362.684, "2010": 359.4767},
                    "efficient": {"2009": 181.342, "2010": 179.7383}},
                "competed": {
                    "baseline": {"2009": 362.684, "2010": 359.4767},
                    "efficient": {"2009": 181.342, "2010": 179.7383}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {
                            "2009": 1200000000, "2010": 1600000000},
                        "efficient": {
                            "2009": 6000000000, "2010": 8000000000}},
                    "competed": {
                        "baseline": {
                            "2009": 1200000000, "2010": 1600000000},
                        "efficient": {
                            "2009": 6000000000, "2010": 8000000000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 64.6932, "2010": 61.888},
                        "efficient": {"2009": 32.3466, "2010": 30.944}},
                    "competed": {
                        "baseline": {"2009": 64.6932, "2010": 61.888},
                        "efficient": {"2009": 32.3466, "2010": 30.944}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 11968.57, "2010": 11862.73},
                        "efficient": {"2009": 5984.287, "2010": 5931.365}},
                    "competed": {
                        "baseline": {"2009": 11968.57, "2010": 11862.73},
                        "efficient": {"2009": 5984.287, "2010": 5931.365}}}},
            "lifetime": {"baseline": {"2009": 20, "2010": 20},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 600000000, "2010": 800000000},
                    "measure": {"2009": 600000000, "2010": 800000000}},
                "competed": {
                    "all": {"2009": 600000000, "2010": 800000000},
                    "measure": {"2009": 600000000, "2010": 800000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 146.74, "2010": 147.2},
                    "efficient": {"2009": 55.29333, "2010": 55.46667}},
                "competed": {
                    "baseline": {"2009": 146.74, "2010": 147.2},
                    "efficient": {"2009": 55.29333, "2010": 55.46667}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 8341.733, "2010": 8267.964},
                    "efficient": {"2009": 3143.262, "2010": 3115.465}},
                "competed": {
                    "baseline": {"2009": 8341.733, "2010": 8267.964},
                    "efficient": {"2009": 3143.262, "2010": 3115.465}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {
                            "2009": 3100000000, "2010": 4133333333.33},
                        "efficient": {
                            "2009": 6000000000, "2010": 8000000000}},
                    "competed": {
                        "baseline": {
                            "2009": 3100000000, "2010": 4133333333.33},
                        "efficient": {
                            "2009": 6000000000, "2010": 8000000000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 1487.944, "2010": 1423.424},
                        "efficient": {"2009": 560.6744, "2010": 536.3627}},
                    "competed": {
                        "baseline": {"2009": 1487.944, "2010": 1423.424},
                        "efficient": {"2009": 560.6744, "2010": 536.3627}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 275277.18, "2010": 272842.8},
                        "efficient": {"2009": 103727.63, "2010": 102810.33}},
                    "competed": {
                        "baseline": {"2009": 275277.18, "2010": 272842.8},
                        "efficient": {"2009": 103727.63, "2010": 102810.33}}}},
            "lifetime": {"baseline": {"2009": 51.67, "2010": 51.67},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 600000000, "2010": 800000000},
                    "measure": {"2009": 600000000, "2010": 800000000}},
                "competed": {
                    "all": {"2009": 600000000, "2010": 800000000},
                    "measure": {"2009": 600000000, "2010": 800000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 146.74, "2010": 147.2},
                    "efficient": {"2009": 52.10333, "2010": 52.26667}},
                "competed": {
                    "baseline": {"2009": 146.74, "2010": 147.2},
                    "efficient": {"2009": 52.10333, "2010": 52.26667}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 8341.733, "2010": 8267.964},
                    "efficient": {"2009": 2961.92, "2010": 2935.726}},
                "competed": {
                    "baseline": {"2009": 8341.733, "2010": 8267.964},
                    "efficient": {"2009": 2961.92, "2010": 2935.726}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {
                            "2009": 3100000000, "2010": 4133333333.33},
                        "efficient": {
                            "2009": 6000000000, "2010": 8000000000}},
                    "competed": {
                        "baseline": {
                            "2009": 3100000000, "2010": 4133333333.33},
                        "efficient": {
                            "2009": 6000000000, "2010": 8000000000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 1487.944, "2010": 1423.424},
                        "efficient": {"2009": 528.3278, "2010": 505.4187}},
                    "competed": {
                        "baseline": {"2009": 1487.944, "2010": 1423.424},
                        "efficient": {"2009": 528.3278, "2010": 505.4187}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 275277.18, "2010": 272842.8},
                        "efficient": {"2009": 97743.35, "2010": 96878.97}},
                    "competed": {
                        "baseline": {"2009": 275277.18, "2010": 272842.8},
                        "efficient": {"2009": 97743.35, "2010": 96878.97}}}},
            "lifetime": {"baseline": {"2009": 51.67, "2010": 51.67},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}},
                "competed": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 31.9, "2010": 32.0},
                    "efficient": {"2009": 17.86, "2010": 17.92}},
                "competed": {
                    "baseline": {"2009": 31.9, "2010": 32.0},
                    "efficient": {"2009": 17.86, "2010": 17.92}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 1813.42, "2010": 1797.38},
                    "efficient": {"2009": 1015.52, "2010": 1006.53}},
                "competed": {
                    "baseline": {"2009": 1813.42, "2010": 1797.38},
                    "efficient": {"2009": 1015.52, "2010": 1006.53}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 154000000, "2010": 154000000},
                        "efficient": {"2009": 275000000, "2010": 275000000}},
                    "competed": {
                        "baseline": {"2009": 154000000, "2010": 154000000},
                        "efficient": {"2009": 275000000, "2010": 275000000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 289.65, "2010": 273.6},
                        "efficient": {"2009": 162.21, "2010": 153.22}},
                    "competed": {
                        "baseline": {"2009": 289.65, "2010": 273.6},
                        "efficient": {"2009": 162.21, "2010": 153.22}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 59842.87, "2010": 59313.65},
                        "efficient": {"2009": 33512, "2010": 33215.65}},
                    "competed": {
                        "baseline": {"2009": 59842.87, "2010": 59313.65},
                        "efficient": {"2009": 33512, "2010": 33215.65}}}},
            "lifetime": {"baseline": {"2009": 140, "2010": 140},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 1.5, "2010": 2.25},
                    "measure": {"2009": 1.5, "2010": 2.25}},
                "competed": {
                    "all": {"2009": 1.5, "2010": 2.25},
                    "measure": {"2009": 1.5, "2010": 2.25}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 1.515, "2010": 2.2725},
                    "efficient": {"2009": 1.0908, "2010": 1.6362}},
                "competed": {
                    "baseline": {"2009": 1.515, "2010": 2.2725},
                    "efficient": {"2009": 1.0908, "2010": 1.6362}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 85.62139, "2010": 124.8003},
                    "efficient": {"2009": 61.6474, "2010": 89.85622}},
                "competed": {
                    "baseline": {"2009": 85.62139, "2010": 124.8003},
                    "efficient": {"2009": 61.6474, "2010": 89.85622}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 27, "2010": 40.5},
                        "efficient": {"2009": 37.5, "2010": 56.25}},
                    "competed": {
                        "baseline": {"2009": 27, "2010": 40.5},
                        "efficient": {"2009": 37.5, "2010": 56.25}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 17.0892, "2010": 24.49755},
                        "efficient": {"2009": 12.30422, "2010": 17.63823}},
                    "competed": {
                        "baseline": {"2009": 17.0892, "2010": 24.49755},
                        "efficient": {"2009": 12.30422, "2010": 17.63823}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 2825.506, "2010": 4118.409},
                        "efficient": {"2009": 2034.364, "2010": 2965.256}},
                    "competed": {
                        "baseline": {"2009": 2825.506, "2010": 4118.409},
                        "efficient": {"2009": 2034.364, "2010": 2965.256}}}},
            "lifetime": {"baseline": {"2009": 180, "2010": 180},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 13.5, "2010": 12.75},
                    "measure": {"2009": 13.5, "2010": 12.75}},
                "competed": {
                    "all": {"2009": 13.5, "2010": 12.75},
                    "measure": {"2009": 13.5, "2010": 12.75}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 13.635, "2010": 12.8775},
                    "efficient": {"2009": 9.8172, "2010": 9.2718}},
                "competed": {
                    "baseline": {"2009": 13.635, "2010": 12.8775},
                    "efficient": {"2009": 9.8172, "2010": 9.2718}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 770.5925, "2010": 707.2018},
                    "efficient": {"2009": 554.8266, "2010": 509.1853}},
                "competed": {
                    "baseline": {"2009": 770.5925, "2010": 707.2018},
                    "efficient": {"2009": 554.8266, "2010": 509.1853}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 243, "2010": 229.5},
                        "efficient": {"2009": 337.5, "2010": 318.75}},
                    "competed": {
                        "baseline": {"2009": 243, "2010": 229.5},
                        "efficient": {"2009": 337.5, "2010": 318.75}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 153.8028, "2010": 138.8195},
                        "efficient": {"2009": 110.738, "2010": 99.94998}},
                    "competed": {
                        "baseline": {"2009": 153.8028, "2010": 138.8195},
                        "efficient": {"2009": 110.738, "2010": 99.94998}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 25429.55, "2010": 23337.66},
                        "efficient": {"2009": 18309.28, "2010": 16803.11}},
                    "competed": {
                        "baseline": {"2009": 25429.55, "2010": 23337.66},
                        "efficient": {"2009": 18309.28, "2010": 16803.11}}}},
            "lifetime": {"baseline": {"2009": 180, "2010": 180},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 148, "2010": 148},
                    "measure": {"2009": 0, "2010": 148}},
                "competed": {
                    "all": {"2009": 18.17, "2010": 148},
                    "measure": {"2009": 0, "2010": 148}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 648.47, "2010": 650.43},
                    "efficient": {"2009": 648.47, "2010": 551.722}},
                "competed": {
                    "baseline": {"2009": 79.78, "2010": 650.43},
                    "efficient": {"2009": 79.78, "2010": 551.722}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 36855.9, "2010": 36504.45},
                    "efficient": {"2009": 36855.9, "2010": 30960.7}},
                "competed": {
                    "baseline": {"2009": 4534.446, "2010": 36504.45},
                    "efficient": {"2009": 4534.446, "2010": 30960.7}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 2972, "2010": 2972},
                        "efficient": {"2009": 2972, "2010": 3700}},
                    "competed": {
                        "baseline": {"2009": 364.016, "2010": 2972},
                        "efficient": {"2009": 364.016, "2010": 3700}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 6601.968, "2010": 6315.443},
                        "efficient": {"2009": 6601.968, "2010": 5360.489}},
                    "competed": {
                        "baseline": {"2009": 812.27, "2010": 6315.443},
                        "efficient": {"2009": 812.27, "2010": 5360.489}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 1216244.58, "2010": 1204646.90},
                        "efficient": {"2009": 1216244.58, "2010": 1021703.20}},
                    "competed": {
                        "baseline": {"2009": 149636.72, "2010": 1204646.90},
                        "efficient": {
                            "2009": 149636.72, "2010": 1021703.20}}}},
            "lifetime": {"baseline": {"2009": 200, "2010": 200},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 148, "2010": 148},
                    "measure": {"2009": 148, "2010": 0}},
                "competed": {
                    "all": {"2009": 148, "2010": 148},
                    "measure": {"2009": 148, "2010": 0}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 648.47, "2010": 650.43},
                    "efficient": {"2009": 550.0692, "2010": 650.43}},
                "competed": {
                    "baseline": {"2009": 648.47, "2010": 650.43},
                    "efficient": {"2009": 550.0692, "2010": 650.43}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 36855.9, "2010": 36504.45},
                    "efficient": {"2009": 31262.24, "2010": 36504.45}},
                "competed": {
                    "baseline": {"2009": 36855.9, "2010": 36504.45},
                    "efficient": {"2009": 31262.24, "2010": 36504.45}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 2972, "2010": 2972},
                        "efficient": {"2009": 3700, "2010": 2972}},
                    "competed": {
                        "baseline": {"2009": 2972, "2010": 2972},
                        "efficient": {"2009": 3700, "2010": 2972}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 6601.968, "2010": 6315.443},
                        "efficient": {"2009": 5603.723, "2010": 6315.443}},
                    "competed": {
                        "baseline": {"2009": 6601.968, "2010": 6315.443},
                        "efficient": {"2009": 5603.723, "2010": 6315.443}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 1216244.58, "2010": 1204646.90},
                        "efficient": {"2009": 1031653.83, "2010": 1204646.90}},
                    "competed": {
                        "baseline": {"2009": 1216244.58, "2010": 1204646.90},
                        "efficient": {
                            "2009": 1031653.83, "2010": 1204646.90}}}},
            "lifetime": {"baseline": {"2009": 200, "2010": 200},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 148, "2010": 148},
                    "measure": {"2009": 148, "2010": 148}},
                "competed": {
                    "all": {"2009": 148, "2010": 148},
                    "measure": {"2009": 148, "2010": 148}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 870.17, "2010": 872.73},
                    "efficient": {"2009": 742.209, "2010": 680.162}},
                "competed": {
                    "baseline": {"2009": 870.17, "2010": 872.73},
                    "efficient": {"2009": 742.209, "2010": 680.162}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 49448.84, "2010": 48952.76},
                    "efficient": {"2009": 42176.13, "2010": 38153.06}},
                "competed": {
                    "baseline": {"2009": 49448.84, "2010": 48952.76},
                    "efficient": {"2009": 42176.13, "2010": 38153.06}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 2972, "2010": 2972},
                        "efficient": {"2009": 3700, "2010": 3700}},
                    "competed": {
                        "baseline": {"2009": 2972, "2010": 2972},
                        "efficient": {"2009": 3700, "2010": 3700}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 8884.55, "2010": 8498.72},
                        "efficient": {"2009": 7581.96, "2010": 6621.936}},
                    "competed": {
                        "baseline": {"2009": 8884.55, "2010": 8498.72},
                        "efficient": {"2009": 7581.96, "2010": 6621.936}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 1631811.885, "2010": 1615440.956},
                        "efficient": {
                            "2009": 1391812.161, "2010": 1259050.87}},
                    "competed": {
                        "baseline": {"2009": 1631811.885, "2010": 1615440.956},
                        "efficient": {
                            "2009": 1391812.161, "2010": 1259050.87}}}},
            "lifetime": {"baseline": {"2009": 200, "2010": 200},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 15, "2010": 15},
                    "measure": {"2009": 15, "2010": 15}},
                "competed": {
                    "all": {"2009": 15, "2010": 15},
                    "measure": {"2009": 15, "2010": 15}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 15.15, "2010": 15.15},
                    "efficient": {"2009": 34.452, "2010": 34.56}},
                "competed": {
                    "baseline": {"2009": 15.15, "2010": 15.15},
                    "efficient": {"2009": 34.452, "2010": 34.56}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 856.2139, "2010": 832.0021},
                    "efficient": {"2009": 1958.494, "2010": 1941.174}},
                "competed": {
                    "baseline": {"2009": 856.2139, "2010": 832.0021},
                    "efficient": {"2009": 1958.494, "2010": 1941.174}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 270, "2010": 270},
                        "efficient": {"2009": 375, "2010": 375}},
                    "competed": {
                        "baseline": {"2009": 270, "2010": 270},
                        "efficient": {"2009": 375, "2010": 375}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 170.892, "2010": 163.317},
                        "efficient": {"2009": 349.3433, "2010": 334.1952}},
                    "competed": {
                        "baseline": {"2009": 170.892, "2010": 163.317},
                        "efficient": {"2009": 349.3433, "2010": 334.1952}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 28255.06, "2010": 27456.07},
                        "efficient": {"2009": 64630.29, "2010": 64058.75}},
                    "competed": {
                        "baseline": {"2009": 28255.06, "2010": 27456.07},
                        "efficient": {"2009": 64630.29, "2010": 64058.75}}}},
            "lifetime": {"baseline": {"2009": 180, "2010": 180},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}},
                "competed": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 11000000, "2010": 11000000}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 31.9, "2010": 32.0},
                    "efficient": {"2009": 17.86, "2010": 17.92}},
                "competed": {
                    "baseline": {"2009": 31.9, "2010": 32.0},
                    "efficient": {"2009": 17.86, "2010": 17.92}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 1813.42, "2010": 1797.38},
                    "efficient": {"2009": 1015.52, "2010": 1006.53}},
                "competed": {
                    "baseline": {"2009": 1813.42, "2010": 1797.38},
                    "efficient": {"2009": 1015.52, "2010": 1006.53}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 154000000, "2010": 154000000},
                        "efficient": {"2009": 275000000, "2010": 275000000}},
                    "competed": {
                        "baseline": {"2009": 154000000, "2010": 154000000},
                        "efficient": {"2009": 275000000, "2010": 275000000}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 289.65, "2010": 273.6},
                        "efficient": {"2009": 162.21, "2010": 153.22}},
                    "competed": {
                        "baseline": {"2009": 289.65, "2010": 273.6},
                        "efficient": {"2009": 162.21, "2010": 153.22}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 59842.87, "2010": 59313.65},
                        "efficient": {"2009": 33512, "2010": 33215.65}},
                    "competed": {
                        "baseline": {"2009": 59842.87, "2010": 59313.65},
                        "efficient": {"2009": 33512, "2010": 33215.65}}}},
            "lifetime": {"baseline": {"2009": 140, "2010": 140},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 7.125, "2010": 6.9375},
                    "measure": {"2009": 7.125, "2010": 6.9375}},
                "competed": {
                    "all": {"2009": 7.125, "2010": 6.9375},
                    "measure": {"2009": 7.125, "2010": 6.9375}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 7.1963, "2010": 7.0069},
                    "efficient": {"2009": 5.1813, "2010": 5.0449}},
                "competed": {
                    "baseline": {"2009": 7.1963, "2010": 7.0069},
                    "efficient": {"2009": 5.1813, "2010": 5.0449}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 406.7016, "2010": 384.801},
                    "efficient": {"2009": 292.8251, "2010": 277.0567}},
                "competed": {
                    "baseline": {"2009": 406.7016, "2010": 384.801},
                    "efficient": {"2009": 292.8251, "2010": 277.0567}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 128.25, "2010": 124.875},
                        "efficient": {"2009": 178.125, "2010": 173.4375}},
                    "competed": {
                        "baseline": {"2009": 128.25, "2010": 124.875},
                        "efficient": {"2009": 178.125, "2010": 173.4375}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 81.1737, "2010": 75.53411},
                        "efficient": {"2009": 58.44506, "2010": 54.38456}},
                    "competed": {
                        "baseline": {"2009": 81.1737, "2010": 75.53411},
                        "efficient": {"2009": 58.44506, "2010": 54.38456}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 13421.15, "2010": 12698.43},
                        "efficient": {"2009": 9663.23, "2010": 9142.871}},
                    "competed": {
                        "baseline": {"2009": 13421.15, "2010": 12698.43},
                        "efficient": {"2009": 9663.23, "2010": 9142.871}}}},
            "lifetime": {"baseline": {"2009": 180, "2010": 180},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 70.3, "2010": 68.45},
                    "measure": {"2009": 70.3, "2010": 68.45}},
                "competed": {
                    "all": {"2009": 70.3, "2010": 68.45},
                    "measure": {"2009": 70.3, "2010": 68.45}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 308.0233, "2010": 300.8239},
                    "efficient": {"2009": 261.2829, "2010": 255.1714}},
                "competed": {
                    "baseline": {"2009": 308.0233, "2010": 300.8239},
                    "efficient": {"2009": 261.2829, "2010": 255.1714}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 17506.55, "2010": 16883.31},
                    "efficient": {"2009": 14849.56, "2010": 14319.33}},
                "competed": {
                    "baseline": {"2009": 17506.55, "2010": 16883.31},
                    "efficient": {"2009": 14849.56, "2010": 14319.33}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 1411.7, "2010": 1374.55},
                        "efficient": {"2009": 1757.5, "2010": 1711.25}},
                    "competed": {
                        "baseline": {"2009": 1411.7, "2010": 1374.55},
                        "efficient": {"2009": 1757.5, "2010": 1711.25}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 3135.935, "2010": 2920.893},
                        "efficient": {"2009": 2661.769, "2010": 2479.226}},
                    "competed": {
                        "baseline": {"2009": 3135.935, "2010": 2920.893},
                        "efficient": {"2009": 2661.769, "2010": 2479.226}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 577716.18, "2010": 557149.19},
                        "efficient": {"2009": 490035.57, "2010": 472537.73}},
                    "competed": {
                        "baseline": {"2009": 577716.18, "2010": 557149.19},
                        "efficient": {"2009": 490035.57, "2010": 472537.73}}}},
            "lifetime": {"baseline": {"2009": 200, "2010": 200},
                         "measure": 1}}]
        cls.ok_mapmas_partchck_msegout = [{
            "stock": {
                "total": {
                    "all": {"2009": 11000000, "2010": 11000000},
                    "measure": {"2009": 298571.43, "2010": 887610.20}},
                "competed": {
                    "all": {"2009": 298571.43, "2010": 597142.86},
                    "measure": {"2009": 298571.43, "2010": 597142.86}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 31.90, "2010": 32.00},
                    "efficient": {"2009": 31.52, "2010": 30.87}},
                "competed": {
                    "baseline": {"2009": 0.87, "2010": 1.74},
                    "efficient": {"2009": 0.48, "2010": 0.97}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 1813.42, "2010": 1797.38},
                    "efficient": {"2009": 1791.76, "2010": 1734.15}},
                "competed": {
                    "baseline": {"2009": 49.22, "2010": 97.57},
                    "efficient": {"2009": 27.56, "2010": 54.64}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 154000000, "2010": 154000000},
                        "efficient": {
                            "2009": 157284285.71, "2010": 163763712.24}},
                    "competed": {
                        "baseline": {"2009": 4180000, "2010": 8360000},
                        "efficient": {
                            "2009": 7464285.71, "2010": 14928571.43}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 289.65, "2010": 273.60},
                        "efficient": {"2009": 286.19, "2010": 263.97}},
                    "competed": {
                        "baseline": {"2009": 7.86, "2010": 14.85},
                        "efficient": {"2009": 4.40, "2010": 8.32}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 59842.87, "2010": 59313.65},
                        "efficient": {"2009": 59128.17, "2010": 57226.98}},
                    "competed": {
                        "baseline": {"2009": 1624.31, "2010": 3219.88},
                        "efficient": {"2009": 909.61, "2010": 1803.14}}}},
            "lifetime": {"baseline": {"2009": 140, "2010": 140},
                         "measure": 1}}]
        cls.ok_distmeas_out = [
            [121.74, 50, 1844.58, 50, 1, 1],
            [11.61, 50, 379.91, 50, 1.03, 50],
            [57.20, 50, 6017912381.8599997, 50, 1, 1]]
        cls.ok_partialmeas_out = [{
            "stock": {
                "total": {
                    "all": {"2009": 18, "2010": 18},
                    "measure": {"2009": 18, "2010": 18}},
                "competed": {
                    "all": {"2009": 18, "2010": 18},
                    "measure": {"2009": 18, "2010": 18}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 57.42, "2010": 57.6},
                    "efficient": {"2009": 27.5616, "2010": 27.648}},
                "competed": {
                    "baseline": {"2009": 57.42, "2010": 57.6},
                    "efficient": {"2009": 27.5616, "2010": 27.648}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 3264.156, "2010": 3235.29},
                    "efficient": {"2009": 1566.795, "2010": 1552.939}},
                "competed": {
                    "baseline": {"2009": 3264.156, "2010": 3235.29},
                    "efficient": {"2009": 1566.795, "2010": 1552.939}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 216, "2010": 216},
                        "efficient": {"2009": 450, "2010": 450}},
                    "competed": {
                        "baseline": {"2009": 216, "2010": 216},
                        "efficient": {"2009": 450, "2010": 450}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 582.2388, "2010": 556.992},
                        "efficient": {"2009": 279.4746, "2010": 267.3562}},
                    "competed": {
                        "baseline": {"2009": 582.2388, "2010": 556.992},
                        "efficient": {"2009": 279.4746, "2010": 267.3562}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 107717.16, "2010": 106764.58},
                        "efficient": {"2009": 51704.24, "2010": 51247}},
                    "competed": {
                        "baseline": {"2009": 107717.16, "2010": 106764.58},
                        "efficient": {"2009": 51704.24, "2010": 51247}}}},
            "lifetime": {"baseline": {"2009": 120, "2010": 120},
                         "measure": 1}},
            {
            "stock": {
                "total": {
                    "all": {"2009": 52, "2010": 52},
                    "measure": {"2009": 52, "2010": 52}},
                "competed": {
                    "all": {"2009": 52, "2010": 52},
                    "measure": {"2009": 52, "2010": 52}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 165.88, "2010": 166.4},
                    "efficient": {"2009": 67.1176, "2010": 67.328}},
                "competed": {
                    "baseline": {"2009": 165.88, "2010": 166.4},
                    "efficient": {"2009": 67.1176, "2010": 67.328}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 9429.785, "2010": 9346.394},
                    "efficient": {"2009": 3815.436, "2010": 3781.695}},
                "competed": {
                    "baseline": {"2009": 9429.785, "2010": 9346.394},
                    "efficient": {"2009": 3815.436, "2010": 3781.695}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 526, "2010": 526},
                        "efficient": {"2009": 1300, "2010": 1300}},
                    "competed": {
                        "baseline": {"2009": 526, "2010": 526},
                        "efficient": {"2009": 1300, "2010": 1300}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 1682.023, "2010": 1609.088},
                        "efficient": {"2009": 680.5725, "2010": 651.0618}},
                    "competed": {
                        "baseline": {"2009": 1682.023, "2010": 1609.088},
                        "efficient": {"2009": 680.5725, "2010": 651.0618}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 311182.9, "2010": 308431},
                        "efficient": {"2009": 125909.39, "2010": 124795.93}},
                    "competed": {
                        "baseline": {"2009": 311182.9, "2010": 308431},
                        "efficient": {"2009": 125909.39, "2010": 124795.93}}}},
            "lifetime": {"baseline": {"2009": 80, "2010": 80},
                         "measure": 1}}]
        cls.ok_warnmeas_out = [
            [("WARNING: 'warn measure 1' has invalid "
              "sub-market scaling fraction source title, author, "
              "organization, and/or year information"),
             ("WARNING: 'warn measure 1' has invalid "
              "sub-market scaling fraction source URL information"),
             ("WARNING: 'warn measure 1' has invalid "
              "sub-market scaling fraction derivation information"),
             ("WARNING (CRITICAL): 'warn measure 1' has "
              "insufficient sub-market source information and "
              "will be removed from analysis")],
            [("WARNING: 'warn measure 2' has invalid "
              "sub-market scaling fraction source URL information"),
             ("WARNING: 'warn measure 2' has invalid "
              "sub-market scaling fraction derivation information"),
             ("WARNING (CRITICAL): 'warn measure 2' has "
              "insufficient sub-market source information and "
              "will be removed from analysis")],
            [("WARNING: 'warn measure 3' has invalid "
              "sub-market scaling fraction source title, author, "
              "organization, and/or year information")]]

    def test_mseg_ok_full_tp(self):
        """Test 'fill_mkts' function given valid inputs.

        Notes:
            Checks the all branches of measure 'markets' attribute
            under a Technical potential scenario.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        # Run function on all measure objects and check output
        for idx, measure in enumerate(self.ok_tpmeas_fullchk_in):
            measure.fill_mkts(self.sample_mseg_in, self.sample_cpl_in,
                              convert_data={})
            self.dict_check(
                measure.markets['Technical potential']['master_mseg'],
                self.ok_tpmeas_fullchk_msegout[idx])
            self.dict_check(
                measure.markets['Technical potential']['mseg_adjust'][
                    'competed choice parameters'],
                self.ok_tpmeas_fullchk_competechoiceout[idx])
            self.dict_check(
                measure.markets['Technical potential']['mseg_adjust'][
                    'secondary mseg adjustments'],
                self.ok_tpmeas_fullchk_msegadjout[idx])
            self.dict_check(
                measure.markets['Technical potential']['mseg_adjust'][
                    'supply-demand adjustment'],
                self.ok_tpmeas_fullchk_supplydemandout[idx])
            self.dict_check(
                measure.markets['Technical potential']['mseg_out_break'],
                self.ok_tpmeas_fullchk_break_out[idx])

    def test_mseg_ok_part_tp(self):
        """Test 'fill_mkts' function given valid inputs.

        Notes:
            Checks the 'master_mseg' branch of measure 'markets' attribute
            under a Technical potential scenario.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        # Run function on all measure objects and check output
        for idx, measure in enumerate(self.ok_tpmeas_partchk_in):
            measure.fill_mkts(self.sample_mseg_in, self.sample_cpl_in,
                              convert_data={})
            self.dict_check(
                measure.markets['Technical potential']['master_mseg'],
                self.ok_tpmeas_partchk_msegout[idx])

    def test_mseg_ok_part_map(self):
        """Test 'fill_mkts' function given valid inputs.

        Notes:
            Checks the 'master_mseg' branch of measure 'markets' attribute
            under a Max adoption potential scenario.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        # Run function on all measure objects and check for correct
        # output
        for idx, measure in enumerate(self.ok_mapmeas_partchk_in):
            measure.fill_mkts(self.sample_mseg_in, self.sample_cpl_in,
                              convert_data={})
            self.dict_check(
                measure.markets['Max adoption potential']['master_mseg'],
                self.ok_mapmas_partchck_msegout[idx])

    def test_mseg_ok_distrib(self):
        """Test 'fill_mkts' function given valid inputs.

        Notes:
            Valid input measures are assigned distributions on
            their cost, performance, and/or lifetime attributes.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        # Seed random number generator to yield repeatable results
        numpy.random.seed(1234)
        for idx, measure in enumerate(self.ok_distmeas_in):
            # Generate lists of energy and cost output values
            measure.fill_mkts(
                self.sample_mseg_in, self.sample_cpl_in,
                convert_data={})
            test_outputs = measure.markets[
                'Technical potential']['master_mseg']
            test_e = test_outputs["energy"]["total"]["efficient"]["2009"]
            test_c = test_outputs[
                "cost"]["stock"]["total"]["efficient"]["2009"]
            test_l = test_outputs["lifetime"]["measure"]
            if type(test_l) == float:
                test_l = [test_l]
            # Calculate mean values from output lists for testing
            param_e = round(sum(test_e) / len(test_e), 2)
            param_c = round(sum(test_c) / len(test_c), 2)
            param_l = round(sum(test_l) / len(test_l), 2)
            # Check mean values and length of output lists to ensure
            # correct
            self.assertEqual([
                param_e, len(test_e), param_c, len(test_c),
                param_l, len(test_l)], self.ok_distmeas_out[idx])

    def test_mseg_partial(self):
        """Test 'fill_mkts' function given partially valid inputs.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        # Run function on all measure objects and check output
        for idx, measure in enumerate(self.ok_partialmeas_in):
            measure.fill_mkts(self.sample_mseg_in, self.sample_cpl_in,
                              convert_data={})
            self.dict_check(
                measure.markets['Technical potential']['master_mseg'],
                self.ok_partialmeas_out[idx])

    def test_mseg_fail(self):
        """Test 'fill_mkts' function given invalid inputs.

        Raises:
            AssertionError: If KeyError is not raised.
        """
        # Run function on all measure objects and check output
        for idx, measure in enumerate(self.failmeas_in):
            with self.assertRaises(KeyError):
                measure.fill_mkts(self.sample_mseg_in, self.sample_cpl_in,
                                  convert_data={})

    def test_mseg_warn(self):
        """Test 'fill_mkts' function given incomplete inputs.

        Raises:
            AssertionError: If function yields unexpected results or
            UserWarning is not raised.
        """
        # Run function on all measure objects and check output
        for idx, mw in enumerate(self.warnmeas_in):
            # Assert that inputs generate correct warnings and that measure
            # is marked inactive where necessary
            with warnings.catch_warnings(record=True) as w:
                mw.fill_mkts(self.sample_mseg_in, self.sample_cpl_in,
                             convert_data={})
                # Check correct number of warnings is yielded
                self.assertEqual(len(w), len(self.ok_warnmeas_out[idx]))
                # Check correct type of warnings is yielded
                self.assertTrue(all([
                    issubclass(wn.category, UserWarning) for wn in w]))
                # Check correct warning messages are yielded
                [self.assertTrue(wm in str([wmt.message for wmt in w])) for
                    wm in self.ok_warnmeas_out[idx]]
                # Check that measure is marked inactive when a critical
                # warning message is yielded
                if any(['CRITICAL' in x for x in self.ok_warnmeas_out[
                        idx]]):
                    self.assertEqual(mw.active, 0)
                else:
                    self.assertEqual(mw.active, 1)


class PartitionMicrosegmentTest(unittest.TestCase, CommonMethods):
    """Test the operation of the 'partition_microsegment' function.

    Ensure that the function properly partitions an input microsegment
    to yield the required total, competed, and efficient stock, energy,
    carbon and cost information.

    Attributes:
        time_horizons (list): A series of modeling time horizons to use
            in the various test functions of the class.
        handyvars (object): Global variables to use for the test measure.
        handyvars.ccosts (numpy.ndarray): Sample carbon costs.
        sample_measure_in (dict): Sample measure attributes.
        ok_diffuse_params_in (NoneType): Placeholder for eventual technology
            diffusion parameters to be used in 'adjusted adoption' scenario.
        ok_mskeys_in (list): Sample key chains associated with the market
            microsegment being partitioned by the function.
        ok_mkt_scale_frac_in (float): Sample market microsegment scaling
            factor.
        ok_newbldg_frac_in (list): Sample fraction of the total stock that
            is new construction, by year.
        ok_stock_in (list): Sample baseline microsegment stock data, by year.
        ok_energy_in (list): Sample baseline microsegment energy data, by year.
        ok_carb_in (list): Sample baseline microsegment carbon data, by year.
        ok_base_cost_in (list): Sample baseline technology unit costs, by year.
        ok_cost_meas_in (list): Sample measure unit costs.
        ok_cost_energy_base_in (numpy.ndarray): Sample baseline fuel costs.
        ok_cost_energy_meas_in (numpy.ndarray): Sample measure fuel costs.
        ok_relperf_in (list): Sample measure relative performance values.
        ok_life_base_in (dict): Sample baseline technology lifetimes, by year.
        ok_life_meas_in (int): Sample measure lifetime.
        ok_ssconv_base_in (numpy.ndarray): Sample baseline fuel site-source
            conversions, by year.
        ok_ssconv_meas_in (numpy.ndarray): Sample measure fuel site-source
            conversions, by year.
        ok_carbint_base_in (numpy.ndarray): Sample baseline fuel carbon
            intensities, by year.
        ok_carbint_meas_in (numpy.ndarray): Sample measure fuel carbon
            intensities, by year.
        ok_out (list): Outputs that should be yielded by the function given
            valid inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        cls.time_horizons = [
            ["2009", "2010", "2011"], ["2025", "2026", "2027"],
            ["2020", "2021", "2022"]]
        cls.handyvars = measures_prep.UsefulVars()
        cls.handyvars.ccosts = numpy.array(
            (b'Test', 1, 4, 1, 1, 1, 1, 1, 1, 3), dtype=[
                ('Category', 'S11'), ('2009', '<f8'),
                ('2010', '<f8'), ('2011', '<f8'),
                ('2020', '<f8'), ('2021', '<f8'),
                ('2022', '<f8'), ('2025', '<f8'),
                ('2026', '<f8'), ('2027', '<f8')])
        sample_measure_in = {
            "name": "sample measure 1",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "supply", "secondary": None},
            "technology": {
                "primary": [
                    "boiler (electric)", "ASHP", "GSHP",
                    "room AC"],
                "secondary": None}}
        cls.measure_instance = measures_prep.Measure(
            cls.handyvars, **sample_measure_in)
        cls.ok_diffuse_params_in = None
        cls.ok_mskeys_in = [
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply', 'boiler (electric)',
             'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply', 'boiler (electric)',
             'existing')]
        cls.ok_mkt_scale_frac_in = 1
        cls.ok_new_bldg_frac_in = [{
            "added": {"2009": 0.1, "2010": 0.05, "2011": 0.1},
            "total": {"2009": 0.1, "2010": 0.15, "2011": 0.25}},
            {"added": {"2025": 0.1, "2026": 0.05, "2027": 0.1},
             "total": {"2025": 0.1, "2026": 0.15, "2027": 0.25}},
            {"added": {"2020": 0.1, "2021": 0.95, "2022": 0.1},
             "total": {"2020": 0.1, "2021": 1, "2022": 1}}]
        cls.ok_stock_in = [
            {"2009": 100, "2010": 200, "2011": 300},
            {"2025": 400, "2026": 500, "2027": 600},
            {"2020": 700, "2021": 800, "2022": 900}]
        cls.ok_energy_in = [
            {"2009": 10, "2010": 20, "2011": 30},
            {"2025": 40, "2026": 50, "2027": 60},
            {"2020": 70, "2021": 80, "2022": 90}]
        cls.ok_carb_in = [
            {"2009": 30, "2010": 60, "2011": 90},
            {"2025": 120, "2026": 150, "2027": 180},
            {"2020": 210, "2021": 240, "2022": 270}]
        cls.ok_base_cost_in = [
            {"2009": 10, "2010": 10, "2011": 10},
            {"2025": 20, "2026": 20, "2027": 20},
            {"2020": 30, "2021": 30, "2022": 30}]
        cls.ok_cost_meas_in = [20, 30, 40]
        cls.ok_cost_energy_base_in, cls.ok_cost_energy_meas_in = \
            (numpy.array((b'Test', 1, 2, 2, 2, 2, 2, 2, 2, 2),
                         dtype=[('Category', 'S11'), ('2009', '<f8'),
                                ('2010', '<f8'), ('2011', '<f8'),
                                ('2020', '<f8'), ('2021', '<f8'),
                                ('2022', '<f8'), ('2025', '<f8'),
                                ('2026', '<f8'), ('2027', '<f8')])
             for n in range(2))
        cls.ok_relperf_in = [
            {"2009": 0.30, "2010": 0.30, "2011": 0.30},
            {"2025": 0.15, "2026": 0.15, "2027": 0.15},
            {"2020": 0.75, "2021": 0.75, "2022": 0.75}]
        cls.ok_life_base_in = {
            "2009": 10, "2010": 10, "2011": 10,
            "2020": 10, "2021": 10, "2022": 10,
            "2025": 10, "2026": 10, "2027": 10}
        cls.ok_life_meas_in = 10
        cls.ok_ssconv_base_in, cls.ok_ssconv_meas_in = \
            (numpy.array((b'Test', 1, 1, 1, 1, 1, 1, 1, 1, 1),
                         dtype=[('Category', 'S11'), ('2009', '<f8'),
                                ('2010', '<f8'), ('2011', '<f8'),
                                ('2020', '<f8'), ('2021', '<f8'),
                                ('2022', '<f8'), ('2025', '<f8'),
                                ('2026', '<f8'), ('2027', '<f8')])
             for n in range(2))
        cls.ok_carbint_base_in, cls.ok_carbint_meas_in = \
            (numpy.array((b'Test', 1, 1, 1, 1, 1, 1, 1, 1, 1),
                         dtype=[('Category', 'S11'), ('2009', '<f8'),
                                ('2010', '<f8'), ('2011', '<f8'),
                                ('2020', '<f8'), ('2021', '<f8'),
                                ('2022', '<f8'), ('2025', '<f8'),
                                ('2026', '<f8'), ('2027', '<f8')])
             for n in range(2))
        cls.ok_out = [
            [[[
                {"2009": 100, "2010": 200, "2011": 300},
                {"2009": 10, "2010": 20, "2011": 30},
                {"2009": 30, "2010": 60, "2011": 90},
                {"2009": 100, "2010": 200, "2011": 300},
                {"2009": 3, "2010": 6, "2011": 9},
                {"2009": 9, "2010": 18, "2011": 27},
                {"2009": 100, "2010": 66.67, "2011": 120},
                {"2009": 10, "2010": 6.67, "2011": 12},
                {"2009": 30, "2010": 20, "2011": 36},
                {"2009": 100, "2010": 66.67, "2011": 120},
                {"2009": 3, "2010": 2, "2011": 3.6},
                {"2009": 9, "2010": 6, "2011": 10.8},
                {"2009": 1000, "2010": 2000, "2011": 3000},
                {"2009": 10, "2010": 40, "2011": 60},
                {"2009": 30, "2010": 240, "2011": 90},
                {"2009": 2000, "2010": 4000, "2011": 6000},
                {"2009": 3, "2010": 12, "2011": 18},
                {"2009": 9, "2010": 72, "2011": 27},
                {"2009": 1000, "2010": 666.67, "2011": 1200},
                {"2009": 10, "2010": 13.33, "2011": 24},
                {"2009": 30, "2010": 80, "2011": 36},
                {"2009": 2000, "2010": 1333.33, "2011": 2400},
                {"2009": 3, "2010": 4, "2011": 7.2},
                {"2009": 9, "2010": 24, "2011": 10.8}],
                [
                {"2009": 100, "2010": 200, "2011": 300},
                {"2009": 10, "2010": 20, "2011": 30},
                {"2009": 30, "2010": 60, "2011": 90},
                {"2009": 100, "2010": 200, "2011": 300},
                {"2009": 3, "2010": 6, "2011": 9},
                {"2009": 9, "2010": 18, "2011": 27},
                {"2009": 100, "2010": 4, "2011": 6},
                {"2009": 10, "2010": 0.4, "2011": 0.6},
                {"2009": 30, "2010": 1.2, "2011": 1.8},
                {"2009": 100, "2010": 4, "2011": 6},
                {"2009": 3, "2010": 0.12, "2011": 0.18},
                {"2009": 9, "2010": 0.36, "2011": 0.54},
                {"2009": 1000, "2010": 2000, "2011": 3000},
                {"2009": 10, "2010": 40, "2011": 60},
                {"2009": 30, "2010": 240, "2011": 90},
                {"2009": 2000, "2010": 4000, "2011": 6000},
                {"2009": 3, "2010": 12, "2011": 18},
                {"2009": 9, "2010": 72, "2011": 27},
                {"2009": 1000, "2010": 40, "2011": 60},
                {"2009": 10, "2010": 0.8, "2011": 1.2},
                {"2009": 30, "2010": 4.8, "2011": 1.8},
                {"2009": 2000, "2010": 80, "2011": 120},
                {"2009": 3, "2010": 0.24, "2011": 0.36},
                {"2009": 9, "2010": 1.44, "2011": 0.54}]],
             [[
                 {"2009": 100, "2010": 200, "2011": 300},
                 {"2009": 10, "2010": 20, "2011": 30},
                 {"2009": 30, "2010": 60, "2011": 90},
                 {"2009": 100, "2010": 166.67, "2011": 286.67},
                 {"2009": 3, "2010": 6, "2011": 9},
                 {"2009": 9, "2010": 18, "2011": 27},
                 {"2009": 100, "2010": 66.67, "2011": 120},
                 {"2009": 10, "2010": 6.67, "2011": 12},
                 {"2009": 30, "2010": 20, "2011": 36},
                 {"2009": 100, "2010": 66.67, "2011": 120},
                 {"2009": 3, "2010": 2, "2011": 3.6},
                 {"2009": 9, "2010": 6, "2011": 10.8},
                 {"2009": 1000, "2010": 2000, "2011": 3000},
                 {"2009": 10, "2010": 40, "2011": 60},
                 {"2009": 30, "2010": 240, "2011": 90},
                 {"2009": 2000, "2010": 3666.67, "2011": 5866.67},
                 {"2009": 3, "2010": 12, "2011": 18},
                 {"2009": 9, "2010": 72, "2011": 27},
                 {"2009": 1000, "2010": 666.67, "2011": 1200},
                 {"2009": 10, "2010": 13.33, "2011": 24},
                 {"2009": 30, "2010": 80, "2011": 36},
                 {"2009": 2000, "2010": 1333.33, "2011": 2400},
                 {"2009": 3, "2010": 4, "2011": 7.2},
                 {"2009": 9, "2010": 24, "2011": 10.8}],
                 [
                 {"2009": 100, "2010": 200, "2011": 300},
                 {"2009": 10, "2010": 20, "2011": 30},
                 {"2009": 30, "2010": 60, "2011": 90},
                 {"2009": 12, "2010": 36, "2011": 72},
                 {"2009": 9.16, "2010": 16.84, "2011": 24.15},
                 {"2009": 27.48, "2010": 50.52, "2011": 72.46},
                 {"2009": 12, "2010": 24, "2011": 36},
                 {"2009": 1.2, "2010": 2.4, "2011": 3.6},
                 {"2009": 3.6, "2010": 7.2, "2011": 10.8},
                 {"2009": 12, "2010": 24, "2011": 36},
                 {"2009": 0.36, "2010": 0.72, "2011": 1.08},
                 {"2009": 1.08, "2010": 2.16, "2011": 3.24},
                 {"2009": 1000, "2010": 2000, "2011": 3000},
                 {"2009": 10, "2010": 40, "2011": 60},
                 {"2009": 30, "2010": 240, "2011": 90},
                 {"2009": 1120, "2010": 2360, "2011": 3720},
                 {"2009": 9.16, "2010": 33.68, "2011": 48.31},
                 {"2009": 27.48, "2010": 202.10, "2011": 72.46},
                 {"2009": 120, "2010": 240, "2011": 360},
                 {"2009": 1.2, "2010": 4.8, "2011": 7.2},
                 {"2009": 3.6, "2010": 28.8, "2011": 10.8},
                 {"2009": 240, "2010": 480, "2011": 720},
                 {"2009": 0.36, "2010": 1.44, "2011": 2.16},
                 {"2009": 1.08, "2010": 8.64, "2011": 3.24}]]],
            [[[
                {"2025": 400, "2026": 500, "2027": 600},
                {"2025": 40, "2026": 50, "2027": 60},
                {"2025": 120, "2026": 150, "2027": 180},
                {"2025": 400, "2026": 500, "2027": 600},
                {"2025": 6, "2026": 7.5, "2027": 9},
                {"2025": 18, "2026": 22.5, "2027": 27},
                {"2025": 400, "2026": 166.67, "2027": 240},
                {"2025": 40, "2026": 16.67, "2027": 24},
                {"2025": 120, "2026": 50, "2027": 72},
                {"2025": 400, "2026": 166.67, "2027": 240},
                {"2025": 6, "2026": 2.5, "2027": 3.6},
                {"2025": 18, "2026": 7.5, "2027": 10.8},
                {"2025": 8000, "2026": 10000, "2027": 12000},
                {"2025": 80, "2026": 100, "2027": 120},
                {"2025": 120, "2026": 150, "2027": 540},
                {"2025": 12000, "2026": 15000, "2027": 18000},
                {"2025": 12, "2026": 15, "2027": 18},
                {"2025": 18, "2026": 22.5, "2027": 81},
                {"2025": 8000, "2026": 3333.33, "2027": 4800},
                {"2025": 80, "2026": 33.33, "2027": 48},
                {"2025": 120, "2026": 50, "2027": 216},
                {"2025": 12000, "2026": 5000, "2027": 7200},
                {"2025": 12, "2026": 5, "2027": 7.2},
                {"2025": 18, "2026": 7.5, "2027": 32.4}],
                [
                {"2025": 400, "2026": 500, "2027": 600},
                {"2025": 40, "2026": 50, "2027": 60},
                {"2025": 120, "2026": 150, "2027": 180},
                {"2025": 400, "2026": 500, "2027": 600},
                {"2025": 6, "2026": 7.5, "2027": 9},
                {"2025": 18, "2026": 22.5, "2027": 27},
                {"2025": 400, "2026": 10, "2027": 12},
                {"2025": 40, "2026": 1.0, "2027": 1.2},
                {"2025": 120, "2026": 3.0, "2027": 3.6},
                {"2025": 400, "2026": 10, "2027": 12},
                {"2025": 6, "2026": 0.15, "2027": 0.18},
                {"2025": 18, "2026": 0.45, "2027": 0.54},
                {"2025": 8000, "2026": 10000, "2027": 12000},
                {"2025": 80, "2026": 100, "2027": 120},
                {"2025": 120, "2026": 150, "2027": 540},
                {"2025": 12000, "2026": 15000, "2027": 18000},
                {"2025": 12, "2026": 15, "2027": 18},
                {"2025": 18, "2026": 22.5, "2027": 81},
                {"2025": 8000, "2026": 200, "2027": 240},
                {"2025": 80, "2026": 2.0, "2027": 2.4},
                {"2025": 120, "2026": 3.0, "2027": 10.8},
                {"2025": 12000, "2026": 300, "2027": 360},
                {"2025": 12, "2026": 0.30, "2027": 0.36},
                {"2025": 18, "2026": 0.45, "2027": 1.62}]],
             [[
                 {"2025": 400, "2026": 500, "2027": 600},
                 {"2025": 40, "2026": 50, "2027": 60},
                 {"2025": 120, "2026": 150, "2027": 180},
                 {"2025": 400, "2026": 500, "2027": 600},
                 {"2025": 6, "2026": 7.5, "2027": 9},
                 {"2025": 18, "2026": 22.5, "2027": 27},
                 {"2025": 400, "2026": 166.67, "2027": 240},
                 {"2025": 40, "2026": 16.67, "2027": 24},
                 {"2025": 120, "2026": 50, "2027": 72},
                 {"2025": 400, "2026": 166.67, "2027": 240},
                 {"2025": 6, "2026": 2.5, "2027": 3.6},
                 {"2025": 18, "2026": 7.5, "2027": 10.8},
                 {"2025": 8000, "2026": 10000, "2027": 12000},
                 {"2025": 80, "2026": 100, "2027": 120},
                 {"2025": 120, "2026": 150, "2027": 540},
                 {"2025": 12000, "2026": 15000, "2027": 18000},
                 {"2025": 12, "2026": 15, "2027": 18},
                 {"2025": 18, "2026": 22.5, "2027": 81},
                 {"2025": 8000, "2026": 3333.33, "2027": 4800},
                 {"2025": 80, "2026": 33.33, "2027": 48},
                 {"2025": 120, "2026": 50, "2027": 216},
                 {"2025": 12000, "2026": 5000, "2027": 7200},
                 {"2025": 12, "2026": 5, "2027": 7.2},
                 {"2025": 18, "2026": 7.5, "2027": 32.4}],
                 [
                 {"2025": 400, "2026": 500, "2027": 600},
                 {"2025": 40, "2026": 50, "2027": 60},
                 {"2025": 120, "2026": 150, "2027": 180},
                 {"2025": 48, "2026": 108, "2027": 180},
                 {"2025": 35.92, "2026": 40.41, "2027": 44.19},
                 {"2025": 107.76, "2026": 121.24, "2027": 132.56},
                 {"2025": 48, "2026": 60, "2027": 72},
                 {"2025": 4.8, "2026": 6, "2027": 7.2},
                 {"2025": 14.4, "2026": 18.0, "2027": 21.6},
                 {"2025": 48, "2026": 60, "2027": 72},
                 {"2025": 0.72, "2026": 0.90, "2027": 1.08},
                 {"2025": 2.16, "2026": 2.70, "2027": 3.24},
                 {"2025": 8000, "2026": 10000, "2027": 12000},
                 {"2025": 80, "2026": 100, "2027": 120},
                 {"2025": 120, "2026": 150, "2027": 540},
                 {"2025": 8480, "2026": 11080, "2027": 13800},
                 {"2025": 71.84, "2026": 80.82, "2027": 88.37},
                 {"2025": 107.76, "2026": 121.24, "2027": 397.67},
                 {"2025": 960, "2026": 1200, "2027": 1440},
                 {"2025": 9.6, "2026": 12.0, "2027": 14.4},
                 {"2025": 14.4, "2026": 18.0, "2027": 64.8},
                 {"2025": 1440, "2026": 1800, "2027": 2160},
                 {"2025": 1.44, "2026": 1.80, "2027": 2.16},
                 {"2025": 2.16, "2026": 2.70, "2027": 9.72}]]],
            [[[
                {"2020": 700, "2021": 800, "2022": 900},
                {"2020": 70, "2021": 80, "2022": 90},
                {"2020": 210, "2021": 240, "2022": 270},
                {"2020": 700, "2021": 800, "2022": 900},
                {"2020": 52.5, "2021": 60, "2022": 67.5},
                {"2020": 157.5, "2021": 180.0, "2022": 202.5},
                {"2020": 700, "2021": 760, "2022": 90},
                {"2020": 70, "2021": 76, "2022": 9},
                {"2020": 210, "2021": 228, "2022": 27},
                {"2020": 700, "2021": 760, "2022": 90},
                {"2020": 52.50, "2021": 57.00, "2022": 6.75},
                {"2020": 157.50, "2021": 171.0, "2022": 20.25},
                {"2020": 21000, "2021": 24000, "2022": 27000},
                {"2020": 140, "2021": 160, "2022": 180},
                {"2020": 210, "2021": 240, "2022": 270},
                {"2020": 28000, "2021": 32000, "2022": 36000},
                {"2020": 105, "2021": 120, "2022": 135},
                {"2020": 157.5, "2021": 180.0, "2022": 202.5},
                {"2020": 21000, "2021": 22800, "2022": 2700},
                {"2020": 140, "2021": 152, "2022": 18.0},
                {"2020": 210, "2021": 228, "2022": 27.0},
                {"2020": 28000, "2021": 30400, "2022": 3600},
                {"2020": 105.0, "2021": 114.0, "2022": 13.5},
                {"2020": 157.50, "2021": 171.00, "2022": 20.25}],
                [
                {"2020": 700, "2021": 800, "2022": 900},
                {"2020": 70, "2021": 80, "2022": 90},
                {"2020": 210, "2021": 240, "2022": 270},
                {"2020": 700, "2021": 800, "2022": 900},
                {"2020": 52.5, "2021": 60, "2022": 67.5},
                {"2020": 157.5, "2021": 180, "2022": 202.5},
                {"2020": 700, "2021": 16, "2022": 18},
                {"2020": 70, "2021": 1.6, "2022": 1.8},
                {"2020": 210, "2021": 4.8, "2022": 5.4},
                {"2020": 700, "2021": 16, "2022": 18},
                {"2020": 52.5, "2021": 1.20, "2022": 1.35},
                {"2020": 157.5, "2021": 3.60, "2022": 4.05},
                {"2020": 21000, "2021": 24000, "2022": 27000},
                {"2020": 140, "2021": 160, "2022": 180},
                {"2020": 210, "2021": 240, "2022": 270},
                {"2020": 28000, "2021": 32000, "2022": 36000},
                {"2020": 105, "2021": 120, "2022": 135},
                {"2020": 157.5, "2021": 180, "2022": 202.5},
                {"2020": 21000, "2021": 480, "2022": 540},
                {"2020": 140, "2021": 3.2, "2022": 3.6},
                {"2020": 210, "2021": 4.8, "2022": 5.4},
                {"2020": 28000, "2021": 640, "2022": 720},
                {"2020": 105, "2021": 2.4, "2022": 2.7},
                {"2020": 157.5, "2021": 3.60, "2022": 4.05}]],
             [[
                 {"2020": 700, "2021": 800, "2022": 900},
                 {"2020": 70, "2021": 80, "2022": 90},
                 {"2020": 210, "2021": 240, "2022": 270},
                 {"2020": 700, "2021": 800, "2022": 890},
                 {"2020": 52.5, "2021": 60, "2022": 67.5},
                 {"2020": 157.5, "2021": 180.0, "2022": 202.5},
                 {"2020": 700, "2021": 760, "2022": 90},
                 {"2020": 70, "2021": 76, "2022": 9},
                 {"2020": 210, "2021": 228, "2022": 27},
                 {"2020": 700, "2021": 760, "2022": 90},
                 {"2020": 52.50, "2021": 57.00, "2022": 6.75},
                 {"2020": 157.50, "2021": 171.0, "2022": 20.25},
                 {"2020": 21000, "2021": 24000, "2022": 27000},
                 {"2020": 140, "2021": 160, "2022": 180},
                 {"2020": 210, "2021": 240, "2022": 270},
                 {"2020": 28000, "2021": 32000, "2022": 35900},
                 {"2020": 105, "2021": 120, "2022": 135},
                 {"2020": 157.5, "2021": 180.0, "2022": 202.5},
                 {"2020": 21000, "2021": 22800, "2022": 2700},
                 {"2020": 140, "2021": 152, "2022": 18.0},
                 {"2020": 210, "2021": 228, "2022": 27.0},
                 {"2020": 28000, "2021": 30400, "2022": 3600},
                 {"2020": 105.0, "2021": 114.0, "2022": 13.5},
                 {"2020": 157.50, "2021": 171.00, "2022": 20.25}],
                 [
                 {"2020": 700, "2021": 800, "2022": 900},
                 {"2020": 70, "2021": 80, "2022": 90},
                 {"2020": 210, "2021": 240, "2022": 270},
                 {"2020": 84, "2021": 180, "2022": 288},
                 {"2020": 67.90, "2021": 75.49, "2022": 82.85},
                 {"2020": 203.70, "2021": 226.46, "2022": 248.54},
                 {"2020": 84, "2021": 96, "2022": 108},
                 {"2020": 8.4, "2021": 9.6, "2022": 10.8},
                 {"2020": 25.2, "2021": 28.8, "2022": 32.4},
                 {"2020": 84, "2021": 96, "2022": 108},
                 {"2020": 6.3, "2021": 7.2, "2022": 8.1},
                 {"2020": 18.9, "2021": 21.6, "2022": 24.3},
                 {"2020": 21000, "2021": 24000, "2022": 27000},
                 {"2020": 140, "2021": 160, "2022": 180},
                 {"2020": 210, "2021": 240, "2022": 270},
                 {"2020": 21840, "2021": 25800, "2022": 29880},
                 {"2020": 135.8, "2021": 150.98, "2022": 165.69},
                 {"2020": 203.70, "2021": 226.46, "2022": 248.54},
                 {"2020": 2520, "2021": 2880, "2022": 3240},
                 {"2020": 16.8, "2021": 19.2, "2022": 21.6},
                 {"2020": 25.2, "2021": 28.8, "2022": 32.4},
                 {"2020": 3360, "2021": 3840, "2022": 4320},
                 {"2020": 12.6, "2021": 14.4, "2022": 16.2},
                 {"2020": 18.9, "2021": 21.6, "2022": 24.3}]]]]

    def test_ok(self):
        """Test the 'partition_microsegment' function given valid inputs.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        # Loop through 'ok_out' elements
        for elem in range(0, len(self.ok_out)):
            # Reset AEO time horizon
            self.measure_instance.handyvars.aeo_years = \
                self.time_horizons[elem]
            # Loop through two test schemes (Technical potential and Max
            # adoption potential)
            for scn in range(0, len(self.handyvars.adopt_schemes)):
                # Loop through two microsegment key chains (one applying
                # to new structure type, another to existing structure type)
                for k in range(0, len(self.ok_mskeys_in)):
                    # List of output dicts generated by the function
                    lists1 = self.measure_instance.partition_microsegment(
                        self.handyvars.adopt_schemes[scn],
                        self.ok_diffuse_params_in,
                        self.ok_mskeys_in[k],
                        self.ok_mkt_scale_frac_in,
                        self.ok_new_bldg_frac_in[elem],
                        self.ok_stock_in[elem], self.ok_energy_in[elem],
                        self.ok_carb_in[elem],
                        self.ok_base_cost_in[elem], self.ok_cost_meas_in[elem],
                        self.ok_cost_energy_base_in,
                        self.ok_cost_energy_meas_in,
                        self.ok_relperf_in[elem],
                        self.ok_life_base_in,
                        self.ok_life_meas_in,
                        self.ok_ssconv_base_in, self.ok_ssconv_meas_in,
                        self.ok_carbint_base_in, self.ok_carbint_meas_in)
                    # Correct list of output dicts
                    lists2 = self.ok_out[elem][scn][k]
                    # Compare each element of the lists of output dicts
                    for elem2 in range(0, len(lists1)):
                        self.dict_check(lists1[elem2], lists2[elem2])


class CreateKeyChainTest(unittest.TestCase, CommonMethods):
    """Test 'create_keychain' function.

    Ensure that the function yields proper key chain output given
    input microsegment information.

    Attributes:
        sample_measure_in (dict): Sample measure attributes.
        ok_out_primary (list): Primary microsegment key chain that should
            be yielded by the function given valid inputs.
        ok_out_secondary (list): Secondary microsegment key chain that
            should be yielded by the function given valid inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        handyvars = measures_prep.UsefulVars()
        sample_measure = {
            "name": "sample measure 2",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": ["electricity"]},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": ["lighting"]},
            "technology_type": {
                "primary": "supply",
                "secondary": "supply"},
            "technology": {
                "primary": [
                    "boiler (electric)", "ASHP",
                    "GSHP", "room AC"],
                "secondary": ["general service (LED)"]},
            "mseg_adjust": {
                "contributing mseg keys and values": {},
                "competed choice parameters": {},
                "secondary mseg adjustments": {
                    "sub-market": {
                        "original stock (total)": {},
                        "adjusted stock (sub-market)": {}},
                    "stock-and-flow": {
                        "original stock (total)": {},
                        "adjusted stock (previously captured)": {},
                        "adjusted stock (competed)": {},
                        "adjusted stock (competed and captured)": {}},
                    "market share": {
                        "original stock (total captured)": {},
                        "original stock (competed and captured)": {},
                        "adjusted stock (total captured)": {},
                        "adjusted stock (competed and captured)": {}}},
                "supply-demand adjustment": {
                    "savings": {},
                    "total": {}}}}
        cls.sample_measure_in = measures_prep.Measure(
            handyvars, **sample_measure)
        cls.ok_out_primary = [
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply',
             'boiler (electric)', 'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply', 'ASHP',
             'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply', 'GSHP',
             'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply', 'room AC',
             'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'cooling', 'supply',
             'boiler (electric)', 'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'cooling', 'supply', 'ASHP',
             'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'cooling', 'supply', 'GSHP',
             'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'cooling', 'supply', 'room AC',
             'new'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'heating', 'supply',
             'boiler (electric)', 'new'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'heating', 'supply', 'ASHP',
             'new'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'heating', 'supply', 'GSHP',
             'new'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'heating', 'supply', 'room AC',
             'new'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'cooling', 'supply',
             'boiler (electric)', 'new'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'cooling', 'supply', 'ASHP',
             'new'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'cooling', 'supply', 'GSHP',
             'new'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'cooling', 'supply', 'room AC',
             'new'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply',
             'boiler (electric)', 'existing'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply', 'ASHP',
             'existing'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply', 'GSHP',
             'existing'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'heating', 'supply', 'room AC',
             'existing'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'cooling', 'supply',
             'boiler (electric)', 'existing'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'cooling', 'supply', 'ASHP',
             'existing'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'cooling', 'supply', 'GSHP',
             'existing'),
            ('primary', 'AIA_CZ1', 'single family home',
             'electricity', 'cooling', 'supply', 'room AC',
             'existing'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'heating', 'supply',
             'boiler (electric)', 'existing'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'heating', 'supply', 'ASHP',
             'existing'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'heating', 'supply', 'GSHP',
             'existing'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'heating', 'supply', 'room AC',
             'existing'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'cooling', 'supply',
             'boiler (electric)', 'existing'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'cooling', 'supply', 'ASHP',
             'existing'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'cooling', 'supply', 'GSHP',
             'existing'),
            ('primary', 'AIA_CZ2', 'single family home',
             'electricity', 'cooling', 'supply', 'room AC',
             'existing')]
        cls.ok_out_secondary = [
            ('secondary', 'AIA_CZ1', 'single family home',
             'electricity', 'lighting',
             'general service (LED)', 'new'),
            ('secondary', 'AIA_CZ2', 'single family home',
             'electricity', 'lighting',
             'general service (LED)', 'new'),
            ('secondary', 'AIA_CZ1', 'single family home',
             'electricity', 'lighting',
             'general service (LED)', 'existing'),
            ('secondary', 'AIA_CZ2', 'single family home',
             'electricity', 'lighting',
             'general service (LED)', 'existing')]

    def test_primary(self):
        """Test 'create_keychain' function given valid inputs.

        Note:
            Tests generation of primary microsegment key chains.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.assertEqual(
            self.sample_measure_in.create_keychain("primary")[0],
            self.ok_out_primary)

    # Test the generation of a list of secondary mseg key chains
    def test_secondary(self):
        """Test 'create_keychain' function given valid inputs.

        Note:
            Tests generation of secondary microsegment key chains.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.assertEqual(
            self.sample_measure_in.create_keychain("secondary")[0],
            self.ok_out_secondary)


class AddKeyValsTest(unittest.TestCase, CommonMethods):
    """Test 'add_keyvals' and 'add_keyvals_restrict' functions.

    Ensure that the functions properly add together input dictionaries.

    Attributes:
        sample_measure_in (dict): Sample measure attributes.
        ok_dict1_in (dict): Valid sample input dict for 'add_keyvals' function.
        ok_dict2_in (dict): Valid sample input dict for 'add_keyvals' function.
        ok_dict3_in (dict): Valid sample input dict for
            'add_keyvals_restrict' function.
        ok_dict4_in (dict): Valid sample input dict for
            'add_keyvals_restrict' function.
        fail_dict1_in (dict): One of two invalid sample input dicts for
            'add_keyvals' function (dict keys do not exactly match).
        fail_dict2_in (dict): Two of two invalid sample input dicts for
            'add_keyvals' function (dict keys do not exactly match).
        ok_out (dict): Dictionary that should be generated by 'add_keyvals'
            function given valid inputs.
        ok_out_restrict (dict): Dictionary that should be generated by
            'add_keyvals_restrict' function given valid inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        handyvars = measures_prep.UsefulVars()
        sample_measure_in = {
            "name": "sample measure 1",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "supply", "secondary": None},
            "technology": {
                "primary": [
                    "boiler (electric)", "ASHP", "GSHP",
                    "room AC"],
                "secondary": None}}
        cls.sample_measure_in = measures_prep.Measure(
            handyvars, **sample_measure_in)
        cls.ok_dict1_in, cls.ok_dict2_in = ({
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}},
            "level 1b": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}}} for n in range(2))
        cls.ok_dict3_in, cls.ok_dict4_in = ({
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}},
            "lifetime": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}}} for n in range(2))
        cls.fail_dict1_in = {
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}},
            "level 1b": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}}}
        cls.fail_dict2_in = {
            "level 1a": {
                "level 2aa": {"2009": 2, "2010": 3},
                "level 2ab": {"2009": 4, "2010": 5}},
            "level 1b": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2011": 9}}}
        cls.ok_out = {
            "level 1a": {
                "level 2aa": {"2009": 4, "2010": 6},
                "level 2ab": {"2009": 8, "2010": 10}},
            "level 1b": {
                "level 2ba": {"2009": 12, "2010": 14},
                "level 2bb": {"2009": 16, "2010": 18}}}
        cls.ok_out_restrict = {
            "level 1a": {
                "level 2aa": {"2009": 4, "2010": 6},
                "level 2ab": {"2009": 8, "2010": 10}},
            "lifetime": {
                "level 2ba": {"2009": 6, "2010": 7},
                "level 2bb": {"2009": 8, "2010": 9}}}

    def test_ok_add_keyvals(self):
        """Test 'add_keyvals' function given valid inputs.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.dict_check(
            self.sample_measure_in.add_keyvals(
                self.ok_dict1_in, self.ok_dict2_in), self.ok_out)

    def test_fail_add_keyvals(self):
        """Test 'add_keyvals' function given invalid inputs.

        Raises:
            AssertionError: If KeyError is not raised.
        """
        with self.assertRaises(KeyError):
            self.sample_measure_in.add_keyvals(
                self.fail_dict1_in, self.fail_dict2_in)

    def test_ok_add_keyvals_restrict(self):
        """Test 'add_keyvals_restrict' function given valid inputs."""
        self.dict_check(
            self.sample_measure_in.add_keyvals_restrict(
                self.ok_dict3_in, self.ok_dict4_in), self.ok_out_restrict)


class DivKeyValsTest(unittest.TestCase, CommonMethods):
    """Test 'div_keyvals' function.

    Ensure that the function properly divides the key values of one dict
    by those of another. Test inputs reflect the use of this function
    to generate output partitioning fractions (used to break out
    measure results by climate zone, building sector, end use).

    Attributes:
        sample_measure_in (dict): Sample measure attributes.
        ok_reduce_dict (dict): Values from second dict to normalize first
            dict values by.
        ok_dict_in (dict): Sample input dict with values to normalize.
        ok_out (dict): Output dictionary that should be yielded by the
            function given valid inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        handyvars = measures_prep.UsefulVars()
        sample_measure_in = {
            "name": "sample measure 1",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "supply", "secondary": None},
            "technology": {
                "primary": [
                    "boiler (electric)", "ASHP", "GSHP",
                    "room AC"],
                "secondary": None}}
        cls.sample_measure_in = measures_prep.Measure(
            handyvars, **sample_measure_in)
        cls.ok_reduce_dict = {"2009": 100, "2010": 100}
        cls.ok_dict_in = {
            "AIA CZ1": {
                "Residential": {
                    "Heating": {"2009": 10, "2010": 10},
                    "Cooling": {"2009": 15, "2010": 15}},
                "Commercial": {
                    "Heating": {"2009": 20, "2010": 20},
                    "Cooling": {"2009": 25, "2010": 25}}},
            "AIA CZ2": {
                "Residential": {
                    "Heating": {"2009": 30, "2010": 30},
                    "Cooling": {"2009": 35, "2010": 35}},
                "Commercial": {
                    "Heating": {"2009": 40, "2010": 40},
                    "Cooling": {"2009": 45, "2010": 45}}}}
        cls.ok_out = {
            "AIA CZ1": {
                "Residential": {
                    "Heating": {"2009": .10, "2010": .10},
                    "Cooling": {"2009": .15, "2010": .15}},
                "Commercial": {
                    "Heating": {"2009": .20, "2010": .20},
                    "Cooling": {"2009": .25, "2010": .25}}},
            "AIA CZ2": {
                "Residential": {
                    "Heating": {"2009": .30, "2010": .30},
                    "Cooling": {"2009": .35, "2010": .35}},
                "Commercial": {
                    "Heating": {"2009": .40, "2010": .40},
                    "Cooling": {"2009": .45, "2010": .45}}}}

    def test_ok(self):
        """Test 'div_keyvals' function given valid inputs.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.dict_check(
            self.sample_measure_in.div_keyvals(
                self.ok_dict_in, self.ok_reduce_dict), self.ok_out)


class DivKeyValsFloatTest(unittest.TestCase, CommonMethods):
    """Test 'div_keyvals_float' and div_keyvals_float_restrict' functions.

    Ensure that the functions properly divide dict key values by a given
    factor.

    Attributes:
        sample_measure_in (dict): Sample measure attributes.
        ok_reduce_num (float): Factor by which dict values should be divided.
        ok_dict_in (dict): Sample input dict with values to divide.
        ok_out (dict): Output dictionary that should be yielded by
            'div_keyvals_float' function given valid inputs.
        ok_out_restrict (dict): Output dictionary that should be yielded by
            'div_keyvals_float_restrict'function given valid inputs.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        handyvars = measures_prep.UsefulVars()
        sample_measure_in = {
            "name": "sample measure 1",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": None},
            "technology_type": {
                "primary": "supply", "secondary": None},
            "technology": {
                "primary": [
                    "boiler (electric)", "ASHP", "GSHP",
                    "room AC"],
                "secondary": None}}
        cls.sample_measure_in = measures_prep.Measure(
            handyvars, **sample_measure_in)
        cls.ok_reduce_num = 4
        cls.ok_dict_in = {
            "stock": {
                "total": {"2009": 100, "2010": 200},
                "competed": {"2009": 300, "2010": 400}},
            "energy": {
                "total": {"2009": 500, "2010": 600},
                "competed": {"2009": 700, "2010": 800},
                "efficient": {"2009": 700, "2010": 800}},
            "carbon": {
                "total": {"2009": 500, "2010": 600},
                "competed": {"2009": 700, "2010": 800},
                "efficient": {"2009": 700, "2010": 800}},
            "cost": {
                "baseline": {
                    "stock": {"2009": 900, "2010": 1000},
                    "energy": {"2009": 900, "2010": 1000},
                    "carbon": {"2009": 900, "2010": 1000}},
                "measure": {
                    "stock": {"2009": 1100, "2010": 1200},
                    "energy": {"2009": 1100, "2010": 1200},
                    "carbon": {"2009": 1100, "2010": 1200}}}}
        cls.ok_out = {
            "stock": {
                "total": {"2009": 25, "2010": 50},
                "competed": {"2009": 75, "2010": 100}},
            "energy": {
                "total": {"2009": 125, "2010": 150},
                "competed": {"2009": 175, "2010": 200},
                "efficient": {"2009": 175, "2010": 200}},
            "carbon": {
                "total": {"2009": 125, "2010": 150},
                "competed": {"2009": 175, "2010": 200},
                "efficient": {"2009": 175, "2010": 200}},
            "cost": {
                "baseline": {
                    "stock": {"2009": 225, "2010": 250},
                    "energy": {"2009": 225, "2010": 250},
                    "carbon": {"2009": 225, "2010": 250}},
                "measure": {
                    "stock": {"2009": 275, "2010": 300},
                    "energy": {"2009": 275, "2010": 300},
                    "carbon": {"2009": 275, "2010": 300}}}}
        cls.ok_out_restrict = {
            "stock": {
                "total": {"2009": 25, "2010": 50},
                "competed": {"2009": 75, "2010": 100}},
            "energy": {
                "total": {"2009": 500, "2010": 600},
                "competed": {"2009": 700, "2010": 800},
                "efficient": {"2009": 700, "2010": 800}},
            "carbon": {
                "total": {"2009": 500, "2010": 600},
                "competed": {"2009": 700, "2010": 800},
                "efficient": {"2009": 700, "2010": 800}},
            "cost": {
                "baseline": {
                    "stock": {"2009": 225, "2010": 250},
                    "energy": {"2009": 900, "2010": 1000},
                    "carbon": {"2009": 900, "2010": 1000}},
                "measure": {
                    "stock": {"2009": 275, "2010": 300},
                    "energy": {"2009": 1100, "2010": 1200},
                    "carbon": {"2009": 1100, "2010": 1200}}}}

    def test_ok_div(self):
        """Test 'div_keyvals_float' function given valid inputs.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.dict_check(
            self.sample_measure_in.div_keyvals_float(
                copy.deepcopy(self.ok_dict_in), self.ok_reduce_num),
            self.ok_out)

    def test_ok_div_restrict(self):
        """Test 'div_keyvals_float_restrict' function given valid inputs.

        Raises:
            AssertionError: If function yields unexpected results.
        """
        self.dict_check(
            self.sample_measure_in.div_keyvals_float_restrict(
                copy.deepcopy(self.ok_dict_in), self.ok_reduce_num),
            self.ok_out_restrict)


class CostConversionTest(unittest.TestCase, CommonMethods):
    """Test 'convert_costs' function.

    Ensure that function properly converts user-defined measure cost units
    to align with comparable baseline cost units.

    Attributes:
        sample_measure_in (dict): Sample measure attributes.
        sample_convertdata_ok_in (dict): Sample cost conversion input data.
        sample_bldgsect_ok_in (list): List of valid building sectors for
            sample measure cost.
        sample_mskeys_ok_in (list): List of valid full market microsegment
            information for sample measure cost (mseg type->czone->bldg->fuel->
            end use->technology type->structure type).
        sample_mskeys_fail_in (list): List of microsegment information for
            sample measure cost that should cause function to fail.
        cost_meas_ok_in (int): Sample measure cost.
        cost_meas_units_ok_in (list): List of valid sample measure cost units.
        cost_meas_units_fail_in (string): List of sample measure cost units
            that should cause the function to fail.
        cost_base_units_ok_in (string): List of valid baseline cost units.
        ok_out_costs (list): Converted measure costs that should be yielded
            given valid inputs to the function.
        ok_out_cost_units (string): Converted measure cost units that should
            be yielded given valid inputs to the function.

    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        handyvars = measures_prep.UsefulVars()
        sample_measure_in = {
            "name": "sample measure 2",
            "active": 1,
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": ["electricity"]},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["heating", "cooling"],
                "secondary": ["lighting"]},
            "technology_type": {
                "primary": "supply",
                "secondary": "supply"},
            "technology": {
                "primary": [
                    "boiler (electric)", "ASHP",
                    "GSHP", "room AC"],
                "secondary": ["general service (LED)"]},
            "mseg_adjust": {
                "contributing mseg keys and values": {},
                "competed choice parameters": {},
                "secondary mseg adjustments": {
                    "sub-market": {
                        "original stock (total)": {},
                        "adjusted stock (sub-market)": {}},
                    "stock-and-flow": {
                        "original stock (total)": {},
                        "adjusted stock (previously captured)": {},
                        "adjusted stock (competed)": {},
                        "adjusted stock (competed and captured)": {}},
                    "market share": {
                        "original stock (total captured)": {},
                        "original stock (competed and captured)": {},
                        "adjusted stock (total captured)": {},
                        "adjusted stock (competed and captured)": {}}},
                "supply-demand adjustment": {
                    "savings": {},
                    "total": {}}}}
        cls.sample_measure_in = measures_prep.Measure(
            handyvars, **sample_measure_in)
        cls.sample_convertdata_ok_in = {
            "building type conversions": {
                "original type": "EnergyPlus reference buildings",
                "revised type": "Annual Energy Outlook (AEO) buildings",
                "conversion data": {
                    "description": "sample",
                    "value": {
                        "residential": {
                            "single family home": {
                                "Single-Family": 1},
                            "mobile home": {
                                "Single-Family": 1},
                            "multi family home": {
                                "Multifamily": 1}},
                        "commercial": {
                            "assembly": {
                                "Hospital": 1},
                            "education": {
                                "PrimarySchool": 0.26,
                                "SecondarySchool": 0.74},
                            "food sales": {
                                "Supermarket": 1},
                            "food service": {
                                "QuickServiceRestaurant": 0.31,
                                "FullServiceRestaurant": 0.69},
                            "healthcare": None,
                            "lodging": {
                                "SmallHotel": 0.26,
                                "LargeHotel": 0.74},
                            "large office": {
                                "LargeOffice": 0.9,
                                "MediumOffice": 0.1},
                            "small office": {
                                "SmallOffice": 0.12,
                                "OutpatientHealthcare": 0.88},
                            "mercantile and service": {
                                "RetailStandalone": 0.53,
                                "RetailStripmall": 0.47},
                            "warehouse": {
                                "Warehouse": 1},
                            "other": None}},
                    "source": {
                        "residential": "sample",
                        "commercial": "sample"},
                    "notes": {
                        "residential": "sample",
                        "commercial": "sample"}}},
            "cost unit conversions": {
                "heating and cooling": {
                    "supply": {
                        "heating equipment": {
                            "original units": "$/kBtuh",
                            "revised units": "$/ft^2 floor",
                            "conversion factor": {
                                "description": "sample",
                                "value": 0.020,
                                "units": "kBtuh/ft^2 floor",
                                "source": "Rule of thumb",
                                "notes": "sample"}},
                        "cooling equipment": {
                            "original units": "$/kBtuh",
                            "revised units": "$/ft^2 floor",
                            "conversion factor": {
                                "description": "sample",
                                "value": 0.036,
                                "units": "kBtuh/ft^2 floor",
                                "source": "Rule of thumb",
                                "notes": "sample"}}},
                    "demand": {
                        "windows": {
                            "original units": "$/ft^2 glazing",
                            "revised units": "$/ft^2 wall",
                            "conversion factor": {
                                "description": "Window to wall ratio",
                                "value": {
                                    "residential": {
                                        "single family home": {
                                            "Single-Family": 0.15},
                                        "mobile home": {
                                            "Single-Family": 0.15},
                                        "multi family home": {
                                            "Multifamily": 0.10}},
                                    "commercial": {
                                        "assembly": {
                                            "Hospital": 0.15},
                                        "education": {
                                            "PrimarySchool": 0.35,
                                            "SecondarySchool": 0.33},
                                        "food sales": {
                                            "Supermarket": 0.11},
                                        "food service": {
                                            "QuickServiceRestaurant": 0.14,
                                            "FullServiceRestaurant": 0.17},
                                        "healthcare": 0.2,
                                        "lodging": {
                                            "SmallHotel": 0.11,
                                            "LargeHotel": 0.27},
                                        "large office": {
                                            "LargeOffice": 0.38,
                                            "MediumOffice": 0.33},
                                        "small office": {
                                            "SmallOffice": 0.21,
                                            "OutpatientHealthcare": 0.19},
                                        "mercantile and service": {
                                            "RetailStandalone": 0.07,
                                            "RetailStripmall": 0.11},
                                        "warehouse": {
                                            "Warehouse": 0.006},
                                        "other": 0.2}},
                                "units": None,
                                "source": {
                                    "residential": "sample",
                                    "commercial": "sample"},
                                "notes": "sample"}},
                        "walls": {
                            "original units": "$/ft^2 wall",
                            "revised units": "$/ft^2 floor",
                            "conversion factor": {
                                "description": "Wall to floor ratio",
                                "value": {
                                    "residential": {
                                        "single family home": {
                                            "Single-Family": 1},
                                        "mobile home": {
                                            "Single-Family": 1},
                                        "multi family home": {
                                            "Multifamily": 1}},
                                    "commercial": {
                                        "assembly": {
                                            "Hospital": 0.26},
                                        "education": {
                                            "PrimarySchool": 0.20,
                                            "SecondarySchool": 0.16},
                                        "food sales": {
                                            "Supermarket": 0.38},
                                        "food service": {
                                            "QuickServiceRestaurant": 0.80,
                                            "FullServiceRestaurant": 0.54},
                                        "healthcare": 0.4,
                                        "lodging": {
                                            "SmallHotel": 0.40,
                                            "LargeHotel": 0.38},
                                        "large office": {
                                            "LargeOffice": 0.26,
                                            "MediumOffice": 0.40},
                                        "small office": {
                                            "SmallOffice": 0.55,
                                            "OutpatientHealthcare": 0.35},
                                        "mercantile and service": {
                                            "RetailStandalone": 0.51,
                                            "RetailStripmall": 0.57},
                                        "warehouse": {
                                            "Warehouse": 0.53},
                                        "other": 0.4}},
                                "units": None,
                                "source": {
                                    "residential": "sample",
                                    "commercial": "sample"},
                                "notes": "sample"}},
                        "footprint": {
                            "original units": "$/ft^2 footprint",
                            "revised units": "$/ft^2 floor",
                            "conversion factor": {
                                "description": "sample",
                                "value": {
                                    "residential": {
                                        "single family home": {
                                            "Single-Family": 0.5},
                                        "mobile home": {
                                            "Single-Family": 0.5},
                                        "multi family home": {
                                            "Multifamily": 0.33}},
                                    "commercial": {
                                        "assembly": {
                                            "Hospital": 0.20},
                                        "education": {
                                            "PrimarySchool": 1,
                                            "SecondarySchool": 0.5},
                                        "food sales": {"Supermarket": 1},
                                        "food service": {
                                            "QuickServiceRestaurant": 1,
                                            "FullServiceRestaurant": 1},
                                        "healthcare": 0.2,
                                        "lodging": {
                                            "SmallHotel": 0.25,
                                            "LargeHotel": 0.17},
                                        "large office": {
                                            "LargeOffice": 0.083,
                                            "MediumOffice": 0.33},
                                        "small office": {
                                            "SmallOffice": 1,
                                            "OutpatientHealthcare": 0.33},
                                        "mercantile and service": {
                                            "RetailStandalone": 1,
                                            "RetailStripmall": 1},
                                        "warehouse": {
                                            "Warehouse": 1},
                                        "other": 1}},
                                "units": None,
                                "source": {
                                    "residential": "sample",
                                    "commercial": "sample"},
                                "notes": "sample"}},
                        "roof": {
                            "original units": "$/ft^2 roof",
                            "revised units": "$/ft^2 footprint",
                            "conversion factor": {
                                "description": "sample",
                                "value": {
                                    "residential": 1.05,
                                    "commercial": 1},
                                "units": None,
                                "source": "Rule of thumb",
                                "notes": "sample"}}}},
                "ventilation": {
                    "original units": "$/1000 CFM",
                    "revised units": "$/ft^2 floor",
                    "conversion factor": {
                        "description": "sample",
                        "value": 0.001,
                        "units": "1000 CFM/ft^2 floor",
                        "source": "Rule of thumb",
                        "notes": "sample"}}}}
        cls.sample_bldgsect_ok_in = [
            "residential", "commercial", "commercial", "commercial",
            "commercial", "commercial"]
        cls.sample_mskeys_ok_in = [
            ('primary', 'marine', 'single family home', 'electricity',
             'cooling', 'demand', 'windows conduction', 'existing'),
            ('primary', 'marine', 'assembly', 'electricity', 'heating',
             'supply', 'rooftop_ASHP-heat', 'new'),
            ('primary', 'marine', 'food sales', 'electricity', 'cooling',
             'demand', 'ground', 'new'),
            ('primary', 'marine', 'education', 'electricity', 'cooling',
             'demand', 'roof', 'existing'),
            ('primary', 'marine', 'lodging', 'electricity', 'cooling',
             'demand', 'wall', 'new'),
            ('primary', 'marine', 'food service', 'electricity', 'ventilation',
             'CAV_Vent', 'existing')]
        cls.sample_mskeys_fail_in = [
            ('primary', 'marine', 'single family home', 'electricity',
             'cooling', 'demand', 'people gain', 'existing'),
            ('primary', 'marine', 'assembly', 'electricity', 'PCs',
             None, 'new')]
        cls.cost_meas_ok_in = 10
        cls.cost_meas_units_ok_in = [
            '$/ft^2 glazing', '2013$/kBtuh', '2010$/ft^2 footprint',
            '2016$/ft^2 roof', '2013$/ft^2 wall', '2012$/1000 CFM']
        cls.cost_meas_units_fail_in = '$/ft^2 facade'
        cls.cost_base_units_ok_in = '2013$/ft^2 floor'
        cls.ok_out_costs = [1.47, 0.2, 10.65, 6.18, 3.85, 0.01015]
        cls.ok_out_cost_units = '2013$/ft^2 floor'

    def test_convertcost_ok(self):
        """Test 'convert_costs' function given valid inputs."""
        for k in range(0, len(self.sample_mskeys_ok_in)):
            func_output = self.sample_measure_in.convert_costs(
                self.sample_convertdata_ok_in, self.sample_bldgsect_ok_in[k],
                self.sample_mskeys_ok_in[k], self.cost_meas_ok_in,
                self.cost_meas_units_ok_in[k], self.cost_base_units_ok_in)
            numpy.testing.assert_almost_equal(
                func_output[0], self.ok_out_costs[k], decimal=2)
            self.assertEqual(func_output[1], self.ok_out_cost_units)

    def test_convertcost_fail(self):
        """Test 'convert_costs' function given invalid inputs."""
        # Test for KeyError
        for k in range(0, len(self.sample_mskeys_fail_in)):
            with self.assertRaises(KeyError):
                self.sample_measure_in.convert_costs(
                    self.sample_convertdata_ok_in,
                    self.sample_bldgsect_ok_in[k],
                    self.sample_mskeys_fail_in[k], self.cost_meas_ok_in,
                    self.cost_meas_units_ok_in[k], self.cost_base_units_ok_in)
        # Test for ValueError
        with self.assertRaises(ValueError):
            self.sample_measure_in.convert_costs(
                self.sample_convertdata_ok_in, self.sample_bldgsect_ok_in[k],
                self.sample_mskeys_ok_in[0], self.cost_meas_ok_in,
                self.cost_meas_units_fail_in[k], self.cost_base_units_ok_in)


class FillMeasuresTest(unittest.TestCase, CommonMethods):
    """Test 'fill_measures' function.

    Ensure that function properly identifies which measures need attribute
    updates and executes these updates.

    Attributes:
        handyvars (object): Global variables to use across measures.
        sample_mseg_in (dict): Sample baseline microsegment stock/energy.
        sample_cpl_in (dict): Sample baseline technology cost, performance,
            and lifetime.
        measures_ok_in (list): List of measures with valid user-defined
            'status' attributes.
        measures_warn_in (list): List of measures that includes one measure
            with invalid 'status' attribute (the measure's 'markets' attribute
            has not been finalized but user has not flagged it for an update).
        convert_data (dict): Data used to convert expected
            user-defined measure cost units to cost units required by Scout
            analysis engine.
        ok_out (list): List of measure master microsegment dicts that
            should be generated by 'fill_measures' given sample input measure
            information to update and an assumed technical potential adoption
            scenario.
        ok_warnmeas_out (list): Warnings that should be yielded when running
            'measures_warn_in' through the function.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        cls.handyvars = measures_prep.UsefulVars()
        # Adjust aeo_years to fit test years
        cls.handyvars.aeo_years = ["2009", "2010"]
        # Adjust carbon intensity data to reflect units originally used for
        # tests (* Note: test outcome units to be adjusted later)
        for k in cls.handyvars.carb_int.keys():
            cls.handyvars.carb_int[k] = {
                yr_key: (cls.handyvars.carb_int[k][yr_key] * 1000000000) for
                yr_key in cls.handyvars.aeo_years}
        cls.sample_mseg_in = {
            "AIA_CZ1": {
                "single family home": {
                    "total square footage": {"2009": 100, "2010": 200},
                    "total homes": {"2009": 1000, "2010": 1000},
                    "new homes": {"2009": 100, "2010": 50},
                    "natural gas": {
                        "water heating": {
                            "stock": {"2009": 15, "2010": 15},
                            "energy": {"2009": 15, "2010": 15}}}}}}
        cls.sample_cpl_in = {
            "AIA_CZ1": {
                "single family home": {
                    "natural gas": {
                        "water heating": {
                            "performance": {
                                "typical": {"2009": 18, "2010": 18},
                                "best": {"2009": 18, "2010": 18},
                                "units": "EF",
                                "source":
                                "EIA AEO"},
                            "installed cost": {
                                "typical": {"2009": 18, "2010": 18},
                                "best": {"2009": 18, "2010": 18},
                                "units": "2014$/unit",
                                "source": "EIA AEO"},
                            "lifetime": {
                                "average": {"2009": 180, "2010": 180},
                                "range": {"2009": 18, "2010": 18},
                                "units": "years",
                                "source": "EIA AEO"},
                            "consumer choice": {
                                "competed market share": {
                                    "source": "EIA AEO",
                                    "model type": "logistic regression",
                                    "parameters": {
                                        "b1": {"2009": None, "2010": None},
                                        "b2": {"2009": None,
                                               "2010": None}}},
                                "competed market": {
                                    "source": "COBAM",
                                    "model type": "bass diffusion",
                                    "parameters": {
                                        "p": "NA",
                                        "q": "NA"}}}}}}}}
        cls.convert_data = {}  # Blank for now
        cls.measures_ok_in = [{
            "name": "sample measure to update (user-flagged)",
            "status": {"active": True, "finalized": False},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {"new": 25, "existing": 25},
                "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}},
            {
            "name": "sample measure to not update",
            "status": {"active": True, "finalized": True},
            "markets": {
                "Technical potential": {
                    "master_mseg": {}, "mseg_adjust": {},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {}, "mseg_adjust": {},
                    "mseg_out_break": {}}},
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {"new": 25, "existing": 25},
                "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}}]
        cls.measures_warn_in = [{
            "name": "sample measure to update (not flagged)",
            "status": {"active": True, "finalized": True},
            "markets": None,
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {"new": 25, "existing": 25},
                "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}},
            {
            "name": "sample measure to not update",
            "status": {"active": True, "finalized": True},
            "markets": {
                "Technical potential": {
                    "master_mseg": {}, "mseg_adjust": {},
                    "mseg_out_break": {}},
                "Max adoption potential": {
                    "master_mseg": {}, "mseg_adjust": {},
                    "mseg_out_break": {}}},
            "installed_cost": 25,
            "cost_units": "2014$/unit",
            "energy_efficiency": {
                "primary": {"new": 25, "existing": 25},
                "secondary": None},
            "energy_efficiency_units": {"primary": "EF",
                                        "secondary": None},
            "market_entry_year": None,
            "market_exit_year": None,
            "product_lifetime": 1,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "bldg_type": ["single family home"],
            "climate_zone": ["AIA_CZ1"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None}}]
        cls.ok_out = [{
            "stock": {
                "total": {
                    "all": {"2009": 15, "2010": 15},
                    "measure": {"2009": 15, "2010": 15}},
                "competed": {
                    "all": {"2009": 15, "2010": 15},
                    "measure": {"2009": 15, "2010": 15}}},
            "energy": {
                "total": {
                    "baseline": {"2009": 15.15, "2010": 15.15},
                    "efficient": {"2009": 10.908, "2010": 10.908}},
                "competed": {
                    "baseline": {"2009": 15.15, "2010": 15.15},
                    "efficient": {"2009": 10.908, "2010": 10.908}}},
            "carbon": {
                "total": {
                    "baseline": {"2009": 856.2139, "2010": 832.0021},
                    "efficient": {"2009": 616.474, "2010": 599.0415}},
                "competed": {
                    "baseline": {"2009": 856.2139, "2010": 832.0021},
                    "efficient": {"2009": 616.474, "2010": 599.0415}}},
            "cost": {
                "stock": {
                    "total": {
                        "baseline": {"2009": 270, "2010": 270},
                        "efficient": {"2009": 375, "2010": 375}},
                    "competed": {
                        "baseline": {"2009": 270, "2010": 270},
                        "efficient": {"2009": 375, "2010": 375}}},
                "energy": {
                    "total": {
                        "baseline": {"2009": 170.892, "2010": 163.317},
                        "efficient": {"2009": 123.0422, "2010": 117.5882}},
                    "competed": {
                        "baseline": {"2009": 170.892, "2010": 163.317},
                        "efficient": {"2009": 123.0422, "2010": 117.5882}}},
                "carbon": {
                    "total": {
                        "baseline": {"2009": 28255.06, "2010": 27456.07},
                        "efficient": {"2009": 20343.64, "2010": 19768.37}},
                    "competed": {
                        "baseline": {"2009": 28255.06, "2010": 27456.07},
                        "efficient": {"2009": 20343.64, "2010": 19768.37}}}},
            "lifetime": {"baseline": {"2009": 180, "2010": 180},
                         "measure": 1}},
            {"master_mseg": {}, "mseg_adjust": {},
             "mseg_out_break": {}}]
        cls.ok_warnmeas_out = \
            [("WARNING: Incomplete 'markets' attribute for active "
              "measure 'sample measure to update (not flagged)'; this "
              "information will be added automatically")]

    def test_fillmeas_ok(self):
        """Test 'fill_measures' function given valid measure inputs.

        Note:
            Ensure that function properly identifies which input measures
            require updating and that the updates are performed correctly.
        """
        measures_out = measures_prep.fill_measures(
            self.measures_ok_in, self.convert_data,
            self.sample_mseg_in, self.sample_cpl_in, self.handyvars,
            eplus_dir=None)
        for oc in range(0, len(measures_out)):
            self.dict_check(
                measures_out[oc]["markets"][
                    "Technical potential"]["master_mseg"], self.ok_out[oc])

    def test_fillmeas_warn(self):
        """Test 'fill_measures' function given incomplete measure inputs.

        Raises:
            AssertionError: If function yields unexpected results or
            UserWarning is not raised.
        """
        with warnings.catch_warnings(record=True) as w:
            measures_prep.fill_measures(
                self.measures_warn_in, self.convert_data,
                self.sample_mseg_in, self.sample_cpl_in, self.handyvars,
                eplus_dir=None)
            # Check correct number of warnings is yielded
            self.assertEqual(len(w), len(self.ok_warnmeas_out))
            # Check correct type of warnings is yielded
            self.assertTrue(all([
                issubclass(wn.category, UserWarning) for wn in w]))
            # Check correct warning messages are yielded
            [self.assertTrue(wm in str([wmt.message for wmt in w])) for
                wm in self.ok_warnmeas_out]


class MergeMeasuresTest(unittest.TestCase, CommonMethods):
    """Test 'merge_measures' function.

    Ensure that the function correctly assembles a series of attributes for
    individual measures into attributes for a packaged measure.

    Attributes:
        sample_measures_in (list): List of valid sample measure attributes
            to package.
        sample_package_name (string): Sample packaged measure name.
        sample_package_in (object): Sample packaged measure object to update.
        genattr_ok_out (list): General attributes that should be yielded
            for the packaged measure given valid sample measures to package.
        markets_ok_out (dict): Packaged measure markets (e.g. stock, energy,
            carbon, cost) that should be yielded given valid sample measures
            to package.
    """

    @classmethod
    def setUpClass(cls):
        """Define variables and objects for use across all class functions."""
        handyvars = measures_prep.UsefulVars()
        handyvars.aeo_years = ["2009", "2010"]
        cls.sample_measures_in = [{
            "name": "sample measure pkg 1",
            "status": {"active": True, "finalized": True},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new", "existing"],
            "climate_zone": ["AIA_CZ1", "AIA_CZ2"],
            "bldg_type": ["single family home"],
            "fuel_type": {"primary": ["natural gas"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["water heating"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": None,
                           "secondary": None},
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 40, "2010": 40},
                                "measure": {"2009": 24, "2010": 24}},
                            "competed": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 4, "2010": 4}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 80, "2010": 80},
                                "efficient": {"2009": 48, "2010": 48}},
                            "competed": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 8, "2010": 8}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 120, "2010": 120},
                                "efficient": {"2009": 72, "2010": 72}},
                            "competed": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 12, "2010": 12}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 72, "2010": 72}},
                                "competed": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 72, "2010": 72}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 80, "2010": 80},
                                    "efficient": {"2009": 48, "2010": 48}},
                                "competed": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 8, "2010": 8}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 120, "2010": 120},
                                    "efficient": {"2009": 72, "2010": 72}},
                                "competed": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 12, "2010": 12}}}},
                        "lifetime": {
                            "baseline": {"2009": 5, "2010": 5},
                            "measure": 10}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'natural gas', 'water heating', None, 'new')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 6, "2010": 6}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 1, "2010": 1}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 12, "2010": 12}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 2, "2010": 2}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 3, "2010": 3}}}},
                                "lifetime": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "measure": 10}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'natural gas', 'water heating', None, "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 6, "2010": 6}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 1, "2010": 1}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 12, "2010": 12}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 2, "2010": 2}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 3, "2010": 3}}}},
                                "lifetime": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "measure": 10}},
                            ("('primary', AIA_CZ2', 'single family home', "
                             "'natural gas', 'water heating', None, 'new')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 6, "2010": 6}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 1, "2010": 1}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 12, "2010": 12}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 2, "2010": 2}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 3, "2010": 3}}}},
                                "lifetime": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "measure": 10}},
                            ("('primary', AIA_CZ2', 'single family home', "
                             "'natural gas', 'water heating', None, "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 6, "2010": 6}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 1, "2010": 1}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 12, "2010": 12}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 2, "2010": 2}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 3, "2010": 3}}}},
                                "lifetime": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "measure": 10}}},
                        "competed choice parameters": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'natural gas', 'water heating', None, 'new')"): {
                                "b1": {"2009": 0.5, "2010": 0.5},
                                "b2": {"2009": 0.5, "2010": 0.5}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'natural gas', 'water heating', None, "
                             "'existing')"): {
                                "b1": {"2009": 0.5, "2010": 0.5},
                                "b2": {"2009": 0.5, "2010": 0.5}},
                            ("('primary', AIA_CZ2', 'single family home', "
                             "'natural gas', 'water heating', None, 'new')"): {
                                "b1": {"2009": 0.5, "2010": 0.5},
                                "b2": {"2009": 0.5, "2010": 0.5}},
                            ("('primary', AIA_CZ2', 'single family home', "
                             "'natural gas', 'water heating', None, "
                             "'existing')"): {
                                "b1": {"2009": 0.5, "2010": 0.5},
                                "b2": {"2009": 0.5, "2010": 0.5}}},
                        "secondary mseg adjustments": {
                            "sub-market": {
                                "original stock (total)": {},
                                "adjusted stock (sub-market)": {}},
                            "stock-and-flow": {
                                "original stock (total)": {},
                                "adjusted stock (previously captured)": {},
                                "adjusted stock (competed)": {},
                                "adjusted stock (competed and captured)": {}},
                            "market share": {
                                "original stock (total captured)": {},
                                "original stock (competed and captured)": {},
                                "adjusted stock (total captured)": {},
                                "adjusted stock (competed and captured)": {}}},
                        "supply-demand adjustment": {
                            "savings": {},
                            "total": {}}},
                    "mseg_out_break": {
                        'AIA CZ1': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {"2009": 0.5, "2010": 0.5},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ2': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {
                                    "2009": 0.5, "2010": 0.5},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ3': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ4': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ5': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {}, 'Refrigeration': {},
                                'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}}}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 40, "2010": 40},
                                "measure": {"2009": 24, "2010": 24}},
                            "competed": {
                                "all": {"2009": 20, "2010": 20},
                                "measure": {"2009": 4, "2010": 4}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 80, "2010": 80},
                                "efficient": {"2009": 48, "2010": 48}},
                            "competed": {
                                "baseline": {"2009": 40, "2010": 40},
                                "efficient": {"2009": 8, "2010": 8}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 120, "2010": 120},
                                "efficient": {"2009": 72, "2010": 72}},
                            "competed": {
                                "baseline": {"2009": 60, "2010": 60},
                                "efficient": {"2009": 12, "2010": 12}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 72, "2010": 72}},
                                "competed": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 72, "2010": 72}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 80, "2010": 80},
                                    "efficient": {"2009": 48, "2010": 48}},
                                "competed": {
                                    "baseline": {"2009": 40, "2010": 40},
                                    "efficient": {"2009": 8, "2010": 8}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 120, "2010": 120},
                                    "efficient": {"2009": 72, "2010": 72}},
                                "competed": {
                                    "baseline": {"2009": 60, "2010": 60},
                                    "efficient": {"2009": 12, "2010": 12}}}},
                        "lifetime": {
                            "baseline": {"2009": 5, "2010": 5},
                            "measure": 10}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'natural gas', 'water heating', None, 'new')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 6, "2010": 6}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 1, "2010": 1}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 12, "2010": 12}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 2, "2010": 2}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 3, "2010": 3}}}},
                                "lifetime": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "measure": 10}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'natural gas', 'water heating', None, "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 6, "2010": 6}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 1, "2010": 1}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 12, "2010": 12}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 2, "2010": 2}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 3, "2010": 3}}}},
                                "lifetime": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "measure": 10}},
                            ("('primary', AIA_CZ2', 'single family home', "
                             "'natural gas', 'water heating', None, 'new')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 6, "2010": 6}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 1, "2010": 1}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 12, "2010": 12}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 2, "2010": 2}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 3, "2010": 3}}}},
                                "lifetime": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "measure": 10}},
                            ("('primary', AIA_CZ2', 'single family home', "
                             "'natural gas', 'water heating', None, "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 10, "2010": 10},
                                        "measure": {"2009": 6, "2010": 6}},
                                    "competed": {
                                        "all": {"2009": 5, "2010": 5},
                                        "measure": {"2009": 1, "2010": 1}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 18, "2010": 18}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 20, "2010": 20},
                                            "efficient": {
                                                "2009": 12, "2010": 12}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 10, "2010": 10},
                                            "efficient": {
                                                "2009": 2, "2010": 2}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 30, "2010": 30},
                                            "efficient": {
                                                "2009": 18, "2010": 18}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 15, "2010": 15},
                                            "efficient": {
                                                "2009": 3, "2010": 3}}}},
                                "lifetime": {
                                    "baseline": {"2009": 5, "2010": 5},
                                    "measure": 10}}},
                        "competed choice parameters": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'natural gas', 'water heating', None, 'new')"): {
                                "b1": {"2009": 0.5, "2010": 0.5},
                                "b2": {"2009": 0.5, "2010": 0.5}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'natural gas', 'water heating', None, "
                             "'existing')"): {
                                "b1": {"2009": 0.5, "2010": 0.5},
                                "b2": {"2009": 0.5, "2010": 0.5}},
                            ("('primary', AIA_CZ2', 'single family home', "
                             "'natural gas', 'water heating', None, 'new')"): {
                                "b1": {"2009": 0.5, "2010": 0.5},
                                "b2": {"2009": 0.5, "2010": 0.5}},
                            ("('primary', AIA_CZ2', 'single family home', "
                             "'natural gas', 'water heating', None, "
                             "'existing')"): {
                                "b1": {"2009": 0.5, "2010": 0.5},
                                "b2": {"2009": 0.5, "2010": 0.5}}},
                        "secondary mseg adjustments": {
                            "sub-market": {
                                "original stock (total)": {},
                                "adjusted stock (sub-market)": {}},
                            "stock-and-flow": {
                                "original stock (total)": {},
                                "adjusted stock (previously captured)": {},
                                "adjusted stock (competed)": {},
                                "adjusted stock (competed and captured)": {}},
                            "market share": {
                                "original stock (total captured)": {},
                                "original stock (competed and captured)": {},
                                "adjusted stock (total captured)": {},
                                "adjusted stock (competed and captured)": {}}},
                        "supply-demand adjustment": {
                            "savings": {},
                            "total": {}}},
                    "mseg_out_break": {
                        'AIA CZ1': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {"2009": 0.5, "2010": 0.5},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ2': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {
                                    "2009": 0.5, "2010": 0.5},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ3': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ4': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ5': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {}, 'Refrigeration': {},
                                'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}}}}}},
            {
            "name": "sample measure pkg 2",
            "status": {"active": True, "finalized": True},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["existing"],
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["single family home"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["lighting"],
                        "secondary": None},
            "technology_type": {"primary": "supply",
                                "secondary": None},
            "technology": {"primary": [
                "reflector (incandescent)",
                "reflector (halogen)"], "secondary": None},
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 200, "2010": 200},
                                "measure": {"2009": 120, "2010": 120}},
                            "competed": {
                                "all": {"2009": 100, "2010": 100},
                                "measure": {"2009": 20, "2010": 20}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 400, "2010": 400},
                                "efficient": {"2009": 240, "2010": 240}},
                            "competed": {
                                "baseline": {"2009": 200, "2010": 200},
                                "efficient": {"2009": 40, "2010": 40}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 600, "2010": 600},
                                "efficient": {"2009": 360, "2010": 360}},
                            "competed": {
                                "baseline": {"2009": 300, "2010": 300},
                                "efficient": {"2009": 60, "2010": 60}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 360, "2010": 360}},
                                "competed": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 360, "2010": 360}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 400, "2010": 400},
                                    "efficient": {"2009": 240, "2010": 240}},
                                "competed": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 40, "2010": 40}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 600, "2010": 600},
                                    "efficient": {"2009": 360, "2010": 360}},
                                "competed": {
                                    "baseline": {"2009": 300, "2010": 300},
                                    "efficient": {"2009": 60, "2010": 60}}}},
                        "lifetime": {
                            "baseline": {"2009": 1, "2010": 1},
                            "measure": 20}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 100, "2010": 100},
                                        "measure": {"2009": 60, "2010": 60}},
                                    "competed": {
                                        "all": {"2009": 50, "2010": 50},
                                        "measure": {"2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": 20}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (halogen)', "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 100, "2010": 100},
                                        "measure": {"2009": 60, "2010": 60}},
                                    "competed": {
                                        "all": {"2009": 50, "2010": 50},
                                        "measure": {"2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 2, "2010": 2},
                                    "measure": 15}}},
                        "competed choice parameters": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "b1": {"2009": 0.25, "2010": 0.25},
                                "b2": {"2009": 0.25, "2010": 0.25}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (halogen)', "
                             "'existing')"): {
                                "b1": {"2009": 0.25, "2010": 0.25},
                                "b2": {"2009": 0.25, "2010": 0.25}}},
                        "secondary mseg adjustments": {
                            "sub-market": {
                                "original stock (total)": {},
                                "adjusted stock (sub-market)": {}},
                            "stock-and-flow": {
                                "original stock (total)": {},
                                "adjusted stock (previously captured)": {},
                                "adjusted stock (competed)": {},
                                "adjusted stock (competed and captured)": {}},
                            "market share": {
                                "original stock (total captured)": {},
                                "original stock (competed and captured)": {},
                                "adjusted stock (total captured)": {},
                                "adjusted stock (competed and captured)": {}}},
                        "supply-demand adjustment": {
                            "savings": {},
                            "total": {}}},
                    "mseg_out_break": {
                        'AIA CZ1': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {"2009": 1, "2010": 1},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ2': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ3': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ4': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ5': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {}, 'Refrigeration': {},
                                'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}}}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 200, "2010": 200},
                                "measure": {"2009": 120, "2010": 120}},
                            "competed": {
                                "all": {"2009": 100, "2010": 100},
                                "measure": {"2009": 20, "2010": 20}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 400, "2010": 400},
                                "efficient": {"2009": 240, "2010": 240}},
                            "competed": {
                                "baseline": {"2009": 200, "2010": 200},
                                "efficient": {"2009": 40, "2010": 40}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 600, "2010": 600},
                                "efficient": {"2009": 360, "2010": 360}},
                            "competed": {
                                "baseline": {"2009": 300, "2010": 300},
                                "efficient": {"2009": 60, "2010": 60}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 360, "2010": 360}},
                                "competed": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 360, "2010": 360}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 400, "2010": 400},
                                    "efficient": {"2009": 240, "2010": 240}},
                                "competed": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 40, "2010": 40}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 600, "2010": 600},
                                    "efficient": {"2009": 360, "2010": 360}},
                                "competed": {
                                    "baseline": {"2009": 300, "2010": 300},
                                    "efficient": {"2009": 60, "2010": 60}}}},
                        "lifetime": {
                            "baseline": {"2009": 1, "2010": 1},
                            "measure": 20}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 100, "2010": 100},
                                        "measure": {"2009": 60, "2010": 60}},
                                    "competed": {
                                        "all": {"2009": 50, "2010": 50},
                                        "measure": {"2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": 20}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (halogen)', "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 100, "2010": 100},
                                        "measure": {"2009": 60, "2010": 60}},
                                    "competed": {
                                        "all": {"2009": 50, "2010": 50},
                                        "measure": {"2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 2, "2010": 2},
                                    "measure": 15}}},
                        "competed choice parameters": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "b1": {"2009": 0.25, "2010": 0.25},
                                "b2": {"2009": 0.25, "2010": 0.25}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (halogen)', "
                             "'existing')"): {
                                "b1": {"2009": 0.25, "2010": 0.25},
                                "b2": {"2009": 0.25, "2010": 0.25}}},
                        "secondary mseg adjustments": {
                            "sub-market": {
                                "original stock (total)": {},
                                "adjusted stock (sub-market)": {}},
                            "stock-and-flow": {
                                "original stock (total)": {},
                                "adjusted stock (previously captured)": {},
                                "adjusted stock (competed)": {},
                                "adjusted stock (competed and captured)": {}},
                            "market share": {
                                "original stock (total captured)": {},
                                "original stock (competed and captured)": {},
                                "adjusted stock (total captured)": {},
                                "adjusted stock (competed and captured)": {}}},
                        "supply-demand adjustment": {
                            "savings": {},
                            "total": {}}},
                    "mseg_out_break": {
                        'AIA CZ1': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {"2009": 1, "2010": 1},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ2': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ3': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ4': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ5': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {}, 'Refrigeration': {},
                                'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}}}}}},
            {
            "name": "sample measure pkg 3",
            "status": {"active": True, "finalized": True},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "full service",
            "structure_type": ["new"],
            "climate_zone": ["AIA_CZ5"],
            "bldg_type": ["multi family home"],
            "fuel_type": {"primary": ["electricity"],
                          "secondary": None},
            "fuel_switch_to": None,
            "end_use": {
                "primary": ["cooling", "lighting"],
                "secondary": None},
            "technology_type": {
                "primary": "supply",
                "secondary": None},
            "technology": {
                "primary": [
                    "ASHP",
                    "reflector (incandescent)"],
                "secondary": None},
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 1000, "2010": 1000},
                                "measure": {"2009": 600, "2010": 600}},
                            "competed": {
                                "all": {"2009": 500, "2010": 500},
                                "measure": {"2009": 100, "2010": 100}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 2000, "2010": 2000},
                                "efficient": {"2009": 1200, "2010": 1200}},
                            "competed": {
                                "baseline": {"2009": 1000, "2010": 1000},
                                "efficient": {"2009": 200, "2010": 200}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 3000, "2010": 3000},
                                "efficient": {"2009": 1800, "2010": 1800}},
                            "competed": {
                                "baseline": {"2009": 1500, "2010": 1500},
                                "efficient": {"2009": 300, "2010": 300}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 180, "2010": 180}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 120, "2010": 120}},
                                "competed": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 20, "2010": 20}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 300, "2010": 300},
                                    "efficient": {"2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {"2009": 150, "2010": 150},
                                    "efficient": {"2009": 30, "2010": 30}}}},
                        "lifetime": {
                            "baseline": {"2009": 18, "2010": 18},
                            "measure": 18}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 100, "2010": 100},
                                        "measure": {"2009": 60, "2010": 60}},
                                    "competed": {
                                        "all": {"2009": 50, "2010": 50},
                                        "measure": {"2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": 20}},
                            ("('primary', AIA_CZ5', 'single family home', "
                             "'electricity',"
                             "'cooling', 'supply', 'ASHP', 'new')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 1000, "2010": 1000},
                                        "measure": {"2009": 600, "2010": 600}},
                                    "competed": {
                                        "all": {"2009": 500, "2010": 500},
                                        "measure": {
                                            "2009": 100, "2010": 100}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 2000, "2010": 2000},
                                        "efficient": {
                                            "2009": 1200, "2010": 1200}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 1000, "2010": 1000},
                                        "efficient": {
                                            "2009": 200, "2010": 200}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 3000, "2010": 3000},
                                        "efficient": {
                                            "2009": 1800, "2010": 1800}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 1500, "2010": 1500},
                                        "efficient": {
                                            "2009": 300, "2010": 300}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 18, "2010": 18},
                                    "measure": 18}}},
                        "competed choice parameters": {
                            ("('primary', AIA_CZ5', 'single family home', "
                             "'electricity',"
                             "'cooling', 'supply', 'ASHP', 'new')"): {
                                "b1": {"2009": 0.75, "2010": 0.75},
                                "b2": {"2009": 0.75, "2010": 0.75}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (halogen)', "
                             "'existing')"): {
                                "b1": {"2009": 0.25, "2010": 0.25},
                                "b2": {"2009": 0.25, "2010": 0.25}}},
                        "secondary mseg adjustments": {
                            "sub-market": {
                                "original stock (total)": {},
                                "adjusted stock (sub-market)": {}},
                            "stock-and-flow": {
                                "original stock (total)": {},
                                "adjusted stock (previously captured)": {},
                                "adjusted stock (competed)": {},
                                "adjusted stock (competed and captured)": {}},
                            "market share": {
                                "original stock (total captured)": {},
                                "original stock (competed and captured)": {},
                                "adjusted stock (total captured)": {},
                                "adjusted stock (competed and captured)": {}}},
                        "supply-demand adjustment": {
                            "savings": {},
                            "total": {}}},
                    "mseg_out_break": {
                        'AIA CZ1': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {"2009": 1, "2010": 1},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ2': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ3': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ4': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ5': {
                            'Residential': {
                                'Cooling': {"2009": 1, "2010": 1},
                                'Ventilation': {},
                                'Lighting': {}, 'Refrigeration': {},
                                'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}}}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 1000, "2010": 1000},
                                "measure": {"2009": 600, "2010": 600}},
                            "competed": {
                                "all": {"2009": 500, "2010": 500},
                                "measure": {"2009": 100, "2010": 100}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 2000, "2010": 2000},
                                "efficient": {"2009": 1200, "2010": 1200}},
                            "competed": {
                                "baseline": {"2009": 1000, "2010": 1000},
                                "efficient": {"2009": 200, "2010": 200}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 3000, "2010": 3000},
                                "efficient": {"2009": 1800, "2010": 1800}},
                            "competed": {
                                "baseline": {"2009": 1500, "2010": 1500},
                                "efficient": {"2009": 300, "2010": 300}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 180, "2010": 180}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 120, "2010": 120}},
                                "competed": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 20, "2010": 20}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 300, "2010": 300},
                                    "efficient": {"2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {"2009": 150, "2010": 150},
                                    "efficient": {"2009": 30, "2010": 30}}}},
                        "lifetime": {
                            "baseline": {"2009": 18, "2010": 18},
                            "measure": 18}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 100, "2010": 100},
                                        "measure": {"2009": 60, "2010": 60}},
                                    "competed": {
                                        "all": {"2009": 50, "2010": 50},
                                        "measure": {"2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": 20}},
                            ("('primary', AIA_CZ5', 'single family home', "
                             "'electricity',"
                             "'cooling', 'supply', 'ASHP', 'new')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 1000, "2010": 1000},
                                        "measure": {"2009": 600, "2010": 600}},
                                    "competed": {
                                        "all": {"2009": 500, "2010": 500},
                                        "measure": {
                                            "2009": 100, "2010": 100}}},
                                "energy": {
                                    "total": {
                                        "baseline": {
                                            "2009": 2000, "2010": 2000},
                                        "efficient": {
                                            "2009": 1200, "2010": 1200}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 1000, "2010": 1000},
                                        "efficient": {
                                            "2009": 200, "2010": 200}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {
                                            "2009": 3000, "2010": 3000},
                                        "efficient": {
                                            "2009": 1800, "2010": 1800}},
                                    "competed": {
                                        "baseline": {
                                            "2009": 1500, "2010": 1500},
                                        "efficient": {
                                            "2009": 300, "2010": 300}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 18, "2010": 18},
                                    "measure": 18}}},
                        "competed choice parameters": {
                            ("('primary', AIA_CZ5', 'single family home', "
                             "'electricity',"
                             "'cooling', 'supply', 'ASHP', 'new')"): {
                                "b1": {"2009": 0.75, "2010": 0.75},
                                "b2": {"2009": 0.75, "2010": 0.75}},
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (halogen)', "
                             "'existing')"): {
                                "b1": {"2009": 0.25, "2010": 0.25},
                                "b2": {"2009": 0.25, "2010": 0.25}}},
                        "secondary mseg adjustments": {
                            "sub-market": {
                                "original stock (total)": {},
                                "adjusted stock (sub-market)": {}},
                            "stock-and-flow": {
                                "original stock (total)": {},
                                "adjusted stock (previously captured)": {},
                                "adjusted stock (competed)": {},
                                "adjusted stock (competed and captured)": {}},
                            "market share": {
                                "original stock (total captured)": {},
                                "original stock (competed and captured)": {},
                                "adjusted stock (total captured)": {},
                                "adjusted stock (competed and captured)": {}}},
                        "supply-demand adjustment": {
                            "savings": {},
                            "total": {}}},
                    "mseg_out_break": {
                        'AIA CZ1': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {"2009": 1, "2010": 1},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ2': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ3': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ4': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ5': {
                            'Residential': {
                                'Cooling': {"2009": 1, "2010": 1},
                                'Ventilation': {},
                                'Lighting': {}, 'Refrigeration': {},
                                'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}}}}}},
            {
            "name": "sample measure pkg 4",
            "status": {"active": True, "finalized": True},
            "market_entry_year": None,
            "market_exit_year": None,
            "market_scaling_fractions": None,
            "market_scaling_fractions_source": None,
            "measure_type": "add-on",
            "structure_type": ["existing"],
            "climate_zone": ["AIA_CZ1"],
            "bldg_type": ["single family home"],
            "fuel_type": {
                "primary": ["electricity"],
                "secondary": None},
            "fuel_switch_to": None,
            "end_use": {"primary": ["lighting"],
                        "secondary": None},
            "technology_type": {
                "primary": "supply",
                "secondary": None},
            "technology": {"primary": [
                "reflector (incandescent)"], "secondary": None},
            "markets": {
                "Technical potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 100, "2010": 100},
                                "measure": {"2009": 60, "2010": 60}},
                            "competed": {
                                "all": {"2009": 50, "2010": 50},
                                "measure": {"2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 200, "2010": 200},
                                "efficient": {
                                    "2009": 120, "2010": 120}},
                            "competed": {
                                "baseline": {"2009": 100, "2010": 100},
                                "efficient": {
                                    "2009": 20, "2010": 20}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 300, "2010": 300},
                                "efficient": {
                                    "2009": 180, "2010": 180}},
                            "competed": {
                                "baseline": {"2009": 150, "2010": 150},
                                "efficient": {
                                    "2009": 30, "2010": 30}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {
                                        "2009": 100, "2010": 100},
                                    "efficient": {
                                        "2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {
                                        "2009": 100, "2010": 100},
                                    "efficient": {
                                        "2009": 180, "2010": 180}}},
                            "energy": {
                                "total": {
                                    "baseline": {
                                        "2009": 200, "2010": 200},
                                    "efficient": {
                                        "2009": 120, "2010": 120}},
                                "competed": {
                                    "baseline": {
                                        "2009": 100, "2010": 100},
                                    "efficient": {
                                        "2009": 20, "2010": 20}}},
                            "carbon": {
                                "total": {
                                    "baseline": {
                                        "2009": 300, "2010": 300},
                                    "efficient": {
                                        "2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {
                                        "2009": 150, "2010": 150},
                                    "efficient": {
                                        "2009": 30, "2010": 30}}}},
                        "lifetime": {
                            "baseline": {"2009": 1, "2010": 1},
                            "measure": 20}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 100, "2010": 100},
                                        "measure": {"2009": 60, "2010": 60}},
                                    "competed": {
                                        "all": {"2009": 50, "2010": 50},
                                        "measure": {"2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": 20}}},
                        "competed choice parameters": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "b1": {"2009": 0.25, "2010": 0.25},
                                "b2": {"2009": 0.25, "2010": 0.25}}},
                        "secondary mseg adjustments": {
                            "sub-market": {
                                "original stock (total)": {},
                                "adjusted stock (sub-market)": {}},
                            "stock-and-flow": {
                                "original stock (total)": {},
                                "adjusted stock (previously captured)": {},
                                "adjusted stock (competed)": {},
                                "adjusted stock (competed and captured)": {}},
                            "market share": {
                                "original stock (total captured)": {},
                                "original stock (competed and captured)": {},
                                "adjusted stock (total captured)": {},
                                "adjusted stock (competed and captured)": {}}},
                        "supply-demand adjustment": {
                            "savings": {},
                            "total": {}}},
                    "mseg_out_break": {
                        'AIA CZ1': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {"2009": 1, "2010": 1},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ2': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ3': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ4': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ5': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {}, 'Refrigeration': {},
                                'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}}}},
                "Max adoption potential": {
                    "master_mseg": {
                        "stock": {
                            "total": {
                                "all": {"2009": 100, "2010": 100},
                                "measure": {"2009": 60, "2010": 60}},
                            "competed": {
                                "all": {"2009": 50, "2010": 50},
                                "measure": {"2009": 10, "2010": 10}}},
                        "energy": {
                            "total": {
                                "baseline": {"2009": 200, "2010": 200},
                                "efficient": {
                                    "2009": 120, "2010": 120}},
                            "competed": {
                                "baseline": {"2009": 100, "2010": 100},
                                "efficient": {
                                    "2009": 20, "2010": 20}}},
                        "carbon": {
                            "total": {
                                "baseline": {"2009": 300, "2010": 300},
                                "efficient": {
                                    "2009": 180, "2010": 180}},
                            "competed": {
                                "baseline": {"2009": 150, "2010": 150},
                                "efficient": {
                                    "2009": 30, "2010": 30}}},
                        "cost": {
                            "stock": {
                                "total": {
                                    "baseline": {
                                        "2009": 100, "2010": 100},
                                    "efficient": {
                                        "2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {
                                        "2009": 100, "2010": 100},
                                    "efficient": {
                                        "2009": 180, "2010": 180}}},
                            "energy": {
                                "total": {
                                    "baseline": {
                                        "2009": 200, "2010": 200},
                                    "efficient": {
                                        "2009": 120, "2010": 120}},
                                "competed": {
                                    "baseline": {
                                        "2009": 100, "2010": 100},
                                    "efficient": {
                                        "2009": 20, "2010": 20}}},
                            "carbon": {
                                "total": {
                                    "baseline": {
                                        "2009": 300, "2010": 300},
                                    "efficient": {
                                        "2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {
                                        "2009": 150, "2010": 150},
                                    "efficient": {
                                        "2009": 30, "2010": 30}}}},
                        "lifetime": {
                            "baseline": {"2009": 1, "2010": 1},
                            "measure": 20}},
                    "mseg_adjust": {
                        "contributing mseg keys and values": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "stock": {
                                    "total": {
                                        "all": {"2009": 100, "2010": 100},
                                        "measure": {"2009": 60, "2010": 60}},
                                    "competed": {
                                        "all": {"2009": 50, "2010": 50},
                                        "measure": {"2009": 10, "2010": 10}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}},
                                "cost": {
                                    "stock": {
                                        "total": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 180, "2010": 180}}},
                                    "energy": {
                                        "total": {
                                            "baseline": {
                                                "2009": 200, "2010": 200},
                                            "efficient": {
                                                "2009": 120, "2010": 120}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 100, "2010": 100},
                                            "efficient": {
                                                "2009": 20, "2010": 20}}},
                                    "carbon": {
                                        "total": {
                                            "baseline": {
                                                "2009": 300, "2010": 300},
                                            "efficient": {
                                                "2009": 180, "2010": 180}},
                                        "competed": {
                                            "baseline": {
                                                "2009": 150, "2010": 150},
                                            "efficient": {
                                                "2009": 30, "2010": 30}}}},
                                "lifetime": {
                                    "baseline": {"2009": 1, "2010": 1},
                                    "measure": 20}}},
                        "competed choice parameters": {
                            ("('primary', AIA_CZ1', 'single family home', "
                             "'electricity',"
                             "'lighting', 'reflector (incandescent)', "
                             "'existing')"): {
                                "b1": {"2009": 0.25, "2010": 0.25},
                                "b2": {"2009": 0.25, "2010": 0.25}}},
                        "secondary mseg adjustments": {
                            "sub-market": {
                                "original stock (total)": {},
                                "adjusted stock (sub-market)": {}},
                            "stock-and-flow": {
                                "original stock (total)": {},
                                "adjusted stock (previously captured)": {},
                                "adjusted stock (competed)": {},
                                "adjusted stock (competed and captured)": {}},
                            "market share": {
                                "original stock (total captured)": {},
                                "original stock (competed and captured)": {},
                                "adjusted stock (total captured)": {},
                                "adjusted stock (competed and captured)": {}}},
                        "supply-demand adjustment": {
                            "savings": {},
                            "total": {}}},
                    "mseg_out_break": {
                        'AIA CZ1': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {"2009": 1, "2010": 1},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ2': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ3': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ4': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}},
                        'AIA CZ5': {
                            'Residential': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {}, 'Refrigeration': {},
                                'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}},
                            'Commercial': {
                                'Cooling': {}, 'Ventilation': {},
                                'Lighting': {},
                                'Refrigeration': {}, 'Other': {},
                                'Water Heating': {},
                                'Computers and Electronics': {},
                                'Heating': {}}}}}}}]
        cls.sample_package_name = "CAC + CFLs + NGWH"
        cls.sample_package_in = measures_prep.MeasurePackage(
            cls.sample_measures_in, cls.sample_package_name, handyvars)
        cls.genattr_ok_out = [
            'Package: CAC + CFLs + NGWH',
            ['AIA_CZ1', 'AIA_CZ2', 'AIA_CZ5'],
            ['single family home', 'multi family home'],
            ['new', 'existing'],
            ['electricity', 'natural gas'],
            ['water heating', 'lighting', 'cooling']]
        cls.markets_ok_out = {
            "Technical potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {'2010': 1240, '2009': 1240},
                            "measure": {'2010': 744, '2009': 744}},
                        "competed": {
                            "all": {'2010': 620, '2009': 620},
                            "measure": {'2010': 124, '2009': 124}}},
                    "energy": {
                        "total": {
                            "baseline": {'2010': 2480, '2009': 2480},
                            "efficient": {'2010': 1488, '2009': 1488}},
                        "competed": {
                            "baseline": {'2010': 1240, '2009': 1240},
                            "efficient": {'2010': 248, '2009': 248}}},
                    "carbon": {
                        "total": {
                            "baseline": {'2010': 3720, '2009': 3720},
                            "efficient": {'2010': 2232, '2009': 2232}},
                        "competed": {
                            "baseline": {'2010': 1860, '2009': 1860},
                            "efficient": {'2010': 372, '2009': 372}}},
                    'cost': {
                        'stock': {
                            'competed': {
                                'efficient': {'2010': 692, '2009': 692},
                                "baseline": {'2010': 340, '2009': 340}},
                            'total': {
                                'efficient': {'2010': 692, '2009': 692},
                                "baseline": {'2010': 340, '2009': 340}}},
                        "energy": {
                            "total": {
                                "baseline": {'2010': 680, '2009': 680},
                                "efficient": {'2010': 408, '2009': 408}},
                            "competed": {
                                "baseline": {'2010': 340, '2009': 340},
                                "efficient": {'2010': 68, '2009': 68}}},
                        "carbon": {
                            "total": {
                                "baseline": {'2010': 1020, '2009': 1020},
                                "efficient": {'2010': 612, '2009': 612}},
                            "competed": {
                                "baseline": {'2010': 510, '2009': 510},
                                "efficient": {'2010': 102, '2009': 102}}}},
                    "lifetime": {
                        "baseline": {'2010': 5.86, '2009': 5.86},
                        "measure": 13.29}},
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'natural gas', 'water heating', None, 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 6, "2010": 6}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 1, "2010": 1}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 12, "2010": 12}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 2, "2010": 2}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 18, "2010": 18}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 3, "2010": 3}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 18, "2010": 18}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}}},
                            "lifetime": {
                                "baseline": {"2009": 5, "2010": 5},
                                "measure": 10}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'natural gas', 'water heating', None, "
                         "'existing')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 6, "2010": 6}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 1, "2010": 1}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 12, "2010": 12}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 2, "2010": 2}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 18, "2010": 18}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 3, "2010": 3}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 18, "2010": 18}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}}},
                            "lifetime": {
                                "baseline": {"2009": 5, "2010": 5},
                                "measure": 10}},
                        ("('primary', AIA_CZ2', 'single family home', "
                         "'natural gas', 'water heating', None, 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 6, "2010": 6}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 1, "2010": 1}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 12, "2010": 12}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 2, "2010": 2}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 18, "2010": 18}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 3, "2010": 3}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 18, "2010": 18}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}}},
                            "lifetime": {
                                "baseline": {"2009": 5, "2010": 5},
                                "measure": 10}},
                        ("('primary', AIA_CZ2', 'single family home', "
                         "'natural gas', 'water heating', None, "
                         "'existing')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 6, "2010": 6}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 1, "2010": 1}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 12, "2010": 12}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 2, "2010": 2}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 18, "2010": 18}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 3, "2010": 3}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 18, "2010": 18}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}}},
                            "lifetime": {
                                "baseline": {"2009": 5, "2010": 5},
                                "measure": 10}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'electricity',"
                         "'lighting', 'reflector (incandescent)', "
                         "'existing')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 100, "2010": 100},
                                    "measure": {"2009": 60, "2010": 60}},
                                "competed": {
                                    "all": {"2009": 50, "2010": 50},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 120, "2010": 120}},
                                "competed": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 20, "2010": 20}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 300, "2010": 300},
                                    "efficient": {"2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {"2009": 150, "2010": 150},
                                    "efficient": {"2009": 30, "2010": 30}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 260, "2010": 260}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 260, "2010": 260}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}}},
                            "lifetime": {
                                "baseline": {"2009": 1, "2010": 1},
                                "measure": 20}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'electricity',"
                         "'lighting', 'reflector (halogen)', 'existing')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 100, "2010": 100},
                                    "measure": {"2009": 60, "2010": 60}},
                                "competed": {
                                    "all": {"2009": 50, "2010": 50},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 120, "2010": 120}},
                                "competed": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 20, "2010": 20}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 300, "2010": 300},
                                    "efficient": {"2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {"2009": 150, "2010": 150},
                                    "efficient": {"2009": 30, "2010": 30}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 180, "2010": 180}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}}},
                            "lifetime": {
                                "baseline": {"2009": 2, "2010": 2},
                                "measure": 15}},
                        ("('primary', AIA_CZ5', 'single family home', "
                         "'electricity',"
                         "'cooling', 'supply', 'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 1000, "2010": 1000},
                                    "measure": {"2009": 600, "2010": 600}},
                                "competed": {
                                    "all": {"2009": 500, "2010": 500},
                                    "measure": {"2009": 100, "2010": 100}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 2000, "2010": 2000},
                                    "efficient": {"2009": 1200, "2010": 1200}},
                                "competed": {
                                    "baseline": {"2009": 1000, "2010": 1000},
                                    "efficient": {"2009": 200, "2010": 200}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 3000, "2010": 3000},
                                    "efficient": {"2009": 1800, "2010": 1800}},
                                "competed": {
                                    "baseline": {"2009": 1500, "2010": 1500},
                                    "efficient": {"2009": 300, "2010": 300}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 180, "2010": 180}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}}},
                            "lifetime": {
                                "baseline": {"2009": 18, "2010": 18},
                                "measure": 18}}},
                    "competed choice parameters": {
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'natural gas', 'water heating', None, 'new')"): {
                            "b1": {"2009": 0.5, "2010": 0.5},
                            "b2": {"2009": 0.5, "2010": 0.5}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'natural gas', 'water heating', None, "
                         "'existing')"): {
                            "b1": {"2009": 0.5, "2010": 0.5},
                            "b2": {"2009": 0.5, "2010": 0.5}},
                        ("('primary', AIA_CZ2', 'single family home', "
                         "'natural gas', 'water heating', None, 'new')"): {
                            "b1": {"2009": 0.5, "2010": 0.5},
                            "b2": {"2009": 0.5, "2010": 0.5}},
                        ("('primary', AIA_CZ2', 'single family home', "
                         "'natural gas', 'water heating', None, "
                         "'existing')"): {
                            "b1": {"2009": 0.5, "2010": 0.5},
                            "b2": {"2009": 0.5, "2010": 0.5}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'electricity',"
                         "'lighting', 'reflector (incandescent)', "
                         "'existing')"): {
                            "b1": {"2009": 0.25, "2010": 0.25},
                            "b2": {"2009": 0.25, "2010": 0.25}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'electricity',"
                         "'lighting', 'reflector (halogen)', "
                         "'existing')"): {
                            "b1": {"2009": 0.25, "2010": 0.25},
                            "b2": {"2009": 0.25, "2010": 0.25}},
                        ("('primary', AIA_CZ5', 'single family home', "
                         "'electricity',"
                         "'cooling', 'supply', 'ASHP', 'new')"): {
                            "b1": {"2009": 0.75, "2010": 0.75},
                            "b2": {"2009": 0.75, "2010": 0.75}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original stock (total)": {},
                            "adjusted stock (sub-market)": {}},
                        "stock-and-flow": {
                            "original stock (total)": {},
                            "adjusted stock (previously captured)": {},
                            "adjusted stock (competed)": {},
                            "adjusted stock (competed and captured)": {}},
                        "market share": {
                            "original stock (total captured)": {},
                            "original stock (competed and captured)": {},
                            "adjusted stock (total captured)": {},
                            "adjusted stock (competed and captured)": {}}},
                    "supply-demand adjustment": {
                        "savings": {},
                        "total": {}}},
                "mseg_out_break": {
                    'AIA CZ1': {
                        'Residential': {
                            'Cooling': {}, 'Ventilation': {},
                            'Lighting': {"2009": 0.161, "2010": 0.161},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {"2009": 0.016, "2010": 0.016},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}},
                    'AIA CZ2': {
                        'Residential': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {"2009": 0.016, "2010": 0.016},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}},
                    'AIA CZ3': {
                        'Residential': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}},
                    'AIA CZ4': {
                        'Residential': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}},
                    'AIA CZ5': {
                        'Residential': {
                            'Cooling': {"2009": 0.806, "2010": 0.806},
                            'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {},
                            'Other': {}, 'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}}}},
            "Max adoption potential": {
                "master_mseg": {
                    "stock": {
                        "total": {
                            "all": {'2010': 1240, '2009': 1240},
                            "measure": {'2010': 744, '2009': 744}},
                        "competed": {
                            "all": {'2010': 620, '2009': 620},
                            "measure": {'2010': 124, '2009': 124}}},
                    "energy": {
                        "total": {
                            "baseline": {'2010': 2480, '2009': 2480},
                            "efficient": {'2010': 1488, '2009': 1488}},
                        "competed": {
                            "baseline": {'2010': 1240, '2009': 1240},
                            "efficient": {'2010': 248, '2009': 248}}},
                    "carbon": {
                        "total": {
                            "baseline": {'2010': 3720, '2009': 3720},
                            "efficient": {'2010': 2232, '2009': 2232}},
                        "competed": {
                            "baseline": {'2010': 1860, '2009': 1860},
                            "efficient": {'2010': 372, '2009': 372}}},
                    'cost': {
                        'stock': {
                            'competed': {
                                'efficient': {'2010': 692, '2009': 692},
                                "baseline": {'2010': 340, '2009': 340}},
                            'total': {
                                'efficient': {'2010': 692, '2009': 692},
                                "baseline": {'2010': 340, '2009': 340}}},
                        "energy": {
                            "total": {
                                "baseline": {'2010': 680, '2009': 680},
                                "efficient": {'2010': 408, '2009': 408}},
                            "competed": {
                                "baseline": {'2010': 340, '2009': 340},
                                "efficient": {'2010': 68, '2009': 68}}},
                        "carbon": {
                            "total": {
                                "baseline": {'2010': 1020, '2009': 1020},
                                "efficient": {'2010': 612, '2009': 612}},
                            "competed": {
                                "baseline": {'2010': 510, '2009': 510},
                                "efficient": {'2010': 102, '2009': 102}}}},
                    "lifetime": {
                        "baseline": {'2010': 5.86, '2009': 5.86},
                        "measure": 13.29}},
                "mseg_adjust": {
                    "contributing mseg keys and values": {
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'natural gas', 'water heating', None, 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 6, "2010": 6}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 1, "2010": 1}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 12, "2010": 12}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 2, "2010": 2}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 18, "2010": 18}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 3, "2010": 3}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 18, "2010": 18}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}}},
                            "lifetime": {
                                "baseline": {"2009": 5, "2010": 5},
                                "measure": 10}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'natural gas', 'water heating', None, "
                         "'existing')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 6, "2010": 6}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 1, "2010": 1}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 12, "2010": 12}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 2, "2010": 2}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 18, "2010": 18}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 3, "2010": 3}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 18, "2010": 18}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}}},
                            "lifetime": {
                                "baseline": {"2009": 5, "2010": 5},
                                "measure": 10}},
                        ("('primary', AIA_CZ2', 'single family home', "
                         "'natural gas', 'water heating', None, 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 6, "2010": 6}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 1, "2010": 1}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 12, "2010": 12}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 2, "2010": 2}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 18, "2010": 18}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 3, "2010": 3}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 18, "2010": 18}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}}},
                            "lifetime": {
                                "baseline": {"2009": 5, "2010": 5},
                                "measure": 10}},
                        ("('primary', AIA_CZ2', 'single family home', "
                         "'natural gas', 'water heating', None, "
                         "'existing')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 10, "2010": 10},
                                    "measure": {"2009": 6, "2010": 6}},
                                "competed": {
                                    "all": {"2009": 5, "2010": 5},
                                    "measure": {"2009": 1, "2010": 1}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 20, "2010": 20},
                                    "efficient": {"2009": 12, "2010": 12}},
                                "competed": {
                                    "baseline": {"2009": 10, "2010": 10},
                                    "efficient": {"2009": 2, "2010": 2}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 30, "2010": 30},
                                    "efficient": {"2009": 18, "2010": 18}},
                                "competed": {
                                    "baseline": {"2009": 15, "2010": 15},
                                    "efficient": {"2009": 3, "2010": 3}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {
                                            "2009": 18, "2010": 18}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 20, "2010": 20},
                                        "efficient": {"2009": 12, "2010": 12}},
                                    "competed": {
                                        "baseline": {"2009": 10, "2010": 10},
                                        "efficient": {"2009": 2, "2010": 2}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 30, "2010": 30},
                                        "efficient": {"2009": 18, "2010": 18}},
                                    "competed": {
                                        "baseline": {"2009": 15, "2010": 15},
                                        "efficient": {"2009": 3, "2010": 3}}}},
                            "lifetime": {
                                "baseline": {"2009": 5, "2010": 5},
                                "measure": 10}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'electricity',"
                         "'lighting', 'reflector (incandescent)', "
                         "'existing')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 100, "2010": 100},
                                    "measure": {"2009": 60, "2010": 60}},
                                "competed": {
                                    "all": {"2009": 50, "2010": 50},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 120, "2010": 120}},
                                "competed": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 20, "2010": 20}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 300, "2010": 300},
                                    "efficient": {"2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {"2009": 150, "2010": 150},
                                    "efficient": {"2009": 30, "2010": 30}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {
                                            "2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 260, "2010": 260}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 260, "2010": 260}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}}},
                            "lifetime": {
                                "baseline": {"2009": 1, "2010": 1},
                                "measure": 20}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'electricity',"
                         "'lighting', 'reflector (halogen)', 'existing')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 100, "2010": 100},
                                    "measure": {"2009": 60, "2010": 60}},
                                "competed": {
                                    "all": {"2009": 50, "2010": 50},
                                    "measure": {"2009": 10, "2010": 10}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 200, "2010": 200},
                                    "efficient": {"2009": 120, "2010": 120}},
                                "competed": {
                                    "baseline": {"2009": 100, "2010": 100},
                                    "efficient": {"2009": 20, "2010": 20}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 300, "2010": 300},
                                    "efficient": {"2009": 180, "2010": 180}},
                                "competed": {
                                    "baseline": {"2009": 150, "2010": 150},
                                    "efficient": {"2009": 30, "2010": 30}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 180, "2010": 180}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}}},
                            "lifetime": {
                                "baseline": {"2009": 2, "2010": 2},
                                "measure": 15}},
                        ("('primary', AIA_CZ5', 'single family home', "
                         "'electricity',"
                         "'cooling', 'supply', 'ASHP', 'new')"): {
                            "stock": {
                                "total": {
                                    "all": {"2009": 1000, "2010": 1000},
                                    "measure": {"2009": 600, "2010": 600}},
                                "competed": {
                                    "all": {"2009": 500, "2010": 500},
                                    "measure": {"2009": 100, "2010": 100}}},
                            "energy": {
                                "total": {
                                    "baseline": {"2009": 2000, "2010": 2000},
                                    "efficient": {"2009": 1200, "2010": 1200}},
                                "competed": {
                                    "baseline": {"2009": 1000, "2010": 1000},
                                    "efficient": {"2009": 200, "2010": 200}}},
                            "carbon": {
                                "total": {
                                    "baseline": {"2009": 3000, "2010": 3000},
                                    "efficient": {"2009": 1800, "2010": 1800}},
                                "competed": {
                                    "baseline": {"2009": 1500, "2010": 1500},
                                    "efficient": {"2009": 300, "2010": 300}}},
                            "cost": {
                                "stock": {
                                    "total": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 180, "2010": 180}}},
                                "energy": {
                                    "total": {
                                        "baseline": {"2009": 200, "2010": 200},
                                        "efficient": {
                                            "2009": 120, "2010": 120}},
                                    "competed": {
                                        "baseline": {"2009": 100, "2010": 100},
                                        "efficient": {
                                            "2009": 20, "2010": 20}}},
                                "carbon": {
                                    "total": {
                                        "baseline": {"2009": 300, "2010": 300},
                                        "efficient": {
                                            "2009": 180, "2010": 180}},
                                    "competed": {
                                        "baseline": {"2009": 150, "2010": 150},
                                        "efficient": {
                                            "2009": 30, "2010": 30}}}},
                            "lifetime": {
                                "baseline": {"2009": 18, "2010": 18},
                                "measure": 18}}},
                    "competed choice parameters": {
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'natural gas', 'water heating', None, 'new')"): {
                            "b1": {"2009": 0.5, "2010": 0.5},
                            "b2": {"2009": 0.5, "2010": 0.5}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'natural gas', 'water heating', None, "
                         "'existing')"): {
                            "b1": {"2009": 0.5, "2010": 0.5},
                            "b2": {"2009": 0.5, "2010": 0.5}},
                        ("('primary', AIA_CZ2', 'single family home', "
                         "'natural gas', 'water heating', None, 'new')"): {
                            "b1": {"2009": 0.5, "2010": 0.5},
                            "b2": {"2009": 0.5, "2010": 0.5}},
                        ("('primary', AIA_CZ2', 'single family home', "
                         "'natural gas', 'water heating', None, "
                         "'existing')"): {
                            "b1": {"2009": 0.5, "2010": 0.5},
                            "b2": {"2009": 0.5, "2010": 0.5}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'electricity',"
                         "'lighting', 'reflector (incandescent)', "
                         "'existing')"): {
                            "b1": {"2009": 0.25, "2010": 0.25},
                            "b2": {"2009": 0.25, "2010": 0.25}},
                        ("('primary', AIA_CZ1', 'single family home', "
                         "'electricity',"
                         "'lighting', 'reflector (halogen)', "
                         "'existing')"): {
                            "b1": {"2009": 0.25, "2010": 0.25},
                            "b2": {"2009": 0.25, "2010": 0.25}},
                        ("('primary', AIA_CZ5', 'single family home', "
                         "'electricity',"
                         "'cooling', 'supply', 'ASHP', 'new')"): {
                            "b1": {"2009": 0.75, "2010": 0.75},
                            "b2": {"2009": 0.75, "2010": 0.75}}},
                    "secondary mseg adjustments": {
                        "sub-market": {
                            "original stock (total)": {},
                            "adjusted stock (sub-market)": {}},
                        "stock-and-flow": {
                            "original stock (total)": {},
                            "adjusted stock (previously captured)": {},
                            "adjusted stock (competed)": {},
                            "adjusted stock (competed and captured)": {}},
                        "market share": {
                            "original stock (total captured)": {},
                            "original stock (competed and captured)": {},
                            "adjusted stock (total captured)": {},
                            "adjusted stock (competed and captured)": {}}},
                    "supply-demand adjustment": {
                        "savings": {},
                        "total": {}}},
                "mseg_out_break": {
                    'AIA CZ1': {
                        'Residential': {
                            'Cooling': {}, 'Ventilation': {},
                            'Lighting': {"2009": 0.161, "2010": 0.161},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {"2009": 0.016, "2010": 0.016},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}},
                    'AIA CZ2': {
                        'Residential': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {"2009": 0.016, "2010": 0.016},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}},
                    'AIA CZ3': {
                        'Residential': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}},
                    'AIA CZ4': {
                        'Residential': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}},
                    'AIA CZ5': {
                        'Residential': {
                            'Cooling': {"2009": 0.806, "2010": 0.806},
                            'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {},
                            'Other': {}, 'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}},
                        'Commercial': {
                            'Cooling': {}, 'Ventilation': {}, 'Lighting': {},
                            'Refrigeration': {}, 'Other': {},
                            'Water Heating': {},
                            'Computers and Electronics': {}, 'Heating': {}}}}}}

    def test_package_measure(self):
        """Test 'merge_measures' function given valid inputs."""
        self.sample_package_in.merge_measures()
        # Check for correct general attributes for packaged measure
        output_lists = [
            self.sample_package_in.name, self.sample_package_in.climate_zone,
            self.sample_package_in.bldg_type,
            self.sample_package_in.structure_type,
            self.sample_package_in.fuel_type["primary"],
            self.sample_package_in.end_use["primary"]]
        for ind in range(0, len(output_lists)):
            self.assertEqual(sorted(self.genattr_ok_out[ind]),
                             sorted(output_lists[ind]))
        # Check for correct markets for packaged measure
        self.dict_check(self.sample_package_in.markets, self.markets_ok_out)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    """Trigger default behavior of running all test fixtures in the file."""
    unittest.main()

if __name__ == "__main__":
    main()
