#!/usr/bin/env python3
import json
import numpy
import copy
import re
from numpy.linalg import LinAlgError
from collections import OrderedDict
import gzip
import pickle
from os import getcwd
from ast import literal_eval


class UsefulInputFiles(object):
    """Class of input files to be opened by this routine.

    Attributes:
        meas_summary_data (string): High-level measure summary data.
        meas_compete_data (string): Contributing microsegment data needed
            for measure competition.
        active_measures (string): Measures that are active for the analysis.
        meas_engine_out (string): Measure output summaries.
    """

    def __init__(self):
        self.meas_summary_data = \
            "/supporting_data/ecm_prep.json"
        self.meas_compete_data = "/supporting_data/ecm_competition_data"
        self.active_measures = "/run_setup.json"
        self.meas_engine_out = "/results/ecm_results.json"


class UsefulVars(object):
    """Class of variables that are used globally across functions.

    Attributes:
        adopt_schemes (list): Possible consumer adoption scenarios.
        aeo_years (list) = Modeling time horizon.
        discount_rate (float): General rate to use in discounting cash flows.
        com_timeprefs (dict): Time preference premiums for commercial adopters.
        out_break_czones (OrderedDict): Maps measure climate zone names to
            the climate zone categories used in summarizing measure outputs.
        out_break_bldgtypes (OrderedDict): Maps measure building type names to
            the building sector categories used in summarizing measure outputs.
        out_break_enduses (OrderedDict): Maps measure end use names to
            the end use categories used in summarizing measure outputs.
    """

    def __init__(self):
        self.adopt_schemes = ['Technical potential', 'Max adoption potential']
        # Set minimum AEO modeling year
        aeo_min = 2009
        # Set maximum AEO modeling year
        aeo_max = 2040
        # Derive time horizon from min/max years
        self.aeo_years = [
            str(i) for i in range(aeo_min, aeo_max + 1)]
        self.discount_rate = 0.07
        self.com_timeprefs = {
            "rates": [10.0, 1.0, 0.45, 0.25, 0.15, 0.065, 0.0],
            "distributions": {
                "heating": {
                    key: [0.265, 0.226, 0.196, 0.192, 0.105, 0.013, 0.003]
                    for key in self.aeo_years},
                "cooling": {
                    key: [0.264, 0.225, 0.193, 0.192, 0.106, 0.016, 0.004]
                    for key in self.aeo_years},
                "water heating": {
                    key: [0.263, 0.249, 0.212, 0.169, 0.097, 0.006, 0.004]
                    for key in self.aeo_years},
                "ventilation": {
                    key: [0.265, 0.226, 0.196, 0.192, 0.105, 0.013, 0.003]
                    for key in self.aeo_years},
                "cooking": {
                    key: [0.261, 0.248, 0.214, 0.171, 0.097, 0.005, 0.004]
                    for key in self.aeo_years},
                "lighting": {
                    key: [0.264, 0.225, 0.193, 0.193, 0.085, 0.013, 0.027]
                    for key in self.aeo_years},
                "refrigeration": {
                    key: [0.262, 0.248, 0.213, 0.170, 0.097, 0.006, 0.004]
                    for key in self.aeo_years}}}
        self.out_break_czones = OrderedDict([
            ('AIA CZ1', 'AIA_CZ1'), ('AIA CZ2', 'AIA_CZ2'),
            ('AIA CZ3', 'AIA_CZ3'), ('AIA CZ4', 'AIA_CZ4'),
            ('AIA CZ5', 'AIA_CZ5')])
        self.out_break_bldgtypes = OrderedDict([
            ('Residential (New)', [
                'new', 'single family home', 'multi family home',
                'mobile home']),
            ('Residential (Existing)', [
                'existing', 'single family home', 'multi family home',
                'mobile home'],),
            ('Commercial (New)', [
                'new', 'assembly', 'education', 'food sales',
                'food service', 'health care', 'mercantile/service',
                'lodging', 'large office', 'small office', 'warehouse',
                'other']),
            ('Commercial (Existing)', [
                'existing', 'assembly', 'education', 'food sales',
                'food service', 'health care', 'mercantile/service',
                'lodging', 'large office', 'small office', 'warehouse',
                'other'])])
        self.out_break_enduses = OrderedDict([
            ('Heating', ["heating", "secondary heating"]),
            ('Cooling', ["cooling"]),
            ('Ventilation', ["ventilation"]),
            ('Lighting', ["lighting"]),
            ('Water Heating', ["water heating"]),
            ('Refrigeration', ["refrigeration", "other (grid electric)"]),
            ('Computers and Electronics', [
                "PCs", "non-PC office equipment", "TVs", "computers"]),
            ('Other', ["cooking", "drying", "MELs", "other (grid electric)"])])


class Measure(object):
    """Class representing individual efficiency measures.

    Attributes:
        **kwargs: Arbitrary keyword arguments used to fill measure attributes
            from an input dictionary.
        update_results (dict): Flags markets, savings, and financial metric
            outputs that have yet to be finalized by the analysis engine.
        markets (dict): Data grouped by adoption scheme on:
            a) 'master_mseg': a measure's master market microsegments (stock,
               energy, carbon, cost),
            b) 'mseg_adjust': all microsegments that contribute to each master
               microsegment (required later for measure competition).
            c) 'mseg_out_break': master microsegment breakdowns by key
               variables (e.g., climate zone, building type, end use, etc.)
        savings (dict): Energy, carbon, and stock, energy, and carbon cost
            savings for measure over baseline technology case.
        portfolio_metrics (dict): Financial metrics relevant to assessing a
            large portfolio of efficiency measures (e.g., CCE, CCC).
        consumer_metrics (dict): Financial metrics relevant to the adoption
            decisions of individual consumers (e.g., NPV, IRR, payback).
    """

    def __init__(self, handyvars, **kwargs):
        # Read Measure object attributes from measures input JSON
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.savings, self.portfolio_metrics, self.consumer_metrics = (
            {} for n in range(3))
        self.update_results = {
            "savings and portfolio metrics": {},
            "consumer metrics": True}
        # Convert any master market microsegment data formatted as lists to
        # numpy arrays
        self.convert_to_numpy(self.markets)
        for adopt_scheme in handyvars.adopt_schemes:
            # Initialize 'uncompeted' and 'competed' versions of
            # Measure markets (initially, they are identical)
            self.markets[adopt_scheme] = {
                "uncompeted": copy.deepcopy(self.markets[adopt_scheme]),
                "competed": copy.deepcopy(self.markets[adopt_scheme])}
            self.update_results["savings and portfolio metrics"][
                adopt_scheme] = {"uncompeted": True, "competed": True}
            self.savings[adopt_scheme] = {
                "uncompeted": {
                    "stock": {
                        "cost savings (total)": None,
                        "cost savings (annual)": None},
                    "energy": {
                        "savings (total)": None,
                        "savings (annual)": None,
                        "cost savings (total)": None,
                        "cost savings (annual)": None},
                    "carbon": {
                        "savings (total)": None,
                        "savings (annual)": None,
                        "cost savings (total)": None,
                        "cost savings (annual)": None}},
                "competed": {
                    "stock": {
                        "cost savings (total)": None,
                        "cost savings (annual)": None},
                    "energy": {
                        "savings (total)": None,
                        "savings (annual)": None,
                        "cost savings (total)": None,
                        "cost savings (annual)": None},
                    "carbon": {
                        "savings (total)": None,
                        "savings (annual)": None,
                        "cost savings (total)": None,
                        "cost savings (annual)": None}}}
            self.portfolio_metrics[adopt_scheme] = {
                "uncompeted": {
                    "cce": None,
                    "cce (w/ carbon cost benefits)": None,
                    "ccc": None,
                    "ccc (w/ energy cost benefits)": None},
                "competed": {
                    "cce": None,
                    "cce (w/ carbon cost benefits)": None,
                    "ccc": None,
                    "ccc (w/ energy cost benefits)": None}}
            self.consumer_metrics = {
                "anpv": {
                    "stock cost": None,
                    "energy cost": None,
                    "carbon cost": None},
                "irr (w/ energy costs)": None,
                "irr (w/ energy and carbon costs)": None,
                "payback (w/ energy costs)": None,
                "payback (w/ energy and carbon costs)": None}

    def convert_to_numpy(self, markets):
        """Convert terminal/leaf node lists in a dict to numpy arrays.

        Args:
            markets (dict): Input dict with possible lists at terminal/leaf
                nodes.
        """
        for k, i in markets.items():
            if isinstance(i, dict):
                self.convert_to_numpy(i)
            else:
                if isinstance(markets[k], list):
                    markets[k] = numpy.array(markets[k])


