#!/usr/bin/env python3
import pandas as pd
from os import getcwd, path


def main(base_dir):
    """Read geo mapping data from XLSX and write sheets out as TXT files."""

    # Geo mapping folder path
    f_path_geo = path.join(
        base_dir, "scout", "supporting_data", "convert_data", "geo_map")
    # XLSX mapping input file
    f_in = path.join(f_path_geo, "Scout Geography Mapping Data (Latest).xlsx")
    # Supporting sheets in mapping file to exclude from TXT write
    excl_shts = [
        "TOC", "Master_Mapping_Sheet", "Grid_Region_Mapping",
        "County_Data_CZones", "Pop_Census_2023",
        "EMM_State_Elec_Map_NEMS_SEDS", "State_Fossil_Mapping_SEDS",
        "Res_AllFuels_SEDS_2022_TBtus", "Com_AllFuels_SEDS_2022_TBtus",
        "State_EMM", "State_EMM_Rev", "State_EMM-EMF37", "EMM_National",
        "Res_SF_Homes_RECS_2020", "State_Fossil_All_Mapping_SEDS",
        "State_EMM_ColSums", "State_EMM_RowSums", "ASH_State_ColSums"]
    # Read in data as dictionary
    data = pd.read_excel(f_in, sheet_name=None)
    # Loop through the dictionary and save each XLSX sheet as TXT
    for sheet_name, df in [x for x in data.items() if x[0] not in excl_shts]:
        df.to_csv(path.join(f_path_geo, f'{sheet_name}.txt'),
                  sep='\t', index=None)


if __name__ == "__main__":
    # Set current working directory
    base_dir = getcwd()
    main(base_dir)
