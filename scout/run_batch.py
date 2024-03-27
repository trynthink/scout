from __future__ import annotations
from pathlib import Path
from scout.config import LogConfig, Config, FilePaths as fp
from scout.ecm_prep_args import ecm_args
from scout import ecm_prep, run
from argparse import ArgumentParser
import logging
LogConfig.configure_logging()
logger = logging.getLogger(__name__)


class BatchRun():
    def __init__(self, yml_dir):
        self.yml_dir = yml_dir.resolve()

    def get_ecm_files(self, ymls: list) -> list:  # noqa: F821
        """Retrieve all ECMs from 1 or more config file and concatenate into a single list

        Args:
            ymls (list): filepaths of yml configuration files

        Returns:
            list: list of all ECMs specified in the yml files
        """

        ecm_files = set()
        for config in ymls:
            config_pth = str(config.resolve())
            ecm_prep_opts = ecm_args(["-y", config_pth])
            ecm_files.update(set(ecm_prep_opts.ecm_files))

        return list(ecm_files)

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
            are first grouped together if they have commone ecm_prep arguments and ecm_prep.main()
            is run for each group. run.main() is then run for each individual configuration file.
        """

        yml_grps = self.group_common_configs(self.yml_dir)
        for ct, yml_grp in enumerate(yml_grps):

            # Set custom generated directory for each group, write .txt file to document the ymls
            fp.set_paths({"GENERATED": fp.GENERATED / f"temp{ct}"})
            paths = [yml.resolve().as_posix() for yml in yml_grp]
            with open(fp.GENERATED / "config_files.txt", "w") as f:
                f.write("\n".join(paths))

            # Set list of ecms and run ecm_prep.main()
            ecm_prep_opts = ecm_args(["-y", str(yml_grp[0].resolve())])
            ecm_prep_opts.ecm_files = self.get_ecm_files(yml_grp)
            ecm_prep_opts.ecm_directory = None
            ecm_prep_opts.ecm_files_regex = []
            logger.info(f"Running ecm_prep.py for the following configuration files: {paths}")
            ecm_prep.main(ecm_prep_opts)

            # Run run.main() for each yml in the group, set custom results directories
            for config in yml_grp:
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
