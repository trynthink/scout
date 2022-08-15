################################################################################
# file: plots_utilities.py
#
# Define functions and methods used for
#
# 1. data preperation
# 2. generating diagnostic graphics
#
# These methods will be called within other files for generating interactive
# dash applications and static graphics as well.
#
# Functions defined in this file are:
#   * json_to_df
#   * flattened_dict
#
# Classes defined in this file are:
#   * ecm_prep
#   * ecm_results
#
################################################################################
import json
import gzip
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

################################################################################
def json_to_df(path = None, data = None):
    """
    Function: json_to_df

        Read data from a json file and format it as a pandas DataFrame

    Arguments:
       data a dictionary with nested levels
       path file path to a .json or .json.gz file

    Return:
        A pandas DataFrame
    """

    assert bool(data is not None) ^ bool(path is not None)

    if path is not None:
        if path.endswith(".gz"):
            with gzip.open(path, 'r') as f:
                file_content = f.read()
            json_str = file_content.decode("utf-8")
            data = json.loads(json_str)
        else:
            f = open(path, "r")
            data = json.load(f)
            f.close()

    x = flatten_dict(data)
    x = [(*a, str(b)) for a,b in x.items()]
    x = pd.DataFrame(x)
    x.columns = ["lvl" + str(i) for i in range(len(x.columns))]
    return x

################################################################################
def flatten_dict(nested_dict):
    """
    Function: flatten_dict
        recursivly parse a nested dictionary and generate a generic pandas
        DataFrame

    Arguments:
        nested_dict a dictionary

    Return:
        A pandas DataFrame
    """

    res = {}
    if isinstance(nested_dict, dict):
        for k in nested_dict:
            flattened_dict = flatten_dict(nested_dict[k])
            for key, val in flattened_dict.items():
                key = list(key)
                key.insert(0, k)
                res[tuple(key)] = val
    else:
        res[()] = nested_dict
    return res

################################################################################
def isfloat(x):
    """
    Return True is x is, or can be, a float value, Return False otherwise
    """
    try:
        float(x)
        return True
    except ValueError:
        return False
    except TypeError:
        return False

################################################################################
def unique_strings(l):
    list_set = set(l)
    ul = (list(list_set))
    return '; '.join(ul)

################################################################################
SCENARIOS = ["Max adoption potential", "Technical potential"]
IMPACTS = [
    'Energy Cost (USD)',      # On-site Generation
    'Energy (MMBtu)',         # On-site Generation
    'CO₂ Emissions (MMTons)', # On-site Generation

    'Energy Savings (MMBtu)',           # Markets and Savings
    'Avoided CO₂ Emissions (MMTons)',   # Markets and Savings
    'CO₂ Cost Savings (USD)',           # Markets and Savings
    'Efficient Energy Cost (USD)',      # Markets and Savings
    'Baseline Energy Cost (USD)',       # Markets and Savings
    'Baseline CO₂ Emissions (MMTons)',  # Markets and Savings
    'Efficient CO₂ Cost (USD)',         # Markets and Savings
    'Efficient CO₂ Emissions (MMTons)', # Markets and Savings
    'Efficient Energy Use (MMBtu)',     # Markets and Savings
    'Baseline CO₂ Cost (USD)',          # Markets and Savings
    'Baseline Energy Use (MMBtu)',      # Markets and Savings
    'Energy Cost Savings (USD)',        # Markets and Savings

    'Cost of Conserved Energy ($/MMBtu saved)',   # Financial Metrics
    'Cost of Conserved CO₂ ($/MTon CO₂ avoided)', # Financial Metrics
    'IRR (%)',                                    # Financial Metrics
    'Payback (years)'                             # Financial Metrics
           ]

# Yes, the AIA regions are sometimes denoted with a underscore, sometimes with a
# space.  There is no way this will cause problems later on.  On-site Generation
# uses the under scores, Markets and Savings use the spaces.
REGIONS = [
    "AIA_CZ1", "AIA_CZ2", "AIA_CZ3", "AIA_CZ4", "AIA_CZ5",
    "AIA CZ1", "AIA CZ2", "AIA CZ3", "AIA CZ4", "AIA CZ5",

    "TRE", "FRCC", "MISW", "MISC", "MISE", "MISS", "ISNE", "NYCW", "NYUP",
    "PJME", "PJMW", "PJMC", "PJMD", "SRCA", "SRSE", "SRCE", "SPPS", "SPPC",
    "SPPN", "SRSG", "CANO", "CASO", "NWPP", "RMRG", "BASN",

    "AL", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FL", "GA", "ID", "IL",
    "IN", "IA", "KS", "KY", "LA", "ME", "MD", "MA", "MI", "MN", "MS", "MO",
    "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "OH", "OK", "OR",
    "PA", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
    ]

