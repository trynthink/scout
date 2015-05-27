#!/usr/bin/env python3
import re
import numpy
import json
import mseg

# Set microsegments JSON as the file that provides the structure for
# the technology performance, cost, and lifetime information output JSON
json_in = 'microsegments.json'
# Set technology performance, cost, and lifetime information output JSON
# file name
json_out = 'base_costperflife.json'

# Set the file names for the EIA information on the performance,
# cost, and lifetime of non-lighting and lighting technologies in the
# residential sector

# EIA non-lighting cost and performance information
r_nlt_costperf = 'rsmeqp.txt'
# EIA non-lighting lifetime information
r_nlt_life = 'rsclass.txt'
# EIA lighting cost, performance, and lifetime information
r_lt_all = 'rsmlgt.txt'

# Pre-specify the numpy field names to be used in importing the EIA
# information on the cost performance, and lifetime of of non-lighting and
# lighting technologies in the residential sector

# Numpy field names for EIA 'rsmeqp.txt' file with cost and performance
# information for non-lighting technologies
r_nlt_cp_names = ('ENDUSE', 'EQUIP_CLASS', 'EQUIP_TYP', 'START_EQUIP_YR',
                  'END_EQUIP_YR', 'CDIV', 'HVAC_POINT', 'HP_POINT', 'MOD_EF',
                  'WH_LOAD', 'BASE_EFF', 'INST_COST', 'RETAIL_COST',
                  'NA1', 'NA2', 'NA3', 'NA4', 'TECH_MATURE', 'COST_TREND',
                  'COST_SHAPE', 'COST_PROP', 'EFF_CHOICE_P1',
                  'EFF_CHOICE_P2', 'EFF_CHOICE_P3', 'EFF_CHOICE_MOD',
                  'NAME')

# Numpy field names for EIA 'rsclass.txt' file with lifetime information
# for non-lighting technologies
r_nlt_l_names = ('ENDUSE', 'EQUIP_CLASS', 'EQUIP_POINT', 'CLASS_POINT',
                 'REPLACE_CLASS', 'FUEL', 'MAJ_FUEL_FLAG', 'FFAN_FLAG',
                 'BASE_EFF', 'LIFE_PARAM', 'LIFE_MIN', 'LIFE_MAX',
                 'FCMOD_P1', 'FCMOD_P2', 'FCMOD_P3', 'FCMOD_P4', 'FCMOD_P5',
                 'FCOD_P6', 'NAME')

# Numpy field names for EIA 'rsmlgt.txt' file with cost, performance, and
# lifetime information for lighting technologies
r_lt_names = ('START_EQUIP_YR', 'END_EQUIP_YR', 'INST_COST', 'SUB1',
              'SUB2', 'SUB3', 'SUB4', 'SUB5', 'SUB6', 'SUB7', 'SUB8',
              'SUB9', 'BASE_EFF', 'BASE_EFF_W', 'LIFE_HRS', 'CRI', 'NAME',
              'BULB_TYPE')

# Initialize a dict with information needed for filtering EIA cost and
# performance information by the census division being run through in the input
# microsegments JSON (* Note: EIA cost and performance information is only
# broken down by census division for non-lighting technologies; for lighting
# technologies, cost and performance information can be applied across all
# census divisions.  Lifetime information is not broken down by census div.)
mseg_cdiv_translate = {'new england': 1, 'mid atlantic': 2,
                       'east north central': 3, 'west north central': 4,
                       'south atlantic': 5, 'east south central': 6,
                       'west south central': 7, 'mountain': 8, 'pacific': 9
                       }

# Create dicts with either:
# a) The information needed to find the cost,
# performance, and lifetime of a given technology in the input microsegment
# JSON from the appropriate EIA .txt file, or
#
# b) Direct information about the
# cost, performance, and lifetime of a given technology in the input
# microsegment.  Ultimately, all updated information will be exported to the
# 'base_costperflife.json' file defined above.

