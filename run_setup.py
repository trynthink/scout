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
    """
    def __init__(self):
        self.setup_file = 'run_setup.json'


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

    # Update configuration/setup object with new ECM lists
    setup_json['active'] = active
    setup_json['inactive'] = inactive

    # Replace JSON file with updated contents
    json.dump(setup_json, open(ref.setup_file, 'w'), indent=2)

if __name__ == '__main__':
    main()
