#!/usr/bin/env python3

"""Docstring
"""

import re
import json
import os


class UsefulVars(object):
    """Stores useful variables to avoid the use of global variables

    Attributes:
        setup_file (str): Scout setup/configuration JSON file name
        ecm_folder_location (str): Path to the folder with the ECM JSON files
    """
    def __init__(self):
        self.setup_file = 'run_setup.json'
        self.ecm_folder_location = './ecm_definitions'
        self.market_filters = ['climate_zone', 'bldg_type', 'structure_type']


class IndexLists(object):
    """Stores indices for articulating or matching baseline market values

    Attributes:
        climate_zone (list): List of possible climate zone values
            in ECM definitions
        structure_type (list): Lists valid structure types for ECMs
        building_type (list): Lists building type families
        building_type_map (list): Specifies the relationship between
            the building type groups and the particular building type
            values that can be specified in an ECM definition
    """
    def __init__(self):
        self.climate_zone = ['AIA_CZ1', 'AIA_CZ2', 'AIA_CZ3',
                             'AIA_CZ4', 'AIA_CZ5']
        self.structure_type = ['new', 'retrofit']
        self.building_type = ['residential', 'commercial']
        self.building_type_map = {
            'residential': [
                'all residential', 'single family home',
                'multi family home', 'mobile home'],
            'commercial': [
                'all commercial', 'assembly', 'education', 'food sales',
                'food service', 'health care', 'lodging', 'large office',
                'small office', 'mercantile/service', 'warehouse', 'other']}
        self.climate_zone_pr = ['AIA Climate Zone 1', 'AIA Climate Zone 2',
                                'AIA Climate Zone 3', 'AIA Climate Zone 4',
                                'AIA Climate Zone 5']
        self.building_type_pr = ['Residential', 'Commercial']
        self.structure_type_pr = ['New Construction', 'Retrofit']


def user_input_ecm_kw(prompt_text):
    """Get user input for keywords to filter the ECM lists

    Args:
        prompt_text (str): The text to use in the input prompt to the user.

    Returns:
        A cleaned list of ECM name filtering keywords derived from
        user input. If the input is empty, an empty string is produced
        by the input() function, which is converted to and returned as
        an empty list.
    """

    # Obtain keywords/search terms from user input
    kw_to_move = input(prompt_text)

    # Split lists of filters input by the user based on the specified
    # delimiter and simultaneously strip any leading or trailing
    # whitespace and any empty strings
    kw_to_move = [val.strip() for val in kw_to_move.split(',') if val.strip()]

    return kw_to_move


def ecm_regex_select(ecm_names_list, list_of_match_str):
    """Identify matching, non-matching ECM names using a list of search terms

    This function searches a list of ECM names to find all of the ECM
    names that have the words specified by the user as search terms.
    This function is used to identify the ECMs that should be moved from
    the active to inactive list or vice versa. The regex is set up to
    be case-insensitive.

    Args:
        ecm_names_list (list): A list of ECM names encoded as strings.
        list_of_match_str (list): A list with at least one entry,
            corresponding to the strings specified by the user to
            be used to select ECMs to move from the active to the
            inactive list, or vice versa.

    Returns:
        A list of all of the ECM names that matched with the search
        string(s) and a separate list of all of the ECM names that did
        not match with the search string.
    """

    # If the list is not empty, identify the matching and non-matching
    # entries in the list of ECM names
    if list_of_match_str:
        # Construct the regex search pattern from the list of strings given
        nom_regex = re.compile(r'(?:%s)' % '|'.join(list_of_match_str),
                               re.IGNORECASE).search

        # Construct a list of all of the ECM names that matched the regex
        matches = [ecm for ecm in ecm_names_list if nom_regex(ecm)]

        # Construct a list of all of the ECM names that did not match the regex
        non_matches = [ecm for ecm in ecm_names_list if not nom_regex(ecm)]

    # If the list is empty, running the above process would result in
    # all of the ECM names matching, which is the opposite of what is
    # desired for the case with no keywords, thus this case of no
    # search terms is handled explicitly
    else:
        matches = []
        non_matches = ecm_names_list

    return matches, non_matches