# The basic structure of a) above for non-lighting technologies is:
#  'microsegments.json' tech. key: [
#   EIA file info.,
#   lifetime filter name,
#  'typical' performance and cost filter name,
#  'best' performance and cost filter name,
#   performance units (* Note: cost units are addressed separately)]
tech_eia_nonlt = {'ASHP': ['EIA_EQUIP', 'ELEC_HP', 'ELEC_HP1', 'ELEC_HP4',
                           'COP'],
                  'GSHP': ['EIA_EQUIP', 'GEO_HP', 'GEO_HP1', 'GEO_HP2', 'COP'],
                  'NGHP': ['EIA_EQUIP', 'NG_HP', 'NG_HP', 'NG_HP', 'COP'],
                  'boiler (NG)': ['EIA_EQUIP', 'NG_RAD', 'NG_RAD1', 'NG_RAD3',
                                  'AFUE'],
                  'boiler (distillate)': ['EIA_EQUIP', 'DISTRAD', 'DISTRAD1',
                                          'DISTRAD3', 'AFUE'],
                  'boiler (electric)': ['EIA_EQUIP', 'ELEC_RAD', 'ELEC_RAD',
                                        'ELEC_RAD', 'AFUE'],
                  'furnace (distillate)': ['EIA_EQUIP', 'DIST_FA', 'DIST_FA1',
                                           'DIST_FA3', 'AFUE'],
                  'furnace (kerosene)': ['EIA_EQUIP', 'KERO_FA', 'KERO_FA1',
                                         'KERO_FA3', 'AFUE'],
                  'furnace (LPG)': ['EIA_EQUIP', 'LPG_FA', 'LPG_FA#1',
                                    'LPG_FA#5', 'AFUE'],
                  'furnace (NG)': ['EIA_EQUIP', 'NG_FA', 'NG_FA#1', 'NG_FA#5',
                                   'AFUE'],
                  'stove (wood)': ['EIA_EQUIP', 'WOOD_HT', 'WOOD_HT',
                                   'WOOD_HT', 'COP'],
                  'solar WH': ['EIA_EQUIP', 'SOLAR_WH', 'SOLAR_WH1',
                               'SOLAR_WH1', 'EF'],
                  'central AC': ['EIA_EQUIP', 'CT_AIR', 'CT_AIR#1', 'CT_AIR#4',
                                 'COP'],
                  'room AC': ['EIA_EQUIP', 'RM_AIR', 'RM_AIR#1', 'RM_AIR#3',
                              'COP'],
                  'clothes washing': ['EIA_EQUIP', 'CW', 'CW#1', 'CW#3',
                                      'kWh/cycle'],
                  'water heating': ['EIA_EQUIP',
                                     ['ELEC_WH', 'NG_WH', 'LPG_WH'],
                                     ['ELEC_WH1', 'NG_WH#1', 'LPG_WH#1'],
                                     ['ELEC_WH5', 'NG_WH#4', 'LPG_WH#4'],
                                     ['EF', 'EF', 'EF']],
                  'cooking': ['EIA_EQUIP',
                              ['ELEC_STV', 'NG_STV', 'LPG_STV'],
                              ['ELEC_STV1', 'NG_STV1', 'LPG_STV1'],
                              ['kWh/yr', 'TEff', 'TEff']],
                  'drying': ['EIA_EQUIP',
                             ['ELEC_DRY', 'NG_DRY'], ['ELEC_DRY1', 'NG_DRY1'],
                             ['ELECDRY2', 'NG_DRY2'], ['EF', 'EF']],
                  'refrigeration': ['EIA_EQUIP', 'REFR'
                                    ['RefBF#1', 'RefSF#1', 'RefTF#1'],
                                    ['RefBF#2', 'RefSF#2', 'RefTF#3'],
                                    ['kWh/yr', 'kWh/yr']],
                  'freezers': ['EIA_EQUIP', 'FREZ', ['FrzrC#1', 'FrzrU#1'],
                               ['FrzrC#2', 'FrzrU#2'], ['kWh/yr', 'kWh/yr']]}

