#!/usr/bin/env python3

# Import code to be tested
import mseg_meta as mm

# Import needed packages
import unittest
import numpy as np


class YearRangeExtractionFromStructuredArraysTest(unittest.TestCase):
    """ Tests for the function that takes numpy structured arrays of
    data from the AEO and extracts the minimum and maximum calendar
    years that appear in those data. """

    # Define example data subsets that test the cases handled by the
    # function under test, where either one or two columns of year data
    # are provided. The arrays given contain: commercial energy, stock,
    # and square footage data; residential non-lighting cost and
    # performance data
    aeo_structured_arrays = [
        np.array([(9, 10, 1, 2, 30,  1.503, 'EndUseConsump'),
                  (9, 10, 1, 2, 31,  1.499, 'EndUseConsump'),
                  (9, 10, 1, 2, 32,  1.493, 'EndUseConsump'),
                  (1,  5, 2, 1, 30,  0.083, 'EndUseConsump'),
                  (1,  5, 2, 1, 31,  0.081, 'EndUseConsump'),
                  (1,  5, 2, 1, 32,  0.078, 'EndUseConsump'),
                  (4,  6, 3, 1, 30,  0.101, 'MiscElConsump'),
                  (4,  6, 3, 1, 31,  0.103, 'MiscElConsump'),
                  (4,  6, 3, 1, 32,  0.106, 'MiscElConsump'),
                  (5,  4, 7, 1, 30,  1.475, 'MiscElConsump'),
                  (5,  4, 7, 1, 31,  1.484, 'MiscElConsump'),
                  (5,  4, 7, 1, 32,  1.492, 'MiscElConsump'),
                  (2,  1, 2, 1, 30,  2.430, 'EndUseConsump'),
                  (2,  1, 2, 1, 31,  2.399, 'EndUseConsump'),
                  (2,  1, 2, 1, 32,  2.360, 'EndUseConsump'),
                  (8,  2, 3, 2, 30,  9.430, 'EndUseConsump'),
                  (8,  2, 3, 2, 31,  9.373, 'EndUseConsump'),
                  (8,  2, 3, 2, 32,  9.311, 'EndUseConsump'),
                  (4,  7, 6, 1, 30,  3.641, 'EndUseConsump'),
                  (4,  7, 6, 1, 31,  3.647, 'EndUseConsump'),
                  (4,  7, 6, 1, 32,  3.654, 'EndUseConsump'),
                  (3,  7, 9, 1, 30, 11.983, 'EndUseConsump'),
                  (3,  7, 9, 1, 31, 12.165, 'EndUseConsump'),
                  (3,  7, 9, 1, 32, 12.377, 'EndUseConsump'),
                  (7,  4, 5, 2, 30, 24.763, 'EndUseConsump'),
                  (7,  4, 5, 2, 31, 24.724, 'EndUseConsump'),
                  (7,  4, 5, 2, 32, 24.733, 'EndUseConsump'),
                  (6,  3, 0, 0, 30,  2.097, 'CMNewFloorSpace'),
                  (6,  3, 0, 0, 31,  2.074, 'CMNewFloorSpace'),
                  (6,  3, 0, 0, 32,  2.037, 'CMNewFloorSpace'),
                  (9,  9, 0, 0, 30, 64.832, 'CMNewFloorSpace'),
                  (9,  9, 0, 0, 31, 61.281, 'CMNewFloorSpace'),
                  (9,  9, 0, 0, 32, 62.020, 'CMNewFloorSpace'),
                  (9,  9, 0, 0, 30, 2484.2, 'SurvFloorTotal'),
                  (9,  9, 0, 0, 31, 2515.2, 'SurvFloorTotal'),
                  (9,  9, 0, 0, 32, 2542.1, 'SurvFloorTotal')],
                 dtype=[('Division', 'i4'), ('BldgType', 'i4'),
                        ('EndUse', 'i4'), ('Fuel', 'i4'), ('Year', 'i4'),
                        ('Amount', 'f8'), ('Label', '<U50')]),
        np.array([(1, 2005, 2040, 3, 4.5, 3000, 2, 3, b"ELEC_RAD"),
                  (1, 2010, 2011, 1, 2.65, 1200, 1, 2, b"ELEC_HP1"),
                  (1, 2011, 2012, 1, 3.1, 1250, 1, 2, b"ELEC_HP1"),
                  (1, 2012, 2014, 1, 4.5, 1450, 1, 2, b"ELEC_HP1"),
                  (1, 2014, 2040, 1, 5, 2000, 1, 2, b"ELEC_HP1"),
                  (1, 2010, 2011, 2, 3.65, 1200, 5, 6, b"ELEC_HP1"),
                  (1, 2011, 2012, 2, 4.1, 1250, 5, 6, b"ELEC_HP1"),
                  (1, 2012, 2014, 2, 5.5, 1450, 5, 6, b"ELEC_HP1"),
                  (1, 2014, 2040, 2, 6, 2000, 5, 6, b"ELEC_HP1"),
                  (1, 2014, 2040, 2, 5, 2000, 5, 6, b"ELEC_HP1"),
                  (2, 2010, 2013, 3, 4.65, 1400, 3, 4, b"ELEC_HP1"),
                  (2, 2013, 2040, 3, 5.1, 1450, 3, 4, b"ELEC_HP1"),
                  (1, 2005, 2010, 1, 2.75, 1200, 1, 2, b"ELEC_HP2"),
                  (1, 2010, 2011, 1, 2.75, 1250, 1, 2, b"ELEC_HP2"),
                  (1, 2011, 2012, 1, 3.2, 1270, 1, 2, b"ELEC_HP2"),
                  (1, 2012, 2014, 1, 4.6, 1800, 1, 2, b"ELEC_HP2"),
                  (1, 2014, 2040, 1, 5.1, 1900, 1, 2, b"ELEC_HP2"),
                  (1, 2005, 2010, 1, 2.8, 1000, 1, 2, b"ELEC_HP4"),
                  (1, 2010, 2011, 1, 2.9, 1300, 1, 2, b"ELEC_HP4"),
                  (1, 2011, 2012, 1, 3.3, 1400, 1, 2, b"ELEC_HP4"),
                  (1, 2012, 2014, 1, 4.8, 1500, 1, 2, b"ELEC_HP4"),
                  (1, 2014, 2040, 1, 6, 2000, 1, 2, b"ELEC_HP4"),
                  (5, 2007, 2040, 4, 3, 1000, 7, 8, b"ELEC_WH1"),
                  (5, 2005, 2009, 4, 2.8, 1000, 7, 8, b"NG_WH#1"),
                  (5, 2009, 2040, 4, 2.9, 1300, 7, 8, b"NG_WH#1"),
                  (5, 2005, 2009, 4, 2.9, 1000, 7, 8, b"NG_WH#2"),
                  (5, 2009, 2040, 4, 3.2, 1300, 7, 8, b"NG_WH#2"),
                  (5, 2005, 2009, 4, 3.2, 2000, 7, 8, b"NG_WH#4"),
                  (5, 2009, 2040, 4, 3.5, 1500, 7, 8, b"NG_WH#4"),
                  (5, 2005, 2009, 5, 2.8, 1000, 7, 8, b"NG_WH#1"),
                  (5, 2009, 2040, 5, 2.9, 1300, 7, 8, b"NG_WH#1"),
                  (5, 2005, 2009, 5, 2.9, 1000, 7, 8, b"NG_WH#2"),
                  (5, 2009, 2040, 5, 3.2, 1300, 7, 8, b"NG_WH#2"),
                  (5, 2005, 2009, 5, 3.2, 2000, 7, 8, b"NG_WH#4"),
                  (5, 2009, 2040, 5, 3.5, 1500, 7, 8, b"NG_WH#4"),
                  (6, 2010, 2011, 2, 28, 100, 6, 7, b"ELEC_STV1"),
                  (6, 2012, 2040, 2, 29, 130, 6, 7, b"ELEC_STV1"),
                  (6, 2010, 2011, 2, 29, 150, 6, 7, b"NG_STV1"),
                  (6, 2012, 2040, 2, 32, 160, 6, 7, b"NG_STV1"),
                  (6, 2010, 2011, 2, 31, 200, 6, 7, b"NG_STV2"),
                  (6, 2012, 2040, 2, 33, 170, 6, 7, b"NG_STV2"),
                  (6, 2010, 2011, 2, 32, 200, 6, 7, b"LPG_STV2"),
                  (6, 2012, 2040, 2, 35, 175, 6, 7, b"LPG_STV2"),
                  (6, 2010, 2011, 2, 33, 300, 6, 7, b"ELEC_STV2"),
                  (6, 2012, 2040, 2, 36, 250, 6, 7, b"ELEC_STV2"),
                  (7, 2010, 2011, 2, 128, 1010, 0, 1, b"ELEC_DRY1"),
                  (7, 2012, 2040, 2, 129, 1310, 0, 1, b"ELEC_DRY1"),
                  (7, 2010, 2011, 2, 129, 1510, 0, 1, b"NG_DRY1"),
                  (7, 2012, 2040, 2, 132, 1610, 0, 1, b"NG_DRY1"),
                  (7, 2010, 2011, 2, 131, 2010, 0, 1, b"NG_DRY2"),
                  (7, 2012, 2040, 2, 133, 1710, 0, 1, b"NG_DRY2"),
                  (7, 2010, 2011, 2, 133, 3010, 0, 1, b"ELEC_DRY2"),
                  (7, 2012, 2040, 2, 136, 2510, 0, 1, b"ELEC_DRY2"),
                  (3, 2010, 2040, 3, 15, 150, 4, 5, b"CW#1"),
                  (3, 2010, 2040, 3, 12, 175, 4, 5, b"CW#2"),
                  (3, 2010, 2040, 3, 10, 300, 4, 5, b"CW#3"),
                  (8, 2005, 2009, 3, 200, 300, 6, 6, b"RefSF#1"),
                  (8, 2009, 2013, 3, 300, 250, 6, 6, b"RefSF#1"),
                  (8, 2013, 2040, 3, 400, 200, 6, 6, b"RefSF#1"),
                  (8, 2005, 2009, 3, 300, 400, 7, 7, b"RefBF#1"),
                  (8, 2009, 2013, 3, 400, 300, 7, 7, b"RefBF#1"),
                  (8, 2013, 2040, 3, 500, 200, 7, 7, b"RefBF#1"),
                  (8, 2005, 2009, 3, 500, 500, 8, 8, b"RefTF#1"),
                  (8, 2009, 2013, 3, 600, 400, 8, 8, b"RefTF#1"),
                  (8, 2013, 2040, 3, 700, 300, 8, 8, b"RefTF#1"),
                  (8, 2005, 2009, 3, 800, 800, 6, 6, b"RefSF#2"),
                  (8, 2009, 2013, 3, 900, 700, 6, 6, b"RefSF#2"),
                  (8, 2013, 2040, 3, 1000, 600, 6, 6, b"RefSF#2"),
                  (8, 2005, 2009, 3, 900, 200, 6, 6, b"RefBF#2"),
                  (8, 2009, 2013, 3, 1000, 100, 6, 6, b"RefBF#2"),
                  (8, 2013, 2040, 3, 1100, 50, 6, 6, b"RefBF#2"),
                  (8, 2005, 2009, 3, 900, 1400, 6, 6, b"RefTF#3"),
                  (8, 2009, 2013, 3, 950, 1200, 6, 6, b"RefTF#3"),
                  (8, 2013, 2040, 3, 1000, 1100, 6, 6, b"RefTF#3"),
                  (8, 2005, 2009, 3, 1500, 700, 6, 6, b"RefTF#2"),
                  (8, 2009, 2013, 3, 1600, 650, 6, 6, b"RefTF#2"),
                  (8, 2013, 2040, 3, 1700, 550, 6, 6, b"RefTF#2"),
                  (8, 2005, 2009, 1, 1500, 700, 6, 6, b"RefTF#2"),
                  (8, 2009, 2013, 1, 1600, 650, 6, 6, b"RefTF#2"),
                  (8, 2013, 2040, 1, 1700, 550, 6, 6, b"RefTF#2"),
                  (2, 2005, 2009, 4, 2.75, 500, 6, 6, b"NG_HP"),
                  (2, 2009, 2011, 4, 2.95, 550, 6, 6, b"NG_HP"),
                  (2, 2011, 2050, 4, 3.15, 575, 6, 6, b"NG_HP"),
                  (1, 2009, 2050, 3, 3.15, 575, 6, 6, b"NG_RAD")],
                 dtype=[("ENDUSE", "<i8"), ("START_EQUIP_YR", "<i8"),
                        ("END_EQUIP_YR", "<f8"), ("CDIV", "<i8"),
                        ("BASE_EFF", "<f8"), ("INST_COST", "<f8"),
                        ("EFF_CHOICE_P1", "<f8"), ("EFF_CHOICE_P2", "<f8"),
                        ("NAME", "S10")])]

    # Define list of lists of column names where year data are located
    # in each of the structured arrays to be tested
    column_names = [['Year'],
                    ['START_EQUIP_YR', 'END_EQUIP_YR']]

    # Define input lists of minimum and maximum years for the function tests
    # since the function is configured to read in a list (possibly empty) of
    # minimum and maximum years obtained from the data; these samples are
    # populated with dummy years
    min_yrs_input_list = [1990, 2009]
    max_yrs_input_list = [2052, 2040]

    # Specify the (optional) pivot year for testing purposes
    opt_pivot_year = [1989, 0]  # None]

    # Define expected minimum and maximum years for each of the
    # structured arrays tested (with separate lists for minimum and
    # maximum data)
    expected_min_years = [[1990, 2009, 2019], [1990, 2009, 2005]]
    expected_max_years = [[2052, 2040, 2021], [2052, 2040, 2050]]

    # Test the minimum and maximum year extraction function
    def test_comparative_year_extraction_from_structured_numpy_arrays(self):
        # Loop through the example structured arrays of AEO data
        for idx, struct_array in enumerate(self.aeo_structured_arrays):
            # Determine function call based on whether the optional
            # pivot year is specified for testing as "None", in which
            # case it should not be passed as an argument
            if not self.opt_pivot_year[idx]:
                min_out, max_out = mm.extract_year_range(
                    struct_array,
                    self.column_names[idx],
                    self.min_yrs_input_list,
                    self.max_yrs_input_list)
            else:
                min_out, max_out = mm.extract_year_range(
                    struct_array,
                    self.column_names[idx],
                    self.min_yrs_input_list,
                    self.max_yrs_input_list,
                    self.opt_pivot_year[idx])

            self.assertCountEqual(min_out, self.expected_min_years[idx])
            self.assertCountEqual(max_out, self.expected_max_years[idx])