BUILDING_CLASSES = [
        "Residential (New)", "Residential (Existing)",
        "Commercial (New)", "Commercial (Existing)"
        ]

BUILDING_TYPES = [
    'single family home', # On-site Generation
    'education',          # On-site Generation
    'lodging',            # On-site Generation
    'other',              # On-site Generation
    'food sales',         # On-site Generation
    'small office',       # On-site Generation
    'health care',        # On-site Generation
    'large office',       # On-site Generation
    'mercantile/service', # On-site Generation
    'warehouse',          # On-site Generation
    'food service',       # On-site Generation
    'assembly',           # On-site Generation
    'Hospitals',            # Markets and Savings
    'Multi Family Homes',   # Markets and Savings
    'Retail',               # Markets and Savings
    'Warehouses',           # Markets and Savings
    'Large Offices',        # Markets and Savings
    'Single Family Homes',  # Markets and Savings
    'Education',            # Markets and Savings
    'Hospitality',          # Markets and Savings
    'Small/Medium Offices', # Markets and Savings
    'Assembly/Other'        # Markets and Savings
    ]

END_USES = [
        'Refrigeration',
        'Ventilation',
        'Water Heating',
        'Cooling (Env.)',
        'Heating (Env.)',
        'Other',
        'Lighting',
        'Cooling (Equip.)',
        'Heating (Equip.)'
        ]

SPLIT_FUEL = ['Non-Electric', 'Electric',
        'Natural Gas',
        'Biomass',
        'Distillate/Other',
        'Propane',
        None
        ]

TOTAL_COMPETED = ['total', 'competed']
ABEM = ['all', 'baseline', 'efficient', 'measure']
ECS = ['energy', 'carbon', 'stock']
BSE = ['baseline', 'savings', 'efficient']
ECC = ['energy', 'carbon', 'cost']


################################################################################
def extract_osg(df):
    """
    Extract On-site Generation from results
    """
    assert any(df.lvl0 == "On-site Generation")
    osg_by_category =\
            df[((df.lvl0 == "On-site Generation") &
                (df.lvl2 == "By Category"))].reset_index(drop = True)
    osg_overall =\
            df[((df.lvl0 == "On-site Generation") &
                (df.lvl2 == "Overall"))].reset_index(drop = True)

    for j in df.columns:
        if all(osg_by_category[j].isna()):
            osg_by_category.drop(columns = j, inplace = True)
        if all(osg_overall[j].isna()):
            osg_overall.drop(columns = j, inplace = True)

    for j in reversed(osg_by_category.columns):
        if all(osg_by_category[j].str.contains(r"^\d{4}$")):
            osg_by_category[j] = osg_by_category[j].apply(int)
            osg_by_category.rename(columns = {j : "year"}, inplace = True)
        elif all(osg_by_category[j].apply(isfloat)):
            osg_by_category[j] = osg_by_category[j].apply(float)
            osg_by_category.rename(columns = {j : "value"}, inplace = True)
        elif all(osg_by_category[j] == "By Category"):
            osg_by_category.drop(columns = j, inplace = True)
        elif all(osg_by_category[j] == "On-site Generation"):
            osg_by_category.drop(columns = j, inplace = True)
        elif all(osg_by_category[j].isin(IMPACTS)):
            osg_by_category.rename(columns = {j : "impact"}, inplace = True)
        elif all(osg_by_category[j].isin(REGIONS)):
            osg_by_category.rename(columns = {j : "region"}, inplace = True)
        elif all(osg_by_category[j].isin(BUILDING_TYPES)):
            osg_by_category.rename(columns = {j : "building_type"}, inplace = True)
        else:
            continue

    for j in reversed(osg_overall.columns):
        if all(osg_overall[j].str.contains(r"^\d{4}$")):
            osg_overall[j] = osg_overall[j].apply(int)
            osg_overall.rename(columns = {j : "year"}, inplace = True)
        elif all(osg_overall[j].apply(isfloat)):
            osg_overall[j] = osg_overall[j].apply(float)
            osg_overall.rename(columns = {j : "value"}, inplace = True)
        elif all(osg_overall[j] == "Overall"):
            osg_overall.drop(columns = j, inplace = True)
        elif all(osg_overall[j] == "On-site Generation"):
            osg_overall.drop(columns = j, inplace = True)
        elif all(osg_overall[j].isin(IMPACTS)):
            osg_overall.rename(columns = {j : "impact"}, inplace = True)
        elif all(osg_overall[j].isin(REGIONS)):
            osg_overall.rename(columns = {j : "region"}, inplace = True)
        elif all(osg_overall[j].isin(BUILDING_TYPES)):
            osg_overall.rename(columns = {j : "building_type"}, inplace = True)
        else:
            continue

    return osg_by_category, osg_overall

