import json
import pandas as pd
from os import getcwd


def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def get_intersecting_elems(lst1, lst2):
    # get intersecting years:val for energy
    # stock pair and filter for 2015-2050 range
    list_t = sorted(list(set(lst1).intersection(set(lst2))))
    list_t = list(filter(lambda yr: yr >= 2015 and yr <= 2050,
                         list(map(int, list_t))))
    list_t = list(map(str, list_t))
    return list_t


def calculate_total_stocks(data):
    # calculate total all stocks and store in a dict
    all_stocks = {}
    for em in data:
        for bt in data[em]:
            for ft in data[em][bt]:
                for eu in data[em][bt][ft]:
                    for tc in data[em][bt][ft][eu]:
                        if tc == 'secondary heating':
                            for yr in data[em][bt][ft][eu][tc]['stock']:
                                value = data[em][bt][ft][eu][tc]['stock'][yr]
                                eu_sh = 'secondary heating'
                                if(bool(all_stocks.get(em)) and
                                   bool(all_stocks[em].get(bt)) and
                                   bool(all_stocks[em][bt].get(eu_sh)) and
                                   bool(all_stocks[em][bt][eu_sh].get(yr))):
                                    old_value = all_stocks[em][bt][eu_sh][yr]
                                    value = old_value + value
                                nested_set(all_stocks, [
                                    em, bt, eu_sh, yr], value)
                        else:
                            try:
                                for yr in data[em][bt][ft][eu][tc]['stock']:
                                    value = \
                                        data[em][bt][ft][eu][tc]['stock'][yr]
                                    if(bool(all_stocks.get(em)) and
                                       bool(all_stocks[em].get(bt)) and
                                       bool(all_stocks[em][bt].get(eu)) and
                                       bool(all_stocks[em][bt][eu].get(yr))):
                                        old_value = all_stocks[em][bt][eu][yr]
                                        value = old_value + value
                                    nested_set(all_stocks, [
                                        em, bt, eu, yr], value)
                            except KeyError:
                                continue
    return all_stocks


def get_gcam_emm(data,all_stocks):
    # get uec and sd_share data in emm region
    gcam_emm = {}
    for em in data:
        for bt in data[em]:
            for ft in data[em][bt]:
                for eu in data[em][bt][ft]:
                    for tc in data[em][bt][ft][eu]:
                        try:
                            years = get_intersecting_elems(
                                list(
                                    data[em][bt][ft][eu][tc]['stock'].keys()),
                                list(
                                    data[em][bt][ft][eu][tc]['energy'].keys()))
                            uec_value_t = 0
                            for yr in years:
                                # to input uec_value
                                stock = data[em][bt][ft][eu][tc]['stock'][yr]
                                energy = data[em][bt][ft][eu][tc]['energy'][yr]
                                if energy != 0 and stock != 0:
                                    uec_value = energy / stock
                                else:
                                    uec_value = 0
                                    if uec_value_t != 0: 
                                        uec_value = uec_value_t
                                nested_set(gcam_emm, [em, bt, ft, eu, tc,
                                           'stock', yr], stock)
                                nested_set(gcam_emm, [em, bt, ft, eu, tc,
                                           'energy', yr], energy)
                                nested_set(gcam_emm, [em, bt, ft, eu, tc,
                                           'uec', yr], uec_value)
                            for yr in years:
                                # to input the sd_share_value
                                stock = data[em][bt][ft][eu][tc]['stock'][yr]
                                if stock != 0:
                                    eu_sh = 'secondary heating'
                                    if tc == eu_sh:
                                        all_stock_value = all_stocks[
                                            em][bt][eu_sh][yr]
                                    else:
                                        all_stock_value = all_stocks[
                                            em][bt][eu][yr]

                                    sd_share_value = stock / all_stock_value
                                else:
                                    sd_share_value = 0
                                try:
                                    sd_share_value < 1
                                except KeyError:
                                    print("LARGER THAN 1")
                                nested_set(gcam_emm, [em, bt, ft, eu, tc,
                                           'sd_share', yr], sd_share_value)
                            if bt == 'comm':
                                # fill in 2015 values the same as 2016 values
                                def input_vals_2015(varstr):
                                    nested_set(
                                        gcam_emm, [em, bt, ft, eu, tc, varstr,
                                                   '2015'],
                                        gcam_emm[em][bt][ft][eu][tc][varstr][
                                                 '2016'])

                                input_vals_2015('stock')
                                input_vals_2015('energy')
                                input_vals_2015('uec')
                                input_vals_2015('sd_share')
                        except KeyError:
                            pass
    return gcam_emm