class YearRangeExtractionFromArrayColumnHeadingsTest(unittest.TestCase):
    """ Test the function that extracts the maximum and minimum year
    from the dtype for a numpy structured array in the case where the
    data are recorded in columns for each year instead of having a row
    that corresponds to the calendar year for the data in each row """

    # Define a dtype in the format consistent with the service demand data
    example_dtype = [('r', '<i4'), ('b', '<i4'), ('s', '<i4'), ('f', '<i4'),
                     ('d', '<i4'), ('t', '<i4'), ('v', '<i4'), ('2004', '<f8'),
                     ('2005', '<f8'), ('2006', '<f8'), ('2007', '<f8'),
                     ('2008', '<f8'), ('2009', '<f8'), ('2010', '<f8'),
                     ('2011', '<f8'), ('2012', '<f8'), ('2013', '<f8'),
                     ('2014', '<f8'), ('2015', '<f8'), ('2016', '<f8'),
                     ('2017', '<f8'), ('2018', '<f8'), ('2019', '<f8'),
                     ('2020', '<f8'), ('Description', '<U50'), ('Eff', '<f8')]

    # Define input lists of minimum and maximum years for the function tests
    # since the function is configured to read in a list (possibly empty) of
    # minimum and maximum years obtained from the data; these samples are
    # populated with dummy years
    min_yrs_input_list = [1990, 2009]
    max_yrs_input_list = [2052, 2040]

    # Define expected minimum and maximum years for each of the
    # structured arrays tested (with separate lists for minimum and
    # maximum data)
    expected_min_years = [1990, 2009, 2004]
    expected_max_years = [2052, 2040, 2020]

    # Compare the output from the function under test to the expected result
    def test_year_min_max_extraction_from_dtype_function(self):
        min_out, max_out = mm.dtype_ripper(self.example_dtype,
                                           self.min_yrs_input_list,
                                           self.max_yrs_input_list)
        self.assertEqual(self.expected_min_years, min_out)
        self.assertEqual(self.expected_max_years, max_out)


# class EIADataFilenameIdentificationTest(unittest.TestCase):
#     """ TEMPORARY
#     """

#     # Define expected list of files output by the function
#     files_to_check = ['RESDBOUT.txt', 'rsmeqp.txt', 'rsmlgt.txt',
#                       'KSDOUT.txt', 'KDBOUT.txt',
#                       'ktek.csv', 'kprem.txt']

#     # Compare the expected list to the output of the function
#     def test_identification_of_EIA_input_files(self):
#         pass
#         # self.assertEqual(self.files_to_check, mm.EIA_filename_identifier())


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == "__main__":
    main()
