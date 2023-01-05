#!/bin/bash python3

import sys
from datetime import date
import pandas as pd
import numpy as np
import pyam
from argparse import ArgumentParser

# FILL IN DOCSTRINGS IN ALL CLASSES AND FUNCTIONS

class Lookups(object):
    """DOCSTRING
    """
    def __init__(self):
        """DOCSTRING
        """
        self.statename_to_abbr = {
            # Other
            'District of Columbia': 'DC',
            # States
            'Alabama': 'AL',
            'Alaska': 'AK',
            'Arizona': 'AZ',
            'Arkansas': 'AR',
            'California': 'CA',
            'Colorado': 'CO',
            'Connecticut': 'CT',
            'Delaware': 'DE',
            'Florida': 'FL',
            'Georgia': 'GA',
            'Hawaii': 'HI',
            'Idaho': 'ID',
            'Illinois': 'IL',
            'Indiana': 'IN',
            'Iowa': 'IA',
            'Kansas': 'KS',
            'Kentucky': 'KY',
            'Louisiana': 'LA',
            'Maine': 'ME',
            'Maryland': 'MD',
            'Massachusetts': 'MA',
            'Michigan': 'MI',
            'Minnesota': 'MN',
            'Mississippi': 'MS',
            'Missouri': 'MO',
            'Montana': 'MT',
            'Nebraska': 'NE',
            'Nevada': 'NV',
            'New Hampshire': 'NH',
            'New Jersey': 'NJ',
            'New Mexico': 'NM',
            'New York': 'NY',
            'North Carolina': 'NC',
            'North Dakota': 'ND',
            'Ohio': 'OH',
            'Oklahoma': 'OK',
            'Oregon': 'OR',
            'Pennsylvania': 'PA',
            'Rhode Island': 'RI',
            'South Carolina': 'SC',
            'South Dakota': 'SD',
            'Tennessee': 'TN',
            'Texas': 'TX',
            'Utah': 'UT',
            'Vermont': 'VT',
            'Virginia': 'VA',
            'Washington': 'WA',
            'West Virginia': 'WV',
            'Wisconsin': 'WI',
            'Wyoming': 'WY'}


def state_convert(df, conv):
    """DOCSTRING
    """

    # Extend data by replicating each row once for each state
    stdf = pd.DataFrame(np.repeat(df.values, len(conv.index), axis=0),
                        columns=df.columns)

    # Add state column with all states repeated for the number
    # of rows in the original array
    stdf['State'] = np.tile(conv.index, df.shape[0])

    # Identify year columns in data based on whether column header
    # string is a number
    try:
        year_cols = [col for col in stdf.columns if col.isdigit()]
    except AttributeError:
        year_cols = [col for col in stdf.columns if isinstance(col, int)]

    # Add column with the EMM to state conversion weight for that row
    stdf['wts'] = stdf.apply(lambda x: conv[x['Region']][x['State']], axis=1)

    # For each year column, update the values using the conversion weights
    for col in year_cols:
        stdf.loc[:, col] = stdf.loc[:, col].multiply(stdf.loc[:, 'wts'])

    # Drop columns no longer needed, rename state column 'Region'
    stdf = stdf.drop(['wts', 'Region'], axis=1)
    stdf = stdf.rename({'State': 'Region'}, axis=1)

    # Regroup data onto a state basis
    stdf = stdf.groupby(
        ['Model', 'Scenario', 'Region', 'Variable', 'Unit']).sum().reset_index()

    return stdf


def national_convert(df, emm_pop_wt):
    """DOCSTRING
    """

    # Identify rows in dataframe with price data
    price_bool_idx = df['Variable'].str.startswith('Price')

    # Calculate weighted average prices
    # Get dataframe with only price data
    price_df = df[price_bool_idx]
    # Add population weight columns
    price_df = price_df.merge(emm_pop_wt, left_on='Region', right_on='EMM')
    # Get year column indices (to be modified with the population weights)
    year_cols = price_df.columns[price_df.columns.str.startswith('20')]
    # Apply population weights to price data
    price_df[year_cols] = price_df[year_cols].multiply(price_df['Population Weight'], axis='index')
    # Calculate U.S. weighted average prices
    us_price_df = price_df.groupby(['Model', 'Variable', 'Unit', 'Scenario']).sum().reset_index()
    us_price_df = us_price_df.drop(us_price_df.columns[us_price_df.columns.str.contains('Population')], axis=1)
    # Add region column for the U.S.
    us_price_df['Region'] = 'United States'

    # Get dataframe with all data except for prices
    ot_df = df[~price_bool_idx]
    # Sum over regions to get national values
    ot_df = ot_df.groupby(['Model', 'Variable', 'Unit', 'Scenario']).sum().reset_index()
    # Add region column for U.S.
    ot_df['Region'] = 'United States'

    # Concat two dataframes
    df = pd.concat([ot_df, us_price_df], axis=0)

    return df


if __name__ == '__main__':
    # Import data file specified by user
    # python(3) iamc_file_restructure.py filename.csv
    df = pd.read_excel(sys.argv[1])

    # Import population-weighted EMM to state translation weights
    conv = pd.read_csv('supporting_data/convert_data/geo_map/EMM_State_RowSums.txt', sep='\t')
    conv = conv.set_index('State').transpose()
    conv.index.name = 'State'
    conv.columns.name = None

    # Import national EMM population weights
    emm_wt = pd.read_csv('supporting_data/convert_data/geo_map/EMM_National.txt', sep='\t')

    # Convert data from EMM regions to states, national totals
    stdf = state_convert(df, conv)
    usdf = national_convert(df, emm_wt)

    # Convert into an IAMC formatted dataframe
    df = pd.concat([usdf, stdf], axis=0)
    df_iamc = pyam.IamDataFrame(df)

    # Export as an Excel (XLSX) data file ready for upload
    # to the IIASA Scenario Explorer portal
    df_iamc.to_excel('emf_output/'+str(date.today())+'_data_IAMC_format.xlsx')

    # # Handle user arguments
    # parser = ArgumentParser()
    # # Optional flag to calculate site (rather than source) energy outputs
    # parser.add_argument('--national', action='store_true',
    #                     help='When true, process data as national sum')
    # parser.add_argument('-f', required=True,
    #                     help='Provide name of file to be ingested')
    # # Object to store all user-specified execution arguments
    # opts = parser.parse_args()

    # # Import data file specified by user
    # # python(3) iamc_file_restructure.py -f filename.xlsx
    # df = pd.read_excel(opts.f)

    # if not opts.national:
    #     # Import population-weighted EMM to state translation weights
    #     conv = pd.read_csv('supporting_data/convert_data/geo_map/EMM_State_RowSums.txt', sep='\t')
    #     conv = conv.set_index('State').transpose()
    #     conv.index.name = 'State'
    #     conv.columns.name = None

    #     # Convert data from EMM regions to states
    #     df = state_convert(df, conv)
    # else:
    #     df = national_convert(df)

    # # Convert into an IAMC formatted dataframe
    # df_iamc = pyam.IamDataFrame(df)

    # Export as an Excel (XLSX) data file ready for upload
    # # to the IIASA Scenario Explorer portal
    # if opts.national:
    #     geog_str = 'national'
    # else:
    #     geog_str = 'state'
    # fp = 'emf_output/'+str(date.today())+'_data_IAMC_format_'+geog_str+'.xlsx'
    # df_iamc.to_excel(fp)
