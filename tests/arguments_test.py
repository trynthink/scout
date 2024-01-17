from __future__ import annotations
import unittest
import copy
import jsonschema
from pathlib import Path
from argparse import ArgumentParser
from scout.config import Config
from scout.ecm_prep_args import ecm_args


class Utils:
    test_files = Path(__file__).parent / "test_files"
    empty_yml_pth = str(test_files / "empty_config.yml")
    default_yml_pth = str(test_files / "default_config.yml")
    valid_yml_pth = str(test_files / "valid_config.yml")

    def _assert_arg_vals(
        self, args: argparse.NameSpace, expected_args: dict, update_dict: dict = {}  # noqa: F821
    ):
        expected_args.update(update_dict)
        for arg, val in expected_args.items():
            self.assertEqual(vars(args).get(arg), val, f"for argument {arg}")


class TestConfig(unittest.TestCase, Utils):
    # Tests to process yml configuration files and parse as arguments
    default_config = {
        "ecm_prep": {
            "site_energy": False,
            "captured_energy": False,
            "alt_regions": None,
            "tsv_type": None,
            "tsv_daily_hr_restrict": None,
            "tsv_sys_shape_case": None,
            "tsv_season": None,
            "tsv_energy_agg": None,
            "tsv_power_agg": None,
            "tsv_average_days": None,
            "sect_shapes": False,
            "rp_persist": False,
            "verbose": False,
            "health_costs": False,
            "split_fuel": False,
            "no_scnd_lgt": False,
            "floor_start": None,
            "pkg_env_costs": None,
            "exog_hp_rate_scenario": None,
            "switch_all_retrofit_hp": False,
            "alt_ref_carb": False,
            "grid_decarb_level": None,
            "grid_assesment_timing": None,
            "adopt_scn_restrict": None,
            "retrofit_type": None,
            "retrofit_multiplier": None,
            "retrofit_mult_year": None,
            "add_typ_eff": False,
            "pkg_env_sep": False,
            "detail_brkout": [],
            "fugitive_emissions": [],
        },
        "run": {
            "verbose": False,
            "mkt_fracs": False,
            "trim_results": False,
            "report_stk": False,
            "report_cfs": False,
        },
    }

    valid_config = {
        "ecm_prep": {
            "add_typ_eff": True,
            "rp_persist": True,
            "alt_regions": "EMM",
            "adopt_scn_restrict": "Max adoption potential",
            "fugitive_emissions": ["methane", "typical refrigerant"],
            "retrofit_type": "increasing",
            "retrofit_multiplier": 1.2,
            "retrofit_mult_year": 2030,
            "exog_hp_rate_scenario": "aggressive",
            "switch_all_retrofit_hp": False,
            "grid_decarb_level": "full",
            "grid_assesment_timing": "after",
            "tsv_type": "energy",
            "tsv_daily_hr_restrict": "all",
            "tsv_sys_shape_case": "total reference",
            "tsv_season": "summer",
            "tsv_energy_agg": "average",
            "tsv_average_days": "weekdays",
            "detail_brkout": ["regions", "fuel types"],
            "pkg_env_costs": "include HVAC",
        },
        "run": {"mkt_fracs": True, "trim_results": True},
    }

    def _get_cfg_args(self, key, cli_args=[]):
        # Instantiate Config class and parse args
        parser = ArgumentParser()
        config = Config(parser, key, cli_args)
        args = config.parse_args()
        return args

    def _check_schema_err(self, expected_err, args_update={}, drop_key=None):
        parser = ArgumentParser()
        c = Config(parser, "ecm_prep", ["--yaml", self.valid_yml_pth])
        c.config_args.update(args_update)
        if drop_key:
            c.config_args.pop(drop_key)

        with self.assertRaises(jsonschema.exceptions.ValidationError) as context:
            c._validate(c.config_args)
        actual_msg = str(context.exception)
        self.assertTrue(expected_err in actual_msg, f"Expected {expected_err} in {actual_msg}")

    def test_empty_args(self):
        # Test defaults from no cfg file
        # ecm_prep.py
        args = self._get_cfg_args("ecm_prep", cli_args=[])
        self._assert_arg_vals(args, self.default_config["ecm_prep"])

        # run.py
        args = self._get_cfg_args("run", cli_args=[])
        self._assert_arg_vals(args, self.default_config["run"])

    def test_minimum_yml(self):
        # Test defaults with empty cfg file
        # ecm_prep.py
        args = self._get_cfg_args("ecm_prep", cli_args=["--yaml", self.empty_yml_pth])
        self._assert_arg_vals(args, self.default_config["ecm_prep"])

        # run.py
        args = self._get_cfg_args("run", cli_args=["--yaml", self.empty_yml_pth])
        self._assert_arg_vals(args, self.default_config["run"])

    def test_default_yml(self):
        # Test explicit defaults values from cfg file
        # ecm_prep.py
        args = self._get_cfg_args("ecm_prep", cli_args=["--yaml", self.default_yml_pth])
        self._assert_arg_vals(args, self.default_config["ecm_prep"])

        # run.py
        args = self._get_cfg_args("run", cli_args=["--yaml", self.empty_yml_pth])
        self._assert_arg_vals(args, self.default_config["run"])

    def test_valid_yml_file(self):
        # Test & validate with valid cfg file
        # ecm_prep.py
        args = self._get_cfg_args("ecm_prep", cli_args=["--yaml", self.valid_yml_pth])
        self._assert_arg_vals(args, self.valid_config["ecm_prep"])

        # run.py
        args = self._get_cfg_args("run", cli_args=["--yaml", self.valid_yml_pth])
        self._assert_arg_vals(args, self.valid_config["run"])

    def test_cli_overwrite(self):
        # Ensure cli arguments take precedence over yml
        # ecm_prep.py
        cli_args = [
            "--yaml",
            self.valid_yml_pth,
            "--adopt_scn_restrict",
            "Technical potential",
            "--fugitive_emissions",
            "low-gwp refrigerant",
        ]
        args = self._get_cfg_args("ecm_prep", cli_args=cli_args)
        expected_args = copy.deepcopy(self.valid_config["ecm_prep"])
        expected_arg_update = {
            "adopt_scn_restrict": "Technical potential",
            "fugitive_emissions": ["low-gwp refrigerant"],
        }
        self._assert_arg_vals(args, expected_args, expected_arg_update)

        # run.py
        cli_args = ["--yaml", self.valid_yml_pth, "--report_stk", "--report_cfs"]
        args = self._get_cfg_args("run", cli_args=cli_args)
        expected_args = copy.deepcopy(self.valid_config["run"])
        expected_arg_update = {
            "report_stk": True,
            "report_cfs": True,
        }
        self._assert_arg_vals(args, expected_args, expected_arg_update)

    def test_invalid_yml_schema(self):
        # Invalid yml schemas
        args_update = {"ecm_prep": {"alt_regions": "invalid"}}
        expected_err = "'invalid' is not one of ['EMM', 'State', 'AIA', None]"
        self._check_schema_err(expected_err, args_update)

        args_update = {
            "ecm_prep": {"fugitive_emissions": ["low-gwp refrigerant", "typical refrigerant"]}
        }
        expected_err = "['low-gwp refrigerant', 'typical refrigerant'] should not be valid under"
        self._check_schema_err(expected_err, args_update)

        expected_err = "'description' is a required property"
        self._check_schema_err(expected_err, drop_key="description")

    def test_invalid_config_args(self):
        # For invalid arguments not captured in the schema
        cli_args = ["--detail_brkout", "fuel types", "--split_fuel"]
        with self.assertRaises(ValueError) as context:
            self._get_cfg_args("ecm_prep", cli_args)
        actual_msg = str(context.exception)
        expected_err = (
            "Detailed breakout (detail_brkout) cannot include `fuel types` if split_fuel==True"
        )
        self.assertTrue(expected_err in actual_msg, f"Expected {expected_err} in {actual_msg}")


