#!/usr/bin/env python3

""" Tests for running the EnergyPlus data import """

# Import code to be tested
import import_eplus
# Import needed packages
import unittest
import xlrd
import numpy

# Define ok sample CBECS square footage file
CBECS_in_test_ok = "CBECS_test_ok.xlsx"
CBECS_ok = xlrd.open_workbook(CBECS_in_test_ok)
CBECS_sh_ok = CBECS_ok.sheet_by_index(0)

# Define fail sample CBECS square footage file
CBECS_in_test_fail = "CBECS_test_fail.xlsx"
CBECS_fail = xlrd.open_workbook(CBECS_in_test_fail)
CBECS_sh_fail = CBECS_fail.sheet_by_index(0)

# Define ok sample EnergyPlus data file
EPlus_perf_in_test_ok = "EPlus_test_ok.xlsx"
EPlus_perf_ok = xlrd.open_workbook(EPlus_perf_in_test_ok)
EPlus_perf_sh_ok = EPlus_perf_ok.sheet_by_index(2)
# Determine EnergyPlus vintage names from the above
EPlus_vintages_ok = [EPlus_perf_sh_ok.cell(x, 2).value for
                     x in range(1, EPlus_perf_sh_ok.nrows)]
EPlus_vintages_ok = numpy.unique(EPlus_vintages_ok)

# Define fail sample EnergyPlus data file
EPlus_perf_in_test_fail = "EPlus_test_fail.xlsx"
EPlus_perf_fail = xlrd.open_workbook(EPlus_perf_in_test_fail)
EPlus_perf_sh_fail = EPlus_perf_fail.sheet_by_index(2)
# Determine EnergyPlus vintage names from the above
EPlus_vintages_fail = [EPlus_perf_sh_fail.cell(x, 2).value for
                       x in range(1, EPlus_perf_sh_fail.nrows)]
EPlus_vintages_fail = numpy.unique(EPlus_vintages_fail)


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
        self.dict_check(import_eplus.CBECS_vintage_sf(
            CBECS_sh_ok), self.ok_out)

    # Test that an error is raised when none of the CBECS XLSX
    # rows are read in
    def test_vintageweights_fail(self):
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

    # Sample set of CBECS square footage data to map to EnergyPlus vintages
    sample_sf = {
        '2004 to 2007': 6524.0, '1960 to 1969': 10362.0,
        '1946 to 1959': 7381.0, '1970 to 1979': 10846.0,
        '1990 to 1999': 13803.0, '2000 to 2003': 7215.0,
        'Before 1920': 3980.0, '2008 to 2012': 5726.0,
        '1920 to 1945': 6020.0, '1980 to 1989': 15185.0}

    # Output dictionary that should be generated given the above sample square
    # footage data and 'EPlus_vintages_ok' input sheet
    ok_out = {
        'DOE Ref 1980-2004': 0.42, '90.1-2004': 0.07,
        '90.1-2007': 0.0, '90.1-2010': 0.07,
        'DOE Ref Pre-1980': 0.44, '90.1-2013': 1}

    # Test for correct determination of vintage weights
    def test_vintageweights(self):
        self.dict_check(import_eplus.find_vintage_weights(
            self.sample_sf, EPlus_vintages_ok), self.ok_out)

    # Test that an error is raised when unexpected EPlus vintages are present
    def test_vintageweights_fail(self):
        with self.assertRaises(KeyError):
            import_eplus.find_vintage_weights(
                self.sample_sf, EPlus_vintages_fail)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == "__main__":
    main()
