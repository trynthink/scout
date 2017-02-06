#!/usr/bin/env python3

"""Tests for the run_setup python module
"""

import run_setup

import unittest
from unittest.mock import patch
from collections import Counter


class CommonUnitTest(unittest.TestCase):
    """Example input and outputs for testing

    This class contains the various example inputs and outputs against
    which tests will be conducted.
    """

    # List of possible ECM names (the list of active ECMs, in this
    # case) that will be changed subject to the search text provided
    # by the user - note that these are not necessarily legitimate ECMs
    active_list = [
        'Thermoelectric Heat Pump (Prospective)',
        'ENERGY STAR Refrigerators v. 3.0',
        'Window A/C (ENERGY STAR Most Efficient)',
        'OLED Manufacturing Cost Reduction',
        'Low-cost Triple Pane Window, U-factor 0.20',
        '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
        'Novel Electric Clothes Dryer, Low-cost',
        '20 CFM Bathroom Ventilation Fan (Prospective)',
        'SEER 20 Central AC System',
        'Air Sealing Retrofit, Infiltration Reduction 20%',
        'ENERGY STAR Water Heater v.5.0',
        'Low-cost Prospective Integrated Heat Pump']

    # Lists of search strings like those that might be specified
    # by a user
    search_string_sets = [
        ['energy star', 'low-cost'],
        ['Prospective', '20%'],
        ['Scenario 1'],
        []]

    # Expected lists of ECM names that matched with the terms in the
    # corresponding list of strings when a function searches the
    # master list of ECM names
    active_list_match = [
        ['Low-cost Triple Pane Window, U-factor 0.20',
         'Novel Electric Clothes Dryer, Low-cost',
         'Low-cost Prospective Integrated Heat Pump',
         'ENERGY STAR Refrigerators v. 3.0',
         'Window A/C (ENERGY STAR Most Efficient)',
         'ENERGY STAR Water Heater v.5.0'],
        ['Thermoelectric Heat Pump (Prospective)',
         '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
         '20 CFM Bathroom Ventilation Fan (Prospective)',
         'Low-cost Prospective Integrated Heat Pump',
         'Air Sealing Retrofit, Infiltration Reduction 20%'],
        [],
        []]

    # Expected lists of ECM names that were not matched by the function
    # inspecting the master list of ECM names using the corresponding
    # list of strings
    active_list_non_match = [
        ['Thermoelectric Heat Pump (Prospective)',
         'OLED Manufacturing Cost Reduction',
         '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
         '20 CFM Bathroom Ventilation Fan (Prospective)',
         'SEER 20 Central AC System',
         'Air Sealing Retrofit, Infiltration Reduction 20%'],
        ['ENERGY STAR Refrigerators v. 3.0',
         'Window A/C (ENERGY STAR Most Efficient)',
         'OLED Manufacturing Cost Reduction',
         'Low-cost Triple Pane Window, U-factor 0.20',
         'Novel Electric Clothes Dryer, Low-cost',
         'SEER 20 Central AC System',
         'ENERGY STAR Water Heater v.5.0'],
        ['Thermoelectric Heat Pump (Prospective)',
         'ENERGY STAR Refrigerators v. 3.0',
         'Window A/C (ENERGY STAR Most Efficient)',
         'OLED Manufacturing Cost Reduction',
         'Low-cost Triple Pane Window, U-factor 0.20',
         '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
         'Novel Electric Clothes Dryer, Low-cost',
         '20 CFM Bathroom Ventilation Fan (Prospective)',
         'SEER 20 Central AC System',
         'Air Sealing Retrofit, Infiltration Reduction 20%',
         'ENERGY STAR Water Heater v.5.0',
         'Low-cost Prospective Integrated Heat Pump'],
        ['Thermoelectric Heat Pump (Prospective)',
         'ENERGY STAR Refrigerators v. 3.0',
         'Window A/C (ENERGY STAR Most Efficient)',
         'OLED Manufacturing Cost Reduction',
         'Low-cost Triple Pane Window, U-factor 0.20',
         '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
         'Novel Electric Clothes Dryer, Low-cost',
         '20 CFM Bathroom Ventilation Fan (Prospective)',
         'SEER 20 Central AC System',
         'Air Sealing Retrofit, Infiltration Reduction 20%',
         'ENERGY STAR Water Heater v.5.0',
         'Low-cost Prospective Integrated Heat Pump']]

    # List of possible ECM names (the list of inactive ECMs, in this
    # case) that will be changed subject to the search text provided
    # by the user - note that these are not necessarily legitimate ECMs
    inactive_list = [
        'low-cost energy star refrigerator v.3.0',
        'Low-cost Insulated Integrated Roof Decking',
        'Peel and stick sensors and integrated fan control (Prospective)',
        'prospective advanced thermoelastic water heater']

    # Basic function to facilitate efficient comparison of two
    # unordered lists to determine whether they have the same elements
    def compare(self, list_a, list_b):
        return Counter(list_a) == Counter(list_b)


