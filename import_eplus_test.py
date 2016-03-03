#!/usr/bin/env python3

""" Tests for running the EnergyPlus data import """

# Import code to be tested
import import_eplus
# Import needed packages
import unittest
import xlrd
import numpy
import os


class CommonMethods(object):
    """ Define common methods for use in all tests below """

    # Create a routine for checking equality of a dict with point vals
    def dict_check(self, dict1, dict2, msg=None):
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
class CBECSVintageSFTest(unittest.TestCase, CommonMethods):
    """ Test 'CBECS_vintage_sf' function to ensure building vintage
     square footages are read in properly from a CBECS data file """

    # Output dictionary that should be generated given the above
    # 'CBECS_sh_ok' input sheet
    ok_out = {
        '2004 to 2007': 6524.0, '1960 to 1969': 10362.0,
        '1946 to 1959': 7381.0, '1970 to 1979': 10846.0,
        '1990 to 1999': 13803.0, '2000 to 2003': 7215.0,
        'Before 1920': 3980.0, '2008 to 2012': 5726.0,
        '1920 to 1945': 6020.0, '1980 to 1989': 15185.0}

    # Test for correct determination of CBECS square footages by
    # building vintage
    def test_vintageweights(self):
        # Define ok sample CBECS square footage file
        CBECS_in_test_ok = "CBECS_test_ok.xlsx"
        CBECS_ok = xlrd.open_workbook(CBECS_in_test_ok)
        CBECS_sh_ok = CBECS_ok.sheet_by_index(0)

        self.dict_check(import_eplus.CBECS_vintage_sf(
            CBECS_sh_ok), self.ok_out)

    # Test that an error is raised when none of the CBECS XLSX
    # rows are read in
    def test_vintageweights_fail(self):
        # Define fail sample CBECS square footage file
        CBECS_in_test_fail = "CBECS_test_fail.xlsx"
        CBECS_fail = xlrd.open_workbook(CBECS_in_test_fail)
        CBECS_sh_fail = CBECS_fail.sheet_by_index(0)

        with self.assertRaises(ValueError):
            import_eplus.CBECS_vintage_sf(
                CBECS_sh_fail)


# Skip this test if running on Travis-CI and print the given skip statement
@unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
                 'External File Dependency Unavailable on Travis-CI')
class FindVintageWeightsTest(unittest.TestCase, CommonMethods):
    """ Test 'find_vintage_weights' function to ensure the proper weights are
    derived for mapping EnergyPlus building vintages to Scout's 'new' and
    'retrofit' building structure types """

    # Sample dict mapping EnergyPlus vintage names to Scout 'new' and
    # 'retrofit' structure types
    structure_type = {
        "new": '90.1-2013',
        "retrofit": {
            '90.1-2004': [2004, 2006],
            '90.1-2007': [2007, 2009],
            '90.1-2010': [2010, 2012],
            'DOE Ref 1980-2004': [1980, 2003],
            'DOE Ref Pre-1980': [0, 1979]}}

    # Sample set of CBECS square footage data to map to EnergyPlus vintages
    sample_sf = {
        '2004 to 2007': 6524.0, '1960 to 1969': 10362.0,
        '1946 to 1959': 7381.0, '1970 to 1979': 10846.0,
        '1990 to 1999': 13803.0, '2000 to 2003': 7215.0,
        'Before 1920': 3980.0, '2008 to 2012': 5726.0,
        '1920 to 1945': 6020.0, '1980 to 1989': 15185.0}

    # Output dictionary that should be generated given the above sample square
    # footage data and 'eplus_vintages_ok' input sheet (see below)
    ok_out = {
        'DOE Ref 1980-2004': 0.42, '90.1-2004': 0.07,
        '90.1-2007': 0.0, '90.1-2010': 0.07,
        'DOE Ref Pre-1980': 0.44, '90.1-2013': 1}

    # Test for correct determination of vintage weights
    def test_vintageweights(self):
        # Define ok sample EnergyPlus data file
        eplus_perf_in_test_ok = "eplus_test_ok.xlsx"
        eplus_perf_ok = xlrd.open_workbook(eplus_perf_in_test_ok)
        eplus_perf_sh_ok = eplus_perf_ok.sheet_by_index(2)
        # Determine EnergyPlus vintage names from the above
        eplus_vintages_ok = []
        for x in range(1, eplus_perf_sh_ok.nrows):
            eplus_vintages_ok.append(eplus_perf_sh_ok.cell(x, 2).value)
        eplus_vintages_ok = numpy.unique(eplus_vintages_ok)

        self.dict_check(import_eplus.find_vintage_weights(
            self.sample_sf, eplus_vintages_ok,
            self.structure_type), self.ok_out)

    # Test that an error is raised when unexpected eplus vintages are present
    def test_vintageweights_fail(self):
        # Define fail sample EnergyPlus data file
        eplus_perf_in_test_fail = "eplus_test_fail.xlsx"
        eplus_perf_fail = xlrd.open_workbook(eplus_perf_in_test_fail)
        eplus_perf_sh_fail = eplus_perf_fail.sheet_by_index(2)
        # Determine EnergyPlus vintage names from the above
        eplus_vintages_fail = []
        for x in range(1, eplus_perf_sh_fail.nrows):
            eplus_vintages_fail.append(eplus_perf_sh_fail.cell(x, 2).value)
        eplus_vintages_fail = numpy.unique(eplus_vintages_fail)

        with self.assertRaises(KeyError):
            import_eplus.find_vintage_weights(
                self.sample_sf, eplus_vintages_fail, self.structure_type)


