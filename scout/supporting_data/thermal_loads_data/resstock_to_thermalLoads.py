'''
ResStock to Scout Thermal Loads Converter

This script processes ResStock Building Energy Simulation Outputs
and converts them into thermal loads component data formatted for
use in Scout's building energy analysis tool.

The conversion steps:
1. Create maps for ResStock building characteristics to categories as used in Scout.
2. Aggregate thermal load components by census division, building type, and end use.
3. Compute weighted average based on ResStock sample weights.
4. Normalize component loads as fractions of total thermal load.

Output format:
Tab seperated text file with columns:
- ENDUSE: 'HT' for heating, 'CL' for cooling
- CDIV: Census Division code (1-9)
- BLDG: Building type code (1: single family, 2: multi family, 3: mobile home)
- NBLDGS: Number of buildings represented
- Component fractions: WIND_COND, WIND_SOL, ROOF, WALL, INFIL, PEOPLE, GRND, EQUIP
'''

import pandas as pd

CDIV_MAX = 9
BLDG_MAX = 3
EUSES = ["HEAT", "COOL"]

# Segment -> category aggregation (intermediate keys)
RESSTOCK_SEGMENT_TO_CATEGORY = {
    # Windows / skylights
    "windows_conduction": "WIND_COND",
    "skylights_conduction": "WIND_COND",
    "windows_solar": "WIND_SOL",
    "skylights_solar": "WIND_SOL",
    # Roof / ceilings
    "roofs": "ROOF",
    "ceilings": "ROOF",
    # Walls / opaque
    "walls": "WALL",
    "foundation_walls": "WALL",
    "rim_joists": "WALL",
    "doors": "WALL",
    # Infiltration / ventilation
    "infiltration": "INFIL",
    "mechanical_ventilation": "INFIL",
    "natural_ventilation": "INFIL",
    # Ground contact
    "slabs": "GRND",
    "floors": "GRND",
    # Internal/equipment gains
    "internal_gains": "EQUIP",
    "internal_mass": "EQUIP",
    "lighting": "EQUIP",
    "whole_house_fan": "EQUIP",
    "ducts": "EQUIP",
}

CDIV_MAPPING = {
    "new england": 1,
    "middle atlantic": 2,
    "east north central": 3,
    "west north central": 4,
    "south atlantic": 5,
    "east south central": 6,
    "west south central": 7,
    "mountain": 8,
    "pacific": 9,
}

BLDG_MAPPING = {
    "50 or more Unit": "multi family home",
    "Single-Family Detached": "single family home",
    "Single-Family Attached": "single family home",
    "Mobile Home": "mobile home",
    "20 to 49 Unit": "multi family home",
    "5 to 9 Unit": "multi family home",
    "3 or 4 Unit": "multi family home",
    "2 Unit": "multi family home",
    "10 to 19 Unit": "multi family home",
    "nan": None,
}

BLDG_CODE = {
    "single family home": 1,
    "multi family home": 2,
    "mobile home": 3,
}

EUSES = ["HEAT", "COOL"]


def map_to_resstock(df):
    """Convert ResStock output dataframe to format suitable for thermal loads processing"""

    # Create NBLDGS column from sample weight
    weight_column = df["build_existing_model.sample_weight"]
    df["NBLDGS"] = weight_column
    print("Number of None in BLDG:", df["NBLDGS"].isna().sum())

    # Map building types and census divisions to codes
    df["BLDG"] = df["build_existing_model.geometry_building_type_acs"].map(BLDG_MAPPING)
    df["BLDG"] = df["BLDG"].map(BLDG_CODE)
    unique_cdivs = df["build_existing_model.census_division"].unique()
    print("Unique census divisions:", unique_cdivs)
    df["CDIV"] = (
        df["build_existing_model.census_division"].str.lower().map(CDIV_MAPPING)
    )

    print("Length before dropping NAs:", len(df))
    return df


