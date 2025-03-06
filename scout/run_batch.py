from __future__ import annotations
from pathlib import Path
from scout.config import LogConfig, Config, FilePaths as fp
from scout.ecm_prep_args import ecm_args
from scout.ecm_prep import Utils, main as ecm_prep_main
from scout.utils import JsonIO
from scout import run
from argparse import ArgumentParser
import logging
import shutil
LogConfig.configure_logging()
logger = logging.getLogger(__name__)


class BatchRun():
    def __init__(self, yml_dir):
        self.yml_dir = yml_dir.resolve()

    def get_ecm_files(self, ymls: list) -> list:  # noqa: F821
        """Retrieve all ECMs from 1 or more config file and return together in a list of lists

        Args:
            ymls (list): filepaths of yml configuration files

        Returns:
            list: list of all ECMs, one item per yml
        """

        return [ecm_args(["-y", str(config.resolve())]).ecm_files for config in ymls]

    def get_unique_ecm_files(self, ymls: list) -> list:  # noqa: F821
        """Retrieve all ECMs from 1 or more config file and return common elements in a single list

        Args:
            ymls (list): filepaths of yml configuration files

        Returns:
            list: list of all unique ECMs across ymls
        """

        ecm_files_list = self.get_ecm_files(ymls)
        return list(set(ecm for ecm_list in ecm_files_list for ecm in ecm_list))

    def get_run_opts(self, config_pth: Path) -> argparse.NameSpace:  # noqa: F821
        """Parse arguments for run.py for a given configuration file. If a results_directory
            argument is not specified in the yml, then the name of the yml will be set as the
            results directory.

        Args:
            config_pth (Path): path to the yml configuration file

        Returns:
            argparse.NameSpace: arguments to be used in run.py
        """

        results_dir_yml = Config.load_config(config_pth)["run"].get("results_directory", None)
        if results_dir_yml:
            run_opts = run.parse_args(["-y", str(config_pth.resolve())])
        else:
            custom_results_dir = Path(__file__).resolve().parents[1] / "results" / config_pth.stem
            run_opts = run.parse_args(["-y", str(config_pth.resolve()),
                                      "--results_directory", str(custom_results_dir)])

        return run_opts

    def group_common_configs(self, yml_dir: Path):
        """Groups together configuration files with similar ecm_prep arguments. Those with
            identical ecm_prep arguments excluding `ecm_directory`, `ecm_files`, and
            `ecm_files_regex` are put in the same group to optimize running ecm_prep.py.
            Note: those with different `ecm_packages` values are not grouped together, as this
            influences which individual ECMs are run, and may omit preparation of desired
            measures.

        Args:
            yml_dir (Path): directory containing all configurations with which to run.

        Returns:
            list: groups of similar yamls that can be run with a single ecm_prep.py call
        """

        exclude_keys = ["ecm_directory", "ecm_files", "ecm_files_regex"]
        yml_groups = []
        yml_group_data = []
        yml_files = sorted([yml for yml in yml_dir.iterdir() if yml.suffix == ".yml"])
        for yml in yml_files:
            yml_data = Config.load_config(yml)
            yml_data_ecm_prep = {
                k: v for k, v in yml_data["ecm_prep"].items() if k not in exclude_keys
                }
            updated = False
            for i, grp_data in enumerate(yml_group_data):
                if grp_data == yml_data_ecm_prep:
                    yml_groups[i].append(yml)
                    updated = True
                    break
            if not updated:
                yml_groups.append([yml])
                yml_group_data.append(yml_data_ecm_prep)

        return yml_groups

    def run_batch(self):
        """Run ecm_prep.py and run.py using 1 or more configuration files. Configuration files
            are first grouped together if they have common ecm_prep arguments and ecm_prep.main()
            is run for each group. run.main() is then run for each individual configuration file.
        """

        yml_grps = self.group_common_configs(self.yml_dir)
        for ct, yml_grp in enumerate(yml_grps):
            # Set custom generated directory for each group, write .txt file to document the ymls
            fp.set_paths({"GENERATED": fp.GENERATED / f"batch_run{ct+1}"})
            paths = [yml.resolve().as_posix() for yml in yml_grp]

            for yml_file in paths:
                shutil.copy(yml_file, fp.GENERATED)

            # Set list of ECMs and run ecm_prep.main()
            ecm_prep_opts = ecm_args(["-y", str(yml_grp[0].resolve())])
            ecm_prep_opts.ecm_files = self.get_unique_ecm_files(yml_grp)
            ecm_prep_opts.ecm_directory = None
            ecm_prep_opts.ecm_files_regex = []
            logger.info(f"Running ecm_prep.py for the following configuration files: {paths}")
            ecm_prep_main(ecm_prep_opts)

            # Run run.main() for each yml in the group, set custom results directories
            run_setup = JsonIO.load_json(fp.GENERATED / "run_setup.json")
            ecm_files_list = self.get_ecm_files(yml_grp)
            for ct, config in enumerate(yml_grp):
                # Set all ECMs inactive
                run_setup = Utils.update_active_measures(run_setup,
                                                         to_inactive=ecm_prep_opts.ecm_files)
                # Set yml-specific ECMs active
                run_setup = Utils.update_active_measures(run_setup, to_active=ecm_files_list[ct])
                JsonIO.dump_json(run_setup, fp.GENERATED / "run_setup.json")
                run_opts = self.get_run_opts(config)
                logger.info(f"Running run.py for {config}")
                run.main(run_opts)
            fp.reset_base_paths()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-b", "--batch",
        type=Path,
        help=("Path to directory containing YAML configuration files")
    )

    opts = parser.parse_args()
    BatchRun(opts.batch).run_batch()
