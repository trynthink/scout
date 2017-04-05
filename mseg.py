#!/usr/bin/env python3

import re
import numpy
import json
import argparse


class EIAData(object):
    """Class of variables naming the EIA data files to be imported.

    Attributes:
        res_energy (str): The file name for the AEO residential energy
            and stock data.
    """
    def __init__(self):
        self.res_energy = 'RESDBOUT.txt'


class UsefulVars(object):
    """Class of variables that would otherwise be global.

    Attributes:
        json_in (str): JSON file containing the structure to be populated
            with AEO data.
        json_out (str): FIlename of the JSON file to be produced with
            residential energy use, building stock, and equipment stock
            data added.
        res_tloads (str): Filename for the residential building thermal
            load components data.
        aeo_metadata (str): File name for the custom AEO metadata JSON.
        unused_supply_re (str): A string usable as a regular expression
            defining the parameters (and thus the corresponding rows)
            from the AEO data that are not needed for the "supply"
            (i.e., equipment) energy and stock data. The two letter
            codes represent: (Switch From | Switch To | Fuel Pumps).
        unused_demand_re (str): A string usable as a regular expression
            defining the parameters (and thus the corresponding rows)
            from the AEO data that should be retained to calculate the
            demand (i.e., envelope) energy and stock data. Because the
            demand only applies to heating and cooling, this regex is
            configured to exclude every row not coded with one of the
            two letter codes given. These codes represent:
            (Heating | Cooling | Secondary Heating).
    """

    def __init__(self):
        self.json_in = 'microsegments.json'
        self.json_out = 'mseg_res_cdiv.json'
        self.res_tloads = 'Res_TLoads_Final.txt'
        self.aeo_metadata = 'metadata.json'
        self.unused_supply_re = '^\(b\'(SF|ST |FP).*'
        self.unused_demand_re = '^\(b\'(?!(HT|CL|SH)).*'


# Define a series of dicts that will translate imported JSON
# microsegment names to AEO microsegment(s)

# Census division dict
cdivdict = {'new england': 1,
            'mid atlantic': 2,
            'east north central': 3,
            'west north central': 4,
            'south atlantic': 5,
            'east south central': 6,
            'west south central': 7,
            'mountain': 8,
            'pacific': 9
            }

# Building type dict (residential)
bldgtypedict = {'single family home': 1,
                'multi family home': 2,
                'mobile home': 3
                }

# Fuel type dict
fueldict = {'electricity (on site)': 'SL',
            'electricity': 'EL',
            'natural gas': 'GS',
            'distillate': 'DS',
            'other fuel': ('LG', 'KS', 'CL', 'GE', 'WD')
            }
# Note that currently in RESDBOUT.txt, electric resistance heaters are
# categorized under GE (geothermal) fuel. Fuel types "SL" and "NG" have
# been removed from the "other fuel" category. "SL" (solar) fuel
# corresponds to solar insolation for solar water heating, and is only
# associated with the "SOLAR" technology type. "NG" is only used by the
# "FP" end use, and in an attempt to avoid problems later if EIA
# changes their natural gas fuel type code to "NG" from "GS", it is
# also left out of the "other fuel" definition.

# End use dict
endusedict = {'total square footage': 'SQ',  # AEO reports ft^2 as an end use
              'new homes': 'HS',
              'total homes': 'HT',
              'heating': 'HT',
              'secondary heating': 'SH',
              'cooling': 'CL',
              'fans & pumps': 'FF',
              'ceiling fan': 'CFN',
              'lighting': 'LT',
              'water heating': 'HW',
              'refrigeration': 'RF',
              'cooking': 'CK',
              'drying': 'DR',
              'TVs': {'TV': 'TVS',
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
                                                       'PHP', 'SEC', 'SPA')}
              }