class UserSearchKeywordInputTest(CommonUnitTest):
    # Set up test strings of user input and the desired output
    # from the function
    def setUp(self):
        # Strings as obtained from the console input
        self.user_input_strings = [
            'Scenario 1, Next Tech, ',
            'Prospective ',
            'ENERGY STAR, Thermoelectric, Heat Pump, HP',
            '']

        # Strings converted the expected form output by the function
        self.expected_out = [
            ['Scenario 1', 'Next Tech'],
            ['Prospective'],
            ['ENERGY STAR', 'Thermoelectric', 'Heat Pump', 'HP'],
            []]

    # Verify that the function successfully reads the user input
    # strings and converts them into lists in the desired format
    @patch.object(run_setup, 'input', create=True)
    def test_handling_of_user_strings_from_stdin(self, patched_input):
        for idx, input_str in enumerate(self.user_input_strings):
            # Patch provided text through as the return value from
            # the 'input' command obtaining user text from stdin
            patched_input.return_value = input_str

            # Run the function using the input patched through
            # to obtain the output from the function
            actual_out = run_setup.user_input_ecm_kw('Enter values: ')

            # Compare the actual and expected outputs
            self.assertEqual(actual_out, self.expected_out[idx])


class RegexMatchingTest(CommonUnitTest):
    # Test that the function returns the correct list of entries
    # that match the given search term
    def test_ECM_list_matching_search_terms(self):
        for idx, str_list in enumerate(self.search_string_sets):
            out, _ = run_setup.ecm_regex_select(self.active_list, str_list)
            self.assertTrue(self.compare(self.active_list_match[idx], out))

    # Test that the function returns the correct list of non-matching
    # entries from the original list
    def test_ECM_list_non_matching_search_term(self):
        for idx, str_list in enumerate(self.search_string_sets):
            _, out = run_setup.ecm_regex_select(self.active_list, str_list)
            self.assertTrue(self.compare(self.active_list_non_match[idx], out))


