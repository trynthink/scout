#!/usr/bin/env python3

""" Tests for commercial microsegment data processing code """

# Import code to be tested
import com_mseg as cm

# Import needed packages
import unittest
import numpy as np
import itertools
import os
import csv
import re


# Skip this test if running on Travis-CI and print the given skip statement
@unittest.skipIf("TRAVIS" in os.environ and os.environ["TRAVIS"] == "true",
                 'External File Dependency Unavailable on Travis-CI')
class EIADataFileIntegrityTest(unittest.TestCase):
    """ Test for the presence of the anticipated column headings in
    both the EIA general commercial buildings database and the EIA
    service demand database and report when any required columns are
    missing. Also test whether all of the years for which data are
    reported in both data files are the same. """

    def setUp(self):
        # Open each EIA data file, extract the header row, and reformat
        # the text in each entry for easier handling, producing a list
        # of strings for the column titles
        with open(cm.serv_dmd, 'r') as sd:
            sd_fl = csv.reader(sd)
            self.sd_head = [entry.strip() for entry in next(sd_fl)]

        with open(cm.catg_dmd, 'r') as db:
            db_fl = csv.reader(db)
            self.db_head = [entry.strip() for entry in next(db_fl)]

    # The function catg_data_selector expects certain columns to be
    # present in the commercial building data - this test checks for
    # the presence of those columns; column order does not matter but
    # the test is case-sensitive since the way the column headers are
    # used in the main code is case-sensitive
    def test_integrity_of_main_commercial_database(self):

        # Anticipated column headings in the commercial database
        col_heads = ['Division', 'BldgType', 'EndUse', 'Fuel', 'Year',
                     'Amount', 'Label']

        # Test for the presence of all of the anticipated column headings
        for head in col_heads:
            self.assertTrue(head in self.db_head, msg=head +
                            ' column not found.')

    # Check whether the years reported in the two EIA data files match
    # (This also tests, in a confounded way, whether the pivot year
    # applied to the commercial data years is still correct.)
    def test_years_in_both_commercial_energy_data_files(self):

        # Create a list of column names in the service demand data
        # that correspond to years (converting the years to integers)
        sd_yrs = [int(a) for a in self.sd_head if re.search('^2[0-9]{3}$', a)]

        # Determine which column has the year data
        loc = self.db_head.index('Year')

        years = []  # Initialize list for reported years

        # Read the first 100 data lines to (subsequently) create a
        # unique list of year numbers in the data
        with open(cm.catg_dmd, 'r') as db:
            db_fl = csv.reader(db)
            next(db_fl)  # Skip first line
            for row in itertools.islice(db_fl, 100):
                years.append(int(row[loc]))

        # Delete any entries that equal 0
        db_yrs = [a for a in years if a != 0]

        # Create a list of the unique years reported out of the first
        # 100 lines of the main commercial data file and adjust the
        # list based on the expected pivot year of 1989
        db_yrs = np.unique(db_yrs) + cm.pivot_year

        # Compare the contents of the two lists, where if the lists are
        # exactly the same, the list comprehension will be empty. Each
        # list comprehension only checks one list against the other, so
        # the comparison must be conducted both ways (as below).
        # N.B. db_yrs is a numpy array and sd_yrs is a list.
        cmpr = set(sd_yrs)
        diff_yrs1 = [a for a in db_yrs if a not in cmpr]

        cmpr = set(db_yrs)
        diff_yrs2 = [a for a in sd_yrs if a not in cmpr]

        diff_yrs = diff_yrs1 + diff_yrs2  # Combine the two lists together

        # Set up test that will fail if diff_yrs has any entries
        self.assertFalse(diff_yrs, msg=('The lists of years in the EIA '
                                        'general commercial data file '
                                        'and the service demand data '
                                        'file do not match.'))

    # The function sd_mseg_percent expects that the service demand data
    # will have certain columns that can be used to select the correct
    # data for further processing - this test checks for the presence
    # of those columns
    def test_integrity_of_commercial_service_demand_database(self):

        # Anticipated (non-year) columns in the service demand data
        col_heads = ['r', 'b', 's', 'f', 'd', 't', 'v', 'Description', 'Eff']

        # Check for the presence of each of the anticipated column headings
        for head in col_heads:
            self.assertTrue(head in self.sd_head, msg='Column ' + head +
                            (' is missing from the service demand data file.'))