# Skip this test if running on Travis-CI and print the given skip statement
@unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
                 'External File Dependency Unavailable on Travis-CI')
class ConverttoArrayTest(unittest.TestCase, CommonMethods):
    """ Test 'convert_to_array' function to ensure it properly converts an
    input XLSX sheet to a structured array """

    # Define the structured array that should be yielded by using
    # 'convert_to_array' on a sample XLSX file with three rows
    # (imported in the function below)
    ok_out = numpy.array([
        ('BA-MixedHumid', 'QuickServiceRestaurant', 'DOE Ref 1980-2004',
         'Success', 0, 0.08826151, 0.08826151, 0.229505682, 0, -0.281087563,
         -0.281087563, 0, 0, 0, 0, 0, 0.087895769, 0, 0.371092043, 0.00295858,
         0, 0, 0, 0.005208793, 0, 0, 0, 0.277025257, 0, 0, 0, 0, 0, 0, 0, 0,
         0, 0, 0, 0, 0, 0, 0),
        ('BA-HotDry', 'SecondarySchool', 'DOE Ref Pre-1980', 'Success', 0,
         0.113925619, 0.113925619, 0.217474038, 0, -0.367260722, -0.367260722,
         0, 0, 0, 0, 0, 0.157089402, 0, 0.386383436, 0.005714286, 0, 0, 0,
         0.004321521, 0, 0, 0, 0.250674034, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
         0, 0, 0, 0)],
        dtype=[('Climate Zone', '<U13'), ('Building Type', '<U22'),
               ('Template', '<U17'), ('Status', 'U22'), ('Floor Area', '<f8'),
               ('Total Site Electricity', '<f8'),
               ('Net Site Electricity', '<f8'),
               ('Total Gas', '<f8'), ('Total Other Fuel', '<f8'),
               ('Total Water', '<f8'), ('Net Water', '<f8'),
               ('Interior Lighting Electricity', '<f8'),
               ('Exterior Lighting Electricity', '<f8'),
               ('Interior Equipment Electricity', '<f8'),
               ('Exterior Equipment Electricity', '<f8'),
               ('Heating Electricity', '<f8'),
               ('Cooling Electricity', '<f8'),
               ('Service Water Heating Electricity', '<f8'),
               ('Fan Electricity', '<f8'),
               ('Pump Electricity', '<f8'),
               ('Heat Recovery Electricity', '<f8'),
               ('Heat Rejection Electricity', '<f8'),
               ('Humidification Electricity', '<f8'),
               ('Refrigeration Electricity', '<f8'),
               ('Generated Electricity', '<f8'),
               ('Interior Equipment Gas', '<f8'),
               ('Exterior Equipment Gas', '<f8'),
               ('Heating Gas', '<f8'),
               ('Service Water Heating Gas', '<f8'),
               ('Interior Equipment Other Fuel', '<f8'),
               ('Exterior Equipment Other Fuel', '<f8'),
               ('Heating Other Fuel', '<f8'),
               ('Service Water Heating Other Fuel', '<f8'),
               ('District Hot Water Heating', '<f8'),
               ('District Hot Water Service Hot Water', '<f8'),
               ('District Chilled Water', '<f8'),
               ('Interior Equipment Water', '<f8'),
               ('Exterior Equipment Water', '<f8'),
               ('Service Water', '<f8'), ('Cooling Water', '<f8'),
               ('Heating Water', '<f8'), ('Humidifcation Water', '<f8'),
               ('Collected Water', '<f8')])

    # Test for correct conversion of an input Excel sheet to structured array
    def test_array_conversion(self):
        # Define reduced EnergyPlus data file (three rows including header)
        eplus_perf_in_test_ok = "eplus_test_ok_abbrev.xlsx"
        eplus_perf_ok = xlrd.open_workbook(eplus_perf_in_test_ok)
        eplus_perf_sh_ok = eplus_perf_ok.sheet_by_index(2)

        # Test for correct structured array output
        numpy.array_equal(import_eplus.convert_to_array(eplus_perf_sh_ok),
                          self.ok_out)