class FixMoveConflictsTest(CommonUnitTest):
    # Set up example lists of conflicting entries from which
    # responses can be drawn
    def setUp(self):
        self.conflict_list_l4 = [
            'Thermoelectric Heat Pump (Prospective)',
            '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
            '20 CFM Bathroom Ventilation Fan (Prospective)',
            'Low-cost Prospective Integrated Heat Pump']

        self.conflict_list_l1 = ['Novel Electric Clothes Dryer, Low-cost']

    # Test the successful selection of a subset of the conflicting entries
    @patch.object(run_setup, 'input', create=True)
    def test_move_conflicts(self, patched_input_still_move):
        # Specify the text string input by the user and returned
        # by the input function
        patched_input_still_move.return_value = '1, 3'

        # Define the expected output based on the user input
        # patched through to the function (using the dummy 4-item
        # conflict list)
        expect_keep = [
            '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
            'Low-cost Prospective Integrated Heat Pump']

        # Note that empty move order text is passed to the function
        # since no one will see the messages printed anyway
        keep = run_setup.fix_move_conflicts(self.conflict_list_l4, '')

        # Compare the expected and actual output - the list
        # of ECMs to keep in place
        self.assertTrue(self.compare(expect_keep, keep))

    # Test the successful selection of a single entry (and verify that
    # extraneous comma entries from the user are also handled properly)
    @patch.object(run_setup, 'input', create=True)
    def test_move_conflicts_list_length_1(self, patched_input_still_move):
        # Specify the text string input by the user and returned
        # by the input function (including an extraneous comma to
        # confirm that the extra input is ignored)
        patched_input_still_move.return_value = '1,'

        # Define the expected output based on the user input
        # patched through to the function (using the dummy
        # single-item conflict list)
        expect_keep = []

        # Note that empty move order text is passed to the function
        # since no one will see the messages printed anyway
        keep = run_setup.fix_move_conflicts(self.conflict_list_l1, '')

        # Compare the expected and actual output - the list
        # of ECMs to keep in place
        self.assertTrue(self.compare(expect_keep, keep))

    # Test the case where the user gives no input to the function
    # (the input() function returns an empty string)
    @patch.object(run_setup, 'input', create=True)
    def test_move_conflicts_no_user_selections(self, patched_input_nothing):
        # Specify the text obtained from the user at the input field
        patched_input_nothing.return_value = ''

        # Define the expected output based on the user input
        # patched through to the function (using the dummy
        # 4-item conflict list)
        expect_keep = [
            'Thermoelectric Heat Pump (Prospective)',
            '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
            '20 CFM Bathroom Ventilation Fan (Prospective)',
            'Low-cost Prospective Integrated Heat Pump']

        # Note that empty move order text is passed to the function
        # since no one will see the messages printed anyway
        keep = run_setup.fix_move_conflicts(self.conflict_list_l4, '')

        # Compare the expected and actual output - the list
        # of ECMs to keep in place
        self.assertTrue(self.compare(expect_keep, keep))

    # Test the case where there are conflicting entries found but the
    # user inputs one or more ECM numeric values that are out of range
    @patch.object(run_setup, 'input', create=True)
    @patch.object(run_setup, 'input', create=True)
    def test_move_conflicts_out_of_range_entry(self, err_input, ok_input):
        # Set up patched input with an out of range value input
        # by the user
        err_input.return_value = '1,3,6'
        ok_input.return_value = '1, 3, 4'

        # Define the expected output based on the user input
        # patched through to the function (using the dummy 4-item
        # conflict list) for the user's "second attempt"
        expect_keep = [
            '(Prospective) Silica Nanoparticle Liquid-applied Insulation']

        # Call the function under test, passing an empty string for the
        # move direction text since the printed messages are not seen
        # when testing the function
        keep = run_setup.fix_move_conflicts(self.conflict_list_l4, '')

        # Compare the expected and actual output - the list
        # of ECMs to keep in place
        self.assertTrue(self.compare(expect_keep, keep))

    # Test the case where the user provides non-numeric inputs in whole
    # or in part, thus preventing valid selections from being made
    @patch.object(run_setup, 'input', create=True)
    @patch.object(run_setup, 'input', create=True)
    def test_move_conflicts_non_numeric_entry(self, invalid_input, ok_input):
        invalid_input.return_value = 'stuff, 3'
        ok_input.return_value = '2,'

        # Define the expected output based on the user input
        # patched through to the function (using the dummy 4-item
        # conflict list) for the user's "second attempt"
        expect_keep = [
            'Thermoelectric Heat Pump (Prospective)',
            '20 CFM Bathroom Ventilation Fan (Prospective)',
            'Low-cost Prospective Integrated Heat Pump']

        # Call the function under test, passing an empty string for the
        # move direction text since the printed messages are not seen
        # when testing the function
        keep = run_setup.fix_move_conflicts(self.conflict_list_l4, '')

        # Compare the expected and actual output - the list
        # of ECMs to keep in place
        self.assertTrue(self.compare(expect_keep, keep))


