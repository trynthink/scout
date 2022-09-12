import sys, getopt
import os.path
import numpy as np
import pandas as pd
from plots_utilities import ECM_PREP
from plots_utilities import ECM_RESULTS

# dev work
# ecm_results_v1 = ECM_RESULTS("./results/ecm_results_v1.json").mas_by_category
# ecm_results_v2 = ECM_RESULTS("./results/ecm_results_v2.json").mas_by_category
# ecm_results_v3 = ECM_RESULTS("./results/ecm_results_v3.json").mas_by_category
# ecm_results_v4 = ECM_RESULTS("./results/ecm_results_v4.json").mas_by_category
# ecm_results_v5 = ECM_RESULTS("./results/ecm_results_v5.json").mas_by_category
# ecm_results_v6 = ECM_RESULTS("./results/ecm_results_v6.json").mas_by_category

# ecm_results_v1.columns
# ecm_results_v2.columns
# ecm_results_v3.columns
# ecm_results_v4.columns
# ecm_results_v5.columns
# ecm_results_v6.columns

# set(ecm_results_v3.building_type)


# set(ecm_results_v4.split_fuel)
# {'Biomass', 'Propane', 'Electric', 'Natural Gas', None, 'Distillate/Other'}


################################################################################
# mappings between ECM results and EMF aggregtaions
emf_base_string =\
    pd.DataFrame(data = {
        "Avoided CO\u2082 Emissions (MMTons)" : "*Emissions|CO2|Energy|Demand|Buildings",
        "Energy Savings (MMBtu)"              : "*Final Energy|Buildings"
        }.items(),
        columns = ["impact", "emf_base_string"]
        )

# NOTE: Mapping to EMF fuel types _might_ require a mapping that uses both fuel
# type and end use.  In the example script the combination of fuel_type = "distillate" and
# end_use = "secondary heating (kerosene)" maps to "Oil_kerosene".
# 
# Other possible end uses that will need to be accounted for,
#   * stove (wood)
#   * secondary heater (wood)
emf_fuel_types =\
        pd.DataFrame(data = {
              "Natural Gas"      : "Gas"              # ecm_results
            , "natural gas"      : "Gas"              # baseline
            , "Propane"          : "Gas"
            , "Distillate/Other" : "Oil"
            , "distillate"       : "Oil"
            , "Biomass"          : "Biomass Solids"  # ecm_results
            , "other fuel"       : "Biomass Solids"  # baseline
            , "Electric"         : "Electricity"
            , "Electricity"      : "Electricity"
            , "electricity"      : "Electricity"       # baseline
            # , "???"              : "Oil_kerosene"      # baseline
            }.items(),
            columns = ["scout_split_fuel", "emf_fuel_type"]
            )

emf_direct_indirect_fuel =\
        pd.DataFrame(data = {
            "Natural Gas"      : "Direct",
            "natural gas"      : "Direct",
            "Distillate/Other" : "Direct",
            "distillate"       : "Direct",
            "Biomass"          : "Direct",
            "Propane"          : "Direct",
            "Electric"         : "Indirect",
            "electricity"      : "Indirect",
            "Non-Electric"     : "Direct",
            "other fuel"       : "Direct"
            }.items(),
            columns = ["scout_split_fuel", "emf_direct_indirect_fuel"]
            )

