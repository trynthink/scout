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

# Define a series of regex comparison inputs that determines what we don't need
# in the imported RESDBOUT.txt file for the "supply" and "demand" portions of
# the microsegment updating routine

# Unused rows in the supply portion of the analysis
# Exclude: (Housing Stock | Switch From | Switch To | Sq. Footage | Fuel Pumps)
unused_supply_re = '^\(b\'(HS|SF|ST|SQ|FP).*'
# Unused rows in the demand portion of the analysis
# Exclude everything except: (Heating | Cooling | Secondary Heating)
unused_demand_re = '^\(b\'(?!(HT|CL|SH|OA)).*'


def json_translator(msdata):
    """ Determine filtering list for finding information in .txt file parse """
    # Translate a heating/cooling demand technology case into a filter list
    # tuple (supply_filter, demand_filter)
    if 'demand' in msdata:
        # Check for the special case of a demand technology of the
        # "other fuel - secondary heating" type (has unique levels)
        if 'other fuel' in msdata and 'secondary heating' in msdata:
            return ([endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]], technology_demanddict[msdata[7]])
        else:
            return ([endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]]], technology_demanddict[msdata[6]])
    # Translate a heating/cooling supply technology case into a filter list
    elif 'supply' in msdata:
        # Check for the special case of a supply technology of the
        # "other fuel - secondary heating" type (has unique levels)
        if 'other fuel' in msdata and 'secondary heating' in msdata:
            return [endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]]  # Note: "non-specific" supply technology for this case
        else:
            return [endusedict[msdata[3]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[6]]]
    # Translate an end sub use case into a filter list
    elif msdata[4] is not 'NA':
        return [endusedict[msdata[3]][msdata[4]], cdivdict[msdata[0]], bldgtypedict[msdata[1]], fueldict[msdata[2]], technology_supplydict[msdata[5]]]
    # Translate all other technologies into a filter list
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
            supply_filter = supply_filter + '(' + newelement + ').+'
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


def txt_parser(mstxt, comparefrom, command_string, file_type):
    """ Given a numpy array and information about what rows we want from it,
    match the rows and then remove them from the array.  If command_string
    input = 'Reduce', only remove the rows; if command_string
    input = 'Record & Reduce', also record matched rows """
    # Determine whether we are removing numpy array rows or also recording them
    record_reduce = re.search('Record & Reduce', command_string, re.IGNORECASE)
    # Determine whether we are parsing the EIA file or the load component file
    eia_parse = re.search('EIA', file_type, re.IGNORECASE)
    # Define intial list of rows to remove from mstxt input
    rows_to_remove = []
    # If recording and removing rows, define initial stock/energy lists
    if record_reduce:
        if eia_parse:  # Case where we are parsing the EIA AEO file
            group_stock = []
            group_energy = []
        else:  # Case where we are parsing the thermal load components file
            tloads_row = []
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
                # If recording/removing rows, record energy/stock info.
                if record_reduce:
                    if eia_parse:
                        group_stock.append(txtlines['EQSTOCK'])
                        group_energy.append(txtlines['CONSUMPTION'])
                    else:
                        tloads_row.append(txtlines)
    # Delete matched rows from numpy array of txt data
    mstxt_reduced = numpy.delete(mstxt, rows_to_remove, 0)
    # Set up proper function return based on command_string input
    if record_reduce:
        if eia_parse:
            parse_return = (group_energy, group_stock, mstxt_reduced)
        else:
            parse_return = (tloads_row, mstxt_reduced)
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
    [comparefrom_base, column_indicator] = filter_formatter(txt_filter)

    # Run through text file and add all appropriate lines to the empty list
    # Check whether current microsegment is a heating/cooling "demand"
    # technology (handled differently)
    if 'demand' in txt_filter:
        # Find baseline heating or cooling energy microsegment (before
        # application of load component); establish reduced numpy array
        [group_energy_base, group_stock, mstxt_demand] = txt_parser(mstxt_demand, comparefrom_base, 'Record & Reduce', 'EIA')
        # Given discovered list of energy values, ensure length = # years
        # currently projected by AEO. If not, reshape the list
        if len(group_energy_base) is not aeo_years:
            if len(group_energy_base) % aeo_years == 0:
                group_energy_base = numpy.reshape(group_energy_base, (aeo_years, -1), order='F').sum(axis=1).tolist()
            else:
                print('Error in length of discovered list!')

        # Find/apply appropriate thermal load component
        # 1. Construct appropriate row filter for tloads array
        fuel_remove = re.search('/./*/w+/./+/w+/./+/w+/./+', comparefrom_base)
        comparefrom_tloads = fuel_remove.group()
        # 2. Find/return appropriate tloads row and reduced tloads array
        [tloads_row, mstxt_loads] = txt_parser(res_tloads, comparefrom_tloads, 'Record & Reduce', 'TLoads')
        # 3. Using appropriate column indicator, find component value in row
        tload_component = tloads_row[column_indicator]
        # 4. Apply component value to baseline energy values for final list
        group_energy = [x * tload_component for x in group_energy_base]

        # Return combined energy use values and updated version of EIA demand
        # data and thermal loads data with already matched data removed
        return [{'stock': 'NA', 'energy': group_energy}, mstxt_supply, mstxt_demand, mstxt_loads]
    else:
        # Given input numpy array and 'compare from' list, return energy/stock
        # projection lists and reduced numpy array (with matched rows removed)
        [group_energy, group_stock, mstxt_supply] = txt_parser(mstxt_supply, comparefrom_base, 'Record & Reduce', 'EIA')

        # Given the discovered lists of energy/stock values, ensure length = #
        # years currently projected by AEO. If not, reshape the list
        if len(group_energy) is not aeo_years:
            if len(group_energy) % aeo_years == 0:
                group_energy = numpy.reshape(group_energy, (aeo_years, -1), order='F').sum(axis=1).tolist()
                group_stock = numpy.reshape(group_stock, (aeo_years, -1), order='F').sum(axis=1).tolist()
            else:
                print('Error in length of discovered list!')

        # Return combined stock/energy use values and updated version of EIA
        # supply data with already matched data removed
        return [{'stock': group_stock, 'energy': group_energy}, mstxt_supply, mstxt_demand, mstxt_loads]


