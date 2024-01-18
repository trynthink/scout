from __future__ import annotations
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import warnings
from scout.config import Config


def ecm_args(args: list) -> argparse.NameSpace:  # noqa: F821
    """Parse arguments for ecm_prep.py

    Args:
        args (list): ecm_prep.py input arguments
    """

    # Retrieve config file and CLI arguments
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter,
                            epilog="For more detail please read: "
                            "https://scout-bto.readthedocs.io/en/latest/tutorials.html"
                            "#tutorial-2-preparing-ecms-for-analysis")
    config = Config(parser, "ecm_prep", args)
    opts = config.parse_args()
    opts = translate_inputs(opts)  # Translate for use downstream

    return opts


def translate_inputs(opts: argparse.NameSpace) -> argparse.NameSpace:  # noqa: F821
    """Process args and translate them for use in ecm_prep.py

    Args:
        opts (argparse.NameSpace): object in which to store user responses

    Returns:
        argparse.NameSpace: opts variable with user inputs added
    """

    # Set adoption scenario restrictions
    if opts.adopt_scn_restrict:
        opts.adopt_scn_restrict = [opts.adopt_scn_restrict]
    else:
        opts.adopt_scn_restrict = ['Technical potential', 'Max adoption potential']

    # Screen for cases where user desires time-sensitive valuation metrics
    # or hourly sector-level load shapes but EMM regions are not used (such
    # options require baseline data to be resolved by EMM region)
    if not opts.tsv_type:
        opts.tsv_metrics = False
    if not opts.alt_regions:
        opts.alt_regions = False
    if (opts.alt_regions != "EMM") and any([
            x is not False for x in [opts.tsv_metrics, opts.sect_shapes]]):
        opts.alt_regions = "EMM"
        # Craft custom warning message based on the option provided
        if all([x is not False for x in [opts.tsv_metrics, opts.sect_shapes]]):
            warn_text = "tsv metrics and sector-level 8760 savings shapes"
        elif opts.tsv_metrics is not False:
            warn_text = "tsv metrics"
        else:
            warn_text = "sector-level 8760 load shapes"
        warnings.warn(
            "WARNING: Analysis regions were set to EMM to allow " +
            warn_text + ": ensure that ECM data reflect these EMM regions "
            "(and not the default AIA regions)")

    # Set fugitive emissions
    if opts.fugitive_emissions:
        input_var = [0, None]
        for emission in opts.fugitive_emissions:
            if emission == "methane":
                input_var[0] = 1
            elif emission == "typical refrigerant":
                input_var[1] = 1
            elif emission == "low-gwp refrigerant":
                input_var[1] = 2
        opts.fugitive_emissions = input_var
    else:
        opts.fugitive_emissions = False

    # Early retrofit settings from the default
    input_var = ['1', None, None]
    if opts.retrofit_type == "constant":
        input_var[0] = '2'
    elif opts.retrofit_type == "increasing":
        input_var[0] = '3'
        input_var[1] = opts.retrofit_multiplier
        input_var[2] = opts.retrofit_mult_year
    opts.retro_set = input_var

    # Set exogenous HP rates scenario and retrofit HP behavior
    input_var = [0, 0]
    if opts.exog_hp_rate_scenario:
        input_var[0] = opts.exog_hp_rate_scenario

        # Retrofit HP switching
        if opts.retro_set[0] != '1':
            if opts.switch_all_retrofit_hp:
                input_var[1] = "1"
            else:
                input_var[1] = "2"
        opts.exog_hp_rates = input_var

        # Ensure that if HP conversion data are to be applied, EMM regional
        # breakouts are set (HP conversion data use this resolution)
        if (opts.alt_regions not in ["EMM", "State"]):
            opts.alt_regions = "EMM"
            warnings.warn(
                "WARNING: Analysis regions were set to EMM to allow HP "
                "conversion rates: ensure that ECM data reflect these EMM "
                "regions or states (and not the default AIA regions)")
    else:
        opts.exog_hp_rates = False

    # Set grid decarbonization scenario and how electricity emissions and
    # cost factors should be handled
    if opts.grid_decarb_level and opts.grid_assesment_timing:
        input_var = [0, 0]
        input_var[0] = {"full": "1", "0.8": "2:"}[opts.grid_decarb_level]
        input_var[1] = {"before": "1", "after": "2"}[opts.grid_assesment_timing]
        opts.grid_decarb = input_var
        # Ensure that if alternate grid decarbonization scenario to be used,
        # EMM regional breakouts are set (grid decarb data use this resolution)
        if (opts.alt_regions in ["State"]):
            opts.alt_regions = "EMM"
            warnings.warn(
                "WARNING: Analysis regions were set to EMM to ensure "
                "ECM data reflect EMM regions to match alternative grid "
                "decarbonization scenario geographical breakdown")
        # Ensure that if alternate grid decarbonization scenario to be used,
        # EMM regional breakouts are set (grid decarb data use this resolution)
        if opts.captured_energy is True:
            opts.captured_energy = False
            warnings.warn(
                "WARNING: Site-source conversion method was set to use the "
                "fossil fuel equivalency method because captured energy "
                "site-source conversion factors not compatible with alternate "
                "grid decarbonization scenario")
    else:
        opts.grid_decarb = False

    # Set time-sensitive efficiency values
    if opts.tsv_average_days and (opts.tsv_power_agg != "average" and opts.tsv_type == "power"):
        opts.tsv_average_days = None
        warnings.warn(
            "WARNING: argument tsv_average_days was provided but is not applicable,"
            " argument will be ignored")
    output_type = {"energy": "1", "power": "2"}.get(opts.tsv_type, None)
    hours = {"all": "1", "peak": "2", "low": "3"}.get(opts.tsv_daily_hr_restrict)
    sys_shape = {"total reference": "1",
                 "total high renewables": "2",
                 "net renewable reference": "3",
                 "net renewable high renewables": "4"}.get(opts.tsv_sys_shape_case, "0")
    season = {"summer": "1", "winter": "2", "intermediate": "3"}.get(opts.tsv_season)
    if opts.tsv_type == "energy":
        calc_type = {"sum": "1", "average": "2"}[opts.tsv_energy_agg]
    elif opts.tsv_type == "power":
        calc_type = {"peak": "1", "average": "2"}[opts.tsv_power_agg]
    day_type = {"all": "1", "weekdays": "2", "weekends": "3"}.get(opts.tsv_average_days, "0")
    if output_type is not None:
        opts.tsv_metrics = [output_type, hours, season, calc_type, sys_shape, day_type]
    else:
        opts.tsv_metrics = False

    # Set detailed breakout options
    if opts.detail_brkout:
        input_var_dict = {
            ("buildings", "fuel types", "regions"): "1",
            ("regions",): "2",
            ("buildings",): "3",
            ("fuel types",): "4",
            ("buildings", "regions"): "5",
            ("fuel types", "regions"): "6",
            ("buildings", "fuel types"): "7",
        }
        opts.detail_brkout.sort()
        opts.detail_brkout = tuple(opts.detail_brkout)
        opts.detail_brkout = input_var_dict.get(opts.detail_brkout)
    else:
        opts.detail_brkout = False

    # Ensure that if public cost health data are to be applied, EMM regional
    # breakouts are set (health data use this resolution)
    if opts.health_costs is True and opts.alt_regions != "EMM":
        opts.alt_regions = "EMM"
        warnings.warn(
            "WARNING: Analysis regions were set to EMM to allow public health "
            "cost adders: ensure that ECM data reflect these EMM regions "
            "(and not the default AIA regions)")

    # Set inclusion of HVAC-only measures in measure competition
    opts.pkg_env_costs = {"include HVAC": "1", "exclude HVAC": "2"}.get(opts.pkg_env_costs, False)

    return opts
