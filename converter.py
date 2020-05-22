#!/usr/bin/env python3

"""Module for updating the conversion factors and prices JSON database.

This module updates the electricity site-source conversion factors and
CO2 intensities and prices for electricity, natural gas, and "other"
fuel stored in a JSON database. This module uses the EIA API to pull
the required data and automate this process without first downloading
AEO data tables.

This module leaves intact any data in the JSON from years prior to
the first year of available data for a particular AEO requested. For
example, if AEO 2018 is requested, the first year of available data
is 2016, so data already present in the conversions JSON file for
years prior to 2016 would remain unchanged by this function.
"""

import requests
import os
import sys
import numpy as np
import json
import argparse
from collections import OrderedDict


class UsefulVars(object):
    """Class of variables that are handy to have widely available.

    Attributes:
        conv_file (str): Relative path from main scout directory to
            conversions JSON file.
        conv_file_out (str): Relative path from main scout directory
            to location for writing newly updated conversions data.
    """
    def __init__(self):
        self.conv_file = ('supporting_data/convert_data/' +
                          'site_source_co2_conversions.json')
        self.conv_file_out = ('supporting_data/convert_data/' +
                              'site_source_co2_conversions-new.json')


class ValidQueries(object):
    """Define valid query options for AEO data requested via the EIA data API

    Attributes:
        years (list): A list of valid AEO report years for which this
            module has been evaluated to work.
        cases (list): A list of valid AEO cases investigated with NEMS,
            specified with the strings employed by the API.
    """
    def __init__(self):
        self.years = ['2018', '2019', '2020']
        self.cases = ['REF2018', 'REF2019', 'REF2020', 'CO2FEE25']


class EIAQueryData(object):
    """Reference strings for obtaining required data from EIA AEO

    Attributes:
        data_series (list): API key strings to obtain the desired data
            from the EIA AEO for the scenario and AEO release year
            specified by the user.
        data_names (list): A list of strings to use as keys for the
            data pulled from the AEO and added to a dict.
    """
    def __init__(self, yr, scen):
        self.data_series = [
            'AEO.'+yr+'.'+scen+'.CNSM_NA_ELEP_NA_HYD_CNV_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_NA_ELEP_NA_GEOTHM_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_NA_ELEP_NA_SLR_THERM_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_NA_ELEP_NA_SLR_PHTVL_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_NA_ELEP_NA_WND_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_ALLS_NA_ELC_DELV_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_ALLS_NA_ERL_DELV_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_RESD_NA_ELC_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_RESD_NA_ERL_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_COMM_NA_ERL_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_COMM_NA_ELC_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.EMI_CO2_RESD_NA_ELC_NA_NA_MILLMETNCO2.A',
            'AEO.'+yr+'.'+scen+'.EMI_CO2_COMM_NA_ELC_NA_NA_MILLMETNCO2.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_RESD_NA_ELC_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_COMM_NA_ELC_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_RESD_NA_NG_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_COMM_NA_NG_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.EMI_CO2_RESD_NA_NG_NA_NA_MILLMETNCO2.A',
            'AEO.'+yr+'.'+scen+'.EMI_CO2_COMM_NA_NG_NA_NA_MILLMETNCO2.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_RESD_NA_NG_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_COMM_NA_NG_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_RESD_NA_LFL_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.EMI_CO2_RESD_NA_PET_NA_NA_MILLMETNCO2.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_COMM_NA_LFL_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.EMI_CO2_COMM_NA_PET_NA_NA_MILLMETNCO2.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_COMM_NA_CL_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.EMI_CO2_COMM_NA_CL_NA_NA_MILLMETNCO2.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_RESD_NA_PROP_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_RESD_NA_DFO_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_RESD_NA_PROP_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_RESD_NA_DFO_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_COMM_NA_PROP_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_COMM_NA_DFO_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.PRCE_REAL_COMM_NA_RFL_NA_NA_Y13DLRPMMBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_COMM_NA_PROP_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_COMM_NA_DFO_NA_NA_QBTU.A',
            'AEO.'+yr+'.'+scen+'.CNSM_ENU_COMM_NA_RFO_NA_NA_QBTU.A']

        self.data_names = [
            'elec_renew_hydro',
            'elec_renew_geothermal',
            'elec_renew_solar_thermal',
            'elec_renew_solar_pv',
            'elec_renew_wind',
            'elec_tot_energy_site',
            'elec_tot_energy_loss',
            'elec_res_energy_site',
            'elec_res_energy_loss',
            'elec_com_energy_site',
            'elec_com_energy_loss',
            'elec_res_co2',
            'elec_com_co2',
            'elec_res_price',
            'elec_com_price',
            'ng_res_energy',
            'ng_com_energy',
            'ng_res_co2',
            'ng_com_co2',
            'ng_res_price',
            'ng_com_price',
            'petro_res_energy',
            'petro_res_co2',
            'petro_com_energy',
            'petro_com_co2',
            'coal_com_energy',
            'coal_com_co2',
            'lpg_res_price',
            'distl_res_price',
            'lpg_res_energy',
            'distl_res_energy',
            'lpg_com_price',
            'distl_com_price',
            'rsid_com_price',
            'lpg_com_energy',
            'distl_com_energy',
            'rsid_com_energy']