# Technology types (supply) dict
technology_supplydict = {'solar WH': 'SOLAR_WH',
                         'electric WH': 'ELEC_WH',
                         'total homes (tech level)': 'ELEC_RAD',
                         'resistance heat': 'ELEC_RAD',
                         'ASHP': 'ELEC_HP',
                         'GSHP': 'GEO_HP',
                         'central AC': 'CENT_AIR',
                         'room AC': 'ROOM_AIR',
                         'linear fluorescent (T-12)': ('LFL', 'T12'),
                         'linear fluorescent (T-8)': ('LFL', 'T-8'),
                         'linear fluorescent (LED)': ('LFL', 'LED'),
                         'general service (incandescent)': ('GSL', 'Inc'),
                         'general service (CFL)': ('GSL', 'CFL'),
                         'general service (LED)': ('GSL', 'LED'),
                         'reflector (incandescent)': ('REF', 'Inc'),
                         'reflector (CFL)': ('REF', 'CFL'),
                         'reflector (halogen)': ('REF', 'HAL'),
                         'reflector (LED)': ('REF', 'LED'),
                         'external (incandescent)': ('EXT', 'Inc'),
                         'external (CFL)': ('EXT', 'CFL'),
                         'external (high pressure sodium)': ('EXT', 'HPS'),
                         'external (LED)': ('EXT', 'LED'),
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
                         'non-specific': ''
                         }

# Technology types (demand) dict
technology_demanddict = {'windows conduction': 'WIND_COND',
                         'windows solar': 'WIND_SOL',
                         'wall': 'WALL',
                         'roof': 'ROOF',
                         'ground': 'GRND',
                         'infiltration': 'INFIL',
                         'people gain': 'PEOPLE',
                         'equipment gain': 'EQUIP'}

# Form residential dictlist for use in JSON translator
res_dictlist = [endusedict, cdivdict, bldgtypedict, fueldict,
                technology_supplydict, technology_demanddict]


def json_translator(dictlist, filterformat):
    """ Determine filtering list for finding information in text file parse """

    # Set base filtering list of lists (1st element supply filter, 2nd demand)
    json_translate = [[], '']

    # Set an indicator for whether a "demand" filtering element has been found
    # (special treatment)
    demand_indicator = 0

    # Set an indicator for whether the technology level is handled on the end
    # use level - i.e., set top boxes (special treatment)
    enduse_techlevel = 0

    # Set an indicator for what level in the microsegment hierarchy we are in:
    # 1) end use, 2) census division, 3) bldg type, 4) fuel type,
    # 5) "supply" tech type, 6) "demand" tech type)
    ms_level = 0

    # Restructure the filterformat variable in the case of a "total homes"
    # update, where "total homes" uses the same filter codes as a heating,
    # electricity, boiler (electric) microsegment in RESDBOUT,
    # but with the relevant data in the "HOUSEHOLDS" column
    if 'total homes' in filterformat and len(filterformat) == 3:
        filterformat = filterformat[0:2]
        filterformat.extend(['electricity', 'total homes',
                             'total homes (tech level)'])
    # Reduce dictlist as appropriate to filtering information (if not a
    # "demand", microsegment, remove "technology_demanddict" from dictlist;
    # if not a "supply" microsegment", remove "technology_supplydict" from
    # dictlist; if a microsegment with no technology level (i.e. water heating)
    # remove "technology_supplydict" and "technology_demanddict" from dictlist;
    # if a microsegment square footage or a new homes update, include only
    # "fueldict", "cdivdict", and "bldgtypedict" (square footage and new
    # homes are included on the fuel type level in the microsegments JSON).
    if 'demand' in filterformat:
        dictlist_loop = dictlist[:(len(dictlist) - 2)]
        dictlist_add = dictlist[-1]
        dictlist_loop.append(dictlist_add)
    elif 'total square footage' in filterformat and len(filterformat) == 3 or \
         'new homes' in filterformat and len(filterformat) == 3:
        dictlist_loop = dictlist[:(len(dictlist) - 3)]
    elif len(filterformat) <= 4:
        dictlist_loop = dictlist[:(len(dictlist) - 2)]
    else:
        dictlist_loop = dictlist[:(len(dictlist) - 1)]

    # Loop through "dictlist" and determine whether any elements of
    # "filterformat" input are in dict keys; if so, add key value to output
    for j in dictlist_loop:
        # Count key matches for given dict
        match_count = 0
        ms_level += 1
        for num, key in enumerate(filterformat):
            # Check whether element is in dict keys
            if key in j.keys():
                match_count += 1
                # "Demand" technologies added to 2nd element of filtering list
                if demand_indicator != 1:
                    # If there are more levels in a keyed item, go down branch
                    if isinstance(j[key], dict):
                        nextkey = filterformat[num + 1]
                        if nextkey in j[key].keys():
                            json_translate[0].append(j[key][nextkey])
                            # Update enduse_techlevel indicator
                            enduse_techlevel = 1
                    else:
                        json_translate[0].append(j[key])
                    break
                else:
                    if isinstance(j[key], dict):
                        nextkey = filterformat[num + 1]
                        if nextkey in j[key].keys():
                            json_translate[1] = str(j[key][nextkey])
                    else:
                        json_translate[1] = str(j[key])
                    break
            # Flag a "demand" microsegment
            elif key == 'demand':
                demand_indicator = 1
        # If there was no key match for given dict and we don't have special
        # case of a technology being handled on the end use level, raise error
        if (match_count == 0 and ms_level != (len(dictlist) - 1)) or \
           (match_count == 0 and ms_level == (len(dictlist) - 1) and
           enduse_techlevel == 0):
            raise(KeyError("Filter list element not found in dict keys!"))

    # Return updated filtering list of lists: [[supply filter],[demand filter]]
    return json_translate