emf_end_uses =\
        pd.DataFrame(data = {
              "Cooking"                   : "Appliances"  # ecm_results
            , "Cooling (Env.)"            : np.nan        # ecm_results
            , "Cooling (Equip.)"          : "Cooling"     # ecm_results
            , "Computers and Electronics" : "Other"       # ecm_results
            , "Heating (Env.)"            : np.nan        # ecm_results
            , "Heating (Equip.)"          : "Heating"     # ecm_results
            , "Lighting"                  : "Lighting"    # ecm_results
            , "Other"                     : "Other"       # ecm_results
            , "Refrigeration"             : "Appliances"  # ecm_results
            , "Ventilation"               : np.nan        # ecm_results
            , "Water Heating"             : "Appliances"  # ecm_results
            , 'ceiling fan'               : "Appliances"  # baseline
            , "cooking"                   : "Appliances"  # baseline
            , 'cooling'                   : "Cooling"     # baseline
            , 'computers'                 : "Other"       # baseline
            , 'drying'                    : "Appliances"  # baseline
            , 'fans and pumps'            : "Heating"     # baseline
            , 'heating'                   : "Heating"     # baseline
            , 'lighting'                  : "Lighting"    # baseline
            , 'MELs'                      : "Other"       # baseline
            , 'non-PC office equipment'   : "Other"       # baseline
            , 'other'                     : "Other"       # baseline
            , 'onsite generation'         : np.nan        # baseline
            , 'PCs'                       : "Other"       # baseline
            , 'refrigeration'             : "Appliances"  # baseline
            , 'secondary heating'         : "Heating"     # baseline
            , 'TVs'                       : "Other"       # baseline
            , 'ventilation'               : "Heating"     # baseline
            , 'water heating'             : "Appliances"  # baseline
            }.items(),
            columns = ["scout_end_use", "emf_end_use"]
            )

# if building_class exists, then part into to two columns
building_class_construction =\
        pd.DataFrame.from_dict(data = {
            "Commercial (Existing)"  : {
                "building_class" : "Commercial",
                "building_construction" : "Existing"
                },
            "Commercial (New)": {
                "building_class" : "Commercial",
                "building_construction" : "New"
                },
            "Residential (Existing)" : {
                "building_class" : "Residential",
                "building_construction" : "Existing"
                },
            "Residential (New)": {
                "building_class" : "Residential",
                "building_construction" : "New"
                }
            }, orient = "index")\
                    .reset_index()\
                    .rename(columns = {"index" : "building_class0"})

building_type_to_class =\
        pd.DataFrame(data = {
              'Assembly/Other'       : "Commercial"
            , 'Education'            : "Commercial"
            , 'Hospitality'          : "Commercial"
            , 'Hospitals'            : "Commercial"
            , 'Large Offices'        : "Commercial"
            , 'Multi Family Homes'   : "Residential"
            , 'Retail'               : "Commercial"
            , 'Single Family Homes'  : "Residential"
            , 'Small/Medium Offices' : "Commercial"
            , "Warehouse"            : "Commercial" # ecm_results
            , "assembly"           : "Commercial"
            , "education"          : "Commercial"
            , "food sales"         : "Commercial"
            , "food service"       : "Commercial"
            , "health care"        : "Commercial"
            , "lodging"            : "Commercial"
            , "large office"       : "Commercial"
            , "small office"       : "Commercial"
            , "mercantile/service" : "Commercial"
            , "warehouse"          : "Commercial"
            , "other"              : "Commercial"
            , "single family home" : "Residential"
            , "multi family home"  : "Residential"
            , "mobile home"        : "Residential"
            }.items(),
            columns = ["building_type", "building_class"]
            )

################################################################################

################################################################################
# Define some help documentation which will be conditionally shown to the end
# user.
help_usage = "Usage: emf_aggregation.py [options]"
help_options = """
Options:
  -h --help          Print this help and exit
  --ecm_prep=FILE    Path to a ecm_prep.json FILE, the results of ecm_prep.py
  --ecm_results=FILE Path to a ecm_results.json FILE, the results of run.py
"""

