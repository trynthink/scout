"""Module for updating the state-level baseline data CSV file.

This module can be used to update the following file:
"EIA_State_Emissions_Prices_Baselines_{year}.csv"

The module gives users the option to specify a data update
year for which to query the EIA SEDS API to generate updated state-level
baseline generation, emissions, and prices data.
"""

import os
import sys
import argparse
from pathlib import Path
import pandas as pd
import requests
from urllib.parse import unquote
from scout.config import FilePaths as fp

# Constants
VALID_UPDATE_YEARS = ['2022', '2021', '2020', '2019', '2018', '2017', '2016', '2015']
DATA_SERIES_DICT = {
    'source-disposition': [
        'direct-use', 'net-interstate-trade', 'estimated-losses',
        'total-disposition', 'total-net-generation',
        'total-international-imports'
    ],
    'emissions-by-state-by-fuel': ['co2-thousand-metric-tons'],
    'retail-sales': ['price']
}
STATE_QUERY_STRING = (
    '&facets[state][]=AL&facets[state][]=AR&facets[state][]=AZ' +
    '&facets[state][]=CA&facets[state][]=CO&facets[state][]=CT' +
    '&facets[state][]=DC&facets[state][]=DE&facets[state][]=FL' +
    '&facets[state][]=GA&facets[state][]=IA&facets[state][]=ID' +
    '&facets[state][]=IL&facets[state][]=IN&facets[state][]=KS' +
    '&facets[state][]=KY&facets[state][]=LA&facets[state][]=MA' +
    '&facets[state][]=MD&facets[state][]=ME&facets[state][]=MI' +
    '&facets[state][]=MN&facets[state][]=MO&facets[state][]=MS' +
    '&facets[state][]=MT&facets[state][]=NC&facets[state][]=ND' +
    '&facets[state][]=NE&facets[state][]=NH&facets[state][]=NJ' +
    '&facets[state][]=NM&facets[state][]=NV&facets[state][]=NY' +
    '&facets[state][]=OH&facets[state][]=OK&facets[state][]=OR' +
    '&facets[state][]=PA&facets[state][]=RI&facets[state][]=SC' +
    '&facets[state][]=SD&facets[state][]=TN&facets[state][]=TX' +
    '&facets[state][]=UT&facets[state][]=VA&facets[state][]=VT' +
    '&facets[state][]=WA&facets[state][]=WI&facets[state][]=WV' +
    '&facets[state][]=WY'
)


def get_baseline_data_path():
    """Get the path to the existing state-level baseline data file."""
    files = list(Path(fp.CONVERT_DATA).glob(
        "EIA_State_Emissions_Prices_Baselines_*.csv"))
    baseline_data_file = files[0] if files else None
    return baseline_data_file


def get_api_key():
    """Get the EIA API key from environment variables."""
    api_key = os.environ.get('EIA_API_KEY')
    if not api_key:
        print(
            '\nExpected environment variable EIA_API_KEY not set.\n'
            'Obtain an API key from EIA at https://www.eia.gov/opendata/\n'
            'On a Mac, add the API key to your environment using the '
            'following command in Terminal (and then open a new window).\n'
            'For bash:\n'
            "$ echo 'export EIA_API_KEY=your api key' >> ~/.bash_profile\n"
            'For zsh:\n'
            "$ echo 'export EIA_API_KEY=your api key' >> ~/.zshrc\n"
        )
        sys.exit(1)
    return api_key


