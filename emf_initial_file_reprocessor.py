#!/usr/bin/env python

import pandas as pd
import numpy as np
from datetime import date
import re
import json
import gzip
# from collections import Counter  # FOR DIAGNOSTICS


def cleanup(df):
    """Clean up processed versions of ecm_results data

    remove unnecessary parameters from dataframe
    and fix up lighting in final energy reporting
    """

    # Remove all total CO2 emissions and rename "direct" CO2 emissions
    totco2_regex = '^Emissions\|.*\|(?:Direct|Indirect)$|^(?!Emissions).*'
    df = df[df['Variable'].str.contains(totco2_regex)]
    df['Variable'] = df.apply(lambda x: re.sub('\|Direct', '', x['Variable']), axis=1)
    # df = df[~df['Variable'].str.endswith('|Direct')]

    # Remove gas cooling
    gas_cool_regex = '^Final Energy\|Buildings\|.*\|Cooling\|Gas'
    df = df[~df['Variable'].str.contains(gas_cool_regex)]

    # Remove Final Energy|Buildings|<bldg class>\<end use> where
    # end use == Appliances, Cooling, Heating
    eu_regex = '^Final Energy\|Buildings\|.*\|(?:Appliances|Cooling|Heating)$'
    df = df[~df['Variable'].str.contains(eu_regex)]

    # Change Final Energy|Buildings|<bldg class>\Lighting to add \Electricity after
    # Change Final Energy|Buildings|<bldg class>|Other to add |Electricity after
    def_re = '^Final Energy\|Buildings\|(?:Residential|Commercial)\|(?:Lighting|Other)$'
    df['Variable'] = df.apply(lambda x: re_elec_fix(x['Variable'], def_re), axis=1)

    return df


def re_elec_fix(idx_str, regex):
    """Add |Electricity onto |Lighting and |Other final energy variables
    """
    if re.search(regex, idx_str):
        return idx_str + '|Electricity'
    else:
        return idx_str


def df_abs_values(base_df, results_df, sub_cols):
    """
    subtract savings from reference to get absolute energy and CO2 emissions
    """
    # Get the scenario
    scenario_str = np.unique(results_df.index.get_level_values('Scenario'))[0]

    # Combine the baseline and results dataframe
    df = base.merge(results_df, on=sub_cols, how='left', suffixes=['_base', '_results']).fillna(0)

    # For each YYYY_base column, subtract the YYYY_results column, and report out as YYYY column
    cols = df.columns[df.columns.str.endswith('_base')]
    for col in cols:
        year = col[:-5]  # get just YYYY
        df[year] = df[year+'_base'] - df[year+'_results']

    # Drop the _base and _results columns
    df = df.drop(df.columns[df.columns.str.endswith('_base')], axis=1)
    df = df.drop(df.columns[df.columns.str.endswith('_results')], axis=1)

    # Reinsert the scenario column and add it to the index
    df['Scenario'] = scenario_str
    df = df.set_index('Scenario', append=True)

    return df


def get_prices_electricity(elec_price_data, emm_regions, years_extr):
    """
    NEW
    """
    kWh_GJ_conv = 1e6/3600  # convert from kWh to GJ
    USD_pres_val_conv = 1/1.023  # convert from 2019 to 2018 dollars (Scout data are in US$2019 not US$2018)
    df = pd.DataFrame()  # allocate empty DataFrame
    for emm in emm_regions:
        for bldg_class in ['residential', 'commercial']:
            # get and reshape intended electricity price data
            elec_pr = elec_price_data['End-use electricity price']['data'][bldg_class][emm]
            elec_extr = pd.DataFrame.from_dict(elec_pr, orient='index').loc[years_extr].transpose()

            # unit conversion
            elec_extr = elec_extr*USD_pres_val_conv*kWh_GJ_conv

            # dataframe index column addition
            var_constr = 'Price|Final Energy|' + bldg_class.title() + '|Electricity'
            elec_extr[['Model', 'Region', 'Variable', 'Unit']] = ['Scout v0.8', emm, var_constr, 'US$2018/GJ']

            # add to constructed dataframe
            df = pd.concat([df, elec_extr], axis=0)

    return df


