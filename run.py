#!/usr/bin/env python3
import json
import numpy
import copy
import re
from numpy.linalg import LinAlgError
from collections import OrderedDict


class UsefulInputFiles(object):
    """Class of input files to be opened by this routine.

    Attributes:
        measures_in (string): Filename for database of initial measure
            definitions.
        json_output_file (string): Filename for summary results database.
    """

    def __init__(self):
        self.measures_in = "measures_test.json"
        self.json_output_file = "output_summary.json"


class UsefulVars(object):
    """Class of variables that are used globally across functions.

    Attributes:
        adopt_schemes (list): Possible consumer adoption scenarios.
        aeo_years (list) = Modeling time horizon.
        discount_rate (float): General rate to use in discounting cash flows.
        com_timeprefs (dict): Time preference premiums for commercial adopters.
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


class Measure(object):
    """Class representing individual efficiency measures.

    Attributes:
        **kwargs: Arbitrary keyword arguments used to fill measure attributes
            from an input dictionary.
        markets (dict): Data grouped by adoption scheme on:
            a) 'master_mseg': a measure's master market microsegments (stock,
               energy, carbon, cost),
            b) 'mseg_adjust': all microsegments that contribute to each master
               microsegment (required later for measure competition).
            c) 'mseg_out_break': master microsegment breakdowns by key
               variables (e.g., climate zone, building type, end use, etc.)
        update_results (dict): Flags markets, savings, and financial metric
            outputs that have yet to be finalized by the analysis engine.
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
        mkt = copy.deepcopy(self.markets)
        for adopt_scheme in handyvars.adopt_schemes:
            # Initialize 'uncompeted' and 'competed' versions of
            # Measure markets (initially, they are identical)
            self.markets[adopt_scheme] = {
                "uncompeted": mkt[adopt_scheme],
                "competed": mkt[adopt_scheme]}
            self.update_results = {
                "markets": False,
                "savings and portfolio metrics": {
                    "uncompeted": True, "competed": True},
                "consumer metrics": True}
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
            for adopt_scheme in self.handyvars.adopt_schemes:
                self.output[m.name] = OrderedDict([
                    ("Filter Variables", OrderedDict()),
                    ("Markets and Savings (Overall)", OrderedDict([
                        (adopt_scheme, OrderedDict())])),
                    ("Markets and Savings (by Category)", OrderedDict([
                        (adopt_scheme, OrderedDict())])),
                    ("Economic Metrics", OrderedDict([
                        ("Portfolio Level", OrderedDict([
                            (adopt_scheme, OrderedDict())])),
                        ("Consumer Level", OrderedDict([
                            (adopt_scheme, OrderedDict())]))]))])

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
            "savings and portfolio metrics"][comp_scheme] is True]

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
                    num_units = markets["stock"]["competed"]["measure"][yr]
                else:
                    num_units = markets["stock"]["total"]["measure"][yr]

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
                if type(num_units) != numpy.ndarray and num_units == 0 or \
                   type(num_units) == numpy.ndarray and all(num_units) == 0:
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
                    if type(num_units) != numpy.ndarray:
                        num_units = numpy.repeat(num_units, len_arr)

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
                        if num_units[x] == 0:
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
                                    m, num_units[x], life_base,
                                    int(life_meas_tmp[x]),
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
                            m, num_units, life_base, int(life_meas),
                            int(life_ratio), markets["cost"]["stock"][
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
            m.update_results[
                "savings and portfolio metrics"][comp_scheme] = False

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
        self, m, num_units, life_base, life_meas, life_ratio, scost_base,
            scostsave, esave, ecostsave, csave, ccostsave):
        """Calculate measure financial metrics for a given year.

        Notes:
            Calculate internal rate of return, simple payback, and cost of
            conserved energy/carbon from cash flows and energy/carbon
            savings across the measure lifetime.

        Args:
            m (object): Measure object.
            num_units (int): Number of competed baseline units in a given year.
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

        cashflows_s = cashflows_s / num_units

        # Construct complete energy and carbon cash flows across measure
        # lifetime (normalized by number of captured stock units). First
        # term (reserved for initial investment figure) is zero.
        cashflows_e, cashflows_c = [numpy.append(0, [x] * life_meas) /
                                    num_units for x in [ecostsave, ccostsave]]

        # Calculate Net Present Value (NPVs) using the above cashflows
        npv_s, npv_e, npv_c = [
            numpy.npv(self.handyvars.discount_rate, x) for x in [
                cashflows_s, cashflows_e, cashflows_c]]

        # Develop arrays of energy and carbon savings across measure
        # lifetime (for use in cost of conserved energy and carbon calcs).
        # First term (reserved for initial investment figure) is zero, and
        # each array is normalized by number of captured stock units
        esave_array = numpy.append(0, [esave] * life_meas) / num_units
        csave_array = numpy.append(0, [csave] * life_meas) / num_units

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
        if npv_esave != 0:
            cce = (-npv_s / npv_esave)
            cce_bens = (-(npv_s + npv_c) / npv_esave)

        # Calculate cost of conserved carbon w/ and w/o energy cost savings
        # benefits.  Check to ensure carbon savings NPV in the denominator
        # is not zero.
        if npv_csave != 0:
            ccc = (-npv_s / npv_csave)
            ccc_bens = (-(npv_s + npv_e) / npv_csave)

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
        """Remove overlaps in savings across competing measures.

        Notes:
            Adjust each competing measure's 'efficient' markets to
            reflect the removed savings overlaps, which are based on
            calculated market shares; these adjusted markets are
            subsequently entered into the 'calc_savings_metrics'
            function to calculate a measure's competed savings and
            portfolio-level financial metrics.

        Args:
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Establish list of key chains for all microsegments that contribute to
        # measure master microsegments, across all active measures
        mseg_keys = []
        measure_list = self.measures
        for x in measure_list:
            mseg_keys.extend(x.master[adopt_scheme]["competed"]["mseg_adjust"][
                "contributing mseg keys and values"].keys())

        # Establish list of unique key chains in mseg_keys list above,
        # ensuring that all primary microsegments are ordered (and thus
        # updated) before secondary microsegments that depend upon them
        msegs = sorted(numpy.unique(mseg_keys))

        # Run through all unique contributing microsegments in above list,
        # determining how the measure savings associated with each should be
        # adjusted to reflect measure competition/market shares and, if
        # applicable, the removal of overlapping heating/cooling supply-side
        # and demand-side savings
        for msu in msegs:

            # For a heating/cooling microsegment update, find all microsegments
            # that overlap with the current contributing microsegment across
            # the supply-side and demand-side (e.g., if the current
            # microsegment key is ['AIA_CZ1', 'single family home',
            # 'electricity (grid)', 'cooling', 'supply', 'ASHP'], find all
            # demand-side microsegments with ['AIA_CZ1', 'single family home',
            # 'electricity (grid)', 'cooling'] in their key chains.
            measures_overlap = {"measures": [], "keys": []}
            msu_split = None
            if 'supply' in msu or 'demand' in msu:
                # Search for microsegment key chains that match that of the
                # current microsegment up until the 'supply' or 'demand'
                # element of the chain

                # Establish key matching criteria
                if 'supply' in msu:
                    msu_split = re.search(
                        "'[a-zA-Z0-9_() /&-]+',\s'(.*)\,.*supply.*",
                        msu).group(1)
                else:
                    msu_split = re.search(
                        "'[a-zA-Z0-9_() /&-]+',\s'(.*)\,.*demand.*",
                        msu).group(1)
                # Loop through all measures to find key chain matches
                for m in measure_list:
                    mkts = m.markets[adopt_scheme]["competed"][
                        "mseg_adjust"]["contributing mseg keys and values"]
                    # Register the matching key chains
                    if 'supply' in msu:
                        keys = [x for x in mkts.keys() if
                                msu_split in x and 'demand' in x]
                    else:
                        keys = [x for x in mkts.keys() if
                                msu_split in x and 'supply' in x]
                    # Record the matched key chains and associated overlapping
                    # measure objects in a 'measures_overlap' dict to
                    # be used further in the 'rec_htcl_overlaps' routine below
                    if len(keys) > 0:
                        measures_overlap["measures"].append(m)
                        measures_overlap["keys"].append(keys)

            # Adjust a measure's primary savings based on the share of the
            # current market microsegment it captures when directly competed
            # against other measures that apply to the same microsegment
            if "primary" in msu:
                # Determine the subset of measures that pertain to the given
                # primary microsegment
                measures_adj = [x for x in measure_list if msu in x.master[
                    adopt_scheme]["competed"]["mseg_adjust"][
                        "contributing mseg keys and values"].keys()]
                # If multiple measures are competing for a primary
                # microsegment, determine the market shares of the
                # competing measures and adjust measure master microsegments
                # accordingly, using separate market share modeling routines
                # for residential and commercial sectors.
                if len(measures_adj) > 1 and any(x in msu for x in (
                        'single family home', 'multi family home',
                        'mobile home')):
                    self.compete_res_primary(measures_adj, msu, adopt_scheme)
                elif len(measures_adj) > 1 and all(x not in msu for x in (
                        'single family home', 'multi family home',
                        'mobile home')):
                    self.compete_com_primary(measures_adj, msu, adopt_scheme)
            # Adjust a measure's secondary savings based on the market share
            # previously calculated for the primary microsegment these
            # secondary savings are associated with
            elif "secondary" in msu:
                # Determine the subset of measures that pertain to the given
                # secondary microsegment and require updates to this
                # microsegment (the latter is indicated by the existence of
                # market share adjustment data for the secondary microsegment
                # in the measure's 'mseg_adjust' attribute)
                measures_adj = [
                    x for x in measure_list if len(x.master[
                        adopt_scheme]["competed"]["mseg_adjust"][
                        "secondary mseg adjustments"]["market share"][
                        "original stock (total captured)"].keys()) > 0 and
                    msu in x.master[adopt_scheme]["competed"]["mseg_adjust"][
                        "secondary mseg adjustments"]["market share"][
                        "original stock (total captured)"].keys()]
                # If at least one measure requires secondary microsegment
                # market share adjustments, proceed with the adjustment
                # calculation
                if len(measures_adj) > 0:
                    self.adj_secondary(measures_adj, msu)

            # If the microsegment applies to heating/cooling and overlaps with
            # other active microsegments across the heating/cooling supply-side
            # and demand-side, record any associated savings; these will be
            # removed from overlapping microsegments in the
            # 'rmv_htcl_overlaps' function below
            if len(measures_overlap["measures"]) > 0:
                self.rec_htcl_overlaps(
                    measures_adj, measures_overlap, msu, adopt_scheme)

        # Determine measures that require further savings adjustments to
        # reflect overlapping heating/cooling supply-side and demand-side
        # energy savings; remove these overlapping savings
        measures_overlap_adj = [x for x in measure_list if len(
            x.master[adopt_scheme]["competed"]["mseg_adjust"][
                "supply-demand adjustment"]["savings"].keys()) > 0]
        self.rmv_htcl_overlaps(measures_overlap_adj, adopt_scheme)

    def compete_res_primary(self, measures_adj, mseg_key, adopt_scheme):
        """Remove overlapping savings across competing residential measures.

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

        # Loop through competing measures and calculate market shares for
        # each based on their annualized capital and operating costs
        for ind, m in enumerate(measures_adj):
            # Set measure markets and market adjustment information
            mkts = m.markets[adopt_scheme]["competed"]["master_mseg"]
            mkts_adj = m.markets[adopt_scheme]["competed"]["mseg_adjust"]
            # # Loop through all years in modeling time horizon
            for yr in self.handyvars.aeo_years:
                # Ensure measure has captured stock to adjust in given year
                if (type(mkts["stock"]["competed"][
                    "measure"][yr]) == numpy.ndarray and all(
                    mkts["stock"]["competed"]["measure"][yr]) != 0) \
                    or (type(mkts["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and mkts[
                        "stock"]["competed"]["measure"][yr] != 0):
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
                        cap_cost * mkts_adj[
                            "competed choice parameters"][
                                str(mseg_key)]["b1"][yr] + op_cost *
                        mkts_adj["competed choice parameters"][
                            str(mseg_key)]["b2"][yr])
                    # Add calculated market fraction to mkt fraction sum
                    mkt_fracs_tot[yr] = \
                        mkt_fracs_tot[yr] + mkt_fracs[ind][yr]

        # Loop through competing measures to normalize their calculated
        # market shares to the total market share sum; use normalized
        # market shares to make adjustments to each measure's master
        # microsegment values
        for ind, m in enumerate(measures_adj):
            # Establish starting master microsegment and contributing
            # microsegment information
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.compete_adjustment_dicts(m, mseg_key, adopt_scheme)
            # Calculate annual market share fraction for the measure and
            # adjust measure's master microsegment values accordingly
            for yr in self.handyvars.aeo_years:
                # Ensure measure has captured stock to adjust in given year
                if (type(mkts["stock"]["competed"][
                    "measure"][yr]) == numpy.ndarray and all(
                    mkts["stock"]["competed"]["measure"][yr]) != 0) \
                    or (type(mkts["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and mkts[
                        "stock"]["competed"]["measure"][yr] != 0):
                    mkt_fracs[ind][yr] = \
                        mkt_fracs[ind][yr] / mkt_fracs_tot[yr]
                    # Make the adjustment to the measure's master microsegment
                    # based on its updated market share
                    self.compete_adjustment(
                        mkt_fracs[ind], base, adj, base_list_eff, adj_list_eff,
                        adj_list_base, yr, mseg_key, m, adopt_scheme)

    def compete_com_primary(self, measures_adj, mseg_key, adopt_scheme):
        """Remove overlapping savings across competing commercial measures.

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

        # Initialize a flag that indicates whether any competing measures
        # have arrays of annualized capital and/or operating costs rather
        # than point values (resultant of distributions on measure inputs)
        length_array = 0
        # Set abbreviated names for the dictionaries containing measure
        # capital and operating cost values, accessed further below

        # Annualized stock cost dictionary
        anpv_s_in = [m.consumer_metrics["anpv"]["stock cost"] for
                     m in measures_adj]
        # Annualized operating cost dictionary
        anpv_e_in = [m.consumer_metrics["anpv"]["energy cost"] for
                     m in measures_adj]

        # Loop through competing measures and calculate market shares for
        # each based on their annualized capital and operating costs
        for ind, m in enumerate(measures_adj):
            # Set measure markets and market adjustment information
            mkts = m.markets[adopt_scheme]["competed"]["master_mseg"]
            mkts_adj = m.markets[adopt_scheme]["competed"]["mseg_adjust"]
            # Loop through all years in modeling time horizon
            for yr in self.handyvars.aeo_years:
                # Ensure measure has captured stock to adjust in given year
                if (type(mkts["stock"]["competed"][
                    "measure"][yr]) == numpy.ndarray and all(
                    mkts["stock"]["competed"]["measure"][yr]) != 0) \
                    or (type(mkts["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and mkts[
                        "stock"]["competed"]["measure"][yr] != 0):
                    # Set measure capital and operating cost inputs. * Note:
                    # operating cost is set to just energy costs (for now), but
                    # could be expanded to include maintenance and carbon costs

                    # Determine whether any of the competing measures have
                    # arrays of annualized capital and/or operating costs; if
                    # so, find the array length. * Note: all array lengths
                    # should be equal to the 'nsamples' variable defined above
                    if length_array > 0 or \
                        any([type(x[yr]) == numpy.ndarray or
                             type(y[yr]) == numpy.ndarray for
                            x, y in zip(anpv_s_in, anpv_e_in)]) is True:
                        length_array = next(
                            (len(x[yr]) or len(y[yr]) for x, y in
                             zip(anpv_s_in, anpv_e_in) if type(x[yr]) ==
                             numpy.ndarray or type(y[yr]) == numpy.ndarray),
                            length_array)

                    # Handle cases where capital and/or operating cost inputs
                    # are specified as arrays for at least one of the competing
                    # measures. In this case, the capital and operating costs
                    # for all measures must be formatted consistently as arrays
                    # of the same length
                    if length_array > 0:
                        cap_cost, op_cost = ([
                            {} for n in range(length_array)] for n in range(2))
                        for i in range(length_array):
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
                            [] for n in range(length_array)]
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
            # Establish starting master microsegment and contributing
            # microsegment information
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.compete_adjustment_dicts(m, mseg_key, adopt_scheme)
            # Calculate annual market share fraction for the measure and
            # adjust measure's master microsegment values accordingly
            for yr in self.handyvars.aeo_years:
                # Ensure measure has captured stock to adjust in given year
                if (type(mkts["stock"]["competed"]["measure"][yr]) ==
                    numpy.ndarray and all(mkts["stock"]["competed"][
                        "measure"][yr]) != 0) or (
                    type(mkts["stock"]["competed"][
                        "measure"][yr]) != numpy.ndarray and mkts[
                        "stock"]["competed"]["measure"][yr] != 0):
                    # Set the fractions of commericial adopters who fall into
                    # each discount rate category for this particular
                    # microsegment
                    mkt_dists = mkts_adj["competed choice parameters"][
                        str(mseg_key)]["rate distribution"][yr]
                    # For each discount rate category, find which measure has
                    # the lowest annualized cost and assign that measure the
                    # share of commercial market adopters defined for that
                    # category above

                    # Handle cases where capital and/or operating cost inputs
                    # are specified as lists for at least one of the competing
                    # measures.
                    if length_array > 0:
                        mkt_fracs[ind][yr] = [
                            [] for n in range(length_array)]
                        for l in range(length_array):
                            for ind2, dr in enumerate(tot_cost[ind][yr][l]):
                                # If the measure has the lowest annualized
                                # cost, assign it the appropriate market share
                                # for the current discount rate category being
                                # looped through; otherwise, set its market
                                # fraction for that category to zero
                                if tot_cost[ind][yr][l][ind2] == \
                                   min([tot_cost[x][yr][l][ind2] for x in
                                        range(0, len(measures_adj))]):
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

                    # Make the adjustment to the measure's master microsegment
                    # based on its updated market share
                    self.compete_adjustment(
                        mkt_fracs[ind], base, adj, base_list_eff, adj_list_eff,
                        adj_list_base, yr, mseg_key, m, adopt_scheme)

    def adj_secondary(self, measures_adj, mseg_key, adopt_scheme):
        """Adjust secondary market microsegments to account for primary competition.

        Notes:
            Adjust a measure's secondary market microsegment values to reflect
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
        # Loop through all measures that apply to the current contributing
        # secondary microsegment
        for ind, m in enumerate(measures_adj):
            # Establish starting master microsegment and current contributing
            # secondary microsegment information for the measure
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.compete_adjustment_dicts(m, mseg_key, adopt_scheme)

            # Adjust measure savings for the current contributing
            # secondary microsegment based on the market share calculated
            # for an associated primary contributing microsegment
            for yr in self.handyvars.aeo_years:
                # Determine the climate zone, building type, and structure
                # type for the current contributing secondary microsegment
                # from the microsegment key chain information
                cz_bldg_struct = re.search(
                    ("'[a-zA-Z0-9_() /&-]+',\s'([a-zA-Z0-9_() /&-]+)',"
                     "\s'([a-zA-Z0-9_() /&-]+)',\s'[a-zA-Z0-9_() /&-]+',"
                     "\s'[a-zA-Z0-9_() /&-]+',\s'[a-zA-Z0-9_() /&-]+',"
                     "\s'[a-zA-Z0-9_() /&-]+',\s'([a-zA-Z0-9_() /&-]+)'"),
                    mseg_key)

                # Use climate zone, building type, and structure type as
                # the key for linking the secondary and its associated
                # primary microsegment
                secnd_mseg_adjkey = (
                    cz_bldg_struct.group(1), cz_bldg_struct.group(2),
                    cz_bldg_struct.group(3))
                # Find the appropriate market share adjustment information
                # for the given secondary climate zone, building type, and
                # structure type in the measure's 'mseg_adjust' attribute
                # and scale down the secondary and master savings accordingly
                secnd_adj_mktshr = m.markets[adopt_scheme]["competed"][
                    "mseg_adjust"]["secondary mseg adjustments"][
                    "market share"]
                # Check to ensure that market share adjustment information
                # exists for the secondary microsegment climate zone, building
                # type, and structure type
                if secnd_mseg_adjkey in \
                   secnd_adj_mktshr["original stock (total captured)"].keys():
                    # Calculate the market share adjustment factors to apply
                    # to the secondary and master savings, for both the
                    # currently competed secondary stock and the
                    # total current and previously competed secondary stock

                    # Initialize competed and total market adjustment factors
                    # for the secondary microsegments as 1 (no adjustment)
                    adj_factors = {"total": 1, "competed": 1}
                    # Update competed market adjustment factor if originally
                    # competed and captured baseline stock is not zero for
                    # current year
                    if secnd_adj_mktshr[
                            "original stock (competed and captured)"][
                            secnd_mseg_adjkey][yr] != 0:
                        adj_factors["competed"] = secnd_adj_mktshr[
                            "adjusted stock (competed and captured)"][
                            secnd_mseg_adjkey][yr] / secnd_adj_mktshr[
                            "original stock (competed and captured)"][
                            secnd_mseg_adjkey][yr]
                    # Update total market adjustment factor if total
                    # originally captured baseline stock is not zero for
                    # current year
                    if secnd_adj_mktshr["original stock (total captured)"][
                            secnd_mseg_adjkey][yr] != 0:
                        adj_factors["total"] = secnd_adj_mktshr[
                            "adjusted stock (total captured)"][
                            secnd_mseg_adjkey][yr] / secnd_adj_mktshr[
                            "original stock (total captured)"][
                            secnd_mseg_adjkey][yr]
                    # Apply any updated secondary market share adjustment
                    # factors to associated energy, carbon, and cost savings
                    if any([type(x) is numpy.ndarray or x != 1 for x in
                            adj_factors.values()]):
                        self.compete_adjustment(
                            adj_factors, base, adj, base_list_eff,
                            adj_list_eff, adj_list_base, yr, mseg_key, m,
                            adopt_scheme)
                # Raise error if no adjustment information exists
                else:
                    raise KeyError(
                        'Secondary market share adjustment info. missing!')

    def rec_htcl_overlaps(
            self, measures_adj, measures_overlap, mseg_key, adopt_scheme):
        """Record overlaps across supply/demand heating/cooling microsegments.

        Notes:
            For heating/cooling measures, record any savings associated
            with the current contributing microsegment that overlap with
            savings for other active contributing microsegments
            across the supply and demand sides of heating/cooling. For
            example, savings in an air source heat pump market (supply-side)
            reduces savings available to a windows conduction market
            (demand-side) and vice versa, though these two markets are not
            directly competed.

        Args:
            measures_adj (list): Measures needing a supply or demand-side
                heating/cooling overlap adjustment.
            measures_overlap (list): Measures that overlap with objects in
                'measures_adj' across the supply/demand sides of
                heating/cooling.
            mseg_key (string): Overlapping market microsegment information
                (mseg type->czone->bldg->fuel->end use->technology type
                 ->structure type).
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Loop through all heating/cooling measures that apply to the the
        # current contributing microsegment and which have savings overlaps
        # across the supply-side and demand-side
        for ind, m in enumerate(measures_adj):
            # Establish starting master microsegment and current contributing
            # microsegment information for the measure
            base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                self.compete_adjustment_dicts(m, mseg_key, adopt_scheme)
            # Record any measure savings associated with the current
            # contributing microsegment; these will be removed from
            # overlapping microsegments in the 'rmv_htcl_overlaps' function
            for yr in self.handyvars.aeo_years:
                # Loop through all overlapping measure microsegments and
                # record the overlapping savings associated with the
                # current measure microsegment
                for ind2, ms in enumerate(measures_overlap["measures"]):
                    keys = measures_overlap["keys"][ind2]
                    for k in keys:
                        ms.markets[adopt_scheme]["competed"]["mseg_adjust"][
                            "supply-demand adjustment"]["savings"][k][yr] += (
                                adj["energy"]["total"]["baseline"][yr] -
                                adj["energy"]["total"]["efficient"][yr])

    def rmv_htcl_overlaps(self, measures_overlap_adj, adopt_scheme):
        """Remove overlaps across supply/demand heating/cooling microsegments.

        Notes:
            For heating/cooling measures, remove any measure savings that
            have been determined to overlap with the savings of other heating/
            cooling measures across the supply and demand sides of
            heating/cooling.

        Args:
            measures_overlap_adj (list): Measures needing a supply or
                demand-side heating/cooling overlap adjustment.
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Loop through all heating/cooling measures with savings overlaps
        # across the supply-side and demand-side
        for m in measures_overlap_adj:
            for mseg in m.markets[adopt_scheme]["competed"]["mseg_adjust"][
                    "supply-demand adjustment"]["savings"].keys():
                # Establish starting master microsegment and contributing
                # microsegment information
                base, adj, base_list_eff, adj_list_eff, adj_list_base = \
                    self.compete_adjustment_dicts(m, mseg, adopt_scheme)
                # Calculate annual supply-demand overlap adjustment fraction
                # for the measure and adjust measure's master microsegment
                # values accordingly
                for yr in self.handyvars.aeo_years:
                    # Calculate supply-demand adjustment fraction
                    if m.markets[adopt_scheme]["competed"]["mseg_adjust"][
                            "supply-demand adjustment"][
                            "total"][mseg][yr] == 0:
                        overlap_adj_frac = 0
                    else:
                        overlap_adj_frac = m.markets[adopt_scheme]["competed"][
                            "mseg_adjust"]["supply-demand adjustment"][
                            "savings"][mseg][yr] / \
                            m.markets[adopt_scheme]["competed"][
                            "mseg_adjust"]["supply-demand adjustment"][
                            "total"][mseg][yr]
                    # Adjust total and competed savings by supply-demand
                    # adjustment fraction
                    base["cost"]["energy"]["total"]["efficient"][yr], \
                        base["cost"]["carbon"]["total"]["efficient"][yr], \
                        base["energy"]["total"]["efficient"][yr],\
                        base["carbon"]["total"]["efficient"][yr] = \
                            [x[yr] + ((z[yr] - y[yr]) * overlap_adj_frac)
                             for x, y, z in zip(
                                base_list_eff[1:5], adj_list_eff[1:5],
                                adj_list_base[1:5])]
                    base["cost"]["energy"]["competed"]["efficient"][yr], \
                        base["cost"]["carbon"]["competed"]["efficient"][yr], \
                        base["energy"]["competed"]["efficient"][yr],\
                        base["carbon"]["competed"]["efficient"][yr] = \
                            [x[yr] + ((z[yr] - y[yr]) * overlap_adj_frac)
                             for x, y, z in zip(
                                base_list_eff[6:], adj_list_eff[6:],
                                adj_list_base[6:])]

    def compete_adjustment_dicts(self, m, mseg_key, adopt_scheme):
        """Set the initial measure market data needed to adjust for overlaps.

        Notes:
            Establishes a measure's initial master microsegment (pre-
            competition) and the contributing microsegment information needed
            to adjust initial master microsegment values following measure
            competition and/or heating/cooling supply and demand-side savings
            overlap adjustments (see 'rec_htcl_overlaps' and
            'rmv_htcl_overlaps' functions).

        Args:
            m (object): Measure needing market overlap adjustments.
            mseg_key (string): Competed market microsegment information
                (mseg type->czone->bldg->fuel->end use->technology type
                 ->structure type).
            adopt_scheme (string): Assumed consumer adoption scenario.

        Returns:
            Lists of initial measure master microsegment data and contributing
            microsegment data needed to adjust for competition across measures.
        """
        # Organize relevant starting master microsegment values into a list
        base = m.markets[adopt_scheme]["competed"]["master_mseg"]
        # Set total-efficient and competed-efficient master microsegment
        # values to be updated in the compete_adjustment or rmv_htcl_overlaps
        # functions below
        base_list_eff = [
            base["cost"]["stock"]["total"]["efficient"],
            base["cost"]["energy"]["total"]["efficient"],
            base["cost"]["carbon"]["total"]["efficient"],
            base["energy"]["total"]["efficient"],
            base["carbon"]["total"]["efficient"],
            base["cost"]["stock"]["competed"]["efficient"],
            base["cost"]["energy"]["competed"]["efficient"],
            base["cost"]["carbon"]["competed"]["efficient"],
            base["energy"]["competed"]["efficient"],
            base["carbon"]["competed"]["efficient"]]
        # Set up lists that will be used to determine the energy, carbon,
        # and cost savings associated with the contributing microsegment that
        # must be adjusted according to a measure's calculated market share
        # and/or heating/cooling supply-side and demand-side savings overlaps
        adj = m.markets[adopt_scheme]["competed"]["mseg_adjust"][
            "contributing mseg keys and values"][mseg_key]
        # Total and competed baseline energy, carbon, and cost for contributing
        # microsegment
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
        # Total and competed energy, carbon, and cost for contributing
        # microsegment under full efficient measure adoption
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

        return base, adj, base_list_eff, adj_list_eff, adj_list_base

    def compete_adjustment(
            self, adj_fracs, base, adj, base_list_eff, adj_list_eff,
            adj_list_base, yr, mseg_key, measure, adopt_scheme):
        """Remove savings overlaps from a measure's master markets.

        Notes:
            Scale savings associated with the current contributing
            market microsegment by the measure's market share for
            this microsegment; remove any uncaptured savings from the
            measure's master market microsegments.

        Args:
            adj_fracs (dict): Competed market share(s) for the measure.
            base (dict): Initial master market microsegment data to adjust
                based on competed market share(s).
            adj (dict): Contributing market microsegment data to use in
                adjusting master microsegment data following competition.
            base_list_eff (dict): Master 'efficient' market microsegment.
            adj_list_eff (dict): Contributing 'efficient' market microsegment
                being competed.
            adj_list_base (dict): Contributing 'baseline' market microsegment
                being competed.
            yr (string): Current year in modeling time horizon.
            mseg_key (string): Competed market microsegment information
                (mseg type->czone->bldg->fuel->end use->technology type
                 ->structure type).
            measure (object): Measure needing market overlap adjustments.
            adopt_scheme (string): Assumed consumer adoption scenario.
        """
        # Set market shares for the competed stock in the current year, and
        # for the weighted combination of the competed stock for the current
        # and all previous years. Handle this calculation differently for
        # primary and secondary microsegment types

        # Set primary microsegment competed and total weighted market shares
        if "primary" in mseg_key:
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
                # market share for the captured stock in current year only
                if ind == 0:
                    adj_frac_tot = copy.deepcopy(adj_fracs[yr])
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
                        wt_comp = adj["stock"]["competed"]["measure"][wyr] / \
                            adj["stock"]["total"]["measure"][wyr]
                        # Calculate weighted combination of market shares for
                        # current and previously captured stock
                        adj_frac_tot = adj_fracs[wyr] * wt_comp + \
                            adj_frac_tot * (1 - wt_comp)
        # Set secondary microsegment competed and total weighted market shares
        # (based on competed/total market shares previously calculated for
        # associated primary microsegment)
        elif "secondary" in mseg_key:
            # Competed stock market share (represents adjustment for current
            # year)
            adj_frac_comp = adj_fracs["competed"]
            # Total weighted stock market share (represents adjustments for
            # current and all previous years)
            adj_frac_tot = adj_fracs["total"]

        # For a primary lighting microsegment with secondary effects,
        # record market share information that will subsequently be used
        # to adjust associated secondary microsegments and associated savings
        if "primary" in mseg_key and "lighting" in mseg_key and len(
            measure.markets[adopt_scheme]["competed"]["mseg_adjust"][
                "secondary mseg adjustments"]["market share"][
                "original stock (total captured)"].keys()) > 0:
            # Determine the climate zone, building type, and structure
            # type for the current contributing primary microsegment from the
            # microsegment key chain information
            cz_bldg_struct = re.search(
                ("'[a-zA-Z0-9_() /&-]+',\s'([a-zA-Z0-9_() /&-]+)',"
                 "\s'([a-zA-Z0-9_() /&-]+)',\s'[a-zA-Z0-9_() /&-]+',"
                 "\s'[a-zA-Z0-9_() /&-]+',\s'[a-zA-Z0-9_() /&-]+',"
                 "\s'([a-zA-Z0-9_() /&-]+)'"), mseg_key)

            # Use climate zone, building type, and structure type as the key
            # for linking the primary and its associated secondary microsegment
            secnd_mseg_adjkey = (
                cz_bldg_struct.group(1), cz_bldg_struct.group(2),
                cz_bldg_struct.group(3))

            # Record original and adjusted primary stock numbers as part of
            # the measure's 'mseg_adjust' attribute
            secnd_adj_mktshr = measure.markets[adopt_scheme]["competed"][
                "mseg_adjust"]["secondary mseg adjustments"]["market share"]
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
        # the appropriate measure market share for the master microsegment and
        # current contributing microsegment
        base["stock"]["total"]["measure"][yr] = \
            base["stock"]["total"]["measure"][yr] - \
            adj["stock"]["total"]["measure"][yr] * (1 - adj_frac_tot)
        base["stock"]["competed"]["measure"][yr] = \
            base["stock"]["competed"]["measure"][yr] - \
            adj["stock"]["competed"]["measure"][yr] * (1 - adj_frac_comp)
        adj["stock"]["total"]["measure"][yr] = \
            adj["stock"]["total"]["measure"][yr] * adj_frac_tot
        adj["stock"]["competed"]["measure"][yr] = \
            adj["stock"]["competed"]["measure"][yr] * adj_frac_comp

        # Adjust the total and competed energy, carbon, and associated cost
        # savings by the appropriate measure market share for the master
        # microsegment and current contributing microsegment
        base["cost"]["stock"]["total"]["efficient"][yr], \
            base["cost"]["energy"]["total"]["efficient"][yr], \
            base["cost"]["carbon"]["total"]["efficient"][yr], \
            base["energy"]["total"]["efficient"][yr], \
            base["carbon"]["total"]["efficient"][yr] = [
                x[yr] + ((z[yr] - y[yr]) * (1 - adj_frac_tot)) for x, y, z in
                zip(base_list_eff[0:5], adj_list_eff[0:5], adj_list_base[0:5])]
        base["cost"]["stock"]["competed"]["efficient"][yr], \
            base["cost"]["energy"]["competed"]["efficient"][yr], \
            base["cost"]["carbon"]["competed"]["efficient"][yr], \
            base["energy"]["competed"]["efficient"][yr], \
            base["carbon"]["competed"]["efficient"][yr] = [
                x[yr] + ((z[yr] - y[yr]) * (1 - adj_frac_comp)) for x, y, z in
                zip(base_list_eff[5:], adj_list_eff[5:], adj_list_base[5:])]
        adj["cost"]["stock"]["total"]["efficient"][yr], \
            adj["cost"]["energy"]["total"]["efficient"][yr], \
            adj["cost"]["carbon"]["total"]["efficient"][yr], \
            adj["energy"]["total"]["efficient"][yr], \
            adj["carbon"]["total"]["efficient"][yr] = [
                x[yr] + ((y[yr] - x[yr]) * (1 - adj_frac_tot)) for x, y in
                zip(adj_list_eff[0:5], adj_list_base[0:5])]
        adj["cost"]["stock"]["competed"]["efficient"][yr], \
            adj["cost"]["energy"]["competed"]["efficient"][yr], \
            adj["cost"]["carbon"]["competed"]["efficient"][yr], \
            adj["energy"]["competed"]["efficient"][yr], \
            adj["carbon"]["competed"]["efficient"][yr] = [
                x[yr] + ((y[yr] - x[yr]) * (1 - adj_frac_comp)) for x, y in
                zip(adj_list_eff[5:], adj_list_base[5:])]

    def write_outputs(self, json_output_file):
        """Write selected measure outputs to a summary JSON file.

        Args:
            json_output_file (string): JSON output file name.
        """
        # Set up subscript translator for carbon variable strings
        sub = str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉")
        # Loop through all measures and populate above dict of summary outputs
        for m in self.measures:
            # Set measure filter variables
            self.output[m.name]["Filter Variables"] = OrderedDict([
                ("Measure Climate Zone", m.climate_zone),
                ("Measure Building Type", m.bldg_type),
                ("Measure Structure Type", m.structure_type),
                ("Measure Fuel Type", m.fuel_type["primary"]),
                ("Measure End Use", m.end_use["primary"])])

            # Loop through consumer adoption schemes
            for adopt_scheme in self.handyvars.adopt_schemes:
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
                # Record updated consumer metrics in Engine 'output' attribute
                self.output[m.name]["Economic Metrics"]["Consumer Level"] = \
                    OrderedDict([
                        ("IRR (%)", irr_e_avg),
                        ("IRR (low) (%)", irr_e_low),
                        ("IRR (high) (%)", irr_e_high),
                        ("IRR (w/ CO2 cost savings) (%)".translate(sub),
                            irr_ec_avg),
                        ("IRR (w/ CO2 cost savings) (low) (%)".translate(sub),
                            irr_ec_low),
                        ("IRR (w/ CO2 cost savings) (high) (%)".translate(sub),
                            irr_ec_high),
                        ("Payback (years)", payback_e_avg),
                        ("Payback (low) (years)", payback_e_low),
                        ("Payback (high) (years)", payback_e_high),
                        ("Payback (w/ CO2 cost savings) (years)".translate(
                            sub), payback_ec_avg),
                        (("Payback (w/ CO2 cost savings) "
                          "(low) (years)").translate(sub), payback_ec_low),
                        (("Payback (w/ CO2 cost savings) "
                          "(high) (years)").translate(sub), payback_ec_high)])

                # Loop through measure competition schemes
                for comp_scheme in ["uncompeted", "competed"]:
                    # Set measure markets, savings, and portfolio-level
                    # financial metrics
                    mkts = m.markets[adopt_scheme][comp_scheme]["master_mseg"]
                    save = m.savings[adopt_scheme][comp_scheme]
                    metrics_port = m.portfolio_metrics[
                        adopt_scheme][comp_scheme]
                    # Group markets, savings, and portfolio metrics into list
                    # for updates
                    save_metric_uncertain = [
                        mkts["energy"]["total"]["efficient"],
                        mkts["carbon"]["total"]["efficient"],
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
                        energy_eff_avg, carb_eff_avg, energy_save_avg, \
                            energy_costsave_avg, carb_save_avg, \
                            carb_costsave_avg, cce_avg, cce_c_avg, ccc_avg, \
                            ccc_e_avg = [{
                                k: numpy.mean(v) for k, v in z.items()} for
                                z in save_metric_uncertain]
                        # 5th percentile values for outputs
                        energy_eff_low, carb_eff_low, energy_save_low, \
                            energy_costsave_low, carb_save_low, \
                            carb_costsave_low, cce_low, cce_c_low, ccc_low, \
                            ccc_e_low = [{
                                k: numpy.percentile(v, 5) for k, v in
                                z.items()} for z in save_metric_uncertain]
                        # 95th percentile values for outputs
                        energy_eff_high, carb_eff_high, energy_save_high, \
                            energy_costsave_high, carb_save_high, \
                            carb_costsave_high, cce_high, \
                            cce_c_high, ccc_high, ccc_e_high = [{
                                k: numpy.percentile(v, 95) for k, v in
                                z.items()} for z in save_metric_uncertain]
                    else:
                        energy_eff_avg, carb_eff_avg, energy_save_avg, \
                            energy_costsave_avg, carb_save_avg, \
                            carb_costsave_avg, cce_avg, cce_c_avg, ccc_avg, \
                            ccc_e_avg, energy_eff_low, carb_eff_low, \
                            energy_save_low, energy_costsave_low, \
                            carb_save_low, carb_costsave_low, cce_low, \
                            cce_c_low, ccc_low, ccc_e_low, energy_eff_high, \
                            carb_eff_high, energy_save_high, \
                            energy_costsave_high, carb_save_high, \
                            carb_costsave_high, cce_high, cce_c_high, \
                            ccc_high, ccc_e_high = [
                                x for x in save_metric_uncertain] * 3
                    # Record updated markets and savings in Engine 'output'
                    # attribute
                    self.output[m.name]["Markets and Savings (Overall)"][
                        adopt_scheme][comp_scheme], self.output[m.name][
                        "Markets and Savings (by Category)"][
                        adopt_scheme][comp_scheme] = (OrderedDict([
                            # Order year entries of baseline energy market
                            ("Baseline Energy Use (MMBtu)",
                                OrderedDict(sorted(mkts[
                                    "energy"]["total"]["baseline"].items()))),
                            ("Efficient Energy Use (MMBtu)", energy_eff_avg),
                            ("Efficient Energy Use (low) (MMBtu)",
                                energy_eff_low),
                            ("Efficient Energy Use (high) (MMBtu)",
                                energy_eff_high),
                            # Order year entries of baseline carbon market
                            ("Baseline CO2 Emissions  (MMTons)".translate(sub),
                                OrderedDict(sorted(mkts[
                                    "carbon"]["total"]["baseline"].items()))),
                            ("Efficient CO2 Emissions (MMTons)".translate(sub),
                                carb_eff_avg),
                            ("Efficient CO2 Emissions (low) (MMTons)".
                                translate(sub), carb_eff_low),
                            ("Efficient CO2 Emissions (high) (MMTons)".
                                translate(sub), carb_eff_high),
                            ("Energy Savings (MMBtu)", energy_save_avg),
                            ("Energy Savings (low) (MMBtu)",
                                energy_save_low),
                            ("Energy Savings (high) (MMBtu)",
                                energy_save_high),
                            ("Energy Cost Savings (USD)", energy_costsave_avg),
                            ("Energy Cost Savings (low) (USD)",
                                energy_costsave_low),
                            ("Energy Cost Savings (high) (USD)",
                                energy_costsave_high),
                            ("Avoided CO2 Emissions (MMTons)".
                                translate(sub), carb_save_avg),
                            ("Avoided CO2 Emissions (low) (MMTons)".
                                translate(sub), carb_save_low),
                            ("Avoided CO2 Emissions (high) (MMTons)".
                                translate(sub), carb_save_high),
                            ("CO2 Cost Savings (USD)".
                                translate(sub), carb_costsave_avg),
                            ("CO2 Cost Savings (low) (USD)".
                                translate(sub), carb_costsave_low),
                            ("CO2 Cost Savings (high) (USD)".
                                translate(sub), carb_costsave_high)]) for
                        n in range(2))

                    # Scale down the measure's markets and savings by the
                    # climate zone, building type, and end use partitioning
                    # fractions previously established for the measure
                    for k in self.output[m.name][
                        "Markets and Savings (by Category)"][
                            adopt_scheme][comp_scheme].keys():
                        self.output[m.name][
                            'Markets and Savings (by Category)'][adopt_scheme][
                            comp_scheme][k] = self.out_break_walk(
                                copy.deepcopy(m.markets[adopt_scheme][
                                    comp_scheme]["mseg_out_break"]),
                                self.output[m.name][
                                    'Markets and Savings (by Category)'][
                                    adopt_scheme][comp_scheme][k])

                    # Record updated portfolio metrics in Engine 'output'
                    # attribute
                    self.output[m.name]["Economic Metrics"]["Portfolio Level"][
                        adopt_scheme][comp_scheme] = OrderedDict([
                            ("Cost of Conserved Energy ($/MMBtu saved)",
                                cce_avg),
                            ("Cost of Conserved Energy (low) ($/MMBtu saved)",
                                cce_low),
                            ("Cost of Conserved Energy (high) ($/MMBtu saved)",
                                cce_high),
                            (("Cost of Conserved Energy (w/ CO2 cost savings "
                              "benefit) ($/MMBtu saved)").
                             translate(sub), cce_c_avg),
                            (("Cost of Conserved Energy (w/ CO2 cost savings "
                              "benefit) (low) ($/MMBtu saved)").
                             translate(sub), cce_c_low),
                            (("Cost of Conserved Energy (w/ CO2 cost savings "
                              "benefit) (high) ($/MMBtu saved)").
                             translate(sub), cce_c_high),
                            (("Cost of Conserved CO2 "
                              "($/MMTon CO2 avoided)").
                             translate(sub), ccc_avg),
                            (("Cost of Conserved CO2 (low) "
                              "($/MMTon CO2 avoided)").
                             translate(sub), ccc_low),
                            (("Cost of Conserved CO2 (high) "
                              "($/MMTon CO2 avoided)").
                             translate(sub), ccc_high),
                            (("Cost of Conserved CO2 "
                              "(w/ energy cost savings benefit) "
                              "($/MMTon CO2 avoided)").
                             translate(sub), ccc_e_avg),
                            (("Cost of Conserved CO2 (low) "
                              "(w/ energy cost savings benefit) "
                              "($/MMTon CO2 avoided)").
                             translate(sub), ccc_e_low),
                            (("Cost of Conserved CO2 (high) "
                              "(w/ energy cost savings benefit) "
                              "($/MMTon CO2 avoided)").
                             translate(sub), ccc_e_high)])

        # Write summary outputs for all measures to a JSON
        with open(json_output_file, "w") as jso:
            json.dump(self.output, jso, indent=4)

    def out_break_walk(self, adjust_dict, adjust_vals):
        """Partition measure results by climate, building sector, and end use.

        Args:
            adjust_dict (dict): Unpartitioned energy, carbon, and cost
                markets/savings.
            adjust_vals (dict): Results partitioning fractions for climate
                zone, building sector, and end use.

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


