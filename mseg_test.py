#!/usr/bin/env python3

""" Tests for processing microsegment data """

# Import code to be tested
import mseg

# Import needed packages
import unittest
import re
import copy
import numpy


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


class NumpyArrayReductionTest(unittest.TestCase):
    """ Test the operation of the txt_parser function to verify row
    selection or deletion operations produce the expected output """

    # Define sample structured array with the same form as the
    # EIA data and that includes some of the rows to be removed
    EIA_example = numpy.array([
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2010, 126007.0, 1452680, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2011, 125784.0, 1577350, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2012, 125386.0, 1324963, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2010, 155340.0, 5955503, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2011, 151349.0, 5550354, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2012, 147470.0, 4490571, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2010, 6423576.0, 9417809, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2011, 6466014.0, 9387396, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2012, 6513706.0, 9386813, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2010, 104401.0, 1897629, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2011, 101793.0, 1875027, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2012, 99374.0, 1848448, -1),
        (b'SF ', 8, 1, b'EL', b'ELEC_RAD', 2011, 78.0, 0, -1),
        (b'SF ', 8, 1, b'EL', b'ELEC_HP ', 2011, 6.0, 0, -1),
        (b'SF ', 8, 1, b'GS', b'NG_FA   ', 2011, 0.0, 0, -1),
        (b'ST ', 3, 1, b'EL', b'ELEC_RAD', 2011, 0.0, 0, -1),
        (b'ST ', 3, 1, b'EL', b'ELEC_HP ', 2011, 3569.0, 0, -1),
        (b'ST ', 3, 1, b'GS', b'NG_FA   ', 2011, 3463.0, 0, -1),
        (b'SQ ', 7, 3, 0, 0, 2010, 2158, 2079, 7301),
        (b'SQ ', 7, 3, 0, 0, 2011, 2164, 2042, 7331),
        (b'SQ ', 7, 3, 0, 0, 2012, 2171, 2130, 7371)],
        dtype=[('ENDUSE', 'S3'), ('CDIV', '<i8'), ('BLDG', '<i8'),
               ('FUEL', 'S2'), ('EQPCLASS', 'S8'), ('YEAR', '<i8'),
               ('EQSTOCK', '<f8'), ('CONSUMPTION', '<i8'),
               ('HOUSEHOLDS', '<i8')])

    # Define reduced version of EIA data after applying the supply filter
    supply_filtered = numpy.array([
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2010, 126007.0, 1452680, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2011, 125784.0, 1577350, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2012, 125386.0, 1324963, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2010, 155340.0, 5955503, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2011, 151349.0, 5550354, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2012, 147470.0, 4490571, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2010, 6423576.0, 9417809, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2011, 6466014.0, 9387396, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2012, 6513706.0, 9386813, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2010, 104401.0, 1897629, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2011, 101793.0, 1875027, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2012, 99374.0, 1848448, -1),
        (b'SQ ', 7, 3, 0, 0, 2010, 2158, 2079, 7301),
        (b'SQ ', 7, 3, 0, 0, 2011, 2164, 2042, 7331),
        (b'SQ ', 7, 3, 0, 0, 2012, 2171, 2130, 7371)],
        dtype=[('ENDUSE', 'S3'), ('CDIV', '<i8'), ('BLDG', '<i8'),
               ('FUEL', 'S2'), ('EQPCLASS', 'S8'), ('YEAR', '<i8'),
               ('EQSTOCK', '<f8'), ('CONSUMPTION', '<i8'),
               ('HOUSEHOLDS', '<i8')])

    # Define reduced version of EIA data after applying the demand filter
    demand_filtered = numpy.array([
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2010, 126007.0, 1452680, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2011, 125784.0, 1577350, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2012, 125386.0, 1324963, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2010, 155340.0, 5955503, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2011, 151349.0, 5550354, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2012, 147470.0, 4490571, -1)],
        dtype=[('ENDUSE', 'S3'), ('CDIV', '<i8'), ('BLDG', '<i8'),
               ('FUEL', 'S2'), ('EQPCLASS', 'S8'), ('YEAR', '<i8'),
               ('EQSTOCK', '<f8'), ('CONSUMPTION', '<i8'),
               ('HOUSEHOLDS', '<i8')])

    # Define supply_filtered array after having some of the data recorded
    # in separate consumption and equipment stock vectors and then
    # removed from the main/data array
    supply_reduced = numpy.array([
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2010, 126007.0, 1452680, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2011, 125784.0, 1577350, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2012, 125386.0, 1324963, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2010, 155340.0, 5955503, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2011, 151349.0, 5550354, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2012, 147470.0, 4490571, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2010, 104401.0, 1897629, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2011, 101793.0, 1875027, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2012, 99374.0, 1848448, -1),
        (b'SQ ', 7, 3, 0, 0, 2010, 2158, 2079, 7301),
        (b'SQ ', 7, 3, 0, 0, 2011, 2164, 2042, 7331),
        (b'SQ ', 7, 3, 0, 0, 2012, 2171, 2130, 7371)],
        dtype=[('ENDUSE', 'S3'), ('CDIV', '<i8'), ('BLDG', '<i8'),
               ('FUEL', 'S2'), ('EQPCLASS', 'S8'), ('YEAR', '<i8'),
               ('EQSTOCK', '<f8'), ('CONSUMPTION', '<i8'),
               ('HOUSEHOLDS', '<i8')])

    sqft_reduced = numpy.array([
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2010, 126007.0, 1452680, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2011, 125784.0, 1577350, -1),
        (b'HT ', 1, 1, b'EL', b'ELEC_RAD', 2012, 125386.0, 1324963, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2010, 155340.0, 5955503, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2011, 151349.0, 5550354, -1),
        (b'HT ', 2, 3, b'KS', b'KERO_FA ', 2012, 147470.0, 4490571, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2010, 6423576.0, 9417809, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2011, 6466014.0, 9387396, -1),
        (b'DW ', 2, 1, b'EL', b'DS_WASH ', 2012, 6513706.0, 9386813, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2010, 104401.0, 1897629, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2011, 101793.0, 1875027, -1),
        (b'HW ', 7, 3, b'GS', b'NG_WH   ', 2012, 99374.0, 1848448, -1)],
        dtype=[('ENDUSE', 'S3'), ('CDIV', '<i8'), ('BLDG', '<i8'),
               ('FUEL', 'S2'), ('EQPCLASS', 'S8'), ('YEAR', '<i8'),
               ('EQSTOCK', '<f8'), ('CONSUMPTION', '<i8'),
               ('HOUSEHOLDS', '<i8')])

    # Define filter to select a subset of the sample EIA supply data
    EIA_supply_filter = '.*DW.+2.+1.+EL.+DS_WASH'

    # Set up selected data from EIA sample array as the basis for comparison
    EIA_supply_sample = ({"2010": 9417809, "2011": 9387396, "2012": 9386813},
                         {"2010": 6423576, "2011": 6466014, "2012": 6513706},
                         supply_reduced)

    # Define filter to select sq. footage subset of sample EIA supply data
    EIA_sqft_filter = '.*SQ.+7.+3'

    # Set up selected data from EIA sample array as the basis for comparison
    EIA_sqft_sample = ({"2010": 7301, "2011": 7331, "2012": 7371},
                       sqft_reduced)

    # Define filter to select a subset of the sample EIA demand data
    EIA_demand_filter = '.*HT.+1.+1.+EL.+ELEC_RAD'

    # Set up selected data from EIA sample array as the basis for comparison
    EIA_demand_sample = ({"2010": 1452680, "2011": 1577350, "2012": 1324963},
                         {"2010": 126007, "2011": 125784, "2012": 125386},
                         demand_filtered)

    # Define sample structured array comparable in form to the thermal
    # loads data (note that the numeric data here do not represent
    # realistic values for these data)
    tloads_example = numpy.array([
        (b'HT', 1, 1, 394.8, 0.28, 0.08, 0.08, 0.25, 0.38, -0.02, 0.22, -0.12),
        (b'CL', 1, 1, 394.8, -0.01, 0.51, 0.10, 0.15, 0.14, 0.03, -0.12, 0.19),
        (b'HT', 2, 1, 813.3, 0.29, -0.07, 0.10, 0.24, 0.38, 0.01, 0.20, -0.13),
        (b'CL', 2, 1, 813.3, -0.01, 0.44, 0.12, 0.14, 0.14, 0.03, -0.09, 0.19),
        (b'HT', 3, 2, 409.5, 0.27, -0.06, 0.23, 0.21, 0.48, 0.05, 0.13, -0.23),
        (b'CL', 3, 2, 409.5, -0.02, 0.34, 0.13, 0.06, 0.09, 0.13, -0.16, 0.41),
        (b'HT', 4, 2, 104.8, 0.29, 0.07, 0.23, 0.23, 0.44, -0.05, 0.17, -0.25),
        (b'CL', 4, 2, 104.8, 0.00, 0.31, 0.09, 0.09, 0.13, 0.11, -0.11, 0.37),
        (b'HT', 5, 3, 140.9, 0.44, -0.13, 0.11, 0.25, 0.33, -0.02, 0.16, 0.16),
        (b'CL', 5, 3, 140.9, 0.00, 0.40, 0.12, 0.11, 0.14, 0.04, -0.03, 0.20),
        (b'HT', 6, 3, 684.1, 0.47, 0.14, 0.18, 0.26, 0.39, -0.03, 0.07, -0.21),
        (b'CL', 6, 3, 684.1, -0.01, 0.37, 0.14, 0.09, 0.14, 0.04, 0.02, 0.23)],
        dtype=[('ENDUSE', 'S2'), ('CDIV', '<i8'), ('BLDG', '<i8'),
               ('NBLDGS', '<f8'), ('WIND_COND', '<f8'), ('WIND_SOL', '<f8'),
               ('ROOF', '<f8'), ('WALL', '<f8'), ('INFIL', '<f8'),
               ('PEOPLE', '<f8'), ('GRND', '<f8'), ('EQUIP', '<f8')])

    # Create filter to select thermal load data
    tl_flt = '.*CL.+2.+1'

    # Identify thermal load data to be reported (based on column names)
    tl_col = 'INFIL'

    # Set up selected data from thermal loads sample array
    tloads_sample = 0.14

    # Test removal of rows based on the supply regex in mseg
    def test_removal_of_rows_using_supply_regex_filter(self):
        self.assertCountEqual(mseg.array_row_remover(self.EIA_example,
                              mseg.unused_supply_re), self.supply_filtered)

    # Test removal of rows based on the demand regex in mseg
    def test_removal_of_rows_using_demand_regex_filter(self):
        self.assertCountEqual(mseg.array_row_remover(self.EIA_example,
                              mseg.unused_demand_re), self.demand_filtered)

    # Test restructuring of EIA data into stock and consumption lists
    # using the EIA_Supply option to confirm that both the reported
    # data and the reduced array with the remaining data are correct
    def test_recording_of_EIA_data_with_reduction_supply(self):
        (a, b, c) = mseg.stock_consume_select(self.supply_filtered,
                                              self.EIA_supply_filter,
                                              'EIA_Supply')
        # Compare equipment stock
        self.assertEqual(a, self.EIA_supply_sample[0])
        # Compare consumption
        self.assertEqual(b, self.EIA_supply_sample[1])
        # Compare remaining data
        self.assertCountEqual(c, self.EIA_supply_sample[2])

    # Test restructuring of EIA data into a sq. footage list, confirming
    # that both the reported data and the reduced array with the remaining
    # data are correct
    def test_recording_of_EIA_data_with_reduction_sqft(self):

        (a, b) = mseg.sqft_select(self.supply_filtered,
                                  self.EIA_sqft_filter)
        # Compare sq. footage
        self.assertEqual(a, self.EIA_sqft_sample[0])
        # Compare remaining data
        self.assertCountEqual(b, self.EIA_sqft_sample[1])

    # Test restructuring of EIA data into stock and consumption lists
    # using an option besides 'EIA_Supply' to confirm that for all
    # other cases, the output data are identical to the input
    def test_recording_of_EIA_data_without_reduction_demand(self):
        (a, b, c) = mseg.stock_consume_select(self.demand_filtered,
                                              self.EIA_demand_filter,
                                              'EIA_Demand')
        # Compare equipment stock
        self.assertEqual(a, self.EIA_demand_sample[0])
        # Compare consumption
        self.assertEqual(b, self.EIA_demand_sample[1])
        # Compare remaining data
        self.assertCountEqual(c, self.EIA_demand_sample[2])

    # Test extraction of the correct value from the thermal load
    # components data
    def test_recording_of_thermal_loads_data(self):
        self.assertEqual(mseg.thermal_load_select(self.tloads_example,
                         self.tl_flt, self.tl_col),
                         self.tloads_sample)