def get_prices_gas_oil(petro_price_data, emm_regions, years_extr):
    """
    NEW
    """
    MMBtu_to_GJ = 1.055056  # convert from MMBtu to GJ
    USD_pres_val_conv = 1/1.023/1.04  # convert from 2020 to 2018 dollars (Scout data are in US$2020 not US$2018)
    df = pd.DataFrame()  # allocate empty DataFrame
    for emm in emm_regions:
        for bldg_class in ['residential', 'commercial']:
            # get and reshape intended price data
            gas_pr = petro_price_data['natural gas']['price']['data'][bldg_class]
            oil_pr = petro_price_data['distillate']['price']['data'][bldg_class]
            gas_extr = pd.DataFrame.from_dict(gas_pr, orient='index').loc[years_extr].transpose()
            oil_extr = pd.DataFrame.from_dict(oil_pr, orient='index').loc[years_extr].transpose()

            # unit conversion
            gas_extr = gas_extr*USD_pres_val_conv*MMBtu_to_GJ
            oil_extr = oil_extr*USD_pres_val_conv*MMBtu_to_GJ

            # dataframe index column addition
            gas_var_constr = 'Price|Final Energy|' + bldg_class.title() + '|Gas'
            oil_var_constr = 'Price|Final Energy|' + bldg_class.title() + '|Oil'
            gas_extr[['Model', 'Region', 'Variable', 'Unit']] = ['Scout v0.8', emm, gas_var_constr, 'US$2018/GJ']
            oil_extr[['Model', 'Region', 'Variable', 'Unit']] = ['Scout v0.8', emm, oil_var_constr, 'US$2018/GJ']

            # add to constructed dataframe
            df = pd.concat([df, gas_extr, oil_extr], axis=0)

    return df


def get_areas(baseline_dict, emm_regions, years_extr):
    """
    NEW
    """
    Msqft_to_Mm2 = 0.092903  # convert from million sqft (Scout baseline) to million m^2
    com_bldg = ['assembly', 'education', 'food sales', 'food service', 
                'health care', 'lodging', 'large office', 'small office', 'mercantile/service', 'warehouse', 'other']
    res_bldg = ['single family home', 'multi family home', 'mobile home']

    df = pd.DataFrame()  # allocate empty DataFrame

    for emm in emm_regions:
        # get commercial floor area
        com_df = pd.DataFrame()  # allocate temporary empty DataFrame
        for com in com_bldg:
            com_df = pd.concat([com_df, pd.DataFrame.from_dict(baseline_dict[emm][com]['total square footage'], orient='index').loc[years_extr]], axis=1)
        com_df = com_df.sum(axis=1).to_frame().transpose()*Msqft_to_Mm2  # collapse square footage values into single row

        # get residential floor area
        res_df = pd.DataFrame()  # allocate temporary empty DataFrame
        for res in res_bldg:
            res_df = pd.concat([res_df, pd.DataFrame.from_dict(baseline_dict[emm][res]['total square footage'], orient='index').loc[years_extr]], axis=1)
        res_df = res_df.sum(axis=1).to_frame().transpose()*Msqft_to_Mm2  # collapse square footage values into single row

        # calculate total floor area
        tot_df = res_df + com_df

        # add index columns to dataframes
        res_var = 'Energy Service|Floor Space|Residential|Value'
        com_var = 'Energy Service|Floor Space|Commercial|Value'
        tot_var = 'Energy Service|Floor Space|Buildings|Value'
        res_df[['Model', 'Region', 'Variable', 'Unit']] = ['Scout v0.8', emm, res_var, 'million m2']
        com_df[['Model', 'Region', 'Variable', 'Unit']] = ['Scout v0.8', emm, com_var, 'million m2']
        tot_df[['Model', 'Region', 'Variable', 'Unit']] = ['Scout v0.8', emm, tot_var, 'million m2']

        # add to constructed dataframe
        df = pd.concat([df, res_df, com_df, tot_df], axis=0)

    return df


def df_static_comb(df, pfa_df, index_cols):
    """
    NEW - combine price and floor area data with each scenario and baseline dataframe
    """
    # get scenario from df
    scenario_str = np.unique(df.index.get_level_values('Scenario'))[0]

    # add scenario to price and floor area dataframe and set multiindex to match df
    pfa_df['Scenario'] = scenario_str
    pfa_df = pfa_df.set_index(index_cols)

    # concatenate energy and CO2 emissions data with price and floor area data
    df = pd.concat([df, pfa_df], axis=0)

    return df