def filter_formatter(txt_filter):
    """ Given a filtering list for a microsegment, format into a
    string that can be entered into a regex comparison in the
    list_generator function """

    # Set base "supply" filter string
    supply_filter = '.*'

    # Determine whether we are updating a "demand" microsegment by
    # whether or not the current function input is a tuple. If so,
    # use the first tuple element as a filter for the EIA data, and
    # the second tuple element as filter for the residential thermal
    # load components.
    if txt_filter[1]:
        txt_filter_loop = txt_filter[0]
        demand_filter = txt_filter[1]
    else:
        txt_filter_loop = txt_filter[0]
        demand_filter = 'NA'

    for element in txt_filter_loop:  # Run through elements of the filter list
        # If element is a tuple and not on the "demand" technology level, join
        # the tuple into a single string, put brackets around it for regex
        # comparison
        if isinstance(element, tuple):
            if endusedict['lighting'] in txt_filter_loop:
                newelement = element[0] + '\W+.*\W+' + element[1]
                supply_filter = supply_filter + newelement + '\W+.*\W+'
            else:
                newelement = '|'.join(element)
                supply_filter = supply_filter + '(' + newelement + ')\W+.*\W+'
        # If element is a number and not on the "demand" technology level, turn
        # into a string for regex comparison
        elif isinstance(element, int):
            newelement = str(element)
            supply_filter = supply_filter + newelement + '\W+.*\W+'
        # If element is a string and not on the "demand" technology level, add
        # it to the filter list without modification
        elif isinstance(element, str):
            supply_filter = supply_filter + element + '\W+.*\W+'
        else:
            print('Error in list finder form!')

    return (supply_filter, demand_filter)


def thermal_load_select(tl_array, comparefrom, demand_column):
    """ Select the desired thermal load component for the relevant
    operating condition (heating or cooling) from the input data
    based on the demand_column variable """

    # Loop through the thermal load component array rows to identify
    # the row matching the 'comparefrom' selection regex
    for row in tl_array:

        # Set up 'compareto' regex string using only the first three
        # columns of the thermal load components array
        compareto = str([row[0], row[1], row[2]])

        # Check whether there is a match for the current row
        match = re.search(comparefrom, compareto)

        # If there's a match, extract the demand modifier value
        # (the fraction of heating or cooling load gained/lost
        # through the relevant exterior surface) in the appropriate
        # column using 'demand_column'
        if match:
            tloads_component = (row[demand_column])

    return tloads_component