# The basic structure of a) above for lighting technologies is:
#  'microsegments.json' tech. key: [
#   EIA file info.,
#   performance, cost, and lifetime filter name (light class and bulb type),
#   performance units (* Note: cost units are addressed separately)]
tech_eia_lt = {'linear fluorescent (T-12)': ['EIA_LT', ['LFL', 'T12'],
                                             'lm/W'],
               'linear fluorescent (T-8)': ['EIA_LT', ['LFL', 'T8'], 'lm/W'],
               'linear fluorescent (LED)': ['EIA_LT', ['LFL', 'LED'], 'lm/W'],
               'general service (incandescent)': ['EIA_LT', ['GSL', 'INC'],
                                                  'lm/W'],
               'general service (CFL)': ['EIA_LT', ['GSL', 'CFL'], 'lm/W'],
               'general service (LED)': ['EIA_LT', ['GSL', 'LED'], 'lm/W'],
               'reflector (incandescent)': ['EIA_LT', ['REF', 'INC'],
                                            'lm/W'],
               'reflector (CFL)': ['EIA_LT', ['REF', 'LED'], 'lm/W'],
               'reflector (halogen)': ['EIA_LT', ['REF', 'HAL'], 'lm/W'],
               'reflector (LED)': ['EIA_LT', ['REF', 'LED'], 'lm/W'],
               'external (incandescent)': ['EIA_LT', ['EXT', 'INC'], 'lm/W'],
               'external (CFL)': ['EIA_LT', ['EXT', 'CFL'], 'lm/W'],
               'external (high pressure sodium)': ['EIA_LT', ['EXT', 'HPS'],
                                                   'lm/W'],
               'external (LED)': ['EIA_LT', ['EXT', 'LED'], 'lm/W']}

# The basic structure of b) above is:
#  'microsegments.json' tech. key: [
#  average lifetime and range and info. source,
#  'typical' and 'best' performance and info. sources,
#  'typical' and 'best' cost and info. sources,
#   performance units]
tech_noneia = {'secondary heating (electric)': [[0, 0, 'NA'], [0, 0, 'NA'],
                                                [0, 0, 'NA'], 'COP'],
               'secondary heating (natural gas)': [[0, 0, 'NA'], [0, 0, 'NA'],
                                                   [0, 0, 'NA'], 'AFUE'],
               'secondary heating (kerosene)': [[0, 0, 'NA'], [0, 0, 'NA'],
                                                [0, 0, 'NA'], 'AFUE'],
               'secondary heating (wood)': [[0, 0, 'NA'], [0, 0, 'NA'],
                                            [0, 0, 'NA'], 'AFUE'],
               'secondary heating (LPG)': [[0, 0, 'NA'], [0, 0, 'NA'],
                                           [0, 0, 'NA'], 'AFUE'],
               'secondary heating (coal)': [[0, 0, 'NA'], [0, 0, 'NA'],
                                            [0, 0, 'NA'], 'AFUE'],
               'TV': [[0, 0, 'NA'], [0, 0, 'NA'], [0, 0, 'NA'], 'W'],
               'set top box': [[0, 0, 'NA'], [0, 0, 'NA'], [0, 0, 'NA'], 'W'],
               'DVD': [[0, 0, 'NA'], [0, 0, 'NA'], [0, 0, 'NA'], 'W'],
               'home theater & audio': [[0, 0, 'NA'], [0, 0, 'NA'],
                                        [0, 0, 'NA'], 'W'],
               'video game consoles': [[0, 0, 'NA'], [0, 0, 'NA'],
                                       [0, 0, 'NA'], 'W'],
               'desktop PC': [[0, 0, 'NA'], [0, 0, 'NA'], [0, 0, 'NA'], 'W'],
               'laptop PC': [[0, 0, 'NA'], [0, 0, 'NA'],
                             [0, 0, 'NA'], 'W'],
               'monitors': [[0, 0, 'NA'], [0, 0, 'NA'],
                            [0, 0, 'NA'], 'W'],
               'network equipment': [[0, 0, 'NA'], [0, 0, 'NA'],
                                     [0, 0, 'NA'], 'W'],
               'fans & pumps': [[0, 0, 'NA'], [0, 0, 'NA'], [0, 0, 'NA'],
                                'HP/W'],
               'ceiling fan': [[0, 0, 'NA'], [0, 0, 'NA'], [0, 0, 'NA'], 'W'],
               'dishwasher': [[0, 0, 'NA'], [0, 0, 'NA'], [0, 0, 'NA'], 'NA'],
               'other MELs': [[0, 0, 'NA'], [0, 0, 'NA'], [0, 0, 'NA'], 'NA'],
               'windows conduction': [[0, 0, 'NA'],
                                      [0, 0, 'NREL Efficiency DB'],
                                      [0, 0, 'RS Means'], 'R Value'],
               'windows solar': [[0, 0, 'NA'],
                                 [0, 0, 'NREL Efficiency DB'],
                                 [0, 0, 'RS Means'], 'SHGC'],
               'wall': [[0, 0, 'NA'], [0, 0, 'EnergyStar'],
                        [0, 0, 'RS Means'], 'R Value/sq.in.'],
               'roof': [[0, 0, 'NA'], [0, 0, 'EnergyStar'],
                        [0, 0, 'RS Means'], 'R Value/sq.in.'],
               'ground': [[0, 0, 'NA'], [0, 0, 'EnergyStar'],
                          [0, 0, 'RS Means'], 'R Value/sq.in.'],
               'infiltration': [[0, 0, 'NA'], [0, 0, 'EnergyStar'],
                                [0, 0, 'RS Means'], 'ACH'],
               'people gain': [[0, 0, 'NA'], ['NA', 'NA', 'NA'],
                               ['NA', 'NA', 'NA'], 'NA'],
               'equipment gain': [['NA', 'NA', 'NA'], ['NA', 'NA', 'NA'],
                                  ['NA', 'NA', 'NA'], 'NA']}


