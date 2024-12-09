import pandas as pd
import json


def load_and_preprocess_data():
    # Load energy and stock data
    panel_shares_energy = pd.read_csv(
        'least_cost_energy_weighted_share_by_panel_outcome_census_division_case_mod_top_3.csv').\
        drop(columns=['Unnamed: 0'])
    panel_shares_stock = pd.read_csv(
        'least_cost_building_count_share_by_panel_outcome_census_division_case_mod_top_3.csv').\
        drop(columns=['Unnamed: 0'])

    # Rename columns and assign units
    panel_shares_energy = panel_shares_energy.rename(
        columns={'energy_mbtu': 'value'}).assign(units='mbtu')
    panel_shares_stock = panel_shares_stock.rename(
        columns={'building_count': 'value'}).assign(units='housing_units')

    # Combine energy and stock data
    panel_shares = pd.concat([panel_shares_energy, panel_shares_stock], axis=0)

    return panel_shares


def process_panel_shares(panel_shares):
    # Query panels data for different cases
    low = panel_shares.query('case == 1')
    med = panel_shares.query('case == 9')
    high = panel_shares.query('case == 18')
    full = pd.concat([low, med, high])

    # Update outcome column
    full['outcome'] = full['outcome'].replace({
        'management': 'panel management',
        'no_management': 'no panel management',
        'replacement': 'panel replacement'
    })

    # Update region column
    full['build_existing_model.census_division'] = \
        full['build_existing_model.census_division'].replace(
        'Middle Atlantic', 'mid atlantic')

    # Group and sum values
    full_upd = full.groupby([
        'build_existing_model.census_division', 'case_name', 'case', 'share_type', 'outcome'])[
        'value'].sum().reset_index()
    # Ensure all outcomes exist for each combination
    full_upd = full_upd.set_index([
        'build_existing_model.census_division',
        'case_name', 'case', 'share_type', 'outcome']).unstack().stack(
        'outcome', future_stack=True).fillna(0).reset_index()
    # Recalculate outcome shares; note that they are share across all cases within each CDIV
    full_upd['outcome_share'] = full_upd.groupby([
        'build_existing_model.census_division', 'share_type'])['value'].transform(
        lambda x: x / x.sum())
    # Update share_type values
    full_upd['share_type'] = full_upd['share_type'].replace(
        {'building_count': 'stock', 'energy_weighted': 'energy'})
    # Rename columns and map case to resstock_upgrade
    full_upd = full_upd.rename(
        columns={'build_existing_model.census_division': 'cdiv'})
    full_upd['resstock_upgrade'] = full_upd['case'].map({
        1: 'low efficiency upgrade',
        9: 'moderate efficiency upgrade',
        18: 'high efficiency upgrade'
    })

    return full_upd


def save_processed_data(full_upd):
    # # Save to CSV
    # full_upd[[
    #     'cdiv', 'resstock_upgrade', 'share_type', 'outcome', 'outcome_share']].to_csv(
    #         'panel_solution_shares.csv', index=False)

    # Prepare data for JSON conversion
    panel_dict = full_upd.set_index([
        'cdiv', 'resstock_upgrade', 'share_type', 'outcome']).reset_index()
    panel_dict['cdiv'] = panel_dict['cdiv'].str.lower()

    # Set categorical data
    panel_dict['cdiv'] = pd.Categorical(panel_dict['cdiv'], categories=[
        'new england', 'mid atlantic', 'east north central', 'west north central',
        'south atlantic', 'east south central', 'west south central', 'mountain', 'pacific'
    ])
    panel_dict['resstock_upgrade'] = pd.Categorical(panel_dict['resstock_upgrade'], categories=[
        'low efficiency upgrade', 'moderate efficiency upgrade', 'high efficiency upgrade'
    ])
    panel_dict['outcome'] = pd.Categorical(panel_dict['outcome'], categories=[
        'no panel management', 'panel replacement', 'panel management'
    ])

    panel_dict.sort_values(['cdiv', 'share_type', 'resstock_upgrade', 'outcome'], inplace=True)

    # Create nested dictionary
    result = {}
    for _, row in panel_dict.iterrows():
        census_division = row['cdiv']
        share_type = row['share_type']
        ee_upgrade = row['resstock_upgrade']
        panel_outcome = row['outcome']
        outcome_share = row['outcome_share']

        result.setdefault(
            census_division, {}).setdefault(share_type, {}).setdefault(
            ee_upgrade, {})[panel_outcome] = outcome_share

    # Save to JSON
    with open('panel_solution_shares.json', 'w') as file:
        json.dump(result, file, indent=2)


def main():
    panel_shares = load_and_preprocess_data()
    full_upd = process_panel_shares(panel_shares)
    save_processed_data(full_upd)


if __name__ == "__main__":
    main()