def stock_consume_select(data, comparefrom, file_type):
    """ Select the stock and consumption data for each year for a
    microsegment and combine them into lists for all reported years """

    # Determine whether we are parsing the "supply" version of the EIA data
    supply_parse = re.search('EIA_Supply', file_type, re.IGNORECASE)

    # Define initial list of rows to remove from data input
    rows_to_remove = []

    # Define initial stock and energy dicts
    group_stock = {}
    group_energy = {}

    # Loop through the numpy input array rows, match to 'comparefrom' input
    for idx, row in enumerate(data):
        # Set up 'compareto' list
        compareto = str(row)

        # Establish the match
        match = re.search(comparefrom, compareto)

        # If there's a match, append values for the current microsegment
        if match:

            # If data for the year is already present for the current
            # microsegment (as with microsegments that combine several
            # EIA categories together, add the new stock and consumption
            # values to the existing values (assume that if the year is
            # present in the group_stock dict it is also in group_energy)
            if str(row['YEAR']) in group_stock:
                # Record energy consumption and stock information
                # (change the year to a string to yield a valid
                # JSON dict, where all keys must be strings)
                group_stock[str(row['YEAR'])] += row['EQSTOCK']
                group_energy[str(row['YEAR'])] += row['CONSUMPTION']

            else:
                group_stock[str(row['YEAR'])] = row['EQSTOCK']
                group_energy[str(row['YEAR'])] = row['CONSUMPTION']

            # If handling the supply data, to reduce computation time,
            # record row index to delete later.  * Note: skip this for
            # a case where electric boilers is being updated, as the
            # filtering information for electric boilers overlaps that
            # of total homes
            if supply_parse and 'ELEC_RAD' not in comparefrom:
                rows_to_remove.append(idx)

    # Remove rows specified by rows_to_remove (an empty list when
    # demand data are being handled by this function, thus deleting no
    # rows, since the demand microsegments apply to multiple categories,
    # e.g. heating through window conduction and envelope conduction).
    data_reduced = numpy.delete(data, rows_to_remove, 0)

    return (group_energy, group_stock, data_reduced)


def sqft_homes_select(data, comparefrom):
    """ Select the square footage, new homes, or total homes data for each year
    for a given census division/building type and combine them into lists for
    all reported years """

    # Define initial list of rows to remove from data input
    rows_to_remove = []

    # Define initial square footage, new homes, or total homes lists
    if endusedict['total square footage'] in comparefrom or \
       endusedict['new homes'] in comparefrom or \
       endusedict['total homes'] in comparefrom:
        group_out = {}
    else:
        raise ValueError('Unexpected housing stock filtering information!')

    # Loop through the numpy input array rows, match to 'comparefrom' input
    for idx, row in enumerate(data):
        # Set up 'compareto' list
        compareto = str(row)

        # Establish the match
        match = re.search(comparefrom, compareto)

        # If there is a match, append values for the current cdiv/bldg. type
        if match:
            if endusedict['total square footage'] in comparefrom or \
               endusedict['total homes'] in comparefrom:
                # Record square foot or total homes info. (in "HOUSEHOLDS"
                # column in RESDBOUT)
                group_out[str(row['YEAR'])] = row['HOUSEHOLDS']
            else:
                # Record new homes info. (in "STOCK" column in RESDBOUT)
                group_out[str(row['YEAR'])] = row['EQSTOCK']

            # To reduce computation time, record row index to delete later.
            # * Note: skip this for a case where total number of homes is
            # being updated, as the filtering information for total homes
            # overlaps that of electric boilers
            if endusedict['total homes'] not in comparefrom:
                rows_to_remove.append(idx)

    # Remove rows specified by rows_to_remove
    data_reduced = numpy.delete(data, rows_to_remove, 0)
    return (group_out, data_reduced)