def walk_techdata(eia_nlt_cp, eia_nlt_l, eia_lt, tech_eia_nonlt,
                  tech_eia_lt, tech_noneia, json_dict, project_dict,
                  key_list=[]):
    """ Proceed recursively through data stored in dict-type structure
    and perform calculations at each leaf/terminal node in the data. In
    this case, the function is running through the input microsegments
    JSON levels and updating the values at each of the technology-level leaf
    nodes to the correct cost, performance, and lifetime information for that
    technology """

    for key, item in json_dict.items():

        # If there are additional levels in the dict, call the function
        # again to advance another level deeper into the data structure
        if isinstance(item, dict):
            walk_techdata(eia_nlt_cp, eia_nlt_l, eia_lt, tech_eia_nonlt,
                          tech_eia_lt, tech_noneia, item, key_list + [key])
        # If a leaf node has been reached, finish constructing the key
        # list for the current location and update the data in the dict
        else:
            leaf_node_keys = key_list + [key]
            # Update data
            [data_dict, eia_nlt_cp, eia_nlt_l, eia_lt] = \
                list_generator_techdata(eia_nlt_cp, eia_nlt_l,
                                        eia_lt, tech_eia_nonlt,
                                        tech_eia_lt, tech_noneia,
                                        leaf_node_keys, project_dict)
            # Set dict key to extracted data
            json_dict[key] = data_dict

    # Return updated dict
    return json_dict