class TestECMPrepArgsTranslate(unittest.TestCase, Utils):
    # Tests for the translation of cli/yml args for use in ecm_prep.py

    default_translated = {
        "site_energy": False,
        "captured_energy": False,
        "alt_regions": False,
        "tsv_type": None,
        "tsv_daily_hr_restrict": None,
        "tsv_sys_shape_case": None,
        "tsv_season": None,
        "tsv_energy_agg": None,
        "tsv_power_agg": None,
        "tsv_average_days": None,
        "sect_shapes": False,
        "rp_persist": False,
        "verbose": False,
        "health_costs": False,
        "split_fuel": False,
        "no_scnd_lgt": False,
        "floor_start": None,
        "pkg_env_costs": False,
        "exog_hp_rate_scenario": None,
        "switch_all_retrofit_hp": False,
        "alt_ref_carb": False,
        "grid_decarb_level": None,
        "grid_assesment_timing": None,
        "adopt_scn_restrict": ["Technical potential", "Max adoption potential"],
        "retrofit_type": None,
        "retrofit_multiplier": None,
        "retrofit_mult_year": None,
        "add_typ_eff": False,
        "pkg_env_sep": False,
        "detail_brkout": False,
        "fugitive_emissions": False,
        "tsv_metrics": False,
        "retro_set": ["1", None, None],
        "exog_hp_rates": False,
        "grid_decarb": False,
    }
    valid_yml_translated = {
        "site_energy": True,
        "captured_energy": False,
        "alt_regions": "EMM",
        "tsv_type": "energy",
        "tsv_daily_hr_restrict": "all",
        "tsv_sys_shape_case": "total reference",
        "tsv_season": "summer",
        "tsv_energy_agg": "average",
        "tsv_power_agg": None,
        "tsv_average_days": "weekdays",
        "sect_shapes": False,
        "rp_persist": True,
        "verbose": False,
        "health_costs": False,
        "split_fuel": False,
        "no_scnd_lgt": False,
        "floor_start": None,
        "pkg_env_costs": "1",
        "exog_hp_rate_scenario": "aggressive",
        "switch_all_retrofit_hp": False,
        "alt_ref_carb": False,
        "grid_decarb_level": "full",
        "grid_assesment_timing": "after",
        "adopt_scn_restrict": ["Max adoption potential"],
        "retrofit_type": "increasing",
        "retrofit_multiplier": 1.2,
        "retrofit_mult_year": 2030,
        "add_typ_eff": True,
        "pkg_env_sep": False,
        "detail_brkout": "6",
        "fugitive_emissions": [1, 1],
        "retro_set": ["3", 1.2, 2030],
        "exog_hp_rates": ["aggressive", "2"],
        "grid_decarb": ["1", "2"],
        "tsv_metrics": ["1", "1", "1", "2", "1", "2"],
    }

    def test_translate_empty_cli(self):
        args = ecm_args([])
        self._assert_arg_vals(args, self.default_translated)

    def test_translate_valid_cli(self):
        cli_args = [
            "--add_typ_eff",
            "--alt_regions",
            "EMM",
            "--detail_brkout",
            "regions",
            "fuel types",
        ]
        args = ecm_args(cli_args)
        self.assertEqual(args.add_typ_eff, True)
        self.assertEqual(args.alt_regions, "EMM")
        self.assertEqual(args.detail_brkout, "6")

        cli_args = [
            "--detail_brkout",
            "buildings",
            "--retrofit_type",
            "increasing",
            "--retrofit_multiplier",
            "2",
            "--retrofit_mult_year",
            "2030",
        ]
        args = ecm_args(cli_args)
        self.assertEqual(args.detail_brkout, "3")
        self.assertEqual(args.retro_set, ["3", 2.0, 2030])

    def test_translate_from_empty_cfg(self):
        args = ecm_args(["--yaml", self.empty_yml_pth])
        self._assert_arg_vals(args, self.default_translated)

    def test_translate_from_valid_cfg(self):
        args = ecm_args(["--yaml", self.valid_yml_pth])
        self._assert_arg_vals(args, self.valid_yml_translated)

    def test_translate_cli_overwrite(self):
        # Ensure cli arguments take precedence over yml
        cli_args = [
            "--yaml",
            self.valid_yml_pth,
            "--adopt_scn_restrict",
            "Technical potential",
            "--fugitive_emissions",
            "low-gwp refrigerant",
        ]
        update_dict = {"adopt_scn_restrict": ["Technical potential"], "fugitive_emissions": [0, 2]}
        args = ecm_args(cli_args)
        self._assert_arg_vals(args, copy.deepcopy(self.valid_yml_translated), update_dict)


if __name__ == "__main__":
    unittest.main()