def main():
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

    # Import measures/microsegments files
    with open(handyfiles.measures_in, 'r') as mjs:
        measures_input = json.load(mjs)

    # Loop through measures data in JSON, initialize objects for all measures
    # that are active
    measures_objlist = [Measure(handyvars, **mi) for mi in measures_input if
                        mi["status"]["active"] is True]

    # Instantiate an Engine object using active measures list
    a_run = Engine(handyvars, measures_objlist)

    # Calculate uncompeted and competed measure savings and financial
    # metrics, and write key outputs to JSON file
    for adopt_scheme in handyvars.adopt_schemes:
        # Calculate each measure's uncompeted savings and metrics
        a_run.calc_savings_metrics(adopt_scheme, "uncompeted")
        # Update each measure's competed markets to reflect the
        # removal of savings overlaps with competing measures
        a_run.compete_measures(adopt_scheme)
        # Calculate each measure's competed measure savings and metrics
        # using updated competed markets
        a_run.calc_savings_metrics(adopt_scheme, "competed")
        # Write selected outputs to a summary JSON file for post-processing
        a_run.write_outputs(handyfiles.json_output_file)

if __name__ == '__main__':
    import time
    start_time = time.time()
    main()
    print("--- Runtime: %s seconds ---" % round((time.time() - start_time), 2))