class DataToListFormatTest(unittest.TestCase):
    """ Test operation of list_generator function (create dummy inputs
    and test against established outputs) """

    # Define sample AEO time horizon for this test
    aeo_years = 2

    # Define a sample set of supply data
    supply_data = [('HT ', 1, 1, 'EL', 'ELEC_RAD', 2010, 0, 1, -1),
                   ('HT ', 1, 1, 'EL', 'ELEC_RAD', 2011, 0, 1, -1),
                   ('HT ', 2, 1, 'GS', 'NG_FA', 2010, 2, 3, -1),
                   ('HT ', 2, 1, 'GS', 'NG_FA', 2011, 2, 3, -1),
                   ('HT ', 2, 1, 'GS', 'NG_RAD', 2010, 4, 5, -1),
                   ('HT ', 2, 1, 'GS', 'NG_RAD', 2011, 4, 5, -1),
                   ('CL ', 2, 3, 'GS', 'NG_HP', 2010, 6, 7, -1),
                   ('CL ', 2, 3, 'GS', 'NG_HP', 2011, 6, 7, -1),
                   ('CL ', 1, 3, 'GS', 'NG_HP', 2010, 8, 9, -1),
                   ('CL ', 1, 3, 'GS', 'NG_HP', 2011, 8, 9, -1),
                   ('SH ', 1, 1, 'EL', 'EL', 2010, 10, 11, -1),
                   ('SH ', 1, 1, 'EL', 'EL', 2011, 10, 11, -1),
                   ('SH ', 1, 1, 'GS', 'GS', 2010, 12, 13, -1),
                   ('SH ', 1, 1, 'GS', 'GS', 2011, 12, 13, -1),
                   ('OA ', 1, 1, 'EL', 'EL', 2010, 14, 15, -1),
                   ('OA ', 1, 1, 'EL', 'EL', 2011, 14, 15, -1),
                   ('OA ', 2, 1, 'GS', 'GS', 2010, 16, 17, -1),
                   ('OA ', 2, 1, 'GS', 'GS', 2011, 16, 17, -1),
                   ('OA ', 3, 1, 'EL', 'EL', 2010, 18, 19, -1),
                   ('OA ', 3, 1, 'EL', 'EL', 2011, 18, 19, -1),
                   ('OA', 3, 1, 'WD', 'WD', 2010, 20, 21, -1),
                   ('OA', 3, 1, 'WD', 'WD', 2011, 20, 21, -1),
                   ('STB', 1, 1, 'EL', 'TV&R', 2010, 22, 23, -1),
                   ('STB', 1, 1, 'EL', 'TV&R', 2011, 22, 23, -1),
                   ('STB', 1, 2, 'EL', 'TV&R', 2010, 24, 25, -1),
                   ('STB', 1, 2, 'EL', 'TV&R', 2011, 24, 25, -1),
                   ('BAT', 2, 2, 'EL', 'MEL', 2010, 36, 37, -1),
                   ('BAT', 2, 2, 'EL', 'MEL', 2011, 36, 37, -1),
                   ('SQ', 1, 1, 0, 0, 2009, 99, 100, 101),
                   ('SQ', 1, 1, 0, 0, 2010, 99, 100, 101)
                   ]

    # Convert supply data into numpy array with column names
    supply_array = numpy.array(supply_data, dtype=[('ENDUSE', 'S3'),
                                                   ('CDIV', 'i8'),
                                                   ('BLDG', 'i8'),
                                                   ('FUEL', 'S2'),
                                                   ('EQPCLASS', 'S8'),
                                                   ('YEAR', 'i8'),
                                                   ('EQSTOCK', 'f8'),
                                                   ('CONSUMPTION', 'i8'),
                                                   ('HOUSEHOLDS', 'i8')])

    # Demand array is the same as the supply array at the start of the tests
    demand_array = copy.deepcopy(supply_array)

    # Define a sample set of thermal load components data
    loads_data = [('CL', 2, 3, 100, -0.25, 0.25, 0, 0, 0.25, 0, 0.5, 0),
                  ('CL', 1, 2, 200, -0.1, 0.1, 0, 0, 0.4, 0, 0.6, 0),
                  ('HT', 2, 3, 300, -0.5, 0.5, 0, 0, 0.5, 0, 0.5, 0),
                  ('HT', 2, 1, 400, -0.75, 0.5, 0, 0, 0.25, 0, 1, 0),
                  ('HT', 1, 1, 300, -0.2, 0.1, 0, 0.4, 0.1, 0.3, 0.3, 0),
                  ('CL', 1, 1, 400, -0.3, 0.5, 0.1, 0.1, 0.2, 0, 0.4, 0)]

    # Convert thermal loads data into numpy array with column names
    loads_array = numpy.array(loads_data, dtype=[('ENDUSE', 'S2'),
                                                 ('CDIV', 'i8'),
                                                 ('BLDG', 'i8'),
                                                 ('NBLDGS', 'f8'),
                                                 ('WIND_COND', 'f8'),
                                                 ('WIND_SOL', 'f8'),
                                                 ('ROOF', 'f8'),
                                                 ('WALL', 'f8'),
                                                 ('INFIL', 'f8'),
                                                 ('PEOPLE', 'f8'),
                                                 ('GRND', 'f8'),
                                                 ('EQUIP', 'f8')])

    # Define a set of filters that should yield matched microsegment
    # stock/energy data
    ok_filters = [['new england', 'single family home',
                   'electricity (grid)', 'heating', 'supply',
                   'boiler (electric)'],
                  ['new england', 'single family home',
                   'electricity (grid)', 'secondary heating',
                   'supply', 'non-specific'],
                  ['new england', 'single family home',
                   'natural gas', 'secondary heating', 'supply',
                   'non-specific'],
                  ['east north central', 'single family home',
                   'electricity (grid)', 'secondary heating', 'supply',
                   'non-specific'],
                  ['new england', 'single family home',
                   'electricity (grid)', 'TVs', 'set top box'],
                  ['new england', 'multi family home',
                   'electricity (grid)', 'TVs', 'set top box'],
                  ['mid atlantic', 'multi family home',
                   'electricity (grid)', 'other (grid electric)',
                   'other MELs'],
                  ['new england', 'single family home',
                   'electricity (grid)', 'heating',
                   'demand', 'ground'],
                  ['mid atlantic', 'single family home',
                   'natural gas', 'heating', 'demand',
                   'windows conduction'],
                  ['mid atlantic', 'mobile home',
                   'natural gas', 'cooling', 'demand',
                   'windows solar'],
                  ['new england', 'single family home', 'square footage'],
                  ['east north central', 'single family home',
                   'other fuel', 'secondary heating', 'supply',
                   'secondary heating (wood)']
                  ]

    # Define a set of filters that should yield zeros for stock/energy
    # data because they do not make sense
    nonsense_filters = [['mid atlantic', 'mobile home', 'natural gas',
                         'lighting', 'room AC'],
                        ['pacific', 'single family home',
                         'electricity (on site)', 'water heating', 'solar WH'],
                        ['new england', 'single family home',
                         'distillate', 'TVs',
                         'set top box']]

    # Define a set of filters that should raise an error because certain
    # filter elements do not have any match in the microsegment dict keys
    fail_filters = [['the moon', 'single family home',
                     'electricity (grid)', 'heating', 'supply',
                     'boiler (electric)'],
                    ['new england', 'single family cave',
                     'natural gas', 'secondary heating'],
                    ['new england', 'mobile home',
                     'human locomotion', 'lighting', 'reflector'],
                    ['south atlantic', 'single family home',
                     'distillate', 'secondary heating', 'supply',
                     'portable heater'],
                    ['mid atlantic', 'mobile home',
                     'electricity (grid)', 'heating',
                     'supply', 'boiler (wood fired)'],
                    ['east north central', 'multi family home',
                     'natural gas', 'cooling', 'demand', 'windows frames'],
                    ['pacific', 'multi family home', 'electricity (grid)',
                     'other (grid electric)', 'beer cooler'],
                    ['pacific', 'multi home', 'square footage'],
                    ['pacific', 'multi family home', 'square foot'],
                    ['mid atlantic', 'mobile home', 'renewables',
                     'water heating', 'solar WH'],
                    ['east north central', 'single family home',
                     'other fuel', 'secondary heating', 'demand',
                     'secondary heating (wood)']]

    # Define the set of outputs that should be yielded by the "ok_filters"
    # information above
    ok_out = [[{'stock': {"2010": 0, "2011": 0},
                'energy': {"2010": 1, "2011": 1}},
               supply_array[2:]],
              [{'stock': {"2010": 24, "2011": 24},
                'energy': {"2010": 26, "2011": 26}},
               numpy.hstack([supply_array[0:10], supply_array[12:14],
                            supply_array[16:]])],
              [{'stock': {"2010": 12, "2011": 12},
                'energy': {"2010": 13, "2011": 13}},
               numpy.hstack([supply_array[0:12], supply_array[14:]])],
              [{'stock': {"2010": 18, "2011": 18},
                'energy': {"2010": 19, "2011": 19}},
               numpy.hstack([supply_array[0:18], supply_array[20:]])],
              [{'stock': {"2010": 22, "2011": 22},
                'energy': {"2010": 23, "2011": 23}},
               numpy.hstack([supply_array[:-8], supply_array[-6:]])],
              [{'stock': {"2010": 24, "2011": 24},
                'energy': {"2010": 25, "2011": 25}},
               numpy.hstack([supply_array[:-6], supply_array[-4:]])],
              [{'stock': {"2010": 36, "2011": 36},
                'energy': {"2010": 37, "2011": 37}},
               numpy.hstack([supply_array[:-4], supply_array[-2:]])],
              [{'stock': 'NA',
                'energy': {"2010": 0.3, "2011": 0.3}},
               supply_array],
              [{'stock': 'NA',
                'energy': {"2010": -6.0, "2011": -6.0}},
               supply_array],
              [{'stock': 'NA',
                'energy': {"2010": 1.75, "2011": 1.75}},
               supply_array],
              [{"2009": 101, "2010": 101}, supply_array[:-2]],
              [{'stock': {"2010": 20, "2011": 20},
                'energy': {"2010": 21, "2011": 21}},
               numpy.hstack([supply_array[0:20], supply_array[22:]])]]

    # Define the set of outputs (empty dicts) that should be yielded
    # by the "nonsense_filters" given above
    nonsense_out = [[{'stock': {}, 'energy': {}}, supply_array],
                    [{'stock': {}, 'energy': {}}, supply_array],
                    [{'stock': {}, 'energy': {}}, supply_array]]

    # Test filter that should match and generate stock/energy data
    def test_ok_filters(self):
        for idx, afilter in enumerate(self.ok_filters):
            # Assert first output (list of values) is correct
            self.assertEqual(mseg.list_generator(self.supply_array,
                             self.demand_array,
                             self.loads_array,
                             afilter,
                             self.aeo_years)[0],
                             self.ok_out[idx][0])
            # Assert second output (reduced "supply" numpy array) is correct
            numpy.testing.assert_array_equal(mseg.list_generator(
                                             self.supply_array,
                                             self.demand_array,
                                             self.loads_array,
                                             afilter,
                                             self.aeo_years)[1],
                                             self.ok_out[idx][1])

    # Test filters that should match but ultimately do not make sense
    def test_nonsense_filters(self):
        for idx, afilter in enumerate(self.nonsense_filters):
            # Assert first output (list of values) is correct
            self.assertEqual(mseg.list_generator(self.supply_array,
                             self.demand_array,
                             self.loads_array,
                             afilter,
                             self.aeo_years)[0],
                             self.nonsense_out[idx][0])
            # Assert second output (reduced "supply" numpy array) is correct
            numpy.testing.assert_array_equal(mseg.list_generator(
                                             self.supply_array,
                                             self.demand_array,
                                             self.loads_array,
                                             afilter,
                                             self.aeo_years)[1],
                                             self.nonsense_out[idx][1])

    # Test filters that should raise an error
    def test_fail_filters(self):
        for idx, afilter in enumerate(self.fail_filters):
            with self.assertRaises(KeyError):
                # Assert first output (list of values) is correct
                mseg.list_generator(self.supply_array,
                                    self.demand_array,
                                    self.loads_array, afilter,
                                    self.aeo_years)