################################################################################
def extract_financial_metrics(df):
    assert any(df.lvl1 == "Financial Metrics")

    fm = df[df.lvl1 == "Financial Metrics"]\
            .drop(columns = "lvl1")\
            .reset_index(drop = True)

    for j in fm.columns:
        if all(fm[j].isna()):
            fm.drop(columns = j, inplace = True)
        elif all(fm[j].str.contains(r"^\d{4}$")):
            fm[j] = fm[j].apply(int)
            fm.rename(columns = {j : "year"}, inplace = True)
        elif all(fm[j].apply(isfloat)):
            fm[j] = fm[j].apply(float)
            fm.rename(columns = {j : "value"}, inplace = True)
        elif all(fm[j].isin(IMPACTS)):
            fm.rename(columns = {j : "impact"}, inplace = True)
        else:
            continue

    return fm

################################################################################
def extract_mas(df):
    mas_by_category =\
            df[df.lvl1 == "Markets and Savings (by Category)"]\
            .drop(columns = "lvl1")\
            .reset_index(drop = True)
    mas_overall =\
            df[df.lvl1 == "Markets and Savings (Overall)"]\
            .drop(columns = "lvl1")\
            .reset_index(drop = True)

    # remove columns with no information
    for j in mas_by_category.columns:
        if all(mas_by_category[j].isna()):
            mas_by_category.drop(columns = j, inplace = True)
        else:
            continue
    for j in mas_overall.columns:
        if all(mas_overall[j].isna()):
            mas_overall.drop(columns = j, inplace = True)
        else:
            continue

    # Look to see if data needs to be shifted from one column to another.
    # Example need, when fuel split is present then some of the rows will have
    # Non-Electric or Electric in a column were as other rows will have nothing
    # as flue split was not relevent.  This requires shifting the columns right
    # so that the data in each column will be conceptually consistent.
    for j in range(len(mas_by_category.columns)):
        idx = mas_by_category[mas_by_category.columns[j]].isin(SPLIT_FUEL)
        if any(idx):
            if all(mas_by_category.loc[~idx, mas_by_category.columns[j + 2]].isna()):
                mas_by_category.loc[~idx, mas_by_category.columns[j + 2]] =\
                    mas_by_category.loc[~idx, mas_by_category.columns[j + 1]]
                mas_by_category.loc[~idx, mas_by_category.columns[j + 1]] =\
                    mas_by_category.loc[~idx, mas_by_category.columns[j + 0]]
                mas_by_category.loc[~idx, mas_by_category.columns[j + 0]] = None

    for j in range(len(mas_overall.columns)):
        idx = mas_overall[mas_overall.columns[j]].isin(SPLIT_FUEL)
        if any(idx):
            if all(mas_overall.loc[~idx, mas_overall.columns[j + 2]].isna()):
                mas_overall.loc[~idx, mas_overall.columns[j + 2]] =\
                    mas_overall.loc[~idx, mas_overall.columns[j + 1]]
                mas_overall.loc[~idx, mas_overall.columns[j + 1]] =\
                    mas_overall.loc[~idx, mas_overall.columns[j + 0]]
                mas_overall.loc[~idx, mas_overall.columns[j + 0]] = None

    # Rename columns, set data storage modes
    for j in mas_by_category.columns:
        if all(mas_by_category[j].isna()):
            mas_by_category.drop(columns = j, inplace = True)
        elif all(mas_by_category[j].str.contains(r"^\d{4}")):
            mas_by_category[j] = mas_by_category[j].apply(int)
            mas_by_category.rename(columns = {j : "year"}, inplace = True)
        elif all(mas_by_category[j].apply(isfloat)):
            mas_by_category[j] = mas_by_category[j].apply(float)
            mas_by_category.rename(columns = {j : "value"}, inplace = True)
        elif all(mas_by_category[j].isin(SCENARIOS)):
            mas_by_category.rename(columns = {j : "scenario"}, inplace = True)
        elif all(mas_by_category[j].isin(IMPACTS)):
            mas_by_category.rename(columns = {j : "impact"}, inplace = True)
        elif all(mas_by_category[j].isin(REGIONS)):
            mas_by_category.rename(columns = {j : "region"}, inplace = True)
        elif all(mas_by_category[j].isin(BUILDING_CLASSES)):
            mas_by_category.rename(columns = {j : "building_class"}, inplace = True)
        elif all(mas_by_category[j].isin(BUILDING_TYPES)):
            mas_by_category.rename(columns = {j : "building_type"}, inplace = True)
        elif all(mas_by_category[j].isin(END_USES)):
            mas_by_category.rename(columns = {j : "end_use"}, inplace = True)
        elif all(mas_by_category[j].isin(SPLIT_FUEL)):
            mas_by_category.rename(columns = {j : "split_fuel"}, inplace = True)
        else:
            continue

    for j in mas_overall.columns:
        if all(mas_overall[j].isna()):
            mas_overall.drop(columns = j, inplace = True)
        elif all(mas_overall[j].str.contains(r"^\d{4}")):
            mas_overall[j] = mas_overall[j].apply(int)
            mas_overall.rename(columns = {j : "year"}, inplace = True)
        elif all(mas_overall[j].apply(isfloat)):
            mas_overall[j] = mas_overall[j].apply(float)
            mas_overall.rename(columns = {j : "value"}, inplace = True)
        elif all(mas_overall[j].isin(SCENARIOS)):
            mas_overall.rename(columns = {j : "scenario"}, inplace = True)
        elif all(mas_overall[j].isin(IMPACTS)):
            mas_overall.rename(columns = {j : "impact"}, inplace = True)
        elif all(mas_overall[j].isin(REGIONS)):
            mas_overall.rename(columns = {j : "region"}, inplace = True)
        elif all(mas_overall[j].isin(BUILDING_CLASSES)):
            mas_overall.rename(columns = {j : "building_class"}, inplace = True)
        elif all(mas_overall[j].isin(BUILDING_TYPES)):
            mas_overall.rename(columns = {j : "building_type"}, inplace = True)
        elif all(mas_overall[j].isin(END_USES)):
            mas_overall.rename(columns = {j : "end_use"}, inplace = True)
        elif all(mas_overall[j].isin(SPLIT_FUEL)):
            mas_overall.rename(columns = {j : "split_fuel"}, inplace = True)
        else:
            continue

    return mas_by_category, mas_overall

