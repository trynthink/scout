import argparse
import copy
import time
import json
import traceback
import warnings
from collections import OrderedDict
from pathlib import Path
from os import stat
from scout.utils import JsonIO, PrintFormat as fmt
from scout.config import LogConfig, FilePaths as fp
from scout.ecm_prep_vars import UsefulInputFiles, UsefulVars
import logging
logger = logging.getLogger("ecm_prep")


class ECMPrepHelper:
    """Shared methods used throughout ecm_prep.py"""

    @staticmethod
    def configure_ecm_prep_logger():
        # Set file name for prep error logs using current date and time
        err_f_name = fp.GENERATED / ("log_ecm_prep_" + time.strftime("%Y%m%d-%H%M%S") + ".txt")
        # Ensure root logger is set up
        LogConfig.configure_logging()
        logger.handlers.clear()  # Remove existing handlers
        filehandler = logging.FileHandler(err_f_name, mode='a', delay=True)
        # Set new handler to match root formatter
        root_format = logging.getLogger().handlers[0].formatter
        filehandler.setFormatter(root_format)
        logger.addHandler(filehandler)

        # Write logger to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(root_format)
        logger.addHandler(console_handler)

        # Disable propagation to root logger
        logger.propagate = False

    @staticmethod
    def initialize_run_setup(input_files: UsefulInputFiles) -> dict:
        """Reads in analysis engine setup file, run_setup.json, and initializes values. If the file
            exists and has measures set to 'active', those will be moved to 'inactive'. If the file
            does not exist, return a dictionary with empty 'active' and 'inactive' lists.

        Args:
            input_files (UsefulInputFiles): UsefulInputFiles instance

        Returns:
            dict: run_setup data with active and inactive lists
        """
        try:
            am = open(input_files.run_setup, 'r')
            try:
                run_setup = json.load(am, object_pairs_hook=OrderedDict)
            except ValueError as e:
                raise ValueError(
                    f"Error reading in '{input_files.run_setup}': {str(e)}") from None
            am.close()
            # Initialize all measures as inactive
            run_setup = ECMPrepHelper.update_active_measures(run_setup,
                                                             to_inactive=run_setup["active"])
        except FileNotFoundError:
            run_setup = {"active": [], "inactive": [], "skipped": []}

        return run_setup

    @staticmethod
    def update_run_setup(run_setup: dict,
                         opts: argparse.Namespace,
                         meas_toprep_package_init: list) -> dict:
        # Set contributing ECMs as inactive in run_setup and throw warning, set all others as active
        ctrb_ms = [ecm for pkg in meas_toprep_package_init for ecm in pkg["contributing_ECMs"]]
        non_ctrb_ms = [ecm for ecm in opts.ecm_files if ecm not in ctrb_ms]
        excluded_ind_ecms = [ecm for ecm in opts.ecm_files_user if ecm in ctrb_ms]
        run_setup = ECMPrepHelper.update_active_measures(run_setup,
                                                         to_active=non_ctrb_ms,
                                                         to_inactive=excluded_ind_ecms)
        if excluded_ind_ecms:
            excluded_ind_ecms_txt = fmt.format_console_list(excluded_ind_ecms)
            warnings.warn("The following ECMs were selected to be prepared, but due to their"
                          " presence in one or more packages, they will not be run individually"
                          " and will only be included as part of the package(s):"
                          f"\n{''.join(excluded_ind_ecms_txt)}")

        # Set packages to active in run_setup
        valid_packages = [pkg["name"] for pkg in meas_toprep_package_init]
        run_setup = ECMPrepHelper.update_active_measures(run_setup, to_active=valid_packages)

        return run_setup

    @staticmethod
    def get_measure_savings_shapes(opts: argparse.Namespace,
                                   handyfiles: UsefulInputFiles) -> list:
        """If applicable, import file to write prepared measure sector shapes to (if file does not
        exist, provide empty list as substitute, since file will be created later when writing ECM
        data)

        Args:
            opts (argparse.Namespace): object containing ecm_prep argument attributes
            handyfiles (UsefulInputFiles): object containing file paths for input and output

        Returns:
            list: measure sector shapes
        """

        meas_shapes = []
        if opts.sect_shapes is True:
            try:
                meas_shapes = JsonIO.load_json(handyfiles.ecm_prep_shapes)
            except FileNotFoundError:
                meas_shapes = []
        return meas_shapes

    @staticmethod
    def get_existing_measure_summary_data(handyfiles: UsefulInputFiles) -> list:
        """Import file of previously prepared measure attributes. If file does not exist, return
        empty list.

        Args:
            handyfiles (UsefulInputFiles): object containing file paths for input and output

        Returns:
            list: Summary of previously prepared measures
        """

        try:
            meas_summary = JsonIO.load_json(handyfiles.ecm_prep)
        except FileNotFoundError:
            meas_summary = []

        return meas_summary

    @staticmethod
    def get_pkg_env_sep_info(handyfiles: UsefulInputFiles, meas_summary: list) -> tuple[list, list]:
        """If user desires isolation of envelope impacts within envelope/HVAC packages, develop a
        list that indicates which individual ECMs contribute to which package(s); this info is
        needed for making copies of certain ECMs and ECM packages that serve as counterfactuals
        for the isolation of envelope impacts within packages.

        Args:
            handyfiles (UsefulInputFiles): object containing file paths for input and output
            meas_summary (list): summary of previously prepared measures

        Raises:
            ValueError: if package or package sectorshape data file cannot be read

        Returns:
            tuple[list, list]: summary of counterfactual envelope/HVAC package
            data isolated for envelope effects (meas_summary_env_cf), counterfactual
            envelope/HVAC package sector shape data (meas_shapes_env_cf), and updated
            summary of prevously prepared measures (meas_summary).
        """

        # Import separate file that will ultimately store all
        # counterfactual package data for later use
        try:
            ecf = open(handyfiles.ecm_prep_env_cf, 'r')
            try:
                meas_summary_env_cf = json.load(ecf)
            except ValueError as e:
                raise ValueError(
                    f"Error reading in '{handyfiles.ecm_prep_env_cf}': {str(e)}") from None
            ecf.close()
            # In some cases, individual ECMs may be defined and written to
            # the counterfactual package data; these ECMs should be added
            # to the list of previously prepared individual ECMs so that
            # they are not prepared again if their definitions haven't
            # been updated
            meas_summary_env_cf_indiv = [
                m for m in meas_summary_env_cf if
                "contributing_ECMs" not in m.keys()]
            if len(meas_summary_env_cf_indiv) != 0:
                meas_summary = meas_summary + meas_summary_env_cf_indiv
        except FileNotFoundError:
            meas_summary_env_cf = []
        # If applicable, import separate file that will store
        # counterfactual package sector shape data
        try:
            ecf_ss = open(handyfiles.ecm_prep_env_cf, 'r')
            try:
                meas_shapes_env_cf = json.load(ecf_ss)
            except ValueError:
                raise ValueError(
                    f"Error reading in '{handyfiles.ecm_prep_env_cf_shapes}'") from None
            ecf_ss.close()
        except FileNotFoundError:
            meas_shapes_env_cf = []

        return meas_summary_env_cf, meas_shapes_env_cf, meas_summary

    @staticmethod
    def get_indiv_measures(opts: argparse.Namespace,
                           handyfiles: UsefulInputFiles,
                           handyvars: UsefulVars,
                           meas_summary: list,
                           meas_toprep_indiv_names: list,
                           meas_toprep_package_init: list,
                           ctrb_ms_pkg_all: list) -> tuple[list, list, list]:

        """Collect individual measures that require updates

        Args:
            opts (argparse.Namespace): object containing ecm_prep argument attributes
            handyfiles (UsefulInputFiles): object containing file paths for input and output
            handyvars (UsefulVars): object containing global ecm_prep variables
            meas_summary (list): summary of previously prepared measures
            meas_toprep_indiv_names (list): individual measure names
            meas_toprep_package_init (list): summary of measure packages from package_ecms.json
            ctrb_ms_pkg_all (list): summary of packages and their contributing ECMs

        Returns:
            tuple[list, list, list]: measures to prepare (meas_toprep_indiv), measures to preapre
            independent of packages (meas_toprep_indiv_nopkg), packages for isolating envelope
            effects (pkg_copy_flag)
        """

        ecm_prep_exists = False
        if len(meas_summary) > 0:
            ecm_prep_exists = True

        # Initialize list of all individual measures that require updates
        meas_toprep_indiv = []
        # Initialize list of individual measures that require an update due to
        # a change in their individual definition (and not a change in the
        # definition or other contributing measures of a package they are a
        # part of, if applicable)
        meas_toprep_indiv_nopkg = []
        # Initialize list to track ECM packages that should be copied as
        # counterfactuals for isolating envelope impacts
        pkg_copy_flag = []

        for mi in meas_toprep_indiv_names:
            # Load each JSON into a dict
            meas_dict = JsonIO.load_json(handyfiles.indiv_ecms / mi)
            try:
                # Shorthand for previously prepared measured data that match
                # current measure
                match_in_prep_file = [y for y in meas_summary if (
                    "contributing_ECMs" not in y.keys() and
                    y["name"] == meas_dict["name"]) or (
                    "contributing_ECMs" in y.keys() and
                    meas_dict["name"] in y["contributing_ECMs"])]
                # Determine whether dict should be added to list of individual
                # measure definitions to update. Add a measure dict to the list
                # requiring further preparation if: a) measure is in package
                # (may be removed from update later) b) measure JSON time stamp
                # indicates it has been modified since the last run of
                # 'ecm_prep.py' c) measure name is not already included in
                # database of prepared measure attributes ('/generated/ecm_prep.json'); d)
                # measure does not already have competition data prepared for
                # it (in '/generated/ecm_competition_data' folder), or
                # or e) command line arguments applied to the measure are not
                # consistent with those reported out the last time the measure
                # was prepared (based on 'usr_opts' attribute), excepting
                # the 'verbose', 'yaml', and 'ecm_directory' options, which have no bearing
                # on results
                compete_files = [x for x in handyfiles.ecm_compete_data.iterdir() if not
                                 x.name.startswith('.')]
                ignore_opts = ["verbose", "yaml", "ecm_directory", "ecm_files", "ecm_files_user",
                               "ecm_packages", "ecm_files_regex"]
                update_indiv_ecm = ((ecm_prep_exists and stat(
                    handyfiles.indiv_ecms / mi).st_mtime > stat(
                    handyfiles.ecm_prep).st_mtime) or
                    (len(match_in_prep_file) == 0 or (
                        "(CF)" not in meas_dict["name"] and all([all([
                            x["name"] != Path(y.stem).stem for y in
                            compete_files]) for
                            x in match_in_prep_file])) or
                        (opts is None and not all([all([
                            m["usr_opts"][k] is False
                            for k in m["usr_opts"].keys()]) for
                            m in match_in_prep_file])) or
                        (not all([all([m["usr_opts"][x] ==
                                      vars(opts)[x] for x in [
                                      k for k in vars(opts).keys() if
                                      k not in ignore_opts]]) for m in
                                 match_in_prep_file]))))
                # Add measure to tracking of individual measures needing update
                # independent of required updates to packages they are a
                # part of (if applicable)
                if update_indiv_ecm:
                    meas_toprep_indiv_nopkg.append(meas_dict["name"])
                # Register name of package measure is a part of, if applicable
                meas_in_pkgs = any([
                    meas_dict["name"] in pkg["contributing_ECMs"] for pkg in
                    meas_toprep_package_init])
                if update_indiv_ecm or meas_in_pkgs:
                    # Check to ensure that tech switching information is
                    # available, if needed; otherwise throw a warning
                    # about this measure

                    # Check for tech. switch attribute, if not there set NA
                    try:
                        meas_dict["tech_switch_to"]
                    except KeyError:
                        meas_dict["tech_switch_to"] = "NA"
                    # If tech switching information is None unexpectedly
                    # (e.g., for a measure that switches fuels, or from
                    # resistance-based tech. to HPs, or to LEDs), prompt user
                    # to provide this information and rerun
                    if meas_dict["tech_switch_to"] == "NA" and (
                            meas_dict["fuel_switch_to"] is not None or (
                                any([x in meas_dict["name"] for x in [
                                    "LED", "solid state",
                                    "Solid State", "SSL"]]) or
                                (any([x in meas_dict["name"] for x in [
                                        "HP", "heat pump", "Heat Pump"]]) and (
                                    meas_dict["technology"] is not None and
                                    (any([
                                        x in handyvars.resist_ht_wh_tech for
                                        x in meas_dict["technology"]]) or
                                        meas_dict["technology"] in
                                        handyvars.resist_ht_wh_tech))))):
                        # Print missing tech switch info. warning
                        raise ValueError(
                            "Measure is missing expected technology switching "
                            "info.; add to 'tech_switch_to' attribute in the "
                            "measure definition JSON and rerun ecm_prep, "
                            "e.g.:\n"
                            "'tech_switch_to': 'ASHP' (switch to ASHP)\n"
                            "'tech_switch_to': 'GSHP' (switch to GSHP)\n"
                            "'tech_switch_to': 'HPWH' (switch to HPWH)\n"
                            "'tech_switch_to': 'electric cooking' "
                            "(switch to electric cooking)\n"
                            "'tech_switch_to': 'electric drying' "
                            "(switch to electric drying)\n"
                            "'tech_switch_to': 'LEDs' "
                            "(switch to LED lighting)\n"
                            " Alternatively, set 'tech_switch_to' to null "
                            "if no tech switching is meant to be represented")

                    # Append measure dict to list of measure definitions
                    # to update if it meets the above criteria
                    meas_toprep_indiv.append(meas_dict)
                    # Add copies of the measure that examine multiple scenarios
                    # of public health cost data additions, assuming the
                    # measure is not already a previously prepared copy
                    # that reflects these additions (judging by name)
                    if opts.health_costs is True and \
                            "PHC" not in meas_dict["name"]:
                        # Check to ensure that the measure applies to the
                        # electric fuel type (or switches to it); if not, do
                        # not prepare additional versions of the measure with
                        # health costs
                        if ((((type(meas_dict["fuel_type"]) is not list) and
                                meas_dict["fuel_type"] not in [
                            "electricity", "all"]) or ((type(
                                meas_dict["fuel_type"]) is list) and all([
                                x not in ["electricity", "all"] for x in
                                meas_dict["fuel_type"]]))) and
                                meas_dict["fuel_switch_to"] != "electricity"):
                            # Warn the user that ECMs that do not apply to the
                            # electric fuel type will not be prepared with
                            # public cost health adders
                            warnings.warn(
                                "WARNING: " + meas_dict["name"] + " does not "
                                "apply to the electric fuel type; versions of "
                                "this ECM with low/high public health cost "
                                "adders will not be prepared.")
                        else:
                            for scn in handyvars.health_scn_names:
                                # Determine unique measure copy name
                                new_name = meas_dict["name"] + "-" + scn[0]
                                # Copy the measure
                                new_meas = copy.deepcopy(meas_dict)
                                # Set the copied measure name to the name above
                                new_meas["name"] = new_name
                                # Append the copied measure to list of measure
                                # definitions to update
                                meas_toprep_indiv.append(new_meas)
                                # Add measure to tracking of individual
                                # measures needing update independent of
                                # required updates to packages they are a
                                # part of (if applicable)
                                if update_indiv_ecm:
                                    meas_toprep_indiv_nopkg.append(
                                        new_meas["name"])
                                # Flag the package(s) that the measure that was
                                # copied contributes to; this package will be
                                # copied as well
                                pkgs_to_copy = [
                                    x[0] for x in ctrb_ms_pkg_all if
                                    meas_dict["name"] in x[1]]
                                # Add the package name, the package copy name,
                                # the name of the original measure that
                                # contributes to the package, and the measure
                                # copy name
                                for p in pkgs_to_copy:
                                    # Set pkg copy name
                                    new_pkg_name = p + "-" + scn[0]
                                    pkg_copy_flag.append([
                                        p, new_pkg_name,
                                        meas_dict["name"], new_name])

                    # Check for whether a reference case analogue measure should be added, which a
                    # user flags via the `ref_analogue` attribute
                    if meas_dict.get("ref_analogue") and opts.add_typ_eff:
                        add_ref_meas = True
                    else:
                        add_ref_meas = False

                    # Add reference case analogues of the measure if the user has flagged the
                    # measure as requiring such an analogue to subsequently compete against (via
                    # `ref_analogue` attribute.)
                    if add_ref_meas:
                        # Determine unique measure copy name
                        new_name = meas_dict["name"] + " (Ref. Analogue)"
                        # Copy the measure
                        new_meas = copy.deepcopy(meas_dict)
                        # Set the copied measure name to the name above
                        new_meas["name"] = new_name
                        opts.ecm_files.append(new_meas["name"])
                        # If measure was set to fuel switch without exogenous
                        # FS rates, reset typical/BAU analogue FS to None (
                        # e.g., such that for an ASHP FS measure, a typical/
                        # BAU fossil-based heating analogue is created
                        # for later competition with that FS measure). Also
                        # ensure that no tech switching is specified for
                        # consistency w/ fuel_switch_to
                        if (meas_dict["fuel_switch_to"] is not None and
                                opts.exog_hp_rates is False):
                            new_meas["fuel_switch_to"], \
                                new_meas["tech_switch_to"] = (
                                    None for n in range(2))
                        # Append the copied measure to list of measure
                        # definitions to update
                        meas_toprep_indiv.append(new_meas)
                        # Add measure to tracking of individual
                        # measures needing update independent of
                        # required updates to packages they are a
                        # part of (if applicable)
                        if update_indiv_ecm:
                            meas_toprep_indiv_nopkg.append(new_meas["name"])
                    # If desired by user, add copies of HVAC equipment measures
                    # that are part of packages; these measures will be
                    # assigned no relative performance improvement and
                    # added to copies of those HVAC/envelope packages, to serve
                    # as counter-factuals that allow isolation of envelope
                    # impacts within each package
                    if opts is not None and opts.pkg_env_sep is True and len(
                        ctrb_ms_pkg_all) != 0 and (any(
                            [meas_dict["name"] in x[1] for
                                x in ctrb_ms_pkg_all])) and (
                        (isinstance(meas_dict["end_use"], list) and any([
                            x in ["heating", "cooling"] for
                            x in meas_dict["end_use"]])) or
                            meas_dict["end_use"] in
                            ["heating", "cooling"]) and (
                        not ((isinstance(meas_dict["technology"], list)
                              and all([x in handyvars.demand_tech for
                                       x in meas_dict["technology"]])) or
                             meas_dict["technology"] in handyvars.demand_tech)):
                        # Determine measure copy name, CF for counterfactual
                        new_name = meas_dict["name"] + " (CF)"
                        # Copy the measure
                        new_meas = copy.deepcopy(meas_dict)
                        # Set the copied measure name to the name above
                        new_meas["name"] = new_name
                        # Append the copied measure to list of measure
                        # definitions to update
                        meas_toprep_indiv.append(new_meas)
                        # Add measure to tracking of individual
                        # measures needing update independent of
                        # required updates to packages they are a
                        # part of (if applicable)
                        if update_indiv_ecm:
                            meas_toprep_indiv_nopkg.append(new_meas["name"])
                        # Flag the package(s) that the measure that was copied
                        # contributes to; this package will be copied as well
                        # to produce the final counterfactual data
                        pkgs_to_copy = [x[0] for x in ctrb_ms_pkg_all if
                                        meas_dict["name"] in x[1]]
                        # Add the package name, the package copy name,
                        # the name of the original measure that contributes
                        # to the package, and the measure copy name
                        for p in pkgs_to_copy:
                            # Set pkg copy name
                            new_pkg_name = p + " (CF)"
                            pkg_copy_flag.append([p, new_pkg_name, meas_dict["name"], new_name])
            except ValueError as e:
                raise ValueError(
                    "Error reading in ECM '" + mi.stem + "': " +
                    str(e)) from None

        return meas_toprep_indiv, meas_toprep_indiv_nopkg, pkg_copy_flag

    @staticmethod
    def get_measure_packages(opts: argparse.Namespace,
                             handyfiles: UsefulInputFiles,
                             meas_toprep_package_init: list,
                             meas_prepped_pkgs: list,
                             meas_toprep_indiv_nopkg: list,
                             pkg_copy_flag: list) -> tuple[list, list]:

        """Collect measures packages that require updates

        Args:
            opts (argparse.Namespace): object containing ecm_prep argument attributes
            handyfiles (UsefulInputFiles): object containing file paths for input and output
            meas_toprep_package_init (list): summary of measure packages from package_ecms.json
            meas_prepped_pkgs (list): previously prepared packages
            meas_toprep_indiv_nopkg (list): measures to preapre independent of packages
            pkg_copy_flag (list): packages used as counterfactuals for isolating envelope effects

        Returns:
            tuple[list, list]: packages to prepare (meas_toprep_package) and measures to prepare
            listed as contributing ECMs to packages.
        """

        # Initialize list of measure package dicts to prepare
        meas_toprep_package = []
        # Initialize a list to track which individual ECMs contribute to packages
        ctrb_ms_pkg_prep = []

        # Loop through each package dict in the current list and determine which
        # of these package measures require further preparation
        for m in meas_toprep_package_init:
            # Determine the subset of previously prepared package measures
            # with the same name as the current package measure
            m_exist = [me for me in meas_prepped_pkgs if me["name"] == m["name"]]

            # Add a package dict to the list requiring further preparation after first checking if
            # all of the package's contributing measures have been updated, then if: a) the package
            # is new, b) package does not already have competition data prepared for it, c) package
            # "contributing_ECMs" and/or "benefits" parameters have been edited from a previous
            # version, or d) package was prepared with different settings around including envelope
            # costs (if applicable) than in the current run

            # Check for existing competition data for the package (condition b)
            name_mask = all(m["name"] != Path(y.stem).stem for y in
                            handyfiles.ecm_compete_data.iterdir())
            exst_ecms_mask = exst_engy_save_mask = exst_cost_red_mask = False
            exst_pkg_env_mask_1 = exst_pkg_env_mask_2 = False
            # Check for differences in the specification of the previously prepared
            # package measure and the current package measure of the same name (condition c and d)
            if len(m_exist) == 1:
                exst_ecms_mask = (sorted(m["contributing_ECMs"]) !=
                                  sorted(m_exist[0]["contributing_ECMs"]))
                # Difference in expected package energy savings
                exst_engy_save_mask = (m["benefits"]["energy savings increase"] !=
                                       m_exist[0]["benefits"]["energy savings increase"])
                exst_cost_red_mask = (m["benefits"]["cost reduction"] !=
                                      m_exist[0]["benefits"]["cost reduction"])
                exst_pkg_env_mask_1 = (opts is not None and opts.pkg_env_costs is not False and
                                       m_exist[0]["pkg_env_costs"] is False)
                exst_pkg_env_mask_2 = (opts is None or opts.pkg_env_costs is False and
                                       m_exist[0]["pkg_env_costs"] is not False)
                updated_contrib_mask = any(
                    contrib in meas_toprep_indiv_nopkg for contrib in m["contributing_ECMs"]
                )

            # Check for conditions that would indicate a package needs to be processed
            # (condition a and previously inspected conditions b, c, and d)
            if len(m_exist) == 0 or name_mask or \
                    ((exst_ecms_mask or exst_engy_save_mask or exst_cost_red_mask) or
                     (exst_pkg_env_mask_1 or exst_pkg_env_mask_2 or updated_contrib_mask)):

                meas_toprep_package.append(m)
                # Add contributing ECMs to those needing updates
                ctrb_ms_pkg_prep.extend(m["contributing_ECMs"])
                # If package is flagged as needing a copy to serve as a
                # counterfactual for isolating envelope impacts, make the copy
                if pkg_copy_flag:
                    pkg_item = [x for x in pkg_copy_flag if x[0] == m["name"]]
                else:
                    pkg_item = []
                if len(pkg_item) > 0:
                    # Determine unique package copy name
                    new_pkg_name = pkg_item[0][1]
                    # Copy the package
                    new_pkg = copy.deepcopy(m)
                    # Set the copied package name to the name above
                    new_pkg["name"] = new_pkg_name
                    # Parse new package data to find information about revised
                    # names in contributing ECM set
                    for p in pkg_item:
                        # Replace original ECM names from the package's list of contributing ECMs
                        # with those of the ECM copies such that data for these copies will be
                        # pulled into the package assessment
                        for ind, ecm in enumerate(new_pkg["contributing_ECMs"]):
                            if ecm in p:
                                new_pkg["contributing_ECMs"][ind] = p[3]
                    # Append the copied package measure to list of measure definitions to update,
                    # and also update the list of individual measures that contribute to packages
                    # being prepared
                    meas_toprep_package.append(new_pkg)
                    ctrb_ms_pkg_prep.extend(new_pkg["contributing_ECMs"])

            # Raise an error if the current package matches the name of
            # multiple previously prepared packages
            elif len(m_exist) > 1:
                raise ValueError(
                    "Multiple existing ECM names match '" + m["name"] + "'")

        return meas_toprep_package, ctrb_ms_pkg_prep

    @staticmethod
    def update_active_measures(run_setup: dict,
                               to_active: list = [],
                               to_inactive: list = [],
                               to_skipped: list = []) -> dict:
        """Update active, inactive, and skipped lists in the run_setup dictionary

        Args:
            run_setup (dict): dictionary to be used as the analysis engine setup file
            to_active (list, optional): measures or packages to set to active
                and remove from inactive or skipped. Defaults to [].
            to_inactive (list, optional): measures or packages to set to inactive
                and remove from active or skipped. Defaults to [].
            to_skipped (list, optional): measures or packages to set to skipped
                and remove from active or inactive. Defaults to [].

        Returns:
            dict: run_setup data with updated active, inactive, and skipped lists.
        """
        active_set = set(run_setup["active"])
        inactive_set = set(run_setup["inactive"])
        skipped_set = set(run_setup["skipped"])

        # Set active and remove from inactive or skipped
        active_set.update(to_active)
        inactive_set.difference_update(to_active)
        skipped_set.difference_update(to_active)

        # Set inactive and remove from active or skipped
        active_set.difference_update(to_inactive)
        inactive_set.update(to_inactive)
        skipped_set.difference_update(to_inactive)

        # Set skipped and remove from active or inactive
        active_set.difference_update(to_skipped)
        inactive_set.difference_update(to_skipped)
        skipped_set.update(to_skipped)

        run_setup["active"] = list(active_set)
        run_setup["inactive"] = list(inactive_set)
        run_setup["skipped"] = list(skipped_set)

        return run_setup

    @staticmethod
    def prep_error(meas_name, handyvars, handyfiles):
        """Prepare and write out error messages for skipped measures/packages.

        Args:
            meas_name (str): Measure or package name.
            handyvars (object): Global variables of use across Measure methods.
            handyfiles (object): Input files of use across Measure methods.
        """
        # # Complete the update to the console for each measure being processed
        # Pull full error traceback
        err_dets = traceback.format_exc()
        # Construct error message to write out
        err_msg = (f"\nECM '{meas_name}' produced the following exception that prevented its "
                   f"preperation: \n{str(err_dets)}\n")
        # Add ECM to skipped list
        handyvars.skipped_ecms.append(meas_name)
        # Print error message if in verbose mode
        # fmt.verboseprint(opts.verbose, err_msg, "error", logger)
        # # Log error message to file (see ./generated)
        logger.error(err_msg)

    @staticmethod
    def downselect_packages(existing_pkgs: list[dict], pkg_subset: list) -> list:
        if "*" in pkg_subset:
            return existing_pkgs
        downselected_pkgs = [pkg for pkg in existing_pkgs if pkg["name"] in pkg_subset]

        return downselected_pkgs

    @staticmethod
    def retrieve_valid_ecms(packages: list,
                            opts: argparse.Namespace,
                            handyfiles: UsefulInputFiles) -> list:
        """Determine full list of individual measure JSON names that 1) contribute to selected
            packages in opts.ecm_packages, or 2) are included in opts.ecm_files, and 3) exist in the
            ecm definitions directory (opts.ecm_directory)

        Args:
            packages (list): List of valid packages
            opts (argparse.Namespace): object storing user responses
            handyfiles (UsefulInputFiles): object storing input filepaths

        Returns:
            list: filtered list of ECMs that meet the criteria above
        """

        contributing_ecms = {
            ecm for pkg in packages for ecm in pkg["contributing_ECMs"]}
        opts.ecm_files.extend([ecm for ecm in contributing_ecms if ecm not in opts.ecm_files])
        valid_ecms = [
            x for x in handyfiles.indiv_ecms.iterdir() if x.suffix == ".json" and
            'package_ecms' not in x.name and x.stem in opts.ecm_files]

        return valid_ecms

    @staticmethod
    def filter_invalid_packages(packages: list[dict],
                                ecms: list,
                                opts: argparse.Namespace) -> tuple[list[dict], list]:
        """Identify and filter packages whose ECMs are not all present in the individual ECM set

        Args:
            packages (list[dict]): List of packages imported from package_ecms.json
            ecms (list): List of ECM definitions file names
            opts (argparse.Namespace): argparse object containing the argument attributes

        Returns:
            filtered_packages (list[dict]): Packages list with invalid packages filtered out
            invalid_pkgs (list): List of invalid packages
        """

        invalid_pkgs = [pkg["name"] for pkg in packages if not
                        set(pkg["contributing_ECMs"]).issubset(set(ecms))]
        filtered_packages = [pkg for pkg in packages if pkg["name"] not in invalid_pkgs]

        # Trigger warning message regarding screening of packages
        package_opt_txt = ""
        if opts.ecm_packages is not None:
            package_opt_txt = "specified with the ecm_packages argument "
        if invalid_pkgs:
            invalid_pkgs_txt = fmt.format_console_list(invalid_pkgs)
            msg = (f"WARNING: Package(s) in package_ecms.json {package_opt_txt}have contributing"
                   " ECMs that are not present among ECM definitions. The following packages will"
                   f" not be executed: \n{''.join(invalid_pkgs_txt)}")
            warnings.warn(msg)

        return filtered_packages, invalid_pkgs

    @staticmethod
    def tsv_cost_carb_yrmap(tsv_data, aeo_years):
        """Map 8760 TSV cost/carbon data years to AEO years.

        Args:
            tsv_data: TSV cost or carbon input datasets.
            aeo_years: AEO year range.

        Returns:
            Mapping between TSV cost/carbon data years and AEO years.
        """

        # Set up a matrix mapping each AEO year to the years available in the
        # TSV data

        # Pull available years from TSV data
        tsv_yrs = list(sorted(tsv_data.keys()))
        # Establish the mapping from available TSV years to AEO years
        tsv_yr_map = {
            yr_tsv: [str(x) for x in range(
                int(yr_tsv), int(tsv_yrs[ind + 1]))]
            if (ind + 1) < len(tsv_yrs) else [str(x) for x in range(
                int(yr_tsv), int(aeo_years[-1]) + 1)]
            for ind, yr_tsv in enumerate(tsv_yrs)
        }
        # Prepend AEO years preceding the start year in the TSV data, if needed
        if (aeo_years[0] not in tsv_yr_map[tsv_yrs[0]]):
            yrs_to_prepend = range(int(aeo_years[0]), min([
                int(x) for x in tsv_yr_map[tsv_yrs[0]]]))
            tsv_yr_map[tsv_yrs[0]] = [str(x) for x in yrs_to_prepend] + \
                tsv_yr_map[tsv_yrs[0]]

        return tsv_yr_map

    @staticmethod
    def split_clean_data(meas_prepped_objs, full_dat_out):
        """Reorganize and remove data from input Measure objects.

        Note:
            The input Measure objects have updated data, which must
            be reorganized/condensed for the purposes of writing out
            to JSON files.

        Args:
            meas_prepped_objs (object): Measure objects with data to
                be split in to separate dicts or removed.
            full_dat_out (dict): Flag that limits technical potential (TP) data
                prep/reporting when TP is not in user-specified adoption schemes.

        Returns:
            Three to four lists of dicts, one containing competition data for
            each updated measure, one containing high level summary
            data for each updated measure, another containing sector shape
            data for each measure (if applicable), and a final one containing
            efficient fuel split data, as applicable to fuel switching measures
            when the user has required fuel splits.
        """
        from scout.ecm_prep import MeasurePackage

        # Initialize lists of measure competition/summary data
        meas_prepped_compete = []
        meas_prepped_summary = []
        meas_prepped_shapes = []
        meas_eff_fs_splt = []
        # Loop through all Measure objects and reorganize/remove the
        # needed data.
        for m in meas_prepped_objs:
            # Initialize a reorganized measure competition data dict and efficient
            # fuel split data dict
            comp_data_dict, fs_splits_dict, shapes_dict = ({} for n in range(3))
            # Retrieve measure contributing microsegment data that are relevant to
            # markets competition in the analysis engine, then remove these data
            # from measure object
            for adopt_scheme in m.handyvars.adopt_schemes_prep:
                # Delete contributing microsegment data that are
                # not relevant to competition in the analysis engine
                del m.markets[adopt_scheme]["mseg_adjust"][
                    "secondary mseg adjustments"]["sub-market"]
                del m.markets[adopt_scheme]["mseg_adjust"][
                    "secondary mseg adjustments"]["stock-and-flow"]
                # If individual measure, delete markets data used to linked
                # heating/cooling turnover and switching rates across msegs (these
                # data are not prepared for packages)
                if not isinstance(m, MeasurePackage):
                    del m.markets[adopt_scheme]["mseg_adjust"][
                        "paired heat/cool mseg adjustments"]
                # Add remaining contributing microsegment data to
                # competition data dict, if the adoption scenario will be competed
                # in the run.py module, then delete from measure
                if full_dat_out[adopt_scheme]:
                    comp_data_dict[adopt_scheme] = \
                        m.markets[adopt_scheme]["mseg_adjust"]
                    # If applicable, add efficient fuel split data to fuel split
                    # data dict
                    if len(m.eff_fs_splt[adopt_scheme].keys()) != 0:
                        fs_splits_dict[adopt_scheme] = \
                            m.eff_fs_splt[adopt_scheme]
                    # If applicable, add sector shape data
                    if m.sector_shapes is not None and len(
                            m.sector_shapes[adopt_scheme].keys()) != 0:
                        shapes_dict["name"] = m.name
                        shapes_dict[adopt_scheme] = \
                            m.sector_shapes[adopt_scheme]
                else:
                    # If adoption scenario will not be competed in the run.py
                    # module, remove detailed mseg breakouts
                    del m.markets[adopt_scheme]["mseg_out_break"]
                del m.markets[adopt_scheme]["mseg_adjust"]
            # Delete info. about efficient fuel splits for fuel switch measures
            del m.eff_fs_splt
            # Delete info. about sector shapes
            del m.sector_shapes

            # Append updated competition data from measure to
            # list of competition data across all measures
            meas_prepped_compete.append(comp_data_dict)
            # Append fuel switching split information, if applicable
            meas_eff_fs_splt.append(fs_splits_dict)
            # Append sector shape information, if applicable
            meas_prepped_shapes.append(shapes_dict)
            # Delete 'handyvars' measure attribute (not relevant to
            # analysis engine)
            del m.handyvars
            # Delete 'tsv_features' measure attributes
            # (not relevant) for individual measures
            if not isinstance(m, MeasurePackage):
                del m.tsv_features
                # Delete individual measure attributes used to link heating/
                # cooling microsegment turnover and switching rates
                del m.linked_htcl_tover
                del m.linked_htcl_tover_anchor_eu
                del m.linked_htcl_tover_anchor_tech
            # For measure packages, replace 'contributing_ECMs'
            # objects list with a list of these measures' names and remove
            # unnecessary heating/cooling equip/env overlap data
            if isinstance(m, MeasurePackage):
                m.contributing_ECMs = [
                    x.name for x in m.contributing_ECMs]
                del m.htcl_overlaps
                del m.contributing_ECMs_eqp
                del m.contributing_ECMs_env
            # Append updated measure __dict__ attribute to list of
            # summary data across all measures
            meas_prepped_summary.append(m.__dict__)

        return meas_prepped_compete, meas_prepped_summary, meas_prepped_shapes, \
            meas_eff_fs_splt
