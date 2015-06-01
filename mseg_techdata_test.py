#!/usr/bin/env python3

""" Tests for processing microsegment cost, performance, and lifetime data """

# Import code to be tested
import mseg_techdata

# Import needed packages
import unittest
import numpy


class FillYrsTest(unittest.TestCase):
    """ Test operation of both the fill_years_nlt and fill_years_lt functions
    to ensure that each yields the correct non-lighting and lighting technology
    cost, performance, and lifetime info. given an input array with these data
    broken out across various time periods. * Note: only the fill_years_lt
    function accesses lifetime info. as lifetime is not broken out by year for
    non-lighting technologies """

    # Define a list of test input arrays with valid EIA data on the cost and
    # performance of non-lighting technologies to be stitched together
    # into a list of cost and performance output dicts that each cover the
    # modeling time horizon. * Note: the second element in this list tests the
    # special case of a freezer technology, which has data on multiple
    # configurations that must be consolidated into a single 'average'
    # configuration for proper handling by the stitch function.
    in_nonlt = [numpy.array([(2005, 2010, 2.5, 1000, b'ELEC_HP1'),
                            (2010, 2011, 2.65, 1200, b'ELEC_HP1'),
                            (2011, 2012, 3.1, 1250, b'ELEC_HP1'),
                            (2012, 2014, 4.5, 1450, b'ELEC_HP1'),
                            (2014, 2040, 5, 2000, b'ELEC_HP1')],
                            dtype=[('START_EQUIP_YR', '<i8'),
                                   ('END_EQUIP_YR', '<f8'),
                                   ('BASE_EFF', '<f8'),
                                   ('INST_COST', '<f8'),
                                   ('NAME', 'S3')]),
                numpy.array([(2005, 2010, 2.5, 1000, b'FrzrC#1'),
                            (2010, 2011, 2.65, 1200, b'FrzrC#1'),
                            (2011, 2012, 3.1, 1250, b'FrzrC#1'),
                            (2012, 2014, 4.5, 1450, b'FrzrC#1'),
                            (2014, 2040, 5, 2000, b'FrzrC#1'),
                            (2005, 2010, 3, 2000, b'FrzrU#1'),
                            (2010, 2011, 3.1, 1500, b'FrzrU#1'),
                            (2011, 2012, 3.7, 1500, b'FrzrU#1'),
                            (2012, 2014, 3.7, 1600, b'FrzrU#1'),
                            (2014, 2040, 6, 1900, b'FrzrU#1')],
                            dtype=[('START_EQUIP_YR', '<i8'),
                                   ('END_EQUIP_YR', '<f8'),
                                   ('BASE_EFF', '<f8'),
                                   ('INST_COST', '<f8'),
                                   ('NAME', 'S3')])]

    # Define a test input array with valid EIA data on the cost, performance,
    # and lifetime of lighting technologies to be stitched together into
    # a list of cost, performance, and lifetime output dicts that each covers
    # the modeling time horizon
    in_lt = numpy.array([(2008, 2012, 0.33, 10000, 55, b'GSL', b'Inc'),
                         (2012, 2013, 1.03, 20000, 60, b'GSL', b'Inc'),
                         (2013, 2017, 1.53, 35000, 61.2, b'GSL', b'Inc'),
                         (2017, 2020, 2.75, 40000, 80.3, b'GSL', b'Inc'),
                         (2020, 2040, 3.45, 50000, 90, b'GSL', b'Inc')],
                        dtype=[('START_EQUIP_YR', '<i8'),
                               ('END_EQUIP_YR', '<f8'),
                               ('BASE_EFF', '<f8'),
                               ('LIFE_HRS', '<f8'),
                               ('INST_COST', '<f8'),
                               ('NAME', 'S3'),
                               ('BULB_TYPE', 'S3')])

    # Define a test input array with faulty EIA data that should yield an
    # error in the fill_years_nlt and fill_years_lt function executions
    # when paired with the tech_fail_keys below (multiple rows with same
    # starting year and not a special technology case (refrigerators, freezers)
    in_fail = numpy.array([(2005, 2010, 2.5, 1000, b'Fail_Test1'),
                           (2010, 2011, 2.65, 1200, b'Fail_Test1'),
                           (2011, 2012, 3.1, 1250, b'Fail_Test1'),
                           (2012, 2014, 4.5, 1450, b'Fail_Test1'),
                           (2014, 2040, 5, 2000, b'Fail_Test1'),
                           (2005, 2010, 3, 2000, b'Fail_Test1'),
                           (2010, 2011, 3.1, 1500, b'Fail_Test1'),
                           (2011, 2012, 3.7, 1500, b'Fail_Test1'),
                           (2012, 2014, 3.7, 1600, b'Fail_Test1'),
                           (2014, 2040, 6, 1900, b'Fail_Test1')],
                          dtype=[('START_EQUIP_YR', '<i8'),
                                 ('END_EQUIP_YR', '<f8'),
                                 ('BASE_EFF', '<f8'),
                                 ('INST_COST', '<f8'),
                                 ('NAME', 'S3')])

    # Define a sample list of the dictionary keys that are assembled while
    # running through the microsegments JSON structure; these keys are used to
    # flag non-lighting technologies that require special handling to update
    # with EIA data because of their unique definitions in these data
    # (i.e. refrigerators, freezers)
    tech_ok_keys = [['new england', 'single family home',
                     'electricity (grid)', 'heating', 'supply', 'ASHP'],
                    ['new england', 'single family home',
                     'electricity (grid)', 'other (grid electric)',
                     'freezers']]

    # Define a sample list of dictionary keys as above that should cause the
    # fill_years_nonlt function to fail when paired with an input array that
    # includes multiple rows with the same 'START_EQUIP_YR' value (this is
    # only allowed when 'refrigerators' or 'freezers' is in the key list)
    tech_fail_keys = ['new england', 'single family home',
                      'electricity (grid)', 'cooling', 'supply', 'ASHP']

    # Define the modeling time horizon to test (2009:2015)
    years = [str(i) for i in range(2009, 2015 + 1)]
    project_dict = dict.fromkeys(years)

    # Define a list of output dicts that should be generated by the
    # fill_years_nlt function for each year of the modeling time horizon
    # based on the in_nonlt array input above
    out_nonlt = [[{"2009": 2.65, "2010": 2.65, "2011": 3.1, "2012": 4.5,
                   "2013": 4.5, "2014": 5, "2015": 5},
                  {"2009": 1200, "2010": 1200, "2011": 1250, "2012": 1450,
                   "2013": 1450, "2014": 2000, "2015": 2000}],
                 [{"2009": 2.88, "2010": 2.88, "2011": 3.4, "2012": 4.1,
                   "2013": 4.1, "2014": 5.5, "2015": 5.5},
                  {"2009": 1350, "2010": 1350, "2011": 1375, "2012": 1525,
                   "2013": 1525, "2014": 1950, "2015": 1950}]]

    # Define a list of output dicts that should be generated by the
    # fill_years_lt function for each year of the modeling time horizon
    # based on the in_lt array input above
    out_lt = [{"2009": 0.33, "2010": 0.33, "2011": 0.33, "2012": 1.03,
               "2013": 1.53, "2014": 1.53, "2015": 1.53},
              {"2009": 55, "2010": 55, "2011": 55, "2012": 60,
               "2013": 61.2, "2014": 61.2, "2015": 61.2},
              {"2009": 1.14, "2010": 1.14, "2011": 1.14, "2012": 2.28,
               "2013": 4.00, "2014": 4.00, "2015": 4.00}]

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test that the fill_years_nlt function yields a correct output list
    # given the in_nlt numpy array, modeling time horizon, and tech_ok_keys
    # inputs defined above
    def test_fill_nlt(self):
        for (idx, tk) in enumerate(self.tech_ok_keys):
            list1 = mseg_techdata.fill_years_nlt(
                self.in_nonlt[idx], self.project_dict, tk)
            list2 = self.out_nonlt[idx]

            for (el1, el2) in zip(list1, list2):
                dict1 = el1
                dict2 = el2
                self.dict_check(dict1, dict2)

    # Test that the fill_years_lt function yields a correct output list given
    # the in_lt numpy array and modeling time horizon inputs defined above
    def test_fill_lt(self):
        list1 = mseg_techdata.fill_years_lt(
            self.in_lt, self.project_dict)
        list2 = self.out_lt

        for (el1, el2) in zip(list1, list2):
            dict1 = el1
            dict2 = el2
            self.dict_check(dict1, dict2)

    # Test that both the fill_years nlt and fill_years_lt functions yield a
    # ValueError when provided a numpy array input that has multiple rows
    # with the same 'START_EQUIP_YR' value
    def test_fail(self):
        with self.assertRaises(ValueError):
            mseg_techdata.fill_years_nlt(self.in_fail, self.project_dict,
                                         self.tech_fail_keys)
            mseg_techdata.fill_years_lt(self.in_fail, self.project_dict)


