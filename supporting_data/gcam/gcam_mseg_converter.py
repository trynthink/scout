import json
from argparse import ArgumentParser
from os import getcwd
import gzip
import shutil
import pandas as pd
import numpy as np


def unzip_gz_file(gz_file_path, output_path):
    with gzip.open(gz_file_path, 'rb') as gz_file:
        with open(output_path, 'wb') as output_file:
            shutil.copyfileobj(gz_file, output_file)


def nested_set(dic, keys, value):
    for key in keys[:-1]:
        dic = dic.setdefault(key, {})
    dic[keys[-1]] = value


def get_child(dic, parent, gchild, default=None):
    return next((x[0] for x in dic[parent].items() if gchild in x[1]), default)


def get_from_dict(dic, keys, default=None):
    for key in keys:
        try:
            dic = dic[key]
        except KeyError:
            return default
    return dic


def contains_str(string_list, substring):
    for s in string_list:
        if substring in s:
            return True
    return False


def process_data(scout_data, gcam_data, scout_keys, gcam_keys):
    for yr, value in scout_data.items():
        if not isinstance(value, (int, float)):
            continue
        bt_gcam = gcam_keys[1]
        es = scout_keys[-1]
        tc = scout_keys[-2]
        heatpumps = ["ASHP", "GSHP", "NGHP"]
        if bt_gcam == 'resid' and es == 'stock' and \
           contains_str(heatpumps, tc):
            value *= 2
        gcam_keys_with_year = gcam_keys + [yr]
        exist_value = get_from_dict(gcam_data, gcam_keys_with_year, default=0)
        new_value = exist_value + value
        nested_set(gcam_data, gcam_keys_with_year, new_value)


def filter_condition(mapdf, column_name, value):
    if isinstance(value, str):
        return mapdf[column_name].str.contains(
            value.strip(), case=False, regex=False)
    elif np.isnan(value):
        return [True] * len(mapdf)
    else:
        return [False] * len(mapdf)


def scout_gcam_map(mapdf, bt_gcam, scout_ft, scout_eu, scout_tc):
    condition = (
        filter_condition(mapdf, 'building_type', bt_gcam) &
        filter_condition(mapdf, 'scout_fuel', scout_ft) &
        filter_condition(mapdf, 'scout_enduse', scout_eu)
    )
    if isinstance(scout_tc, str):
        condition &= filter_condition(mapdf, 'scout_tech', scout_tc)
    return mapdf[condition]


all_map = {
    'fuel_type': ['electricity', 'natural gas', 'distillate', 'other fuel'],
    'bldg_type': {
        'resid': [
          'single family home', 'multi family home', 'mobile home'],
        'comm': [
          'assembly', 'education', 'food sales', 'food service', 'health care',
          'lodging', 'large office', 'small office', 'mercantile/service',
          'warehouse', 'other']
    }
}