def fix_move_conflicts(conflict_ecm_list, move_order_text):
    """Get user input to sort out ECMs moved in both directions

        It is possible that with a given set of active and inactive
        ECMs and some sets of keywords given by the user to move ECMs
        in bulk from one list to the other, there will be cases where
        one or more ECMs moved from one list to the other would be
        moved back by the keyword(s) directing the move in the other
        direction.

        This function takes those ECMs and asks the user whether, for
        each ECM, they would like to continue the move as indicated
        by the keyword(s) they gave for the move in the direction
        indicated by 'move_order_text' or if they would like to leave
        the ECM on its original list.

        Args:
            conflict_ecm_list (list): A list of ECM names corresponding
                to the ECMs that are moved in both directions by the
                keywords given by the user
            move order text (str): A string indicating the original
                intended direction to move the ECMs indicated in
                'conflict_ecm_list'

        Returns:
            A list of the ECM names that should stay on the list
            where they started (i.e., if they started out as active
            ECMs, they should remain active).

            If no ECMs are selected, an empty list is returned.
    """

    # Inform the user that there are overlapping terms present
    print('\nThe following ECMs, when using your specified search terms '
          'would not be moved because the terms used for each direction '
          'conflict for these ECMs. The ECMs listed below were selected '
          'to move from', move_order_text + '.\n')

    # Print each ECM with a corresponding number
    for idx, entry in enumerate(conflict_ecm_list):
        print(idx+1, '-', entry)

    # Construct string to print for the input field
    instruct_str = ('\nFrom the list, indicate which ECMs you would '
                    'still like to have moved from ' + move_order_text +
                    ' by entering their corresponding number(s), if '
                    'any, separated by commas: ')

    # Prompt the user to specify the desired outcome for each conflicting move
    selections = input(instruct_str)

    # Convert user input into a list of integers corresponding to the
    # list entries for the ECMs to move, and handle cases where the
    # user provides non-numeric text to the input
    while True:
        # Convert the user input into a list of integers with
        # no extraneous trailing or leading spaces
        try:
            move_ecm_numbers = [int(x.strip())
                                for x in selections.split(',') if x.strip()]
        # Handle the exception if a non-integer entry is passed
        # to the input by requesting the user attempt to enter
        # their desired entries from the list again
        except ValueError:
            input('An invalid non-numeric entry was given. '
                  'Please try again: ')
        # When a valid input is received, interrupt the loop
        else:
            break

    # Check that values aren't out of range and prompt the user for
    # the list of desired entries until only valid entries are given
    if move_ecm_numbers:
        while max(move_ecm_numbers) > len(conflict_ecm_list):
            selections = input('An out of range number was given. '
                               'Please try again: ')
            move_ecm_numbers = [int(x.strip())
                                for x in selections.split(',') if x.strip()]

    # Create a list of all of the ECMs that are going to be kept
    # in place/not moved
    keep_in_place = [conflict_ecm_list[i-1]
                     for i in range(1, len(conflict_ecm_list)+1)
                     if i not in move_ecm_numbers]

    return keep_in_place