################################################################################
def extract_lifetime_baseline(df):
    lb = df[(df.lvl2 == "lifetime") & (df.lvl3 == "baseline")]\
            .drop(columns = ["mseg", "lvl2", "lvl3"])\
            .rename(columns = {
                "lvl0" : "scenario",
                "lvl4" : "year",
                "lvl5" : "value"
                })\
            .reset_index(drop = True)

    for j in lb.columns:
        if all(lb[j].isna()):
            lb.drop(columns = j, inplace = True)

    if all(lb.year.str.contains(r"^\d{4}$")):
        lb.year = lb.year.apply(int)
    if all(lb.value.apply(isfloat)):
        lb.value = lb.value.apply(float)

    return lb

################################################################################
def extract_stock(df):
    stock = df[df.lvl2 == "stock"]\
            .drop(columns = ["mseg", "lvl2"])\
            .reset_index(drop = True)

    for j in stock.columns:
        if all(stock[j].isna()):
            stock.drop(columns = j, inplace = True)
        elif all(stock[j].str.contains(r"^\d{4}$")):
            stock[j] = stock[j].apply(int)
            stock.rename(columns = {j : "year"}, inplace = True)
        elif all(stock[j].apply(isfloat)):
            stock[j] = stock[j].apply(float)
            stock.rename(columns = {j : "value"}, inplace = True)
        elif all(stock[j].isin(TOTAL_COMPETED)):
            stock.rename(columns = {j : "total_competed"}, inplace = True)
        elif all(stock[j].isin(ABEM)):
            stock.rename(columns = {j : "abem"}, inplace = True)
        else:
            continue

    return stock

################################################################################
def extract_lifetime_measure(df):
    lm = df[(df.lvl2 == "lifetime") & (df.lvl3 == "measure")]\
            .drop(columns = ["mseg", "lvl2", "lvl3"])\
            .rename(columns = {
                "lvl4" : "value",
                })\
            .reset_index(drop = True)

    for j in lm.columns:
        if all(lm[j].isna()):
            lm.drop(columns = j, inplace = True)

    if all(lm.value.apply(isfloat)):
        lm.value = lm.value.apply(float)

    return lm