def remap_uec_sdshr(inFile_str, outFile_str):

    inFile = open(inFile_str)
    state_emm_file = 'state_emm.csv'
    state_emm_rev_file = 'state_emm_rev.csv'
    data = json.load(inFile)
    all_stocks = calculate_total_stocks(data)
    gcam_emm = get_gcam_emm(data, all_stocks)
    gcam_state = {}
    df = pd.read_csv(state_emm_file)
    df_rev = pd.read_csv(state_emm_rev_file)
    emm_regions = df.columns[1:].tolist()
    em = emm_regions[0]
    emm_regions = emm_regions[1:]
    for r1, r2 in zip(df.itertuples(index=False),
                      df_rev.itertuples(index=False)):
        state = r1.State
        if state in ['Alaska', 'Hawaii']:
            nested_set(gcam_state, [state], {})
        else:
            for bt in gcam_emm[em]:
                for ft in gcam_emm[em][bt]:
                    for eu in gcam_emm[em][bt][ft]:
                        for tc in gcam_emm[em][bt][ft][eu]:
                            try:
                                def input_var_vals(yr, varstr, uec_b):
                                    mult = r1[df.columns.get_loc(em)]
                                    if varstr == 'stock' or varstr == 'energy':
                                        mult = r2[df_rev.columns.get_loc(em)]
                                    emm_val = gcam_emm[
                                        em][bt][ft][eu][tc][varstr][yr]
                                    emm_yr_val = mult * emm_val
                                    for em_t in emm_regions:
                                        mult = r1[df.columns.get_loc(em_t)]
                                        if varstr == 'stock' or \
                                           varstr == 'energy':
                                            mult = r2[
                                                df_rev.columns.get_loc(em_t)]
                                        var_years = list(gcam_emm[em_t][bt][
                                            ft][eu][tc][varstr].keys())
                                        emm_yr_val_t = 0
                                        if(yr in var_years):
                                            emm_val =  gcam_emm[em_t][bt][ft][
                                                eu][tc][varstr][yr]
                                            emm_yr_val_t = mult * emm_val
                                        emm_yr_val += emm_yr_val_t
                                    nested_set(gcam_state, [
                                        state, bt, ft, eu, tc, varstr, yr],
                                        emm_yr_val)
                                    if varstr == 'uec':
                                        emm_uecdelt_yr_val = 0.0
                                        if yr == '2015':
                                            uec_b = emm_yr_val
                                        else:
                                            if uec_b != 0.0:
                                                emm_uecdelt_yr_val = (
                                                    emm_yr_val - uec_b
                                                    ) / uec_b * 100
                                        nested_set(gcam_state, [
                                            state, bt, ft, eu, tc,
                                            'uec_pct_change', yr],
                                            emm_uecdelt_yr_val)
                                    return uec_b

                                years = get_intersecting_elems(
                                    list(gcam_emm[em][bt][ft][eu][tc][
                                         'uec'].keys()),
                                    list(gcam_emm[em][bt][ft][eu][tc][
                                        'sd_share'].keys()))
                                uec_b = 0.0
                                for yr in years:
                                    uec_b = \
                                        input_var_vals(yr, 'stock', uec_b)
                                    uec_b = \
                                        input_var_vals(yr, 'energy', uec_b)
                                    uec_b = \
                                        input_var_vals(yr, 'uec', uec_b)
                                    uec_b = \
                                        input_var_vals(yr, 'sd_share', uec_b)
                            except KeyError:
                                pass

    json.dump(gcam_state, open(outFile_str, 'w'), indent=2)
    inFile.close()


def main(base_dir):
    fdir = './'
    fnames = ['IRA_Low', 'Ineff_Elec', 'Mid', 'High', 'Breakthrough']
    for f in fnames:
        remap_uec_sdshr(f'{fdir}alt/msegs_emm_gcam_alt-{f}.json',
                        f'{fdir}uec_sdshr/uec_sdshr_gcam_alt-{f}.json')
    print('Remap to uec, sd_share, uec_pct_change values complete!')


if __name__ == '__main__':

    base_dir = getcwd()
    main(base_dir)