class CreatePerformanceDictTest(unittest.TestCase, CommonMethods):
    """ Test 'create_perf_dict' function to ensure it properly creates a
    nested dictionary to later be filled with EnergyPlus measure performance
    data """

    # Define a sample input dictionary containing baseline microsegment
    # information that will be used to check validity of candidate key chains
    # for the nested dictionary branches
    sample_input_mseg = {
        'hot dry': {
            'education': {
                'electricity (grid)': {
                    'lighting': {
                        "linear fluorescent (LED)": 0,
                        "general service (LED)": 0,
                        "external (LED)": 0},
                    'heating': {
                        'supply': {
                            'ASHP': 0},
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
                            'NGHP': 0},
                        'demand': {
                            'windows conduction': 0,
                            'windows solar': 0}},
                    'cooling': {
                        'supply': {
                            'NGHP': 0},
                        'demand': {
                            'windows conduction': 0,
                            'windows solar': 0}}}},
            'assembly': {
                'electricity (grid)': {
                    'lighting': {
                        "linear fluorescent (LED)": 0,
                        "general service (LED)": 0,
                        "external (LED)": 0},
                    'heating': {
                        'supply': {
                            'ASHP': 0},
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
                            'NGHP': 0},
                        'demand': {
                            'windows conduction': 0,
                            'windows solar': 0}},
                    'cooling': {
                        'supply': {
                            'NGHP': 0},
                        'demand': {
                            'windows conduction': 0,
                            'windows solar': 0}}}}},
        'mixed humid': {
            'education': {
                'electricity (grid)': {
                    'lighting': {
                        "linear fluorescent (LED)": 0,
                        "general service (LED)": 0,
                        "external (LED)": 0},
                    'heating': {
                        'supply': {
                            'ASHP': 0},
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
                            'NGHP': 0},
                        'demand': {
                            'windows conduction': 0,
                            'windows solar': 0}},
                    'cooling': {
                        'supply': {
                            'NGHP': 0},
                        'demand': {
                            'windows conduction': 0,
                            'windows solar': 0}}}},
            'assembly': {
                'electricity (grid)': {
                    'lighting': {
                        "linear fluorescent (LED)": 0,
                        "general service (LED)": 0,
                        "external (LED)": 0},
                    'heating': {
                        'supply': {
                            'ASHP': 0},
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
                            'NGHP': 0},
                        'demand': {
                            'windows conduction': 0,
                            'windows solar': 0}},
                    'cooling': {
                        'supply': {
                            'NGHP': 0},
                        'demand': {
                            'windows conduction': 0,
                            'windows solar': 0}}}}}}

    # Define a sample measure to initialize a performance dictionary for
    sample_eplus_measure = {
        "name": "EPlus sample measure 1",
        "installed_cost": 25,
        "cost_units": "2014$/unit",
        "energy_efficiency": {
            "EnergyPlus file": "sample EnergyPlus file name"},
        "energy_efficiency_units": {
            "primary": "relative savings (constant)",
            "secondary":
                "relative savings (constant)"},
        "market_entry_year": None,
        "market_exit_year": None,
        "product_lifetime": 10,
        "structure_type": ["new", "retrofit"],
        "bldg_type": ["assembly", "education"],
        "climate_zone": ["hot dry", "mixed humid"],
        "fuel_type": {
            "primary": ["electricity (grid)"],
            "secondary": [
                "electricity (grid)", "natural gas", "other fuel"]},
        "fuel_switch_to": None,
        "end_use": {
            "primary": ["lighting"],
            "secondary": ["heating", "cooling"]},
        "technology_type": {
            "primary": "supply",
            "secondary": "demand"},
        "technology": {
            "primary": ["linear fluorescent (LED)", "general service (LED)",
                        "external (LED)"],
            "secondary": ["windows conduction", "windows solar"]}}

    # Define correct performance dictionary output for sample measure
    ok_out = {
        "primary": {
            'hot dry': {
                'education': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0, 'new': 0}}},
                'assembly': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0, 'new': 0}}}},
            'mixed humid': {
                'education': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0, 'new': 0}}},
                'assembly': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0, 'new': 0}}}}},
        "secondary": {
            'hot dry': {
                'education': {
                    'electricity (grid)': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}},
                    'natural gas': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}}},
                'assembly': {
                    'electricity (grid)': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}},
                    'natural gas': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}}}},
            'mixed humid': {
                'education': {
                    'electricity (grid)': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}},
                    'natural gas': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}}},
                'assembly': {
                    'electricity (grid)': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}},
                    'natural gas': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}}}}}}

    # Test for correct generation of measure performance dictionary
    def test_dict_creation(self):
        self.dict_check(
            import_eplus.create_perf_dict(
                self.sample_eplus_measure, self.sample_input_mseg),
            self.ok_out)