def list_generator_techdata(eia_nlt_cp, eia_nlt_l, eia_lt, tech_eia_nonlt,
                            tech_eia_lt, tech_noneia, leaf_node_keys,
                            project_dict):
    """ Given an empty leaf node for a specific technology in the microsegments
    JSON, as well as projected technology costs, performance, and lifetimes
    from EIA and internal BTO analysis, find the appropriate data for the
    specific technology, record it in a performance/cost/lifetime
    dict, and update the leaf node value to this dict """

    # Initialize a dict with performance, cost, and lifetime information to
    # be updated for a given technology in the microsegments JSON input
    data_dict = {'performance': None,
                 'installed cost': None,
                 'lifetime': None}

    # Identify the census division to be used in filtering EIA data as the
    # first level in the dict key hierarchy of the input microsegments JSON
    cdiv = leaf_node_keys[0]

    # Identify the fuel type to be used in filtering EIA data as the
    # third level in the dict key hierarchy of the input microsegments JSON
    fuel_type = leaf_node_keys[2]

    # Identify the technology to be used in filtering EIA data as the last
    # level in the dict key hierarchy of the input microsegments JSON
    tech_dict_key = leaf_node_keys[-1]

    # Flag a special case of a 'non-specific' technology type, which is
    # unique to the secondary heating end use.  Identify which type of
    # secondary heating technology is being filtered for based on the
    # fuel type of the microsegment as defined above.  Note that
    # a 'non-specific' technology type only applies to electric and natural
    # gas secondary heating in the microsegments JSON
    if tech_dict_key == "non-specific":
        if fuel_type == "electric (grid)":
            tech_dict_key = "secondary heating (electric)"
        else:
            tech_dict_key = "secondary heating (natural gas)"

    # Determine which technology dict from the beginning of the script
    # to use in determining filtering information
    if tech_dict_key in tech_eia_nonlt.keys():
        tech_dict = tech_eia_nonlt
    elif tech_dict_key in tech_eia_lt.keys():
        tech_dict = tech_eia_lt
    elif tech_dict_key in tech_noneia.keys():
        tech_dict = tech_noneia
    else:
        raise KeyError('No tech dict key found for given technology!')

    # Access the correct technology filtering information based on the
    # tech_dict_key developed in the above few lines
    filter_info = tech_dict[tech_dict_key]

    # Update dict values given filtering information

    # In first case (EIA non-lighting technology), run through technology info.
    # found in EIA 'rsmeqp.txt' and 'rsclass.txt' files via tech_eia_nonlt dict
    if filter_info[0] == 'EIA_EQUIP':

        # Initialize matched row lists for 'typical' and 'best' performance
        # and cost information for the non-lighting technology in the EIA files
        match_list_typ_perfcost = []
        match_list_best_perfcost = []

        # Initialize a list for recording and removing matched rows
        rows_to_remove_nlt_cp = []
        rows_to_remove_nlt_l = []

        # Loop through the EIA non-lighting technology performance and cost
        # data, searching for a match with the desired technology
        for (idx, row) in enumerate(eia_nlt_cp):

            # Check whether the looped row concerns the census division
            # currently being updated in the microsegments JSON; if
            # it does, proceed further (note that only EIA non-lighting
            # technology cost/performance info. is broken down by census
            # division); otherwise, loop to next row
            if row['CDIV'] == mseg_cdiv_translate[cdiv]:

                # Set up each row in the array as a 'compareto' string for use
                # in a regex comparison below
                compareto = str(row)

                # In some cases, a technology will have multiple variants for
                # performance/cost and/or lifetime information in the EIA data.
                # These variants may be based on a) technology configuration
                # (i.e. 'FrzrC#1' (chest), 'FrzrU#1' (upright)) or b) fuel type
                # (i.e., 'ELEC_STV' (electric stove), 'NG_STV' (natural gas
                # stove) for cooking).  In case a), all tech. configurations
                # will be included in the filter, and single performance and
                # cost values will be averaged across these configurations. In
                # case b), the filtering information for cost, performance, and
                # lifetime will be each comprised of multiple elements (i.e.,
                # cost will be specified as [cost electric, cost natural gas,
                # cost other fuel]). Note that these elements are ordered by
                # fuel type: electric, then natural gas, then 'other' fuel

                # Determine filtering names for case a) in comment above
                if tech_dict_key in ['refrigeration', 'freezers']:
                    # Note: refrigeration has three technology configuration
                    # variants for filtering (bottom freezer, side freezer,
                    # top freezer)
                    if tech_dict_key == 'refrigeration':
                        typ_filter_name = '(' + filter_info[2][0] + '|' + \
                            filter_info[2][1] + '|' + filter_info[2][2] + ')'
                        best_filter_name = '(' + filter_info[3][0] + '|' + \
                            filter_info[3][1] + '|' + filter_info[3][2] + ')'
                    # Note: refrigeration has two technology configuration
                    # variants for filtering (chest, upright)
                    else:
                        typ_filter_name = '(' + filter_info[2][0] + '|' + \
                            filter_info[2][1] + ')'
                        best_filter_name = '(' + filter_info[3][0] + '|' + \
                            filter_info[3][1] + ')'
                # Determine filtering names for case b) in comment above
                elif len(filter_info[2]) > 1:
                    # Filter names determined by fuel type (electricity,
                    # natural gas, and 'other')
                    if fuel_type == "electricity (grid)":
                        typ_filter_name = filter_info[2][0]
                        best_filter_name = filter_info[3][0]
                    elif fuel_type == "natural gas":
                        typ_filter_name = filter_info[2][1]
                        best_filter_name = filter_info[3][1]
                    elif len(filter_info[2] == 3):
                        typ_filter_name = filter_info[2][2]
                        best_filter_name = filter_info[3][2]
                # Determine filtering names for technologies with only one
                # configuration/fuel type
                else:
                    typ_filter_name = filter_info[2]
                    best_filter_name = filter_info[3]

                # Construct the full non-lighting technology performance and
                # cost filtering info. to compare against the current numpy row
                # in a regex for 'typical' and 'best' performance/cost cases
                comparefrom_typ = '.+' + typ_filter_name
                comparefrom_best = '.+' + best_filter_name

                # Check for a match between the 'typical' performance and cost
                # filtering information and the row
                match_typ = re.search(comparefrom_typ, compareto)
                # If there is no match for the 'typical' performance and cost
                # case, check for a 'best' case performance and cost match
                if not match_typ:
                    match_best = re.search(comparefrom_best, compareto)

                # If there was a match for the 'typical' performance and cost
                # cases, append the row to the match lists initialized for
                # non-lighting technologies above.  Do the same if there was a
                # match for the 'best' performance and cost case
                if match_typ:
                    match_list_typ_perfcost.append(row)
                    # Record any matched rows for removal
                    rows_to_remove_nlt_cp.append(idx)
                elif match_best:
                    match_list_best_perfcost.append(row)
                    # Record any matched rows for removal
                    rows_to_remove_nlt_cp.append(idx)

            # Reduce array by removing all matched rows
            eia_nlt_cp = numpy.delete(eia_nlt_cp, rows_to_remove_nlt_cp, 0)

        # Once the 'typical' and 'best' performance and cost arrays have been
        # constructed for the given non-lighting technology, rearrange the
        # projection year info. for these data in the array to be consistent
        # with the 'mseg.py' microsegment projection years (i.e., {"2009": XXX,
        # "2010": XXX, etc.}) using the 'fill_years_nlt' function
        [perf_typ, cost_typ] = fill_years_nlt(match_list_typ_perfcost,
                                              project_dict, tech_dict_key)
        [perf_best, cost_best] = fill_years_nlt(match_list_best_perfcost,
                                                project_dict, tech_dict_key)

        # Set units of the performance information (cost units set later)
        perf_units = filter_info[4]

        # Loop through the EIA non-lighting technology lifetime
        # data, searching for a match with the desired technology
        for (idx, row) in enumerate(eia_nlt_l):

            # Set up each row in the array as a 'compareto' string for use
            # in a regex comparison below
            compareto = str(row)
            # Construct the full non-lighting technology lifetime filtering
            # information to compare against the current numpy row in a regex
            comparefrom = '.+' + filter_info[1]

            # Check for a match between the filtering information and row
            match = re.search(comparefrom, compareto)
            # If there was a match, draw the final technology lifetime
            # info. (average and range) from the appropriate column in the row
            if match:
                life_avg = (row['LIFE_MAX'] + row['LIFE_MIN']) / 2
                life_range = row['LIFE_MAX'] - life_avg
                # Record any matched rows for removal
                rows_to_remove_nlt_l.append(idx)

            # Reduce array by removing all matched rows
            eia_nlt_l = numpy.delete(eia_nlt_l, rows_to_remove_nlt_l, 0)

        # Set source to EIA AEO for these non-lighting technologies
        [perf_source, cost_source, life_source] = ['EIA AEO' for n in range(3)]

    # In second case (EIA lighting technology), run through technology info.
    # found in EIA 'rsmlgt.txt' and "rsclass.txt" files via tech_eia_lt dict
    elif filter_info[0] == 'EIA_LT':

        # Initialize matched row list for performance, cost, and lifetime
        # information for the lighting technology in the EIA files
        match_list = []

        # Initialize a list for recording and removing matched rows
        rows_to_remove_lt = []

        # Loop through the EIA lighting technology performance, cost, and
        # lifetime data, searching for a match with the desired technology
        for (idx, row) in enumerate(eia_lt):

            # Set up each row in the array as a 'compareto' string for use
            # in a regex comparison below
            compareto = str(row)
            # Construct the full lighting technology performance, cost, and
            # lifetime filtering info. to compare against current numpy row in
            # a regex
            comparefrom = '.+' + filter_info[1][0] + '.+' + filter_info[1][1]

            # Check for a match between the filtering information and row
            match = re.search(comparefrom, compareto)
            # If there was a match, append the row to the match list
            # initialized for lighting technologies above
            if match:
                match_list.append(row)
                # Record any matched rows for removal
                rows_to_remove_lt.append(idx)

            # Reduce array by removing all matched rows
            eia_lt = numpy.delete(eia_lt, rows_to_remove_lt, 0)

        # Once the performance, cost, and lifetime arrays have been constructed
        # for the given lighting technology, rearrange the projection year
        # information for these data in the array to be consistent with the
        # 'mseg.py' microsegment projection years (i.e., {"2009": XXX, "2010":
        # XXX, etc.}) using the 'fill_years_lt' function
        [perf_typ, cost_typ, life_avg] = fill_years_lt(match_list,
                                                       project_dict)

        # No 'best' technology performance or cost data are available from EIA
        # for lighting technologies, so set these variables to 'NA'.  Also set
        # lifetime range to 'NA' for lighting techologies, since only a single
        # lifetime number is provided by EIA (presumably an average lifetime)
        [perf_best, cost_best, life_range] = ['NA' for n in range(3)]

        # Set units of the performance information (cost units set later)
        perf_units = filter_info[3]

        # Set source to EIA AEO for these lighting technologies
        [perf_source, cost_source, life_source] = ['EIA AEO' for n in range(3)]

    # In third case (BTO-defined technology), run through technology info.
    # directly specified in tech_noneia above
    else:
        # Set all performance, cost, and lifetime information to that specified
        # in 'tech_noneia' towards the beginning of this script.
        [perf_typ, perf_best, perf_units, perf_source, cost_typ, cost_best,
         cost_source, life_avg, life_range, life_source] = [
            dict.fromkeys(project_dict.keys(), n) for n in [
                filter_info[2][0], filter_info[2][1], filter_info[4],
                filter_info[2][2], filter_info[3][0], filter_info[3][1],
                filter_info[3][2], filter_info[0][0], filter_info[0][1],
                filter_info[0][2]]]

    # Set cost units for the given technology based on whether it is a
    # "demand" type or "supply" type technology
    if "demand" in leaf_node_keys:
            cost_units = '$/sf'
    else:
        cost_units = '$/unit'

    # Based on above search results, update the dict with performance, cost,
    # and lifetime information for the given technology

    # Update performance information
    data_dict['performance'] = {'typical': perf_typ,
                                'best': perf_best,
                                'units': perf_units,
                                'source': perf_source}
    # Update cost information
    data_dict['installed cost'] = {'typical': cost_typ,
                                   'best': cost_best,
                                   'units': cost_units,
                                   'source': cost_source}
    # Update lifetime information
    data_dict['lifetime'] = {'average': life_avg,
                             'range': life_range,
                             'units': 'years',
                             'source': life_source}

    # Return updated technology performance, cost, and lifetime information
    return [data_dict, eia_nlt_cp, eia_nlt_l, eia_lt]