################################################################################
def extract_master_mseg(df):
    mm = df[(df.mseg == "master_mseg") & ~(df.lvl2.isin(["cost", "lifetime"]))]\
            .drop(columns = ["mseg"])\
            .reset_index(drop = True)

    for j in mm.columns:
        if all(mm[j].isna()):
            mm.drop(columns = j, inplace = True)
        elif all(mm[j].str.contains(r"^\d{4}$")):
            mm[j] = mm[j].apply(int)
            mm.rename(columns = {j : "year"}, inplace = True)
        elif all(mm[j].apply(isfloat)):
            mm[j] = mm[j].apply(float)
            mm.rename(columns = {j : "value"}, inplace = True)
        elif all(mm[j].isin(TOTAL_COMPETED)):
            mm.rename(columns = {j : "total_competed"}, inplace = True)
        elif all(mm[j].isin(ABEM)):
            mm.rename(columns = {j : "abem"}, inplace = True)
        elif all(mm[j].isin(ECS)):
            mm.rename(columns = {j : "energy_carbon_stock"}, inplace = True)
        else:
            continue


    return mm

################################################################################
def extract_master_mseg_cost(df):
    mmc = df[(df.mseg == "master_mseg") & (df.lvl2 == "cost")]\
            .drop(columns = ["mseg", "lvl2"])\
            .reset_index(drop = True)

    for j in mmc.columns:
        if all(mmc[j].isna()):
            mmc.drop(columns = j, inplace = True)
        elif all(mmc[j].str.contains(r"^\d{4}$")):
            mmc[j] = mmc[j].apply(int)
            mmc.rename(columns = {j : "year"}, inplace = True)
        elif all(mmc[j].apply(isfloat)):
            mmc[j] = mmc[j].apply(float)
            mmc.rename(columns = {j : "value"}, inplace = True)
        elif all(mmc[j].isin(TOTAL_COMPETED)):
            mmc.rename(columns = {j : "total_competed"}, inplace = True)
        elif all(mmc[j].isin(ABEM)):
            mmc.rename(columns = {j : "abem"}, inplace = True)
        elif all(mmc[j].isin(ECS)):
            mmc.rename(columns = {j : "energy_carbon_stock"}, inplace = True)
        else:
            continue

    return mmc

################################################################################
def extract_mseg_out_break(df):
    mob = df[(df.mseg == "mseg_out_break")]\
            .drop(columns = ["mseg"])\
            .reset_index(drop = True)

    # split fuels and years can be in the first column
    for j in range(len(mob.columns)):
        idx1 = mob[mob.columns[j]].str.contains(r"\d{4}$")
        idx2 = mob[mob.columns[j]].isin(SPLIT_FUEL)
        idx = idx1 | idx2
        if all(idx) and (not all(idx1)) and (not all(idx2)):
            if all(mob.loc[idx1, mob.columns[j + 2]].isna()):
                mob.loc[idx1, mob.columns[j + 2]] = mob.loc[idx1, mob.columns[j + 1]]
                mob.loc[idx1, mob.columns[j + 1]] = mob.loc[idx1, mob.columns[j]]
                mob.loc[idx1, mob.columns[j]] = np.nan

    # rename columns, set storage modes
    for j in mob.columns:
        if all(mob[j].isna()):
            mob.drop(columns = j, inplace = True)
        elif all(mob[j].str.contains(r"^\d{4}$")):
            mob[j] = mob[j].apply(int)
            mob.rename(columns = {j : "year"}, inplace = True)
        elif all(mob[j].apply(isfloat)):
            mob[j] = mob[j].apply(float)
            mob.rename(columns = {j : "value"}, inplace = True)
        elif all(mob[j].isin(TOTAL_COMPETED)):
            mob.rename(columns = {j : "total_competed"}, inplace = True)
        elif all(mob[j].isin(ABEM)):
            mob.rename(columns = {j : "abem"}, inplace = True)
        elif all(mob[j].isin(ECS)):
            mob.rename(columns = {j : "energy_carbon_stock"}, inplace = True)
        elif all(mob[j].isin(REGIONS)):
            mob.rename(columns = {j : "region"}, inplace = True)
        elif all(mob[j].isin(BUILDING_CLASSES)):
            mob.rename(columns = {j : "building_class"}, inplace = True)
        elif all(mob[j].isin(BUILDING_TYPES)):
            mob.rename(columns = {j : "building_type"}, inplace = True)
        elif all(mob[j].isin(END_USES)):
            mob.rename(columns = {j : "end_use"}, inplace = True)
        elif all(mob[j].isin(BSE)):
            mob.rename(columns = {j : "baseline_savings_efficient"}, inplace = True)
        elif all(mob[j].isin(ECC)):
            mob.rename(columns = {j : "energy_carbon_cost"}, inplace = True)
        elif all(mob[j].isin(SPLIT_FUEL) | mob[j].isna()):
            mob.rename(columns = {j : "split_fuel"}, inplace = True)
        else:
            continue

    return mob