class JSONInterpretationTest(unittest.TestCase):
    """ Test the conversion of lists of keys from the JSON database
    into lists that can be used to select data from the appropriate
    EIA or thermal loads (i.e., "demand") data record """

    # Set up a list of lists that would be recursively generated by the
    # walk function from the JSON database
    sample_keys = [['pacific', 'warehouse', 'natural gas',
                    'heating', 'demand', 'ground'],
                   ['new england', 'health care', 'electricity',
                    'cooling', 'demand', 'people gain'],
                   ['mid atlantic', 'assembly', 'electricity',
                    'cooling', 'supply'],
                   ['east north central', 'large office', 'electricity',
                    'lighting'],
                   ['west north central', 'lodging', 'electricity',
                    'MELs', 'elevators'],
                   ['south atlantic', 'food service', 'electricity',
                    'MELs', 'kitchen ventilation'],
                   ['mountain', 'education', 'natural gas',
                    'water heating']]

    # Define list outputs from the key conversion function
    sample_keys_converted = [[9, 10, 1, 2, 'GRND'],
                             [1, 5, 2, 1, 'PEOPLE'],
                             [2, 1, 2, 1],
                             [3, 7, 6, 1],
                             [4, 6, 10, 1, 3],
                             [5, 4, 10, 1, 7],
                             [8, 2, 3, 2]]

    # Define sample lists that either a) do not have keys in the
    # correct order to be converted (and should not appear in this
    # order in the JSON file) or b) include keys that are not
    # applicable to commercial buildings and should raise an error
    # or exception
    fail_keys = [['new england', 'mobile home', 'electricity',
                  'cooling', 'demand', 'people gain'],
                 ['west south central', 'single family home', 'natural gas',
                  'water heating'],
                 ['west north central', 'cooking', 'natural gas',
                  'drying'],
                 ['pacific', 'large office', 'security systems',
                  'distillate'],
                 ['neptune', 'education', 'distillate',
                  'heating', 'supply'],
                 ['mountain', 'small office', 'lamp oil',
                  'lighting']]

    # Test that the sample keys are correctly converted
    def test_key_conversion(self):
        for idx, a_key_list in enumerate(self.sample_keys):
            self.assertEqual(cm.json_interpreter(a_key_list),
                             self.sample_keys_converted[idx])

    # Test that the keys intended to fail all successfully raise the
    # expected KeyError
    def test_expected_failing_key_conversion(self):
        for a_key_list in self.fail_keys:
            with self.assertRaises(KeyError):
                cm.json_interpreter(a_key_list)


class PercentageCalculationTest(unittest.TestCase):
    """ Test function that converts service demand data from the EIA
    data file into percentages of the total reported energy use for the
    specified census division, building type, end use, and fuel type. """
    # Note that the service demand is only characterized for some end uses

    # Define lists that specify the census division, building type,
    # end use, and fuel type from which to select the desired data
    selection1 = [1, 3, 2, 1]  # New England, Food Sales, Cooling, Electricity
    selection2 = [4, 7, 6, 1]  # West North Central, Large Office, Lighting

    # Define a numpy array of sample service demand data, including a
    # limited number of year columns (compared to the actual service
    # demand data) for the sake of simplicity
    service_demand = np.array([
        (1, 3, 2, 1, 1, 13, 4, 0.28, 0.29, 0.37,
         'reciprocating_chiller 2013 mid-range', 4.4),
        (1, 3, 2, 1, 2, 13, 4, 0.0, 0.0, 0.01,
         'reciprocating_chiller 2013 mid-range', 4.4),
        (1, 3, 2, 1, 3, 13, 4, 0.02, 0.03, 0.04,
         'reciprocating_chiller 2013 mid-range', 4.4),
        (1, 3, 2, 1, 1, 52, 2, 0.18, 0.25, 0.27,
         'rooftop_AC 2012 installed base', 3.11),
        (1, 3, 2, 1, 2, 52, 2, 0.19, 0.19, 0.21,
         'rooftop_AC 2012 installed base', 3.11),
        (1, 3, 2, 1, 3, 52, 2, 0.0, 0.01, 0.01,
         'rooftop_AC 2012 installed base', 3.11),
        (1, 3, 2, 1, 1, 53, 5, 0.72, 0.15, 0.08,
         'wall-window_room_AC 2014 standard/ 2020 typi', 3.22),
        (1, 3, 2, 1, 2, 53, 5, 0.02, 0.05, 0.06,
         'wall-window_room_AC 2014 standard/ 2020 typi', 3.22),
        (1, 3, 2, 1, 3, 53, 5, 0.01, 0.03, 0.03,
         'wall-window_room_AC 2014 standard/ 2020 typi', 3.22),
        (1, 3, 2, 1, 1, 54, 1, 0.0, 0.0, 0.0,
         'res_type_gasHP-cool placeholder to reconcile', 0.01),
        (1, 3, 2, 1, 2, 54, 1, 0.0, 0.0, 0.0,
         'res_type_gasHP-cool placeholder to reconcile', 0.01),
        (1, 3, 2, 1, 3, 54, 1, 0.0, 0.0, 0.0,
         'res_type_gasHP-cool placeholder to reconcile', 0.01),
        (4, 7, 6, 1, 1, 24, 7, 0.0, 0.0, 0.0,
         '100W incand 2003 installed base', 10.0),
        (4, 7, 6, 1, 2, 24, 7, 1.28, 1.35, 1.36,
         '100W incand 2003 installed base', 10.0),
        (4, 7, 6, 1, 3, 24, 7, 1.23, 1.18, 1.15,
         '100W incand 2003 installed base', 10.0),
        (4, 7, 6, 1, 1, 24, 7, 0.27, 0.26, 0.24,
         '23W CFL 2011 typical', 42.4),
        (4, 7, 6, 1, 2, 24, 7, 0.93, 0.91, 0.88,
         '23W CFL 2011 typical', 42.4),
        (4, 7, 6, 1, 3, 24, 7, 0.15, 0.14, 0.13,
         '23W CFL 2011 typical', 42.4),
        (4, 7, 6, 1, 1, 24, 14, 0.39, 0.43, 0.47,
         '90W Halogen Edison 2030 typical', 21.36),
        (4, 7, 6, 1, 2, 24, 14, 0.27, 0.27, 0.26,
         '90W Halogen Edison 2030 typical', 21.36),
        (4, 7, 6, 1, 3, 24, 14, 0.18, 0.19, 0.21,
         '90W Halogen Edison 2030 typical', 21.36),
        (4, 7, 6, 1, 1, 25, 1, 0.0, 0.0, 0.0,
         'F34T12', 41.60),
        (4, 7, 6, 1, 2, 25, 1, 0.0, 0.0, 0.0,
         'F34T12', 41.60),
        (4, 7, 6, 1, 3, 25, 1, 0.0, 0.0, 0.0,
         'F34T12', 41.60),
        (4, 7, 6, 1, 1, 25, 7, 0.53, 0.55, 0.56,
         'F28T8 HE 2020 typical - 2012 stnd', 62.56),
        (4, 7, 6, 1, 2, 25, 7, 0.48, 0.43, 0.42,
         'F28T8 HE 2020 typical - 2012 stnd', 62.56),
        (4, 7, 6, 1, 3, 25, 7, 0.09, 0.13, 0.14,
         'F28T8 HE 2020 typical - 2012 stnd', 62.56)],
        dtype=[('r', '<i4'), ('b', '<i4'), ('s', '<i4'), ('f', '<i4'),
               ('d', '<i4'), ('t', '<i4'), ('v', '<i4'),
               ('2012', '<f8'), ('2013', '<f8'), ('2014', '<f8'),
               ('Description', '<U50'), ('Eff', '<f8')])
    # The columns specifying the census division, building type, etc.
    # in this sample array correctly match the description text, but
    # the data reported are fabricated and only for the purposes of
    # testing the calculations in the function (except the placeholder
    # lines, added to test the effective removal of those lines)

    # Define the anticipated outputs from the function based on the
    # inputs specified above (note that technology names, and thus the
    # percentages appear to end up in alphabetical order)
    selection1_technames = ['reciprocating_chiller',
                            'rooftop_AC',
                            'wall-window_room_AC']
    selection1_pct = np.array([[0.211267606, 0.32, 0.388888889],
                               [0.26056338, 0.45, 0.453703704],
                               [0.528169014, 0.23, 0.157407407]])

    selection2_technames = ['100W incand',
                            '23W CFL',
                            '90W Halogen Edison',
                            'F28T8 HE',
                            'F34T12']
    selection2_pct = np.array([[0.432758621, 0.433219178, 0.431271478],
                               [0.232758621, 0.224315068, 0.214776632],
                               [0.144827586, 0.15239726, 0.161512027],
                               [0.189655172, 0.190068493, 0.192439863],
                               [0.0, 0.0, 0.0]])

    # Run both example selections with the service demand reprocessing
    # function and save outputs for testing
    def setUp(self):
        (self.a, self.b) = cm.sd_mseg_percent(
            self.service_demand, self.selection1)
        (self.c, self.d) = cm.sd_mseg_percent(
            self.service_demand, self.selection2)

    # Test technology type name capture/identification
    def test_service_demand_name_identification(self):
        self.assertEqual(self.b, self.selection1_technames)
        self.assertEqual(self.d, self.selection2_technames)

    # Test energy percentage contribution calculation (correcting for
    # potential floating point precision problems)
    def test_service_demand_percentage_conversion(self):
        self.assertTrue(
            (np.round(self.a - self.selection1_pct, decimals=5) == 0).all())
        self.assertTrue(
            (np.round(self.c - self.selection2_pct, decimals=5) == 0).all())