def generate_query_string(key, freq):
    """Generate the EIA API query string for a given data series key and
    frequency."""
    base_url = 'https://api.eia.gov/v2/electricity'
    query_params = {
        'source-disposition': {
            'url': f'{base_url}/state-electricity-profiles/{key}/data/',
            'frequency': freq[0],
            'data': [
                f'data[{i}]={field}'
                for i, field in enumerate(DATA_SERIES_DICT[key])
            ],
            'sort': '&sort[0][column]=state&start=2015&sort[0][direction]=asc'
                    '&offset=0&length=5000'
        },
        'emissions-by-state-by-fuel': {
            'url': f'{base_url}/state-electricity-profiles/{key}/data/',
            'frequency': freq[0],
            'data': [f'data[0]={DATA_SERIES_DICT[key][0]}'],
            'sort': '&sort[0][column]=stateid&start=2015&sort[0][direction]='
                    'asc&offset=0&length=5000'
        },
        'retail-sales': {
            'url': f'{base_url}/{key}/data/',
            'frequency': freq[0],
            'data': [f'data[0]={DATA_SERIES_DICT[key][0]}'],
            'sort': '&sort[0][column]=period&start=2015&sort[0][direction]='
                    'desc&offset=0&length=5000'
        }
    }

    params = query_params[key]
    query_str = (
        f"{params['url']}?frequency={params['frequency']}"
        f"&{'&'.join(params['data'])}"
        + (f"{STATE_QUERY_STRING.replace('state', 'stateid')}"
            if key != 'source-disposition'
            else STATE_QUERY_STRING)
        + f"{params['sort']}"
    )
    return query_str


def api_query(query_str, api_key):
    """Execute an EIA API query and return the response data."""
    response = requests.get(unquote(query_str) + '&api_key=' + api_key)
    response.raise_for_status()
    return response.json()['response']['data']


def clean_source_disposition_data(data):
    """Clean and process source disposition data."""
    df = pd.DataFrame(data)
    # select relevant columns
    df = df[['period', 'state', 'total-net-generation', 'net-interstate-trade',
             'direct-use', 'total-international-imports', 'estimated-losses']]
    # convert df columns except period and state to numeric
    df[df.columns[2:]] = df[df.columns[2:]].apply(pd.to_numeric)
    # calculate total disposition:
    # total disposition = total net generation + abs(net interstate trade) +
    # total international imports if net interstate trade < 0
    # else total disposition = total net generation +
    # total international imports
    # *only add the absolute value of net interstate trade if it is negative
    df['total_disposition'] = df.apply(lambda x: x['total-net-generation'] +
                                       abs(x['net-interstate-trade'] +
                                           x['total-international-imports'])
                                       if x['net-interstate-trade'] < 0 else
                                       x['total-net-generation'] +
                                       x['total-international-imports'],
                                       axis=1)
    # convert generation to TWh
    df['generation_twh'] = df['total-net-generation'] * 1e-6
    # calculate T&D loss factor as estimated losses / (total disposition -
    # direct use)
    df['TD_loss_factor'] = df['estimated-losses'] / (df['total_disposition'] -
                                                     df['direct-use'])
    df = df.rename(columns={'state': 'stateid'})
    return df


def clean_emissions_data(data):
    """Clean and process emissions data."""
    df = pd.DataFrame(data)
    # select relevant columns
    df = df[df['fuelid'] == 'ALL'][['period', 'stateid',
                                    'co2-thousand-metric-tons']]
    # convert columns to numeric and calculate CO2 emissions in MMT
    df[df.columns[2:]] = df[df.columns[2:]].apply(pd.to_numeric)
    df['co2_mmt'] = df['co2-thousand-metric-tons'] * 1e-3
    return df


def clean_retail_sales_data(data):
    """Clean and process retail sales data."""
    df = pd.DataFrame(data)
    # select residential and commercial electricity prices
    df = df[df['sectorid'].isin(['RES', 'COM'])]
    # convert to numeric
    df['price'] = df['price'].astype(float)
    # reshape data to wide format
    df = df.pivot(index=['period', 'stateid', 'stateDescription'],
                  columns='sectorName', values='price').reset_index()
    # select relevant columns
    df.columns = ['period', 'stateid', 'stateDescription', 'commercial',
                  'residential']
    df['period'] = pd.to_datetime(df['period'])
    # # resample from monthly to annual data (filling in missing monthly
    # # values with the last value) using the annual average
    # df = df.set_index('period').sort_index(ascending=True).ffill().groupby(
    #     ['stateid', 'stateDescription']).resample('YE').mean().reset_index()
    df['period'] = df['period'].dt.year.astype(str)
    # convert prices to $/kWh
    df[['residential', 'commercial']] = df[['residential', 'commercial']] / 100
    return df


