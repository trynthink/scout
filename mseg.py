#!/usr/bin/env python3

# import sys
import re
import numpy
import json

# Set AEO time horizon in years (used in "value_listfinder" function
# below to check correctness of microsegment value lists)
aeo_years = 32

# Identify files to import for conversion
EIA_res_file = 'RESDBOUT.txt'
jsonfile = 'microsegments_test.json'
res_tloads = 'Res_TLoads_Final.txt'
res_climate_convert = 'Res_Cdiv_Czone_ConvertTable_Final.txt'
com_tloads = 'Com_TLoads_Final.txt'
com_climate_convert = 'Com_Cdiv_Czone_ConvertTable_Final.txt'

# Define a series of dicts that will translate imported JSON
# microsegment name to AEO microsegment(s)

# Census division dict
cdivdict = {'new england': 1,
            'mid atlantic': 2,
            'east north central': 3,
            'west north central': 4,
            'south atlantic': 5,
            'east south central': 6,
            'west south central': 7,
            'mountain': 8,
            'pacific': 9,
            'NA': ''}

# Building type dict (residential)
bldgtypedict = {'single family home': 1,
                'multi family home': 2,
                'mobile home': 3,
                'all/NA': ''}

# Fuel type dict
fueldict = {'electricity (on site)': 'SL',
            'electricity (grid)': 'EL',
            'natural gas': 'GS',
            'distillate': 'DS',
            'other fuel': ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD'),
            'NA': ''}
# Note that currently in RESDBOUT.txt, electric resistance heaters are
# categorized under GE (geothermal) fuel. SL (solar) fuel is attached
# to water heating, but the end technology is only listed as "Solar",
# which will not currently be included in our analysis.

# End use dict
endusedict = {'heating': 'HT',
              'secondary heating': ('SH', 'OA'),
              'cooling': 'CL',
              'fans & pumps': 'FF',
              'ceiling fan': 'CFN',
              'lighting': 'LT',
              'water heating': 'HW',
              'refrigeration': 'RF',
              'cooking': 'CK',
              'drying': 'DR',
              'TVs': {'TV': 'TV',
                      'set top box': 'STB',
                      'DVD': 'DVD',
                      'home theater & audio': 'HTS',
                      'video game consoles': 'VGC'},
              'computers': {'desktop PC': 'DPC',
                            'laptop PC': 'LPC',
                            'monitors': 'MON',
                            'network equipment': 'NET'},
              'other (grid electric)': {'clothes washing': 'CW',
                                        'dishwasher': 'DW',
                                        'freezers': 'FZ',
                                        'other MELs': ('BAT', 'COF', 'DEH',
                                                       'EO', 'MCO', 'OA',
                                                       'PHP', 'SEC', 'SPA')},
              'NA': ''}

# Technology types (supply) dict
technology_supplydict = {'solar WH': 'SOLAR_WH',
                         'boiler (electric)': 'ELEC_RAD',
                         'ASHP': 'ELEC_HP',
                         'GSHP': 'GEO_HP',
                         'central AC': 'CENT_AIR',
                         'room AC': 'ROOM_AIR',
                         'linear fluorescent': 'LFL',
                         'general service': 'GSL',
                         'reflector': 'REF',
                         'external': 'EXT',
                         'furnace (NG)': 'NG_FA',
                         'boiler (NG)': 'NG_RAD',
                         'NGHP': 'NG_HP',
                         'furnace (distillate)': 'DIST_FA',
                         'boiler (distillate)': 'DIST_RAD',
                         'furnace (kerosene)': 'KERO_FA',
                         'furnace (LPG)': 'LPG_FA',
                         'stove (wood)': 'WOOD_HT',
                         'resistance': 'GE2',
                         'secondary heating (kerosene)': 'KS',
                         'secondary heating (LPG)': 'LG',
                         'secondary heating (wood)': 'WD',
                         'secondary heating (coal)': 'CL',
                         'non-specific': '',
                         'NA': ''}

# Technology types (demand) dict
technology_demanddict = {'windows conduction': 'WIND_COND',
                         'windows solar': 'WIND_SOL',
                         'wall': 'WALL',
                         'roof': 'ROOF',
                         'ground': 'GRND',
                         'infiltration': 'INFIL',
                         'people gain': 'PEOPLE',
                         'equipment gain': 'EQUIP'}


def json_translator(msdata):
    """ Determine filtering list for finding information in .txt file parse """
    # Translate a heating/cooling demand technology case into a filter list
    # tuple (supply_filter, demand_filter)
    if 'demand' in msdata:
        # Check for the special case of a demand technology of the
        # "other fuel - secondary heating" type (has unique levels)
        if 'other fuel' and 'secondary heating' in msdata:
            return ([endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]], technology_demanddict[msdata[7]])
        else:
            return ([endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]]], technology_demanddict[msdata[6]])
    # Translate a heating/cooling supply technology case into a filter list
    elif 'supply' in msdata:
        # Check for the special case of a supply technology of the
        # "other fuel - secondary heating" type (has unique levels)
        if 'other fuel' and 'secondary heating' in msdata:
            return [endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]]  # Note: "non-specific" supply technology for this case
        else:
            return [endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[6]]]
    # Translate an end sub use case into a filter list
    elif msdata[4] is not 'NA':
        return [endusedict[msdata[3]][msdata[4]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]]
    # Translate all other technologies into a filter lis
    else:
        return [endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]]


