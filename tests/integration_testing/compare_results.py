import pandas as pd
import argparse
import json
from pathlib import Path


class ScoutCompare():
    """Class to compare results from  Scout workflow run. Comparisons are saved as csv files to
        summarize differences in results json files (agg_results.json, ecm_results.json) and/or
        summary report files (Summary_Data-TP.xlsx, Summary_Data-MAP.xlsx)
    """

    @staticmethod
    def load_json(file_path):
        with open(file_path, 'r') as file:
            return json.load(file)

    def compare_dict_keys(self, dict1, dict2, paths, path='', key_diffs=None):
        """Compares nested keys across two dictionaries by recursively searching each level

        Args:
            dict1 (dict): dictionary to compare
            dict2 (dict): dictionary to compare
            paths (list): paths to the original files from which the dictionaries are imported
            path (str, optional): current dictionary path at whcih to compare. Defaults to ''.
            key_diffs (pd.DataFrame, optional): existing summary of difference. Defaults to None.

        Returns:
            pd.DataFrame: summary of differences specifying the file, the unique keys, and the
                path that key is found at.
        """
        if key_diffs is None:
            key_diffs = pd.DataFrame(columns=["Results file", "Unique key", "Found at"])
        keys1 = set(dict1.keys())
        keys2 = set(dict2.keys())
        only_in_dict1 = keys1 - keys2
        only_in_dict2 = keys2 - keys1

        if only_in_dict1:
            new_row = pd.DataFrame({"Results file": paths[0].stem,
                                    "Unique key": str(only_in_dict1),
                                    "Found at": path[2:]}, index=[0])
            key_diffs = pd.concat([key_diffs, new_row], ignore_index=True)
        if only_in_dict2:
            new_row = pd.DataFrame({"Results file": paths[1].stem,
                                    "Unique key": str(only_in_dict2),
                                    "Found at": path[2:]}, index=[0])
            key_diffs = pd.concat([key_diffs, new_row], ignore_index=True)

        for key in keys1.intersection(keys2):
            if isinstance(dict1[key], dict) and isinstance(dict2[key], dict):
                key_diffs = self.compare_dict_keys(dict1[key],
                                                   dict2[key],
                                                   paths,
                                                   path=f"{path}: {key}",
                                                   key_diffs=key_diffs)

        return key_diffs

    def compare_dict_values(self, dict1, dict2, percent_threshold=10, abs_threshold=1000):
        """Compares values across two dictionary by recursively searching keys until identifying
            values at common paths. Both thresholds must be met to report results.

        Args:
            dict1 (dict): dictionary to compare
            dict2 (dict): dictionary to compare
            percent_threshold (int, optional): the percent difference threshold at which
                                               differences are reported. Defaults to 10.
            abs_threshold (int, optional): the abosolute difference threshold at which differences
                                           are reported. Defaults to 10.

        Returns:
            pd.DataFrame: summary of percent differences that meet thresholds
        """
        diff_report = {}

        def compare_recursive(d1, d2, path=""):
            for key in d1.keys():
                current_path = f"{path}['{key}']"
                if isinstance(d1[key], dict) and key in d2:
                    compare_recursive(d1[key], d2[key], current_path)
                elif isinstance(d1[key], (int, float)) and key in d2:
                    if isinstance(d2[key], (int, float)):
                        val1 = d1[key]
                        val2 = d2[key]
                        if val1 != 0:
                            percent_change = ((val2 - val1) / val1) * 100
                            if (abs(percent_change) >= percent_threshold) and \
                                    (abs(val1) >= abs_threshold or abs(val2) >= abs_threshold):
                                diff_report[current_path] = percent_change

        compare_recursive(dict1, dict2)
        return diff_report

    def write_dict_key_report(self, diff_report, output_path):
        if diff_report.empty:
            return
        diff_report.to_csv(output_path, index=False)

    def write_dict_value_report(self, diff_report, output_path):
        df = pd.DataFrame(columns=["Results path", "Percent difference"],
                          data=list(zip(diff_report.keys(), diff_report.values())))
        if df.empty:
            return
        df.to_csv(output_path, index=False)

    def compare_jsons(self, json1_path, json2_path, write_reports=True):
        """Compare two jsons and report differences in keys and in values

        Args:
            json1_path (Path): json file to compare
            json2_path (Path): json file to compare
            write_reports (bool, optional): _description_. Defaults to True.
        """
        json1 = self.load_json(json1_path)
        json2 = self.load_json(json2_path)

        # Compare differences in json keys
        key_diffs = self.compare_dict_keys(json1, json2, [json1_path, json2_path])
        if write_reports:
            out_path = json2_path.parent / f"{json2_path.stem}_key_diffs.csv"
            self.write_dict_key_report(key_diffs, out_path)

        # Compare differences in json values
        val_diffs = self.compare_dict_values(json1, json2)
        if write_reports:
            out_path = json2_path.parent / f"{json2_path.stem}_value_diffs.csv"
            self.write_dict_value_report(val_diffs, out_path)

    def compare_summary_reports(self, report1_path, report2_path, write_reports=True):
        # Compare Summary_Data-TP.xlsx and Summary_Data-MAP.xlsx with baseline files
        pass


def main():
    parser = argparse.ArgumentParser(description="Compare results files for Scout.")
    parser.add_argument("--json-baseline", type=Path, help="Path to the baseline JSON file")
    parser.add_argument("--json-new", type=Path, help="Path to the new JSON file")
    parser.add_argument("--summary-baseline", type=Path,
                        help="Path to the baseline summary report (Excel file)")
    parser.add_argument("--summary-new", type=Path,
                        help="Path to the new summary report (Excel file)")
    parser.add_argument("-d", "--directory", type=Path,
                        help="Directory containing files to compare")
    parser.add_argument("--baseline_suffix", type=str, default="_master",
                        help="If using the --directory argument, specify the suffix for the "
                        "baseline files (e.g., '_master')")
    parser.add_argument("--threshold", type=float, default=10,
                        help="Threshold for percent difference")
    args = parser.parse_args()

    compare = ScoutCompare()
    if args.directory:
        # Compare all files
        results_dir = args.directory.resolve()
        agg_results_json_base = results_dir / f"agg_results{args.baseline_suffix}.json"
        agg_results_json = results_dir / "agg_results.json"
        compare.compare_jsons(agg_results_json_base, agg_results_json)

        ecm_results_json_base = results_dir / f"ecm_results{args.baseline_suffix}.json"
        ecm_results_json = results_dir / "ecm_results.json"
        compare.compare_jsons(ecm_results_json_base, ecm_results_json)

        plots_dir = results_dir / "plots"
        summary_tp_base = plots_dir / "tech_potential" / \
            f"Summary_Data-TP{args.baseline_suffix}.xlsx"
        summary_tp = plots_dir / "tech_potential" / "Summary_Data-TP.xlsx"
        compare.compare_summary_reports(summary_tp_base, summary_tp)

        summary_map_base = (plots_dir / "max_adopt_potential" /
                            f"Summary_Data-MAP{args.baseline_suffix}.xlsx")
        summary_map = plots_dir / "tech_potential" / "Summary_Data-MAP.xlsx"
        compare.compare_summary_reports(summary_map_base, summary_map)

    else:
        # Compare only as specified by the arguments
        if args.json_baseline and args.json_new:
            compare.compare_jsons(args.json_baseline, args.json_new)
        if args.summary_baseline and args.summary_new:
            compare.compare_summary_reports(args.summary_baseline, args.summary_new)


if __name__ == "__main__":
    main()
