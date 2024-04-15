#!/usr/bin/env python3
import pandas as pd
import json
import ast
from datetime import datetime
from os import getcwd, path


def main(base_dir):
    """Import measure data from CSV and generate a JSON for each measure."""

    # Set up input CSV column -> attribute mapping
    col_attr_map = {
        "Name": "name",
        "Description": "_description",
        "Measure Type": "measure_type",
        "Market Entry Year": "market_entry_year",
        "Region": "climate_zone",
        "Building Type": "bldg_type",
        "Building Vintage": "structure_type",
        "End Use": "end_use",
        "Baseline Fuel Type": "fuel_type",
        "Switched to Fuel Type": "fuel_switch_to",
        "Baseline Technology": "technology",
        "Switched to Technology": "tech_switch_to",
        "Energy Performance": "energy_efficiency",
        "Performance Units": "energy_efficiency_units",
        "Performance Source Notes": ["energy_efficiency_source", "notes"],
        "Performance Source Details": [
            "energy_efficiency_source", "source_data"],
        "Installed Cost": "installed_cost",
        "Cost Units": "cost_units",
        "Cost Source Notes": ["installed_cost_source", "notes"],
        "Cost Source Details": ["installed_cost_source", "source_data"],
        "Lifetime": "product_lifetime",
        "Lifetime Units": "product_lifetime_units",
        "Lifetime Source Notes": ["product_lifetime_source", "notes"],
        "Lifetime Source Details": ["product_lifetime_source", "source_data"],
        "Market Scaling Fraction": "market_scaling_fraction",
        "Market Scaling Source Notes": [
            "market_scaling_fraction_source", "notes"],
        "Market Scaling Source Details": [
            "market_scaling_fraction_source", "source_data"],
        "Author Details": "_updated_by"
    }
    # Set fields for all measure source data
    srce_flds = ["title", "author", "year", "pages", "url"]
    # Set fields for measure author data (timestamp is added subsequently)
    auth_flds = ["name", "organization", "email"]

    # Set JSON output folder
    fpo = "ecm_definitions"

    # Load individual measure data
    # CSV input file path
    fpi = path.join(base_dir, "ecm_definitions/test_data/meas_gen/meas_in.csv")
    # CSV read in
    m_in = pd.read_csv(fpi)

    # Load measure package data (if any)
    # CSV input file path
    fpi_pk = path.join(
        base_dir, "ecm_definitions/test_data/meas_gen/pkg_in.csv")
    # CSV read in
    m_pk_in = pd.read_csv(fpi_pk)

    # Iterate across all measure rows in CSV and populate data for JSONs
    for m_ind, m in m_in.iterrows():
        # Initialize measure JSON
        m_out = {}
        # Loop through all input data columns for measure row in CSV
        for c in col_attr_map.items():
            # Translate CSV input to JSON output
            i_o_val(c, m_out, m, srce_flds, auth_flds)
        # Write final measure JSON; use measure name as file name
        with open(path.join(base_dir, fpo, (m["Name"] + ".json")), "w") as jso:
            json.dump(m_out, jso, indent=2)

    # Initialize output package information
    pkg_out = []
    # Set up input CSV column -> attribute mapping
    col_attr_map_pk = {
        "Name": "name",
        "Measures in Package": "contributing_ECMs",
        "Additional Energy Savings": ["benefits", "energy savings increase"],
        "Energy Savings Source Notes": ["energy_savings_source", "notes"],
        "Energy Savings Source Details": [
            "energy_savings_source", "source_data"],
        "Additional Cost Reductions": ["benefits", "cost reduction"],
        "Cost Reductions Source Notes": ["cost_reduction_source", "notes"],
        "Cost Reductions Source Details": [
            "cost_reduction_source", "source_data"]}

    # Iterate across all measure package rows in CSV and populate JSON

    # Write final measure package JSON; use measure name as file name
    for m_pk_ind, m_pk in m_pk_in.iterrows():
        # Initialize individual package JSON
        m_pk_out = {}
        # Loop through all input data columns for measure row in CSV
        for c in col_attr_map_pk.items():
            # Translate CSV input to JSON output
            i_o_val(c, m_pk_out, m_pk, srce_flds, auth_flds)
        pkg_out.append(m_pk_out)

    print(pkg_out)
    with open(path.join(base_dir, fpo, ("package_ecms.json")), 'a+') as jso:
        json.dump(pkg_out, jso, indent=2)


