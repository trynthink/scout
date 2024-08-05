#!/usr/bin/env python3
import pandas as pd
from scout.config import FilePaths as fp


if __name__ == "__main__":
    """Read geographic mapping data from XLSX and write sheets out as text files."""

    # Geographic mapping XLSX input file
    f_in = fp.CONVERT_DATA / "geo_map" / "Scout Geography Mapping Data (Latest).xlsx"

    # Read in data as dictionary
    data = pd.read_excel(f_in, sheet_name=None)

    # Supporting sheets in mapping file to exclude from TXT write
    skip_sheets = [
        "TOC", "Master_Mapping_Sheet", "Grid_Region_Mapping",
        "County_Data_CZones", "Pop_Census_2023",
        "EMM_State_Elec_Map_NEMS_SEDS", "State_Fossil_Mapping_SEDS",
        "Res_AllFuels_SEDS_2022_TBtus", "Com_AllFuels_SEDS_2022_TBtus",
        "State_EMM", "State_EMM_Rev", "State_EMM-EMF37", "EMM_National",
        "Res_SF_Homes_RECS_2020", "State_Fossil_All_Mapping_SEDS",
        "State_EMM_ColSums", "State_EMM_RowSums", "ASH_State_ColSums"]

    # Loop through the dictionary and save each XLSX sheet as text file
    for sheet_name, df in [x for x in data.items() if x[0] not in skip_sheets]:
        f_out = fp.CONVERT_DATA / "geo_map" / f'{sheet_name}.txt'
        df.to_csv(f_out, sep='\t', index=None)
