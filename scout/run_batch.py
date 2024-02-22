from pathlib import Path
from scout.config import Config, FilePaths as fp
from scout.ecm_prep_args import ecm_args
from scout import ecm_prep, run
from argparse import ArgumentParser


def run_batch(yml_dir: Path):
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

        # Set list of ecms and run ecm_prep.main()
        ecm_prep_opts.ecm_files = list(ecm_files)
        ecm_prep_opts.ecm_directory = None
        ecm_prep_opts.ecm_files_regex = []
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
            run.main(run_opts)
        fp.reset_base_paths()


def group_common_configs(yml_dir):
    exclude_keys = ["ecm_directory", "ecm_files", "ecm_files_regex"]
    yml_groups = []
    yml_group_data = []
    for yml in yml_dir.iterdir():
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
        help=("Path to YAML configuration files")
    )

    opts = parser.parse_args()
    run_batch(opts.batch)