class CommercialDataSelectionTest(unittest.TestCase):
    """ Test function that selects a subset of data from the combined
    commercial building energy and characteristics array and outputs
    that subset with the years adjusted based on the pivot year """

    # Define array with identical data format to EIA data file KDBOUT
    # but only a few years for each entry to reduce the total number
    # of rows
    sample_db_array = np.array([
        (9, 10, 1, 2, 30, 1.503, 'EndUseConsump'),
        (9, 10, 1, 2, 31, 1.499, 'EndUseConsump'),
        (9, 10, 1, 2, 32, 1.493, 'EndUseConsump'),
        (1,  5, 2, 1, 30, 0.083, 'EndUseConsump'),
        (1,  5, 2, 1, 31, 0.081, 'EndUseConsump'),
        (1,  5, 2, 1, 32, 0.078, 'EndUseConsump'),
        (2,  1, 2, 1, 30, 2.430, 'EndUseConsump'),
        (2,  1, 2, 1, 31, 2.399, 'EndUseConsump'),
        (2,  1, 2, 1, 32, 2.360, 'EndUseConsump'),
        (3, 7, 6, 1, 30, 27.667, 'EndUseConsump'),
        (3, 7, 6, 1, 31, 27.467, 'EndUseConsump'),
        (3, 7, 6, 1, 32, 27.289, 'EndUseConsump'),
        (4,  6, 3, 1, 30, 0.101, 'MiscElConsump'),
        (4,  6, 3, 1, 31, 0.103, 'MiscElConsump'),
        (4,  6, 3, 1, 32, 0.106, 'MiscElConsump'),
        (5,  4, 7, 1, 30, 1.475, 'MiscElConsump'),
        (5,  4, 7, 1, 31, 1.484, 'MiscElConsump'),
        (5,  4, 7, 1, 32, 1.492, 'MiscElConsump'),
        (8,  2, 3, 2, 30, 9.430, 'EndUseConsump'),
        (8,  2, 3, 2, 31, 9.373, 'EndUseConsump'),
        (8,  2, 3, 2, 32, 9.311, 'EndUseConsump')],
        dtype=[('Division', 'i4'), ('BldgType', 'i4'),
               ('EndUse', 'i4'), ('Fuel', 'i4'), ('Year', 'i4'),
               ('Amount', 'f8'), ('Label', '<U50')])

    # Define list of selection lists used to subset data
    # from the target array
    sample_sel = [[9, 10, 1, 2, 'GRND'],
                  [1, 5, 2, 1, 'PEOPLE'],
                  [2, 1, 2, 1],
                  [3, 7, 6, 1],
                  [4, 6, 3, 1, 3],  # MELs
                  [5, 4, 7, 1, 7],  # MELs
                  [8, 2, 3, 2]]

    # List of booleans indicating whether the selection comes from the
    # MELs rows in the array
    MEL_status = [False, False, False, False, True, True, False]

    # Define list of expected numpy structured arrays generated by
    # the function to be tested
    expected_selection = [np.array([('2019', 1.503),
                                    ('2020', 1.499),
                                    ('2021', 1.493)],
                                   dtype=[('Year', 'U4'), ('Amount', 'f8')]),
                          np.array([('2019', 0.083),
                                    ('2020', 0.081),
                                    ('2021', 0.078)],
                                   dtype=[('Year', 'U4'), ('Amount', 'f8')]),
                          np.array([('2019', 2.430),
                                    ('2020', 2.399),
                                    ('2021', 2.360)],
                                   dtype=[('Year', 'U4'), ('Amount', 'f8')]),
                          np.array([('2019', 27.667),
                                    ('2020', 27.467),
                                    ('2021', 27.289)],
                                   dtype=[('Year', 'U4'), ('Amount', 'f8')]),
                          np.array([('2019', 0.101),
                                    ('2020', 0.103),
                                    ('2021', 0.106)],
                                   dtype=[('Year', 'U4'), ('Amount', 'f8')]),
                          np.array([('2019', 1.475),
                                    ('2020', 1.484),
                                    ('2021', 1.492)],
                                   dtype=[('Year', 'U4'), ('Amount', 'f8')]),
                          np.array([('2019', 9.430),
                                    ('2020', 9.373),
                                    ('2021', 9.311)],
                                   dtype=[('Year', 'U4'), ('Amount', 'f8')])]

    # Test correct selection and conversion
    def test_data_selection_and_reduction(self):
        for idx, _ in enumerate(self.sample_sel):
            # Determine whether the target data are for MELs
            if self.MEL_status[idx]:
                correct_label_str = 'MiscElConsump'
            else:
                correct_label_str = 'EndUseConsump'

            self.assertCountEqual(
                cm.catg_data_selector(self.sample_db_array,
                                      self.sample_sel[idx],
                                      correct_label_str),
                self.expected_selection[idx])