if __name__ == "__main__":
    # get command line args
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:", ["help", "ecm_results=", "ecm_prep="])
    except getopt.GetoptError:
        print(help_usage)
        print("Get more details by running: plots_interactive.py -h")
        sys.exit(2)

    # set default values for command line arguments
    ecm_prep_path    = "./supporting_data/ecm_prep.json"
    ecm_results_path = "./results/ecm_results.json"

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_usage)
            print(help_options)
            sys.exit()
        elif opt in ("--ecm_results"):
            ecm_results_path = arg
        elif opt in ("--ecm_prep"):
            ecm_prep_path = arg

    if not os.path.exists(ecm_prep_path):
        print(f"{ecm_prep_path} can not be reached or does not exist.")
        sys.exit(1)
    if not os.path.exists(ecm_results_path):
        print(f"{ecm_results_path} can not be reached or does not exist.")
        sys.exit(1)

    ############################################################################
    # Import the Data sets
    # print(f"Importing data from {ecm_prep_path}")
    # ecm_prep = ECM_PREP(path = ecm_prep_path)

    print(f"Importing data from {ecm_results_path}")
    ecm_results = ECM_RESULTS(path = ecm_results_path).mas_by_category


    ############################################################################
    # Data clean up
    # reduce rows to only the needed impacts:
    ecm_results =\
            ecm_results.merge(emf_base_string, how = "inner", on = "impact")

    # merge on emf_fuel types and end uses
    if "split_fuel" in ecm_results.columns:
        ecm_results = \
                ecm_results\
                .merge(
                        emf_fuel_types,
                        how = "left",
                        left_on = "split_fuel",
                        right_on = "scout_split_fuel"
                        )\
            .merge(
                    emf_direct_indirect_fuel,
                    how = "left",
                    left_on = "split_fuel",
                    right_on = "scout_split_fuel"
                    )
    else:
        sys.exit("split_fuel is not a column in the ecm_results.")

    # if building_class is part of the ecm_results then split into two columns
    if "building_class" in ecm_results.columns:
        ecm_results = \
            ecm_results\
            .merge(
                    right = building_class_construction,
                    how = "left",
                    left_on = "building_class",
                    right_on = "building_class0",
                    suffixes = ("_x", "")
                    )\
            .drop(columns = ["building_class0", "building_class_x"])

    if "building_type" in ecm_results.columns:
        ecm_results = \
            ecm_results\
            .merge(
                    right = building_type_to_class,
                    how = "left",
                    on = "building_type"
                    )


    if "end_use" in ecm_results.columns:
        ecm_results = \
                ecm_results\
            .merge(
                    emf_end_uses,
                    how = "left",
                    left_on = "end_use",
                    right_on = "scout_end_use"
                    )\
            .drop(columns = ["end_use"])

    ############################################################################
    # ECM Results aggregations:
    a0 = ecm_results\
            .groupby(["region", "emf_base_string", "year"])\
            .agg(value = ("value", "sum"))

    a1 = ecm_results\
            .groupby(["region", "emf_base_string", "building_class", "year"])\
            .agg(value = ("value", "sum"))

    a2 = ecm_results\
            .groupby(["region", "emf_base_string", "building_class", "emf_end_use", "year"])\
            .agg(value = ("value", "sum"))

    a3_0 = ecm_results\
            [ecm_results.emf_base_string == "*Emissions|CO2|Energy|Demand|Buildings"]\
            .groupby(["region", "emf_base_string", "direct_indirect_fuel", "year"])\
            .agg(value = ("value", "sum"))
    a3_1 = ecm_results\
            [ecm_results.emf_base_string == "*Emissions|CO2|Energy|Demand|Buildings"]\
            .groupby(["region", "emf_base_string", "building_class", "direct_indirect_fuel", "year"])\
            .agg(value = ("value", "sum"))
    a3_2 = ecm_results\
            [ecm_results.emf_base_string == "*Emissions|CO2|Energy|Demand|Buildings"]\
            .groupby(["region", "emf_base_string", "building_class", "emf_end_use", "direct_indirect_fuel", "year"])\
            .agg(value = ("value", "sum"))

    a4_0 = ecm_results\
            [ecm_results.emf_base_string == "*Final Energy|Buildings"]\
            .groupby(["region", "emf_base_string", "emf_fuel_type", "year"])\
            .agg(value = ("value", "sum"))
    a4_1 = ecm_results\
            [ecm_results.emf_base_string == "*Final Energy|Buildings"]\
            .groupby(["region", "emf_base_string", "building_class", "emf_fuel_type", "year"])\
            .agg(value = ("value", "sum"))
    a4_2 = ecm_results\
            [ecm_results.emf_base_string == "*Final Energy|Buildings"]\
            .groupby(["region", "emf_base_string", "building_class", "emf_end_use", "emf_fuel_type", "year"])\
            .agg(value = ("value", "sum"))

    # Aggregation clean up
    a0.reset_index(inplace = True)
    a1.reset_index(inplace = True)
    a2.reset_index(inplace = True)
    a3_0.reset_index(inplace = True)
    a3_1.reset_index(inplace = True)
    a3_2.reset_index(inplace = True)
    a4_0.reset_index(inplace = True)
    a4_1.reset_index(inplace = True)
    a4_2.reset_index(inplace = True)

    # build the full emf_string
    a0["emf_string"] = a0.region + a0.emf_base_string
    a1["emf_string"] = a0.region + a1.emf_base_string + "|" + a1.building_class
    a2["emf_string"] = a0.region + a2.emf_base_string + "|" + a2.building_class + "|" + a2.emf_end_use

    a3_0["emf_string"] = a3_0.region + a3_0.emf_base_string + "|" + a3_0.direct_indirect_fuel
    a3_1["emf_string"] = a3_1.region + a3_1.emf_base_string + "|" + a3_1.building_class + "|" + a3_1.direct_indirect_fuel
    a3_2["emf_string"] = a3_2.region + a3_2.emf_base_string + "|" + a3_2.building_class + "|" + a3_2.emf_end_use + "|" + a3_2.direct_indirect_fuel

    a4_0["emf_string"] = a4_0.region + a4_0.emf_base_string + "|" + a4_0.emf_fuel_type
    a4_1["emf_string"] = a4_1.region + a4_1.emf_base_string + "|" + a4_1.building_class + "|" + a4_1.emf_fuel_type
    a4_2["emf_string"] = a4_2.region + a4_2.emf_base_string + "|" + a4_2.building_class + "|" + a4_2.emf_end_use + "|" + a4_2.emf_fuel_type

    # build one data frame with all the aggregations
    ecm_results_emf_aggregation = pd.concat([
        a0[["emf_string", "year", "value"]],
        a1[["emf_string", "year", "value"]],
        a2[["emf_string", "year", "value"]],
        a3_0[["emf_string", "year", "value"]],
        a3_1[["emf_string", "year", "value"]],
        a3_2[["emf_string", "year", "value"]],
        a4_0[["emf_string", "year", "value"]],
        a4_1[["emf_string", "year", "value"]],
        a4_2[["emf_string", "year", "value"]]
        ])

    # create a wide version of the ecm_results_emf_aggregation
    ecm_results_emf_aggregation_wide = ecm_results_emf_aggregation.copy(deep = True)

    ecm_results_emf_aggregation_wide.year =\
            ecm_results_emf_aggregation_wide.year.apply(str) # this is needed so the column names post pivot are strings

    ecm_results_emf_aggregation_wide =\
            ecm_results_emf_aggregation_wide.pivot_table(
                    index = ["emf_string"],
                    columns = ["year"],
                    values = ["value"]
                    )

    ecm_results_emf_aggregation_wide.columns = ecm_results_emf_aggregation_wide.columns.droplevel(0)

    ecm_results_emf_aggregation.reset_index(inplace = True, drop = True)
    ecm_results_emf_aggregation_wide.reset_index(inplace = True, drop = False)

    
    ecm_results_emf_aggregation.to_csv(
            path_or_buf = ecm_results_path + "_emf_aggregation.csv"
            )
    ecm_results_emf_aggregation_wide.to_csv(
            path_or_buf = ecm_results_path + "_emf_aggregation_wide.csv"
            )