def ecm_list_update(active_list, inactive_list):
    """Update the lists of ECMs based on the keywords specified by the user

    Taking the lists of ECM names that are indicated as active and
    inactive in run_setup.json, this function gets user input on
    the keywords to use to move ECMs from their current list to the
    other list (in both directions) and then resolves any conflicts
    that might arise as a result of keywords that would move an ECM
    from its original list to the other list and then back again,
    depending on the order in which the keyword selection and
    reassignment were performed. Finally, this function will output
    updated lists of active and inactive ECMs to write back to the
    JSON file.

    Args:
        active_list (list): A list of ECM names that are set to be
            active (i.e., included) when executing run.py.
        inactive_list (list): A list of ECN names corresponding to the
            ECMs that will not be included in an analysis using run.py.

    Returns:
        Revised lists of active and inactive ECMs.
    """

    # Text to print to the console, broken into short blocks
    print('You can use short strings to quickly move groups of ECMs '
          'from the active to inactive lists and vice versa. '
          'For example, you can specify "Prospective" to select all '
          'ECMs that have the word "Prospective" in their name.\n')
    print('You may input more than one search term. Please separate '
          'each term with a comma, for example, "Efficient, 20%".\n')
    print('If you are unsure of the ECMs currently listed as active '
          'and inactive, inspect the lists in the run_setup.json file.\n')

    # Define text for prompts to user to input keywords for moving
    # ECMs to the inactive and active lists
    to_inactive_prompt_text = ('Enter ECM name keywords separated by '
                               'commas to move ECMs active -> inactive: ')
    to_active_prompt_text = ('Enter ECM name keywords separated by '
                             'commas to move ECMs inactive -> active: ')

    # Call function to obtain list of user input strings
    kw_to_inactive = user_input_ecm_kw(to_inactive_prompt_text)
    kw_to_active = user_input_ecm_kw(to_active_prompt_text)

    # Update active and inactive lists and identify moves
    move_to_inactive, active_list = ecm_regex_select(active_list,
                                                     kw_to_inactive)
    move_to_active, inactive_list = ecm_regex_select(inactive_list,
                                                     kw_to_active)

    # ACTIVE ECM LIST AND ASSOCIATED MOVES ----------------------------
    # Check if the keywords given for selecting inactive ECMs to move
    # to the active list would select any of the ECMs about to move
    # to the inactive list
    if kw_to_active and move_to_inactive:
        back_to_active, _ = ecm_regex_select(move_to_inactive, kw_to_active)

        # If there are any ECMs that are selected to move to the
        # inactive list that could then be moved back to active
        # (depending on the order in which the moves are applied),
        # resolve what to do with those ECMs based on user input
        if back_to_active:
            # Get user input on how to move the ECMs
            keep_active = fix_move_conflicts(back_to_active,
                                             'active to inactive')

            # Update the active list by restoring the ECMs that had
            # been slated for removal and rebuild the list of ECMs
            # to move to the inactive list by removing all those that
            # will now be kept as active
            active_list = active_list + keep_active
            move_to_inactive = [ecm for ecm in move_to_inactive
                                if ecm not in keep_active]

    # INACTIVE ECM LIST AND ASSOCIATED MOVES --------------------------
    # Check if the keywords given for selecting active ECMs to move to
    # the inactive list would select any of the ECMs about to move the
    # the active list
    if kw_to_inactive and move_to_active:
        back_to_inactive, _ = ecm_regex_select(move_to_active, kw_to_inactive)

        # If there are any ECMs that are selected to move to the
        # active list that could then be moved back to inactive
        # (depending on the order in which the moves are applied),
        # resolve what to do with those ECMs based on user input
        if back_to_inactive:
            # Get user input on how to move the ECMs
            keep_inactive = fix_move_conflicts(back_to_inactive,
                                               'inactive to active')

            # Update the inactive list by restoring the ECMs that had
            # been slated for removal and rebuild the list of ECMs to
            # move to the active list by removing all those that will
            # now be kept as inactive
            inactive_list = inactive_list + keep_inactive
            move_to_active = [ecm for ecm in move_to_active
                              if ecm not in keep_inactive]

    # Update the active and inactive lists based on the moves
    # indicated by the user from their keyword inputs, including
    # any changes indicated by the user to resolve move conflicts
    active_list = active_list + move_to_active
    inactive_list = inactive_list + move_to_inactive

    return active_list, inactive_list