def api_query(api_key, series_id):
    """Execute an EIA API query and extract the data returned

    Execute a query of the EIA API and extract the data from the
    structure returned by the API.

    Args:
        api_key (str): EIA API key.
        series_id (str): Identifying string for a specific data series.

    Returns:
        A nested list of data with inner lists structured as
        [year string, data value].
    """
    query_str = ('https://api.eia.gov/series/?series_id=' + series_id +
                 '&api_key=' + api_key)
    data = requests.get(query_str).json()
    try:
        data = data['series'][0]['data']
    # If an invalid series_id is used, the 'series' key will not be present
    except KeyError:
        print('\nSeries ID not available from API: ' + series_id)
    return data


def data_processor(data):
    """Restructure the data obtained from the API into numpy arrays

    Args:
        data (list): A list of data, with each value a list where
            the first value is the year as a string and the second
            value is the number for that year for the data requested.

    Returns:
        Two numpy arrays, one containing the data and one containing
        the years corresponding to those data. Both arrays are sorted
        according to ascending year order.
    """
    years, data = zip(*data)
    years = np.array(years)
    data = np.array(data)[years.argsort()]  # Re-sort in ascending year order
    years = years[years.argsort()]  # Re-sort to be in ascending year order
    return data, years


def data_getter(api_key, series_names, api_series_list):
    """Get data from EIA using their data API and store in dict

    Call the required functions to obtain data from EIA using their
    data API, restructure the data into numpy arrays, and store in
    a dict according to the specified series names for later recall.

    Args:
        api_key (str): EIA API key.
        series_names (list): List of strings for the desired keys
            to use for the data in the dict.
        api_series_list (list): List of series strings to indicate
            the desired data from the EIA API call.

    Returns:
        Dict with keys specified in series_names for which the
        values correspond to the numpy arrays of data obtained from
        the EIA API for the series indicated in api_series_list.
    """
    mstr_data_dict = {}

    for idx, series in enumerate(api_series_list):
        try:
            prev_years = years.copy()
        except NameError:
            prev_years = None

        # Obtain data from EIA API; if the data returned is a dict,
        # there was an error with the series_id provided and that
        # output should be ignored entirely; the resulting error
        # from the missing key in the master dict will be handled
        # in the updater function
        raw_data = api_query(api_key, series)
        if isinstance(raw_data, (list,)):
            data, years = data_processor(raw_data)

            # Check against years vector from series pulled immediately
            # prior to determine if years vectors are being consistently
            # returned by the API; if so, or if there is no previous
            # years vector, record the data, otherwise raise a ValueError
            if isinstance(prev_years, np.ndarray):
                if (prev_years == years).all():
                    mstr_data_dict[series_names[idx]] = data
                else:
                    raise ValueError('Years vectors did not match.')
            else:
                mstr_data_dict[series_names[idx]] = data

    return mstr_data_dict, years


