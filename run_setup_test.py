#!/usr/bin/env python3

"""Tests for the run_setup python module
"""

import run_setup

import unittest
from unittest.mock import patch, mock_open
from collections import Counter
import os
import json
import sys


class NullDevice(object):
    """Class to capture any output to stdout from the function under test.

    Create non-operative write and flush methods to redirect output
    from the run_setup function so that it is not printed to the console.

    The write method is used to print the stdout to the console,
    while the flush function is simply a requirement for an object
    receiving stdout content.
    """
    def write(self, x):
        pass

    def flush(self):
        pass

# Send the standard output (stdout) to nowhere, effectively, to prevent
# the user prompts printed by the run_setup module from appearing in
# the console when testing those functions
sys.stdout = NullDevice()


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
        [],
        ['!energy star'],
        ['!energy star', 'low-cost'],
        ['! prospective', '!low-cost']]

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
        [],
        [
         'Thermoelectric Heat Pump (Prospective)',
         'OLED Manufacturing Cost Reduction',
         'Low-cost Triple Pane Window, U-factor 0.20',
         '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
         'Novel Electric Clothes Dryer, Low-cost',
         '20 CFM Bathroom Ventilation Fan (Prospective)',
         'SEER 20 Central AC System',
         'Air Sealing Retrofit, Infiltration Reduction 20%',
         'Low-cost Prospective Integrated Heat Pump'],
        [
         'Low-cost Triple Pane Window, U-factor 0.20',
         'Low-cost Prospective Integrated Heat Pump',
         'Novel Electric Clothes Dryer, Low-cost',
         'Thermoelectric Heat Pump (Prospective)',
         'OLED Manufacturing Cost Reduction',
         '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
         '20 CFM Bathroom Ventilation Fan (Prospective)',
         'SEER 20 Central AC System',
         'Air Sealing Retrofit, Infiltration Reduction 20%'],
        [
         'ENERGY STAR Refrigerators v. 3.0',
         'Window A/C (ENERGY STAR Most Efficient)',
         'OLED Manufacturing Cost Reduction',
         'SEER 20 Central AC System',
         'Air Sealing Retrofit, Infiltration Reduction 20%',
         'ENERGY STAR Water Heater v.5.0',
         ]]

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
         'Low-cost Prospective Integrated Heat Pump'],
        [
         'ENERGY STAR Refrigerators v. 3.0',
         'Window A/C (ENERGY STAR Most Efficient)',
         'ENERGY STAR Water Heater v.5.0'],
        [
         'ENERGY STAR Refrigerators v. 3.0',
         'Window A/C (ENERGY STAR Most Efficient)',
         'ENERGY STAR Water Heater v.5.0'],
        ['Thermoelectric Heat Pump (Prospective)',
         'Low-cost Triple Pane Window, U-factor 0.20',
         '(Prospective) Silica Nanoparticle Liquid-applied Insulation',
         'Novel Electric Clothes Dryer, Low-cost',
         '20 CFM Bathroom Ventilation Fan (Prospective)',
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


class RegexECMNameMatchingTest(CommonUnitTest):
    # Test that the function returns the correct list of entries
    # that match the given search term
    def test_ECM_list_matching_search_terms(self):
        for idx, str_list in enumerate(self.search_string_sets):
            out, _ = run_setup.ecm_kw_regex_select(self.active_list, str_list)
            self.assertTrue(self.compare(self.active_list_match[idx], out))

    # Test that the function returns the correct list of non-matching
    # entries from the original list
    def test_ECM_list_non_matching_search_term(self):
        for idx, str_list in enumerate(self.search_string_sets):
            _, out = run_setup.ecm_kw_regex_select(self.active_list, str_list)
            self.assertTrue(self.compare(self.active_list_non_match[idx], out))


class FixECMMoveConflictsTest(CommonUnitTest):
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
        keep = run_setup.fix_ecm_move_conflicts(self.conflict_list_l4, '')

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
        keep = run_setup.fix_ecm_move_conflicts(self.conflict_list_l1, '')

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
        keep = run_setup.fix_ecm_move_conflicts(self.conflict_list_l4, '')

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
        keep = run_setup.fix_ecm_move_conflicts(self.conflict_list_l4, '')

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
        keep = run_setup.fix_ecm_move_conflicts(self.conflict_list_l4, '')

        # Compare the expected and actual output - the list
        # of ECMs to keep in place
        self.assertTrue(self.compare(expect_keep, keep))


class ECMListKeywordSelectionUpdatingTest(CommonUnitTest):
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
        actual_active, actual_inactive = run_setup.ecm_list_kw_update(
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
    @patch('run_setup.fix_ecm_move_conflicts', side_effect=[
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
        actual_active, actual_inactive = run_setup.ecm_list_kw_update(
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
        actual_active, actual_inactive = run_setup.ecm_list_kw_update(
            self.active_list, self.inactive_list)

        # Compare the active and inactive lists output by the function
        # with the expected output
        self.assertTrue(self.compare(actual_active, self.expected_active))
        self.assertTrue(self.compare(actual_inactive, self.expected_inactive))


class UserBaselineMarketSelectionsTest(unittest.TestCase):
    # Test the output of the baseline market selection function when
    # passed a list of numeric selections from the user representing
    # a subset of the available climate zones
    @patch.object(run_setup, 'input', create=True)
    def test_user_baseline_climate_zone_selections(self, user_txt):
        # Define user text input to select climate zones
        user_txt.return_value = '2, 3, 4'

        # Specify market category text to pass to function under test
        baseline_mkt = 'climate_zone'

        # Define the expected list of climate zones output by the function
        expected_output = ['AIA_CZ2', 'AIA_CZ3', 'AIA_CZ4']

        # Test user input function
        self.assertEqual(
            run_setup.user_input_baseline_market_filters(baseline_mkt),
            expected_output)

    # Test the baseline market selection against a user input to
    # select a subset of the available building types
    @patch.object(run_setup, 'input', create=True)
    def test_user_baseline_building_type_selections(self, user_txt):
        # Define user text input to select building types
        user_txt.return_value = '2,'

        # Specify market category text to pass to function under test
        baseline_mkt = 'bldg_type'

        # Define the expected building type selection output by the function
        expected_output = ['commercial']

        # Test user input function for building type output
        self.assertEqual(
            run_setup.user_input_baseline_market_filters(baseline_mkt),
            expected_output)

    # Test the baseline market selection against a user input to
    # select a subset of the available structure types
    @patch.object(run_setup, 'input', create=True)
    def test_user_baseline_structure_type_selections(self, user_txt):
        # Define user text input to select structure types
        user_txt.return_value = '1'

        # Specify market category text to pass to function under test
        baseline_mkt = 'structure_type'

        # Define the expected structure type selection output by the function
        expected_output = ['new']

        # Test user input function for structure type output
        self.assertEqual(
            run_setup.user_input_baseline_market_filters(baseline_mkt),
            expected_output)

    # Test the baseline market selection function when passed an
    # invalid input followed by a valid input for climate zone selection
    @patch.object(run_setup, 'input', create=True)
    @patch.object(run_setup, 'input', create=True)
    def test_user_baseline_climate_zone_invalid_entry(self, a, b):
        # Define improper first attempt and acceptable second attempt
        # at a climate zone selection
        a.return_value = '1, 3, 5, 6,'
        b.return_value = '1, 2, 3'

        # Specify market category text to pass to function under test
        baseline_mkt = 'climate_zone'

        # Define the expected climate zones for the second (valid)
        # user input passed to the function
        expected_output = ['AIA_CZ1', 'AIA_CZ2', 'AIA_CZ3']

        # Test user input function for climate zone input with
        # a rejected first input
        self.assertEqual(
            run_setup.user_input_baseline_market_filters(baseline_mkt),
            expected_output)

    # Test the baseline market user selection function when the user
    # attempts to first input an invalid text string, followed by a
    # valid input for the building type
    @patch.object(run_setup, 'input', create=True)
    @patch.object(run_setup, 'input', create=True)
    def test_user_baseline_building_type_non_numeric_entry(self, a, b):
        # Define improper first attempt and acceptable second
        # attempt at a building type selection
        a.return_value = 'residential'
        b.return_value = '1'

        # Specify market category text to pass to function under test
        baseline_mkt = 'bldg_type'

        # Define the expected building type returned for the valid user input
        expected_output = ['residential']

        # Test user input function for building type input with an
        # invalid and rejected first input from the user
        self.assertEqual(
            run_setup.user_input_baseline_market_filters(baseline_mkt),
            expected_output)

    # Test whether the baseline user market selection function
    # correctly returns the boolean False when, for any of the
    # available baseline market parameters, the user specifies
    # all of the options
    @patch.object(run_setup, 'input', create=True)
    def test_user_baseline_all_selected(self, user_txt):
        # Define user input for each of the input types consistent with
        # user input selecting all of the options for a given baseline market
        user_txt.side_effect = ['1,2,3,4,5', '1,2', '1,2']

        # Specify market category text to pass to function under test
        baseline_mkt = ['climate_zone', 'bldg_type', 'structure_type']

        # Test that the function returns False when all of the options
        # for a given baseline market are selected
        for mkt in baseline_mkt:
            self.assertFalse(
                run_setup.user_input_baseline_market_filters(mkt))


class ECMJSONEvaluationTest(unittest.TestCase):
    # Set up partially complete "imported" ECMs (i.e., dicts) to use
    # as test articles
    def setUp(self):
        # Sample ECM definitions, including only the portion of the
        # ECM that affects the filters presented to the user, plus
        # a few additional fields to ensure that the functions will
        # not fail as a result of extraneous fields
        self.ecm1 = {
            'name': 'ENERGY STAR Air Source HP v. 5.0',
            'climate_zone': 'all',
            'bldg_type': 'all residential',
            'structure_type': 'existing',
            'end_use': ['cooling', 'heating'],
            'fuel_type': 'electricity',
            'technology': 'ASHP',
            'market_entry_year': 2015}
        self.ecm2 = {
            'name': 'Commercial Gas Boiler, 90.1 c. 2013',
            'climate_zone': ['AIA_CZ3', 'AIA_CZ4'],
            'bldg_type': 'all commercial',
            'structure_type': 'all',
            'end_use': 'heating',
            'fuel_type': 'natural gas',
            'technology': 'gas_boiler',
            'market_entry_year': 2013}
        self.ecm3 = {
            'name': 'ENERGY STAR Windows v. 6.0',
            'climate_zone': ['AIA_CZ1', 'AIA_CZ2', 'AIA_CZ3'],
            'bldg_type': 'all residential',
            'structure_type': 'all',
            'end_use': ['heating', 'secondary heating', 'cooling'],
            'fuel_type': 'all',
            'technology': ['windows conduction', 'windows solar'],
            'market_entry_year': 2015}
        self.ecm4 = {
            'name': 'Commercial Lighting, IECC c. 2015',
            'climate_zone': 'all',
            'bldg_type': ['assembly', 'education', 'small office',
                          'large office', 'lodging'],
            'structure_type': 'all',
            'end_use': 'lighting',
            'fuel_type': 'electricity',
            'technology': ['F32T8', 'T8 F32 EEMag (e)'],
            'market_entry_year': 2015}

        # Constructed list of sample ECM definitions
        self.ecms = [self.ecm1, self.ecm2, self.ecm3, self.ecm4]

    # Test the ECM baseline market matching function for a single
    # climate zone requested by the user
    def test_single_climate_zone_user_selection(self):
        # Specify the filters given by the user and the string for the
        # corresponding JSON/dict key
        filter_str = ['AIA_CZ5']
        filter_cat = 'climate_zone'

        # Specify the expected response from the function under test
        expected_response = [True, False, False, True]

        # Test the function with each of the ECMs using the specified
        # filter string to verify that it returns the correct status
        for idx, ecm_obj in enumerate(self.ecms):
            self.assertIs(
                run_setup.evaluate_ecm_json(ecm_obj, filter_str, filter_cat),
                expected_response[idx])

    # Test the ECM baseline market matching function for a case
    # where multiple climate zones have been requested by the user
    def test_multiple_climate_zones_user_selection(self):
        # Specify the filters given by the user and the string for the
        # corresponding JSON/dict key
        filter_str = ['AIA_CZ5', 'AIA_CZ4']
        filter_cat = 'climate_zone'

        # Specify the expected response from the function under test
        expected_response = [True, True, False, True]

        # Test the function with each of the ECMs using the specified
        # filter string to verify that it returns the correct status
        for idx, ecm_obj in enumerate(self.ecms):
            self.assertIs(
                run_setup.evaluate_ecm_json(ecm_obj, filter_str, filter_cat),
                expected_response[idx])

    # Test the ECM baseline market matching function for a case
    # where the ECMs should be limited to one of the two groups
    # of building types
    def test_building_type_user_selection(self):
        # Specify the filters given by the user and the string for the
        # corresponding JSON/dict key
        filter_str = ['residential']
        filter_cat = 'bldg_type'

        # Specify the expected response from the function under test
        expected_response = [True, False, True, False]

        # Test the function with each of the ECMs using the specified
        # filter string to verify that it returns the correct status
        for idx, ecm_obj in enumerate(self.ecms):
            self.assertIs(
                run_setup.evaluate_ecm_json(ecm_obj, filter_str, filter_cat),
                expected_response[idx])

    # Test the ECM baseline market matching function for a case where
    # the ECMs should be limited to one of the two structure types
    def test_structure_type_user_selection(self):
        # Specify the filters given by the user and the string for the
        # corresponding JSON/dict key
        filter_str = ['new']
        filter_cat = 'structure_type'

        # Specify the expected response from the function under test
        expected_response = [False, True, True, True]

        # Test the function with each of the ECMs using the specified
        # filter string to verify that it returns the correct status
        for idx, ecm_obj in enumerate(self.ecms):
            self.assertIs(
                run_setup.evaluate_ecm_json(ecm_obj, filter_str, filter_cat),
                expected_response[idx])


class ECMListMarketSelectionUpdatingTest(CommonUnitTest):
    # Set up several key variables for the tests of the ECM
    # list update function
    def setUp(self):
        # Define several ECMs as JSON objects mimicking the form that
        # the file contents take when they are first opened and before
        # they are converted into dicts by json.load()
        self.ecm1 = json.dumps({
            'name': 'ENERGY STAR Air Source HP v. 5.0',
            'climate_zone': 'all',
            'bldg_type': 'all residential',
            'structure_type': 'existing',
            'end_use': ['cooling', 'heating'],
            'fuel_type': 'electricity',
            'technology': 'ASHP',
            'market_entry_year': 2015})
        self.ecm2 = json.dumps({
            'name': 'Commercial Gas Boiler, 90.1 c. 2013',
            'climate_zone': ['AIA_CZ3', 'AIA_CZ4'],
            'bldg_type': 'all commercial',
            'structure_type': 'all',
            'end_use': 'heating',
            'fuel_type': 'natural gas',
            'technology': 'gas_boiler',
            'market_entry_year': 2013})
        self.ecm3 = json.dumps({
            'name': 'ENERGY STAR Windows v. 6.0',
            'climate_zone': ['AIA_CZ1', 'AIA_CZ2', 'AIA_CZ3'],
            'bldg_type': 'all residential',
            'structure_type': 'all',
            'end_use': ['heating', 'secondary heating', 'cooling'],
            'fuel_type': 'all',
            'technology': ['windows conduction', 'windows solar'],
            'market_entry_year': 2015})
        self.ecm4 = json.dumps({
            'name': 'Commercial Lighting, IECC c. 2015',
            'climate_zone': 'all',
            'bldg_type': ['assembly', 'education', 'small office',
                          'large office', 'lodging'],
            'structure_type': 'all',
            'end_use': 'lighting',
            'fuel_type': 'electricity',
            'technology': ['F32T8', 'T8 F32 EEMag (e)'],
            'market_entry_year': 2015})
        self.ecm5 = json.dumps({
            'name': 'ENERGY STAR Gas Boiler v. 3.0',
            'climate_zone': 'all',
            'bldg_type': 'all residential',
            'structure_type': 'all',
            'end_use': ['heating'],
            'fuel_type': ['natural gas', 'distillate'],
            'technology': ['boiler (NG)', 'boiler (distillate)'],
            'market_entry_year': 2014})

        # Lists of active and inactive ECMs
        self.active_list = [
            'ENERGY STAR Air Source HP v. 5.0',
            'Commercial Gas Boiler, 90.1 c. 2013',
            'ENERGY STAR Windows v. 6.0',
            'Commercial Lighting, IECC c. 2015']
        self.inactive_list = ['ENERGY STAR Gas Boiler v. 3.0']

    # Patch through the mock_open functionality and the os.listdir command
    @patch('builtins.open', new_callable=mock_open)
    @patch.object(os, 'listdir', create=True)
    def test_ecm_list_baseline_market_updating(self, mock_listdir, mock_fopen):
        # Set up file list to be returned by the mocked os.listdir
        # call, including the package_ecms.json file and a few folders
        # that should be skipped automatically by the function
        mock_listdir.return_value = [
            'ecm1.json', 'ecm2.json', 'ecm3.json', 'ecm4.json', 'ecm5.json']

        # Specify the climate zone baseline market and the climate zone
        # filters to apply to the dummy ECMs in setUp()
        market_cat = 'climate_zone'
        filters = ['AIA_CZ1', 'AIA_CZ2']

        # Patch through the output from the file open line in the
        # function to be the ECM JSON objects in setUp()
        handlers = (mock_open(read_data=self.ecm1).return_value,
                    mock_open(read_data=self.ecm2).return_value,
                    mock_open(read_data=self.ecm3).return_value,
                    mock_open(read_data=self.ecm4).return_value,
                    mock_open(read_data=self.ecm5).return_value)
        mock_fopen.side_effect = handlers

        # Define the anticipated active and inactive ECM lists
        # output by the function under test based on the specified
        # baseline market category and filters applied
        expect_active = [
            'ENERGY STAR Air Source HP v. 5.0',
            'ENERGY STAR Windows v. 6.0',
            'Commercial Lighting, IECC c. 2015']
        expect_inactive = [
            'Commercial Gas Boiler, 90.1 c. 2013',
            'ENERGY STAR Gas Boiler v. 3.0']

        # Call the function to be tested and obtain the updated
        # active and inactive ECM lists output by the function
        active, inactive = run_setup.ecm_list_market_update(
            'whatever', self.active_list, self.inactive_list,
            filters, market_cat)

        # Test that both the active and inactive ECM lists are as expected
        self.assertTrue(self.compare(active, expect_active))
        self.assertTrue(self.compare(inactive, expect_inactive))


# Offer external code execution (include all lines below this point in all
# test files)
def main():
    """Trigger default behavior of running all test fixtures in the file."""
    unittest.main()

if __name__ == '__main__':
    main()