def mseg_updater_main():
    """ Import .txt and JSON files; run through JSON objects; find
    analogous .txt information; replace JSON values; update JSON """
    # Import EIA RESDBOUT.txt file
    mstxt_supply = numpy.genfromtxt(EIA_res_file, names=True, delimiter='\t', dtype=None)
    # Reduce mstxt_supply array to only needed rows
    mstxt_supply = txt_parser(mstxt_supply, unused_supply_re, 'Reduce', 'EIA')

    # Set RESDBOUT.txt list for separate use in "demand" microsegments
    mstxt_demand = mstxt_supply
    # Reduce mstxt_demand array to only needed rows
    mstxt_demand = txt_parser(mstxt_demand, unused_demand_re, 'Reduce', 'EIA')

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
                                                [data_dict, mstxt_supply, mstxt_demand, mstxt_loads] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                                                msjson[cdiv][bldgtype][fueltype][endusetype][techtype][heatcooltechtype][heatcooltechtypesub] = data_dict
                                        else:
                                            filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', techtype, heatcooltechtype]
                                            [data_dict, mstxt_supply, mstxt_demand, mstxt_loads] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
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
                                        [data_dict, mstxt_supply, mstxt_demand, mstxt_loads] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                                        msjson[cdiv][bldgtype][fueltype][endusetype][subendusetype] = data_dict
                                    else:
                                        filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', techtype, 'NA']
                                        [data_dict, mstxt_supply, mstxt_demand, mstxt_loads] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                                        msjson[cdiv][bldgtype][fueltype][endusetype][techtype] = data_dict
                        else:
                            filterdata = [cdiv, bldgtype, fueltype, endusetype, 'NA', 'NA', 'NA']
                            [data_dict, mstxt_supply, mstxt_demand, mstxt_loads] = list_generator(mstxt_supply, mstxt_demand, mstxt_loads, filterdata)
                            msjson[cdiv][bldgtype][fueltype][endusetype] = data_dict
    # Return the updated json
    # print(msjson)
    return msjson


if __name__ == '__main__':
    mseg_updater_main()
