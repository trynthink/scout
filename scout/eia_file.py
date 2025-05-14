#!/usr/bin/env python3
"""Reprocess AEO output files as-received from EIA

Beginning in 2020, EIA modified the structure of some of the NEMS
output files used by Scout. This module restructures those files
to be consistent with the prior format, as expected by the other
modules used to convert the AEO data into the format used by Scout.
"""
import os
import csv
import re
import openpyxl as pyxl
from scout import mseg_techdata as rmt


class EIAFiles(object):
    """AEO data file reprocessing."""

    def __init__(self, input_dir='data', output_dir=None):
        """
        input_dir  - where to read EIA/AEO source files
        output_dir - where to write the restructured files.
                     Defaults to input_dir if you only want one folder.
        """
        self.input_dir = input_dir
        self.output_dir = output_dir or input_dir

        # ensure the output directory exists
        os.makedirs(self.output_dir, exist_ok=True)

        # inputs
        self.r_db_in   = os.path.join(self.input_dir,  'RESDBOUT-orig.txt')
        self.r_mess    = os.path.join(self.input_dir,  'rsmess.xlsx')
        self.c_tech_in = os.path.join(self.input_dir,  'ktekx.xlsx')
        self.r_lgt_in  = os.path.join(self.input_dir,  'rsmlgt.txt')

        # outputs
        self.r_db_out   = os.path.join(self.output_dir, 'RESDBOUT.txt')
        self.r_class    = os.path.join(self.output_dir, 'rsclass.txt')
        self.r_meqp     = os.path.join(self.output_dir, 'rsmeqp.txt')
        self.c_tech_out = os.path.join(self.output_dir, 'ktek.csv')
        self.r_lgt_out  = os.path.join(self.output_dir, 'rsmlgt.txt')

    def resdbout_fill_household(self):
        """Modify RESDBOUT such that all rows have the same number of columns."""
        try:
            f_dbin = open(self.r_db_in, 'r')
        except FileNotFoundError:
            os.rename(self.r_db_out, self.r_db_in)
            f_dbin = open(self.r_db_in, 'r')

        with open(self.r_db_out, 'w+', encoding='utf-8', newline='') as f_dbout:
            csv_dbin  = csv.DictReader(f_dbin)
            header    = csv_dbin.fieldnames
            csv_dbout = csv.DictWriter(f_dbout, fieldnames=header)
            csv_dbout.writeheader()
            for row in csv_dbin:
                if not row['HOUSEHOLDS']:
                    row['HOUSEHOLDS'] = '0'
                if not row['BULBTYPE']:
                    row['BULBTYPE'] = ''
                row.update({k: v.strip() for k, v in row.items()})
                csv_dbout.writerow(row)

        f_dbin.close()

    def res_gsl_lt_update(self):
        """Replace 'HAL' with 'INC' for GSL residential lighting."""
        # update RESDBOUT.csv
        with open(self.r_db_out, 'r', encoding='utf-8') as f_dbin:
            csv_cont = []
            csv_dbin = csv.DictReader(f_dbin)
            header   = csv_dbin.fieldnames
            for row in csv_dbin:
                if row.get('EQPCLASS') == 'GSL' and row.get('BULBTYPE') == 'HAL':
                    row['BULBTYPE'] = 'INC'
                csv_cont.append(row)

        with open(self.r_db_out, 'w', encoding='utf-8', newline='') as f_dbout:
            csv_dbout = csv.DictWriter(f_dbout, fieldnames=header)
            csv_dbout.writeheader()
            csv_dbout.writerows(csv_cont)

        # update lighting file
        with open(self.r_lgt_in, 'r', encoding='latin1') as f_ltin:
            modified = [
                line.replace('HAL', 'INC')
                if re.search(r'(?<=GSL\s)HAL', line)
                else line
                for line in f_ltin
            ]

        with open(self.r_lgt_out, 'w', encoding='latin1') as f_ltout:
            f_ltout.writelines(modified)

    def generate_rsclass(self):
        """Construct rsclass.txt file from table in combined XLSX file."""
        # derive the sheet name from the filename
        sheet_name = os.path.splitext(os.path.basename(self.r_class))[0].upper()
        wb         = pyxl.load_workbook(self.r_mess, data_only=True)
        rsclass    = wb[sheet_name]

        # find column to skip
        skip = 0
        for cell in rsclass[19]:
            if cell.value == 'Efficiency Metric':
                skip = cell.column

        with open(self.r_class, 'w+', encoding='utf-8') as f:
            # header row
            cols = [c for c in range(3, 22) if c != skip]
            f.write('\t'.join(str(rsclass.cell(row=19, column=c).value) for c in cols) + '\n')
            # names row
            f.write('\t'.join(rmt.r_nlt_l_names) + '\n')
            # data rows
            for row_num in range(21, 51):
                f.write(
                    '\t'.join(
                        str(rsclass.cell(row=row_num, column=c).value) for c in cols
                    ) + '\n'
                )

    def generate_rsmeqp(self):
        """Construct rsmeqp.txt file from data in combined XLSX file."""
        # derive the sheet name from the filename
        sheet_name = os.path.splitext(os.path.basename(self.r_meqp))[0].upper()
        wb        = pyxl.load_workbook(self.r_mess, data_only=True)
        rsmeqp    = wb[sheet_name]

        # locate start/end rows
        col_vals = list(*rsmeqp.iter_cols(max_col=1, values_only=True))
        rstart = rend = 0
        for cell in rsmeqp.iter_rows(min_col=1, max_col=1, values_only=False):
            v = cell[0].value
            if v == 'xlI':
                rstart = cell[0].row + 1
            elif isinstance(v, int) and v == list(filter(None, col_vals)).pop():
                rend = cell[0].row + 1

        if rend <= rstart:
            print('rsmeqp table dimensions not obtained successfully.')
            print('rsmeqp generation failed.')
            return

        with open(self.r_meqp, 'w+', encoding='utf-8') as f:
            # header
            f.write(
                '\t'.join(
                    str(rsmeqp.cell(row=22, column=c).value) for c in range(2, 30)
                ) + '\n'
            )
            # names
            f.write('\t'.join(rmt.r_nlt_cp_names) + '\n')
            # data
            for row_num in range(rstart, rend):
                f.write(
                    '\t'.join(
                        str(rsmeqp.cell(row=row_num, column=c).value) for c in range(2, 30)
                    ) + '\n'
                )
                
    def convert_ktekx(self):
        """Convert commercial technology characteristics data to CSV format."""
        if not os.path.isfile(self.c_tech_out):
            sheet_name = os.path.splitext(os.path.basename(self.c_tech_out))[0]
            ktekx      = pyxl.load_workbook(self.c_tech_in, data_only=True)[sheet_name]

            with open(self.c_tech_out, 'w+', newline='') as f:
                writer = csv.writer(f)
                for row in ktekx.rows:
                    writer.writerow([cell.value for cell in row])
        else:
            print(f"{self.c_tech_out} is already present and will not be modified.")


def main():
    # read from AEO2023, write processed files into 'inputs'
    f = EIAFiles(input_dir='AEO2025', output_dir='AEO2025')

    f.resdbout_fill_household()
    f.res_gsl_lt_update()
    f.generate_rsclass()
    f.generate_rsmeqp()
    f.convert_ktekx()


if __name__ == "__main__":
    main()