def process_routine(mapdf, gcam_data, scout_data, em, bt, bt_gcam):
    if bt_gcam in list(all_map['bldg_type'].keys()):
        for ft in scout_data[em][bt]:
            if ft in all_map['fuel_type']:
                for eu in scout_data[em][bt][ft]:
                    for tc in scout_data[em][bt][ft][eu]:
                        if tc == 'supply' or tc == 'demand':
                            if tc == 'supply':
                                for tc in scout_data[em][bt][ft][eu]['supply']:
                                    for es in scout_data[
                                                em][bt][ft][eu]['supply'][tc]:
                                        if eu == 'secondary heating' and \
                                           es == 'stock':
                                            continue
                                        else:
                                            mapped = scout_gcam_map(
                                                mapdf, bt_gcam, ft, eu, tc)
                                            sub_scout_data = scout_data[
                                                em][bt][ft][eu][
                                                'supply'][tc][es]
                                            if sub_scout_data == 'NA':
                                                sub_scout_data = scout_data[
                                                    em][bt][
                                                    'total square footage']
                                            scout_keys = \
                                                [em, bt, ft, eu, tc, es]
                                            gcam_keys = \
                                                [em,
                                                 bt_gcam,
                                                 mapped.iloc[0][
                                                    'gcam_subsector'],
                                                 mapped.iloc[0][
                                                    'gcam_supplysector'],
                                                 mapped.iloc[0][
                                                    'gcam_tech'],
                                                 es]
                                            process_data(sub_scout_data,
                                                         gcam_data, scout_keys,
                                                         gcam_keys)

                        elif tc == 'energy' or tc == 'stock':
                            mapped = scout_gcam_map(
                                mapdf, bt_gcam, ft, eu, np.nan)
                            if mapped.empty:
                                pass
                                # should be only onsite generation
                                # print(f'{bt_gcam} {ft} {eu} {tc}')
                            else:
                                sub_scout_data = scout_data[em][bt][ft][eu][tc]
                                if sub_scout_data == 'NA':  # for stock
                                    sub_scout_data = scout_data[em][bt][
                                            'total square footage']
                                scout_keys = [em, bt, ft, eu, tc]
                                gcam_keys = \
                                    [em,
                                     bt_gcam,
                                     mapped.iloc[0]['gcam_subsector'],
                                     mapped.iloc[0]['gcam_supplysector'],
                                     mapped.iloc[0]['gcam_tech'],
                                     tc]
                                process_data(
                                    sub_scout_data, gcam_data, scout_keys,
                                    gcam_keys)
                        else:
                            for es in scout_data[em][bt][ft][eu][tc]:
                                mapped = scout_gcam_map(
                                    mapdf, bt_gcam, ft, eu, tc)
                                # for checking missing techs
                                # if mapped.empty:
                                #    print(f'{bt_gcam} {ft} {eu} {tc}')
                                sub_scout_data = scout_data[
                                    em][bt][ft][eu][tc][es]
                                if sub_scout_data == 'NA':  # for stock
                                    sub_scout_data = scout_data[em][bt][
                                        'total square footage']
                                scout_keys = [em, bt, ft, eu, tc, es]
                                gcam_keys = \
                                    [em,
                                     bt_gcam,
                                     mapped.iloc[0]['gcam_subsector'],
                                     mapped.iloc[0]['gcam_supplysector'],
                                     mapped.iloc[0]['gcam_tech'],
                                     es]
                                process_data(sub_scout_data, gcam_data,
                                             scout_keys, gcam_keys)
    if bt_gcam == 'resid':
        years_hpwh = list(range(2016, 2051, 1))
        for yr in years_hpwh:
            nested_set(gcam_data, [em, bt_gcam, 'electricity', 'hot water',
                       'electric heat pump water heater', 'stock', yr], 0.0)
            nested_set(gcam_data, [em, bt_gcam, 'electricity', 'hot water',
                       'electric heat pump water heater', 'energy', yr], 0.0)


def generate_step2():
    fdir = "../stock_energy_tech_data"
    fname = "mseg_res_com_emm"
    fname_gcam = "msegs_emm_gcam_ref.json"
    unzip_gz_file(f'{fdir}/{fname}.gz', f'{fdir}/{fname}.json')
    f = open(f'{fdir}/{fname}.json')
    scout_data = json.load(f)
    mapdf = pd.read_csv("scout_gcam_map.csv")
    gcam_data = {}
    for em in scout_data:
        for bt in scout_data[em]:
            bt_gcam = get_child(all_map, 'bldg_type', bt)
            process_routine(mapdf, gcam_data, scout_data, em, bt, bt_gcam)
    json.dump(gcam_data, open(f'{fdir}/{fname_gcam}', 'w'), indent=2)


def main(base_dir):
    generate_step2()
    print("Complete Remapping")


if __name__ == '__main__':
    parser = ArgumentParser()
    opts = parser.parse_args()
    base_dir = getcwd()
    main(base_dir)