def list_generator(ms_supply, ms_demand, ms_loads, filterdata, aeo_years):
    """ Given filtering list for a microsegment, find rows in text
    files to reference in determining associated energy data, append
    energy data to a new list """

    # Find the corresponding text filtering information
    txt_filter = json_translator(res_dictlist, filterdata)

    # Set up 'compare from' list (based on data file contents)
    [comparefrom_base, column_indicator] = filter_formatter(txt_filter)

    # Run through text file and add all appropriate lines to the empty list
    # Check whether current microsegment is a heating/cooling "demand"
    # technology (handled differently)
    if 'demand' in filterdata:
        # Find baseline heating or cooling energy microsegment (before
        # application of load component); establish reduced numpy array
        [group_energy_base, group_stock, ms_demand] = stock_consume_select(
            ms_demand, comparefrom_base, 'EIA_Demand')

        # Given the discovered lists of energy/stock values, ensure
        # length is equal to the number of years currently projected
        # by AEO. If not, and the list isn't empty, trigger an error.
        if len(group_energy_base) is not aeo_years:
            if len(group_energy_base) != 0:
                raise(ValueError('Error in length of discovered list!'))

        # Find/apply appropriate thermal load component

        # 1. Construct appropriate row filter for tloads array
        fuel_remove = re.search(
            '(\.\*)(\(*\w+\|*\w+\)*)(\W+\w+\W+\w+\W+\w+\W+\w+\W+\w+\W+\w+)',
            comparefrom_base)
        # If special case of secondary heating, change end use part of regex to
        # 'HT', which is what both primary and secondary heating are coded as
        # in thermal loads text file data
        if (fuel_remove.group(2) == 'SH'):
            comparefrom_tloads = fuel_remove.group(1) + 'HT' + \
                fuel_remove.group(3)
        else:
            comparefrom_tloads = fuel_remove.group()

        # 2. Find/return appropriate thermal loads component and reduced
        #    thermal loads array
        tloads_component = thermal_load_select(
            ms_loads, comparefrom_tloads, column_indicator)

        # 3. Apply component value to baseline energy values for final list
        group_energy = {key: val * tloads_component
                        for key, val in group_energy_base.items()}

        # Return combined energy use values and updated version of EIA demand
        # data and thermal loads data with already matched data removed
        return [{'stock': 'NA', 'energy': group_energy}, ms_supply]
    # Check whether current microsegment is updating "total square footage"
    # information (handled differently)
    elif 'total square footage' in filterdata or 'new homes' in filterdata or \
         'total homes' in filterdata:
        # Given input numpy array and 'compare from' list, return sq. footage
        # projection lists and reduced numpy array (with matched rows removed)
        [group_sqft_homes, ms_supply] = sqft_homes_select(
            ms_supply, comparefrom_base)

        # Given the discovered lists of sq. footage values, ensure
        # length is equal to the number of years currently projected
        # by AEO. If not, and the list isn't empty, trigger an error.
        if len(group_sqft_homes) is not aeo_years:
            if len(group_sqft_homes) != 0:
                raise(ValueError('Error in length of discovered list!'))

        # Return sq. footage values and updated version of EIA
        # supply data with already matched data removed
        return [group_sqft_homes, ms_supply]
    else:
        # Given input numpy array and 'compare from' list, return energy/stock
        # projection lists and reduced numpy array (with matched rows removed)
        [group_energy, group_stock, ms_supply] = stock_consume_select(
            ms_supply, comparefrom_base, 'EIA_Supply')

        # Given the discovered lists of energy/stock values, ensure
        # length is equal to the number of years currently projected
        # by AEO. If not, and the list isn't empty, trigger an error.
        if len(group_energy) is not aeo_years:
            if len(group_energy) != 0:
                raise(ValueError('Error in length of discovered list!'))

        # Return combined stock/energy use values and updated version of EIA
        # supply data with already matched data removed
        return [{'stock': group_stock, 'energy': group_energy}, ms_supply]


def walk(supply, demand, loads, json_dict, yrs_range, key_list=[]):
    """ Proceed recursively through data stored in dict-type structure
    and perform calculations at each leaf/terminal node in the data """

    for key, item in json_dict.items():

        # If there are additional levels in the dict, call the function
        # again to advance another level deeper into the data structure
        if isinstance(item, dict):
            walk(supply, demand, loads, item, yrs_range, key_list + [key])

        # If a leaf node has been reached, check if the second entry in
        # the key list is one of the recognized building types, and if
        # so, finish constructing the key list for the current location
        # and obtain the data to update the dict
        else:
            if key_list[1] in bldgtypedict.keys():
                leaf_node_keys = key_list + [key]
                # Extract data from original data sources
                [data_dict, supply] = list_generator(supply, demand, loads,
                                                     leaf_node_keys, yrs_range)
                # Set dict key to extracted data
                json_dict[key] = data_dict

    # Return final file
    return json_dict


