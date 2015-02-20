#!/usr/bin/env python3

""" Tests for processing microsegment data """

# Import code to be tested
import mseg

# Import needed packages
import unittest
import re

# class FileImportTest(unittest.TestCase):
#     """ Tests the file import function """

#     def test_import(self):
#         pass


class ResidentialDataIntegrityTest(unittest.TestCase):
    """ Tests the imported residential equipment energy use data from
    EIA to confirm that the data are in the expected order and that the
    consumption and equipment stock data have the required names """

    # Open the EIA data file for use by all tests
    f = open(mseg.EIA_res_file, 'r')

    # Read in header line
    header = f.readline()

    # The function that parses and assigns the data from the EIA data
    # to the JSON file expects consumption data with specific header;
    # test for the presence of that header
    def test_for_presence_of_consumption_column(self):
        chk_consumption = re.search('CONSUMPTION', self.header, re.IGNORECASE)
        self.assertTrue(chk_consumption, msg='In a case-insensitive \
                        search, the CONSUMPTION column header was not \
                        found in the EIA data file.')

    # The function that parses and assigns the data from the EIA data
    # to the JSON file expects equipment stock data with specific
    # header; test for the presence of that header
    def test_for_presence_of_equipment_stock_column(self):
        chk_eqstock = re.search('EQSTOCK', self.header, re.IGNORECASE)
        self.assertTrue(chk_eqstock, msg='In a case-insensitive \
                        search, the EQSTOCK column header was not \
                        found in the EIA data file.')

    # Test for the order of the headers in the EIA data file
    def test_order_of_columns_in_header_line(self):
        # Define a regex for the expected order of the columns of data
        # (formatting of regex takes advantage of string concatenation
        # inside parentheses)
        expectregex = (r'\w*[EU]\w*\s+'
                       r'\w*[CD]\w*\s+'
                       r'\w*[BG]\w*\s+'
                       r'\w*[FL]\w*\s+'
                       r'\w*[EQ]\w*\s+'
                       r'\w*[YR]\w*\s+'
                       r'\w*[ST]\w*\s+'
                       r'\w*[CNS]\w*\s+'
                       r'\w*[HS]\w*')

        # Check for a match between the defined regex and the header line
        match = re.search(expectregex, self.header, re.IGNORECASE)

        # If there is no match, print the header line
        if not match:
            print("Header Line: " + self.header)

        # Run assertTrue to check for match and complete unit test
        self.assertTrue(match, msg="Column headers in the EIA data file \
                        are different than expected")


class texttype(unittest.TestCase):
    """ Test the formatting (byte or unicode) of the imported EIA data
    and enforce formatting requirement as dictated by code """
    # Should potentially be placed inside the txt_parser function test
    pass


class listgenerator(unittest.TestCase):
    """ Test operation of list_generator function (create dummy inputs and
    test against established outputs) """
    pass


class JSONFileStructureTest(unittest.TestCase):
    """ Test order of structure in microsegment JSON file to ensure
    that keys will be provided in the expected order and that terms in
    the JSON match with the keys of the dicts used for matching data """
    pass


class RegexConstructionTest(unittest.TestCase):
    """ Test creation of regular expressions to match against EIA text
    file data by comparing the constructed match string and the
    desired regex """

    # Identify lists to convert into regex formats using the mseg function
    convert_lists = [['VGC', 4, 1, 'EL', ''],
                     ['LT', 3, 2, 'EL', 'GSL'],
                     [('BAT', 'COF', 'DEH', 'EO', 'MCO', 'OA', 'PHP', 'SEC',
                      'SPA'), 7, 1, 'EL', ''],
                     (['HT', 1, 2, 'DS'], 'ROOF'),
                     ['HT', 5, 3, ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD'),
                      'WOOD_HT']]

    # Define the desired final regular expressions output using the
    # regex conversion function in mseg
    final_regexes = [('.*VGC.+4.+1.+EL.+.+', 'NA'),
                     ('.*LT.+3.+2.+EL.+GSL.+', 'NA'),
                     ('.*(BAT|COF|DEH|EO|MCO|OA|PHP|SEC|SPA).+7.+1.+EL.+.+',
                      'NA'),
                     ('.*HT.+1.+2.+DS.+', 'ROOF'),
                     ('.*HT.+5.+3.+(LG|KS|CL|SL|GE|NG|WD).+WOOD_HT.+', 'NA')]

    # Compare the regular expressions with the conversion function output
    def test_regex_creation_function(self):
        for idx, alist in enumerate(self.convert_lists):
            self.assertEqual(mseg.filter_formatter(alist),
                             self.final_regexes[idx])


