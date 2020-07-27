#!/usr/bin/env python3

import csv
import xlrd

import mseg_techdata


class EIAFiles(object):

    def __init__(self):
        # input files
        self.r_bout_in = "RESDBOUT.xlsx"
        self.r_mess = "rsmess.xlsx"

        # output files
        self.r_bout_out = "RESDBOUT.csv"
        self.r_class = "rsclass.txt"
        self.r_meqp = "rsmeqp.txt"

        self.eiadata = mseg_techdata.EIAData()

    def resdbout_fill_household(self):
        """
        Replace empty "HOUSEHOLDS" cell with 0 and export as csv:

        """

        # 1. Rename RESDBOUT.txt to RESDBOUT_orig.txt;
        # and manually import into Excel sheet "RESDBOUT".

        # 2. Fill empty households cells with 0:
        hh_index = 0
        headers = []
        wb = xlrd.open_workbook(self.r_bout_in)
        sheet = wb.sheet_by_name("RESDBOUT")
        for i, header in enumerate(sheet.row(0)):
            headers.append(header.value)
            if header.value == "HOUSEHOLDS":
                hh_index = i

        with open(self.r_bout_out, 'w+') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for row in range(1, sheet.nrows):
                if sheet.cell_type(row, hh_index) == xlrd.XL_CELL_EMPTY:
                    sheet._cell_values[row][hh_index] = 0
                writer.writerow(sheet.row_values(row))

        # 3. Change RESDBOUT.csv file extension to '.txt' manually

    def generate_rsclass(self):
        """

        Returns: rsclass.txt

        """

        # Skip column “Efficiency Metric”
        skip = 0
        rsclass = xlrd.open_workbook(self.r_mess).sheet_by_name('RSCLASS')
        for i, v in enumerate(rsclass.row(18)):
            if (v.value == 'Efficiency Metric'):
                skip = i

        with open(self.r_class, 'w+') as f:
            f.write('\t'.join(str(name) for name in self.eiadata.r_nlt_l_names) + '\n')
            for cell in range(0, (50 - 19)):
                f.write('\t'.join(str(rsclass.col_values(i, 19, 50)[cell])
                                  for i in [x for x in range(2, 21) if x != skip]) + '\n')
            f.close()

    def generate_rsmeqp(self):
        """

        Returns: rsmeqp.txt

        """

        rstart = rend = 0
        rsmeqp = xlrd.open_workbook(self.r_mess).sheet_by_name('RSMEQP')
        for k, v in enumerate(rsmeqp.col_values(0)):
            if v == 'xlI':
                rstart = k
            elif isinstance(v, float) and v == list(filter(None, rsmeqp.col_values(0))).pop():
                rend = k + 1

        with open(self.r_meqp, 'w+') as f:
            f.write('\t'.join(str(name) for name in self.eiadata.r_nlt_cp_names) + '\n')
            for row in range(rstart, rend):
                f.write('\t'.join(str(rsmeqp.row_values(row, 1, rsmeqp.ncols - 1)[cell])
                                  for cell in range(0, 28)) + '\n')
            f.close()


def main():
    f = EIAFiles()

    f.resdbout_fill_household()
    f.generate_rsclass()
    f.generate_rsmeqp()


if __name__ == "__main__":
    main()
