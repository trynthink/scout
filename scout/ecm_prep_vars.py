from __future__ import annotations
import argparse
import itertools
import numpy
from datetime import datetime
from collections import OrderedDict
from scout.utils import JsonIO
from scout.config import FilePaths as fp


class UsefulVars(object):
    """Class of variables that are used globally across functions.

    Attributes:
        adopt_schemes_prep (list): Adopt schemes to use in preparing ECM data.
        adopt_schemes_run (list): Adopt schemes to be used in competing ECMs.
        full_dat_out (dict): Flag that limits technical potential (TP) data
            prep/reporting when TP is not in user-specified adoption schemes.
        discount_rate (float): Rate to use in discounting costs/savings.
        nsamples (int): Number of samples to draw from probability distribution
            on measure inputs.
        regions (string): User region settings.
        aeo_years (list): Modeling time horizon.
        aeo_years_summary (list): Reduced set of snapshot years in the horizon.
        retro_rate (dict): Annual rate of deep retrofitting existing stock.
        demand_tech (list): All demand-side heating/cooling technologies.
        zero_cost_tech (list): All baseline technologies with cost of zero.
        inverted_relperf_list (list) = Performance units that require
            an inverted relative performance calculation (e.g., an air change
            rate where lower numbers indicate higher performance).
        valid_submkt_urls (list) = Valid URLs for sub-market scaling fractions.
        consumer_price_ind (numpy.ndarray) = Historical Consumer Price Index.
        ss_conv (dict): Site-source conversion factors by fuel type.
        fuel_switch_conv (dict): Performance unit conversions for expected
            fuel switching cases.
        carb_int (dict): Carbon intensities by fuel type (MMTon/quad).
        ecosts (dict): Energy costs by building and fuel type ($/MMBtu).
        ccosts (dict): Carbon costs ($/MTon).
        com_timeprefs (dict): Commercial adoption time preference premiums.
        hp_rates (dict): Exogenous rates of conversions from baseline
            equipment to heat pumps, if applicable.
        link_htcl_tover_anchor_tech_opts = For measures that apply to separate
            heating and cooling technologies, stock turnover and exogenous
            switching rates will be anchored on whichever technology in the
            measure's definition appears first in the lists in this dict,
            given the anchor end use above and applicable bldg. type (res/com)
        fug_emissions (dict): Refrigerant leakage data and supply chain
            methane data to support assessments of fugitive emissions.
        in_all_map (dict): Maps any user-defined measure inputs marked 'all' to
            list of climates, buildings, fuels, end uses, or technologies.
        valid_mktnames (list): List of all valid applicable baseline market
            input names for a measure.
        out_break_czones (OrderedDict): Maps measure climate zone names to
            the climate zone categories used in summarizing measure outputs.
        out_break_bldgtypes (OrderedDict): Maps measure building type names to
            the building sector categories used in summarizing measure outputs.
        out_break_enduses (OrderedDict): Maps measure end use names to
            the end use categories used in summarizing measure outputs.
        out_break_eus_w_fsplits (List): List of end use categories that
            would potentially apply across multiple fuels.
        out_break_fuels (OrderedDict): Maps measure fuel types to electric vs.
            non-electric fuels (for heating, cooling, WH, and cooking).
        out_break_in (OrderedDict): Breaks out key measure results by
            climate zone, building sector, and end use.
        cconv_topkeys_map (dict): Maps measure cost units to top-level keys in
            an input cost conversion data dict.
        tech_units_rmv (list): Flags baseline performance units that cannot
            currently be handled, thus the associated segment must be removed.
        tech_units_map (dict): Maps baseline performance units to measure units
            in cases where the conversion is expected (e.g., EER to COP).
        sf_to_house (dict): Stores information for mapping stock units in
            sf to number of households, as applicable.
        com_eqp_eus_nostk (list): Flags commercial equipment end uses for
            which no service demand data (which are used to represent com.
            "stock") are available and square footage should be used for stock.
        res_lts_per_home (list): RECS 2015 Table HC5.1 number of lights per
            household, by building type, used to get from $/home to $/bulb
        cconv_tech_mltstage_map (dict): Maps measure cost units to cost
            conversion dict keys for demand-side heating/cooling
            technologies and controls technologies requiring multiple
            conversion steps (e.g., $/ft^2 glazing -> $/ft^2 wall ->
            $/ft^2 floor).
        cconv_bybldg_units (list): Flags cost unit conversions that must
            be re-initiated for each new microsegment building type.
        deflt_choice (list): Residential technology choice capital/operating
            cost parameters to use when choice data are missing.
        regions (str): Regions to use in geographically breaking out the data.
        warm_cold_regs (dict): Warm and cold climate subsets of current
            region set.
        region_cpl_mapping (str or dict): Maps states to census divisions for
            the case where states are used; otherwise empty string.
        self.com_RTU_fs_tech (list): Flag heating tech. that pairs with RTU.
        self.com_nRTU_fs_tech (list): Flag heating tech. that pairs with
            larger commercial cooling equipment (not RTU).
        resist_ht_wh_tech (list): Flag for resistance-based heat/WH technology.
        minor_hvac_tech (list): Minor/secondary HVAC tech. to remove stock/
            stock/cost data for when major tech. is also in measure definition.
        alt_attr_brk_map (dict): Mapping factors used to handle alternate
            regional breakouts in measure performance, cost, or mkt. scaling.
        months (str): Month sequence for accessing time-sensitive data.
        tsv_feature_types (list): Possible types of TSV features.
        tsv_climate_regions (list): Possible ASHRAE climate regions for
            time-sensitive analysis and metrics.
        tsv_nerc_regions (list): Possible NERC regions for time-sensitive data.
        tsv_metrics_data (str): Includes information on max/min net system load
            hours, peak/take net system load windows, and peak days by EMM
            region/season, as well as days of year to attribute to each season.
        tsv_hourly_price (dict): Dict for storing hourly price factors.
        tsv_hourly_emissions (dict): Dict for storing hourly emissions factors.
        tsv_hourly_lafs (dict): Dict for storing annual energy, cost, and
            carbon adjustment factors by region, building type, and end use.
        emm_name_num_map (dict): Maps EMM region names to EIA region numbers.
        cz_emm_map (dict): Maps climate zones to EMM region net system load
            shape data.
        state_emm_map (dict): Maps states to the EMM region with the largest
            geographical overlap.
        health_scn_names (list): List of public health data scenario names.
        health_scn_data (numpy.ndarray): Public health cost data.
        env_heat_ls_scrn (tuple): Envelope heat gains to screen out of time-
            sensitive valuation for heating (no load shapes for these gains).
        skipped_ecms (int): List of names for ECMs skipped due to errors.
        save_shp_warn (list): Tracks missing savings shape error history.
    """

    def __init__(self, base_dir, handyfiles, opts):
        # Set adoption schemes to use in preparing ECM data. Note that high-
        # level technical potential (TP) market data are always prepared, even
        # if the user has excluded the TP adoption scheme from the run, because
        # these data are later required to derive unit-level metrics in the
        # ECM competition module
        self.adopt_schemes_prep = ["Technical potential"]
        if opts.adopt_scn_restrict is False or \
                "Max adoption potential" in opts.adopt_scn_restrict:
            self.adopt_schemes_prep.append("Max adoption potential")
        # Assume default adoption scenarios will be used in the competition
        # scheme if user doesn't specify otherwise
        if opts.adopt_scn_restrict is False:
            self.adopt_schemes_run = self.adopt_schemes_prep
        # Otherwise set adoption scenarios to be used in the competition
        # scheme to the user-specified choice
        else:
            self.adopt_schemes_run = opts.adopt_scn_restrict
        # Only prepare full datasets (including high-level and detailed market
        # information) for adoption scenarios that will be used in the
        # competition scheme. If a user has excluded the technical potential
        # scheme, a limited set of high-level market data are prepared; these
        # data are needed to calculate unit-level cost metrics for competition
        self.full_dat_out = {
            a_s: (True if a_s in self.adopt_schemes_run else False)
            for a_s in self.adopt_schemes_prep}

        self.discount_rate = 0.07
        self.nsamples = 100
        self.regions = opts.alt_regions
        # Load metadata including AEO year range
        aeo_yrs = JsonIO.load_json(handyfiles.metadata)
        # Set minimum modeling year to current year
        aeo_min = datetime.today().year
        # Set maximum modeling year
        aeo_max = aeo_yrs["max year"]
        # Derive time horizon from min/max years
        self.aeo_years = [
            str(i) for i in range(aeo_min, aeo_max + 1)]
        self.aeo_years_summary = ["2030", "2050"]
        # Set early retrofit rate assumptions

        # Default case (zero early retrofits) or user has set early retrofits
        # to zero
        if opts.retro_set is False or opts.retro_set[0] == "1":
            self.retro_rate = {yr: 0 for yr in self.aeo_years}
        # User has set early retrofits to non-zero
        else:
            # Set default assumptions about starting values for early
            # retrofits at the technology component-level. Values are based
            # on survey questions about renovations in CBECS and the American
            # Housing Survey, which cover lighting, HVAC, and envelope for
            # commercial and HVAC and envelope for residential, respectively.
            # Water heating values are assumed to be identical to HVAC
            # values for the given building type, and residential lighting
            # values are assumed to be identical to commercial values. Values
            # for all other components are set to zero.
            start_vals = {
                "commercial": {
                    "lighting": 0.015, "HVAC": 0.009, "roof": 0.006,
                    "windows": 0.003, "wall": 0.003,
                    "water heating": 0.009, "other": 0
                },
                "residential": {
                    "lighting": 0.015, "HVAC": 0.005, "roof": 0.0027,
                    "windows": 0.0023, "wall": 0.0006,
                    "water heating": 0.005, "other": 0
                }
            }

            # Set multipliers that progressively scale up the early retrofit
            # values over time

            # User desires no change in starting values for early retrofits
            # across the modeled time horizon; set multipliers to 1 across yrs.
            if opts.retro_set[0] == "2":
                multipliers = {yr: 1 for yr in self.aeo_years}
            # User specified a rate multiplier and year by which it is
            # achieved; assume linear increase in early retrofit rates from
            # starting values to the increased values by the indicated year,
            # and maintain increased value for all years thereafter
            else:
                # Pull in user-defined rate multiplier and year by which it
                # is achieved
                rate_inc, yr_inc = opts.retro_set[1:3]
                # Calculate progressively increasing multipliers to the early
                # retrofit rate based on user settings
                multipliers = {yr: 1 + ((rate_inc - 1) / (yr_inc - aeo_min)) *
                               (int(yr) - aeo_min) if int(yr) < yr_inc else
                               rate_inc for yr in self.aeo_years}
            # For each year, multiply starting early retrofit rate values by
            # rate multipliers to obtain final early retrofit rates by year;
            # nest by building type and technology component, consistent with
            # the structure of the starting values above
            self.retro_rate = {bldg: {cmpo: {
                yr: start_vals[bldg][cmpo] * multipliers[yr]
                for yr in self.aeo_years} for cmpo in start_vals[bldg].keys()}
                for bldg in start_vals.keys()}

        self.demand_tech = [
            'roof', 'ground', 'lighting gain', 'windows conduction',
            'equipment gain', 'floor', 'infiltration', 'people gain',
            'windows solar', 'ventilation', 'other heat gain', 'wall']
        # Note: ASHP costs are zero by convention in EIA data for new
        # construction
        self.zero_cost_tech = ['infiltration', 'ASHP']
        self.inverted_relperf_list = ["ACH", "CFM/ft^2 @ 0.3 in. w.c.",
                                      "kWh/yr", "kWh/day", "SHGC", "HP/CFM",
                                      "kWh/cycle"]
        self.valid_submkt_urls = [
            '.eia.gov', '.doe.gov', '.energy.gov', '.data.gov',
            '.energystar.gov', '.epa.gov', '.census.gov', '.pnnl.gov',
            '.lbl.gov', '.nrel.gov', 'www.sciencedirect.com', 'www.costar.com',
            'www.navigantresearch.com']
        try:
            self.consumer_price_ind = numpy.genfromtxt(
                handyfiles.cpi_data,
                names=True, delimiter=',',
                dtype=[('DATE', 'U10'), ('VALUE', '<f8')])
            # Ensure that consumer price date is in expected format
            if len(self.consumer_price_ind['DATE'][0]) != 10:
                raise ValueError("CPI date format should be YYYY-MM-DD")
        except ValueError as e:
            raise ValueError(
                f"Error reading in '{handyfiles.cpi_data}': {str(e)}") from None
        # Read in commercial equipment capacity factors
        self.cap_facts = JsonIO.load_json(handyfiles.cap_facts)
        # Read in national-level site-source, emissions, and costs data
        cost_ss_carb = JsonIO.load_json(handyfiles.ss_data)

        # Set base-case emissions/cost data to use in assessing reductions for
        # non-fuel switching microsegments under a high grid decarbonization
        # case, if desired by the user
        if handyfiles.ss_data_nonfs is not None:
            # Read in national-level site-source, emissions, and costs data
            cost_ss_carb_nonfs = JsonIO.load_json(handyfiles.ss_data_nonfs)
        else:
            cost_ss_carb_nonfs = None
        # Set national site to source conversion factors
        self.ss_conv = {
            "electricity": cost_ss_carb[
                "electricity"]["site to source conversion"]["data"],
            "natural gas": {yr: 1 for yr in self.aeo_years},
            "distillate": {yr: 1 for yr in self.aeo_years},
            "other fuel": {yr: 1 for yr in self.aeo_years}}
        # Set electric emissions intensities and prices differently
        # depending on whether EMM regions are specified (use EMM-specific
        # data) or not (use national data)
        if self.regions in ["EMM", "State"]:
            # Read in EMM- or state-specific emissions factors and price data
            cost_ss_carb_altreg = JsonIO.load_json(handyfiles.ss_data_altreg)
            # Set base-case emissions/cost data to use in assessing reductions
            # for non-fuel switching microsegments under a high grid
            # decarbonization case, if desired by the user
            if handyfiles.ss_data_altreg_nonfs is not None:
                # Read in EMM- or state-specific emissions factors and price data
                cost_ss_carb_altreg_nonfs = JsonIO.load_json(handyfiles.ss_data_altreg_nonfs)
            else:
                cost_ss_carb_altreg_nonfs = None
            # Initialize CO2 intensities based on electricity intensities by
            # EMM region or state; convert CO2 intensities from Mt/TWh site to
            # MMTon/MMBTu site to match expected multiplication by site energy
            self.carb_int = {bldg: {"electricity": {reg: {
                yr: round((cost_ss_carb_altreg["CO2 intensity of electricity"][
                    "data"][reg][yr] / 3412141.6331), 10) for
                yr in self.aeo_years} for reg in cost_ss_carb_altreg[
                    "CO2 intensity of electricity"]["data"].keys()}} for
                bldg in ["residential", "commercial"]}
            # Initialize energy costs based on electricity prices by EMM region
            # or state; convert prices from $/kWh site to $/MMBTu site to match
            # expected multiplication by site energy units
            self.ecosts = {bldg: {"electricity": {reg: {
                yr: round((cost_ss_carb_altreg["End-use electricity price"][
                    "data"][bldg][reg][yr] / 0.003412), 6) for
                yr in self.aeo_years} for reg in cost_ss_carb_altreg[
                    "End-use electricity price"]["data"][bldg].keys()}} for
                bldg in ["residential", "commercial"]}
            # Finalize base-case emissions/cost data to use in assessing
            # reductions for non-fuel switching microsegments under a high grid
            # decarbonization case, if desired by the user
            if cost_ss_carb_altreg_nonfs is not None:
                self.carb_int_nonfs = {bldg: {"electricity": {reg: {
                    yr: round((cost_ss_carb_altreg_nonfs[
                        "CO2 intensity of electricity"][
                        "data"][reg][yr] / 3412141.6331), 10) for
                    yr in self.aeo_years} for reg in cost_ss_carb_altreg_nonfs[
                        "CO2 intensity of electricity"]["data"].keys()}} for
                    bldg in ["residential", "commercial"]}
                self.ecosts_nonfs = {bldg: {"electricity": {reg: {
                    yr: round((cost_ss_carb_altreg_nonfs[
                        "End-use electricity price"][
                        "data"][bldg][reg][yr] / 0.003412), 6) for
                    yr in self.aeo_years} for reg in cost_ss_carb_altreg_nonfs[
                        "End-use electricity price"]["data"][bldg].keys()}} for
                    bldg in ["residential", "commercial"]}
            else:
                self.carb_int_nonfs, self.ecosts_nonfs = (
                    None for n in range(2))
        else:
            # Initialize CO2 intensities based on national CO2 intensities
            # for electricity; convert CO2 intensities from Mt/quad source to
            # Mt/MMBTu source to match expected multiplication by source energy
            self.carb_int = {bldg: {"electricity": {yr: cost_ss_carb[
                "electricity"]["CO2 intensity"]["data"][bldg][yr] /
                1000000000 for yr in self.aeo_years}} for bldg in [
                "residential", "commercial"]}
            # Initialize energy costs based on national electricity prices; no
            # conversion needed as the prices will be multiplied by MMBtu
            # source energy units and are already in units of $/MMBtu source
            self.ecosts = {bldg: {"electricity": {yr: cost_ss_carb[
                "electricity"]["price"]["data"][bldg][yr] for
                yr in self.aeo_years}} for bldg in [
                "residential", "commercial"]}
            # Finalize base-case emissions/cost data to use in assessing
            # reductions for non-fuel switching microsegments under a high grid
            # decarbonization case, if desired by the user
            if cost_ss_carb_nonfs is not None:
                self.carb_int_nonfs = {
                    bldg: {"electricity": {yr: cost_ss_carb_nonfs[
                        "electricity"]["CO2 intensity"]["data"][bldg][yr] /
                        1000000000 for yr in self.aeo_years}} for bldg in [
                        "residential", "commercial"]}
                self.ecosts_nonfs = {
                    bldg: {"electricity": {yr: cost_ss_carb_nonfs[
                        "electricity"]["price"]["data"][bldg][yr] for
                        yr in self.aeo_years}} for bldg in [
                        "residential", "commercial"]}
            else:
                self.carb_int_nonfs, self.ecosts_nonfs = (
                    None for n in range(2))
        # Pull non-electric CO2 intensities and energy prices and update
        # the CO2 intensity and energy cost dicts initialized above
        # accordingly; convert CO2 intensities from Mt/quad source to
        # Mt/MMBTu source to match expected multiplication by source energy;
        # price data are already in units of $/MMBtu source and do not require
        # further conversion
        carb_int_nonelec = {bldg: {fuel: {yr: (
            cost_ss_carb[fuel_map]["CO2 intensity"]["data"][
                bldg][yr] / 1000000000) for yr in self.aeo_years}
                for fuel, fuel_map in zip(
                ["natural gas", "distillate", "other fuel"],
                ["natural gas", "distillate", "propane"])
            } for bldg in ["residential", "commercial"]}
        ecosts_nonelec = {bldg: {fuel: {yr: cost_ss_carb[
            fuel_map]["price"]["data"][bldg][yr] for yr in
            self.aeo_years} for fuel, fuel_map in zip([
                "natural gas", "distillate", "other fuel"], [
                "natural gas", "distillate", "propane"])} for bldg in [
            "residential", "commercial"]}
        for bldg in ["residential", "commercial"]:
            self.carb_int[bldg].update(carb_int_nonelec[bldg])
            self.ecosts[bldg].update(ecosts_nonelec[bldg])
            # Update base-case emissions/cost data to use in
            # assessing reductions for non-fuel switching microsegments
            # under a high grid decarbonization case to reflect non-electric
            # emissions intensities/energy costs
            if self.carb_int_nonfs is not None:
                self.carb_int_nonfs[bldg].update(carb_int_nonelec[bldg])
            if self.ecosts_nonfs is not None:
                self.ecosts_nonfs[bldg].update(ecosts_nonelec[bldg])
        # Set carbon costs
        ccosts_init = cost_ss_carb["CO2 price"]["data"]
        # Multiply carbon costs by 1000000 to reflect
        # conversion from import units of $/MTon to $/MMTon
        self.ccosts = {
            yr_key: (ccosts_init[yr_key] * 1000000) for
            yr_key in self.aeo_years}
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
        # Load external data on conversion rates for HP measures
        if opts.exog_hp_rates is not False:
            self.hp_rates = JsonIO.load_json(handyfiles.hp_convert_rates)

            # Set a priori assumptions about which non-elec-HP heating/cooling
            # technologies in commercial buildings are part of an RTU config.
            # vs. not; this is necessary to choose the appropriate exogenous
            # fuel switching rates for such technologies, if applicable

            # Use RTU HP fuel switching rates for furnace and/or small electric
            # resistance + AC tech.
            self.com_RTU_fs_tech = [
                "gas_furnace", "oil_furnace", "electric_res-heat",
                "rooftop_AC", "wall-window_room_AC", "res_type_central_AC"]
            # Use non-RTU HP fuel switching rates for boiler/chiller tech.
            # and/or gas chillers/HPs
            self.com_nRTU_fs_tech = [
                "elec_boiler", "gas_eng-driven_RTHP-heat",
                "res_type_gasHP-heat", "gas_boiler", "oil_boiler",
                "scroll_chiller", "reciprocating_chiller",
                "centrifugal_chiller", "screw_chiller",
                "gas_eng-driven_RTAC", "gas_chiller", "res_type_gasHP-cool",
                "gas_eng-driven_RTHP-cool"]
        # Fugitive refrigerant emissions calculations also require
        # understanding of which commercial heating/cooling technologies fall
        # into the RTU/small commercial category vs. large commercial category
        elif opts.fugitive_emissions is not False:
            self.hp_rates = None
            self.com_RTU_fs_tech = [
                "gas_furnace", "oil_furnace", "electric_res-heat",
                "rooftop_AC", "wall-window_room_AC", "res_type_central_AC"]
            self.com_nRTU_fs_tech = [
                "elec_boiler", "gas_eng-driven_RTHP-heat",
                "res_type_gasHP-heat", "gas_boiler", "oil_boiler",
                "scroll_chiller", "reciprocating_chiller",
                "centrifugal_chiller", "screw_chiller",
                "gas_eng-driven_RTAC", "gas_chiller", "res_type_gasHP-cool",
                "gas_eng-driven_RTHP-cool"]
        else:
            self.hp_rates, self.com_RTU_fs_tech, self.com_nRTU_fs_tech = (
                None for n in range(3))
        self.resist_ht_wh_tech = [
                "elec_boiler", "electric_res-heat", "resistance heat",
                "electric WH", "elec_booster_water_heater",
                "elec_water_heater", "Solar water heater", "solar WH"]
        self.minor_hvac_tech = [
                "room AC", "wall-window_room_AC", "secondary heater",
                "secondary heater (wood)", "secondary heater (coal)",
                "secondary heater (kerosene)", "secondary heater (LPG)"]

        # Global information for anchoring linked heating/cooling stock
        # turnover and exogenous switching rate calculations

        # Technology anchor – list order assigns priority for which technology
        # in a measure's definition serves as the anchor
        self.link_htcl_tover_anchor_tech_opts = {
            "residential": {
                "heating": [
                    "resistance heat", "furnace (NG)", "boiler (NG)",
                    "furnace (distillate)", "boiler (distillate)",
                    "furnace (LPG)", "furnace (kerosene)", "stove (wood)",
                    "ASHP", "GSHP", "NGHP"],
                "cooling": ["central AC", "ASHP", "GSHP", "NGHP", "room AC"]
            },
            "commercial": {
                "heating": [
                    "elec_boiler", "electric_res-heat", "gas_boiler",
                    "gas_furnace", "oil_boiler", "oil_furnace",
                    "rooftop_ASHP-heat", "comm_GSHP-heat",
                    "gas_eng-driven_RTHP-heat", "res_type_gasHP-heat"],
                "cooling": [
                    "rooftop_AC", "rooftop_ASHP-cool",
                    "reciprocating_chiller", "scroll_chiller",
                    "centrifugal_chiller", "screw_chiller",
                    "res_type_central_AC", "comm_GSHP-cool",
                    "gas_eng-driven_RTAC", "gas_chiller",
                    "res_type_gasHP-cool", "gas_eng-driven_RTHP-cool",
                    "wall-window_room_AC"]
            }
        }

        # Load external refrigerant and supply chain methane leakage data
        # to assess fugitive emissions sources
        if opts.fugitive_emissions is not False:
            self.fug_emissions = JsonIO.load_json(handyfiles.fug_emissions_dat)
        else:
            self.fug_emissions = None

        # Set valid region names and regional output categories
        if opts.alt_regions == "AIA":
            valid_regions = [
             "AIA_CZ1", "AIA_CZ2", "AIA_CZ3", "AIA_CZ4", "AIA_CZ5"]
            regions_out = [
                ('AIA CZ1', 'AIA_CZ1'), ('AIA CZ2', 'AIA_CZ2'),
                ('AIA CZ3', 'AIA_CZ3'), ('AIA CZ4', 'AIA_CZ4'),
                ('AIA CZ5', 'AIA_CZ5')]
            self.warm_cold_regs = {
                "warm climates": ["AIA_CZ3", "AIA_CZ4", "AIA_CZ5"],
                "cold climates": ["AIA_CZ1", "AIA_CZ2"]}
            self.region_cpl_mapping = ''
            # Read in mapping for alternate performance/cost unit breakouts
            # IECC -> AIA mapping
            try:
                iecc_reg_map = numpy.genfromtxt(
                    handyfiles.iecc_reg_map,
                    names=True, delimiter='\t', dtype=(
                        ['<U25'] * 1 + ['<f8'] * len(valid_regions)))
            except ValueError as e:
                raise ValueError(
                    f"Error reading in '{handyfiles.iecc_reg_map}': {str(e)}") from None
            # BA -> AIA mapping
            try:
                ba_reg_map = numpy.genfromtxt(
                    handyfiles.ba_reg_map, names=True, delimiter='\t',
                    dtype=(['<U25'] * 1 + ['<f8'] * len(valid_regions)))
                # List of possible BA region names
                ba_list = ["Hot-Humid", "Mixed-Humid", "Very Cold", "Subarctic",
                           "Cold", "Hot-Dry", "Mixed-Dry", "Marine"]
            except ValueError as e:
                raise ValueError(
                    f"Error reading in '{handyfiles.ba_reg_map}': {str(e)}") from None
            # Store alternate breakout mapping in dict for later use
            self.alt_attr_brk_map = {
                "IECC": iecc_reg_map, "BA": ba_reg_map, "levels": str([
                    "IECC_CZ" + str(n + 1) for n in range(8)]) + " 0R " +
                str(["BA_" + n for n in ba_list])}
            # Read in state -> AIA mapping data only when methane leakage is
            # assessed
            if opts.fugitive_emissions is not False and \
                    opts.fugitive_emissions[0] in ['1', '3']:
                try:
                    self.fugitive_emissions_map = numpy.genfromtxt(
                        handyfiles.state_aia_map, names=True,
                        delimiter='\t', dtype=(['<U25'] * 1 + ['<f8'] * 51))
                except ValueError as e:
                    raise ValueError(
                        f"Error reading in '{handyfiles.state_aia_map}': {str(e)}") from None
            else:
                self.fugitive_emissions_map = None
            # HP conversion rates unsupported for AIA regional breakouts
            self.hp_rates_reg_map = None
        elif opts.alt_regions in ["EMM", "State"]:
            if opts.alt_regions == "EMM":
                valid_regions = [
                    'TRE', 'FRCC', 'MISW', 'MISC', 'MISE', 'MISS',
                    'ISNE', 'NYCW', 'NYUP', 'PJME', 'PJMW', 'PJMC',
                    'PJMD', 'SRCA', 'SRSE', 'SRCE', 'SPPS', 'SPPC',
                    'SPPN', 'SRSG', 'CANO', 'CASO', 'NWPP', 'RMRG', 'BASN']
                self.warm_cold_regs = {
                    "warm climates": [
                        "TRE", "FRCC", "MISC", "MISS", "PJMD", "SRCA",
                        "SRSE", "SRCE", "SPPS", "SPPC", "SRSG", "CANO",
                        "CASO"],
                    "cold climates": [
                        "NWPP", "BASN", "RMRG", "SPPN", "MISW", "PJMC",
                        "PJMW", "MISE", "PJME", "NYUP", "NYCW", "ISNE"]}
                self.region_cpl_mapping = ''
                try:
                    self.ash_emm_map = numpy.genfromtxt(
                        handyfiles.ash_emm_map, names=True, delimiter='\t',
                        dtype=(['<U25'] * 1 + ['<f8'] * len(valid_regions)))
                except ValueError as e:
                    raise ValueError(
                        f"Error reading in '{handyfiles.ash_emm_map}': {str(e)}") from None
                # If applicable, pull regional mapping needed to read in
                # HP conversion rate data for certain measures/microsegments
                if self.hp_rates:
                    self.hp_rates_reg_map = {
                        "midwest": [
                            "SPPN", "MISW", "SPPC", "MISC",
                            "PJMW", "PJMC", "MISE"],
                        "northeast": [
                            "PJME", "NYCW", "NYUP", "ISNE"],
                        "south": [
                            "SPPS", "TRE", "MISS", "SRCE", "PJMD",
                            "SRCA", "SRSE", "FRCC"],
                        "west": [
                            "NWPP", "BASN", "RMRG", "SRSG", "CASO", "CANO"]
                    }
                else:
                    self.hp_rates_reg_map = None
                # Read in state -> EMM mapping data only when methane leakage
                # is assessed
                if opts.fugitive_emissions is not False and \
                        opts.fugitive_emissions[0] in ['1', '3']:
                    try:
                        self.fugitive_emissions_map = numpy.genfromtxt(
                            handyfiles.state_emm_map, names=True,
                            delimiter='\t', dtype=(['<U25'] * 1 + ['<f8'] * 51))
                    except ValueError as e:
                        raise ValueError(
                            f"Error reading in '{handyfiles.state_emm_map}': {str(e)}") from None
                else:
                    self.fugitive_emissions_map = None
            else:
                # Note: for now, exclude AK and HI in valid regions b/c we lack
                # grid data needed to project forward their emissions and
                # retail rates
                valid_regions = [
                    'AL', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
                    'GA', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
                    'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
                    'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
                    'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI',
                    'WY']
                self.warm_cold_regs = {
                    "warm climates": [
                        'AL', 'AZ', 'AR', 'CA', 'DE', 'DC', 'FL', 'GA', 'KS',
                        'KY', 'LA', 'MD', 'MS', 'MO', 'NC', 'NJ', 'NM', 'NV',
                        'OK', 'SC', 'TN', 'TX', 'VA'],
                    "cold climates": [
                        'CO', 'CT', 'ID', 'IA', 'IL', 'IN', 'MA', 'ME', 'MI',
                        'MN', 'MT', 'ND', 'NE', 'NH', 'NY', 'OH', 'OR', 'PA',
                        'RI', 'SD', 'UT', 'VT', 'WA', 'WI', 'WV', 'WY']}
                self.region_cpl_mapping = {
                    "new england": ['CT', 'MA', 'ME', 'NH', 'RI', 'VT'],
                    "mid atlantic": ['NJ', 'NY', 'PA'],
                    "east north central": ['IL', 'IN', 'MI', 'OH', 'WI'],
                    "west north central": [
                        'IA', 'KS', 'MN', 'MO', 'ND', 'NE', 'SD'],
                    "south atlantic": [
                        'DC', 'DE', 'FL', 'GA', 'MD', 'NC', 'SC', 'VA', 'WV'],
                    "east south central": ['AL', 'KY', 'MS', 'TN'],
                    "west south central": ['AR', 'LA', 'OK', 'TX'],
                    "mountain": [
                        'AZ', 'CO', 'ID', 'MT', 'NM', 'NV', 'UT', 'WY'],
                    "pacific": ['AK', 'CA', 'HI', 'OR', 'WA']}
                # If applicable, pull regional mapping needed to read in
                # HP conversion rate data for certain measures/microsegments
                if self.hp_rates:
                    self.hp_rates_reg_map = {
                        "midwest": [
                            "ND", "SD", "NE", "KS", "MO", "IA", "MN", "WI",
                            "IL", "IN", "MI", "OH"],
                        "northeast": [
                            "PA", "NY", "NJ", "CT", "RI", "MA", "VT", "NH",
                            "ME"],
                        "south": [
                            "TX", "OK", "AR", "LA", "MS", "AL", "GA", "FL",
                            "SC", "NC", "TN", "KY", "WV", "VA", "DC", "MD",
                            "DE"],
                        "west": [
                            "WA", "OR", "ID", "MT", "WY", "CA", "NV", "UT",
                            "AZ", "NM", "CO", "AK", "HI"]
                    }
                else:
                    self.hp_rates_reg_map = None
            regions_out = [(x, x) for x in valid_regions]

            # Read in mapping for alternate performance/cost unit breakouts
            # AIA -> EMM or State mapping
            try:
                # Hard code number of valid states at 51 (includes DC) to avoid
                # potential issues later when indexing numpy columns by state
                if opts.alt_regions == "State":
                    len_reg = 51
                else:
                    len_reg = len(valid_regions)
                # Read in the data
                aia_altreg_map = numpy.genfromtxt(
                    handyfiles.aia_altreg_map, names=True, delimiter='\t',
                    dtype=(['<U25'] * 1 + ['<f8'] * len_reg))
            except ValueError:
                raise ValueError(
                    f"Error reading in '{str(handyfiles.aia_altreg_map)}'")
            # IECC -> EMM or State mapping
            try:
                iecc_altreg_map = numpy.genfromtxt(
                    handyfiles.iecc_reg_map, names=True, delimiter='\t',
                    dtype=(['<U25'] * 1 + ['<f8'] * len_reg))
            except ValueError as e:
                raise ValueError(
                    f"Error reading in '{handyfiles.iecc_reg_map}': {str(e)}") from None
            # BA -> EMM or State mapping
            try:
                ba_altreg_map = numpy.genfromtxt(
                    handyfiles.ba_reg_map, names=True, delimiter='\t',
                    dtype=(['<U25'] * 1 + ['<f8'] * len_reg))
                # List of possible BA region names
                ba_list = ["Hot-Humid", "Mixed-Humid", "Very Cold", "Subarctic",
                           "Cold", "Hot-Dry", "Mixed-Dry", "Marine"]
            except ValueError as e:
                raise ValueError(
                    f"Error reading in '{handyfiles.ba_reg_map}': {str(e)}") from None
            # Store alternate breakout mapping in dict for later use
            self.alt_attr_brk_map = {
                "IECC": iecc_altreg_map, "BA": ba_altreg_map,
                "AIA": aia_altreg_map,
                "levels": str([
                    "IECC_CZ" + str(n + 1) for n in range(8)]) + " 0R " + str([
                        "AIA_CZ" + str(n + 1) for n in range(5)]) + " 0R " +
                str(["BA_" + n for n in ba_list])}
        self.months = ["january", "february", "march", "april", "may", "june",
                       "july", "august", "september", "october", "november",
                       "december"]
        self.in_all_map = {
            "climate_zone": valid_regions,
            "bldg_type": {
                "residential": [
                    "single family home", "multi family home", "mobile home"],
                "commercial": [
                    "assembly", "education", "food sales", "food service",
                    "health care", "lodging", "large office", "small office",
                    "mercantile/service", "warehouse", "other",
                    "unspecified"]},
            "structure_type": ["new", "existing"],
            "fuel_type": {
                "residential": [
                    "electricity", "natural gas", "distillate", "other fuel"],
                "commercial": [
                    "electricity", "natural gas", "distillate", "other fuel"]},
            "end_use": {
                "residential": {
                    "electricity": [
                        'drying', 'other', 'water heating',
                        'cooling', 'cooking', 'computers', 'lighting',
                        'secondary heating', 'TVs', 'heating', 'refrigeration',
                        'fans and pumps', 'ceiling fan'],
                    "natural gas": [
                        'drying', 'water heating', 'cooling', 'heating',
                        'cooking', 'secondary heating', 'other'],
                    "distillate": [
                        'water heating', 'heating', 'secondary heating',
                        'other'],
                    "other fuel": [
                        'water heating', 'cooking', 'heating',
                        'secondary heating', 'other']},
                "commercial": {
                    "electricity": [
                        'ventilation', 'water heating', 'cooling',
                        'heating', 'refrigeration', 'MELs',
                        'non-PC office equipment', 'PCs', 'lighting',
                        'cooking', "unspecified"],
                    "natural gas": [
                        'cooling', 'water heating', 'cooking', 'heating',
                        'other', 'unspecified'],
                    "distillate": [
                        'water heating', 'heating', 'other', 'unspecified'],
                    "other fuel": ["unspecified"]}},
            "technology": {
                "residential": {
                    "supply": {
                        "electricity": {
                            'other': [
                                'dishwasher', 'clothes washing', 'freezers',
                                'rechargeables', 'coffee maker',
                                'dehumidifier', 'electric other',
                                'small kitchen appliances', 'microwave',
                                'smartphones', 'pool heaters', 'pool pumps',
                                'security system', 'portable electric spas',
                                'smart speakers', 'tablets', 'wine coolers'],
                            'water heating': ['solar WH', 'electric WH'],
                            'cooling': [
                                'room AC', 'ASHP', 'GSHP', 'central AC'],
                            'computers': [
                                'desktop PC', 'laptop PC', 'network equipment',
                                'monitors'],
                            'lighting': [
                                'linear fluorescent (T-8)',
                                'linear fluorescent (T-12)',
                                'reflector (LED)', 'general service (CFL)',
                                'external (high pressure sodium)',
                                'general service (incandescent)',
                                'external (CFL)',
                                'external (LED)', 'reflector (CFL)',
                                'reflector (incandescent)',
                                'general service (LED)',
                                'external (incandescent)',
                                'linear fluorescent (LED)',
                                'reflector (halogen)'],
                            'secondary heating': ['secondary heater'],
                            'TVs': [
                                'home theater and audio', 'set top box',
                                'video game consoles', 'TV',
                                'OTT streaming devices'],
                            'heating': ['GSHP', 'resistance heat', 'ASHP'],
                            'ceiling fan': [None],
                            'fans and pumps': [None],
                            'refrigeration': [None],
                            'drying': [None],
                            'cooking': [None]},
                        "natural gas": {
                            'cooling': ['NGHP'],
                            'heating': ['furnace (NG)', 'NGHP', 'boiler (NG)'],
                            'secondary heating': ['secondary heater'],
                            'drying': [None],
                            'water heating': [None],
                            'cooking': [None],
                            'other': ["other appliances"]},
                        "distillate": {
                            'heating': [
                                'boiler (distillate)', 'furnace (distillate)'],
                            'secondary heating': ['secondary heater'],
                            'water heating': [None],
                            'other': ["other appliances"]},
                        "other fuel": {
                            'heating': [
                                'furnace (kerosene)',
                                'stove (wood)', 'furnace (LPG)'],
                            'secondary heating': [
                                'secondary heater (wood)',
                                'secondary heater (coal)',
                                'secondary heater (kerosene)',
                                'secondary heater (LPG)'],
                            'cooking': [None],
                            'water heating': [None],
                            'other': ["other appliances"]}},
                    "demand": [
                        'roof', 'ground', 'windows solar',
                        'windows conduction', 'equipment gain',
                        'people gain', 'wall', 'infiltration']},
                "commercial": {
                    "supply": {
                        "electricity": {
                            'ventilation': ['VAV_Vent', 'CAV_Vent'],
                            'water heating': [
                                'HP water heater',
                                'elec_water_heater',
                                'solar water heater', 'solar_water_heater_north'],
                            'cooling': [
                                'rooftop_AC', 'scroll_chiller',
                                'res_type_central_AC', 'reciprocating_chiller',
                                'comm_GSHP-cool', 'centrifugal_chiller',
                                'rooftop_ASHP-cool', 'wall-window_room_AC',
                                'screw_chiller',
                                "pkg_terminal_AC-cool",
                                "pkg_terminal_HP-cool"],
                            'heating': [
                                'electric_res-heat', 'comm_GSHP-heat',
                                'rooftop_ASHP-heat', 'elec_boiler',
                                "pkg_terminal_HP-heat",
                                "elec_res-heater"],
                            'refrigeration': [
                                'Commercial Beverage Merchandisers',
                                'Commercial Compressor Rack Systems',
                                'Commercial Condensers',
                                'Commercial Ice Machines',
                                'Commercial Reach-In Freezers',
                                'Commercial Reach-In Refrigerators',
                                'Commercial Refrigerated Vending Machines',
                                'Commercial Supermarket Display Cases',
                                'Commercial Walk-In Freezers',
                                'Commercial Walk-In Refrigerators'],
                            'MELs': [
                                'distribution transformers',
                                'kitchen ventilation', 'security systems',
                                'lab fridges and freezers',
                                'medical imaging', 'large video boards',
                                'coffee brewers', 'non-road electric vehicles',
                                'fume hoods', 'laundry', 'elevators',
                                'escalators', 'IT equipment', 'office UPS',
                                'data center UPS', 'shredders',
                                'private branch exchanges',
                                'voice-over-IP telecom',
                                'point-of-sale systems', 'warehouse robots',
                                'televisions', 'telecom systems', 'other'
                            ],
                            'lighting': [
                                '100W A19 Incandescent',
                                '100W Equivalent A19 Halogen',
                                '100W Equivalent CFL Bare Spiral',
                                '100W Equivalent LED A Lamp',
                                'Halogen Infrared Reflector (HIR) PAR38',
                                'Halogen PAR38',
                                'LED Integrated Luminaire',
                                'LED PAR38',
                                'Mercury Vapor',
                                'Metal Halide',
                                'Sodium Vapor',
                                'T5 4xF54 HO High Bay',
                                'T5 F28',
                                'T8 F28',
                                'T8 F32',
                                'T8 F59',
                                'T8 F96'
                            ],
                            'cooking': [
                                'elec_range-combined'],
                            'PCs': [None],
                            'non-PC office equipment': [None],
                            'unspecified': [None]},
                        "natural gas": {
                            'cooling': [
                                'gas_eng-driven_RTAC', 'gas_chiller',
                                'res_type_gasHP-cool',
                                'gas_eng-driven_RTHP-cool'],
                            'water heating': [
                                'gas_water_heater', 'gas_instantaneous_water_heater'],
                            'cooking': [
                                'gas_range-combined'],
                            'heating': [
                                'gas_eng-driven_RTHP-heat',
                                'res_type_gasHP-heat', 'gas_boiler',
                                'gas_furnace'],
                            'other': [None],
                            'unspecified': [None]},
                        "distillate": {
                            'water heating': ['oil_water_heater'],
                            'heating': ['oil_boiler', 'oil_furnace'],
                            'other': [None],
                            'unspecified': [None]},
                        "other fuel": {
                            "unspecified": [None]}},
                    "demand": [
                        'roof', 'ground', 'lighting gain',
                        'windows conduction', 'equipment gain',
                        'floor', 'infiltration', 'people gain',
                        'windows solar', 'ventilation',
                        'other heat gain', 'wall']}}}
        # Find the full set of valid names for describing a measure's
        # applicable baseline that do not begin with 'all'
        mktnames_non_all = self.append_keyvals(
            self.in_all_map, keyval_list=[]) + ['supply', 'demand'] + \
            ['warm climates', 'cold climates']
        # Find the full set of valid names for describing a measure's
        # applicable baseline that do begin with 'all'
        mktnames_all_init = ["all", "all residential", "all commercial"] + \
            self.append_keyvals(self.in_all_map["end_use"], keyval_list=[])
        mktnames_all = ['all ' + x if 'all' not in x else x for
                        x in mktnames_all_init]
        self.valid_mktnames = mktnames_non_all + mktnames_all
        if opts.detail_brkout in ['1', '2', '5', '6']:
            self.out_break_czones = OrderedDict(regions_out)
        else:
            if opts.alt_regions == "EMM":
                # Map to modified version of AVERT regions
                self.out_break_czones = OrderedDict([
                    ("Northwest", ["NWPP"]),
                    ("Great Basin", ["BASN"]),
                    ("California", ["CASO", "CANO"]),
                    ("Rocky Mountains", ["RMRG"]),
                    ("Upper Midwest", ["SPPN", "MISW", "MISC"]),
                    ("Lower Midwest", ["SPPC", "SPPS"]),
                    ("Lakes/Mid-Atl.", [
                        "MISE", "PJMW", "PJMC", "PJME"]),
                    ("Texas", ["TRE"]),
                    ("Southwest", ["SRSG"]),
                    ("Southeast", ["PJMD", "SRCA", "SRSE", "FRCC",
                                   "MISS", "SRCE"]),
                    ("Northeast", ["NYCW", "NYUP", "ISNE"])])
            elif opts.alt_regions == "State":
                # Map to Census subregions
                self.out_break_czones = OrderedDict([
                    ("New England", ['CT', 'MA', 'ME', 'NH', 'RI', 'VT']),
                    ("Mid Atlantic", ['NJ', 'NY', 'PA']),
                    ("East North Central", ['IL', 'IN', 'MI', 'OH', 'WI']),
                    ("West North Central", [
                        'IA', 'KS', 'MN', 'MO', 'ND', 'NE', 'SD']),
                    ("South Atlantic", [
                        'DC', 'DE', 'FL', 'GA', 'MD', 'NC', 'SC', 'VA', 'WV']),
                    ("East South Central", ['AL', 'KY', 'MS', 'TN']),
                    ("West South Central", ['AR', 'LA', 'OK', 'TX']),
                    ("Mountain", [
                        'AZ', 'CO', 'ID', 'MT', 'NM', 'NV', 'UT', 'WY']),
                    ("Pacific", ['AK', 'CA', 'HI', 'OR', 'WA'])])
            else:
                self.out_break_czones = OrderedDict(regions_out)

        if opts.detail_brkout in ['1', '3', '5', '7']:
            # Map to more granular building type definition
            self.out_break_bldgtypes = OrderedDict([
                ('Single Family Homes', [
                    'new', 'existing', 'single family home', 'mobile home']),
                ('Multi Family Homes', [
                    'new', 'existing', 'multi family home']),
                ('Hospitals', ['new', 'existing', 'health care']),
                ('Large Offices', ['new', 'existing', 'large office']),
                ('Small/Medium Offices', ['new', 'existing', 'small office']),
                ('Retail', ['new', 'existing', 'food sales',
                            'mercantile/service']),
                ('Hospitality', [
                    'new', 'existing', 'lodging', 'food service']),
                ('Education', ['new', 'existing', 'education']),
                ('Assembly/Other', [
                    'new', 'existing', 'assembly', 'other', 'unspecified']),
                ('Warehouses', ['new', 'existing', 'warehouse'])])
        else:
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
                    'other', 'unspecified']),
                ('Commercial (Existing)', [
                    'existing', 'assembly', 'education', 'food sales',
                    'food service', 'health care', 'mercantile/service',
                    'lodging', 'large office', 'small office', 'warehouse',
                    'other', 'unspecified'])])
        self.out_break_enduses = OrderedDict([
            ('Heating (Equip.)', ["heating", "secondary heating"]),
            ('Cooling (Equip.)', ["cooling"]),
            ('Heating (Env.)', ["heating", "secondary heating"]),
            ('Cooling (Env.)', ["cooling"]),
            ('Ventilation', ["ventilation"]),
            ('Lighting', ["lighting"]),
            ('Water Heating', ["water heating"]),
            ('Refrigeration', ["refrigeration", "other"]),
            ('Cooking', ["cooking"]),
            ('Computers and Electronics', [
                "PCs", "non-PC office equipment", "TVs", "computers"]),
            ('Other', [
                "drying", "ceiling fan", "fans and pumps",
                "MELs", "other", "unspecified"])])
        self.out_break_eus_w_fsplits = [
            "Heating (Equip.)", "Cooling (Equip.)", "Heating (Env.)",
            "Cooling (Env.)", "Water Heating", "Cooking", "Other"]
        # Configure output breakouts for fuel type if user has set this option
        if opts.split_fuel is True:
            if opts.detail_brkout in ['1', '4', '6', '7']:
                # Map to more granular fuel type breakout
                self.out_break_fuels = OrderedDict([
                    ('Electric', ["electricity"]),
                    ('Natural Gas', ["natural gas"]),
                    ('Propane', ["other fuel"]),
                    ('Distillate/Other', ['distillate', 'other fuel']),
                    ('Biomass', ["other fuel"])])
            else:
                self.out_break_fuels = OrderedDict([
                    ('Electric', ["electricity"]),
                    ('Non-Electric', [
                        "natural gas", "distillate", "other fuel"])])
        else:
            self.out_break_fuels = {}
        # Use the above output categories to establish a dictionary with blank
        # values at terminal leaf nodes; this dict will eventually store
        # partitioning fractions needed to breakout the measure results
        # Determine all possible outcome category combinations
        out_levels = [
            self.out_break_czones.keys(), self.out_break_bldgtypes.keys(),
            self.out_break_enduses.keys()]
        out_levels_keys = list(itertools.product(*out_levels))
        # Create dictionary using outcome category combinations as key chains
        self.out_break_in = OrderedDict()
        for kc in out_levels_keys:
            current_level = self.out_break_in
            for ind, elem in enumerate(kc):
                # If fuel splits are desired and applicable for the current
                # end use breakout, add the fuel splits to the dict vals
                if len(self.out_break_fuels.keys()) != 0 and (
                        elem in self.out_break_eus_w_fsplits) and \
                        elem not in current_level:
                    current_level[elem] = OrderedDict(
                        [(x, OrderedDict()) for x in
                         self.out_break_fuels.keys()])
                # Otherwise, set dict vals to another empty dict
                elif elem not in current_level:
                    current_level[elem] = OrderedDict()
                current_level = current_level[elem]
        self.cconv_bybldg_units = [
            "$/ft^2 glazing", "$/ft^2 roof", "$/ft^2 wall",
            "$/ft^2 footprint", "$/ft^2 floor", "$/occupant", "$/node"]
        self.cconv_tech_mltstage_map = {
            "windows": {
                "key": ["$/ft^2 glazing"],
                "conversion stages": ["windows", "walls"]},
            "roof": {
                "key": ["$/ft^2 roof"],
                "conversion stages": ["roof", "footprint"]},
            "walls": {
                "key": ["$/ft^2 wall"],
                "conversion stages": ["walls"]},
            "footprint": {
                "key": ["$/ft^2 footprint"],
                "conversion stages": ["footprint"]}}
        self.tech_units_rmv = ["HHV"]
        # Note: EF handling for ECMs written before scout v0.5 (AEO 2019)
        self.tech_units_map = {
            "COP": {"AFUE": 1, "EER": 0.2930712},
            "EER": {"COP": 3.412},
            "AFUE": {"COP": 1}, "UEF": {"SEF": 1},
            "EF": {"UEF": 1, "SEF": 1, "CEF": 1},
            "SEF": {"UEF": 1}}
        self.sf_to_house = {}
        self.com_eqp_eus_nostk = [
            "PCs", "non-PC office equipment", "MELs", "other",
            "unspecified"]
        self.res_lts_per_home = {
            "single family home": 36,
            "multi family home": 15,
            "mobile home": 19
        }
        # Assume that missing technology choice parameters come from the
        # appliances/MELs areas; default is thus the EIA choice parameters
        # for refrigerator technologies
        self.deflt_choice = [-0.01, -0.12]

        # Set valid types of TSV feature types
        self.tsv_feature_types = ["shed", "shift", "shape"]

        # Initialize handy TSV variables if selected region setting supports
        # TSV (EMM, state)
        if opts.alt_regions in ["EMM", "State"]:
            # Set a dict that maps EMM region names to region
            # numbers as defined by EIA
            # (https://www.eia.gov/outlooks/aeo/pdf/f2.pdf); this mapping is
            # required to support both savings shape calculations and
            # TSV metrics calculations
            emm_region_names = [
                'TRE', 'FRCC', 'MISW', 'MISC', 'MISE', 'MISS',
                'ISNE', 'NYCW', 'NYUP', 'PJME', 'PJMW', 'PJMC',
                'PJMD', 'SRCA', 'SRSE', 'SRCE', 'SPPS', 'SPPC',
                'SPPN', 'SRSG', 'CANO', 'CASO', 'NWPP', 'RMRG', 'BASN']
            self.emm_name_num_map = {
                name: (ind + 1) for ind, name in enumerate(
                    emm_region_names)}
            if opts.alt_regions == "EMM":
                self.tsv_climate_regions = [
                    "2A", "2B", "3A", "3B", "3C", "4A", "4B",
                    "4C", "5A", "5B", "5C", "6A", "6B", "7"]
                self.tsv_nerc_regions = [
                    "FRCC", "MRO", "NPCC", "RFC", "SERC", "SPP", "TRE", "WECC"]
                # Set a dict that maps each ASH climate zone to an EMM region
                # in the climate zone with the most representative set of
                # min/max system load hour and peak/take system load hour
                # windows to use for that climate zone. For most climates, two
                # of these representative regions is assumed to account for
                # varying types of renewable mixes (e.g., high solar vs. low
                # solar, which yield differences in net load shapes and net
                # peak/take periods). In these cases, the terminal value is
                # formatted as a list with the EMM region number with the
                # representative load hour data stored in the first element,
                # and all other EMM regions in the climate that are covered
                # by that representative load hour data stored in the second
                # element. NOTE: the selection of representative EMM regions
                # for each ASH region is based on the plots found here:
                # https://drive.google.com/drive/folders/
                # 1JSoQb78LgooUD_uXqBOzAC7Nl7eLJZnc?usp=sharing
                self.cz_emm_map = {
                    "2A": {
                        "set 1": [2, (1, 2, 17)],
                        "set 2": [6, (6, 15)]},
                    "2B": {
                        "set 1": [20, (1, 20)]},
                    "3A": {
                        "set 1": [15, (6, 13, 14, 15, 16)],
                        "set 2": [1, (1, 17)]},
                    "3B": {
                        "set 1": [22, (21, 22)],
                        "set 2": [25, (1, 17, 20, 25)]},
                    "3C": {
                        "set 1": [21, (21, 22)]},
                    "4A": {
                        "set 1": [10, (4, 8, 10, 11, 17, 18)],
                        "set 2": [16, (6, 13, 14, 15, 16)]},
                    "4B": {
                        "set 1": [20, (1, 17, 20, 24)],
                        "set 2": [21, (21, 22)]},
                    "4C": {
                        "set 1": [23, (23,)],
                        "set 2": [21, (21,)]},
                    "5A": {
                        "set 1": [11, (3, 4, 7, 9, 10, 11, 18, 19, 24)],
                        "set 2": [5, (5, 12, 14)]},
                    "5B": {
                        "set 1": [24, (20, 23, 24, 25)],
                        "set 2": [21, (21,)]},
                    "5C": {
                        "set 1": [23, (23,)]},
                    "6A": {
                        "set 1": [3, (3, 5, 19)],
                        "set 2": [7, (7, 9, 10, 24)]},
                    "6B": {
                        "set 1": [23, (3, 19, 23, 24, 25)],
                        "set 2": [22, (21, 22)]},
                    "7": {
                        "set 1": [3, (3, 19)],
                        "set 2": [24, (7, 24, 25)]}}
                self.state_emm_map = None
            elif opts.alt_regions == "State":
                # Set a dict that maps each state to the EMM region with the
                # largest geographical overlap with that state; this is
                # necessary to calculate TSV metrics (summarized by EMM region)
                # when the user desires state-resolved outputs. See Scout
                # geography mapping file https://docs.google.com/spreadsheets/
                # d/13n4abgODUrZ5w4CY1xrvg7APvNJtNVty8sPJn2vM4yU/
                # edit?gid=1157237940#gid=1157237940, sheets
                # "EMM_State_ColSums" and "State_EMM-EMF37" for basis.
                self.state_emm_map = {
                    "AL": "SRSE", "AK": "TRE", "AZ": "SRSG", "AR": "MISS",
                    "CA": "CASO", "CO": "RMRG", "CT": "ISNE", "DE": "PJME",
                    "DC": "PJMD", "FL": "FRCC", "GA": "SRSE", "HI": "TRE",
                    "ID": "BASN", "IL": "PJMC", "IN": "MISC", "IA": "MISW",
                    "KS": "SPPC", "KY": "SRCE", "LA": "MISS", "ME": "ISNE",
                    "MD": "PJME", "MA": "ISNE", "MI": "MISE", "MN": "MISW",
                    "MS": "MISS", "MO": "MISC", "MT": "NWPP", "NE": "SPPN",
                    "NV": "BASN", "NH": "ISNE", "NJ": "PJME", "NM": "SRSG",
                    "NY": "NYCW", "NC": "SRCA", "ND": "SPPN", "OH": "PJMW",
                    "OK": "SPPS", "OR": "NWPP", "PA": "PJME", "RI": "ISNE",
                    "SC": "SRCA", "SD": "SPPN", "TN": "SRCE", "TX": "TRE",
                    "UT": "BASN", "VT": "ISNE", "VA": "PJMD", "WA": "NWPP",
                    "WV": "PJMW", "WI": "MISW", "WY": "BASN"
                }
                self.tsv_climate_regions, self.tsv_nerc_regions, \
                    self.cz_emm_map = (None for n in range(3))

            if opts.tsv_metrics is not False:
                # Develop weekend day flags
                wknd_day_flags = [0 for n in range(365)]
                current_wkdy = 1
                for d in range(365):
                    # Flag weekend day
                    if current_wkdy in [1, 7]:
                        wknd_day_flags[d] = 1
                    # Advance day of week by one unless Saturday (7), in which
                    # case day switches back to 1 (Sunday)
                    if current_wkdy <= 6:
                        current_wkdy += 1
                    else:
                        current_wkdy = 1

                # Develop lists with seasonal day of year ranges, both with and
                # without weekends

                # Summer days of year
                sum_days = list(range(152, 274))
                sum_days_wkdy = [
                    x for x in sum_days if wknd_day_flags[(x - 1)] != 1]
                sum_days_wknd = [
                    x for x in sum_days if wknd_day_flags[(x - 1)] == 1]
                # Winter days of year
                wint_days = (list(
                            range(1, 91)) + list(range(335, 366)))
                wint_days_wkdy = [
                    x for x in wint_days if wknd_day_flags[(x - 1)] != 1]
                wint_days_wknd = [
                    x for x in wint_days if wknd_day_flags[(x - 1)] == 1]
                # Intermediate days of year
                inter_days = (list(
                            range(91, 152)) + list(range(274, 335)))
                inter_days_wkdy = [
                    x for x in inter_days if wknd_day_flags[(x - 1)] != 1]
                inter_days_wknd = [
                    x for x in inter_days if wknd_day_flags[(x - 1)] == 1]

                # Set column names for a dataset that includes information on
                # max/min net system load hours and peak/take net system load
                # hour windows by season and EMM region
                peak_take_names = (
                    "Region", "Year", "SummerMaxHr", "SummerMinHr",
                    "SummerPeakStartHr", "SummerPeakEndHr",
                    "SummerTakeStartHr1", "SummerTakeEndHr1",
                    "SummerTakeStartHr2", "SummerTakeEndHr2",
                    "SummerTakeStartHr3", "SummerTakeEndHr3",
                    "WinterMaxHr", "WinterMinHr",
                    "WinterPeakStartHr", "WinterPeakEndHr",
                    "WinterTakeStartHr1", "WinterTakeEndHr1",
                    "WinterTakeStartHr2", "WinterTakeEndHr2",
                    "WinterTakeStartHr3", "WinterTakeEndHr3",
                    "InterMaxHr", "InterMinHr",
                    "InterPeakStartHr", "InterPeakEndHr",
                    "InterTakeStartHr1", "InterTakeEndHr1",
                    "InterTakeStartHr2", "InterTakeEndHr2",
                    "InterTakeStartHr3", "InterTakeEndHr3")

                # Choose the appropriate data to use in determining peak/take
                # windows (total vs. net system load under reference vs. "Low
                # Renewable Cost" supply-side AEO case)
                if opts.tsv_metrics[-2] == "1":
                    metrics_data = handyfiles.tsv_metrics_data_tot_ref
                elif opts.tsv_metrics[-2] == "2":
                    metrics_data = handyfiles.tsv_metrics_data_tot_hr
                elif opts.tsv_metrics[-2] == "3":
                    metrics_data = handyfiles.tsv_metrics_data_net_ref
                else:
                    metrics_data = handyfiles.tsv_metrics_data_net_hr

                # Import system max/min and peak/take hour load by EMM region
                sysload_dat = numpy.genfromtxt(
                    metrics_data, names=peak_take_names, delimiter=',',
                    dtype="<i4", encoding="latin1", skip_header=1)
                # Find unique set of projection years in system peak/take data
                sysload_dat_yrs = numpy.unique(sysload_dat["Year"])
                # Initialize a set of dicts that will store representative
                # system load data for the summer, winter, and intermediate
                # seasons by projection year
                sysld_sum, sysld_wint, sysld_int = ({
                    str(yr): {reg: None for reg in valid_regions} for yr in
                    sysload_dat_yrs} for n in range(3))
                # Fill in the dicts with seasonal system load data by year
                # Loop through all projection years available in the system
                # peak/take period data
                for sys_yr in sysload_dat_yrs:
                    # Convert projection year to string for dict keys
                    sys_yr_str = str(sys_yr)
                    sysload_dat_yr = sysload_dat[
                        numpy.where((sysload_dat["Year"] == sys_yr))]
                    # Loop through all climate zones
                    for reg in emm_region_names:
                        sysld_sum[sys_yr_str][reg], \
                            sysld_wint[sys_yr_str][reg], \
                            sysld_int[sys_yr_str][reg] = self.set_peak_take(
                                sysload_dat_yr, self.emm_name_num_map[reg])
                self.tsv_metrics_data = {
                    "season days": {
                        "all": {
                            "summer": sum_days,
                            "winter": wint_days,
                            "intermediate": inter_days
                        },
                        "weekdays": {
                            "summer": sum_days_wkdy,
                            "winter": wint_days_wkdy,
                            "intermediate": inter_days_wkdy

                        },
                        "weekends": {
                            "summer": sum_days_wknd,
                            "winter": wint_days_wknd,
                            "intermediate": inter_days_wknd

                        }
                    },
                    "system load hours": {
                        "summer": sysld_sum,
                        "winter": sysld_wint,
                        "intermediate": sysld_int
                    },
                    # Note: these currently correspond to the days in which the
                    # overall Scout buildings sector winter and summer
                    # baseline load peaks, given the tsv_load shape data
                    # (which are based on EULP)
                    "peak days": {
                        "summer": 183,
                        "winter": 1
                    },
                    "hourly index": list(enumerate(
                        itertools.product(range(365), range(24))))
                }
            else:
                self.tsv_metrics_data = None
            self.tsv_hourly_price, self.tsv_hourly_emissions = ({
                reg: None for reg in valid_regions
            } for n in range(2))

            self.tsv_hourly_lafs = {
                reg: {
                    "residential": {
                        bldg: {} for bldg in self.in_all_map[
                            "bldg_type"]["residential"]
                    },
                    "commercial": {
                        bldg: {} for bldg in self.in_all_map[
                            "bldg_type"]["commercial"]
                    }
                } for reg in valid_regions
            }
        else:
            self.tsv_hourly_lafs = None

        # Condition health data scenario initialization on whether user
        # has requested that public health costs be accounted for
        if opts.health_costs is True:
            # For each health data scenario, set the intended measure name
            # appendage (tuple element 1), type of efficiency to attach health
            # benefits to (element 2), and column in the data file from which
            # to retrieve these benefit values (element 3)
            self.health_scn_names = [
                ("PHC-EE (low)", "Uniform EE", "2017cents_kWh_7pct_low"),
                ("PHC-EE (high)", "Uniform EE", "2017cents_kWh_3pct_high")]
            # Set data file with public health benefits information
            self.health_scn_data = numpy.genfromtxt(
                handyfiles.health_data,
                names=("AVERT_Region", "EMM_Region", "Category",
                       "2017cents_kWh_3pct_low", "2017cents_kWh_3pct_high",
                       "2017cents_kWh_7pct_low",
                       "2017cents_kWh_7pct_high"),
                delimiter=',', dtype=(['<U25'] * 3 + ['<f8'] * 4))
        self.env_heat_ls_scrn = (
            "windows solar", "equipment gain", "people gain",
            "other heat gain")
        self.skipped_ecms = []
        self.save_shp_warn = []

    def set_peak_take(self, sysload_dat, restrict_key):
        """Fill in dicts with seasonal system load shape data.

            Args:
                sysload_dat (numpy.ndarray): System load shape data.
                restrict_key (int): EMM region to restrict net load data to.

            Returns:
                Appropriate min/max net system load hour and peak/take net
                system load hour window data for the EMM region of interest,
                stored in dicts that are distinguished by season.
        """

        # Restrict net system load data to the representative EMM region for
        # the current climate zone
        peak_take_cz = sysload_dat[numpy.where(
            (sysload_dat["Region"] == restrict_key))]
        # Set summer max load hour, min load hour, and peak/take windows
        sum_peak_take = {
            "max": peak_take_cz["SummerMaxHr"][0],
            "min": peak_take_cz["SummerMinHr"][0],
            "peak range": list(range(peak_take_cz["SummerPeakStartHr"][0],
                                     peak_take_cz["SummerPeakEndHr"][0] + 1)),
            "take range": list(range(peak_take_cz["SummerTakeStartHr1"][0],
                                     peak_take_cz["SummerTakeEndHr1"][0] + 1))}
        # Set winter max load hour, min load hour, and peak/take windows
        wint_peak_take = {
            "max": peak_take_cz["WinterMaxHr"][0],
            "min": peak_take_cz["WinterMinHr"][0],
            "peak range": list(range(peak_take_cz["WinterPeakStartHr"][0],
                                     peak_take_cz["WinterPeakEndHr"][0] + 1)),
            "take range": list(range(peak_take_cz["WinterTakeStartHr1"][0],
                                     peak_take_cz["WinterTakeEndHr1"][0] + 1))}
        # Set intermediate max load hour, min load hour, and peak/take windows
        inter_peak_take = {
            "max": peak_take_cz["InterMaxHr"][0],
            "min": peak_take_cz["InterMinHr"][0],
            "peak range": list(range(peak_take_cz["InterPeakStartHr"][0],
                                     peak_take_cz["InterPeakEndHr"][0] + 1)),
            "take range": list(range(peak_take_cz["InterTakeStartHr1"][0],
                                     peak_take_cz["InterTakeEndHr1"][0] + 1))}
        # Handle cases where seasonal low demand periods cover two or three
        # non-contiguous time segments (e.g., 2-6AM, 10AM-2PM)

        # Loop through seasonal take variable names
        for seas in ["SummerTake", "WinterTake", "InterTake"]:
            # Loop through segment number in the variable name
            for seg in ["2", "3"]:
                # Sandwich start/end hour information between season and
                # segment information in the variable name
                st_key = seas + "StartHr" + seg
                end_key = seas + "EndHr" + seg
                # Check to see whether data are present for the given season
                # and segment (use segment starting hour variable as indicator)
                if numpy.isfinite(peak_take_cz[st_key][0]):
                    # Append additional low demand periods as appropriate for
                    # the given season
                    if "Summer" in seas:
                        sum_peak_take["take range"].extend(list(
                            range(peak_take_cz[st_key][0],
                                  peak_take_cz[end_key][0])))
                    elif "Winter" in seas:
                        wint_peak_take["take range"].extend(list(
                            range(peak_take_cz[st_key][0],
                                  peak_take_cz[end_key][0])))
                    else:
                        inter_peak_take["take range"].extend(list(
                            range(peak_take_cz[st_key][0],
                                  peak_take_cz[end_key][0])))

        return sum_peak_take, wint_peak_take, inter_peak_take

    def append_keyvals(self, dict1, keyval_list):
        """Append all terminal key values in a dict to a list.

        Note:
            Values already in the list should not be appended.

        Args:
            dict1 (dict): Dictionary with terminal key values
                to append.

        Returns:
            List including all terminal key values from dict.

        Raises:
            ValueError: If terminal key values are not formatted as
                either lists or strings.
        """
        for (k, i) in dict1.items():
            if isinstance(i, dict):
                self.append_keyvals(i, keyval_list)
            elif isinstance(i, list):
                keyval_list.extend([
                    x for x in i if x not in keyval_list])
            elif isinstance(i, str) and i not in keyval_list:
                keyval_list.append(i)
            else:
                raise ValueError(
                    "Input dict terminal key values expected to be "
                    "lists or strings in the 'append_keyvals' function"
                    "for ECM '" + self.name + "'")

        return keyval_list


