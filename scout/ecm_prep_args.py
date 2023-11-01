from __future__ import annotations
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
import warnings
from scout.config import Config


def ecm_args(args: list) -> argparse.NameSpace:  # noqa: F821
    """Parse arguments for ecm_prep.py

    Args:
        args (list): ecm_prep.py input arguments
    """

    # Handle optional user-specified execution arguments
    parser = ArgumentParser(formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        "-y", "--yaml",
        type=str,
        help=("Path to YAML configuration file, arguments in this file will take priority over "
              "arguments passed via the CLI")
        )

    # Translate config schema to parser args
    config = Config(parser, "ecm_prep")
    opts = parser.parse_args()

    # Update args with yml config data
    if opts.yaml:
        config_opts = config.get_args(opts.yaml)
        opts.__dict__.update(config_opts)
    opts = fill_user_inputs(opts)

    return opts


def fill_user_inputs(opts: argparse.NameSpace) -> argparse.NameSpace:  # noqa: F821
    """Request additional user inputs through command line prompts and store them

    Args:
        opts (argparse.NameSpace): object in which to store user responses

    Returns:
        argparse.NameSpace: opts variable with user inputs added
    """

    # If a user wants to restrict to one adoption scenario, prompt the user to
    # select that scenario
    if opts.adopt_scn_restrict is True:
        input_var = 0
        # Determine the restricted adoption scheme to use (max adoption (1) vs.
        # technical potential (2))
        while input_var not in ['1', '2']:
            input_var = input(
                "\nEnter 1 to restrict to a Max Adoption Potential adoption "
                "scenario only,\nor 2 to restrict to a Technical Potential "
                "adoption scenario only: ")
            if input_var not in ['1', '2', '3']:
                print('Please try again. Enter either 1 or 2. '
                      'Use ctrl-c to exit.')
        if input_var == '1':
            opts.adopt_scn_restrict = ["Max adoption potential"]
        elif input_var == '2':
            opts.adopt_scn_restrict = ["Technical potential"]

    # If a user has specified the use of an alternate regional breakout
    # than the AIA climate zones, prompt the user to directly select that
    # alternate regional breakout (NEMS EMM or State)
    if opts.alt_regions and not opts.alt_regions_option:
        input_var = 0
        # Determine the regional breakdown to use (NEMS EMM (1) vs. State (2)
        # vs. AIA (3))
        while input_var not in ['1', '2', '3']:
            input_var = input(
                "\nEnter 1 to use an EIA NEMS Electricity Market Module (EMM) "
                "geographical breakdown,\n2 to use a state geographical "
                "breakdown,\nor 3 to use an AIA climate zone"
                " geographical breakdown: ")
            if input_var not in ['1', '2', '3']:
                print('Please try again. Enter either 1, 2, or 3. '
                      'Use ctrl-c to exit.')
        if input_var == '1':
            opts.alt_regions = "EMM"
        elif input_var == '2':
            opts.alt_regions = "State"
        else:
            opts.alt_regions = "AIA"
    elif opts.alt_regions_option:
        opts.alt_regions = opts.alt_regions_option

    # Screen for cases where user desires time-sensitive valuation metrics
    # or hourly sector-level load shapes but EMM regions are not used (such
    # options require baseline data to be resolved by EMM region)
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

    # If accounting for fugitive emissions is to be applied, gather further
    # information about which fugitive emissions sources should be included and
    # whether to use typical refrigerants (including representation of expected
    # phase-out years) or user-defined low-GWP refrigerants, as applicable
    if opts and opts.fugitive_emissions is True:
        input_var = [0, None]
        # Determine which fugitive emissions setting to use
        while input_var[0] not in ['1', '2', '3']:
            input_var[0] = input(
                "\nChoose which fugitive emissions sources to account for \n"
                "(1 = assess supply chain methane leakage only, \n"
                "2 = assess refrigerant leakage only, \n"
                "3 = assess both refrigerant leakage and "
                "supply chain methane leakage): ")
            if input_var[0] not in ['1', '2', '3']:
                print('Please try again. Enter either 1, 2, or 3. '
                      'Use ctrl-c to exit.')
        # In cases where refrigerant emissions are being assessed,
        # determine assumptions about typical vs. low-GWP refrigerants
        if input_var[0] != '1':
            while input_var[1] not in ['1', '2']:
                input_var[1] = input(
                    "\nEnter 1 to assume measures use typical refrigerants, "
                    "including representation of their phase-out years,\nor 2 "
                    "to assume measures use low-GWP refrigerants: ")
                if input_var[1] not in ['1', '2']:
                    print('Please try again. Enter either 1 or 2. '
                          'Use ctrl-c to exit.')
        opts.fugitive_emissions = input_var

    # If the user wishes to modify early retrofit settings from the default
    # (zero), gather further information about which set of assumptions to use
    if opts.retro_set is True:
        # Initialize list that stores user early retrofit settings
        input_var = [None, None, None]
        # Determine the early retrofit settings to use
        while input_var[0] not in ['1', '2', '3']:
            input_var[0] = input(
                "\nEnter 1 to assume no early retrofits,"
                "\n2 to assume component-based early retrofit rates that do "
                "not change over time, or"
                "\n3 to assume component-based early retrofit rates that "
                "increase over time: ")
            if input_var[0] not in ['1', '2', '3']:
                print('Please try again. Enter either 1, 2, or 3. '
                      'Use ctrl-c to exit.')
        # If user desired non-zero early retrofits that progressively increase
        # over time, gather further information about that assumed increase
        if input_var[0] == '3':
            # Initialize year by which a rate multiplier is achieved
            mult_yr = ""
            # Gather an assumed retrofit rate multiplier and the year by
            # which that multiplier is achieved
            while len(mult_yr) == 0 or " " not in mult_yr:
                mult_yr = input(
                    "\nEnter the factor by which early retrofit rates should "
                    "be multiplied along with the year by which this "
                    "multiplier is achieved, separated by a space: ")
                if len(mult_yr) == 0 or " " not in mult_yr:
                    print('Please try again. Enter two integers separated by '
                          'a space. Use ctrl-c to exit.')
                else:
                    # Convert user input to a list of integers
                    mult_yr_list = list(map(int, mult_yr.split()))
                    # Reset 2nd and 3rd element of list initialized above to
                    # the rate/year information provided by the user
                    input_var[1] = mult_yr_list[0]
                    input_var[2] = mult_yr_list[1]
        opts.retro_set = input_var

    # If exogenous HP rates are specified, gather further information about
    # which exogenous HP rate scenario should be used and how these rates
    # should be applied to retrofit decisions
    if opts.exog_hp_rates is True:
        input_var = [0, 0]
        # Determine which fuel switching scenario to use
        while input_var[0] not in ['1', '2', '3', '4']:
            input_var[0] = input(
                "\nChoose the Guidehouse E3HP conversion scenario to use \n"
                "(1 = conservative, 2 = optimistic, 3 = aggressive, 4 = most "
                "aggressive): ")
            if input_var[0] not in ['1', '2', '3', '4']:
                print('Please try again. Enter either 1, 2, 3, or 4. '
                      'Use ctrl-c to exit.')
        # Convert the user scenario choice to a scenario name in the input file
        scn_names = [
            "conservative", "optimistic", "aggressive", "most aggressive"]
        input_var[0] = scn_names[int(input_var[0])-1]
        # Determine assumptions about early retrofits and HP switching; only
        # prompt for this information if early retrofits are non-zero
        if (opts.retro_set is not False and opts.retro_set[0] != '1'):
            while input_var[1] not in ['1', '2']:
                input_var[1] = input(
                    "\nEnter 1 to assume that all retrofits convert to heat "
                    "pumps \nor 2 to assume that retrofits are subject to the "
                    "same external heat pump conversion rates assumed for new/"
                    "replacement decisions: ")
                if input_var[1] not in ['1', '2']:
                    print('Please try again. Enter either 1 or 2. '
                          'Use ctrl-c to exit.')
        else:
            input_var[1] = '2'
        opts.exog_hp_rates = input_var
        # Ensure that if HP conversion data are to be applied, EMM regional
        # breakouts are set (HP conversion data use this resolution)
        if (opts.alt_regions not in ["EMM", "State"]):
            opts.alt_regions = "EMM"
            warnings.warn(
                "WARNING: Analysis regions were set to EMM to allow HP "
                "conversion rates: ensure that ECM data reflect these EMM "
                "regions or states (and not the default AIA regions)")

    # If alternate grid decarbonization specified, gather further info. about
    # which grid decarbonization scenario should be used, how electricity
    # emissions and cost factors should be handled, and ensure State regional
    # breakouts and/or captured energy method are not used
    if opts.grid_decarb is True:
        input_var = [0, 0]
        # Find which grid decarbonization scenario should be used
        while input_var[0] not in ['1', '2']:
            input_var[0] = input(
                "\nEnter 1 to assume full grid decarbonization by 2035 \n"
                "or 2 to assume that grid emissions are reduced 80% from "
                "current levels by 2050: ")
            if input_var[0] not in ['1', '2']:
                print('Please try again. Enter either 1 or 2. '
                      'Use ctrl-c to exit.')
        # Find how emissions/cost factors should be handled
        while input_var[1] not in ['1', '2']:
            input_var[1] = input(
                "\nEnter 1 to assess avoided emissions and costs "
                "from non-fuel switching measures BEFORE additional grid "
                "decarbonization \nor 2 to assess avoided emissions and "
                "costs from non-fuel switching measures AFTER "
                "additional grid decarbonization: ")
            if input_var[1] not in ['1', '2']:
                print('Please try again. Enter either 1 or 2. '
                      'Use ctrl-c to exit.')
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

    # If a user wishes to change the outputs to metrics relevant for
    # time-sensitive efficiency valuation, prompt them for information needed
    # to reach the desired metric type
    if opts.tsv_metrics is True:
        # Determine the desired output type (change in energy, power)
        output_type = input(
            "\nEnter the type of time-sensitive metric desired "
            "(1 = change in energy (e.g., multiple hour GWh), "
            "2 = change in power (e.g., single hour GW)): ")

        # Determine the hourly range to restrict results to (24h, peak, take)
        hours = input(
            "Enter the daily hour range to restrict to (1 = all hours, "
            "2 = peak demand period hours, 3 = low demand period hours): ")

        # If peak/take hours are chosen, determine whether total or net
        # system shapes should be used to determine the hour ranges
        if hours == '2' or hours == '3':
            sys_shape = input(
                "Enter the basis for determining peak or low demand hour "
                "ranges: 1 = total system load (reference case), 2 = total "
                "system load (high renewables case), 3 = total system load "
                "net renewables (reference case), 4 = total system load "
                "net renewables (high renewables case): "
            )
        else:
            sys_shape = '0'

        # Determine the season to restrict results to (summer, winter,
        # intermediate)
        season = input(
            "Enter the desired season of focus (1 = summer, "
            "2 = winter, 3 = intermediate): ")

        # Determine desired calculations (dependent on output type) for given
        # flexibility mode, output type, and temporal boundaries

        # Energy output case (multiple hours)
        if output_type == '1':
            # Sum/average energy change across all hours
            if hours == '1':
                calc_type = input(
                    "Enter calculation type (1 = sum across all "
                    "hours, 2 = daily average): ")
            # Sum/average energy change across peak hours
            elif hours == '2':
                calc_type = input(
                    "Enter calculation type (1 = sum across peak "
                    "hours, 2 = daily peak period average): ")
            # Sum/average energy change across take hours
            elif hours == '3':
                calc_type = input(
                    "Enter calculation type (1 = sum across low demand "
                    "hours, 2 = daily low demand period average): ")
        # Power output case (single hour)
        else:
            # Max/average power change across all hours
            if hours == '1':
                calc_type = input(
                    "Enter calculation type (1 = peak day maximum, "
                    "2 = daily hourly average): ")
            # Max/average power change across peak hours
            elif hours == '2':
                calc_type = input(
                    "Enter calculation type (1 = peak day, peak period "
                    "maximum, 2 = daily peak period hourly average): ")
            # Max/average power change across take hours
            elif hours == '3':
                calc_type = input(
                    "Enter calculation type (1 = peak day, low demand period "
                    "maximum, 2 = daily low demand period hourly average): ")
        # Determine the day type to average over (if needed)
        if output_type == '1' or calc_type == '2':
            day_type = input(
                "Enter day type to calculate across (1 = all days, "
                "2 = weekdays, 3 = weekends): ")
        else:
            day_type = "0"

        # Summarize user TSV metric settings in a single dict for further use
        opts.tsv_metrics = [
            output_type, hours, season, calc_type, sys_shape, day_type]
    else:
        opts.tsv_metrics = False

    if opts.detail_brkout is True and opts.alt_regions is not False:
        # Condition detailed breakout options on whether or not user has
        # chosen fuel splits
        if opts.split_fuel is True:
            txt = (
                "\nEnter 1 to report detailed breakouts for regions, "
                "building types, and fuel types,\n2 to report detailed "
                "breakouts for regions only,\n3 to report detailed breakouts "
                "for building types only,\n4 to report detailed breakouts "
                "for fuel types only,\n5 to report detailed breakouts "
                "for regions and building types,\n6 to report detailed "
                "breakouts for regions and fuel types, or\n7 to report "
                "detailed breakouts for building types and fuel types: ")
            input_var = 0
            # Determine the detailed breakout settings to use
            while input_var not in ['1', '2', '3', '4', '5', '6', '7']:
                input_var = input(txt)
                if input_var not in ['1', '2', '3', '4', '5', '6', '7']:
                    print('Please try again. Enter an integer between 1 and '
                          '7. Use ctrl-c to exit.')
        else:
            txt = (
                "\nEnter 1 to report detailed breakouts for regions "
                "and building types,\n2 to report detailed breakouts for "
                "regions only, or\n3 to report detailed breakouts "
                "for building types only: ")
            input_var = 0
            # Determine the detailed breakout settings to use
            while input_var not in ['1', '2', '3']:
                input_var = input(txt)
                if input_var not in ['1', '2', '3']:
                    print('Please try again. Enter either 1, 2, or 3. '
                          'Use ctrl-c to exit.')
        opts.detail_brkout = input_var
    elif opts.detail_brkout is True:
        if opts.split_fuel is True:
            input_var = 0
            # Determine the detailed breakout settings to use
            while input_var not in ['1', '2', '3']:
                input_var = input(
                    "\nEnter 1 to report detailed breakouts for building "
                    "types and fuel types,\n2 to report detailed breakouts "
                    "for building types only, or\n3 to report detailed "
                    "breakouts for fuel types only: ")
                if input_var not in ['1', '2', '3']:
                    print('Please try again. Enter either 1, 2, or 3. '
                          'Use ctrl-c to exit.')
            # Ensure that building and fuel-type only selections map to those
            # used in the 'alt_regions' case above to simplify later use
            if input_var == '2':
                opts.detail_brkout = '3'
            elif input_var == '3':
                opts.detail_brkout = '4'
            else:
                opts.detail_brkout = input_var
        else:
            # If no fuel splits, set detailed breakouts for buildings only
            # (mapping to selections used in 'alt_regions' case)
            opts.detail_brkout = '3'

    # Ensure that if public cost health data are to be applied, EMM regional
    # breakouts are set (health data use this resolution)
    if opts.health_costs is True and opts.alt_regions != "EMM":
        opts.alt_regions = "EMM"
        warnings.warn(
            "WARNING: Analysis regions were set to EMM to allow public health "
            "cost adders: ensure that ECM data reflect these EMM regions "
            "(and not the default AIA regions)")

    # Given inclusion of envelope costs in envelope/HVAC packages, prompt
    # user to select whether HVAC-only measure data should be written out
    # for inclusion in subsequent measure competition, or not
    if opts.pkg_env_costs is True:
        input_var = 0
        while input_var not in ['1', '2']:
            input_var = input(
                "\nEnter 1 to prepare HVAC-only versions of all HVAC/envelope "
                "packages for subsequent measure competition,\nor 2 to "
                "exclude these HVAC-only measures from subsequent measure "
                "competition: ")
            if input_var not in ['1', '2']:
                print('Please try again. Enter either 1 or 2. '
                      'Use ctrl-c to exit.')
        opts.pkg_env_costs = input_var

    return opts