def clean_and_aggregate_data(data_dict, year):
    """Clean and aggregate data from EIA API query results."""
    # load and clean data sets
    source_disp = clean_source_disposition_data(data_dict['source-disposition']
                                                )
    emissions = clean_emissions_data(data_dict['emissions-by-state-by-fuel'])
    retail_sales = clean_retail_sales_data(data_dict['retail-sales'])
    # merge data sets
    df = source_disp.merge(emissions, on=['period', 'stateid'], how='left')
    df = df.merge(retail_sales, on=['period', 'stateid'], how='left')
    # calculate emissions rate in Mt/TWh by dividing CO2 emissions by
    # generation (TWh) * (1 - T&D loss fraction)
    df['co2_int'] = df['co2_mmt'] / (df['generation_twh'] * (
        1 - df['TD_loss_factor']))
    # drop unnecessary columns and rename columns
    df = df.drop(columns=['co2-thousand-metric-tons', 'stateDescription'])
    df = df.rename(columns={
        'stateid': 'State',
        'period': 'Year',
        'generation_twh': 'Generation (TWh)',
        'co2_mmt': 'CO2 Emissions (MMT)',
        'co2_int': 'Emissions Rate (Mt/TWh)',
        'TD_loss_factor': 'T&D Loss Fraction',
        'estimated-losses': 'Estimated Losses (MWh)',
        'total_disposition': 'Total Disposition (MWh)',
        'direct-use': 'Direct Use (MWh)',
        'commercial': 'Commercial Electricity Price ($/kWh)',
        'residential': 'Residential Electricity Price ($/kWh)'
    })
    # sort data by year and state and select final columns for data output
    df = df.sort_values(by=['Year', 'State'], ascending=[False, True])
    df = df[['Year', 'State', 'Generation (TWh)', 'CO2 Emissions (MMT)',
             'Residential Electricity Price ($/kWh)',
             'Commercial Electricity Price ($/kWh)', 'Total Disposition (MWh)',
             'Direct Use (MWh)', 'Estimated Losses (MWh)',
             'T&D Loss Fraction', 'Emissions Rate (Mt/TWh)']]
    df = df[df['Year'] == year].reset_index(drop=True)
    return df


def main():
    """Main function to update the state-level baseline data file."""
    api_key = get_api_key()
    baseline_data_path = get_baseline_data_path()

    # Parse command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument('-y', '--year', choices=VALID_UPDATE_YEARS,
                        help="Desired year to update state-level data")
    parser.add_argument('-o', '--overwrite', action='store_true',
                        help="Overwrite existing state baseline data?")
    args = parser.parse_args()

    # Get year and overwrite preference from user input
    if args.year:
        year = args.year
    else:
        year = input(
            "Please specify the desired update year. Valid entries are: " +
            ', '.join(VALID_UPDATE_YEARS) +
            ".\n")
        if year not in VALID_UPDATE_YEARS:
            print('Invalid year entered.')
            sys.exit(1)
    if args.overwrite:
        overwrite = 'y'
        print(
            f'Existing state-level baseline data file found in the '
            f'convert_data directory: {baseline_data_path}'
        )
    else:
        if baseline_data_path:
            overwrite = input(
                'Would you like to overwrite this file? (y/n)\n'
            )
            if overwrite.lower() != 'y':
                print('Leaving existing baseline data file in place.')
        else:
            overwrite = 'n'

    # Query EIA API for data
    data_dict = {}
    for key in DATA_SERIES_DICT.keys():
        query_str = generate_query_string(key, ['annual', 'monthly'])
        data_dict[key] = api_query(query_str, api_key)
    # Clean and aggregate data
    df = clean_and_aggregate_data(data_dict, year)
    # Save data to CSV
    if baseline_data_path:
        output_path = str(baseline_data_path.parent) + \
            f'/EIA_State_Emissions_Prices_Baselines_{year}.csv'
    else:
        print(
                'No existing state-level baseline data file found in the '
                'convert_data directory. Creating new file.'
            )
        output_path = str(fp.CONVERT_DATA /
                          f'EIA_State_Emissions_Prices_Baselines_{year}.csv')
    if overwrite == 'y':
        os.remove(baseline_data_path)
        print('Existing state-level baseline data file overwritten.')
    df.to_csv(output_path, index=False)
    print(f'State-level baseline data updated for {year} and saved to {output_path}')


if __name__ == '__main__':
    main()
