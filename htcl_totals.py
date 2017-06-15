#!/usr/bin/env python3

from os import getcwd, path
import json


class UsefulInputFiles(object):
    """Class of input file paths to be used by this routine.

    Attributes:
        msegs_in (string): Database of baseline microsegment stock/energy.
        htcl_totals (string): Heating/cooling energy totals by climate zone,
            building type, and structure type.
        metadata (dict): Baseline metadata including min/max for year range.
    """

    def __init__(self):
        self.msegs_in = ("supporting_data", "stock_energy_tech_data",
                         "mseg_res_com_cz.json")
        self.htcl_totals = ("supporting_data", "stock_energy_tech_data",
                            "htcl_totals.json")
        self.metadata = "metadata.json"


class UsefulVars(object):
    """Class of variables that are used globally across functions.

    Attributes:
        aeo_years (list): Modeling time horizon.
        ss_conv (dict): Site-source conversion factors by fuel type.
    """

    def __init__(self, base_dir, handyfiles):
        # Load metadata including AEO year range
        with open(path.join(base_dir, handyfiles.metadata), 'r') as aeo_yrs:
            try:
                aeo_yrs = json.load(aeo_yrs)
            except ValueError as e:
                raise ValueError(
                    "Error reading in '" +
                    handyfiles.metadata + "': " + str(e)) from None
        # Set minimum AEO modeling year
        aeo_min = aeo_yrs["min year"]
        # Set maximum AEO modeling year
        aeo_max = aeo_yrs["max year"]
        # Derive time horizon from min/max years
        self.aeo_years = [
            str(i) for i in range(aeo_min, aeo_max + 1)]
        # Read in JSON with site to source conversion, fuel CO2 intensity,
        # and energy/carbon costs data
        with open(path.join(
            base_dir, *("supporting_data", "convert_data",
                        "site_source_co2_conversions.json")), 'r') as ss:
            cost_ss_carb = json.load(ss)
        # Set site to source conversions
        self.ss_conv = {
            "electricity": cost_ss_carb[
                "electricity"]["site to source conversion"]["data"],
            "natural gas": {yr: 1 for yr in self.aeo_years},
            "distillate": {yr: 1 for yr in self.aeo_years},
            "other fuel": {yr: 1 for yr in self.aeo_years}}


def sum_htcl_branches(nested_dict, adj_frac, sum_val):
    """Sum all leaf node values under a given nested dict level.

    Args:
        nested_dict (dict): The nested dict with values to sum.
        adj_frac (dict): Adjustment fraction to apply to values.
        sum_val (dict): Summed values.

    Returns:
        Summed total values, each adjusted by the input fraction.
    """
    for (k, i) in sorted(nested_dict.items()):
        # Restrict summation of all values under the 'stock' key
        if k == "stock":
            continue
        elif isinstance(i, dict):
            sum_htcl_branches(i, adj_frac, sum_val)
        elif k in sum_val.keys():
            sum_val[k] = sum_val[k] + nested_dict[k] * adj_frac[k]

    return sum_val


def set_new_exist_frac(msegs, aeo_years, bldg):
    """ Determine cumulative new vs. existing structures by year.

    Attributes:
        msegs (dict): Data on new and existing homes (residential) and new and
            existing square feet (commercial), broken down by building type.
        aeo_years (list): Modeling time horizon.
        bldg (string): Building type energy data is currently being retrieved
            for.

    Returns:
        Fractions of the total building stock that are existing or newly
        constructed since the first year in the modeling time horizon.
    """

    # Initialize dict of supporting data for new/existing structure calcs.
    new_constr = {
        "annual new": {}, "annual total": {}}
    # Initialize dict to store new vs. existing structure fractions
    new_exist_frac = {"new": {}, "existing": {}}

    # Determine annual and total new construction for each year (by new
    # homes for the residential sector, by square feet for commercial)
    if bldg in ["single family home", "mobile home",
                "multi family home"]:
        new_constr["annual new"] = {yr: msegs["new homes"][yr] for
                                    yr in aeo_years}
        new_constr["annual total"] = {yr: msegs["total homes"][yr] for
                                      yr in aeo_years}
    else:
        new_constr["annual new"] = {yr: msegs["new square footage"][yr] for
                                    yr in aeo_years}
        new_constr["annual total"] = {yr: msegs["total square footage"][yr] for
                                      yr in aeo_years}

    # Find the cumulative fraction of new buildings constructed in all
    # years since the beginning of the modeling time horizon

    # Set cumulative new homes or square footage totals
    for yr in aeo_years:
        if yr == aeo_years[0]:
            new_exist_frac["new"][yr] = new_constr["annual new"][yr]
        else:
            new_exist_frac["new"][yr] = new_constr["annual new"][yr] + \
                new_exist_frac["new"][str(int(yr) - 1)]
    # Divide cumulative new home or square footage totals by total
    # new homes or square footage to arrive at cumulative new fraction
    new_exist_frac["new"] = {
        key: val / new_constr["annual total"][key] for key, val in
        new_exist_frac["new"].items()}
    # Cumulative existing fraction equals 1 - cumulative new fraction
    new_exist_frac["existing"] = {key: (1 - val) for key, val in
                                  new_exist_frac["new"].items()}

    return new_exist_frac