class StitchTest(unittest.TestCase):
    """ Test operation of stitch function, which reconstructs EIA performance,
    cost, and lifetime projections for a technology between a series of
    time periods (i.e. 2010-2014, 2014-2020, 2020-2040) in a dict with annual
    keys across a given modeling time horizon (i.e. {"2009": XXX, "2010": XXX,
    ..., "2040": XXX}) """

    # Define a test input array with valid EIA data to stich together
    # across modeling time horizon
    ok_array = numpy.array([(2008, 2012, 0.33, 14.5, 55, b'GSL', b'Inc'),
                            (2012, 2013, 1.03, 20, 60, b'GSL', b'Inc'),
                            (2013, 2017, 1.53, 21, 61.2, b'GSL', b'Inc'),
                            (2017, 2020, 2.75, 22, 80.3, b'GSL', b'Inc'),
                            (2020, 2040, 3.45, 23, 90, b'GSL', b'Inc')],
                           dtype=[('START_EQUIP_YR', '<i8'),
                                  ('END_EQUIP_YR', '<f8'),
                                  ('BASE_EFF', '<f8'),
                                  ('LIFE_HRS', '<f8'),
                                  ('INST_COST', '<f8'),
                                  ('NAME', 'S3'),
                                  ('BULB_TYPE', 'S3')])

    # Define a test input array with faulty EIA data that should yield an
    # error in the function execution (multiple rows with same starting year)
    fail_array = numpy.array([(2008, 2012, 0.33, 14.5, 55, b'GSL', b'Inc'),
                              (2012, 2013, 1.03, 20, 60, b'GSL', b'Inc'),
                              (2013, 2017, 1.53, 21, 61.2, b'GSL', b'Inc'),
                              (2017, 2020, 2.75, 22, 80.3, b'GSL', b'Inc'),
                              (2020, 2040, 3.45, 23, 90, b'GSL', b'Inc'),
                              (2013, 2017, 1.53, 21, 61.2, b'GSL', b'Inc'),
                              (2017, 2020, 2.75, 22, 80.3, b'GSL', b'Inc'),
                              (2020, 2040, 3.45, 23, 90, b'GSL', b'Inc')],
                             dtype=[('START_EQUIP_YR', '<i8'),
                                    ('END_EQUIP_YR', '<f8'),
                                    ('BASE_EFF', '<f8'),
                                    ('LIFE_HRS', '<f8'),
                                    ('INST_COST', '<f8'),
                                    ('NAME', 'S3'),
                                    ('BULB_TYPE', 'S3')])

    # Define the modeling time horizon to test (2009:2015)
    years = [str(i) for i in range(2009, 2015 + 1)]
    project_dict = dict.fromkeys(years)

    # Define the each variable (column) in the input array with the values that
    # will be reconstructed annually across the modeling time horizon, based on
    # each row's 'START_EQUIP_YR' column value
    col_names = ['BASE_EFF', 'INST_COST', 'LIFE_HRS']

    # Define a dict of output values for the above variables in col_names that
    # should be generated by the function for each year of the modeling time
    # horizon based on the ok_array above
    ok_out = [{"2009": 0.33, "2010": 0.33, "2011": 0.33, "2012": 1.03,
               "2013": 1.53, "2014": 1.53, "2015": 1.53},
              {"2009": 55, "2010": 55, "2011": 55, "2012": 60,
               "2013": 61.2, "2014": 61.2, "2015": 61.2},
              {"2009": 14.5, "2010": 14.5, "2011": 14.5, "2012": 20,
               "2013": 21, "2014": 21, "2015": 21}]

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(sorted(dict1.items()),
                                    sorted(dict2.items())):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                self.assertAlmostEqual(dict1[k], dict2[k2], places=2)

    # Test that the function yields a correct output dict for each set of
    # variable values to be stitched together across the modeling time
    # horizon, given the ok_array above as an input
    def test_convert_match(self):
        for (idx, col_name) in enumerate(self.col_names):
            dict1 = mseg_techdata.stitch(
                self.ok_array, self.project_dict,
                col_name)
            dict2 = self.ok_out[idx]
            self.dict_check(dict1, dict2)

    # Test that the function yields a ValueError given the fail_array above,
    # which includes multiple rows with the same 'START_EQUIP_YR' column value
    def test_convert_fail(self):
        for (idx, col_name) in enumerate(self.col_names):
            with self.assertRaises(ValueError):
                mseg_techdata.stitch(self.fail_array, self.project_dict,
                                     col_name)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == '__main__':
    main()