################################################################################
class ECM_PREP:
    """
    Class: ecm_prep

    Objects:
        lifetime_baseline
        lifetime_baseline

    Methods:

    """
    def __init__(self, path):

        ########################################################################
        # import and format results
        f = open(path, "r")
        data = json.load(f)
        f.close()

        markets = []
        for i in range(len(data)):
            markets.append(json_to_df(data = data[i]["markets"]))
            markets[i]["ecm"] = data[i]["name"]

        markets = pd.concat(markets)

        assert len(markets.columns) - 1 == 9,\
                f"expected ecm_prep to be nine levels deep," +\
                f" got {len(markets.columns)}"

        markets = markets.rename(columns =
                {"lvl0" : "scenario", "lvl1" : "mseg"})

        ########################################################################
        # split the data into several seperate DataFrames
        self.lifetime_baseline = extract_lifetime_baseline(markets)
        self.lifetime_measure = extract_lifetime_measure(markets)

        self.stock = extract_stock(markets)

        self.master_mseg = extract_master_mseg(markets)

        self.master_mseg_cost = extract_master_mseg_cost(markets)

        self.mseg_out_break = extract_mseg_out_break(markets)

    ############################################################################
    def info(self):
        print("Objects:")
        print("  lifetime_baseline: a pandas DataFrame")
        print("  lifetime_measure:  a pandas DataFrame")
        print("  stock:             a pandas DataFrame")
        print("  master_mseg:       a pandas DataFrame")
        print("  master_mseg_cost:  a pandas DataFrame")
        print("  mseg_out_break:    a pandas DataFrame")
        print("Methods:")
        print("  info():")