def results_df_reprocessor(base_df, df, index_cols, sub_cols, pfa_df):
    """
    NEW
    """
    # Clean up ecm_results
    df = cleanup(df)

    # Set MultiIndex for DataFrame
    df = df.set_index(index_cols)

    # Calculate absolute energy and CO2 emissions
    df = df_abs_values(base_df, df, sub_cols)

    # Combine energy and CO2 emissions data with energy price and
    # building floor area data to create complete tables for the
    # baseline and each scenario included
    df = df_static_comb(df, pfa_df, index_cols)

    return df


if __name__ == '__main__':
    # Specify paths for energy price and floor area source data files
    base_path = './'
    oil_gas_path = 'supporting_data/convert_data/site_source_co2_conversions.json'
    elec_path = 'supporting_data/convert_data/emm_region_emissions_prices.json'
    floor_area_path = 'supporting_data/stock_energy_tech_data/mseg_res_com_emm.gz'

    # Import energy price and floor area source data files
    oil_gas_prices = json.load(open(base_path + oil_gas_path, 'r'))
    elec_prices = json.load(open(base_path + elec_path, 'r'))
    floor_area = json.loads(gzip.open(base_path + floor_area_path).read().decode('utf-8'))

    # Specify columns for indexing all imported data
    index_cols = ['Model', 'Region', 'Variable', 'Unit', 'Scenario']
    sub_cols = index_cols[:-1]

    # Import files output from emf_aggregation.py
    base = pd.read_csv('emf_output/baseline_emf_aggregation_wide_mod.csv')
    s1 = pd.read_csv('emf_output/ecm_results_1-1_emf_aggregation_wide_mod.csv')
    s2 = pd.read_csv('emf_output/ecm_results_2_emf_aggregation_wide_mod.csv')
    s3 = pd.read_csv('emf_output/ecm_results_3-1_emf_aggregation_wide_mod.csv')

    # Remove extraneous rows from baseline and modify CO2 emissions
    # to report direct emissions without the 'Direct' tag (and drop
    # the total direct + indirect emissions values)
    totco2_regex = '^Emissions\|.*\|(?:Direct|Indirect)$|^(?!Emissions).*'
    base = base[base['Variable'].str.contains(totco2_regex)]
    base['Variable'] = base.apply(lambda x: re.sub('\|Direct', '', x['Variable']), axis=1)
    base = base[~base['Variable'].str.endswith('|Cooling|Gas')]

    # Set MultiIndex for baseline
    base = base.set_index(index_cols)

    # Specify years of price and floor area data to extract
    years_to_keep = [str(yr) for yr in range(2019, 2051) if yr%5 == 0]

    # Define iterable (numpy array) of EMM region name strings
    emm_region_array = np.unique(base.index.get_level_values('Region'))

    # Get electricity and fossil fuel retail prices
    elec_df = get_prices_electricity(elec_prices, emm_region_array, years_to_keep)
    petro_df = get_prices_gas_oil(oil_gas_prices, emm_region_array, years_to_keep)

    # Get building floor areas
    areas_df = get_areas(floor_area, emm_region_array, years_to_keep)

    price_floor_area_df = pd.concat([elec_df, petro_df, areas_df])

    # Combine energy and CO2 emissions data with energy price and
    # building floor area data to create complete tables for the
    # baseline
    basez = df_static_comb(base, price_floor_area_df, index_cols)

    # Restructure the ecm_results data
    s1z = results_df_reprocessor(base, s1, index_cols, sub_cols, price_floor_area_df)
    s2z = results_df_reprocessor(base, s2, index_cols, sub_cols, price_floor_area_df)
    s3z = results_df_reprocessor(base, s3, index_cols, sub_cols, price_floor_area_df)

    # Merge all dataframes together into a single dataframe
    comb_data = pd.concat([basez, s1z, s2z, s3z])

    # Export resulting combined dataframe
    comb_data.reset_index().to_excel('emf_output/final_aggregation_' + str(date.today()) + '.xlsx', index=False)