def convert_to_thermalLoads(data: pd.DataFrame) -> pd.DataFrame:
    """Convert ResStock data to Scout thermal loads format

    This function aggregates ResStock thermal load segments into
    Scout thermal load categories, computes weighted averages based
    on the number of buildings represented, and normalizes the results
    to fractions of total thermal load.

    Parameters:
        data (pd.DataFrame): Input DataFrame containing ResStock simulation outputs with
                             the added following required columns:
            - 'CDIV': Census Division code (1-9)
            - 'BLDG': Building type code (1: single family, 2: multi
                        family, 3: mobile home)
            - 'NBLDGS': Number of buildings represented by each row

    Returns:
        pd.DataFrame: DataFrame formatted for Scout thermal loads with columns:
            - 'ENDUSE': 'HT' for heating, 'CL' for cooling
            - 'CDIV': Census Division code
            - 'BLDG': Building type code
            - 'NBLDGS': Number of buildings represented
            - Component fractions: WIND_COND, WIND_SOL, ROOF, WALL, INFIL,
              PEOPLE, GRND, EQUIP

    Process:
        1. Iterate over all combinations of CDIV, BLDG, and EUSE.
        2. For each combination, filter the data and compute weighted sums
           for each thermal load category based on the number of buildings.
        3. Normalize the component loads to fractions of total thermal load.
        4. Compile results into a final DataFrame.
    """
    # Local accumulator for results to avoid relying on a global and fix F823
    final_data = pd.DataFrame()

    categories = sorted(set(RESSTOCK_SEGMENT_TO_CATEGORY.values()))
    if "PEOPLE" not in categories:
        categories.append("PEOPLE")

    for cdiv in range(1, CDIV_MAX + 1):
        for bldg in range(1, BLDG_MAX + 1):
            for euse in EUSES:
                subset = data[(data["CDIV"] == cdiv) & (data["BLDG"] == bldg)]

                # Determine internal end-use selector and output label
                euse_lower = "heating" if euse == "HEAT" else "cooling"
                output_enduse = "HT" if euse == "HEAT" else "CL"
                keep_cols = [
                    c
                    for c in subset.columns
                    if (
                        "component_load_" + euse_lower in str(c).lower()
                        or c in ["CDIV", "BLDG", "NBLDGS"]
                    )
                ]
                subset = subset[keep_cols]

                # Compute weights and prepare a category accumulator
                sum_bldgs = subset["NBLDGS"].sum()
                # Per-row weight; if sum is zero, set weight to 0 (vector of zeros via broadcasting)
                row_weight = subset["NBLDGS"] / sum_bldgs if sum_bldgs > 0 else 0.0

                # Accumulate weighted totals per category in this dict
                cat_weighted = {cat: 0.0 for cat in categories}
                cat_weighted["PEOPLE"] = 0.0

                for segment, category in RESSTOCK_SEGMENT_TO_CATEGORY.items():
                    seg_cols = [
                        col
                        for col in subset.columns
                        if ("component_load_" + euse_lower in str(col).lower())
                        and (segment in str(col).lower())
                    ]

                    # Row-wise sum across all matched segment columns
                    seg_row_sum = subset[seg_cols].sum(axis=1)
                    seg_weighted_value = float((seg_row_sum * row_weight).sum())
                    cat_weighted[category] += seg_weighted_value

                final_data = pd.concat(
                    [
                        final_data,
                        pd.DataFrame(
                            {
                                "CDIV": cdiv,
                                "BLDG": bldg,
                                "ENDUSE": output_enduse,
                                "NBLDGS": sum_bldgs,
                            },
                            index=[0],
                        ),
                    ],
                    ignore_index=True,
                )

                # weighted thermal components (compute scalar weighted averages per row)
                row_mask = (
                    (final_data["CDIV"] == cdiv)
                    & (final_data["BLDG"] == bldg)
                    & (final_data["ENDUSE"] == output_enduse)
                )

                for cat, val in cat_weighted.items():
                    final_data.loc[row_mask, cat] = val

                # Normalize to shares (fractions of total)
                share_components = [c for c in categories if c != "TOTAL"]

                # Sum across share components for just this row (Series of length 1)
                row_total = final_data.loc[row_mask, share_components].sum(axis=1)

                # Normalize only if positive (avoid divide-by-zero)
                if not row_total.empty and float(row_total.iloc[0]) != 0:
                    final_data.loc[row_mask, share_components] = final_data.loc[
                        row_mask, share_components
                    ].div(row_total.values, axis=0)

    # Save to CSV with tab separator and txt extension
    # Reorder columns to match original file
    desired_order = [
        "ENDUSE",
        "CDIV",
        "BLDG",
        "NBLDGS",
        "WIND_COND",
        "WIND_SOL",
        "ROOF",
        "WALL",
        "INFIL",
        "PEOPLE",
        "GRND",
        "EQUIP",
    ]

    # Ensure all desired columns exist (create if missing)
    for col in desired_order:
        if col not in final_data.columns:
            final_data[col] = 0.0

    # Select and reorder
    final_data = final_data[desired_order].copy()

    # Round numeric columns to 4 decimal places
    numeric_cols = final_data.select_dtypes(include=["number"]).columns
    final_data[numeric_cols] = final_data[numeric_cols].round(4)

    return final_data


def main():
    df = pd.read_csv(
        "scout/supporting_data/thermal_loads_data/results_up00_update.csv",
        low_memory=False,
    )
    df = map_to_resstock(df)
    final_data = convert_to_thermalLoads(df)
    final_data.to_csv(
        "scout/supporting_data/thermal_loads_data/Res_TLoads_Final.txt",
        sep="\t",
        index=False,
    )
    print("Conversion complete! Output saved to Res_TLoads_Final.txt")


if __name__ == "__main__":

    main()