class DataToFinalDictAtLeafNodeRestructuringTest(unittest.TestCase):
    """ Test function that handles selection of the appropriate data
    and any required restructuring or reprocessing to convert it into a
    dict formatted for insertion into the microsegments JSON """

    # Define a list of the end uses found in the service demand data
    sd_end_uses = [1, 2, 3, 4, 6, 7]

    # Define array with identical data format to EIA data file KDBOUT
    # but only a few years for each entry to reduce the total number
    # of rows
    sample_db_array = np.array([
        (9, 10, 1, 2, 30,  1.503, 'EndUseConsump'),
        (9, 10, 1, 2, 31,  1.499, 'EndUseConsump'),
        (9, 10, 1, 2, 32,  1.493, 'EndUseConsump'),
        (1,  5, 2, 1, 30,  0.083, 'EndUseConsump'),
        (1,  5, 2, 1, 31,  0.081, 'EndUseConsump'),
        (1,  5, 2, 1, 32,  0.078, 'EndUseConsump'),
        (2,  1, 2, 1, 30,  2.430, 'EndUseConsump'),
        (2,  1, 2, 1, 31,  2.399, 'EndUseConsump'),
        (2,  1, 2, 1, 32,  2.360, 'EndUseConsump'),
        (4,  6, 3, 1, 30,  0.101, 'MiscElConsump'),
        (4,  6, 3, 1, 31,  0.103, 'MiscElConsump'),
        (4,  6, 3, 1, 32,  0.106, 'MiscElConsump'),
        (5,  4, 7, 1, 30,  1.475, 'MiscElConsump'),
        (5,  4, 7, 1, 31,  1.484, 'MiscElConsump'),
        (5,  4, 7, 1, 32,  1.492, 'MiscElConsump'),
        (8,  2, 3, 2, 30,  9.430, 'EndUseConsump'),
        (8,  2, 3, 2, 31,  9.373, 'EndUseConsump'),
        (8,  2, 3, 2, 32,  9.311, 'EndUseConsump'),
        (3,  7, 9, 1, 30, 11.983, 'EndUseConsump'),
        (3,  7, 9, 1, 31, 12.165, 'EndUseConsump'),
        (3,  7, 9, 1, 32, 12.377, 'EndUseConsump'),
        (7,  4, 5, 2, 30, 24.763, 'EndUseConsump'),
        (7,  4, 5, 2, 31, 24.724, 'EndUseConsump'),
        (7,  4, 5, 2, 32, 24.733, 'EndUseConsump')],
        dtype=[('Division', 'i4'), ('BldgType', 'i4'),
               ('EndUse', 'i4'), ('Fuel', 'i4'), ('Year', 'i4'),
               ('Amount', 'f8'), ('Label', '<U50')])

    # Define array with identical data format to EIA service demand
    # data that provides the relevant supporting data for the cases
    # being tested that involve service demand data; note that for the
    # two sample cases tested, not all of the data were captured from
    # the service demand data in the interest of brevity and test speed
    sample_sd_array = np.array([
        (2, 1, 2, 1, 1, 6, 1, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2003 installed base', 2.73),
        (2, 1, 2, 1, 2, 6, 1, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2003 installed base', 2.73),
        (2, 1, 2, 1, 3, 6, 1, 0.013, 0.012, 0.011,
         'rooftop_ASHP-cool 2003 installed base', 2.73),
        (2, 1, 2, 1, 1, 6, 2, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2012 installed base', 2.99),
        (2, 1, 2, 1, 2, 6, 2, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2012 installed base', 2.99),
        (2, 1, 2, 1, 3, 6, 2, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2012 installed base', 2.99),
        (2, 1, 2, 1, 1, 6, 3, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2013 current standard/ typ', 3.22),
        (2, 1, 2, 1, 2, 6, 3, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2013 current standard/ typ', 3.22),
        (2, 1, 2, 1, 3, 6, 3, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2013 current standard/ typ', 3.22),
        (2, 1, 2, 1, 1, 6, 4, 0.001, 0.0, 0.0,
         'rooftop_ASHP-cool 2013 ENERGY STAR', 3.31),
        (2, 1, 2, 1, 2, 6, 4, 0.007, 0.0, 0.0,
         'rooftop_ASHP-cool 2013 ENERGY STAR', 3.31),
        (2, 1, 2, 1, 3, 6, 4, 0.067, 0.069, 0.064,
         'rooftop_ASHP-cool 2013 ENERGY STAR', 3.31),
        (2, 1, 2, 1, 1, 6, 5, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2013 high', 3.52),
        (2, 1, 2, 1, 2, 6, 5, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2013 high', 3.52),
        (2, 1, 2, 1, 3, 6, 5, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2013 high', 3.52),
        (2, 1, 2, 1, 1, 6, 6, 0.0, 0.001, 0.001,
         'rooftop_ASHP-cool 2020 typical', 3.22),
        (2, 1, 2, 1, 2, 6, 6, 0.0, 0.007, 0.007,
         'rooftop_ASHP-cool 2020 typical', 3.22),
        (2, 1, 2, 1, 3, 6, 6, 0.0, 0.0, 0.007,
         'rooftop_ASHP-cool 2020 typical', 3.22),
        (2, 1, 2, 1, 1, 6, 7, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2020 high', 3.52),
        (2, 1, 2, 1, 2, 6, 7, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2020 high', 3.52),
        (2, 1, 2, 1, 3, 6, 7, 0.0, 0.0, 0.0,
         'rooftop_ASHP-cool 2020 high', 3.52),
        (2, 1, 2, 1, 1, 7, 1, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2003 installed base', 4.04),
        (2, 1, 2, 1, 2, 7, 1, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2003 installed base', 4.04),
        (2, 1, 2, 1, 3, 7, 1, 0.009, 0.009, 0.008,
         'comm_GSHP-cool 2003 installed base', 4.04),
        (2, 1, 2, 1, 1, 7, 2, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2012 installed base', 4.1),
        (2, 1, 2, 1, 2, 7, 2, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2012 installed base', 4.1),
        (2, 1, 2, 1, 3, 7, 2, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2012 installed base', 4.1),
        (2, 1, 2, 1, 1, 7, 3, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 typical', 5.01),
        (2, 1, 2, 1, 2, 7, 3, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 typical', 5.01),
        (2, 1, 2, 1, 3, 7, 3, 0.002, 0.002, 0.002,
         'comm_GSHP-cool 2013 typical', 5.01),
        (2, 1, 2, 1, 1, 7, 4, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 mid', 5.16),
        (2, 1, 2, 1, 2, 7, 4, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 mid', 5.16),
        (2, 1, 2, 1, 3, 7, 4, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 mid', 5.16),
        (2, 1, 2, 1, 1, 7, 5, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 high', 6.04),
        (2, 1, 2, 1, 2, 7, 5, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 high', 6.04),
        (2, 1, 2, 1, 3, 7, 5, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 high', 6.04),
        (2, 1, 2, 1, 1, 7, 6, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2020 typical', 5.28),
        (2, 1, 2, 1, 2, 7, 6, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2020 typical', 5.28),
        (2, 1, 2, 1, 3, 7, 6, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2020 typical', 5.28),
        (2, 1, 2, 1, 1, 7, 7, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2020 high', 6.45),
        (2, 1, 2, 1, 2, 7, 7, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2020 high', 6.45),
        (2, 1, 2, 1, 3, 7, 7, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2020 high', 6.45),
        (2, 1, 2, 1, 1, 7, 8, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2030 typical', 5.86),
        (2, 1, 2, 1, 2, 7, 8, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2030 typical', 5.86),
        (2, 1, 2, 1, 3, 7, 8, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2030 typical', 5.86),
        (2, 1, 2, 1, 1, 7, 9, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2030 high', 7.03),
        (2, 1, 2, 1, 2, 7, 9, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2030 high', 7.03),
        (2, 1, 2, 1, 3, 7, 9, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2030 high', 7.03),
        (2, 1, 2, 1, 1, 7, 10, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 typ 10% ITC w MACRS', 5.01),
        (2, 1, 2, 1, 2, 7, 10, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 typ 10% ITC w MACRS', 5.01),
        (2, 1, 2, 1, 3, 7, 10, 0.003, 0.002, 0.002,
         'comm_GSHP-cool 2013 typ 10% ITC w MACRS', 5.01),
        (2, 1, 2, 1, 1, 7, 11, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 mid 10% ITC w MACRS', 5.16),
        (2, 1, 2, 1, 2, 7, 11, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 mid 10% ITC w MACRS', 5.16),
        (2, 1, 2, 1, 3, 7, 11, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 mid 10% ITC w MACRS', 5.16),
        (2, 1, 2, 1, 1, 7, 12, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 high 10% ITC w MACRS', 6.04),
        (2, 1, 2, 1, 2, 7, 12, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 high 10% ITC w MACRS', 6.04),
        (2, 1, 2, 1, 3, 7, 12, 0.0, 0.0, 0.0,
         'comm_GSHP-cool 2013 high 10% ITC w MACRS', 6.04),
        (2, 1, 2, 1, 1, 54, 1, 0.0, 0.0, 0.0,
         'res_type_central_AC 2003 installed base', 3.34),
        (2, 1, 2, 1, 2, 54, 1, 0.0, 0.0, 0.0,
         'res_type_central_AC 2003 installed base', 3.34),
        (2, 1, 2, 1, 3, 54, 1, 0.645, 0.595, 0.549,
         'res_type_central_AC 2003 installed base', 3.34),
        (2, 1, 2, 1, 1, 54, 2, 0.004, 0.004, 0.004,
         'res_type_central_AC 2013 current standard', 3.81),
        (2, 1, 2, 1, 2, 54, 2, 0.082, 0.08, 0.079,
         'res_type_central_AC 2013 current standard', 3.81),
        (2, 1, 2, 1, 3, 54, 2, 0.831, 0.847, 0.86,
         'res_type_central_AC 2013 current standard', 3.81),
        (2, 1, 2, 1, 1, 54, 3, 0.0, 0.0, 0.0,
         'res_type_central_AC 2013 typical', 3.81),
        (2, 1, 2, 1, 2, 54, 3, 0.0, 0.0, 0.0,
         'res_type_central_AC 2013 typical', 3.81),
        (2, 1, 2, 1, 3, 54, 3, 0.0, 0.0, 0.0,
         'res_type_central_AC 2013 typical', 3.81),
        (2, 1, 2, 1, 1, 54, 4, 0.0, 0.0, 0.0,
         'res_type_central_AC 2013 ENERGY STAR', 4.25),
        (2, 1, 2, 1, 2, 54, 4, 0.0, 0.0, 0.0,
         'res_type_central_AC 2013 ENERGY STAR', 4.25),
        (2, 1, 2, 1, 3, 54, 4, 0.013, 0.012, 0.012,
         'res_type_central_AC 2013 ENERGY STAR', 4.25),
        (2, 1, 2, 1, 1, 54, 5, 0.0, 0.0, 0.0,
         'res_type_central_AC 2013 high', 7.03),
        (2, 1, 2, 1, 2, 54, 5, 0.0, 0.0, 0.0,
         'res_type_central_AC 2013 high', 7.03),
        (2, 1, 2, 1, 3, 54, 5, 0.0, 0.0, 0.0,
         'res_type_central_AC 2013 high', 7.03),
        (2, 1, 2, 1, 1, 54, 6, 0.0, 0.0, 0.0,
         'res_type_central_AC 2020 typical', 4.1),
        (2, 1, 2, 1, 2, 54, 6, 0.011, 0.011, 0.011,
         'res_type_central_AC 2020 typical', 4.1),
        (2, 1, 2, 1, 3, 54, 6, 0.105, 0.108, 0.11,
         'res_type_central_AC 2020 typical', 4.1),
        (2, 1, 2, 1, 1, 54, 7, 0.0, 0.0, 0.0,
         'res_type_central_AC 2020 high', 7.03),
        (2, 1, 2, 1, 2, 54, 7, 0.0, 0.0, 0.0,
         'res_type_central_AC 2020 high', 7.03),
        (2, 1, 2, 1, 3, 54, 7, 0.0, 0.0, 0.0,
         'res_type_central_AC 2020 high', 7.03),
        (2, 1, 2, 1, 1, 54, 8, 0.0, 0.0, 0.0,
         'res_type_central_AC 2030 typical', 4.1),
        (2, 1, 2, 1, 2, 54, 8, 0.0, 0.0, 0.0,
         'res_type_central_AC 2030 typical', 4.1),
        (2, 1, 2, 1, 3, 54, 8, 0.0, 0.0, 0.0,
         'res_type_central_AC 2030 typical', 4.1),
        (8, 2, 3, 2, 1, 22, 1, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2003 installed base', 0.76),
        (8, 2, 3, 2, 2, 22, 1, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2003 installed base', 0.76),
        (8, 2, 3, 2, 3, 22, 1, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2003 installed base', 0.76),
        (8, 2, 3, 2, 1, 22, 2, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2012 installed base', 0.78),
        (8, 2, 3, 2, 2, 22, 2, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2012 installed base', 0.78),
        (8, 2, 3, 2, 3, 22, 2, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2012 installed base', 0.78),
        (8, 2, 3, 2, 1, 22, 3, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 current standard', 0.8),
        (8, 2, 3, 2, 2, 22, 3, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 current standard', 0.8),
        (8, 2, 3, 2, 3, 22, 3, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 current standard', 0.8),
        (8, 2, 3, 2, 1, 22, 4, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 typical', 0.89),
        (8, 2, 3, 2, 2, 22, 4, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 typical', 0.89),
        (8, 2, 3, 2, 3, 22, 4, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 typical', 0.89),
        (8, 2, 3, 2, 1, 22, 5, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 high', 0.97),
        (8, 2, 3, 2, 2, 22, 5, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 high', 0.97),
        (8, 2, 3, 2, 3, 22, 5, 0.0, 0.0, 0.0,
         'gas_instantaneous_WH 2013 high', 0.97),
        (8, 2, 3, 2, 1, 57, 1, 0.0, 0.0, 0.0,
         'gas_water_heater 2003 installed base', 0.77),
        (8, 2, 3, 2, 2, 57, 1, 0.0, 0.0, 0.0,
         'gas_water_heater 2003 installed base', 0.77),
        (8, 2, 3, 2, 3, 57, 1, 0.624, 0.57, 0.521,
         'gas_water_heater 2003 installed base', 0.77),
        (8, 2, 3, 2, 1, 57, 2, 0.038, 0.037, 0.035,
         'gas_water_heater 2013 current standard/ typi', 0.8),
        (8, 2, 3, 2, 2, 57, 2, 0.151, 0.153, 0.155,
         'gas_water_heater 2013 current standard/ typi', 0.8),
        (8, 2, 3, 2, 3, 57, 2, 2.046, 2.043, 2.04,
         'gas_water_heater 2013 current standard/ typi', 0.8),
        (8, 2, 3, 2, 1, 57, 3, 0.036, 0.035, 0.034,
         'gas_water_heater 2013 high', 0.99),
        (8, 2, 3, 2, 2, 57, 3, 0.144, 0.146, 0.147,
         'gas_water_heater 2013 high', 0.99),
        (8, 2, 3, 2, 3, 57, 3, 0.806, 0.905, 0.995,
         'gas_water_heater 2013 high', 0.99),
        (8, 2, 3, 2, 1, 57, 4, 0.0, 0.0, 0.0,
         'gas_water_heater 2020 typical', 0.8),
        (8, 2, 3, 2, 2, 57, 4, 0.0, 0.0, 0.0,
         'gas_water_heater 2020 typical', 0.8),
        (8, 2, 3, 2, 3, 57, 4, 0.0, 0.0, 0.0,
         'gas_water_heater 2020 typical', 0.8),
        (8, 2, 3, 2, 1, 57, 5, 0.0, 0.0, 0.0,
         'gas_water_heater 2020 high', 0.99),
        (8, 2, 3, 2, 2, 57, 5, 0.0, 0.0, 0.0,
         'gas_water_heater 2020 high', 0.99),
        (8, 2, 3, 2, 3, 57, 5, 0.0, 0.0, 0.0,
         'gas_water_heater 2020 high', 0.99)],
        dtype=[('r', '<i4'), ('b', '<i4'), ('s', '<i4'), ('f', '<i4'),
               ('d', '<i4'), ('t', '<i4'), ('v', '<i4'),
               ('2019', '<f8'), ('2020', '<f8'), ('2021', '<f8'),
               ('Description', '<U50'), ('Eff', '<f8')])

    # Define array similar to the thermal loads data, but with only the
    # data required to test the sample cases explored here (plus an
    # extra that can be added later, if desired)
    sample_tl_array = np.array([
        ('HT', 9, 10, -0.2964, -0.069, 1.0994),
        ('CL', 1, 5, 0.1338, 0.084, 0.0),
        ('CL', 2, 1, 0.448, 0.0956, -0.0427)],
        dtype=[('ENDUSE', '<U50'), ('CDIV', '<i4'), ('BLDG', '<i4'),
               ('WIND_SOL', '<f8'), ('PEOPLE', '<f8'), ('GRND', '<f8')])

    # Set up a list of lists that would be recursively generated by the
    # walk function from the JSON database
    sample_keys = [['pacific', 'warehouse', 'natural gas',
                    'heating', 'demand', 'ground'],
                   ['new england', 'health care', 'electricity',
                    'cooling', 'demand', 'people gain'],
                   ['west north central', 'lodging', 'electricity',
                    'MELs', 'elevators'],
                   ['south atlantic', 'food service', 'electricity',
                    'MELs', 'kitchen ventilation'],
                   ['mid atlantic', 'assembly', 'electricity',
                    'cooling', 'supply'],
                   ['mountain', 'education', 'natural gas',
                    'water heating'],
                   ['east north central', 'large office', 'electricity',
                    'non-PC office equipment'],
                   ['west south central', 'food sales', 'natural gas',
                    'cooking']]

    # For reference: keys converted to numbers
    # [9, 10, 1, 2, 'GRND'] - DEMAND
    # [1, 5, 2, 1, 'PEOPLE'] - DEMAND
    # [4, 6, 10, 1, 3] - MEL
    # [5, 4, 10, 1, 7] - MEL
    # [2, 1, 2, 1] - SD
    # [8, 2, 3, 2] - SD
    # [3, 7, 9, 1]
    # [7, 4, 5, 2]

    # Final dicts in the form that should be produced by the function
    # under test, in the same order as the sample_keys list
    dict_list = [
        {'2019': 1.6523982, '2020': 1.6480006, '2021': 1.6414042},
        {'2019': 0.006972, '2020': 0.006804, '2021': 0.006552},
        {'2019': 0.101, '2020': 0.103, '2021': 0.106},
        {'2019': 1.475, '2020': 1.484, '2021': 1.492},
        {'rooftop_ASHP-cool':
            {'2019': 0.1192638, '2020': 0.12138204, '2021': 0.12298784},
         'comm_GSHP-cool':
            {'2019': 0.01897379, '2020': 0.01772996, '2021': 0.01639838},
         'res_type_central_AC':
            {'2019': 2.29176241, '2020': 2.259888, '2021': 2.22061378}},
        {'gas_instantaneous_WH': {'2019': 0, '2020': 0, '2021': 0},
         'gas_water_heater': {'2019': 9.430, '2020': 9.373, '2021': 9.311}},
        {'2019': 11.983, '2020': 12.165, '2021': 12.377},
        {'2019': 24.763, '2020': 24.724, '2021': 24.733}]

    # Create a routine for checking equality of a dict with point values
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test each if/else data condition in the energy_select function separately
    def test_restructuring_cases_with_thermal_loads(self):
        for i in [0, 1]:
            self.dict_check(cm.energy_select(self.sample_db_array,
                                             self.sample_sd_array,
                                             self.sample_tl_array,
                                             self.sample_keys[i],
                                             self.sd_end_uses),
                            self.dict_list[i])

    def test_restructuring_cases_with_miscellaneous_electric_loads(self):
        for i in [2, 3]:
            self.dict_check(cm.energy_select(self.sample_db_array,
                                             self.sample_sd_array,
                                             self.sample_tl_array,
                                             self.sample_keys[i],
                                             self.sd_end_uses),
                            self.dict_list[i])

    def test_restructuring_cases_with_service_demand_data(self):
        for i in [4, 5]:
            self.dict_check(cm.energy_select(self.sample_db_array,
                                             self.sample_sd_array,
                                             self.sample_tl_array,
                                             self.sample_keys[i],
                                             self.sd_end_uses),
                            self.dict_list[i])

    def test_restructuring_all_other_cases(self):
        for i in [6, 7]:
            self.dict_check(cm.energy_select(self.sample_db_array,
                                             self.sample_sd_array,
                                             self.sample_tl_array,
                                             self.sample_keys[i],
                                             self.sd_end_uses),
                            self.dict_list[i])


class StructuredArrayStringProcessingTest(unittest.TestCase):
    """ Test function that processes strings stored in a column of a
    structured array to eliminate extraneous spaces and double quotes. """

    # Define a test array with strings like those in the Description
    # column of KSDOUT (with double quotes and extraneous spaces
    # both inside and outside of the quotes)
    string_format1 = np.array([
        (' "appliance_name 2012 minimum                "', 5),
        (' "other_device-model 2019 design standard    "', 3),
        (' "final product-2010 w/price $50 cond applied"', 9)],
        dtype=[('Column Name', '<U60'), ('Other', '<i4')])

    # Define the corresponding array with the strings cleaned up
    string_format1_clean = np.array([
        ('appliance_name 2012 minimum', 5),
        ('other_device-model 2019 design standard', 3),
        ('final product-2010 w/price $50 cond applied', 9)],
        dtype=[('Column Name', '<U60'), ('Other', '<i4')])

    # Define a test array with strings like those in the Label column
    # of KDBOUT (without double quotes)
    string_format2 = np.array([
        (' GenerallyNoSpaces            ', 12),
        (' With Spaces Just In Case     ', 39),
        (' WithSome&pecial/Chars        ', 16)],
        dtype=[('The Column', '<U50'), ('Other', '<i4')])

    # Define the corresponding array with the strings cleaned up
    string_format2_clean = np.array([
        ('GenerallyNoSpaces', 12),
        ('With Spaces Just In Case', 39),
        ('WithSome&pecial/Chars', 16)],
        dtype=[('The Column', '<U50'), ('Other', '<i4')])

    # Test processing of strings that have double quotes
    def test_string_processing_with_double_quotes(self):
        self.assertCountEqual(
            cm.str_cleaner(self.string_format1, 'Column Name'),
            self.string_format1_clean)

    # Test processing of strings that only have extra spaces
    def test_string_processing_with_no_extraneous_quotes(self):
        self.assertCountEqual(
            cm.str_cleaner(self.string_format2, 'The Column'),
            self.string_format2_clean)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == '__main__':
    main()