def fill_years_nlt(match_list, project_dict, tech_dict_key):
    """ Reconstruct EIA performance, cost, and lifetime projections for
    non-lighting technologies into a dict containing information for each
    projection year used for microsegments in 'mseg.py' """

    # For the special non-lighting technology cases of refrigeration and
    # freezers, any given year will have multiple technology configurations.
    # The next few lines average the performance and cost figures across those
    # configurations to yield just one number for each in each year
    if tech_dict_key in ['refrigeration', 'freezers']:

        # Initialize a new list to append averaged performance/cost information
        # to
        match_list_new = []

        # Loop through all the rows in the match_list array and average
        # performance and cost figures by year; then append to match_list_new
        for x in sorted(numpy.unique(match_list['START_EQUIP_YR'])):
            match_list_new.append(
                (x, numpy.average(
                    match_list[numpy.where(
                        match_list['START_EQUIP_YR'] == x)]['BASE_EFF']),
                    numpy.average(
                    match_list[numpy.where(
                        match_list['START_EQUIP_YR'] == x)]['INST_COST'])))

        # Once all the averaged figures are available, reconstruct this
        # information into a numpy array with named columns for later use
        # (* NOTE: it may be possible to perform the above averaging on the
        # initial match_list array above without converting it to a list; this
        # should be investigated further)
        match_list = numpy.array(match_list_new,
                                 dtype=[('START_EQUIP_YR', '<i8'),
                                        ('BASE_EFF', '<f8'),
                                        ('INST_COST', '<f8')])

    # Update performance information for projection years
    perf = stitch(match_list, project_dict, 'BASE_EFF')
    # Update performance information for projection years
    cost = stitch(match_list, project_dict, 'INST_COST')

    # Return updated EIA performance and cost information for
    # non-lighting technologies
    return [perf, cost]