class FillPerformanceDictTest(unittest.TestCase, CommonMethods):
    """ Test 'fill_perf_dict' function to ensure it properly updates a
    dictionary with EnergyPlus measure performance data """

    # Define a valid zeroed-out measure performance dict input
    ok_perf_dict_empty = {
        "primary": {
            'hot dry': {
                'education': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0, 'new': 0}}}},
            'mixed humid': {
                'education': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0, 'new': 0}}}}},
        "secondary": {
            'hot dry': {
                'education': {
                    'electricity (grid)': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}}}},
            'mixed humid': {
                'education': {
                    'electricity (grid)': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}}}}}}

    # Define invalid zeroed-out measure performance dict input (includes an
    # invalid climate zone key)
    fail_perf_dict_empty = {
        "primary": {
            'blazing hot': {
                'education': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0, 'new': 0}}}},
            'mixed humid': {
                'education': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0, 'new': 0}}}}},
        "secondary": {
            'hot dry': {
                'education': {
                    'electricity (grid)': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}}}},
            'mixed humid': {
                'education': {
                    'electricity (grid)': {
                        'heating': {'retrofit': 0, 'new': 0},
                        'cooling': {'retrofit': 0, 'new': 0}}}}}}

    # Define valid EnergyPlus performance data array
    ok_EPlus_perf_array = numpy.array([
        ('BA-MixedHumid', 'PrimarySchool', 'DOE Ref 1980-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'PrimarySchool', '90.1-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'PrimarySchool', '90.1-2007', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'PrimarySchool', '90.1-2010', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'PrimarySchool', 'DOE Ref Pre-1980', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'PrimarySchool', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'SecondarySchool', 'DOE Ref 1980-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'SecondarySchool', '90.1-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'SecondarySchool', '90.1-2007', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'SecondarySchool', '90.1-2010', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'SecondarySchool', 'DOE Ref Pre-1980', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-MixedHumid', 'SecondarySchool', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', 'DOE Ref 1980-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', '90.1-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', '90.1-2007', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', '90.1-2010', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', 'DOE Ref Pre-1980', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', 'DOE Ref 1980-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', '90.1-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', '90.1-2007', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', '90.1-2010', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', 'DOE Ref Pre-1980', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-SubArctic', 'PrimarySchool', 'DOE Ref 1980-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-SubArctic', 'PrimarySchool', '90.1-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-SubArctic', 'PrimarySchool', '90.1-2007', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-SubArctic', 'PrimarySchool', '90.1-2010', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-SubArctic', 'PrimarySchool', 'DOE Ref Pre-1980', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-SubArctic', 'PrimarySchool', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SmallOffice', 'DOE Ref 1980-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SmallOffice', '90.1-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SmallOffice', '90.1-2007', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SmallOffice', '90.1-2010', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SmallOffice', 'DOE Ref Pre-1980', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SmallOffice', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2)],
        dtype=[('Climate Zone', '<U13'), ('Building Type', '<U22'),
               ('Template', '<U17'), ('Status', 'U7'), ('Floor Area', '<f8'),
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

    # Define invalid EnergyPlus performance data array (missing mixed/humid
    # climate zone for 'PrimarySchool' building type)
    fail_EPlus_perf_array = numpy.array([
        ('BA-MixedHumid', 'SecondarySchool', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', 'DOE Ref 1980-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', '90.1-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', '90.1-2007', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', '90.1-2010', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', 'DOE Ref Pre-1980', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'PrimarySchool', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', 'DOE Ref 1980-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', '90.1-2004', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', '90.1-2007', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', '90.1-2010', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', 'DOE Ref Pre-1980', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2),
        ('BA-HotDry', 'SecondarySchool', '90.1-2013', 'Success',
         0, 0.5, 0.5, 0.25, 0.25, 0.25, 0.25, 0.75, 0, -0.1, 0.1, 0.5, -0.2)],
        dtype=[('Climate Zone', '<U13'), ('Building Type', '<U22'),
               ('Template', '<U17'), ('Status', 'U7'), ('Floor Area', '<f8'),
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

    # Define valid initial building type weighting of 1
    ok_EPlus_bldg_type_weight = 1

    # Define valid building vintage weights
    ok_EPlus_bldg_vintage_weights = {
        'DOE Ref 1980-2004': 0.42, '90.1-2004': 0.07,
        '90.1-2007': 0.0, '90.1-2010': 0.07,
        'DOE Ref Pre-1980': 0.44, '90.1-2013': 1}

    # Define output dictionary that should be generated by the function
    # given the 'ok' inputs defined above
    ok_perf_dict_filled = {
        "primary": {
            'hot dry': {
                'education': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0.75, 'new': 0.75}}}},
            'mixed humid': {
                'education': {
                    'electricity (grid)': {
                        'lighting': {'retrofit': 0.75, 'new': 0.75}}}}},
        "secondary": {
            'hot dry': {
                'education': {
                    'electricity (grid)': {
                        'heating': {'retrofit': -0.3, 'new': -0.3},
                        'cooling': {'retrofit': -0.1, 'new': -0.1}}}},
            'mixed humid': {
                'education': {
                    'electricity (grid)': {
                        'heating': {'retrofit': -0.3, 'new': -0.3},
                        'cooling': {'retrofit': -0.1, 'new': -0.1}}}}}}

    # Test for correct updating of measure performance dictionary,
    # given 'ok' inputs defined above
    def test_dict_fill(self):
        self.dict_check(
            import_eplus.fill_perf_dict(
                self.ok_perf_dict_empty,
                self.ok_EPlus_perf_array, self.ok_EPlus_bldg_type_weight,
                self.ok_EPlus_bldg_vintage_weights),
            self.ok_perf_dict_filled)

    # Test for error generation, given 'fail' inputs defined above
    def test_dict_fill_fail(self):
        # Ensure that an empty performance dict input with improper key
        # generates a KeyError
        with self.assertRaises(KeyError):
            import_eplus.fill_perf_dict(
                self.fail_perf_dict_empty,
                self.ok_EPlus_perf_array, self.ok_EPlus_bldg_type_weight,
                self.ok_EPlus_bldg_vintage_weights)
        # Ensure that an EnergyPlus array that is missing climate zone
        # information generates a ValueError
        with self.assertRaises(ValueError):
            import_eplus.fill_perf_dict(
                self.ok_perf_dict_empty,
                self.fail_EPlus_perf_array, self.ok_EPlus_bldg_type_weight,
                self.ok_EPlus_bldg_vintage_weights)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == "__main__":
    main()
