#!/usr/bin/env python3

""" Tests for commercial microsegment data processing code """

# Import code to be tested
import com_mseg as cm

# Import needed packages
import unittest
import numpy


class StructuredArrayStringProcessingTest(unittest.TestCase):
    """ Test function that processes strings stored in a column of a
    structured array to eliminate extraneous spaces and double quotes """

    # Define a test array with strings like those in the Description
    # column of KSDOUT (with dougble quotes and extraneous spaces
    # both inside and outside of the quotes)
    string_format1 = numpy.array([
        (' "appliance_name 2012 minimum                "', 5),
        (' "other_device-model 2019 design standard    "', 3),
        (' "final product-2010 w/price $50 cond applied"', 9)],
        dtype=[('Column Name', '<U60'), ('Other', '<i4')])

    # Define the corresponding array with the strings cleaned up
    string_format1_clean = numpy.array([
        ('appliance_name 2012 minimum', 5),
        ('other_device-model 2019 design standard', 3),
        ('final product-2010 w/price $50 cond applied', 9)],
        dtype=[('Column Name', '<U60'), ('Other', '<i4')])

    # Define a test array with strings like those in the Label column
    # of KDBOUT (without double quotes)
    string_format2 = numpy.array([
        (' GenerallyNoSpaces            ', 12),
        (' With Spaces Just In Case     ', 39),
        (' WithSome&pecial/Chars        ', 16)],
        dtype=[('The Column', '<U50'), ('Other', '<i4')])

    # Define the corresponding array with the strings cleaned up
    string_format2_clean = numpy.array([
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