def fill_years_lt(match_list, project_dict):
    """ Reconstruct EIA performance, cost, and lifetime projections for
    lighting technologies into a dict containing information for each
    projection year used for microsegments in 'mseg.py' """

    # Update performance information for projection years
    perf = stitch(match_list, project_dict, 'BASE_EFF')
    # Update cost information for projection years
    cost = stitch(match_list, project_dict, 'INST_COST')
    # Update lifetime information for projection years
    life = stitch(match_list, project_dict, 'LIFE_HRS') / 61194  # Hrs -> yrs

    # Return updated EIA performance, cost, and lifetime information
    # for lighting technologies
    return [perf, cost, life]


def stitch(input_array, project_dict, col_name):
    """ Given EIA performance, cost, and lifetime projections for a technology
    between a certain series of time periods (i.e. 2010-2014, 2014-2020,
    2020-2040), reconstruct this information in a dict annually for the
    projection period used in "mseg.py" (i.e. {"2009": XXX, "2010": XXX, ...,
    "2040": XXX}) """

    # Initialize output dict which will contain EIA performance, cost,
    # or lifetime information continuous across each year of the
    # projection horizon
    output_dict = {}

    # Initialize a previous year value indicator to be used
    # in cases where the input array does not contain information
    # for a given year in the projection horizon
    prev_yr_val = None

    # Loop through each year of the projection and fill in information
    # from the appropriate row and column from the input array
    for (yr_ind, yr) in enumerate(project_dict.keys()):
        # Reduce the input array to only the row concerning the year being
        # looped through (if this year exists in the 'START_EQUIP_YR' column)
        array_reduce = input_array[input_array['START_EQUIP_YR'] == yr]

        # If a row has been discovered for the looped year, draw output
        # information from column in that row keyed by col_name input
        if len(array_reduce) > 0:
            if len(array_reduce) == 1:
                output_dict[yr] = array_reduce[col_name]
            else:
                raise ValueError('Multiple identical years in filtered array!')
        # If no row has been discovered for the looped year and we are not in
        # the first year of the loop, set output information to that of the
        # previously looped year
        elif yr_ind != 0:
            output_dict[yr] = prev_yr_val
        # If no row has been discovered for the looped year and we are in the
        # first year of the loop, set output information to that of the row
        # with a 'START_EQUIP_YR' that is closest to the looped year
        else:
            # Find the row(s) where the absolute difference between the loop
            # year and value for the 'START_EQUIP_YR' column is smallest
            array_close_ind = numpy.where(abs(int(yr) -
                                          input_array['START_EQUIP_YR']) ==
                                          min(abs(int(yr) -
                                              input_array['START_EQUIP_YR'])))
            # If only one row has been found above, draw output information
            # from the column in that row keyed by col_name input
            if len(array_close_ind) == 1:
                output_dict[yr] = input_array[array_close_ind][col_name]
            # If multiple rows have been found above, draw output information
            # from the column in the first of these rows keyed by col_name
            # input
            else:
                output_dict[yr] = input_array[array_close_ind][0][col_name]

        # Update previous year value indicator to the output information for
        # the current loop
        prev_yr_val = output_dict[yr]

    # Return output dictionary with performance, lifetime, or cost information
    # updated across all projection years
    return output_dict