def i_o_val(c, m_out, m, srce_flds, auth_flds):
    """Translate CSV measure data inputs into JSON outputs."""

    # Pull output initial value from CSV for current column
    val_i = m[c[0]]
    # Replace NA or NaN values with None
    if val_i == "NA" or pd.isna(val_i):
        val_f = None
    # Handle source data with multiple sources (each on newline in CSV)
    elif ("Source Details" in c[0] and
          isinstance(val_i, str) and "\n" in val_i):
        # Separate the data for each source, splitting by newlines
        val_strp_frst = [x.strip() for x in val_i.split("\n")]
        # Initialize final data for each source
        val_f = []
        # Loop through and add each source's data to list
        for ind_v, v in enumerate(val_strp_frst):
            # Separate dict key val pairs; remove any preceding/
            # trailing spaces around the delimiter
            val_strip_scnd = [x.strip() for x in v.split(";")]
            # Add key val pairs to dict
            val_f.append(
                dlm_nst(c, val_strip_scnd, srce_flds, auth_flds))
    # Handle values with nested information (denoted by ';' delimiter)
    elif isinstance(val_i, str) and ";" in val_i:
        # Separate dict key val pairs; remove any preceding/trailing
        # spaces around the delimiter
        val_strp = [x.strip() for x in val_i.split(";")]
        # Add key val pairs to dict
        val_f = dlm_nst(c, val_strp, srce_flds, auth_flds)
    # Otherwise finalize CSV value as-is for JSON
    else:
        val_f = val_i

    # Set output value in JSON; handle formatting of sourcing info.
    # as a dict with two keys ("notes" and "source_data", per variable
    # col_attr_map above)
    if not isinstance(c[1], list):
        m_out[c[1]] = val_f
    else:
        # Handle existing dict (add to)
        if c[1][0] in m_out.keys():
            m_out[c[1][0]][c[1][1]] = val_f
        else:
            m_out[c[1][0]] = {c[1][1]: val_f}


def dlm_nst(attr, val, srce_flds, auth_flds):
    """Manage measure attributes with delimited and/or nested input data.

    Args:
        attr (list): Input CSV heading/output JSON attribute name pairs.
        val (list): CSV data to be assigned across multiple sub-fields.
        srce_flds (list): Sub-fields for sourcing information.
        auth_flds (list): Sub-fields for author information attribute.s

    Returns:
        Nested dict with required information for given attributes.
    """

    # Handle nested performance, performance units, cost, cost units, lifetime,
    # lifetime units, or market scaling data
    if any([(x in attr[0] and "Source" not in attr[0]) for x in [
        "Performance", "Cost", "Lifetime", "Scaling"]]) and any(
            ["-" in x for x in val]):
        # Initialize dict for nested information
        val_dlm_nst = {}
        # Loop through and populate sub-fields
        for vi in val:
            # Nested dict data are further delimited by a dash '-'; separate
            items = vi.split("-")
            # Recursively populate the nested dict
            val_dlm_nst[items[0]] = recursive_dict(items[1:])
        # Finalize value to report out
        val_f = val_dlm_nst
    # Populate source details data
    elif "Source Details" in attr[0]:
        # Initialize dict for semicolon-delimited information
        val_dlm_nst = {}
        # Loop through and populate source sub-fields
        for f_i, f in enumerate(srce_flds):
            # Reset na values to None
            if val[f_i] == "NA" or pd.isna(val[f_i]):
                val[f_i] = None
            # Set year and individual page information to integers
            elif f == "year" or (f == "pages" and "," not in val[f_i]):
                val[f_i] = int(val[f_i])
            # Finalize page range as a list
            elif f == "pages" and "," in val[f_i]:
                val[f_i] = ast.literal_eval(val[f_i])
            val_dlm_nst[f] = val[f_i]
        # Finalize value to report out
        val_f = val_dlm_nst
    # Handle measure author data
    elif "Author" in attr[0]:
        val_dlm_nst = {}
        # Loop through and populate author sub-fields
        for f_i, f in enumerate(auth_flds):
            if val[f_i] == "NA" or pd.isna(val[f_i]):
                val[f_i] = None
            val_dlm_nst[f] = val[f_i]
        # Finalize value to report out
        val_f = val_dlm_nst
        # Add timestamp information
        val_f["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # All other data set as is
    else:
        val_f = val

    return val_f


def recursive_dict(data):
    """Recursively populate dict given nested attribute data."""

    # At terminal value (one element list); convert to float
    if len(data) == 1:
        return float(data[0])
    # Not yet at terminal value; nest recursively
    else:
        # Take first value
        first_value = data[0]
        # Take every value but the first value and nest further
        data = {first_value: recursive_dict(data[1:])}
        return data


if __name__ == "__main__":
    # Set current working directory
    base_dir = getcwd()
    main(base_dir)
