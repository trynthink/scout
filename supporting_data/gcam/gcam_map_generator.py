#!/usr/bin/env python3
import pandas as pd
import json


def remove_duplicates_from_dict(d):
    """Remove duplicates from dictionary"""
    for key, value in d.items():
        if isinstance(value, list):
            d[key] = list(set(value))
    return d


def replace_nan_with_null_in_dict(d):
    """Replace NAN with null in dictionary"""
    for key, value in d.items():
        if isinstance(value, dict):
            replace_nan_with_null_in_dict(value)
        elif isinstance(value, list):
            for i in range(len(value)):
                if value[i] == "nan":
                    value[i] = None
                elif isinstance(value[i], dict):
                    replace_nan_with_null_in_dict(value[i])
        elif value == "nan":
            d[key] = None
    return d


def move_none_to_start(d):
    for key, value in d.items():
        if isinstance(value, list):
            none_values = [v for v in value if v is None]
            other_values = [v for v in value if v is not None]
            d[key] = none_values + other_values
    return d


def process_mapping(df, col1, col2, additional_processing=None):
    """Process mapping as basis"""
    if additional_processing:
        additional_processing(df)
    mapping = df[[col1, col2]].copy()
    mapping[col2] = mapping[col2].str.split(',')
    exploded_mapping = mapping.explode(col2).reset_index(drop=True)
    exploded_mapping[col2] = exploded_mapping[col2].str.strip()
    grouped_mapping = \
        exploded_mapping.groupby(col1)[col2].apply(list).reset_index()
    mapping_json = grouped_mapping.set_index(col1)[col2].to_dict()
    return move_none_to_start(
        replace_nan_with_null_in_dict(
            remove_duplicates_from_dict(mapping_json)))


def eu_additional_processing(df):
    """Additional mapping to include End Use"""
    df.loc[df['scout_enduse'] == 'refrigeration', 'scout_enduse'] = \
        df['scout_enduse'].astype(str) + ',' + df['building_type']


def tech_additional_processing(df):
    """Additional mapping to include Tech"""
    df['scout_tech'] = df['scout_tech'].astype(str) + ',' + \
        df['scout_enduse'] + ',' + df['scout_fuel']


def main():
    df = pd.read_csv('scout_gcam_map.csv')
    fuel_mapping_json = process_mapping(df, 'gcam_subsector', 'scout_fuel')
    eu_mapping_json = process_mapping(
        df, 'gcam_supplysector', 'scout_enduse', eu_additional_processing(df))
    tech_mapping_json = process_mapping(
        df, 'gcam_tech', 'scout_tech', tech_additional_processing(df))

    mapping_json = {
        "bldg": {
            "resid": [
                "single family home",
                "multi family home",
                "mobile home"
            ],
            "comm": [
                "assembly",
                "education",
                "food sales",
                "food service",
                "health care",
                "lodging",
                "large office",
                "small office",
                "mercantile/service",
                "warehouse",
                "other"
            ],
        },
        "fuel": fuel_mapping_json,
        "end_use": eu_mapping_json,
        "tech": tech_mapping_json
    }

    json_file_path = "../convert_data/gcam_map.json"
    with open(json_file_path, 'w') as json_file:
        json.dump(mapping_json, json_file, indent=4)

    print("Complete")


if __name__ == "__main__":
    main()