class Engine(object):
    """Class representing a collection of efficiency measures.

    Attributes:
        handyvars (object): Global variables useful across class methods.
        measures (list): List of active measure objects to be analyzed.
        output (OrderedDict): Summary results data for all active measures.
    """

    def __init__(self, handyvars, measure_objects):
        self.handyvars = handyvars
        self.measures = measure_objects
        self.output = OrderedDict()
        for m in self.measures:
            # Set measure climate zone, building sector, and end use
            # output category names for use in filtering and/or breaking
            # out results
            czones, bldgtypes, end_uses = ([] for n in range(3))
            # Find measure climate zone output categories
            for cz in self.handyvars.out_break_czones.items():
                if any([x in cz[1] for x in m.climate_zone]) and \
                        cz[0] not in czones:
                    czones.append(cz[0])
            # Find measure building sector output categories
            for bldg in self.handyvars.out_break_bldgtypes.items():
                if any([x in bldg[1] for x in m.bldg_type]) and \
                        bldg[0] not in bldgtypes:
                    bldgtypes.append(bldg[0])
            # Find measure end use output categories
            for euse in self.handyvars.out_break_enduses.items():
                if any([x in euse[1] for x in m.end_use["primary"]]) and \
                        euse[0] not in end_uses:
                    end_uses.append(euse[0])
            # Set measure climate zone(s), building sector(s), and end use(s)
            # as filter variables
            self.output[m.name] = OrderedDict([
                ("Filter Variables", OrderedDict([
                    ("Applicable Climate Zones", czones),
                    ("Applicable Building Classes", bldgtypes),
                    ("Applicable End Uses", end_uses)])),
                ("Markets and Savings (Overall)", OrderedDict()),
                ("Markets and Savings (by Category)", OrderedDict()),
                ("Financial Metrics", OrderedDict([
                    ("Portfolio Level", OrderedDict()),
                    ("Consumer Level", OrderedDict())]))])
            for adopt_scheme in self.handyvars.adopt_schemes:
                # Initialize measure overall markets and savings
                self.output[m.name]["Markets and Savings (Overall)"][
                    adopt_scheme] = OrderedDict()
                # Initialize measure markets and savings broken out by climate
                # zone, building sector, and end use categories
                self.output[m.name]["Markets and Savings (by Category)"][
                    adopt_scheme] = OrderedDict()
                # Initialize measure financial metrics
                self.output[m.name]["Financial Metrics"]["Portfolio Level"][
                    adopt_scheme] = OrderedDict()

    def calc_savings_metrics(self, adopt_scheme, comp_scheme):
        """Calculate and update measure savings and financial metrics.

        Notes:
            Given information on measure master microsegments for
            each projection year, determine stock, energy, and carbon
            cost savings; energy and carbon savings; and the net present
            value, internal rate of return, simple payback, cost of
            conserved energy, and cost of conserved carbon for the measure.

        Args:
            adopt_scheme (string): Assumed consumer adoption scenario.
            comp_scheme (string): Assumed measure competition scenario.
        """
        # Find all active measures that require savings updates
        measures_update = [m for m in self.measures if m.update_results[
            "savings and portfolio metrics"][
            adopt_scheme][comp_scheme] is True]

        # Update measure savings and associated financial metrics
        for m in measures_update:
            # Set measure master microsegments for the current adoption and
            # competition schemes
            markets = m.markets[adopt_scheme][comp_scheme]["master_mseg"]

            # Initialize stock cost, energy/energy cost savings, carbon/
            # carbon cost savings, and economic metrics dicts
            scostsave_tot, scostsave, esave_tot, esave, ecostsave_tot, \
                ecostsave, csave_tot, csave, ccostsave_tot, ccostsave, \
                stock_anpv, energy_anpv, carb_anpv, irr_e, irr_ec, \
                payback_e, payback_ec, cce, cce_bens, ccc, ccc_bens = (
                    {} for d in range(21))

            # Calculate stock cost savings, energy/carbon savings, and
            # energy/carbon cost savings for each projection year
            for yr in self.handyvars.aeo_years:
                # Calculate total annual energy/carbon and stock/energy/carbon
                # cost savings for the measure vs. baseline. Total savings
                # reflect the impact of all measure adoptions simulated up
                # until and including the current year of the modeling time
                # horizon
                esave_tot[yr] = \
                    markets["energy"]["total"]["baseline"][yr] - \
                    markets["energy"]["total"]["efficient"][yr]
                csave_tot[yr] = \
                    markets["carbon"]["total"]["baseline"][yr] - \
                    markets["carbon"]["total"]["efficient"][yr]
                scostsave_tot[yr] = \
                    markets["cost"]["stock"]["total"]["baseline"][yr] - \
                    markets["cost"]["stock"]["total"]["efficient"][yr]
                ecostsave_tot[yr] = \
                    markets["cost"]["energy"]["total"]["baseline"][yr] - \
                    markets["cost"]["energy"]["total"]["efficient"][yr]
                ccostsave_tot[yr] = \
                    markets["cost"]["carbon"]["total"]["baseline"][yr] - \
                    markets["cost"]["carbon"]["total"]["efficient"][yr]

                # Calculate the annual energy/carbon and stock/energy/carbon
                # cost savings for the measure vs. baseline. (Annual savings
                # will later be used in measure competition routines). In non-
                # technical potential scenarios, annual savings reflect the
                # impact of only the measure adoptions that are new in the
                # current year of the modeling time horizon. In a technical
                # potential scenario, where we are simulating an 'overnight'
                # adoption of the measure across the entire applicable stock
                # in each year, annual savings are set to the total savings
                # from all current/previous adoptions of the measure
                if adopt_scheme != "Technical potential":
                    esave[yr] = \
                        markets["energy"]["competed"]["baseline"][yr] - \
                        markets["energy"]["competed"]["efficient"][yr]
                    csave[yr] = \
                        markets["carbon"]["competed"]["baseline"][yr] - \
                        markets["carbon"]["competed"]["efficient"][yr]
                    scostsave[yr] = markets[
                        "cost"]["stock"]["competed"]["baseline"][yr] - \
                        markets["cost"]["stock"]["competed"]["efficient"][yr]
                    ecostsave[yr] = markets[
                        "cost"]["energy"]["competed"]["baseline"][yr] - \
                        markets["cost"]["energy"]["competed"]["efficient"][yr]
                    ccostsave[yr] = markets[
                        "cost"]["carbon"]["competed"]["baseline"][yr] - \
                        markets["cost"]["carbon"]["competed"]["efficient"][yr]
                else:
                    esave[yr], csave[yr], scostsave[yr], \
                        ecostsave[yr], ccostsave[yr] = [
                        esave_tot[yr], csave_tot[yr], scostsave_tot[yr],
                        ecostsave_tot[yr], ccostsave_tot[yr]]

                # Set the number of competed stock units that are captured by
                # the measure for the given year; this number is used for
                # normalizing stock, energy and carbon cash flows to a per
                # unit basis in the "metric_update" function below. * Note:
                # for a technical potential scenario, all stock units are
                # captured in each year
                if adopt_scheme != "Technical potential":
                    nunits_tot = markets["stock"]["competed"]["all"][yr]
                    nunits_meas = markets["stock"]["competed"]["measure"][yr]
                else:
                    nunits_tot = markets["stock"]["total"]["all"][yr]
                    nunits_meas = markets["stock"]["total"]["measure"][yr]

                # Set the lifetime of the baseline technology for comparison
                # with measure lifetime
                life_base = markets["lifetime"]["baseline"][yr]
                # Ensure that baseline lifetime is at least 1 year
                if type(life_base) == numpy.ndarray and any(life_base) < 1:
                    life_base[numpy.where(life_base) < 1] = 1
                elif type(life_base) != numpy.ndarray and life_base < 1:
                    life_base = 1
                # Set lifetime of the measure
                life_meas = markets["lifetime"]["measure"]
                # Ensure that measure lifetime is at least 1 year
                if type(life_meas) == numpy.ndarray and any(life_meas) < 1:
                    life_meas[numpy.where(life_meas) < 1] = 1
                elif type(life_meas) != numpy.ndarray and life_meas < 1:
                    life_meas = 1
                # Define ratio of measure lifetime to baseline lifetime.  This
                # will be used below in determining cashflows over the measure
                # lifetime
                life_ratio = life_meas / life_base

                # Calculate measure financial metrics

                # Check whether number of adopted units for a measure is zero,
                # in which case all financial metrics are set to 999
                if type(nunits_meas) != numpy.ndarray and nunits_meas < 1 or \
                   type(nunits_meas) == numpy.ndarray and all(nunits_meas) < 1:
                    stock_anpv[yr], energy_anpv[yr], carb_anpv[yr] = [
                        {"residential": 999, "commercial": 999} for n in
                        range(3)]
                    irr_e[yr], irr_ec[yr], payback_e[yr], payback_ec[yr], \
                        cce[yr], cce_bens[yr], ccc[yr], ccc_bens[yr] = [
                            999 for n in range(8)]
                # Check whether any financial metric calculation inputs that
                # can be arrays are in fact arrays, proceed accordingly
                elif any(type(x) == numpy.ndarray for x in [
                        scostsave[yr], esave[yr], life_meas]):
                    # Make copies of the above stock, energy, carbon, and cost
                    # variables for possible further manipulation below before
                    # using as inputs to the "metric update" function below
                    scostsave_tmp, esave_tmp, ecostsave_tmp, csave_tmp, \
                        ccostsave_tmp, life_meas_tmp, life_ratio_tmp = [
                            scostsave[yr], esave[yr], ecostsave[yr],
                            csave[yr], ccostsave[yr], life_meas, life_ratio]

                    # Ensure consistency in length of all "metric_update"
                    # inputs that can be arrays

                    # Determine the length that any array inputs to
                    # "metric_update" should consistently have
                    len_arr = next((len(item) for item in [
                        scostsave[yr], esave[yr], life_meas] if
                        type(item) == numpy.ndarray), None)

                    # Ensure all array inputs to "metric_update" are of the
                    # above length

                    # Check incremental stock cost input
                    if type(scostsave_tmp) != numpy.ndarray:
                        scostsave_tmp = numpy.repeat(scostsave_tmp, len_arr)
                    # Check energy/energy cost and carbon/cost savings inputs
                    if type(esave_tmp) != numpy.ndarray:
                        esave_tmp = numpy.repeat(esave_tmp, len_arr)
                        ecostsave_tmp = numpy.repeat(ecostsave_tmp, len_arr)
                        csave_tmp = numpy.repeat(csave_tmp, len_arr)
                        ccostsave_tmp = numpy.repeat(ccostsave_tmp, len_arr)
                    # Check measure lifetime and lifetime ratio inputs
                    if type(life_meas_tmp) != numpy.ndarray:
                        life_meas_tmp = numpy.repeat(life_meas_tmp, len_arr)
                        life_ratio_tmp = numpy.repeat(life_ratio_tmp, len_arr)
                    # Check number of units captured by the measure
                    if type(nunits_meas) != numpy.ndarray:
                        nunits_meas = numpy.repeat(nunits_meas, len_arr)

                    # Initialize numpy arrays for financial metrics outputs

                    # First three arrays will be populated by dicts
                    # containing residential and commercial annuity equivalent
                    # Net Present Values (ANPVs)
                    stock_anpv[yr], energy_anpv[yr], carb_anpv[yr] = (
                        numpy.repeat({}, len(scostsave_tmp)) for v in range(3))
                    # Remaining eight arrays will be populated by floating
                    # point values
                    irr_e[yr], irr_ec[yr], payback_e[yr], payback_ec[yr], \
                        cce[yr], cce_bens[yr], ccc[yr], ccc_bens[yr] = \
                        (numpy.zeros(len(scostsave_tmp)) for v in range(8))

                    # Run measure energy/carbon/cost savings and lifetime
                    # inputs through "metric_update" function to yield
                    # financial metric outputs. To handle inputs that are
                    # arrays, use a for loop to generate an output for each
                    # input array element one-by-one and append it to the
                    # appropriate output list
                    for x in range(0, len(scostsave_tmp)):
                        # Check whether number of adopted units for a measure
                        # is zero, in which case all economic outputs are set
                        # to 999
                        if nunits_meas[x] == 0:
                            stock_anpv[yr][x], energy_anpv[yr][x], \
                                carb_anpv[yr][x] = [{
                                    "residential": 999, "commercial": 999} for
                                    n in range(3)]
                            irr_e[yr][x], irr_ec[yr][x], payback_e[yr][x], \
                                payback_ec[yr][x], cce[yr][x], \
                                cce_bens[yr][x], ccc[yr][x], \
                                ccc_bens[yr][x] = [999 for n in range(8)]
                        else:
                            stock_anpv[yr][x], energy_anpv[yr][x],\
                                carb_anpv[yr][x], irr_e[yr][x], \
                                irr_ec[yr][x], payback_e[yr][x], \
                                payback_ec[yr][x], cce[yr][x], \
                                cce_bens[yr][x], ccc[yr][x], \
                                ccc_bens[yr][x] = self.metric_update(
                                    m, nunits_tot, nunits_meas[x],
                                    life_base, int(life_meas_tmp[x]),
                                    int(life_ratio_tmp[x]), markets[
                                        "cost"]["stock"]["competed"][
                                        "baseline"][yr], scostsave_tmp[x],
                                    esave_tmp[x], ecostsave_tmp[x],
                                    csave_tmp[x], ccostsave_tmp[x])
                else:
                    # Run measure energy/carbon/cost savings and lifetime
                    # inputs through "metric_update" function to yield economic
                    # metric outputs
                    stock_anpv[yr], energy_anpv[yr], carb_anpv[yr], \
                        irr_e[yr], irr_ec[yr], payback_e[yr], payback_ec[yr], \
                        cce[yr], cce_bens[yr], ccc[yr], ccc_bens[yr] = \
                        self.metric_update(
                            m, nunits_tot, nunits_meas, life_base,
                            int(life_meas), int(life_ratio),
                            markets["cost"]["stock"][
                                "competed"]["baseline"][yr], scostsave[yr],
                            esave[yr], ecostsave[yr], csave[yr], ccostsave[yr])

            # Record final measure savings figures and financial metrics

            # Set measure savings dict to update
            save = m.savings[adopt_scheme][comp_scheme]
            # Update stock cost savings
            save["stock"]["cost savings (total)"] = scostsave_tot
            save["stock"]["cost savings (annual)"] = scostsave
            # Update energy and energy cost savings
            save["energy"]["savings (total)"] = esave_tot
            save["energy"]["savings (annual)"] = esave
            save["energy"]["cost savings (total)"] = ecostsave_tot
            save["energy"]["cost savings (annual)"] = ecostsave
            # Update carbon and carbon cost savings
            save["carbon"]["savings (total)"] = csave_tot
            save["carbon"]["savings (annual)"] = csave
            save["carbon"]["cost savings (total)"] = ccostsave_tot
            save["carbon"]["cost savings (annual)"] = ccostsave

            # Set measure portfolio-level financial metrics dict to update
            metrics_port = m.portfolio_metrics[adopt_scheme][comp_scheme]
            # Update cost of conserved energy
            metrics_port["cce"] = cce
            metrics_port["cce (w/ carbon cost benefits)"] = cce_bens
            # Update cost of conserved carbon
            metrics_port["ccc"] = ccc
            metrics_port["ccc (w/ energy cost benefits)"] = ccc_bens

            # Set measure savings and portolio-level metrics for the current
            # adoption and competition schemes to finalized status
            m.update_results["savings and portfolio metrics"][
                adopt_scheme][comp_scheme] = False

            # Update measure consumer-level financial metrics if they have
            # not already been finalized (these metrics remain constant across
            # all consumer adoption and measure competition schemes)
            if m.update_results["consumer metrics"] is True:
                # Set measure consumer-level financial metrics dict to update
                metrics_consumer = m.consumer_metrics
                # Update annuity equivalent NPV
                metrics_consumer["anpv"]["stock cost"] = stock_anpv
                metrics_consumer["anpv"]["energy cost"] = energy_anpv
                metrics_consumer["anpv"]["carbon cost"] = carb_anpv
                # Update internal rate of return
                metrics_consumer["irr (w/ energy costs)"] = irr_e
                metrics_consumer["irr (w/ energy and carbon costs)"] = irr_ec
                # Update payback period
                metrics_consumer["payback (w/ energy costs)"] = payback_e
                metrics_consumer["payback (w/ energy and carbon costs)"] = \
                    payback_ec

                # Set measure consumer-level metrics to finalized status
                m.update_results["consumer metrics"] = False

    def metric_update(
        self, m, nunits_tot, nunits_meas, life_base, life_meas, life_ratio,
            scost_base, scostsave, esave, ecostsave, csave, ccostsave):
        """Calculate measure financial metrics for a given year.

        Notes:
            Calculate internal rate of return, simple payback, and cost of
            conserved energy/carbon from cash flows and energy/carbon
            savings across the measure lifetime.

        Args:
            m (object): Measure object.
            nunits_tot (int): Total competed baseline units in a given year.
            nunits_meas (int): Total competed units captured by measure in
                given year.
            life_base (float): Baseline technology lifetime.
            life_meas (float): Measure lifetime.
            life_ratio (float): Ratio of measure lifetime to baseline lifetime.
            scost_base (list): Cost of competed baseline stock for given year.
            scostsave (list): Annual stock cost cash flows over the measure
                lifetime, starting in given year.
            esave (list): Annual energy savings over the measure lifetime,
                starting in given year.
            ecostsave (list): Annual energy cost savings over the measure
                lifetime, starting in a given year.
            csave (list): Annual avoided carbon emissions over the measure
                lifetime, starting in given year.
            ccostsave (list): Annual carbon cost savings over the measure
                lifetime, starting in a given year.

        Returns:
            Consumer and portfolio-level financial metrics for the given
            measure cost savings inputs.
        """
        # Develop four initial cash flow scenarios over the measure life:
        # 1) Cash flows considering capital costs only
        # 2) Cash flows considering capital costs and energy costs
        # 3) Cash flows considering capital costs and carbon costs
        # 4) Cash flows considering capital, energy, and carbon costs

        # Determine when over the course of the measure lifetime (if at all)
        # a cost gain is realized from an avoided purchase of the baseline
        # technology due to longer measure lifetime; store this information in
        # a list of year indicators for subsequent use below.  Example: an LED
        # bulb lasts 30 years compared to a baseline bulb's 10 years, meaning
        # 3 purchases of the baseline bulb would have occured by the time the
        # LED bulb has reached the end of its life.
        added_stockcost_gain_yrs = []
        if life_ratio > 1:
            for i in range(0, life_ratio - 1):
                added_stockcost_gain_yrs.append(
                    (life_base - 1) + (life_base * i))
        # If the measure lifetime is less than 1 year, set it to 1 year
        # (a minimum for measure lifetime to work in below calculations)
        if life_meas < 1:
            life_meas = 1

        # Construct complete stock cash flows across measure lifetime
        # (normalized by number of captured stock units)

        # Initialize stock cash flows with incremental capital cost
        cashflows_s = numpy.array(scostsave)

        for life_yr in range(0, life_meas):
            # Check whether an avoided cost of the baseline technology should
            # be added for given year; if not, set this term to zero
            if life_yr in added_stockcost_gain_yrs:
                scost_life = scost_base
            else:
                scost_life = 0

            # Add avoided capital costs and saved energy and carbon costs
            # as appropriate
            cashflows_s = numpy.append(cashflows_s, scost_life)

        cashflows_s = cashflows_s / nunits_meas

        # Construct complete energy and carbon cash flows across measure
        # lifetime (normalized by number of captured stock units). First
        # term (reserved for initial investment figure) is zero.
        cashflows_e, cashflows_c = [numpy.append(0, [x] * life_meas) /
                                    nunits_tot for x in [ecostsave, ccostsave]]

        # Calculate Net Present Value (NPVs) using the above cashflows
        npv_s, npv_e, npv_c = [
            numpy.npv(self.handyvars.discount_rate, x) for x in [
                cashflows_s, cashflows_e, cashflows_c]]

        # Develop arrays of energy and carbon savings across measure
        # lifetime (for use in cost of conserved energy and carbon calcs).
        # First term (reserved for initial investment figure) is zero, and
        # each array is normalized by number of captured stock units
        esave_array = numpy.append(0, [esave] * life_meas) / nunits_tot
        csave_array = numpy.append(0, [csave] * life_meas) / nunits_tot

        # Calculate Net Present Value and annuity equivalent Net Present Value
        # of the above energy and carbon savings
        npv_esave = numpy.npv(self.handyvars.discount_rate, esave_array)
        npv_csave = numpy.npv(self.handyvars.discount_rate, csave_array)

        # Initially set financial metrics to 999 for cases where the
        # metric should not or cannot be computed (e.g., consumer-level metrics
        # have already been calculated; or zeros in denominator of portfolio-
        # level financial metrics due to no energy savings)
        anpv_s_in, anpv_e_in, anpv_c, irr_e, irr_ec, payback_e, payback_ec, \
            cce, cce_bens, ccc, ccc_bens = (999 for n in range(11))

        # Calculate portfolio-level financial metrics

        # Calculate cost of conserved energy w/ and w/o carbon cost savings
        # benefits.  Check to ensure energy savings NPV in the denominator
        # is not zero
        if npv_esave > 0:
            cce = (-npv_s / npv_esave)
            cce_bens = (-(npv_s + npv_c) / npv_esave)

        # Calculate cost of conserved carbon w/ and w/o energy cost savings
        # benefits.  Check to ensure carbon savings NPV in the denominator
        # is not zero.
        if npv_csave > 0:
            ccc = (-npv_s / (npv_csave * 1000000))
            ccc_bens = (-(npv_s + npv_e) / (npv_csave * 1000000))

        # Calculate consumer-level financial metrics

        # Only calculate consumer-level financial metrics once; do not
        # recalculate if already finalized
        if m.update_results["consumer metrics"] is True:
            # Calculate Annualized Net Present Value (ANPV) using the above
            # cashflows for later use in measure competition calculations. For
            # residential sector measures, ANPV is calculated using the
            # above NPVs, with a general discount rate applied.  For commerical
            # sector measures, ANPV is calculated using multiple discount rate
            # levels that reflect various degrees of risk tolerance observed
            # amongst commercial adopters.  These discount rate levels are
            # imported from the commercial AEO demand module data.

            # Populate ANPVs for residential sector
            # Check whether measure applies to residential sector
            if any([x in ["single family home", "multi family home",
                          "mobile home"] for x in m.bldg_type]):
                # Set ANPV values under general discount rate
                res_anpv_s_in, res_anpv_e_in, res_anpv_c = [
                    numpy.pmt(self.handyvars.discount_rate, life_meas, x) for
                    x in [npv_s, npv_e, npv_c]]
            # If measure does not apply to residential sector, set residential
            # ANPVs to 'None'
            else:
                res_anpv_s_in, res_anpv_e_in, res_anpv_c = (
                    None for n in range(3))

            # Populate ANPVs for commercial sector
            # Check whether measure applies to commercial sector
            if any([x not in ["single family home", "multi family home",
                              "mobile home"] for x in m.bldg_type]):
                com_anpv_s_in, com_anpv_e_in, com_anpv_c = (
                    {} for n in range(3))
                # Set ANPV values under 7 discount rate categories
                for ind, tps in enumerate(
                        self.handyvars.com_timeprefs["rates"]):
                    com_anpv_s_in["rate " + str(ind + 1)],\
                        com_anpv_e_in["rate " + str(ind + 1)],\
                        com_anpv_c["rate " + str(ind + 1)] = \
                        [numpy.pmt(tps, life_meas, numpy.npv(tps, x))
                         for x in [cashflows_s, cashflows_e, cashflows_c]]
            # If measure does not apply to commercial sector, set commercial
            # ANPVs to 'None'
            else:
                com_anpv_s_in, com_anpv_e_in, com_anpv_c = (
                    None for n in range(3))

            # Set overall ANPV dicts based on above updating of residential
            # and commercial sector ANPV values
            anpv_s_in = {
                "residential": res_anpv_s_in, "commercial": com_anpv_s_in}
            anpv_e_in = {
                "residential": res_anpv_e_in, "commercial": com_anpv_e_in}
            anpv_c = {
                "residential": res_anpv_c, "commercial": com_anpv_c}

            # Calculate internal rate of return and simple payback for capital
            # + energy and capital + energy + carbon cash flows.  Check to
            # ensure that relevant cash flows are non-zero and that IRR/payback
            # can be calculated
            if any(cashflows_e) != 0:
                # IRR/payback given capital + energy cash flows
                try:
                    irr_e = numpy.irr(cashflows_s + cashflows_e)
                    payback_e = self.payback(cashflows_s + cashflows_e)
                except (ValueError, LinAlgError):
                    pass
                # IRR/payback given capital + energy + carbon cash flows
                try:
                    irr_ec = numpy.irr(cashflows_s + cashflows_e + cashflows_c)
                    payback_ec = \
                        self.payback(cashflows_s + cashflows_e + cashflows_c)
                except (ValueError, LinAlgError):
                    pass

        # Return all updated economic metrics
        return anpv_s_in, anpv_e_in, anpv_c, irr_e, irr_ec, payback_e, \
            payback_ec, cce, cce_bens, ccc, ccc_bens

    def payback(self, cashflows):
        """Calculate simple payback period.

        Notes:
            Calculate the simple payback period given an input list of
            cash flows, which may be uneven.

        Args:
            cashflows (list): Cash flows across measure lifetime.

        Returns:
            Simple payback period for the input cash flows.
        """
        # Separate initial investment and subsequent cash flows
        # from "cashflows" input
        investment, cashflows = cashflows[0], cashflows[1:]
        # If initial investment is positive, payback = 0
        if investment >= 0:
            payback_val = 0
        else:
            # Find absolute value of initial investment to compare
            # subsequent cash flows against
            investment = abs(investment)
            # Initialize cumulative cashflow and # years tracking
            total, years, cumulative = 0, 0, []
            # Add to years and cumulative cashflow trackers while cumulative
            # cashflow < investment
            for cashflow in cashflows:
                total += cashflow
                if total < investment:
                    years += 1
                cumulative.append(total)
            # If investment pays back within the measure lifetime,
            # calculate this payback period in years
            if years < len(cashflows):
                a = years
                # Case where payback period < 1 year
                if (years - 1) < 0:
                    b = investment
                    c = cumulative[0]
                # Case where payback period >= 1 year
                else:
                    b = investment - cumulative[years - 1]
                    c = cumulative[years] - cumulative[years - 1]
                payback_val = a + (b / c)
            # If investment does not pay back within measure lifetime,
            # set payback period to artifically high number
            else:
                payback_val = 999

        # Return updated payback period value in years
        return payback_val

    def compete_measures(self, adopt_scheme):
        """Compete and apportion total stock/energy/carbon/cost across measures.

        Notes:
            Adjust each competing measure's 'baseline' and 'efficient'
            energy/carbon/cost to reflect either a) direct competition between
            measures, or b) the indirect effects of measure competition.

        Args:
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Establish list of key chains and supporting competition data for all
        # stock/energy/carbon/cost microsegments that contribute to a measure's
        # total stock/energy/carbon/cost microsegments, across active measures
        mseg_keys, mkts_adj = ([] for n in range(2))
        for x in self.measures:
            mseg_keys.extend(x.markets[adopt_scheme]["competed"][
                "mseg_adjust"]["contributing mseg keys and values"].keys())
            mkts_adj.append(x.markets[adopt_scheme]["competed"]["mseg_adjust"])

        # Establish list of unique key chains in mseg_keys list above,
        # ensuring that all 'primary' microsegments (e.g., relating to direct
        # equipment replacement) are ordered and updated before 'secondary'
        # microsegments (e.g., relating to indirect effects of equipment
        # replacement, such as reduced waste heat from changes in lighting)
        msegs = sorted(numpy.unique(mseg_keys))

        # Run through all unique contributing microsegments in the above list,
        # determining how the initial measure stock/energy/carbon/cost data
        # associated with each should be adjusted to reflect the effects of
        # measure competition
        for msu in msegs:

            # Determine the subset of measures that pertain to the current
            # contributing microsegment
            measures_adj = [self.measures[x] for x in range(
                0, len(self.measures)) if msu in mkts_adj[x][
                "contributing mseg keys and values"].keys()]

            # If the current contributing microsegment is of the 'primary'
            # type, directly compete the microsegment across applicable
            # measures
            if "primary" in msu:
                # If multiple measures are competing for the primary
                # microsegment, determine the market shares of each competing
                # measure and adjust primary stock/energy/carbon/cost
                # totals for each measure accordingly, using separate market
                # share modeling routines for residential/commercial sectors.
                if len(measures_adj) > 1 and any(x in msu for x in (
                        'single family home', 'multi family home',
                        'mobile home')):
                    self.compete_res_primary(measures_adj, msu, adopt_scheme)
                elif len(measures_adj) > 1 and all(x not in msu for x in (
                        'single family home', 'multi family home',
                        'mobile home')):
                    self.compete_com_primary(measures_adj, msu, adopt_scheme)
            # If the current contributing microsegment is of the 'secondary'
            # type, adjust the microsegment across applicable measures as
            # needed to reflect competition of associated primary
            # contributing microsegment(s) for each measure
            elif "secondary" in msu:
                # Determine the climate zone, building type, and structure type
                # needed to link the secondary microsegment and associated3
                # primary microsegment(s)
                cz_bldg_struct = literal_eval(msu)
                secnd_mseg_adjkey = str((
                    cz_bldg_struct[1], cz_bldg_struct[2], cz_bldg_struct[-1]))
                # Determine the subset of measures pertaining to the given
                # secondary microsegment that require total energy/carbon/cost
                # adjustments due to changes in associated primary
                # microsegment(s) (note that secondary microsegments do not
                # affect stock totals, only energy/carbon and associated costs)
                measures_adj_scnd = [self.measures[x] for x in range(
                    0, len(self.measures)) if x in measures_adj and any(
                    [(y[1] > 0) for y in mkts_adj[x][
                        "secondary mseg adjustments"]["market share"][
                        "original stock (total captured)"][
                        secnd_mseg_adjkey].items()])]
                # If at least one applicable measure requires adjustments to
                # total secondary energy/carbon/cost, proceed with the
                # adjustment calculation
                if len(measures_adj_scnd) > 0:
                    self.adj_secondary(measures_adj_scnd, msu,
                                       secnd_mseg_adjkey, adopt_scheme)

            # For any contributing microsegment that pertains to heating or
            # cooling, additional adjustments may be needed post-competition to
            # a) balance out total supply-side and demand-side heating and
            # cooling energy to reflect competition-driven changes in primary
            # or secondary energy/carbon/cost totals, or b) account for the
            # demand-side effects of competition-driven changes in secondary
            # energy/carbon/cost totals.

            # Ensure the current contributing microsegment pertains to
            # heating or cooling (marked by 'supply' or 'demand' keys)
            if 'supply' in msu or 'demand' in msu:
                # Initialize a dict to determine which measures will require
                # additional adjustments post-competition to reflect
                # competition-driven changes in the current heating/cooling
                # microsegment, and what contributing microsegment keys for
                # each measure will be affected
                measures_adj_htcl_add = {"measures": [], "keys": []}

                # Establish criteria for matching a primary, supply-side
                # heating/cooling microsegment with either a primary or
                # secondary demand-side heating/cooling microsegment
                # (same climate zone, building type, and fuel)
                if 'primary' in msu and'supply' in msu:
                    msu_split = re.search(
                        "'[a-zA-Z0-9_() /&-]+',\s'(.*)\,.*supply.*",
                        msu).group(1)
                # Establish criteria for matching a primary, demand-side
                # heating/cooling microsegment with a primary supply-side
                # heating/cooling microsegment (same climate zone, building
                # type, and fuel)
                elif 'primary' in msu and 'demand' in msu:
                    msu_split = re.search(
                        "'[a-zA-Z0-9_() /&-]+',\s'(.*)\,.*demand.*",
                        msu).group(1)
                # Establish criteria for matching a secondary, demand-side
                # heating/cooling microsegment with either a primary,
                # supply-side heating/cooling microsegment, a primary,
                # demand-side heating/cooling microsegment, or another
                # secondary, demand-side heating/cooling microsegment
                elif 'secondary' in msu:
                    # When matching a secondary, demand-side heating/cooling
                    # microsegment with primary, supply-side heating/cooling
                    # microsegments, the matching criteria is same climate
                    # zone, building type, and fuel, as above
                    msu_split_supply = re.search(
                        "'[a-zA-Z0-9_() /&-]+',\s'(.*)\,.*demand.*",
                        msu).group(1)
                    # When matching a secondary, demand-side heating/cooling
                    # microsegment with either a primary, demand-side
                    # heating/cooling microsegment or another secondary
                    # demand-side heating/cooling microsegment, the matching
                    # criteria is the same climate zone, building type,
                    # structure type, fuel type, end use, technology type,
                    # and technology
                    msu_split_demand = re.search(
                        "'[a-zA-Z0-9_() /&-]+',\s'(.*)", msu).group(1)

                # Loop through all measures to find key chain matches
                for ind, m in enumerate(self.measures):
                    # Register a match between a primary, supply-side
                    # heating/cooling microsegment and a primary or
                    # secondary demand-side heating/cooling microsegment
                    if 'primary' in msu and 'supply' in msu:
                        keys = [x for x in mkts_adj[ind][
                            "contributing mseg keys and values"].keys() if
                            msu_split in x and 'demand' in x]
                    # Register a match between a primary, demand-side
                    # heating/cooling microsegment and a primary supply-side
                    # heating/cooling microsegment
                    elif 'primary' in msu and 'demand' in msu:
                        keys = [x for x in mkts_adj[ind][
                            "contributing mseg keys and values"].keys() if
                            msu_split in x and 'supply' in x]
                    # Register a match between a secondary, demand-side
                    # heating/cooling microsegment and either a primary,
                    # supply-side heating/cooling microsegment or a secondary,
                    # demand-side heating/cooling microsegment
                    elif 'secondary' in msu:
                        keys = [x for x in mkts_adj[ind][
                            "contributing mseg keys and values"].keys() if
                            (msu_split_supply in x and 'supply' in x) or
                            (msu_split_demand in x and 'demand' in x)]
                    # Record the matched key chains and associated
                    # measure objects in a dict for further use in the function
                    # that records the data needed to make the additional
                    # adjustments to energy/carbon/cost totals for these
                    # measures ('adj_htcl_add_rec')
                    if len(keys) > 0:
                        measures_adj_htcl_add["measures"].append(m)
                        measures_adj_htcl_add["keys"].append(keys)

                # If any measures require additional adjustments to their
                # heating/cooling microsegments, record the energy/carbon/cost
                # data for the current contributing microsegment that is
                # is needed to make these adjustments
                if len(measures_adj_htcl_add["measures"]) > 0:
                    self.adj_htcl_add_rec(
                        measures_adj, measures_adj_htcl_add, msu, adopt_scheme)

        # Determine heating/cooling measures that require additional post-
        # competition energy/carbon/cost adjustments and implement these
        # adjustments
        measures_adj_htcl_add = [
            self.measures[x] for x in range(0, len(self.measures)) if len(
                mkts_adj[x]["supply-demand adjustment"]["savings"].keys()) > 0]
        if len(measures_adj_htcl_add) > 0:
            self.adj_htcl_add(measures_adj_htcl_add, adopt_scheme)

    def compete_res_primary(self, measures_adj, mseg_key, adopt_scheme):
        """Apportion stock/energy/carbon/cost across competing residential measures.

        Notes:
            Determine the shares of a given market microsegment that are
            captured by a series of residential efficiency measures that
            compete for this market microsegment.

        Args:
            measures_adj (list): Competing residential measure objects.
            mseg_key (string): Competed market microsegment information
                (mseg type->czone->bldg->fuel->end use->technology type
                 ->structure type).
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Initialize list of dicts that each store the annual market fractions
        # captured by competing measures; also initialize a dict that sums
        # market fractions by year across competing measures (used to normalize
        # the measure market fractions such that they all sum to 1)
        mkt_fracs = [{} for l in range(0, len(measures_adj))]
        mkt_fracs_tot = dict.fromkeys(self.handyvars.aeo_years, 0)

        # Loop through competing measures and calculate market shares for each
        # based on their annualized capital and operating costs.

        # Set abbreviated names for the dictionaries containing measure
        # capital and operating cost values, accessed further below

        # Annualized capital cost dictionary
        anpv_s_in = [m.consumer_metrics["anpv"]["stock cost"] for
                     m in measures_adj]
        # Annualized operating cost dictionary
        anpv_e_in = [m.consumer_metrics["anpv"]["energy cost"] for
                     m in measures_adj]

        # Find the year range in which at least one measure that applies
        # to the competed primary microsegment is on the market
        years_on_mkt_all = []
        [years_on_mkt_all.extend(x.yrs_on_mkt) for x in measures_adj]
        years_on_mkt_all = numpy.unique(years_on_mkt_all)

        # Loop through competing measures and calculate market shares for
        # each based on their annualized capital and operating costs
        for ind, m in enumerate(measures_adj):
            # Set measure markets and market adjustment information

            # Loop through all years where at least one competing measure
            # is on the market
            for yr in years_on_mkt_all:
                # Ensure measure is on the market in given year
                if yr in m.yrs_on_mkt:
                    # Set measure capital and operating cost inputs. * Note:
                    # operating cost is set to just energy costs (for now), but
                    # could be expanded to include maintenance and carbon costs

                    # Set capital cost (handle as numpy array or point value)
                    if type(anpv_s_in[ind][yr]) == numpy.ndarray:
                        cap_cost = numpy.zeros(len(anpv_s_in[ind][yr]))
                        for i in range(0, len(anpv_s_in[ind][yr])):
                            cap_cost[i] = anpv_s_in[ind][yr][i][
                                "residential"]
                    else:
                        cap_cost = anpv_s_in[ind][yr]["residential"]
                    # Set operating cost (handle as numpy array or point value)
                    if type(anpv_e_in[ind][yr]) == numpy.ndarray:
                        op_cost = numpy.zeros(len(anpv_e_in[ind][yr]))
                        for i in range(0, len(anpv_e_in[ind][yr])):
                            op_cost[i] = anpv_e_in[ind][yr][i][
                                "residential"]
                    else:
                        op_cost = anpv_e_in[ind][yr]["residential"]

                    # Calculate measure market fraction using log-linear
                    # regression equation that takes capital/operating
                    # costs as inputs
                    mkt_fracs[ind][yr] = numpy.exp(
                        cap_cost * m.markets[adopt_scheme]["competed"][
                            "mseg_adjust"]["competed choice parameters"][
                                str(mseg_key)]["b1"][yr] + op_cost *
                        m.markets[adopt_scheme]["competed"]["mseg_adjust"][
                            "competed choice parameters"][
                                str(mseg_key)]["b2"][yr])
                    # Add calculated market fraction to mkt fraction sum
                    mkt_fracs_tot[yr] = \
                        mkt_fracs_tot[yr] + mkt_fracs[ind][yr]

        # Loop through competing measures to normalize their calculated
        # market shares to the total market share sum; use normalized
        # market shares to make adjustments to each measure's master
        # microsegment values
        for ind, m in enumerate(measures_adj):
            # Set measure markets and market adjustment information
            # Establish starting energy/carbon/cost totals and current
            # contributing primary energy/carbon/cost information for measure
            mast, adj, mast_list_base, mast_list_eff, adj_list_eff, \
                adj_list_base = self.compete_adjustment_dicts(
                    m, mseg_key, adopt_scheme)
            # Calculate annual market share fraction for the measure and
            # adjust measure's master microsegment values accordingly
            for yr in years_on_mkt_all:
                # Ensure measure is on the market in given year; if not,
                # the measure's market share is zero
                if yr in m.yrs_on_mkt:
                    mkt_fracs[ind][yr] = \
                        mkt_fracs[ind][yr] / mkt_fracs_tot[yr]
                else:
                    mkt_fracs[ind][yr] = 0
                # Make the adjustment to the measure's stock/energy/carbon/
                # cost totals based on its updated competed market share
                self.compete_adjustment(
                    mkt_fracs[ind], mast, adj, mast_list_base,
                    mast_list_eff, adj_list_eff, adj_list_base, yr,
                    mseg_key, m, adopt_scheme)

    def compete_com_primary(self, measures_adj, mseg_key, adopt_scheme):
        """Apportion stock/energy/carbon/cost across competing commercial measures.

        Notes:
            Determines the shares of a given market microsegment that are
            captured by a series of commerical efficiency measures that
            compete for this market microsegment.

        Args:
            measures_adj (list): Competing commercial measure objects.
            mseg_key (string): Competed market microsegment information
                (mseg type->czone->bldg->fuel->end use->technology type
                 ->structure type).
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Initialize list of dicts that each store the annual market fractions
        # captured by competing measures; also initialize a dict that records
        # the total annualized capital + operating costs for each measure
        # and discount rate level (used to choose which measure is adopted
        # under each discount rate level)
        mkt_fracs = [{} for l in range(0, len(measures_adj))]
        tot_cost = [{} for l in range(0, len(measures_adj))]

        # Calculate the total annualized cost (capital + operating) needed to
        # determine market shares below

        # Set abbreviated names for the dictionaries containing measure
        # capital and operating cost values, accessed further below

        # Annualized stock cost dictionary
        anpv_s_in = [m.consumer_metrics["anpv"]["stock cost"] for
                     m in measures_adj]
        # Annualized operating cost dictionary
        anpv_e_in = [m.consumer_metrics["anpv"]["energy cost"] for
                     m in measures_adj]

        # Find the year range in which at least one measure that applies
        # to the competed primary microsegment is on the market
        years_on_mkt_all = []
        [years_on_mkt_all.extend(x.yrs_on_mkt) for x in measures_adj]
        years_on_mkt_all = numpy.unique(years_on_mkt_all)

        # Initialize a flag that indicates whether any competing measures
        # have arrays of annualized capital and/or operating costs rather
        # than point values (resultant of distributions on measure inputs),
        # for each year in the range above
        length_array = numpy.repeat(0, len(years_on_mkt_all))

        # Loop through all years where at least one competing measure
        # is on the market
        for ind_l, yr in enumerate(years_on_mkt_all):
            # Determine whether any of the competing measures have
            # arrays of annualized capital and/or operating costs for
            # the given year; if so, find the array length. * Note: all
            # array lengths should be equal to the 'nsamples' variable
            # defined in 'ecm_prep.py'
            if any([type(x[yr]) == numpy.ndarray or
                    type(y[yr]) == numpy.ndarray for
                    x, y in zip(anpv_s_in, anpv_e_in)]) is True:
                length_array[ind_l] = next(
                    (len(x[yr]) or len(y[yr]) for x, y in
                     zip(anpv_s_in, anpv_e_in) if type(x[yr]) ==
                     numpy.ndarray or type(y[yr]) == numpy.ndarray),
                    length_array[ind_l])

        # Loop through competing measures and calculate market shares for
        # each based on their annualized capital and operating costs
        for ind, m in enumerate(measures_adj):
            # Set measure markets and market adjustment information

            # Loop through all years where at least one competing measure
            # is on the market
            for ind_l, yr in enumerate(years_on_mkt_all):
                # Ensure measure is on the market in given year
                if yr in m.yrs_on_mkt:
                    # Set measure capital and operating cost inputs. * Note:
                    # operating cost is set to just energy costs (for now), but
                    # could be expanded to include maintenance and carbon costs

                    # Handle cases where capital and/or operating cost inputs
                    # are specified as arrays for at least one of the competing
                    # measures. In this case, the capital and operating costs
                    # for all measures must be formatted consistently as arrays
                    # of the same length
                    if length_array[ind_l] > 0:
                        cap_cost, op_cost = ([
                            {} for n in range(length_array[ind_l])] for
                            n in range(2))
                        for i in range(length_array[ind_l]):
                            # Set capital cost input array
                            if type(anpv_s_in[ind][yr]) == numpy.ndarray:
                                cap_cost[i] = anpv_s_in[ind][yr][i][
                                    "commercial"]
                            else:
                                cap_cost[i] = anpv_s_in[ind][yr]["commercial"]
                            # Set operating cost input array
                            if type(anpv_e_in[ind][yr]) == numpy.ndarray:
                                op_cost[i] = anpv_e_in[ind][yr][i][
                                    "commercial"]
                            else:
                                op_cost[i] = anpv_e_in[ind][yr]["commercial"]
                        # Sum capital and operating cost arrays and add to the
                        # total cost dict entry for the given measure
                        tot_cost[ind][yr] = [
                            [] for n in range(length_array[ind_l])]
                        for l in range(0, len(tot_cost[ind][yr])):
                            for dr in sorted(cap_cost[l].keys()):
                                tot_cost[ind][yr][l].append(
                                    cap_cost[l][dr] + op_cost[l][dr])
                    # Handle cases where capital and/or operating cost inputs
                    # are specified as point values for all competing measures
                    else:
                        # Set capital cost point value
                        cap_cost = anpv_s_in[ind][yr]["commercial"]
                        # Set operating cost point value
                        op_cost = anpv_e_in[ind][yr]["commercial"]
                        # Sum capital and opearting cost point values and add
                        # to the total cost dict entry for the given measure
                        tot_cost[ind][yr] = []
                        for dr in sorted(cap_cost.keys()):
                            tot_cost[ind][yr].append(
                                cap_cost[dr] + op_cost[dr])

        # Loop through competing measures and use total annualized capital
        # + operating costs to determine the overall share of the market
        # that is captured by each measure; use market shares to make
        # adjustments to each measure's master microsegment values
        for ind, m in enumerate(measures_adj):
            # Set measure markets and market adjustment information
            # Establish starting energy/carbon/cost totals and current
            # contributing primary energy/carbon/cost information for measure
            mast, adj, mast_list_base, mast_list_eff, adj_list_eff, \
                adj_list_base = self.compete_adjustment_dicts(
                    m, mseg_key, adopt_scheme)
            # Calculate annual market share fraction for the measure and
            # adjust measure's master microsegment values accordingly

            # Loop through all years where at least one competing measure
            # is on the market
            for ind_l, yr in enumerate(years_on_mkt_all):
                # Ensure measure is on the market in given year; if not,
                # the measure's market share is zero
                if yr in m.yrs_on_mkt:
                    # Set the fractions of commericial adopters who fall into
                    # each discount rate category for this particular
                    # microsegment
                    mkt_dists = m.markets[adopt_scheme]["competed"][
                        "mseg_adjust"]["competed choice parameters"][
                            str(mseg_key)]["rate distribution"][yr]
                    # For each discount rate category, find which measure has
                    # the lowest annualized cost and assign that measure the
                    # share of commercial market adopters defined for that
                    # category above

                    # Handle cases where capital and/or operating cost inputs
                    # are specified as lists for at least one of the competing
                    # measures.
                    if length_array[ind_l] > 0:
                        mkt_fracs[ind][yr] = [
                            [] for n in range(length_array[ind_l])]
                        for l in range(length_array[ind_l]):
                            for ind2, dr in enumerate(tot_cost[ind][yr][l]):
                                # If the measure has the lowest annualized
                                # cost, assign it the appropriate market share
                                # for the current discount rate category being
                                # looped through; otherwise, set its market
                                # fraction for that category to zero
                                if tot_cost[ind][yr][l][ind2] == \
                                   min([tot_cost[x][yr][l][ind2] for x in
                                        range(0, len(measures_adj)) if
                                        yr in tot_cost[x].keys()]):
                                    mkt_fracs[ind][yr][l].append(
                                        mkt_dists[ind2])  # * EQUALS? *
                                else:
                                    mkt_fracs[ind][yr][l].append(0)
                            mkt_fracs[ind][yr][l] = sum(
                                mkt_fracs[ind][yr][l])
                        # Convert market fractions list to numpy array for
                        # use in compete_adjustment function below
                        mkt_fracs[ind][yr] = numpy.array(
                            mkt_fracs[ind][yr])
                    # Handle cases where capital and/or operating cost inputs
                    # are specified as point values for all competing measures
                    else:
                        mkt_fracs[ind][yr] = []
                        for ind2, dr in enumerate(tot_cost[ind][yr]):
                            if tot_cost[ind][yr][ind2] == \
                               min([tot_cost[x][yr][ind2] for x in range(
                                    0, len(measures_adj)) if
                                    yr in tot_cost[x].keys()]):
                                mkt_fracs[ind][yr].append(mkt_dists[ind2])
                            else:
                                mkt_fracs[ind][yr].append(0)
                        mkt_fracs[ind][yr] = sum(mkt_fracs[ind][yr])
                else:
                    mkt_fracs[ind][yr] = 0

                # Make the adjustment to the measure's stock/energy/carbon/
                # cost totals based on its updated competed market share
                self.compete_adjustment(
                    mkt_fracs[ind], mast, adj, mast_list_base,
                    mast_list_eff, adj_list_eff, adj_list_base, yr,
                    mseg_key, m, adopt_scheme)

    def adj_secondary(
            self, measures_adj, mseg_key, secnd_mseg_adjkey, adopt_scheme):
        """Adjust secondary microsegments to account for primary competition.

        Notes:
            Adjust a measure's secondary energy/carbon/cost totals to reflect
            the updated market shares calculated for an associated primary
            microsegment.

        Args:
            measures_adj (list): Competing commercial measure objects.
            mseg_key (string): Competed market microsegment information
                (mseg type->czone->bldg->fuel->end use->technology type
                 ->structure type).
            adopt_scheme (string): Assumed consumer adoption scenario.

        Raises:
            KeyError: If secondary market microsegment has no associated
                primary market microsegment.
        """
        # Find the year range in which at least one measure that applies
        # to the secondary microsegment is on the market
        years_on_mkt_all = []
        [years_on_mkt_all.extend(x.yrs_on_mkt) for x in measures_adj]
        years_on_mkt_all = numpy.unique(years_on_mkt_all)

        # Loop through all measures that apply to the current contributing
        # secondary microsegment
        for ind, m in enumerate(measures_adj):
            # Establish starting energy/carbon/cost totals and current
            # contributing secondary energy/carbon/cost information for measure
            mast, adj, mast_list_base, mast_list_eff, adj_list_eff, \
                adj_list_base = self.compete_adjustment_dicts(
                    m, mseg_key, adopt_scheme)

            # Adjust secondary energy/carbon/cost totals based on the measure's
            # competed market share for an associated primary contributing
            # microsegment

            # Loop through all years where at least one measure that applies
            # to the secondary microsegment is on the market
            for yr in self.handyvars.aeo_years:
                # Find the appropriate market share adjustment information
                # for the given secondary climate zone, building type, and
                # structure type in the measure's 'mseg_adjust' attribute
                # and scale down the energy/carbon/cost totals accordingly
                secnd_adj_mktshr = m.markets[adopt_scheme]["competed"][
                    "mseg_adjust"]["secondary mseg adjustments"][
                    "market share"]
                # Calculate the competed and total market share adjustment
                # factors to apply to the measure secondary energy/carbon/cost
                # totals, where the 'competed' share considers the effects
                # of primary microsegment competition for the current year
                # only, and the 'total' share considers the effects of
                # primary microsegment competition for the current and all
                # previous years the measure was on the market

                # Set competed market share adjustment
                if secnd_adj_mktshr[
                        "original stock (competed and captured)"][
                        secnd_mseg_adjkey][yr] != 0:
                    adj_frac_comp = secnd_adj_mktshr[
                        "adjusted stock (competed and captured)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_mktshr[
                        "original stock (competed and captured)"][
                        secnd_mseg_adjkey][yr]
                # Set competed market share adjustment to zero if total
                # originally captured baseline stock is zero for
                # current year
                else:
                    adj_frac_comp = 0

                # Set total market share adjustment
                if secnd_adj_mktshr["original stock (total captured)"][
                        secnd_mseg_adjkey][yr] != 0:
                    adj_frac_tot = secnd_adj_mktshr[
                        "adjusted stock (total captured)"][
                        secnd_mseg_adjkey][yr] / secnd_adj_mktshr[
                        "original stock (total captured)"][
                        secnd_mseg_adjkey][yr]
                # Set total market share adjustment to zero if total
                # originally captured baseline stock is zero for
                # current year
                else:
                    adj_frac_tot = 0

                # Adjust total and competed baseline and efficient
                # data by the appropriate secondary adjustment factor
                for x in ["baseline", "efficient"]:
                    # Determine appropriate adjustment data to use
                    # for baseline or efficient case
                    if x == "baseline":
                        mastlist, adjlist = [mast_list_base, adj_list_base]
                    else:
                        mastlist, adjlist = [mast_list_eff, adj_list_eff]
                    # Adjust the total and competed energy, carbon, and
                    # associated cost savings by the secondary adjustment
                    # factor, both overall and for the current
                    # contributing microsegment
                    mast["cost"]["energy"]["total"][x][yr], \
                        mast["cost"]["carbon"]["total"][x][yr], \
                        mast["energy"]["total"][x][yr], \
                        mast["carbon"]["total"][x][yr] = [
                            x[yr] - (y[yr] * (1 - adj_frac_tot)) for x, y in
                            zip(mastlist[1:5], adjlist[1:5])]
                    mast["cost"]["energy"]["competed"][x][yr], \
                        mast["cost"]["carbon"]["competed"][x][yr], \
                        mast["energy"]["competed"][x][yr], \
                        mast["carbon"]["competed"][x][yr] = [
                            x[yr] - (y[yr] * (1 - adj_frac_comp)) for x, y in
                            zip(mastlist[6:], adjlist[6:])]
                    adj["cost"]["energy"]["total"][x][yr], \
                        adj["cost"]["carbon"]["total"][x][yr], \
                        adj["energy"]["total"][x][yr], \
                        adj["carbon"]["total"][x][yr] = [
                            (x[yr] * adj_frac_tot) for x in adjlist[1:5]]
                    adj["cost"]["energy"]["competed"][x][yr], \
                        adj["cost"]["carbon"]["competed"][x][yr], \
                        adj["energy"]["competed"][x][yr], \
                        adj["carbon"]["competed"][x][yr] = [
                            (x[yr] * adj_frac_comp) for x in adjlist[6:]]

    def adj_htcl_add_rec(
            self, measures_adj, measures_adj_htcl_add, mseg_key, adopt_scheme):
        """Record additional adjustment data for heating/cooling microsegments.

        Notes:
            For heating/cooling measures, additional post-competition
            energy/carbon/cost adjustments may be required to reflect balancing
            of supply-side and demand-side heating/cooling energy and the
            effects of post-competition changes in secondary demand-side
            microsegments on supply-side and demand-side heating and cooling
            energy. This function records the data needed to make these added
            adjustments.

        Args:
            measures_adj (list): Measures that pertain to the current
                contributing microsegment being competed across measures.
            measures_adj_htcl_add (list): Measures requiring additional
                adjustments (outside of direct competitiont) to reflect
                changes in the current contributing microsegment.
            mseg_key (string): Key for current contributing microsegment being
                competed/adjusted across measures.
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Loop through all heating/cooling measures that apply to the the
        # current contributing microsegment
        for ind, m in enumerate(measures_adj):
            # Establish starting energy/carbon/cost totals and current
            # contributing energy/carbon/cost information for measure
            mast, adj, mast_list_base, mast_list_eff, adj_list_eff, \
                adj_list_base = self.compete_adjustment_dicts(
                    m, mseg_key, adopt_scheme)
            # Record any measure savings associated with the current
            # contributing microsegment; these will be used to implement
            # additional adjustments in the 'adj_htcl_add' function
            for yr in self.handyvars.aeo_years:
                # Loop through all measures that would be affected by
                # changes in savings for the current measure and contributing
                # microsegment; record the magnitude of these changes for
                # later use in adjusting energy/carbon/cost totals for these
                # affected measures after all competition is completed
                # (see 'adj_htcl_add' function)
                for ind2, ms in enumerate(measures_adj_htcl_add["measures"]):
                    # Ensure an adjustment is not being recorded for within
                    # the same measure, only across different measures
                    # (this would otherwise lead to double counting savings)
                    if ms.name != m.name:
                        keys = measures_adj_htcl_add["keys"][ind2]
                        for k in keys:
                            ms.markets[adopt_scheme]["competed"][
                                "mseg_adjust"]["supply-demand adjustment"][
                                "savings"][k][yr] += (
                                    adj["energy"]["total"]["baseline"][yr] -
                                    adj["energy"]["total"]["efficient"][yr])

    def adj_htcl_add(self, measures_adj_htcl_add, adopt_scheme):
        """Apply post-competition adjustments to measure energy/carbon/cost.

        Notes:
            These additional adjustments are required to balance supply-side
            and demand-side heating/cooling energy and account for the effects
            of competition-driven changes in secondary demand-side
            microsegments on supply-side and demand-side heating and cooling
            energy

        Args:
            measures_adj_htcl_add (list): Measures requiring additional
                post-competition adjustments to energy/carbon/cost totals.
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Loop through all measures requiring additional energy/carbon/cost
        # adjustments
        for m in measures_adj_htcl_add:
            for mseg in m.markets[adopt_scheme]["competed"]["mseg_adjust"][
                    "supply-demand adjustment"]["savings"].keys():
                # Establish starting energy/carbon/cost totals and current
                # contributing energy/carbon/cost information for measure
                mast, adj, mast_list_base, mast_list_eff, adj_list_eff, \
                    adj_list_base = self.compete_adjustment_dicts(
                        m, mseg, adopt_scheme)
                # Calculate post-competition adjustment fraction for measure
                # and adjust measure's energy/carbon/cost totals accordingly
                for yr in self.handyvars.aeo_years:
                    if m.markets[adopt_scheme]["competed"]["mseg_adjust"][
                            "supply-demand adjustment"][
                            "total"][mseg][yr] == 0:
                        adj_frac_add = 0
                    else:
                        adj_frac_add = m.markets[adopt_scheme][
                            "competed"]["mseg_adjust"][
                            "supply-demand adjustment"][
                            "savings"][mseg][yr] / \
                            m.markets[adopt_scheme]["competed"][
                            "mseg_adjust"]["supply-demand adjustment"][
                            "total"][mseg][yr]

                    # Apply adjustment fraction to total and competed
                    # baseline and efficient energy/carbon/cost data
                    for x in ["baseline", "efficient"]:
                        # Determine appropriate adjustment data to use
                        # for baseline or efficient case
                        if x == "baseline":
                            mastlist, adjlist = [mast_list_base, adj_list_base]
                        else:
                            mastlist, adjlist = [mast_list_eff, adj_list_eff]
                        # Adjust the total and competed energy, carbon, and
                        # associated cost savings by the secondary adjustment
                        # factor
                        mast["cost"]["energy"]["total"][x][yr], \
                            mast["cost"]["carbon"]["total"][x][yr], \
                            mast["energy"]["total"][x][yr],\
                            mast["carbon"]["total"][x][yr] = [
                                x[yr] - (y[yr] * adj_frac_add)
                                for x, y in zip(mastlist[1:5], adjlist[1:5])]
                        mast["cost"]["energy"]["competed"][x][yr], \
                            mast["cost"]["carbon"]["competed"][x][yr], \
                            mast["energy"]["competed"][x][yr],\
                            mast["carbon"]["competed"][x][yr] = [
                                x[yr] - (y[yr] * adj_frac_add)
                                for x, y in zip(mastlist[6:], adjlist[6:])]

    def compete_adjustment_dicts(self, m, mseg_key, adopt_scheme):
        """Set the initial measure market data needed to adjust for overlaps.

        Notes:
            Establishes a measure's initial stock/energy/carbon/cost totals
            (pre-competition) and the contributing microsegment information
            needed to adjust these totals following measure competition.

        Args:
            m (object): Measure needing market overlap adjustments.
            mseg_key (string): Key for competed market microsegment.
            adopt_scheme (string): Assumed consumer adoption scenario.

        Returns:
            Lists of initial measure master microsegment data and contributing
            microsegment data needed to adjust for competition across measures.
        """
        # Organize relevant starting master microsegment values into a list
        mast = m.markets[adopt_scheme]["competed"]["master_mseg"]
        # Set total-baseline and competed-baseline overall
        # stock/energy/carbon/cost totals to be updated in the
        # 'compete_adjustment', 'adj_secondary', and 'adj_htcl_add' functions
        mast_list_base = [
            mast["cost"]["stock"]["total"]["baseline"],
            mast["cost"]["energy"]["total"]["baseline"],
            mast["cost"]["carbon"]["total"]["baseline"],
            mast["energy"]["total"]["baseline"],
            mast["carbon"]["total"]["baseline"],
            mast["cost"]["stock"]["competed"]["baseline"],
            mast["cost"]["energy"]["competed"]["baseline"],
            mast["cost"]["carbon"]["competed"]["baseline"],
            mast["energy"]["competed"]["baseline"],
            mast["carbon"]["competed"]["baseline"]]
        # Set total-efficient and competed-efficient overall
        # stock/energy/carbon/cost totals to be updated in the
        # 'compete_adjustment', 'adj_secondary', and 'adj_htcl_add' functions
        mast_list_eff = [
            mast["cost"]["stock"]["total"]["efficient"],
            mast["cost"]["energy"]["total"]["efficient"],
            mast["cost"]["carbon"]["total"]["efficient"],
            mast["energy"]["total"]["efficient"],
            mast["carbon"]["total"]["efficient"],
            mast["cost"]["stock"]["competed"]["efficient"],
            mast["cost"]["energy"]["competed"]["efficient"],
            mast["cost"]["carbon"]["competed"]["efficient"],
            mast["energy"]["competed"]["efficient"],
            mast["carbon"]["competed"]["efficient"]]
        # Set up lists that will be used to determine the energy, carbon,
        # and cost totals associated with the contributing microsegment that
        # must be adjusted to reflect measure competition/interaction
        adj = m.markets[adopt_scheme]["competed"]["mseg_adjust"][
            "contributing mseg keys and values"][mseg_key]
        # Set total-baseline and competed-baseline contributing microsegment
        # stock/energy/carbon/cost totals to be updated in the
        # 'compete_adjustment', 'adj_secondary', and 'adj_htcl_add' functions
        adj_list_base = [
            adj["cost"]["stock"]["total"]["baseline"],
            adj["cost"]["energy"]["total"]["baseline"],
            adj["cost"]["carbon"]["total"]["baseline"],
            adj["energy"]["total"]["baseline"],
            adj["carbon"]["total"]["baseline"],
            adj["cost"]["stock"]["competed"]["baseline"],
            adj["cost"]["energy"]["competed"]["baseline"],
            adj["cost"]["carbon"]["competed"]["baseline"],
            adj["energy"]["competed"]["baseline"],
            adj["carbon"]["competed"]["baseline"]]
        # Set total-efficient and competed-efficient contributing microsegment
        # stock/energy/carbon/cost totals to be updated in the
        # 'compete_adjustment', 'adj_secondary', and 'adj_htcl_add' functions
        adj_list_eff = [
            adj["cost"]["stock"]["total"]["efficient"],
            adj["cost"]["energy"]["total"]["efficient"],
            adj["cost"]["carbon"]["total"]["efficient"],
            adj["energy"]["total"]["efficient"],
            adj["carbon"]["total"]["efficient"],
            adj["cost"]["stock"]["competed"]["efficient"],
            adj["cost"]["energy"]["competed"]["efficient"],
            adj["cost"]["carbon"]["competed"]["efficient"],
            adj["energy"]["competed"]["efficient"],
            adj["carbon"]["competed"]["efficient"]]

        return mast, adj, mast_list_base, mast_list_eff, adj_list_eff, \
            adj_list_base

    def compete_adjustment(
            self, adj_fracs, mast, adj, mast_list_base, mast_list_eff,
            adj_list_eff, adj_list_base, yr, mseg_key, measure, adopt_scheme):
        """Scale down measure stock/energy/carbon/cost totals to reflect competition.

        Notes:
            Scale stock/energy/carbon/cost totals associated with the current
            contributing market microsegment by the measure's market share for
            this microsegment; reflect these scaled down contributing
            microsegment totals in the measure's overall
            stock/energy/carbon/cost totals.

        Args:
            adj_fracs (dict): Competed market share(s) for the measure.
            mast (dict): Initial overall stock/energy/carbon/cost totals to
                adjust based on competed market share(s).
            adj (dict): Contributing microsegment data to use in adjusting
                overall stock/energy/carbon/cost following competition.
            mast_list_base (dict): Overall 'baseline' scenario
                stock/energy/carbon/cost totals.
            mast_list_eff (dict): Overall 'efficient' scenario
                stock/energy/carbon/cost totals.
            adj_list_eff (dict): Contributing microsegment 'efficient' scenario
                stock/energy/carbon/cost totals.
            adj_list_base (dict): Contributing microsegment 'baseline' scenario
                stock/energy/carbon/cost totals.
            yr (string): Current year in modeling time horizon.
            mseg_key (string): Key for competed market microsegment.
            measure (object): Measure needing competition adjustments.
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Set market shares for the competed stock in the current year, and
        # for the weighted combination of the competed stock for the current
        # and all previous years. Handle this calculation differently for
        # primary and secondary microsegment types

        # Set primary microsegment competed and total weighted market shares

        # Competed stock market share (represents adjustment for current
        # year)
        adj_frac_comp = copy.deepcopy(adj_fracs[yr])

        # Combine the competed market share adjustment for the stock
        # captured by the measure in the current year with that of the
        # stock captured by the measure in all previous years, yielding a
        # weighted market share adjustment

        # Determine the subset of all years leading up to the current
        # year in the modeling time horizon
        weighting_yrs = sorted([
            x for x in adj_fracs.keys() if int(x) <= int(yr)])
        # Loop through the above set of years, successively updating the
        # weighted market share based on the captured stock in each year
        for ind, wyr in enumerate(weighting_yrs):
            # First year in time horizon; weighted market share equals
            # market share for the captured stock in this year only
            if ind == 0:
                adj_frac_tot = copy.deepcopy(adj_fracs[wyr])
            # Subsequent year; weighted market share combines market share
            # for captured stock in current year and all previous years
            else:
                # Only update weighted market share if measure captures
                # stock in the current year
                if type(adj["stock"]["total"]["measure"][wyr]) == \
                    numpy.ndarray and all(
                        adj["stock"]["total"]["measure"][wyr]) != 0 or \
                   type(adj["stock"]["total"]["measure"][wyr]) != \
                    numpy.ndarray and \
                        adj["stock"]["total"]["measure"][wyr] != 0:
                    # Develop the split between captured stock in the
                    # current year and all previously captured stock
                    wt_comp = adj["stock"]["competed"]["all"][wyr] / \
                        adj["stock"]["total"]["all"][wyr]
                    # Calculate weighted combination of market shares for
                    # current and previously captured stock
                    adj_frac_tot = adj_fracs[wyr] * wt_comp + \
                        adj_frac_tot * (1 - wt_comp)

        # For a primary microsegment with secondary effects, record market
        # share information that will subsequently be used to adjust associated
        # secondary microsegments and associated energy/carbon/cost totals
        if len(measure.markets[adopt_scheme]["competed"]["mseg_adjust"][
                "secondary mseg adjustments"]["market share"][
                "original stock (total captured)"].keys()) > 0:
            # Determine the climate zone, building type, and structure
            # type for the current contributing primary microsegment from the
            # microsegment key chain information and use as the key for linking
            # the primary and its associated secondary microsegment
            cz_bldg_struct = literal_eval(mseg_key)
            secnd_mseg_adjkey = str((
                cz_bldg_struct[1], cz_bldg_struct[2], cz_bldg_struct[-1]))

            if secnd_mseg_adjkey in measure.markets[adopt_scheme][
                "competed"]["mseg_adjust"][
                "secondary mseg adjustments"]["market share"][
                    "original stock (total captured)"].keys():
                # Record original and adjusted primary stock numbers as part of
                # the measure's 'mseg_adjust' attribute
                secnd_adj_mktshr = measure.markets[adopt_scheme][
                    "competed"]["mseg_adjust"]["secondary mseg adjustments"][
                    "market share"]
                # Original total captured stock
                secnd_adj_mktshr["original stock (total captured)"][
                    secnd_mseg_adjkey][yr] += \
                    adj["stock"]["total"]["measure"][yr]
                # Original competed and captured stock
                secnd_adj_mktshr["original stock (competed and captured)"][
                    secnd_mseg_adjkey][yr] += \
                    adj["stock"]["competed"]["measure"][yr]
                # Adjusted total captured stock
                secnd_adj_mktshr["adjusted stock (total captured)"][
                    secnd_mseg_adjkey][yr] += \
                    (adj["stock"]["total"]["measure"][yr] * adj_frac_tot)
                # Adjusted competed and captured stock
                secnd_adj_mktshr["adjusted stock (competed and captured)"][
                    secnd_mseg_adjkey][yr] += \
                    (adj["stock"]["competed"]["measure"][yr] * adj_frac_comp)

        # Adjust the total and competed stock captured by the measure by
        # the appropriate measure market share, both overall and for the
        # current contributing microsegment
        mast["stock"]["total"]["measure"][yr] = \
            mast["stock"]["total"]["measure"][yr] - \
            adj["stock"]["total"]["measure"][yr] * (1 - adj_frac_tot)
        mast["stock"]["competed"]["measure"][yr] = \
            mast["stock"]["competed"]["measure"][yr] - \
            adj["stock"]["competed"]["measure"][yr] * (1 - adj_frac_comp)
        adj["stock"]["total"]["measure"][yr] = \
            adj["stock"]["total"]["measure"][yr] * adj_frac_tot
        adj["stock"]["competed"]["measure"][yr] = \
            adj["stock"]["competed"]["measure"][yr] * adj_frac_comp

        # Adjust total and competed baseline and efficient data by measure
        # market share
        for x in ["baseline", "efficient"]:
            # Determine appropriate adjustment data to use
            # for baseline or efficient case
            if x == "baseline":
                mastlist, adjlist = [mast_list_base, adj_list_base]
            else:
                mastlist, adjlist = [mast_list_eff, adj_list_eff]

            # Adjust the total and competed energy, carbon, and associated cost
            # savings by the appropriate measure market share, both overall
            # and for the current contributing microsegment
            mast["cost"]["stock"]["total"][x][yr], \
                mast["cost"]["energy"]["total"][x][yr], \
                mast["cost"]["carbon"]["total"][x][yr], \
                mast["energy"]["total"][x][yr], \
                mast["carbon"]["total"][x][yr] = [
                    x[yr] - (y[yr] * (1 - adj_frac_tot)) for x, y in
                    zip(mastlist[0:5], adjlist[0:5])]
            mast["cost"]["stock"]["competed"][x][yr], \
                mast["cost"]["energy"]["competed"][x][yr], \
                mast["cost"]["carbon"]["competed"][x][yr], \
                mast["energy"]["competed"][x][yr], \
                mast["carbon"]["competed"][x][yr] = [
                    x[yr] - (y[yr] * (1 - adj_frac_comp)) for x, y in
                    zip(mastlist[5:], adjlist[5:])]
            adj["cost"]["stock"]["total"][x][yr], \
                adj["cost"]["energy"]["total"][x][yr], \
                adj["cost"]["carbon"]["total"][x][yr], \
                adj["energy"]["total"][x][yr], \
                adj["carbon"]["total"][x][yr] = [
                    (x[yr] * adj_frac_tot) for x in adjlist[0:5]]
            adj["cost"]["stock"]["competed"][x][yr], \
                adj["cost"]["energy"]["competed"][x][yr], \
                adj["cost"]["carbon"]["competed"][x][yr], \
                adj["energy"]["competed"][x][yr], \
                adj["carbon"]["competed"][x][yr] = [
                    (x[yr] * adj_frac_comp) for x in adjlist[5:]]

    def finalize_outputs(self, adopt_scheme):
        """Prepare selected measure outputs to write to a summary JSON file.

        Args:
            adopt_scheme (string): Consumer adoption scenario to summarize
                outputs for.
        """
        # Set up subscript translator for carbon variable strings
        sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        # Loop through all measures and populate above dict of summary outputs
        for m in self.measures:
            # Set competed measure markets, savings, and portfolio-level
            # financial metrics
            mkts = m.markets[adopt_scheme]["competed"]["master_mseg"]
            save = m.savings[adopt_scheme]["competed"]
            metrics_port = m.portfolio_metrics[adopt_scheme]["competed"]
            # Group markets, savings, and portfolio metrics into list
            # for updates
            save_metric_uncertain = [
                mkts["energy"]["total"]["baseline"],
                mkts["carbon"]["total"]["baseline"],
                mkts["cost"]["energy"]["total"]["baseline"],
                mkts["cost"]["carbon"]["total"]["baseline"],
                mkts["energy"]["total"]["efficient"],
                mkts["carbon"]["total"]["efficient"],
                mkts["cost"]["energy"]["total"]["efficient"],
                mkts["cost"]["carbon"]["total"]["efficient"],
                save["energy"]["savings (total)"],
                save["energy"]["cost savings (total)"],
                save["carbon"]["savings (total)"],
                save["carbon"]["cost savings (total)"],
                metrics_port["cce"],
                metrics_port["cce (w/ carbon cost benefits)"],
                metrics_port["ccc"],
                metrics_port["ccc (w/ energy cost benefits)"]]
            # Order the year entries in the above markets, savings,
            # and portfolio metrics outputs
            save_metric_uncertain = [OrderedDict(
                sorted(x.items())) for x in save_metric_uncertain]

            # Check if the current measure's markets, savings, and
            # portfolio metrics are arrays of values. If so, find the
            # average and 5th/95th percentile values of each output
            # array and report out. Otherwise, report the point values
            # for each output
            if any([type(x) == numpy.ndarray for x in
                    save["energy"]["savings (total)"].values()]):
                # Average values for outputs
                energy_base_avg, carb_base_avg, energy_cost_base_avg, \
                    carb_cost_base_avg, energy_eff_avg, carb_eff_avg, \
                    energy_cost_eff_avg, \
                    carb_cost_eff_avg, energy_save_avg, \
                    energy_costsave_avg, carb_save_avg, \
                    carb_costsave_avg, cce_avg, cce_c_avg, ccc_avg, \
                    ccc_e_avg = [{
                        k: numpy.mean(v) for k, v in z.items()} for
                        z in save_metric_uncertain]
                # 5th percentile values for outputs
                energy_base_low, carb_base_low, energy_cost_base_low, \
                    carb_cost_base_low, energy_eff_low, carb_eff_low, \
                    energy_cost_eff_low, \
                    carb_cost_eff_low, energy_save_low, \
                    energy_costsave_low, carb_save_low, \
                    carb_costsave_low, cce_low, cce_c_low, ccc_low, \
                    ccc_e_low = [{
                        k: numpy.percentile(v, 5) for k, v in
                        z.items()} for z in save_metric_uncertain]
                # 95th percentile values for outputs
                energy_base_high, carb_base_high, energy_cost_base_high, \
                    carb_cost_base_high, energy_eff_high, carb_eff_high, \
                    energy_cost_eff_high, \
                    carb_cost_eff_high, energy_save_high, \
                    energy_costsave_high, carb_save_high, \
                    carb_costsave_high, cce_high, \
                    cce_c_high, ccc_high, ccc_e_high = [{
                        k: numpy.percentile(v, 95) for k, v in
                        z.items()} for z in save_metric_uncertain]
            else:
                energy_base_avg, carb_base_avg, energy_cost_base_avg, \
                    carb_cost_base_avg, energy_eff_avg, carb_eff_avg, \
                    energy_cost_eff_avg, \
                    carb_cost_eff_avg, energy_save_avg, \
                    energy_costsave_avg, carb_save_avg, \
                    carb_costsave_avg, cce_avg, cce_c_avg, ccc_avg, \
                    ccc_e_avg, energy_base_low, carb_base_low, \
                    energy_cost_base_low, \
                    carb_cost_base_low, energy_eff_low, carb_eff_low, \
                    energy_cost_eff_low, carb_cost_eff_low, \
                    energy_save_low, energy_costsave_low, \
                    carb_save_low, carb_costsave_low, cce_low, \
                    cce_c_low, ccc_low, ccc_e_low, energy_base_high, \
                    carb_base_high, energy_cost_base_high, \
                    carb_cost_base_high, energy_eff_high, \
                    carb_eff_high, energy_cost_eff_high, \
                    carb_cost_eff_high, energy_save_high, \
                    energy_costsave_high, carb_save_high, \
                    carb_costsave_high, cce_high, cce_c_high, \
                    ccc_high, ccc_e_high = [
                        x for x in save_metric_uncertain] * 3

            # Record updated markets and savings in Engine 'output'
            # attribute; yield low and high estimates on the values if
            # available
            if energy_eff_avg != energy_eff_low:
                self.output[m.name]["Markets and Savings (Overall)"][
                    adopt_scheme], self.output[m.name][
                    "Markets and Savings (by Category)"][
                    adopt_scheme] = (OrderedDict([
                        ("Baseline Energy Use (MMBtu)", energy_base_avg),
                        ("Efficient Energy Use (MMBtu)", energy_eff_avg),
                        ("Efficient Energy Use (low) (MMBtu)",
                            energy_eff_low),
                        ("Efficient Energy Use (high) (MMBtu)",
                            energy_eff_high),
                        ("Baseline CO2 Emissions (MMTons)".translate(sub),
                            carb_base_avg),
                        ("Efficient CO2 Emissions (MMTons)".translate(sub),
                            carb_eff_avg),
                        ("Efficient CO2 Emissions (low) (MMTons)".
                            translate(sub), carb_eff_low),
                        ("Efficient CO2 Emissions (high) (MMTons)".
                            translate(sub), carb_eff_high),
                        ("Baseline Energy Cost (USD)", energy_cost_base_avg),
                        ("Efficient Energy Cost (USD)", energy_cost_eff_avg),
                        ("Efficient Energy Cost (low) (USD)",
                            energy_cost_eff_low),
                        ("Efficient Energy Cost (high) (USD)",
                            energy_cost_eff_high),
                        ("Baseline CO2 Cost (USD)".translate(sub),
                            carb_cost_base_avg),
                        ("Efficient CO2 Cost (USD)".translate(sub),
                            carb_cost_eff_avg),
                        ("Energy Savings (MMBtu)", energy_save_avg),
                        ("Energy Cost Savings (USD)", energy_costsave_avg),
                        ("Avoided CO2 Emissions (MMTons)".
                            translate(sub), carb_save_avg),
                        ("CO2 Cost Savings (USD)".
                            translate(sub), carb_costsave_avg)]) for
                    n in range(2))
            else:
                self.output[m.name]["Markets and Savings (Overall)"][
                    adopt_scheme], self.output[m.name][
                    "Markets and Savings (by Category)"][
                    adopt_scheme] = (OrderedDict([
                        ("Baseline Energy Use (MMBtu)", energy_base_avg),
                        ("Efficient Energy Use (MMBtu)", energy_eff_avg),
                        ("Baseline CO2 Emissions (MMTons)".translate(sub),
                            carb_base_avg),
                        ("Efficient CO2 Emissions (MMTons)".translate(sub),
                            carb_eff_avg),
                        ("Baseline Energy Cost (USD)", energy_cost_base_avg),
                        ("Efficient Energy Cost (USD)", energy_cost_eff_avg),
                        ("Baseline CO2 Cost (USD)".translate(sub),
                            carb_cost_base_avg),
                        ("Efficient CO2 Cost (USD)".translate(sub),
                            carb_cost_eff_avg),
                        ("Energy Savings (MMBtu)", energy_save_avg),
                        ("Energy Cost Savings (USD)", energy_costsave_avg),
                        ("Avoided CO2 Emissions (MMTons)".
                            translate(sub), carb_save_avg),
                        ("CO2 Cost Savings (USD)".
                            translate(sub), carb_costsave_avg)]) for
                    n in range(2))

            # Scale down the measure's markets and savings by the
            # climate zone, building type, and end use partitioning
            # fractions previously established for the measure
            for k in self.output[m.name][
                "Markets and Savings (by Category)"][
                    adopt_scheme].keys():
                self.output[m.name][
                    'Markets and Savings (by Category)'][adopt_scheme][
                        k] = self.out_break_walk(
                        copy.deepcopy(m.markets[adopt_scheme][
                            "competed"]["mseg_out_break"]),
                        self.output[m.name][
                            'Markets and Savings (by Category)'][
                            adopt_scheme][k])

            # Record updated portfolio metrics in Engine 'output' attribute;
            # yield low and high estimates on the metrics if available
            if cce_avg != cce_low:
                self.output[m.name]["Financial Metrics"]["Portfolio Level"][
                    adopt_scheme] = OrderedDict([
                        ("Cost of Conserved Energy ($/MMBtu saved)",
                            cce_avg),
                        ("Cost of Conserved Energy (low) ($/MMBtu saved)",
                            cce_low),
                        ("Cost of Conserved Energy (high) ($/MMBtu saved)",
                            cce_high),
                        (("Cost of Conserved CO2 "
                          "($/MTon CO2 avoided)").
                         translate(sub), ccc_avg),
                        (("Cost of Conserved CO2 (low) "
                          "($/MTon CO2 avoided)").
                         translate(sub), ccc_low),
                        (("Cost of Conserved CO2 (high) "
                          "($/MTon CO2 avoided)").
                         translate(sub), ccc_high)])
            else:
                self.output[m.name]["Financial Metrics"]["Portfolio Level"][
                    adopt_scheme] = OrderedDict([
                        ("Cost of Conserved Energy ($/MMBtu saved)",
                            cce_avg),
                        (("Cost of Conserved CO2 "
                          "($/MTon CO2 avoided)").
                         translate(sub), ccc_avg)])

            # Set consumer-level financial metrics
            metrics = m.consumer_metrics
            # Group consumer-level financial metrics into list for updates
            consume_metric_uncertain = [
                metrics["irr (w/ energy costs)"],
                metrics["irr (w/ energy and carbon costs)"],
                metrics["payback (w/ energy costs)"],
                metrics["payback (w/ energy and carbon costs)"]]
            # Order the year entries in consumer metrics outputs
            consume_metric_uncertain = [OrderedDict(
                sorted(x.items())) for x in consume_metric_uncertain]

            # Check if the current measure's consumer metrics
            # are arrays of values. If so, find the average and 5th/95th
            # percentile values of each output array and report out.
            # Otherwise, report the point values for each output
            if any([type(x) == numpy.ndarray for x in
                    metrics["irr (w/ energy costs)"].values()]):
                # Average values for outputs
                irr_e_avg, irr_ec_avg, payback_e_avg, payback_ec_avg = \
                    [{k: numpy.mean(v) for k, v in z.items()} for
                     z in consume_metric_uncertain]
                # 5th percentile values for outputs
                irr_e_low, irr_ec_low, payback_e_low, payback_ec_low = \
                    [{k: numpy.percentile(v, 5) for k, v in z.items()} for
                     z in consume_metric_uncertain]
                # 95th percentile values for outputs
                irr_e_high, irr_ec_high, payback_e_high, \
                    payback_ec_high = [{
                        k: numpy.percentile(v, 95) for k, v in
                        z.items()} for z in consume_metric_uncertain]
            else:
                irr_e_avg, irr_ec_avg, payback_e_avg, payback_ec_avg, \
                    irr_e_low, irr_ec_low, payback_e_low, payback_ec_low, \
                    irr_e_high, irr_ec_high, payback_e_high, \
                    payback_ec_high = [
                        x for x in consume_metric_uncertain] * 3
            # Record updated consumer metrics in Engine 'output' attribute;
            # yield low and high estimates on the metrics if available
            if irr_e_avg != irr_e_low:
                self.output[m.name]["Financial Metrics"]["Consumer Level"] = \
                    OrderedDict([
                        ("IRR (%)", irr_e_avg),
                        ("IRR (low) (%)", irr_e_low),
                        ("IRR (high) (%)", irr_e_high),
                        ("Payback (years)", payback_e_avg),
                        ("Payback (low) (years)", payback_e_low),
                        ("Payback (high) (years)", payback_e_high)])
            else:
                self.output[m.name]["Financial Metrics"]["Consumer Level"] = \
                    OrderedDict([
                        ("IRR (%)", irr_e_avg),
                        ("Payback (years)", payback_e_avg)])

    def out_break_walk(self, adjust_dict, adjust_vals):
        """Partition measure results by climate, building sector, and end use.

        Args:
            adjust_dict (dict): Results partitioning structure and fractions
                for climate zone, building sector, and end use.
            adjust_vals (dict): Unpartitioned energy, carbon, and cost
                markets/savings.

        Returns:
            Measure results partitioned by climate, building sector, and
            end use.
        """
        for (k, i) in sorted(adjust_dict.items()):
            if isinstance(i, dict):
                self.out_break_walk(i, adjust_vals)
            else:
                # Apply appropriate climate zone/building type/end use
                # partitioning fraction to the overall market/savings
                # value
                adjust_dict[k] = adjust_dict[k] * adjust_vals[k]

        return adjust_dict


