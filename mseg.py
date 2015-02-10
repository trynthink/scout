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
            'other': ('LG', 'KS', 'CL', 'SL', 'GE', 'NG', 'WD'),
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
                                                       'EO', 'FP', 'MCO', 'OA',
                                                       'PHP', 'SEC', 'SPA')},
              'other (non electric)': {'fuel pumps': 'FP'},
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
    if 'demand' in msdata:
        return [endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_demanddict[msdata[6]], 'demand']
    # Translate a heating/cooling supply technology case into a filter list
    elif 'supply' in msdata:
        return [endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[6]]]
    # Translate an end sub use case into a filter list
    elif msdata[4] is not 'NA':
        return [endusedict[msdata[3]][msdata[4]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]]
    # Translate all other technologies into a filter lis
    else:
        return [endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]]


def value_listfinder_filterformat(txt_filter):
    """ Given a filtering list for a microsegment, format into a
    string that can be entered into a regex comparsion in
    value_listfinder function """
    # Set base comparefrom string
    comparefrom = '.*'
    for element in txt_filter:  # Run through all elements of the filter list
        # If element is a tuple, join the tuple into a single string,
        # put brackets around it for regex comparison
        if isinstance(element, tuple):
            newelement = ' |'.join(element)
            comparefrom = comparefrom + '(' + newelement + ' ).+'
        # If element is a number, turn into a string for regex comparison
        elif isinstance(element, int):
            newelement = str(element)
            comparefrom = comparefrom + newelement + '.+'
        # If element is a string, add it to the list without modification
        elif isinstance(element, str):
            comparefrom = comparefrom + element + '.+'
        # If element is something else, print error
        else:
            print('Error in list finder form!')
    return comparefrom


def value_listfinder_listcondense(group_list):
    """ Given a list of energy data representing multiple technology
    types projected out over the AEO time horizon, condense into a list
    that is length of horizon """
    # Establish a baseline chunk of projected energy data to add to
    # (i.e. 32 years projected energy data for a given technology)
    group_base = group_list[0:aeo_years]
    # Establish how many chunks of data will be accessed
    construct_limit = int(float(len(group_list))/float(aeo_years))
    # Break original list into chunks and add to new master list that
    # is length of AEO time horizon
    for newrows in range(construct_limit-1):
        startrow = aeo_years*(newrows+1)
        endrow = startrow + aeo_years
        newmat = group_list[startrow:endrow]
        group_base = [group_base[i] + newmat[i] for i in range(aeo_years)]
    # Return final list
    return group_base


# Note: in the future, will need to add a third input (mstxt_demand) to
# provide thermal load components data
def value_listfinder(mstxt_supply, txt_filter):
    """ Given filtering list for a microsegment, find rows in *.txt
    files to reference in determining associated energy data, append
    energy data to a new list """
    # Define initial stock/energy lists
    group_stock = []
    group_energy = []

    # Run through text file and add all appropriate lines to the empty list
    # Check whether current microsegment is a heating/cooling "demand"
    # technology (handled differently)
    if 'demand' in txt_filter:
        # *** Fill in as we compile demand information ***
        return 999999999999999  # Use this placeholder for now
    else:
        for txtlines in mstxt_supply:
            # Set up 'compare to' list
            compareto = str(txtlines)
            # Set up 'compare from' list (based on .txt file)
            comparefrom = value_listfinder_filterformat(txt_filter)
            # Establish the match
            match = re.search(comparefrom, compareto)
            # If there's a match, append line to stock/energy lists for
            # the current microsegment
            if match:
                group_stock.append(txtlines[6])
                group_energy.append(txtlines[7])
        # Given the discovered lists of values, check to ensure
        # length = # of years currently projected by AEO.  If not,
        # execute value_listfinder_listcondense function
        # to arrive at final lists
        if len(group_energy) is not aeo_years:
            if len(group_energy) % aeo_years == 0:
                group_energy = value_listfinder_listcondense(group_energy)
                group_stock = value_listfinder_listcondense(group_stock)
            else:
                print('Error in length of discovered list!')
        # Return updated group_energy
        return {'stock': group_stock, 'energy': group_energy}