class UsefulInputFiles(object):
    """Class of input file paths to be used by this routine.

    Attributes:
        msegs_in (tuple): Database of baseline microsegment stock/energy.
        msegs_cpl_in (tuple): Database of baseline technology characteristics.
        iecc_reg_map (tuple): Maps IECC climates to AIA or EMM regions/states.
        ba_reg_map (tuple): Maps Building America climates to AIA/EMM/states.
        ash_emm_map (tuple): Maps ASHRAE climates to EMM regions.
        aia_altreg_map (tuple): Maps AIA climates to EMM regions or states.
        state_emm_map (tuple): Maps states to EMM regions.
        state_aia_map (tuple): Maps states to AIA regions.
        metadata (str) = Baseline metadata inc. min/max for year range.
        glob_vars (str) = Global settings from ecm_prep to use later in run
        cost_convert_in (tuple): Database of measure cost unit conversions.
        cap_facts (tuple): Database of commercial equip. capacity factors.
        cbecs_sf_byvint (tuple): Commercial sq.ft. by vintage data.
        indiv_ecms (tuple): Individual ECM JSON definitions folder.
        ecm_packages (tuple): Measure package data.
        ecm_prep (tuple): Prepared measure attributes data for use in the analysis engine.
        ecm_prep_env_cf (tuple): Prepared envelope/HVAC package measure
            attributes data with effects of HVAC removed (isolate envelope).
        ecm_prep_shapes (tuple): Prepared measure sector shapes data.
        ecm_prep_env_cf_shapes (tuple): Prepared envelope/HVAC package measure
            sector shapes data with effects of HVAC removed (isolate envelope).
        ecm_compete_data (tuple): Folder with contributing microsegment data
            needed to run measure competition in the analysis engine.
        ecm_eff_fs_splt_data (tuple): Folder with data needed to determine the
            fuel splits of efficient case results for fuel switching measures.
        run_setup (str): Names of active measures that should be run in
            the analysis engine.
        cpi_data (tuple): Historical Consumer Price Index data.
        ss_data (tuple): Site-source, emissions, and price data, national.
        ss_data_nonfs (tuple): Site-source, emissions, and price data,
            national, to assign in certain cases to non-fuel switching
            microsegments under high grid decarb case.
        ss_data_altreg (tuple): Emissions/price data, EMM- or state-resolved.
        ss_data_altreg_nonfs (tuple): Base-case emissions/price data, EMM– or
            state-resolved, to assign in certain cases to non-fuel switching
            microsegments under high grid decarb case.
        tsv_load_data (tuple): Time sensitive energy demand data, EMM- or
            state-resolved.
        tsv_cost_data (tuple): Time sensitive electricity price data, EMM- or
            state-resolved.
        tsv_carbon_data (tuple): Time sensitive average CO2 emissions data,
            EMM- or state-resolved.
        tsv_cost_data_nonfs (tuple): Time sensitive electricity price data to
            assign in certain cases to non-fuel switching microsegments under
            high grid decarb case, EMM- or state-resolved.
        tsv_carbon_data_nonfs (tuple): Time sensitive average CO2 emissions
            data to assign in certain cases to non-fuel switching microsegments
            under high grid decarb case, EMM- or state-resolved.
        tsv_shape_data (tuple): Custom hourly savings shape data.
        tsv_metrics_data_tot (tuple): Total system load data by EMM region.
        tsv_metrics_data_net (tuple): Net system load shape data by EMM region.
        health_data (tuple): EPA public health benefits data by EMM region.
        hp_convert_rates (tuple): Fuel switching conversion rates.
        fug_emissions_dat (tuple): Refrigerant and supply chain methane leakage
            data to asses fugitive emissions sources.
    """

    def __init__(self, opts):
        if opts.alt_regions == 'AIA':
            self.msegs_in = fp.STOCK_ENERGY / "mseg_res_com_cz.json"
            self.msegs_cpl_in = fp.STOCK_ENERGY / "cpl_res_com_cz.gz"
            self.iecc_reg_map = fp.CONVERT_DATA / "geo_map" / "IECC_AIA_ColSums.txt"
            self.ba_reg_map = fp.CONVERT_DATA / "geo_map" / "BA_AIA_ColSums.txt"
            self.state_aia_map = fp.CONVERT_DATA / "geo_map" / "AIA_State_RowSums.txt"
            self.tsv_load_data = None
        elif opts.alt_regions == 'EMM':
            self.msegs_in = fp.STOCK_ENERGY / "mseg_res_com_emm.gz"
            self.msegs_cpl_in = fp.STOCK_ENERGY / "cpl_res_com_emm.gz"
            self.ash_emm_map = fp.CONVERT_DATA / "geo_map" / "ASH_EMM_ColSums.txt"
            self.aia_altreg_map = fp.CONVERT_DATA / "geo_map" / "AIA_EMM_ColSums.txt"
            self.iecc_reg_map = fp.CONVERT_DATA / "geo_map" / "IECC_EMM_ColSums.txt"
            self.ba_reg_map = fp.CONVERT_DATA / "geo_map" / "BA_EMM_ColSums.txt"
            self.state_emm_map = fp.CONVERT_DATA / "geo_map" / "EMM_State_RowSums.txt"
            self.tsv_load_data = fp.TSV_DATA / "tsv_load_EMM.gz"
        elif opts.alt_regions == 'State':
            self.msegs_in = fp.STOCK_ENERGY / "mseg_res_com_state.gz"
            self.msegs_cpl_in = fp.STOCK_ENERGY / "cpl_res_com_cdiv.gz"
            self.aia_altreg_map = fp.CONVERT_DATA / "geo_map" / "AIA_State_ColSums.txt"
            self.iecc_reg_map = fp.CONVERT_DATA / "geo_map" / "IECC_State_ColSums.txt"
            self.ba_reg_map = fp.CONVERT_DATA / "geo_map" / "BA_State_ColSums.txt"
            self.tsv_load_data = fp.TSV_DATA / "tsv_load_State.gz"
        else:
            raise ValueError(
                "Unsupported regional breakout (" + opts.alt_regions + ")")

        self.set_decarb_grid_vars(opts)
        self.metadata = fp.METADATA_PATH
        self.glob_vars = fp.GENERATED / "glob_run_vars.json"
        self.cost_convert_in = fp.CONVERT_DATA / "ecm_cost_convert.json"
        self.cap_facts = fp.CONVERT_DATA / "cap_facts.json"
        self.cbecs_sf_byvint = fp.CONVERT_DATA / "cbecs_sf_byvintage.json"
        self.indiv_ecms = fp.ECM_DEF
        self.ecm_packages = fp.ECM_DEF / "package_ecms.json"
        self.ecm_prep = fp.GENERATED / "ecm_prep.json"
        self.ecm_prep_env_cf = fp.GENERATED / "ecm_prep_env_cf.json"
        self.ecm_prep_shapes = fp.GENERATED / "ecm_prep_shapes.json"
        self.ecm_prep_env_cf_shapes = fp.GENERATED / "ecm_prep_env_cf_shapes.json"
        self.ecm_compete_data = fp.ECM_COMP
        self.ecm_eff_fs_splt_data = fp.EFF_FS_SPLIT
        self.run_setup = fp.GENERATED / "run_setup.json"
        self.cpi_data = fp.CONVERT_DATA / "cpi.csv"
        self.tsv_shape_data = (
            fp.ECM_DEF / "energyplus_data" / "savings_shapes")
        self.tsv_metrics_data_tot_ref = fp.TSV_DATA / "tsv_hrs_tot_ref.csv"
        self.tsv_metrics_data_net_ref = fp.TSV_DATA / "tsv_hrs_net_ref.csv"
        self.tsv_metrics_data_tot_hr = fp.TSV_DATA / "tsv_hrs_tot_hr.csv"
        self.tsv_metrics_data_net_hr = fp.TSV_DATA / "tsv_hrs_net_hr.csv"
        self.health_data = fp.CONVERT_DATA / "epa_costs.csv"
        self.hp_convert_rates = fp.CONVERT_DATA / "hp_convert_rates.json"
        self.fug_emissions_dat = fp.CONVERT_DATA / "fugitive_emissions_convert.json"

    def set_decarb_grid_vars(self, opts: argparse.NameSpace):  # noqa: F821
        """Assign instance variables related to grid decarbonization which are dependent on the
            alt_regions, alt_ref_carb, grid_decarb_level, and grid_assessment_timing arguments.

        Args:
            opts (argparse.NameSpace): argparse object containing the argument attributes
        """

        def get_suffix(arg):
            """Return a suffix derived from a user-supplied argument string to append to filepath
                variables; if argument is None, return an empty string.
            """
            if arg is None:
                return ''
            else:
                return f"-{arg}"
        alt_ref_carb_suffix = get_suffix(opts.alt_ref_carb)
        grid_decarb_level_suffix = get_suffix(opts.grid_decarb_level)
        # Toggle EMM emissions and price data based on whether or not a grid decarbonization
        # scenario is used
        if opts.alt_regions in ['EMM', "State"]:
            emission_var_map = {}  # Map UsefulInputFiles instance vars to filenames suffixes
            if opts.grid_decarb_level:
                # Set grid decarbonization case
                emission_var_map["ss_data_altreg"] = grid_decarb_level_suffix
            else:
                # Set baseline emissions factors
                emission_var_map["ss_data_altreg"] = alt_ref_carb_suffix
                self.ss_data_altreg_nonfs = None
            if opts.grid_assessment_timing and opts.grid_assessment_timing == "before":
                # Set emissions/cost reductions for non-fuel switching measures before grid
                # decarbonization
                emission_var_map["ss_data_altreg_nonfs"] = alt_ref_carb_suffix
            elif (not opts.grid_decarb or
                    (opts.grid_assessment_timing and opts.grid_assessment_timing == "after")):
                # Set emissions/cost reductions for non-fuel switching measures after grid
                # decarbonization
                self.ss_data_altreg_nonfs = None
            # Set filepaths for EMM region emissions and prices
            for var, filesuffix in emission_var_map.items():
                if opts.alt_regions == "EMM":
                    filepath = fp.CONVERT_DATA / f"emm_region_emissions_prices{filesuffix}.json"
                else:
                    filepath = fp.CONVERT_DATA / f"state_emissions_prices{filesuffix}.json"
                setattr(self, var, filepath)

        # Set site-source conversions and TSV files for grid decarbonization case
        if opts.grid_decarb:
            self.ss_data = (fp.CONVERT_DATA /
                            f"site_source_co2_conversions{grid_decarb_level_suffix}.json")
            # Update tsv data file suffixes for DECARB levels
            if "DECARB" in grid_decarb_level_suffix:
                grid_decarb_level_suffix = {
                    "-DECARB-mid": "-95by2050",
                    "-DECARB-high": "-100by2035"}[grid_decarb_level_suffix]
            self.tsv_cost_data = (
                fp.TSV_DATA /
                f"tsv_cost-{opts.alt_regions.lower()}-{grid_decarb_level_suffix}.json")
            self.tsv_carbon_data = (
                fp.TSV_DATA /
                f"tsv_carbon-{opts.alt_regions.lower()}-{grid_decarb_level_suffix}.json")

        # Set site-source conversions and TSV files for non-fuel switching measures
        # before grid decarbonization
        if opts.grid_assessment_timing and opts.grid_assessment_timing == "before":
            self.ss_data_nonfs = (fp.CONVERT_DATA /
                                  f"site_source_co2_conversions{alt_ref_carb_suffix}.json")
            self.tsv_cost_data_nonfs = (fp.TSV_DATA /
                                        f"tsv_cost-{opts.alt_regions.lower()}-MidCase.json")
            self.tsv_carbon_data_nonfs = (fp.TSV_DATA /
                                          f"tsv_carbon-{opts.alt_regions.lower()}-MidCase.json")
        # Set site-source conversions and TSV files for non-fuel switching measures
        # after grid decarbonization
        elif (not opts.grid_decarb or
                (opts.grid_assessment_timing and opts.grid_assessment_timing == "after")):
            self.ss_data_nonfs, self.tsv_cost_data_nonfs, \
                self.tsv_carbon_data_nonfs = (None for n in range(3))

        # Set site-source conversions and TSV files for captured energy method
        if opts.captured_energy:
            self.ss_data = fp.CONVERT_DATA / "site_source_co2_conversions-ce.json"
        elif not opts.grid_decarb:
            self.ss_data = (fp.CONVERT_DATA /
                            f"site_source_co2_conversions{alt_ref_carb_suffix}.json")
            self.tsv_cost_data = fp.TSV_DATA / f"tsv_cost-{opts.alt_regions.lower()}-MidCase.json"
            self.tsv_carbon_data = (fp.TSV_DATA /
                                    f"tsv_carbon-{opts.alt_regions.lower()}-MidCase.json")
            self.ss_data_nonfs, self.tsv_cost_data_nonfs, \
                self.tsv_carbon_data_nonfs = (None for n in range(3))