def filter_formatter(txt_filter):
    """ Given a filtering list for a microsegment, format into a
    string that can be entered into a regex comparsion in
    value_listfinder function """

    # Set base "supply" filter string
    supply_filter = '.*'

    # Determine whether we are updating a "demand" microsegment by whether or
    # not current function input is a tuple.  If so, use first tuple element
    # as filter for EIA .txt file, and second tuple element as filter for
    # residential thermal load components .txt file.
    if isinstance(txt_filter, tuple):
        txt_filter_loop = txt_filter[0]
        demand_filter = txt_filter[1]
    else:
        txt_filter_loop = txt_filter
        demand_filter = 'NA'

    for element in txt_filter_loop:  # Run through elements of the filter list
        # If element is a tuple and not on the "demand" technology level, join
        # the tuple into a single string, put brackets around it for regex
        # comparison
        if isinstance(element, tuple):
            newelement = '|'.join(element)
            supply_filter = supply_filter + '(' + newelement + ' ).+'
        # If element is a number and not on the "demand" technology level, turn
        # into a string for regex comparison
        elif isinstance(element, int):
            newelement = str(element)
            supply_filter = supply_filter + newelement + '.+'
        # If element is a string and not on the "demand" technology level, add
        # it to the filter list without modification
        elif isinstance(element, str):
            supply_filter = supply_filter + element + '.+'
        else:
            print('Error in list finder form!')

        comparefrom = (supply_filter, demand_filter)
        return comparefrom


def list_condenser(group_list):
    """ Given a list of energy data representing multiple technology
    types projected out over the AEO time horizon, condense into a list
    that is length of horizon """
    # Establish a baseline chunk of projected energy data to add to
    # (i.e. 32 years projected energy data for a given technology)
    group_base = group_list[0:aeo_years]
    # Establish how many chunks of data will be accessed
    construct_limit = int(float(len(group_list)) / float(aeo_years))
    # Break original list into chunks and add to new master list that
    # is length of AEO time horizon
    for newrows in range(construct_limit - 1):
        startrow = aeo_years * (newrows + 1)
        endrow = startrow + aeo_years
        newmat = group_list[startrow:endrow]
        group_base = [group_base[i] + newmat[i] for i in range(aeo_years)]
    # Return final list
    return group_base


def txt_parser(mstxt, comparefrom, command_string):
    """ Given a numpy array and information about what rows we want from it,
    match the rows and then remove them from the array.  If command_string
    input = 'Reduce', only remove the rows; if command_string
    input = 'Record & Reduce', also record matched rows """
    # Determine whether we are just removing numpy array rows or also recording them
    record_reduce = re.search(command_string, 'Record & Reduce', re.IGNORECASE)
    # Define intial list of rows to remove from mstxt input
    rows_to_remove = []

    # If recording and removing rows, define initial stock/energy lists
    if record_reduce:
        group_stock = []
        group_energy = []

    # Loop through the numpy input array rows, match to 'comparefrom' input
    for idx, txtlines in enumerate(mstxt):
            # Set up 'compareto' list
            compareto = str(txtlines)
            # Establish the match
            match = re.search(comparefrom, compareto)
            # If there's a match, append line to stock/energy lists for
            # the current microsegment
            if match:
                # Record additional row index to delete
                rows_to_remove.append(idx)
                # If recording and removing rows, record discovered energy/stock info.
                if record_reduce:
                    group_stock.append(txtlines[6])
                    group_energy.append(txtlines[7])

    # Delete matched rows from numpy array of txt data
    mstxt_reduced = numpy.delete(mstxt, rows_to_remove, 0)

    # Set up proper function return based on command_string input
    if record_reduce:
        parse_return = (group_energy, group_stock, mstxt_reduced)
    else:
        parse_return = mstxt_reduced

    return parse_return