# *** The below function is handled in the function above ***

# def grouper(prev_line, curr_line, consume, eqstock):
#     """ Combine data or create new data vectors where appropriate """
#     # Fragile to changes in the column definition in the input file
#     if curr_line[0:5] == prev_line[0:5]:
#         eqstock.append(curr_line[6])
#         consume.append(curr_line[-1])
#     return (consume, eqstock)


def value_replacer_listassemble(mstxt_supply, filterdata):
    """ Given filtering information from JSON, translate to filter info
    for .txt and find a list of energy values from .txt given filter """
    print(filterdata)
    # Find the corresponding txt filtering information
    txt_filter = json_translator(filterdata)
    print(txt_filter)
    # For given microsegment in txt, find a list of energy use projections
    return value_listfinder(mstxt_supply, txt_filter)


def value_replacer_main():
    """ Import .txt and JSON files; run through JSON objects; find
    analogous .txt information; replace JSON values; update JSON """
    # Import .txt file
    mstxt_supply = numpy.genfromtxt(EIA_res_file, names=True, delimiter='\t', dtype=None)
    # Import JSON file and run through updating scheme
    with open(jsonfile, 'r') as js:
        msjson = json.load(js)
        # Run through JSON objects, determine replacement information
        # to mine from .txt file, and make the replacement

        # Census level
        cdivkeys = msjson.keys()
        filterdata = []
        # Building level
        for cdiv in cdivkeys:
            bldg = msjson[cdiv]
            bldgtypekeys = bldg.keys()
            # Fuel level
            for bldgtype in bldgtypekeys:
                fuel = bldg[bldgtype]
                fueltypekeys = fuel.keys()
                # End use level
                for fueltype in fueltypekeys:
                    enduse = fuel[fueltype]
                    endusekeys = enduse.keys()
                    # Technology level
                    for endusetype in endusekeys:
                        tech = enduse[endusetype]
                        # Check whether there are more levels for given microsegment, if not end loop
                        if tech:
                            techkeys = tech.keys()
                            # Heating/cooling technology sub-level
                            for techtype in tech:
                                heatcooltech = tech[techtype]
                                # Check whether there are more levels for given microsegment, if not end loop
                                if heatcooltech:
                                    for heatcooltechtype in heatcooltech:
                                        filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', techtype, heatcooltechtype]
                                        # Replace initial json value for microsegment with list
                                        msjson[filterdata[0]][filterdata[1]][filterdata[2]][filterdata[3]][filterdata[5]][filterdata[6]] = value_replacer_listassemble(mstxt_supply, filterdata)
                                else:
                                    # Check whether the given technology is handled as its own end use in AEO (As an example: While our microsegments JSON currently
                                    # considers DVDs to be a technology type within a "TVs" end use category, AEO handles "DVDs" as an end use)
                                    if isinstance(endusedict[endusetype], dict):
                                        # Set subendusetype to the tech type to
                                        # reconcile JSON/txt difference in handling
                                        subendusetype = techtype
                                        filterdata = [cdiv, bldgtype, fueltype, endusetype, subendusetype, 'NA', 'NA']
                                        msjson[filterdata[0]][filterdata[1]][filterdata[2]][filterdata[3]][filterdata[4]] = value_replacer_listassemble(mstxt_supply, filterdata)
                                    else:
                                        filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', techtype, 'NA']
                                        msjson[filterdata[0]][filterdata[1]][filterdata[2]][filterdata[3]][filterdata[5]] = value_replacer_listassemble(mstxt_supply, filterdata)
                        else:
                            filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', 'NA', 'NA']
                            msjson[filterdata[0]][filterdata[1]][filterdata[2]][filterdata[3]] = value_replacer_listassemble(mstxt_supply, filterdata)
    # Return the updated json
    print(msjson)
    return msjson

if __name__ == '__main__':
    value_replacer_main()