################################################################################
class ECM_RESULTS:

    def __init__(self, path):

        ########################################################################
        # define objects which will be generated conditionally
        self.emf_aggregation = None # not currently in this version
        self.by_category_aggreation_vs_overall = None

        self.fm_agg_ecms = None # plotly figure, financial metrics
        self.ces_data = None # a DataFrame generated by
                             # generate_cost_effective_savings to build
                             # cost effective saving graphics

        ########################################################################
        # import and format results
        df = json_to_df(path = path)

        self.osg_by_category, self.osg_overall = extract_osg(df)
        df.rename(columns = {"lvl0" : "ecm"}, inplace = True)
        self.financial_metrics = extract_financial_metrics(df)
        self.mas_by_category, self.mas_overall = extract_mas(df)

        return None

    ############################################################################
    def  by_category_vs_overall(self, tol = 1e-8):
         mas = self.mas_by_category\
                 .groupby(["ecm", "scenario", "impact", "year"])\
                 .agg({"value" : "sum"})\
                 .reset_index()\
                 .merge(self.mas_overall,
                         how = "outer",
                         on = ["ecm", "scenario", "impact", "year"],
                         suffixes = ("_aggregated", "_overall")
                         )
         mas["delta"] = mas.value_aggregated - mas.value_overall
         mas = mas[mas.delta > tol]

         osg = self.osg_by_category\
                 .groupby(["impact", "year"])\
                 .agg({"value" : "sum"})\
                 .reset_index()\
                 .merge(self.osg_overall,
                         how = "outer",
                         on = ["impact", "year"],
                         suffixes = ("_aggregated", "_overall")
                         )
         osg["delta"] = osg.value_aggregated - osg.value_overall
         osg = osg[osg.delta > tol]

         self.by_category_aggreation_vs_overall =\
                 {"Markets and Savings" : mas, "On-site Generation"  : osg}

    ############################################################################
    def generate_fm_agg_ecms(self, force = False):
        if (self.fm_agg_ecms is None) or (force):
            self.fm_agg_ecms =\
                    px.line(
                        data_frame = self.financial_metrics\
                            .groupby(["impact", "year"])\
                            .value\
                            .agg(["mean"])\
                            .reset_index(),
                        x = "year",
                        y = "mean",
                        title = "Mean Financial Metric Value by Year",
                        facet_col = "impact",
                        facet_col_wrap = 2,
                        facet_col_spacing = 0.04,
                        markers = True
                        )
            self.fm_agg_ecms.update_yaxes(
                    title = None,
                    matches = None,
                    exponentformat = "B",
                    showticklabels = True,
                    gridcolor = "lightgrey"
                    )
            self.fm_agg_ecms.update_xaxes(
                    title = None,
                    tick0 = 2025,
                    dtick = 5,
                    gridcolor = "lightgrey"
                    )
            self.fm_agg_ecms.for_each_annotation(
                    lambda a: a.update(text = a.text.split("=")[-1])
                    )
            self.fm_agg_ecms.for_each_annotation(
                    lambda a: a.update(text = a.text.replace(" (", "<br>("))
                    )
            self.fm_agg_ecms.update_layout(
                    autosize = False,
                    width = 1175,
                    height = 875,
                    plot_bgcolor = "whitesmoke", #"rgba(0, 0, 0, 0)"
                    )
        return self.fm_agg_ecms

    ############################################################################
    def generate_fm_by_ecm(self, ecm = None, force = False):
        if (ecm is not None):
            if (not any(self.financial_metrics.ecm == ecm)):
                # warning ECM UNDEFINED, setting to None
                # This logic is not needed for dash app, will be needed to deal
                # with actual end users.
                ecm = None

        if (ecm is None):
            fig = px.line(
                    data_frame = self.financial_metrics,
                    x = "year",
                    y = "value",
                    color = "ecm",
                    facet_col = "impact",
                    facet_col_wrap = 2,
                    facet_col_spacing = 0.05,
                    markers = True
                    )
            fig.update_yaxes(
                    title = None,
                    matches = None,
                    exponentformat = "B",
                    showticklabels = True,
                    gridcolor = "lightgrey"
                    )
            fig.update_xaxes(
                    title = None,
                    tick0 = 2025,
                    dtick = 5,
                    gridcolor = "lightgrey"
                    )
            fig.for_each_annotation(
                    lambda a: a.update(text = a.text.split("=")[-1])
                    )
            fig.for_each_annotation(
                    lambda a: a.update(text = a.text.replace(" (", "<br>("))
                    )
            fig.update_layout(
                    autosize = False,
                    width = 1175,
                    height = 875,
                    plot_bgcolor = "whitesmoke", #"rgba(0, 0, 0, 0)",
                    legend = {
                        "title" : "ECM"
                        }
                    )
        else:
            fig = px.line(
                    data_frame =
                      self.financial_metrics[self.financial_metrics.ecm == ecm],
                    x = "year",
                    y = "value",
                    facet_col = "impact",
                    facet_col_wrap = 2,
                    facet_col_spacing = 0.04,
                    markers = True
                    )
            fig.update_yaxes(
                    title = None,
                    matches = None,
                    exponentformat = "B",
                    showticklabels = True,
                    gridcolor = "lightgrey"
                    )
            fig.update_xaxes(
                    title = None,
                    tick0 = 2025,
                    dtick = 5,
                    gridcolor = "lightgrey"
                    )
            fig.for_each_annotation(
                    lambda a: a.update(text = a.text.split("=")[-1])
                    )
            fig.for_each_annotation(
                    lambda a: a.update(text = a.text.replace(" (", "<br>("))
                    )
            fig.update_layout(
                    autosize = False,
                    width = 1175,
                    height = 875,
                    plot_bgcolor = "whitesmoke", #"rgba(0, 0, 0, 0)"
                    )

        return fig

    ############################################################################
    def generate_cost_effective_savings(self, m, year, end_uses, building_classes, building_types, force = False):
        self.ces_data = self.mas_by_category.copy(deep = True)

        if len(end_uses) > 0:
            self.ces_data =\
                self.ces_data[self.mas_by_category.end_use.isin(end_uses)]
        if (building_classes[0] is not None) and (len(building_classes) > 0) :
            self.ces_data =\
                self.ces_data[self.mas_by_category.building_class.isin(building_classes)]
        if (building_types[0] is not None) and (len(building_types) > 0) :
            self.ces_data =\
                self.ces_data[self.mas_by_category.building_type.isin(building_types)]

        agg_dict = {
                "value" : "sum",
                "region" : unique_strings,
                "end_use" : unique_strings}

        pivot_index = ["scenario", "ecm", "end_use", "year"]

        if "building_class" in self.ces_data.columns:
            agg_dict["building_class"] = unique_strings
            pivot_index.append("building_class")

        if "building_type" in self.ces_data.columns:
            agg_dict["building_type"] = unique_strings
            pivot_index.append("building_type")

        self.ces_data =\
                self.ces_data\
                    .groupby(["scenario", "ecm", "impact", "year"])\
                    .agg(agg_dict)\
                    .reset_index()


        self.ces_data = \
                pd.pivot_table(self.ces_data,
                        values = "value",
                        index = pivot_index,
                        columns = ["impact"]
                        )\
                .reset_index()\
                .merge(self.financial_metrics,
                        how = "left",
                        on = ["ecm", "year"])

        fig = px.scatter(
                    self.ces_data[(self.ces_data.year == year)],
                x = m,
                y = "value",
                #symbol = "building_class",
                #color = "end_use",
                facet_col = "scenario",
                facet_row = "impact",
                hover_data = {
                    "ecm": True,
                    m : True,
                    "value": True,
                    "end_use": True#,
                    #"building_class": True,
                    #"building_type": True
                    }
                )

        fig.update_yaxes(
                title_text = "",
                matches = None,
                exponentformat = "B",
                gridcolor = "lightgrey"
                )
        fig.update_xaxes(
                exponentformat = "B",
                gridcolor = "lightgrey"
                )
        fig.for_each_annotation(
                lambda a: a.update(text=a.text.split("=")[-1])
                )
        fig.for_each_annotation(
                lambda a: a.update(text = a.text.replace(" (", "<br>("))
                )
        fig.update_layout(
                autosize = False,
                width = 1175,
                height = 875,
                plot_bgcolor = "whitesmoke", #"rgba(0, 0, 0, 0)",
                showlegend = False
                )

        return fig

    ############################################################################
    def generate_total_savings(self, m, by, annual_or_cumulative, force = False):

        a_data = self.mas_by_category\
            .sort_values(by = ["scenario", "impact", "year"])\
            .groupby([j for j in ["scenario", "impact", "year", by] if j is not None])\
            .agg({"value" : "sum"})\
            .reset_index()
        c_data = self.mas_by_category\
            .sort_values(by = ["scenario", "impact", "year"])\
            .groupby([j for j in ["scenario", "impact", "year", by] if j is not None])\
            .agg({"value" : "sum"})\
            .groupby(level = [j for j in ["scenario", "impact", by] if j is not None])\
            .cumsum()\
            .reset_index()
        a_data["total"] = "annual"
        c_data["total"] = "cumulative"
        plot_data = pd.concat([a_data, c_data])

        # legend title
        if by is not None:
            lgnd_title = by.replace("_", " ").title()
        else:
            lgnd_title = None

        fig = px.line(
                  plot_data[((plot_data.impact == m) &
                             (plot_data.total == annual_or_cumulative))],
                  x = "year",
                  y = "value",
                  color = by,
                  facet_col = "scenario",
                  markers = True
                )
        fig.update_traces(mode = "lines+markers")
        fig.update_yaxes(
                exponentformat = "B",
                title = None,
                gridcolor = "lightgrey"
                )
        fig.update_xaxes(
                tick0 = 2025,
                dtick = 5,
                title = None,
                gridcolor = "lightgrey"
                )
        fig.for_each_annotation(
                lambda a: a.update(text=a.text.split("=")[-1])
                )
        fig.for_each_annotation(
                lambda a: a.update(text = a.text.replace(" (", "<br>("))
                )
        fig.update_layout(
                title = m,
                autosize = False,
                width = 1175,
                height = 875,
                plot_bgcolor = "whitesmoke", #"rgba(0, 0, 0, 0)",
                legend = {
                    "x" : 0.02,
                    "y" : 0.98,
                    "title" : lgnd_title,
                    "bordercolor" : "black",
                    "borderwidth" : 2
                    }
                )

        return fig



    ############################################################################
    def info(self):
        info_str = """
Objects:
    * DataFrames
      * mas_by_category:   Markets and Savings (by Category)
      * mas_overall:       Markets and Savings (Overall)
      * financial_metrics: Financial Metrics
      * financial_metrics_thresholds: Financial Metrics thresholds
      * filter_variables:  Filter Variables
      * osg_by_category:   On-site Generation (by Category)
      * osg_overall:       On-site Generation (Overall)

Methods:
    * info():
      - Displays this info about the components of the class
    * by_category_aggregation_vs_overall(tol = 1e-8):
      - Returns a DataFrames showing the differences between the "by category"
        and "Overall" value exceeding the given tol(erance).
    * generate_fm_agg_ecms(force = False):
      - generate a plotly object showing the annual summaries of each financial
        metric overall all ECMs.  If the object already exists then nothing is
        done, force the rebuild by setting `force = True`.
    * generate_fm_by_ecm(ecm = None, force = True):
      - generate a plotly object showing the annual value for each financial
        metric by the specified ecm.  if `ecm = None` then all ecms will be
        shown in one graphic.
        """
        print(info_str)

################################################################################
#                                 End of File                                  #
################################################################################