def updater(conv, api_key, aeo_yr, scen, captured_energy_method):
    """Perform calculations using EIA data to update conversion factors JSON

    Using data from the AEO year and specified NEMS modeling scenario,
    calculate revised site-source conversion factors, CO2 emissions
    rates, and energy prices. In the case of the "other" fuel types,
    energy prices are based on a energy use by fuel type-weighted
    average.

    For each of the calculations performed, in case of data missing from
    the record dict 'z' not obtained from the API due to invalid series
    IDs, run each calculation and update in a try/except block to catch
    KeyErrors for missing data and address them by not updating the
    original data and printing a warning to the console for the user.

    Args:
        conv (dict): Data structure from conversion JSON data file.
        api_key (str): EIA API key from system environment variable.
        aeo_yr (str): The desired year of the Annual Energy Outlook
            to query for data.
        scen (str): The desired AEO "case" or scenario to query.
        captured_energy_method (bool): If true, use the captured
            energy method to calculate the site-source conversions
            for electricity. For details, refer to the DOE report
            "Accounting Methodology for Source Energy of
            Non-Combustible Renewable Electricity Generation"

    Returns:
        Updated conversion factors dict to be exported to the conversions JSON.
    """

    # Get data via EIA API
    dq = EIAQueryData(aeo_yr, scen)
    z, yrs = data_getter(api_key, dq.data_names, dq.data_series)

    # Calculate adjustment factor to use the captured energy method
    # to account for electric source energy from renewable generation;
    # this approach is derived from the DOE report "Accounting
    # Methodology for Source Energy of Non-Combustible Renewable
    # Electricity Generation"
    if captured_energy_method:
        renew_factor = ((z['elec_renew_hydro'] + z['elec_renew_geothermal'] +
                         z['elec_renew_wind'] + z['elec_renew_solar_thermal'] +
                         z['elec_renew_solar_pv']) /
                        (z['elec_tot_energy_site'] + z['elec_tot_energy_loss']))
        capnrg = 1 - renew_factor + renew_factor*3412/9510
        # Since proceeding without this conversion factor would yield
        # results that are not as expected, the possible KeyError exception
        # due to missing data is intentionally not caught
    else:
        # Use the existing calculations for the fossil fuel equivalence method
        capnrg = np.ones(np.shape(z['elec_renew_hydro']))

    # Electricity site-source conversion factors
    try:
        ss_conv = ((z['elec_tot_energy_site'] + z['elec_tot_energy_loss']) /
                   z['elec_tot_energy_site'])
        for idx, year in enumerate(yrs):
            conv['electricity']['site to source conversion']['data'][year] = (
                round(ss_conv[idx]*capnrg[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, electricity '
              'site-source conversion factors were not updated.')

    # Residential electricity CO2 intensities [Mt CO2/quads]
    try:
        co2_res_ints = (z['elec_res_co2'] /
                        (z['elec_res_energy_site'] + z['elec_res_energy_loss']))
        for idx, year in enumerate(yrs):
            conv['electricity']['CO2 intensity']['data']['residential'][year] = (
                round(co2_res_ints[idx]/capnrg[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, residential '
              'electricity CO2 emissions intensities were not updated.')

    # Commercial electricity CO2 intensities [Mt CO2/quads]
    try:
        co2_com_ints = (z['elec_com_co2'] /
                        (z['elec_com_energy_site'] + z['elec_com_energy_loss']))
        for idx, year in enumerate(yrs):
            conv['electricity']['CO2 intensity']['data']['commercial'][year] = (
                round(co2_com_ints[idx]/capnrg[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, commercial '
              'electricity CO2 emissions intensities were not updated.')

    # Residential natural gas CO2 intensities [Mt CO2/quads]
    try:
        co2_res_ng_ints = z['ng_res_co2']/z['ng_res_energy']
        for idx, year in enumerate(yrs):
            conv['natural gas']['CO2 intensity']['data']['residential'][year] = (
                round(co2_res_ng_ints[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, residential '
              'natural gas CO2 emissions intensities were not updated.')

    # Commercial natural gas CO2 intensities [Mt CO2/quads]
    try:
        co2_com_ng_ints = z['ng_com_co2']/z['ng_com_energy']
        for idx, year in enumerate(yrs):
            conv['natural gas']['CO2 intensity']['data']['commercial'][year] = (
                round(co2_com_ng_ints[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, commercial '
              'natural gas CO2 emissions intensities were not updated.')

    # Residential other fuel CO2 intensities [Mt CO2/quads]
    try:
        co2_res_ot_ints = z['petro_res_co2']/z['petro_res_energy']
        for idx, year in enumerate(yrs):
            conv['other']['CO2 intensity']['data']['residential'][year] = (
                round(co2_res_ot_ints[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, residential '
              '"other fuel" CO2 emissions intensities were not updated.')

    # Commercial other fuel CO2 intensities [Mt CO2/quads]
    try:
        co2_com_ot_ints = ((z['petro_com_co2'] + z['coal_com_co2']) /
                           (z['petro_com_energy'] + z['coal_com_energy']))
        for idx, year in enumerate(yrs):
            conv['other']['CO2 intensity']['data']['commercial'][year] = (
                round(co2_com_ot_ints[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, commercial '
              '"other fuel" CO2 emissions intensities were not updated.')

    # Residential electricity prices [$/MMBtu source]
    try:
        for idx, year in enumerate(yrs):
            conv['electricity']['price']['data']['residential'][year] = (
                round(z['elec_res_price'][idx]/(ss_conv[idx]*capnrg[idx]), 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, residential '
              'electricity prices were not updated.')

    # Commercial electricity prices [$/MMBtu source]
    try:
        for idx, year in enumerate(yrs):
            conv['electricity']['price']['data']['commercial'][year] = (
                round(z['elec_com_price'][idx]/(ss_conv[idx]*capnrg[idx]), 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, commercial '
              'electricity prices were not updated.')

    # Residential natural gas prices [$/MMBtu source]
    try:
        for idx, year in enumerate(yrs):
            conv['natural gas']['price']['data']['residential'][year] = (
                round(z['ng_res_price'][idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, residential '
              'natural gas prices were not updated.')

    # Commercial natural gas prices [$/MMBtu source]
    try:
        for idx, year in enumerate(yrs):
            conv['natural gas']['price']['data']['commercial'][year] = (
                round(z['ng_com_price'][idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, commercial '
              'natural gas prices were not updated.')

    # Residential other fuel price as energy use-weighted average
    # of propane and distillate (fuel oil) prices [$/MMBtu source]
    try:
        res_other_price = (z['lpg_res_price']*z['lpg_res_energy']/(
                            z['lpg_res_energy'] + z['distl_res_energy']) +
                           z['distl_res_price']*z['distl_res_energy']/(
                            z['lpg_res_energy'] + z['distl_res_energy']))
        for idx, year in enumerate(yrs):
            conv['other']['price']['data']['residential'][year] = (
                round(res_other_price[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, residential '
              '"other fuel" prices were not updated.')

    # Commercial other fuel price as energy use-weighted average of
    # propane, distillate (fuel oil), and residual (fuel oil) prices
    # [$/MMBtu source]
    try:
        denom = z['lpg_com_energy']+z['distl_com_energy']+z['rsid_com_energy']
        com_other_price = (z['lpg_com_price']*z['lpg_com_energy']/denom +
                           z['distl_com_price']*z['distl_com_energy']/denom +
                           z['rsid_com_price']*z['rsid_com_energy']/denom)
        for idx, year in enumerate(yrs):
            conv['other']['price']['data']['commercial'][year] = (
                round(com_other_price[idx], 6))
    except KeyError:
        print('\nDue to failed data retrieval from the API, commercial '
              '"other fuel" prices were not updated.')

    return conv


if __name__ == '__main__':
    # Get API key from available environment variables
    if 'EIA_API_KEY' in os.environ:
        api_key = os.environ['EIA_API_KEY']
    else:
        print('\nExpected environment variable EIA_API_KEY not set.\n'
              'Obtain an API key from EIA at https://www.eia.gov/opendata/\n'
              'On a Mac, add the API key to your environment using the '
              'following command in Terminal (and then open a new window):'
              "$ echo 'export EIA_API_KEY=your api key' >> ~/.bash_profile\n")
        sys.exit(1)

    # Load current site-source and CO2 emissions conversion file
    ssconv = json.load(open(UsefulVars().conv_file, 'r'))

    # Ask the user to specify the desired report year, informing the
    # user about the valid year options
    while True:
        year = input('Please specify the desired AEO year. '
                     'Valid entries are: ' +
                     ', '.join(ValidQueries().years) + '.\n')
        if year not in ValidQueries().years:
            print('Invalid year entered.')
        else:
            break

    # Ask the user to specify the desired AEO case or scenario,
    # informing the user about the valid scenario options
    while True:
        scenario = input('Please specify the desired AEO scenario. '
                         'Valid entries are: ' +
                         ', '.join(ValidQueries().cases) + '.\n')
        if scenario not in ValidQueries().cases:
            print('Invalid scenario entered.')
        else:
            break

    # Set up command line argument for switching to the "captured
    # energy" method for calculating electricity site-source conversions
    parser = argparse.ArgumentParser()
    parser.add_argument('--captured', action='store_true')
    use_captured_nrg_method = parser.parse_args().captured
    if use_captured_nrg_method:
        method_text = 'CAPTURED ENERGY'
    else:
        method_text = 'FOSSIL FUEL EQUIVALENCE'
    print('\nATTENTION: SITE-SOURCE CONVERSIONS FOR ELECTRICITY '
          'WILL BE CALCULATED USING THE ' + method_text + ' METHOD.')

    # Change conversion factors dict imported from JSON to OrderedDict
    # so that the AEO year and scenario specified by the user can be
    # added with the indicated keys to the beginning of the file
    ssconv = OrderedDict(ssconv)
    ssconv['updated_to_aeo_year'] = year
    ssconv['updated_to_aeo_case'] = scenario
    ssconv['site-source calculation method'] = method_text.lower()
    ssconv.move_to_end('site-source calculation method', last=False)
    ssconv.move_to_end('updated_to_aeo_case', last=False)
    ssconv.move_to_end('updated_to_aeo_year', last=False)

    # Update site-source and CO2 emissions conversions
    ssconv = updater(ssconv, api_key, year, scenario, use_captured_nrg_method)

    # Output modified site-source and CO2 emissions conversion data
    js_out = open(UsefulVars().conv_file_out, 'w')
    json.dump(ssconv, js_out, indent=2)

    # Warn user that source fields need to be updated manually
    print('\nWARNING: THE SOCIAL COST OF CARBON AND ALL "source" AND '
          '"units" FIELDS IN THE CONVERSIONS JSON ARE NOT UPDATED '
          'BY THIS FUNCTION. PLEASE UPDATE THOSE FIELDS MANUALLY.\n')
