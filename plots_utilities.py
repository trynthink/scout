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
        self.lifetime_baseline =\
                markets[
                        (markets.lvl2 == "lifetime") &
                        (markets.lvl3 == "baseline")
                        ]

        self.lifetime_measure =\
                markets[
                        (markets.lvl2 == "lifetime") &
                        (markets.lvl3 == "measure")
                        ]

        self.stock = markets[markets.lvl2 == "stock"]

        self.master_mseg =\
                markets[
                        (markets.mseg == "master_mseg") &
                        (markets.lvl2 != "cost")
                        ]

        self.master_mseg_cost =\
                markets[
                        (markets.mseg == "master_mseg") &
                        (markets.lvl2 == "cost")
                        ]

        self.mseg_out_break = markets[markets.mseg == "mseg_out_break"]

        ########################################################################
        # clean up lifetime_baseline
        self.lifetime_baseline =\
                self.lifetime_baseline\
                .drop(columns =
                        ["mseg", "lvl2", "lvl3", "lvl6", "lvl7", "lvl8"]
                     )\
                .rename(columns = {"lvl4" : "year", "lvl5" : "value"})\
                .reset_index(drop = True)

        ########################################################################
        # clean up lifetime_measure
        self.lifetime_measure =\
                self.lifetime_measure\
                .drop(columns =
                        ["mseg", "lvl2", "lvl3", "lvl5", "lvl6", "lvl7", "lvl8"]
                     )\
                .rename(columns = {"lvl4" : "value"})\
                .reset_index(drop = True)

        ########################################################################
        # clean up stock
        self.stock = \
                self.stock\
                .drop(columns = ["lvl2", "lvl7", "lvl8"])\
                .rename(columns = {
                    "lvl3" : "total_or_competed",
                    "lvl4" : "measure_or_all",
                    "lvl5" : "year",
                    "lvl6" : "value"})\
                .reset_index(drop = True)

        ########################################################################
        # Clean up master_mseg
        self.master_mseg = \
                self.master_mseg\
                .drop(columns = ["mseg", "lvl7", "lvl8"])\
                .reset_index(drop = True)

        # move values from one column to another as needed
        idx = (self.master_mseg.lvl6.isna()) & (self.master_mseg.lvl5.notna())
        self.master_mseg.loc[idx, "lvl6"] = self.master_mseg.loc[idx, "lvl5"]
        self.master_mseg.loc[idx, "lvl5"] = self.master_mseg.loc[idx, "lvl4"]
        self.master_mseg.loc[idx, "lvl4"] = None

        idx = (self.master_mseg.lvl6.isna()) &\
                (self.master_mseg.lvl5.isna()) &\
                (self.master_mseg.lvl4.notna())
        self.master_mseg.loc[idx, "lvl6"] = self.master_mseg.loc[idx, "lvl4"]
        self.master_mseg.loc[idx, "lvl4"] = self.master_mseg.loc[idx, "lvl3"]
        self.master_mseg.loc[idx, "lvl3"] = None

        self.master_mseg\
                .rename(columns = {
                    "lvl3" : "total_or_competed",
                    "lvl4" : "baseline_measure",
                    "lvl5" : "year",
                    "lvl6" : "value"},
                    inplace = True)

        ########################################################################
        # clean up master_mseg_cost
        self.master_mseg_cost = \
                self.master_mseg_cost\
                .drop(columns = ["mseg", "lvl2", "lvl8"])\
                .rename(columns = {
                    "lvl3" : "impact",
                    "lvl4" : "total_or_competed",
                    "lvl5" : "baseline_efficient",
                    "lvl6" : "year",
                    "lvl7" : "value"})\
                .reset_index(drop = True)
        self.master_mseg_cost.loc[
                self.master_mseg_cost.impact == "stock", "impact"] = "capital"
        self.master_mseg_cost.loc[
                self.master_mseg_cost.impact == "energy", "impact"] =\
                        "utility bill"
        self.master_mseg_cost.loc[
                self.master_mseg_cost.impact == "carbon", "impact"] =\
                        "social cost"

        ########################################################################
        # clean up mseg_out_break
        self.mseg_out_break = \
                self.mseg_out_break\
                .drop(columns = ["mseg"])\
                .rename(columns = {
                    "lvl2" : "impact",
                    "lvl3" : "baseline_efficient_savings",
                    "lvl4" : "region",
                    "lvl5" : "building_class",
                    "lvl6" : "end_use",
                    "lvl7" : "year",
                    "lvl8" : "value"})\
                .reset_index(drop = True)

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
def import_ecm_results(path) :
    """
    Function: import_ecm_results

        Parse a ecm_results.json file and return a useful pandas DataFrame for
        plotting

    Arguments:
        path file path to the ecm_results.json file

    Return:
        A pandas DataFrame
    """
################################################################################
#                                 End of File                                  #
################################################################################