class JSONTranslatorTest(unittest.TestCase):
    """ Test conversion of lists of strings from JSON file into
    restructured lists corresponding to the codes used by EIA in the
    residential microsegment text file """

    # Define example filters for each of the data cases present in
    # the JSON (and handled by the json_translator function)
    ok_filters = [['pacific', 'multi family home', 'natural gas',
                   'heating', 'NA', 'demand', 'ground'],
                  ['mid atlantic', 'single family home', 'electricity (grid)',
                   'cooling', 'NA', 'supply', 'room AC'],
                  ['west south central', 'mobile home', 'electricity (grid)',
                   'TVs', 'set top box', 'NA', 'NA'],
                  ['east north central', 'mobile home', 'electricity (grid)',
                   'lighting', 'NA', 'general service', 'NA'],
                  ['west north central', 'mobile home', 'other fuel',
                   'heating', 'NA', 'supply', 'resistance'],
                  ['south atlantic', 'multi family home', 'distillate',
                   'secondary heating', 'NA', 'demand', 'windows solar'],
                  ['new england', 'single family home', 'other fuel',
                   'secondary heating', 'NA', 'secondary heating (coal)',
                   'supply', 'non-specific']]

    # Define nonsense filter examples (combinations of building types,
    # end uses, etc. that aren't possible and thus wouldn't appear in
    # the microsegments JSON)
    nonsense_filters = [['mountain', 'multi family home', 'natural gas',
                         'ceiling fan', 'NA', 'NA', 'NA'],
                        ['mid atlantic', 'mobile home', 'distillate',
                         'TVs', 'home theater & audio', 'NA', 'NA']]

    # Define example filters that do not have information in the
    # correct order to be prepared using json_translator and should
    # raise an error or exception
    fail_filters = [['west north central', 'cooking', 'natural gas',
                     'drying', 'NA', 'NA', 'NA'],
                    ['pacific', 'multi family home', 'electricity (grid)',
                     'computers', 'video game consoles', 'NA', 'NA']]

    # Define what json_translator should produce for the given filters;
    # this part is critically important, as these tuples and/or lists
    # will be used by later functions to extract data from the imported
    # data files
    ok_out = [(['HT', 9, 2, 'GS'], 'GRND'),
              ['CL', 2, 1, 'EL', 'ROOM_AIR'],
              ['STB', 7, 3, 'EL', ''],
              ['LT', 3, 3, 'EL', 'GSL'],
              ['HT', 4, 3, ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD'), 'GE2'],
              ([('SH', 'OA'), 5, 2, 'DS'], 'WIND_SOL'),
              [('SH', 'OA'), 1, 1, ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD'),
               'CL']]
    nonsense_out = [['CFN', 8, 2, 'GS', ''],
                    ['HTS', 2, 3, 'DS', '']]

    # Test filters that have expected technology definitions and should match
    def test_ok_filters(self):
        for idx, afilter in enumerate(self.ok_filters):
            self.assertEqual(mseg.json_translator(afilter),
                             self.ok_out[idx])

    # Test filters that have nonsensical technology definitions but
    # should nonetheless match
    def test_nonsense_filters(self):
        for idx, afilter in enumerate(self.nonsense_filters):
            self.assertEqual(mseg.json_translator(afilter),
                             self.nonsense_out[idx])

    # Test that filters that don't conform to the structure of the
    # dicts or the expected order of data raise an error or exception
    def test_fail_filters(self):
        with self.assertRaises(KeyError):
            for afilter in self.fail_filters:
                mseg.json_translator(afilter)


# Offer external code execution (include all lines below this point in all
    # test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == '__main__':
    main()
