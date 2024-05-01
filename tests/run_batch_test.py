import unittest
from pathlib import Path
from scout.run_batch import BatchRun
from scout.config import FilePaths as fp


class TestBatchRun(unittest.TestCase):

    @classmethod
    def setUpClass(self):
        self.yml_dir = Path(__file__).parent / "test_files" / "batch_files"
        self.yml_files = sorted([yml for yml in self.yml_dir.iterdir()])
        self.batch_run = BatchRun(self.yml_dir)

    def trim_dir_path(self, path: Path, levels: int = 2):
        # Trim directory to assert against the specified number of levels (lowest first)
        return str(Path(*path.parts[-levels:])).replace("\\", "/")

    def test_yml_groups(self):
        # Test ymls are grouped by common ecm_prep args
        yml_grps = self.batch_run.group_common_configs(self.yml_dir)
        yml_grp_names = [[yml.name for yml in yml_grp] for yml_grp in yml_grps]
        expected_grps = [['config1.yml', 'config2.yml'], ['config3.yml']]

        self.assertEqual(yml_grp_names, expected_grps, yml_grp_names)

    def test_ecm_concat(self):
        # Test retrieval of ECMs from numerous ymls
        ecm_list = self.batch_run.get_ecm_files(self.yml_files)
        expected_ecms = ['Best Com. ASHP, Env., PC (EE+DF-FS)',
                         'Best Com. ASHP, Env., PC (EE+DF-FS) CC',
                         'Best Com. Air Sealing (Exist)',
                         'Best Com. Air Sealing (New)',
                         'Residential Walls, IECC c. 2021']
        self.assertEqual(sorted(ecm_list), expected_ecms)

    def test_auto_results_dir(self):
        # Test creation of results directories
        # Using `results_directory` arg
        _ = self.batch_run.get_run_opts(self.yml_dir / "config1.yml")
        self.assertEqual(self.trim_dir_path(fp.RESULTS), "results/custom_dir_config1")
        self.assertEqual(self.trim_dir_path(fp.PLOTS, 3), "results/custom_dir_config1/plots")

        # Automatically set based on config name
        _ = self.batch_run.get_run_opts(self.yml_dir / "config2.yml")
        self.assertEqual(self.trim_dir_path(fp.RESULTS), "results/config2")
        self.assertEqual(self.trim_dir_path(fp.PLOTS, 3), "results/config2/plots")


if __name__ == '__main__':
    unittest.main()