def array_row_remover(data, comparefrom):
    """ Remove rows from large arrays (e.g. EIA data) based on a
    regular expression that defines which rows are not going to
    be needed later in the analysis """

    # Define an initial list of rows to remove from the input array
    rows_to_remove = []

    # Loop through the numpy input array rows and match to 'comparefrom' regex
    for idx, row in enumerate(data):

            # Set up 'compareto' string
            compareto = str(row)

            # Check whether there is a match for the current row
            match = re.search(comparefrom, compareto)

            # If there is a match, record the row index for later deletion
            if match:
                rows_to_remove.append(idx)

    # Delete matched rows from numpy input array
    data_reduced = numpy.delete(data, rows_to_remove, 0)

    return data_reduced


def main():
    """ Import text and JSON files; run through JSON objects; find
    analogous text information; replace JSON values; update JSON """

    # Set up to support user option to specify the year for the
    # AEO data being imported (default if the option is not used
    # should be current year)
    parser = argparse.ArgumentParser()
    help_string = 'Specify year of AEO data to be imported'
    parser.add_argument('-y', '--year', type=int, help=help_string,
                        choices=[2015, 2017])

    # Get import year specified by user (if any)
    aeo_import_year = parser.parse_args().year

    # Instantiate objects that contain useful variables
    handyvars = UsefulVars()
    eiadata = EIAData()

    # Import EIA RESDBOUT.txt file
    supply = numpy.genfromtxt(eiadata.res_energy, names=True,
                              delimiter='\t', dtype=None)
    # Reduce supply array to only needed rows
    supply = array_row_remover(supply, handyvars.unused_supply_re)

    # Set RESDBOUT.txt data for separate use in "demand" microsegments
    demand = supply
    # Reduce demand array to only needed rows
    demand = array_row_remover(demand, handyvars.unused_demand_re)

    # Import residential thermal load components data
    loads = numpy.genfromtxt(handyvars.res_tloads, names=True,
                             delimiter='\t', dtype=None)

    # Import metadata generated based on EIA AEO data files
    with open(handyvars.aeo_metadata, 'r') as metadata:
        metajson = json.load(metadata)

    # Calculate number of years in the AEO data; expecting 32 years
    # for AEO 2015 data, 42 years in AEO 2017 data (though 38 years
    # are common across all input EIA data files)

    # Use AEO data import year specified by user (if any) to determine
    # how to specify the year range to be used for processing the data
    if aeo_import_year == 2015:
        yrs_range = metajson['max year'] - metajson['min year'] + 1
    else:
        yrs_range = 42
    # THIS APPROACH MAY NEED TO BE REVISITED IN THE FUTURE; AS IS,
    # IT DOES NOT ENSURE CONSISTENCY WITH THE OTHER AEO INPUT DATA
    # IN THE RANGE OF YEARS OF THE DATA REPORTED

    # json.dump cannot convert ("serialize") numbers of the type
    # np.int64 to integers, but all of the integers in 'result' are
    # formatted as np.int64; this function fixes that problem as the
    # data are serialized and exported
    def fix_ints(num):
        if isinstance(num, numpy.integer):
            return int(num)
        else:
            raise TypeError

    # Import JSON file and run through updating scheme
    with open(handyvars.json_in, 'r') as jsi, open(
         handyvars.json_out, 'w') as jso:
        msjson = json.load(jsi)

        # Run through JSON objects, determine replacement information
        # to mine from the imported data, and make the replacements
        result = walk(supply, demand, loads, msjson, yrs_range)

        # Write the updated dict of data to a new JSON file
        json.dump(result, jso, indent=2, default=fix_ints)


if __name__ == '__main__':
    main()