def user_input_baseline_market_filters(market_cat):
    """Obtain user selections for the baseline market filtering categories

    Based on the indicated baseline market category given by the
    input argument, this function prompts the user to indicate
    which of the available options should be applied to determine
    which ECMs should remain in the active list.

    Args:
        market_cat (str): Applicable baseline market string used to
            indicate what data should be requested from the user

    Returns:
        A list of filters corresponding to the values that should
        match with the updated list of active ECMs.

        This function returns False if the user explicitly requests
        all of the options for a given baseline market (i.e., the
        user specifies all five climate zones).
    """
    # Instantiate index lists object
    il = IndexLists()

    # Set function-specific variables regarding the options to be
    # presented to the user and the corresponding descriptive string
    if market_cat == 'climate_zone':
        user_options = il.climate_zone_pr
        selection_name = 'climate zones'
        json_keys = il.climate_zone
    elif market_cat == 'bldg_type':
        user_options = il.building_type_pr
        selection_name = 'building types'
        json_keys = il.building_type
    elif market_cat == 'structure_type':
        user_options = il.structure_type_pr
        selection_name = 'structure types'
        json_keys = il.structure_type

    # Describe the filtering available to the user
    print('Please indicate the', selection_name, 'for which you want '
          'to include applicable ECMs in the analysis. If you want to '
          'include all of the', selection_name, 'simply type "enter" '
          'or "return" to skip.\n')

    # Print and label the options for the user
    for idx, val in enumerate(user_options):
        print(idx+1, '-', val)

    # Prompt the user for input
    selections = input('\nPlease enter your selections, separated by commas: ')

    # Convert user input into a list of integers corresponding to the
    # list entries for the ECMs to move, and handle cases where the
    # user provides non-numeric text to the input
    while True:
        # Convert the user input into a list of integers with
        # no extraneous trailing or leading spaces
        try:
            user_select_keep_numbers = [
                int(x.strip()) for x in selections.split(',') if x.strip()]
        # Handle the exception if a non-integer entry is passed
        # to the input by requesting the user attempt to enter
        # their desired entries from the list again
        except ValueError:
            input('An invalid non-numeric entry was given. '
                  'Please try again: ')
        # When a valid input is received, interrupt the loop
        else:
            break

    # Check that values aren't out of range and prompt the user for
    # the list of desired entries until only valid entries are given
    if user_select_keep_numbers:
        while max(user_select_keep_numbers) > len(user_options):
            selections = input('An out of range number was given. '
                               'Please try again: ')
            user_select_keep_numbers = [
                int(x.strip()) for x in selections.split(',') if x.strip()]

    # Build the list of keys to match against individual ECM JSON data
    user_match_filters = [json_keys[i-1] for i in user_select_keep_numbers]

    # Set the target return value of this function to boolean False
    # to prevent further evaluation function calls to subset the list
    # of active ECMs if the user has effectively selected "all"
    if len(user_match_filters) == len(json_keys):
        user_match_filters = False

    return user_match_filters


def evaluate_ecm_json(json_contents, filters, market_cat):
    """Determine whether a given ECM should remain in the active list

    IMPORTANT! - This function should not be called if the user has
    indicated that they want to keep all of the options for a given
    applicable baseline market category (e.g., they want to keep
    ECMs from all of the climate zones).

    For a given ECM, use the baseline market information from the
    definition and the filter options specified by the user,
    determine whether or not the ECM should remain in the active list.

    Note that "filters" is generated by a different function and
    is automatic, so this function does not have to handle incomplete
    or incorrect text strings provided by the user (as a result of
    e.g., typos) for various baseline market category fields.

    Args:
        json_contents (dict): The contents of a single ECM JSON definition file
        filters (list): A list of strings to use to determine whether
            the current ECM should be active or not
        market_cat (str): The name of the key in the ECM JSON to which
            the strings in the 'filters' variable correspond. Valid
            values include e.g., "climate_zone", "bldg_type".

    Returns:
        Boolean value indicating whether or not the ECM (contents)
        passed to the function should be kept on the active list,
        where keep = True, move to inactive = False
    """

    # Extract the relevant values from the key in the dict indicated
    # by the 'market_cat' variable
    json_vals = json_contents[market_cat]

    # Set the return value (active_bool) to False initially
    active_bool = False

    # Determine whether the filter values are in the current ECM
    if json_vals == 'all':
        # If the JSON is set to "all" for the current field of
        # interest, then there's certainly a match with whatever
        # filters the user has requested
        active_bool = True
    # Special handling for building type
    elif market_cat == 'bldg_type':
        # Do not need for loop through filters since only two
        # building type values can be passed to this function,
        # and if both apply, this function should not be called
        # in the first place

        il = IndexLists()  # Instantiate object

        # Make the value(s) in json_vals into a list
        # if it is not already
        if not isinstance(json_vals, list):
            json_vals = [json_vals]

        # Set active_bool based on whether or not there are any matching
        # building types present in the ECM; note that the isdisjoint
        # set evaluation returns FALSE if matches are found;
        # 'filters[0]' will always match one of the two building type
        # keys specified in the building_type_map attribute of IndexLists
        if not set(il.building_type_map[filters[0]]).isdisjoint(json_vals):
            active_bool = True
    else:
        # Cycle through all of the filter values
        for entry in filters:
            # If any of the entries in the list of filters match for
            # this ECM, set the active status of this ECM to True
            if entry in json_vals:
                active_bool = True

    return active_bool