def list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata):
    """ Given filtering list for a microsegment, find rows in *.txt
    files to reference in determining associated energy data, append
    energy data to a new list """

    # Find the corresponding txt filtering information
    txt_filter = json_translator(filterdata)

    # Set up 'compare from' list (based on .txt file)
    comparefrom = filter_formatter(txt_filter)[0]

    # Run through text file and add all appropriate lines to the empty list
    # Check whether current microsegment is a heating/cooling "demand"
    # technology (handled differently)
    if 'demand' in txt_filter:
        # *** Fill in as we compile demand information ***
        return [{'stock': 'NA', 'energy': 999999999999999}, mstxt_demand]  # Use this placeholder for now
    else:
        # Given input numpy array and 'compare from' list, return energy/stock
        # projection lists and reduced numpy array (with matched rows removed)
        group_energy = txt_parser(mstxt_supply, comparefrom, 'Record & Reduce')[0]
        group_stock = txt_parser(mstxt_supply, comparefrom, 'Record & Reduce')[1]
        mstxt_supply = txt_parser(mstxt_supply, comparefrom, 'Record & Reduce')[2]

        # Given the discovered lists of energy/stock values, check to ensure
        # length = # of years currently projected by AEO. If not,
        # execute list_condenser function
        # to arrive at final lists
        if len(group_energy) is not aeo_years:
            if len(group_energy) % aeo_years == 0:
                group_energy = list_condenser(group_energy)
                group_stock = list_condenser(group_stock)
            else:
                print('Error in length of discovered list!')

        # Return combined stock and energy use values, along with
        # updated version of EIA data with already matched data removed
        return [{'stock': group_stock, 'energy': group_energy}, mstxt_supply]


def mseg_updater_main():
    """ Import .txt and JSON files; run through JSON objects; find
    analogous .txt information; replace JSON values; update JSON """
    # Import EIA RESDBOUT.txt file
    mstxt_supply = numpy.genfromtxt(EIA_res_file, names=True, delimiter='\t', dtype=None)
    # Set RESDBOUT.txt list for separate use in "demand" microsegments
    mstxt_demand = mstxt_supply
    # Set thermal loads .txt file (*currently residential)
    mstxt_loads = numpy.genfromtxt(res_tloads, names=True, delimiter='\t', dtype=None)

    # Import JSON file and run through updating scheme
    with open(jsonfile, 'r') as js:
        msjson = json.load(js)
        # Run through JSON objects, determine replacement information
        # to mine from .txt file, and make the replacement

        # Building level
        for cdiv in msjson:
            # Fuel level
            for bldgtype in msjson[cdiv]:
                # End use level
                for fueltype in msjson[cdiv][bldgtype]:
                    # Technology level
                    for endusetype in msjson[cdiv][bldgtype][fueltype]:
                        # Check whether there are more levels for given
                        # microsegment; if not, end loop
                        if msjson[cdiv][bldgtype][fueltype][endusetype]:
                            # Heating/cooling technology sub-level
                            for techtype in msjson[cdiv][bldgtype][fueltype][endusetype]:
                                # Check whether there are more levels for given
                                # microsegment, if not end loop
                                if msjson[cdiv][bldgtype][fueltype][endusetype][techtype]:
                                    for heatcooltechtype in msjson[cdiv][bldgtype][fueltype][endusetype][techtype]:
                                        # Check whether there are more levels
                                        # (will be for secondary heating -
                                        # "other" fuel), if not end loop
                                        if msjson[cdiv][bldgtype][fueltype][endusetype][techtype][heatcooltechtype]:
                                            for heatcooltechtypesub in msjson[cdiv][bldgtype][fueltype][endusetype][techtype][heatcooltechtype]:
                                                filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', techtype, heatcooltechtype, heatcooltechtypesub]
                                                # Replace initial json value
                                                # for microsegment with list
                                                [data_dict, mstxt_supply] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                                                msjson[cdiv][bldgtype][fueltype][endusetype][techtype][heatcooltechtype][heatcooltechtypesub] = data_dict
                                        else:
                                            filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', techtype, heatcooltechtype]
                                            [data_dict, mstxt_supply] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                                            msjson[cdiv][bldgtype][fueltype][endusetype][techtype][heatcooltechtype] = data_dict
                                else:
                                    # Check whether the given technology is handled as its own end use in AEO (As an
                                    # example: While our microsegments JSON currently considers DVDs to be a technology
                                    # type within a "TVs" end use category, AEO handles "DVDs" as an end use)
                                    if isinstance(endusedict[endusetype], dict):
                                        # Set subendusetype to the tech type to
                                        # reconcile JSON/txt difference in
                                        # handling
                                        subendusetype = techtype
                                        filterdata = [cdiv, bldgtype, fueltype, endusetype, subendusetype, 'NA', 'NA']
                                        [data_dict, mstxt_supply] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                                        msjson[cdiv][bldgtype][fueltype][endusetype][subendusetype] = data_dict
                                    else:
                                        filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', techtype, 'NA']
                                        [data_dict, mstxt_supply] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                                        msjson[cdiv][bldgtype][fueltype][endusetype][techtype] = data_dict
                        else:
                            filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', 'NA', 'NA']
                            [data_dict, mstxt_supply] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                            msjson[cdiv][bldgtype][fueltype][endusetype] = data_dict
    # Return the updated json
    # print(msjson)
    return msjson


if __name__ == '__main__':
    mseg_updater_main()
