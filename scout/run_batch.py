from pathlib import Path
from scout.config import LogConfig, Config, FilePaths as fp
from scout.ecm_prep_args import ecm_args
from scout import ecm_prep, run
from argparse import ArgumentParser
import logging
LogConfig.configure_logging()
logger = logging.getLogger(__name__)


def run_batch(yml_dir: Path):
    """Run ecm_prep.py and run.py using 1 or more configuration files

    Args:
        yml_dir (Path): directory containing all configurations with which to run.
    """

    ecm_files = set()
    yml_dir = yml_dir.resolve()

    # Run ecm_prep.py for each yml group
    yml_grps = group_common_configs(yml_dir)
    for ct, yml_grp in enumerate(yml_grps):

        # Combine ECMs across the group
        ecm_files = set()
        for config in yml_grp:
            config_pth = str(config.resolve())
            ecm_prep_opts = ecm_args(["-y", config_pth])
            ecm_files.update(set(ecm_prep_opts.ecm_files))

        # Each group has a unique set of files in ./generated
        fp.set_paths({"GENERATED": fp.GENERATED / f"temp{ct}"})
        # Write which yml files are associated with the ./generated/temp dir
        paths = [yml.resolve().as_posix() for yml in yml_grp]
        with open(fp.GENERATED / "config_files.txt", "w") as f:
            f.write("\n".join(paths))

        # Set list of ecms and run ecm_prep.main()
        ecm_prep_opts.ecm_files = list(ecm_files)
        ecm_prep_opts.ecm_directory = None
        ecm_prep_opts.ecm_files_regex = []
        logger.info(f"Running ecm_prep.py for the following configuration files: {paths}")
        ecm_prep.main(ecm_prep_opts)

        # Run run.py for each yml in the group, set custom results directories
        for config in yml_grp:
            config_pth = str(config.resolve())
            results_dir_yml = Config._load_config(config)["run"].get("results_directory", None)
            if results_dir_yml:
                run_opts = run.parse_args(["-y", str(config.resolve())])
            else:
                custom_results_dir = Path(__file__).resolve().parents[1] / "results" / config.stem
                run_opts = run.parse_args(["-y", str(config.resolve()),
                                           "--results_directory", str(custom_results_dir)])
            logger.info(f"Running run.py for {config}")
            run.main(run_opts)
        fp.reset_base_paths()


def group_common_configs(yml_dir: Path):
    """Groups together configuration files with similar ecm_prep arguments. Those with identical
        ecm_prep arguments excluding `ecm_directory`, `ecm_files`, and `ecm_files_regex`, will be
        put in the same group to optimize running ecm_prep.py.

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
        yml_data = Config._load_config(yml)
        yml_data_ecm_prep = {k: v for k, v in yml_data["ecm_prep"].items() if k not in exclude_keys}
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


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument(
        "-b", "--batch",
        type=Path,
        help=("Path to directory containing YAML configuration files")
    )

    opts = parser.parse_args()
    run_batch(opts.batch)
