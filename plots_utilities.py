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
class ECM_RESULTS:
    def __init__(self, path):

        ########################################################################
        # define objects which will be generated conditionally
        self.emf_aggregation = None # not currently in this version
        self.by_category_aggreation_vs_overall = None

        self.fm_agg_year = None # plotly figure, financial metrics
        self.ces_data = None # a DataFrame generated by
                             # generate_cost_effective_savings to build
                             # cost effective saving graphics

        ########################################################################
        # import and format results
        df = json_to_df(path = path)

        assert len(df.columns) == 9, f"Expected {path} to be nine levels deep"+\
                f" got {len(df.columns)}."

        # build individual DataFrames - start by splitting up the df
        osg  = df[df.lvl0 == "On-site Generation"].drop(columns = ["lvl0"])
        ecms = df[df.lvl0 != "On-site Generation"]

        # we can rename one of the columns for ecms
        ecms = ecms.rename(columns = {"lvl0" : "ecm"})

        # ecms will be split out further:
        financial_metrics  = ecms[ecms.lvl1 == "Financial Metrics"]
        filter_variables   = ecms[ecms.lvl1 == "Filter Variables"]
        mas                = ecms[(
                                    (ecms.lvl1 != "Financial Metrics") &
                                    (ecms.lvl1 != "Filter Variables")
                                 )]

        # NOTE: additionally, the osg and mas will be split after some cleaning
        # steps into _by_category and _overall

        ########################################################################
        # clean up the on-site generation DataFrame
        assert all(osg.lvl7.isna())
        assert all(osg.lvl8.isna())
        osg = osg.drop(columns = ["lvl7", "lvl8"])

        # The "Overall" version needs to have the year and value shifted right
        # two columns
        idx = osg.lvl2 == "Overall"
        osg.loc[idx, "lvl6"] = osg.loc[idx, "lvl4"]
        osg.loc[idx, "lvl5"] = osg.loc[idx, "lvl3"]

        osg.loc[idx, "lvl4"] = np.nan
        osg.loc[idx, "lvl3"] = np.nan

        # rename columns in the osg frame for human ease of use
        osg.rename(columns = {
            "lvl1" : "impact",
            # "lvl2" : "version" # "By Category" or "Overall"; will be dropped
            "lvl3" : "region",
            "lvl4" : "building_type",
            "lvl5" : "year",
            "lvl6" : "value"},
            inplace = True)

        # set data types
        assert all(osg.value.apply(isfloat))
        osg.value = osg.value.apply(float)

        assert all(osg.year.str.contains(r"^\d{4}$"))
        osg.year = osg.year.apply(int)

        self.osg_by_category =\
                osg[osg.lvl2 == "By Category"]\
                .drop(columns = ["lvl2"])

        self.osg_overall =\
                osg[osg.lvl2 != "By Category"]\
                .drop(columns = ["lvl2", "region", "building_type"])

        ########################################################################
        # clean up filter_variables
        filter_variables = filter_variables.pivot(
                index = ["ecm"],
                columns = ["lvl2"],
                values  = ["lvl3"]
                )

        filter_variables = filter_variables.reset_index(col_level = 1)
        filter_variables.columns = filter_variables.columns.map(lambda t: t[1])

        self.filter_variables = filter_variables

        ########################################################################
        # markets_and_savings
        mas = mas.rename(columns = {
            # "lvl1" : "version", -- by Category or Overall; will be dropped
            "lvl2" : "scenario",
            "lvl3" : "impact",
            "lvl4" : "region",
            "lvl5" : "building_class",
            "lvl6" : "end_use",
            "lvl7" : "year",
            "lvl8" : "value"
            })

        # For the "Overall" set there are no region, building_class, or end_use.
        # Move the to the correct column.
        idx = mas.lvl1 == "Markets and Savings (Overall)"
        assert all(mas[idx].value.isna())
        assert all(mas[idx].year.isna())
        assert all(mas[idx].end_use.isna())

        mas.loc[idx, "value"] = mas.loc[idx, "building_class"]
        mas.loc[idx, "year"]  = mas.loc[idx, "region"]
        mas.loc[idx, "building_class"] = np.nan
        mas.loc[idx, "region"] = np.nan

        # set data types
        assert all(mas.value.apply(isfloat))
        mas.value = mas.value.apply(float)

        assert all(mas.year.str.contains("^\d{4}$"))
        mas.year = mas.year.apply(int)

        self.mas_by_category =\
                mas[mas.lvl1 == "Markets and Savings (by Category)"]\
                .drop(columns = ["lvl1"])

        self.mas_overall =\
                mas[mas.lvl1 == "Markets and Savings (Overall)"]\
                .drop(columns = ["lvl1", "region", "building_class", "end_use"])

        ########################################################################
        # # clean up financial_metrics
        financial_metrics = financial_metrics[["ecm", "lvl2", "lvl3", "lvl4"]]
        financial_metrics = financial_metrics.rename(columns =
                {"lvl2" : "impact", "lvl3" : "year", "lvl4" : "value"})

        # set data types
        assert all(financial_metrics.value.apply(isfloat))
        financial_metrics.value = financial_metrics.value.apply(float)

        assert all(financial_metrics.year.str.contains("^\d{4}$"))
        financial_metrics.year = financial_metrics.year.apply(int)

        self.financial_metrics =\
                financial_metrics.sort_values(by = ["ecm", "impact", "year"])

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
    def generate_fm_agg_year(self, force = False):
        if (self.fm_agg_year is None) or (force):
            self.fm_agg_year =\
                    px.line(data_frame = self.financial_metrics\
                            .groupby(["impact", "year"])\
                            .value\
                            .agg(["mean"])\
                            .reset_index()
                        , x = "year"
                        , y = "mean"
                        , title = "Mean Financial Metric Value by Year"
                        , facet_col = "impact"
                        , facet_col_wrap = 2
                        )
            self.fm_agg_year.update_yaxes(matches = None, exponentformat = "e")
            self.fm_agg_year.for_each_annotation(lambda a: a.update(text = a.text.split("=")[-1]))
            self.fm_agg_year.for_each_annotation(lambda a: a.update(text = a.text.replace(" (", "<br>(")))
            self.fm_agg_year.update_layout(autosize = False, width = 900, height = 900)
        return self.fm_agg_year

    ############################################################################
    def generate_fm_by_ecm(self, ecm = None, force = False):
        if (ecm is not None):
            if (not any(self.financial_metrics.ecm == ecm)):
                # warning ECM UNDEFINED, setting to None
                # This logic is not needed for dash app, will be needed to deal
                # with actual end users.
                ecm = None

        if (ecm is None):
            fig = px.line(data_frame = self.financial_metrics
                    , x = "year"
                    , y = "value"
                    , color = "ecm"
                    , facet_col = "impact"
                    , facet_col_wrap = 2
                    )
            fig.update_yaxes(matches = None, exponentformat = "e")
            fig.for_each_annotation(lambda a: a.update(text = a.text.split("=")[-1]))
            fig.for_each_annotation(lambda a: a.update(text = a.text.replace(" (", "<br>(")))
            fig.update_layout(autosize = False, width = 900, height = 900)
        else:
            fig = px.line(data_frame = self.financial_metrics[self.financial_metrics.ecm == ecm]
                    , x = "year"
                    , y = "value"
                    , facet_col = "impact"
                    , facet_col_wrap = 2
                    )
            fig.update_yaxes(matches = None, exponentformat = "e")
            fig.for_each_annotation(lambda a: a.update(text = a.text.split("=")[-1]))
            fig.for_each_annotation(lambda a: a.update(text = a.text.replace(" (", "<br>(")))
            fig.update_layout(autosize = False, width = 900, height = 900)

        return fig

    ############################################################################
    def generate_cost_effective_savings(self, m, year, force = False):
        if (self.ces_data is None) or (force):
            self.ces_data =\
                self.mas_by_category\
                        .groupby(["scenario", "ecm", "impact", "year"])\
                        .agg({
                            "value" : "sum",
                            "building_class" : unique_strings,
                            "region" : unique_strings,
                            "end_use" : unique_strings
                            })\
                        .reset_index()
            self.ces_data = \
                    pd.pivot_table(self.ces_data,
                            values = "value",
                            index = ["scenario", "ecm", "building_class", "end_use", "year"],
                            columns = ["impact"]
                            )\
                    .reset_index()\
                    .merge(self.financial_metrics,
                            how = "left",
                            on = ["ecm", "year"])

        fig = px.scatter(
                    self.ces_data[(self.ces_data.year == year)]
                , x = m
                , y = "value"
                , symbol = "building_class"
                , color = "end_use"
                , facet_col = "scenario"
                , facet_row = "impact"
                , hover_data = {
                    "ecm": True,
                    m : True,
                    "value": True,
                    "end_use": True,
                    "building_class": True
                    }
                )
        fig.update_yaxes(title_text = "", matches = None, exponentformat = "e")
        fig.update_xaxes(exponentformat = "e")
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.for_each_annotation(lambda a: a.update(text = a.text.replace(" (", "<br>(")))
        fig.update_layout(autosize = False, width = 1200, height = 800)

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

        fig = px.line(
                  plot_data[((plot_data.impact == m) & (plot_data.total == annual_or_cumulative))]
                , x = "year"
                , y = "value"
                , color = by
                , facet_col = "scenario"
                , markers = True
                )
        fig.update_traces(mode = "lines+markers")
        fig.update_yaxes(exponentformat = "e", title = m)
        fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
        fig.for_each_annotation(lambda a: a.update(text = a.text.replace(" (", "<br>(")))
        fig.update_layout(autosize = False, width = 1200, height = 800)

        return fig



    ############################################################################
    def info(self):
        info_str = """
Objects:
    * DataFrames
      * mas_by_category:   Markets and Savings (by Category)
      * mas_overall:       Markets and Savings (Overall)
      * financial_metrics: Financial Metrics
      * filter_variables:  Filter Variables
      * osg_by_category:   On-site Generation (by Category)
      * osg_overall:       On-site Generation (Overall)

Methods:
    * info():
      - Displays this info about the components of the class
    * by_category_aggregation_vs_overall(tol = 1e-8):
      - Returns a DataFrames showing the differences between the "by category"
        and "Overall" value exceeding the given tol(erance).
    * generate_fm_agg_year(force = False):
      - generate a plotly object showing the annual summaries of each financial
        metric overall all ECMs.  If the object already exists then nothing is
        done, force the rebuild by setting `force = True`.
    * generate_fm_by_ecm(ecm = None, force = True):
      - generate a plotly object showing the annual value for each financial
        metric by the specified ecm.  if `ecm = None` then all ecms will be
        shown in one graphic.
        """
        print(info_str)
        #print("Methods")
        #print("  * by_category_vs_overall(tol = 1e-8):")
        #print("      - returns DataFrames showing the differences between the"+\
        #        "By Category' and 'Overall' exceeding the tol(erance).")
        #print("  * plot_fm_agg_year():")
        #print("      - returns plotly object plotting ")

################################################################################
#                                 End of File                                  #
################################################################################