class ECMListUpdatingTest(CommonUnitTest):
    # Note that the user input entries patched to the function under
    # test in this block MUST be given as lists or the function
    # (and these tests) will not perform as expected

    # Test a standard case for processing and updating an active and
    # inactive list of ECMs based on keywords given by the user
    @patch('run_setup.user_input_ecm_kw', side_effect=[
        ['ENERGY STAR'], ['Prospective']])
    def test_ecm_list_updating(self, input):
        # Active list for the given keywords
        self.expected_active = [
            'Thermoelectric Heat Pump (Prospective)',
            'OLED Manufacturing Cost Reduction',
            'Low-cost Triple Pane Window, U-factor 0.20',
            '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
            'Novel Electric Clothes Dryer, Low-cost',
            '20 CFM Bathroom Ventilation Fan (Prospective)',
            'SEER 20 Central AC System',
            'Air Sealing Retrofit, Infiltration Reduction 20%',
            'Low-cost Prospective Integrated Heat Pump',
            'Peel and stick sensors and integrated fan control (Prospective)',
            'prospective advanced thermoelastic water heater']

        # Inactive list for the given keywords
        self.expected_inactive = [
            'low-cost energy star refrigerator v.3.0',
            'Low-cost Insulated Integrated Roof Decking',
            'ENERGY STAR Refrigerators v. 3.0',
            'Window A/C (ENERGY STAR Most Efficient)',
            'ENERGY STAR Water Heater v.5.0']

        # Obtain outputs from the function under test
        actual_active, actual_inactive = run_setup.ecm_list_update(
            self.active_list, self.inactive_list)

        # Compare the active and inactive lists output by the function
        # with the expected output
        self.assertTrue(self.compare(actual_active, self.expected_active))
        self.assertTrue(self.compare(actual_inactive, self.expected_inactive))

    # Test a case for processing and updating an active and inactive
    # list of ECMs based on keywords where the ECMs selected by both
    # sets of keywords will have one or more conflicts to resolve
    @patch('run_setup.user_input_ecm_kw', side_effect=[
        ['Prospective', 'ENERGY STAR', 'Novel'], ['Low-cost']])
    @patch('run_setup.fix_move_conflicts', side_effect=[
        ['Novel Electric Clothes Dryer, Low-cost'],
        ['low-cost energy star refrigerator v.3.0']])
    def test_ecm_list_update_with_conflicting_moves(self, patch_fix, patch_kw):
        # Active list for the given keywords
        self.expected_active = [
            'OLED Manufacturing Cost Reduction',
            'Low-cost Triple Pane Window, U-factor 0.20',
            'Novel Electric Clothes Dryer, Low-cost',
            'SEER 20 Central AC System',
            'Air Sealing Retrofit, Infiltration Reduction 20%',
            'Low-cost Insulated Integrated Roof Decking']

        # Inactive list for the given keywords
        self.expected_inactive = [
            'Peel and stick sensors and integrated fan control (Prospective)',
            'prospective advanced thermoelastic water heater',
            'low-cost energy star refrigerator v.3.0',
            'Thermoelectric Heat Pump (Prospective)',
            'ENERGY STAR Refrigerators v. 3.0',
            'Window A/C (ENERGY STAR Most Efficient)',
            '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
            '20 CFM Bathroom Ventilation Fan (Prospective)',
            'ENERGY STAR Water Heater v.5.0',
            'Low-cost Prospective Integrated Heat Pump']

        # Obtain outputs from the function under test
        actual_active, actual_inactive = run_setup.ecm_list_update(
            self.active_list, self.inactive_list)

        # Compare the active and inactive lists output by the function
        # with the expected output
        self.assertTrue(self.compare(actual_active, self.expected_active))
        self.assertTrue(self.compare(actual_inactive, self.expected_inactive))

    # Test a case where the user only provides keywords for one of
    # the two prompts and leaves the other prompt blank (note that
    # the blank entry by the user should be patched to this function
    # as an empty list, not an empty string or nothing at all)
    @patch('run_setup.user_input_ecm_kw', side_effect=[['Prospective'], []])
    def test_ecm_list_update_with_only_one_move(self, input):
        # Active list for the given keywords
        self.expected_active = [
            'ENERGY STAR Refrigerators v. 3.0',
            'Window A/C (ENERGY STAR Most Efficient)',
            'OLED Manufacturing Cost Reduction',
            'Low-cost Triple Pane Window, U-factor 0.20',
            'Novel Electric Clothes Dryer, Low-cost',
            'SEER 20 Central AC System',
            'Air Sealing Retrofit, Infiltration Reduction 20%',
            'ENERGY STAR Water Heater v.5.0']

        # Inactive list for the given keywords
        self.expected_inactive = [
            'low-cost energy star refrigerator v.3.0',
            'Low-cost Insulated Integrated Roof Decking',
            'Peel and stick sensors and integrated fan control (Prospective)',
            'prospective advanced thermoelastic water heater',
            'Thermoelectric Heat Pump (Prospective)',
            '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
            '20 CFM Bathroom Ventilation Fan (Prospective)',
            'Low-cost Prospective Integrated Heat Pump']

        # Obtain outputs from the function under test
        actual_active, actual_inactive = run_setup.ecm_list_update(
            self.active_list, self.inactive_list)

        # Compare the active and inactive lists output by the function
        # with the expected output
        self.assertTrue(self.compare(actual_active, self.expected_active))
        self.assertTrue(self.compare(actual_inactive, self.expected_inactive))


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    """Trigger default behavior of running all test fixtures in the file."""
    unittest.main(buffer=True)

if __name__ == '__main__':
    main()