def sum_htcl_energy(msegs, aeo_years, ss_conv):
    """ Sum heating/cooling energy by climate, building, and structure.

    Attributes:
        msegs (dict): Baseline energy data to sum.
        aeo_years (list): Modeling time horizon.
        ss_conv (dict): Site-source energy conversions by fuel type.

    Note:
        Energy values are summed across a particular climate zone,
        building type, and structure type combination. All energy values must
        be converted to source energy and apportioned to the given structure
        type, in order to be consistent with the ECM competition data these
        data are later combined with in the analysis engine.

    Returns:
        Total energy by year associated with a given climate zone,
        building type, and structure type combination.
    """

    # Initialize dict for storing summed heating/cooling energy totals
    htcl_totals = {}

    # Loop through all climate zone, building type, and structure type
    # combinations and sum the energy values associated with each
    for cz in msegs.keys():
        htcl_totals[cz] = {}
        for bldg in msegs[cz].keys():
            htcl_totals[cz][bldg] = {}
            # Find new vs. existing structure type fraction for bldg. type
            new_exist_frac = set_new_exist_frac(
                msegs[cz][bldg], aeo_years, bldg)
            for vint in new_exist_frac.keys():
                htcl_totals[cz][bldg][vint] = {
                    yr: 0 for yr in aeo_years}
                # Sum energy values across remaining fuel type and end use
                # levels in the baseline energy data dict
                for fuel in msegs[cz][bldg].keys():
                    for eu in [x for x in [
                        "heating", "secondary heating", "cooling"] if
                            x in msegs[cz][bldg][fuel].keys()]:
                        # Find energy value to add to total
                        sum_val = sum_htcl_branches(
                            msegs[cz][bldg][fuel][eu]["demand"],
                            adj_frac={yr: new_exist_frac[vint][yr] *
                                      ss_conv[fuel][yr] for yr in aeo_years},
                            sum_val={yr: 0 for yr in aeo_years})
                        # Update total energy for given climate,
                        # building and structure type combination
                        htcl_totals[cz][bldg][vint] = {
                            yr: htcl_totals[cz][bldg][vint][yr] +
                            sum_val[yr] for yr in aeo_years}

    return htcl_totals


def main():
    """ Import JSON energy data and sum by climate, building, and structure."""

    # Instantiate useful input files object
    handyfiles = UsefulInputFiles()
    # Instantiate useful variables
    handyvars = UsefulVars(base_dir, handyfiles)

    # Import baseline microsegment stock and energy data
    with open(path.join(base_dir, *handyfiles.msegs_in), 'r') as msi:
        try:
            msegs = json.load(msi)
        except ValueError as e:
            raise ValueError(
                "Error reading in '" +
                handyfiles.msegs_in + "': " + str(e)) from None

    # Find total heating and cooling energy use for each climate zone,
    # building type, and structure type combination
    htcl_totals = sum_htcl_energy(
        msegs, handyvars.aeo_years, handyvars.ss_conv)

    # Write out summed heating/cooling energy data
    with open(path.join(base_dir, *handyfiles.htcl_totals), 'w') as jso:
        json.dump(htcl_totals, jso, indent=2)

if __name__ == '__main__':
    # Set current working directory
    base_dir = getcwd()
    main()