def ecm_list_market_update(ecm_folder, active_list, inactive_list,
                           filters, market_cat):
    """Update the active and inactive lists based on the user-selected filters

    Based on the filters identified by the user for a given baseline
    market parameter, this function opens each ECM and (after checking
    to ensure that it is on the active list) checks to see if it
    passes the filters and can thus be retained on the active list
    or if it should be moved to the inactive list. The active and
    and inactive lists are updated after reviewing each ECM

    Args:
        ecm_folder (str): The path to the folder where the ECM JSON
            definition files are located
        active_list (list): A list of ECM names that are set to be
            active (i.e., included) when executing run.py
        inactive_list (list): A list of ECN names corresponding to the
            ECMs that will not be included in an analysis using run.py
        filters (list): A list of strings to use to determine whether
            the current ECM should be active or not
        market_cat (str): Applicable baseline market string used to
            indicate what data should be requested from the user

    Returns:
        Updated lists of active and inactive ECMs.
    """

    # Get list of files in the ECM folder
    file_list = os.listdir(ecm_folder)

    # Clean up list of files to include only ECM JSONs
    file_list = [name for name in file_list if name.endswith('.json')]

    # Try to remove the package ECMs JSON definition file if it is
    # present, otherwise continue
    try:
        file_list.remove('package_ecms.json')
    except ValueError:
        pass

    # Work through the list of ECMs
    for ecm_file in file_list:
        # Construct file path
        ecm_file_path = ecm_folder + '/' + ecm_file

        # Import JSON file
        with open(ecm_file_path, 'r') as fobj:
            ecm_json_contents = json.load(fobj)

        # Check if the ECM is currently in the active list, and if
        # it is, determine whether it should remain in that list
        if ecm_json_contents['name'] in active_list:
            # Find out whether or not this ECM should be included
            # in the active list
            keep = evaluate_ecm_json(ecm_json_contents, filters, market_cat)

            # Update the active and inactive lists based on the
            # evaluation of the ECM by the evaluate_ecm_json function
            if not keep:
                active_list.remove(ecm_json_contents['name'])
                inactive_list.append(ecm_json_contents['name'])

    # Return the updated list of active ECMs and ECMs to be moved to inactive
    return active_list, inactive_list


def main():
    # Clear the console window before printing any text
    os.system('cls' if os.name == 'nt' else 'clear')

    # Print initial script message to the console
    print('\nThis function will help configure the simulation. '
          'Respond to each of the prompts.\n'
          'Hit "enter" or "return" to skip a question.\n')

    # Instantiate object with useful master variables
    ref = UsefulVars()

    # Import configuration/setup JSON file
    with open(ref.setup_file, 'r') as fobj:
        setup_json = json.load(fobj)

    # Execute function to update lists
    active, inactive = ecm_list_update(setup_json['active'],
                                       setup_json['inactive'])

    # Clear the console window again
    os.system('cls' if os.name == 'nt' else 'clear')

    # Print instructions regarding additional filtering opportunities
    print('\nNow, you will be prompted to further reduce the '
          'list of ECMs to include in the analysis, if you desire. '
          'Your selections in the subsequent prompts will override '
          'the previous step, but will only apply to the active ECM '
          'list.\nHit "enter" or "return" to skip a question.\n')

    # Loop through the baseline market fields available, prompt
    # the user, and update the list of active ECMs accordingly
    for market in ref.market_filters:
        user_filter_choices = user_input_baseline_market_filters(market)

        # If False, do not proceed, otherwise use filters to select
        # the appropriate ECMs and move them from the active to the
        # inactive list
        if user_filter_choices:
            active, inactive = ecm_list_market_update(ref.ecm_folder_location,
                                                      active,
                                                      inactive,
                                                      user_filter_choices,
                                                      market)

    # Update configuration/setup object with new ECM lists
    setup_json['active'] = active
    setup_json['inactive'] = inactive

    # Replace JSON file with updated contents
    json.dump(setup_json, open(ref.setup_file, 'w'), indent=2)

if __name__ == '__main__':
    main()
