#!/usr/bin/env python3

# Identify files to import for conversion
serv_dmd = 'KDBOUT.txt'
catg_dmd = 'KDBOUT.txt'
# json_in = 'microsegments.json'
# json_out = 'microsegments_out.json'
res_tloads = 'Res_TLoads_Final.txt'
res_climate_convert = 'Res_Cdiv_Czone_ConvertTable_Final.txt'
com_tloads = 'Com_TLoads_Final.txt'
com_climate_convert = 'Com_Cdiv_Czone_ConvertTable_Final.txt'

# Define a series of dicts that will translate imported JSON
# microsegment names to AEO microsegment(s)

# Census division (identical to residential)
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

# Building type
bldgtypedict = {'assembly': 1,
                'education': 2,
                'food sales': 3,
                'food service': 4,
                'health care': 5,
                'lodging': 6,
                'large office': 7,
                'small office': 8,
                'mercantile/service': 9,
                'warehouse': 10,
                'other': 11,
                'FIGURE THIS ONE OUT': 12
                }

# End use
endusedict = {'space heating': 1,
              'space cooling': 2,
              'water heating': 3,
              'ventilation': 4,
              'cooking': 5,
              'lighting': 6,
              'refrigeration': 7,
              'PCs': 8,
              'non-PC office equipment': 9,
              'MELs': 10
              }

# Miscellaneous electric load end uses
mels_techdict = {'distribution transformers': 1,
                 'security systems': 2,
                 'elevators': 3,
                 'escalators': 4,
                 'non-road electric vehicles': 5,
                 'coffee brewers': 6,
                 'kitchen ventilation': 7,
                 'laundry': 8,
                 'lab fridges and freezers': 9,
                 'fume hoods': 10,
                 'medical imaging': 11,
                 'video displays': 15,
                 'large video displays': 16,
                 'municipal water services': 17
                 }

# Fuel types
fueldict = {'electricity': 1,
            'natural gas': 2,
            'distillate': 3,
            'liquefied petroleum gas (LPG)': 5,
            'other fuel': (4, 6, 7, 8)
            }
# Other fuel includes residual oil (4), steam from coal (6),
# motor gasoline (7), and kerosene (8)


def main():
    """ Import input data files and do other things """

    # Import EIA AEO 'KSDOUT' service demand file

    # Import EIA AEO 'KDBOUT' additiona data file


if __name__ == '__main__':
    main()
