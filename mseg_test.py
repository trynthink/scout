#!/usr/bin/env python3

""" Tests for processing microsegment data """

# Import code to be tested
import mseg

# Import needed packages
import unittest


# class FileImportTest(unittest.TestCase):
#     """ Tests the file import function """

#     def test_import(self):
#         pass


class ResidentialDataIntegrityTest(unittest.TestCase):
    """ Tests the columns in the residential data """


class GrouperTest(unittest.TestCase):
    """ Test function for combining data for each end use across years """

    # POSSIBLY ADD SETUP FUNCTION FOR VECTORS NEEDED FOR THESE TESTS

    # Test that the function successfully appends the consumption and stock
    # data to the appropriate vectors when
    def test_merging_consumption(self):
        prev_line = ['HT', 1, 1, 'EL', 'ELEC_RAD', 2009, 126206, 1858635]
        curr_line = ['HT', 1, 1, 'EL', 'ELEC_RAD', 2010, 126007, 1452680]
        consumption = [5, 20]
        c_length = len(consumption)+1
        eqstock = [6, 4]
        [consumption_m, eqstock_m] = mseg.grouper(prev_line, curr_line,
                                                  consumption, eqstock)
        self.assertEqual(len(consumption_m), c_length)

    def test_merging_equipment_stock(self):
        prev_line = ['HT', 1, 1, 'EL', 'ELEC_RAD', 2009, 126206, 1858635]
        curr_line = ['HT', 1, 1, 'EL', 'ELEC_RAD', 2010, 126007, 1452680]
        consumption = [5, 20]
        eqstock = [6, 4]
        e_length = len(eqstock)+1
        [consumption_m, eqstock_m] = mseg.grouper(prev_line, curr_line,
                                                  consumption, eqstock)
        self.assertEqual(len(eqstock_m), e_length)

    # Test differentiation


# ENDUSE  CDIV    BLDG    FUEL    EQPCLASS    YEAR    EQSTOCK CONSUMPTION
# HOUSEHOLDS
# HT  1   1   EL  ELEC_RAD    2009    126206  1858635
# HT  1   1   EL  ELEC_RAD    2010    126007  1452680
# HT  1   1   EL  ELEC_RAD    2011    125784  1577350
# HT  1   1   EL  ELEC_RAD    2012    125386  1324963
# HT  1   1   EL  ELEC_RAD    2013    125002  1715385
# HT  1   1   EL  ELEC_RAD    2014    124624  1768458
# HT  1   1   EL  ELEC_RAD    2015    124263  1623467


# Offer external code execution (include all lines below this point in all
    # test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == '__main__':
    main()