def main(base_dir):
    """Import, finalize, and write out measure savings and financial metrics.

    Note:
        Import measures from a JSON, calculate competed and uncompeted
        savings and financial metrics for each measure, and write a summary
        of key results to an output JSON.
    """
    # Instantiate useful input files object
    handyfiles = UsefulInputFiles()
    # Instantiate useful variables object
    handyvars = UsefulVars()

    # Import measure files
    with open((base_dir + handyfiles.meas_summary_data), 'r') as mjs:
        meas_summary = json.load(mjs)
    # Import list of all unique active measures
    with open((base_dir + handyfiles.active_measures), 'r') as am:
        active_meas_all = numpy.unique(json.load(am)["active"])
    print('Measure attributes data load complete')

    # Loop through measures data in JSON, initialize objects for all measures
    # that are active and valid
    measures_objlist = [Measure(handyvars, **m) for m in meas_summary if
                        m["name"] in active_meas_all and m["remove"] is False]

    # Load and set competition data for active measure objects
    for m in measures_objlist:
        with gzip.open((base_dir + handyfiles.meas_compete_data + '/' +
                       m.name + ".pkl.gz"), 'r') as zp:
            meas_comp_data = pickle.load(zp)
        for adopt_scheme in handyvars.adopt_schemes:
            m.markets[adopt_scheme]["uncompeted"]["mseg_adjust"] = \
                meas_comp_data[adopt_scheme]
            m.markets[adopt_scheme]["competed"]["mseg_adjust"] = \
                meas_comp_data[adopt_scheme]
        print("Imported measure '" + m.name + "' competition data")
    print('Measure competition data load complete')

    # Instantiate an Engine object using active measures list
    a_run = Engine(handyvars, measures_objlist)

    # Calculate uncompeted and competed measure savings and financial
    # metrics, and write key outputs to JSON file
    for adopt_scheme in handyvars.adopt_schemes:
        # Calculate each measure's uncompeted savings and metrics
        a_run.calc_savings_metrics(adopt_scheme, "uncompeted")
        print("Uncompeted '" + adopt_scheme +
              "' savings/metrics calculations complete")
        # Update each measure's competed markets to reflect the
        # removal of savings overlaps with competing measures
        a_run.compete_measures(adopt_scheme)
        print("Measure competition complete for '" +
              adopt_scheme + "' scenario")
        # Calculate each measure's competed measure savings and metrics
        # using updated competed markets
        a_run.calc_savings_metrics(adopt_scheme, "competed")
        print("Competed '" + adopt_scheme +
              "' savings/metrics calculations complete")
        # Write selected outputs to a summary JSON file for post-processing
        a_run.finalize_outputs(adopt_scheme)

    # Notify user that all analysis engine calculations are completed
    print('All calculations complete; writing output data...')
    # Write summary outputs for all measures to a JSON
    with open((base_dir + handyfiles.meas_engine_out), "w") as jso:
        json.dump(a_run.output, jso, indent=2)

if __name__ == '__main__':
    import time
    start_time = time.time()
    base_dir = getcwd()
    main(base_dir)
    print("--- Runtime: %s seconds ---" % round((time.time() - start_time), 2))
