import os

# set working directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import pandas as pd

data = pd.read_csv("Res_TLoads_Base.csv")

# Components that appear twice (heat and cool) and should be suffixed accordingly
components = [
    "ROOF",
    "WALL",
    "WIND_SOL",
    "WIND_COND",
    "INFIL",
    "PEOPLE",
    "EQUIP",
    "GROUND",
    "TOTAL",
]

# Build new, unique, and semantically clear column names
counts = {c: 0 for c in components}
new_columns = []
for col in data.columns.tolist():
    base = col.split(".")[0]  # handle pandas duplicate suffixes like ".1"
    if base in counts:
        counts[base] += 1
        if counts[base] == 1:
            new_columns.append(f"{base}_HEAT")
        elif counts[base] == 2:
            new_columns.append(f"{base}_COOL")
        else:
            # Unexpected third+ occurrence; keep unique but marked
            new_columns.append(f"{base}_EXTRA{counts[base]}")
    else:
        new_columns.append(col)

data.columns = new_columns

CDIV_MAX = 9
BLDG_MAX = 3
EUSES = ["HEAT", "COOL"]


final_data = pd.DataFrame()

for cdiv in range(1, CDIV_MAX + 1):
    for bldg in range(1, BLDG_MAX + 1):
        for euse in EUSES:

            # Filter data for current combination
            subset = data[
                (data["CDIV"] == cdiv) & (data["BLDG"] == bldg)
            ]

            if euse == "HEAT":
                # filter column names with _HEAT
                subset = subset[[col for col in subset.columns if col.endswith("_HEAT") or col in ["CDIV", "BLDG", "NBLDGS"]]]
            else:
                # filter column names with _COOL
                subset = subset[[col for col in subset.columns if col.endswith("_COOL") or col in ["CDIV", "BLDG", "NBLDGS"]]]
            
            sum_bldgs = subset['NBLDGS'].sum()
            # print(f"Sum of nbldgs for CDIV {cdiv}, BLDG {bldg}, EUSE {euse}: {sum_bldgs}")

            final_data = pd.concat([final_data, pd.DataFrame({
                "CDIV": cdiv,
                "BLDG": bldg,
                "EUSE": euse,
                "SUM_NBLDGS": sum_bldgs
            }, index=[0])], ignore_index=True)

            row_weight = subset['NBLDGS'] / sum_bldgs if sum_bldgs > 0 else 0
            # weighted thermal components (compute scalar weighted averages per row)
            row_mask = (
                (final_data["CDIV"] == cdiv)
                & (final_data["BLDG"] == bldg)
                & (final_data["EUSE"] == euse)
            )
            for component in components:
                src_col = f"{component}_{euse}"
                if src_col in subset.columns:
                    weighted_value = (subset[src_col] * row_weight).sum() if sum_bldgs > 0 else 0
                    final_data.loc[row_mask, component] = weighted_value
                else:
                    # If the expected column is missing, set to 0 to avoid KeyError
                    final_data.loc[row_mask, component] = 0

            
            # normalize component shares (exclude TOTAL from normalization)
            share_components = [c for c in components if c != "TOTAL"]
            row_mask = (
                (final_data["CDIV"] == cdiv)
                & (final_data["BLDG"] == bldg)
                & (final_data["EUSE"] == euse)
            )
            row_total = final_data.loc[row_mask, share_components].sum(axis=1)
            if not row_total.empty and row_total.iloc[0] not in (0, None):
                final_data.loc[row_mask, share_components] = final_data.loc[row_mask, share_components].div(
                    row_total.values, axis=0
                )

print(final_data.head())