def main():
    """ Import EIA cost/performance and lifetime files; run through these
    files, using their information to fill in a dict with technology-level
    cost, performance, and lifetime information (where EIA data do not exist
    for a given technology, fill information in with BTO numbers); before
    exporting updated dict to a JSON, translate the dict from a census division
    breakdown to a climate zone breakdown """

    # Import EIA non-lighting residential cost and performance data
    eia_nlt_cp = numpy.genfromtxt(r_nlt_costperf, names=r_nlt_cp_names,
                                  dtype=None, skip_header=20)

    # Import EIA non-lighting residential lifetime data
    eia_nlt_l = numpy.genfromtxt(r_nlt_life, names=r_nlt_l_names,
                                 dtype=None, skip_header=19)

    # Import EIA lighting residential cost, performance and lifetime data
    eia_lt = numpy.genfromtxt(r_lt_all, names=r_lt_names, dtype=None,
                              skip_header=35, skip_footer=54)

    # Establish the projection horizon to be consistent with the "mseg.py"
    # routine
    aeo_min = mseg.aeo_years_min
    aeo_max = aeo_min + (mseg.aeo_years - 1)
    aeo_years = [str(i) for i in range(aeo_min, aeo_max + 1)]
    project_dict = dict.fromkeys(aeo_years)

    # Import microsegments JSON file as a dictionary structure
    with open(json_in, 'r') as jsi:
        msjson = json.load(jsi)

    # Run through microsegment JSON levels, determine technology leaf node
    # info. to mine from the imported data, and update nodes with this info.
    updated_data = walk_techdata(eia_nlt_cp, eia_nlt_l, eia_lt,
                                 tech_eia_nonlt, tech_eia_lt, tech_noneia,
                                 msjson, project_dict)

    # Convert the updated data from census division to climate breakdown
    final_data = mseg.clim_converter(updated_data, mseg.res_convert_array)

    # Write the updated dict of data to a new JSON file
    with open(json_out, 'w') as jso:
        json.dump(final_data, jso, indent=4)


if __name__ == '__main__':
    main()