class RegexConstructionTest(unittest.TestCase):
    """ Test creation of regular expressions to match against EIA text
    file data by comparing the constructed match string and the
    desired regex """

    # Identify lists to convert into regex formats using the mseg function
    convert_lists = [[['VGC', 4, 1, 'EL'], ''],
                     [['LT', 3, 2, 'EL', 'GSL'], ''],
                     [[('BAT', 'COF', 'DEH', 'EO', 'MCO', 'OA', 'PHP', 'SEC',
                      'SPA'), 7, 1, 'EL'], ''],
                     [['HT', 1, 2, 'DS'], 'ROOF'],
                     [['HT', 5, 3, ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD'),
                      'WOOD_HT'], '']]

    # Define the desired final regular expressions output using the
    # regex conversion function in mseg
    final_regexes = [('.*VGC.+4.+1.+EL.+', 'NA'),
                     ('.*LT.+3.+2.+EL.+GSL.+', 'NA'),
                     ('.*(BAT|COF|DEH|EO|MCO|OA|PHP|SEC|SPA).+7.+1.+EL.+',
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
                   'heating', 'demand', 'ground'],
                  ['new england', 'mobile home', 'electricity (grid)',
                   'cooling', 'demand', 'people gain'],
                  ['mid atlantic', 'single family home', 'electricity (grid)',
                   'cooling', 'supply', 'room AC'],
                  ['west south central', 'mobile home', 'electricity (grid)',
                   'TVs', 'set top box'],
                  ['east north central', 'mobile home', 'electricity (grid)',
                   'lighting', 'general service'],
                  ['west north central', 'mobile home', 'other fuel',
                   'heating', 'supply', 'resistance'],
                  ['south atlantic', 'multi family home', 'distillate',
                   'secondary heating', 'demand', 'windows solar'],
                  ['new england', 'single family home', 'other fuel',
                   'secondary heating', 'supply', 'secondary heating (coal)'],
                  ['new england', 'single family home', 'natural gas',
                   'water heating'],
                  ['new england', 'single family home', 'square footage'],
                  ['new england', 'single family home', 'other fuel',
                   'secondary heating', 'secondary heating (kerosene)',
                   'demand', 'windows conduction']]

    # Define nonsense filter examples (combinations of building types,
    # end uses, etc. that are not possible and thus wouldn't appear in
    # the microsegments JSON)
    nonsense_filters = [['west north central', 'mobile home', 'natural gas',
                         'lighting', 'room AC'],
                        ['new england', 'single family home',
                         'electricity (on site)', 'cooling', 'supply',
                         'room AC'],
                        ['new england', 'single family home',
                         'electricity (grid)', 'refrigeration',
                         'linear fluorescent'],
                        ['new england', 'single family home', 'natural gas',
                         'water heating', 'general service']
                        ]

    # Define example filters that do not have information in the
    # correct order to be prepared using json_translator and should
    # raise an error or exception
    fail_filters = [['west north central', 'cooking', 'natural gas',
                     'drying'],
                    ['pacific', 'multi family home', 'electricity (grid)',
                     'computers', 'video game consoles'],
                    ['the moon', 'mobile home', 'distillate',
                     'heating', 'supply', 'boiler (distillate)'],
                    ['mountain', 'multi family home', 'natural gas',
                     'resistance'],
                    ['mid atlantic', 'mobile home', 'distillate',
                     'TVs', 'monitors'],
                    ['mid atlantic', 'mobile home', 'electricity (grid)',
                     'TVs', 'antennas'],
                    ['west north central', 'mobile home',
                     'electricity (grid)', 'cooling', 'supply',
                     'windows solar'],
                    ['west north central', 'mobile home',
                     'heating', 'electricity (grid)', 'demand', 'room AC'],
                    ['mountain', 'mobile home', 'sq ft'],
                    ['west north central', 'mobile home', 'square footage',
                     'water heating', 'room AC'],
                    ['new england', 'single family home', 'other fuel',
                     'secondary heating', 'supply',
                     'windows conduction'],
                    ['new england', 'single family home', 'other fuel',
                     'secondary heating', 'demand',
                     'secondary heating (coal)']
                    ]
    # Define what json_translator should produce for the given filters;
    # this part is critically important, as these tuples and/or lists
    # will be used by later functions to extract data from the imported
    # data files
    ok_out = [[['HT', 9, 2, 'GS'], 'GRND'],
              [['CL', 1, 3, 'EL'], 'PEOPLE'],
              [['CL', 2, 1, 'EL', 'ROOM_AIR'], ''],
              [['STB', 7, 3, 'EL'], ''],
              [['LT', 3, 3, 'EL', 'GSL'], ''],
              [['HT', 4, 3, ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD'),
                'GE2'], ''],
              [[('SH', 'OA'), 5, 2, 'DS'], 'WIND_SOL'],
              [[('SH', 'OA'), 1, 1, ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD'),
                'CL'], ''],
              [['HW', 1, 1, 'GS'], ''],
              [['SQ', 1, 1], ''],
              [[('SH', 'OA'), 1, 1,
               ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD')], 'WIND_COND']]
    nonsense_out = [[['LT', 4, 3, 'GS', 'ROOM_AIR'], ''],
                    [['CL', 1, 1, 'SL', 'ROOM_AIR'], ''],
                    [['RF', 1, 1, 'EL', 'LFL'], ''],
                    [['HW', 1, 1, 'GS', 'GSL'], '']]

    # Test filters that have expected technology definitions and should match
    def test_ok_filters(self):
        for idx, afilter in enumerate(self.ok_filters):
            self.assertEqual(mseg.json_translator(mseg.res_dictlist, afilter),
                             self.ok_out[idx])

    # Test filters that have nonsensical technology definitions but
    # should nonetheless match
    def test_nonsense_filters(self):
        for idx, afilter in enumerate(self.nonsense_filters):
            self.assertEqual(mseg.json_translator(mseg.res_dictlist, afilter),
                             self.nonsense_out[idx])

    # Test that filters that don't conform to the structure of the
    # dicts or the expected order of data raise an error or exception
    def test_fail_filters(self):
        for afilter in self.fail_filters:
            with self.assertRaises(KeyError):
                mseg.json_translator(mseg.res_dictlist, afilter)


class ClimConverterTest(unittest.TestCase):
    """ Test operation of climate conversion function (create dummy
    inputs and test against established outputs) """

    # Create a test input dict with 3 census divisions
    test_input = \
        {'new england': {'single family home': {
                         'electricity (grid)': {'lighting': {
                                                'linear fluorescent':
                                                [1, 1, 1]}}}},
         'mid atlantic': {'single family home': {
                          'electricity (grid)': {'lighting': {
                                                 'linear fluorescent':
                                                 [2, 2, 2]}}}},
         'east north central': {'single family home': {
                                'electricity (grid)': {'lighting': {
                                                       'linear fluorescent':
                                                       [3, 3, 3]}}}}}

    test_fail_input = \
        {'new england': {'single family home': {
                         'electricity (grid)': {'lighting': {
                                                'linear fluorescent':
                                                [1, 1, 1]}}}},
         'middle atlantic': {'single family home': {
                             'electricity (grid)': {'lighting': {
                                                    'linear fluorescent':
                                                    [2, 2, 2]}}}},
         'east north central': {'single family home': {
                                'electricity (grid)': {'lighting': {
                                                       'linear fluorescent':
                                                       [3, 3, 3]}}}}}

    # Create an expected output dict broken down by climate zone
    test_output = {'AIA_CZ1': {'single family home': {'electricity (grid)': {
                               'lighting': {'linear fluorescent':
                                            [0.8056, 0.8056, 0.8056]}}}},
                   'AIA_CZ2': {'single family home': {'electricity (grid)': {
                               'lighting': {'linear fluorescent':
                                            [3.4304, 3.4304, 3.4304]}}}},
                   'AIA_CZ3': {'single family home': {'electricity (grid)': {
                               'lighting': {'linear fluorescent':
                                            [1.7641, 1.7641, 1.7641]}}}},
                   'AIA_CZ4': {'single family home': {'electricity (grid)': {
                               'lighting': {'linear fluorescent':
                                            [0, 0, 0]}}}},
                   'AIA_CZ5': {'single family home': {'electricity (grid)': {
                               'lighting': {'linear fluorescent':
                                            [0, 0, 0]}}}}
                   }

    # Create a routine for checking equality of a dict
    def dict_check(self, dict1, dict2, msg=None):
        for (k, i), (k2, i2) in zip(dict1.items(), dict2.items()):
            if isinstance(i, dict):
                self.assertCountEqual(i, i2)
                self.dict_check(i, i2)
            else:
                # Demand "stock" currently 'NA', this handles that case
                # if we wanted to test it
                if isinstance(dict1[k], str):
                    self.assertEqual(dict1[k], dict2[k2])
                else:
                    self.assertEqual([elem for elem in dict1[k]], dict2[k2])

    # Implement dict check routine
    def test_convert_match(self):
        dict1 = mseg.clim_converter(self.test_input, mseg.res_convert_array)
        dict2 = self.test_output
        self.dict_check(dict1, dict2)

    # Implement dict fail check routine
    def test_convert_fail(self):
        with self.assertRaises(KeyError):
            mseg.clim_converter(self.test_fail_input, mseg.res_convert_array)


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    # Triggers default behavior of running all test fixtures in the file
    unittest.main()

if __name__ == '__main__':
    main()
