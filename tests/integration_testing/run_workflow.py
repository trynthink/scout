from pathlib import Path
import sys
sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))
from scout import ecm_prep  # noqa: E402
from scout.ecm_prep_args import ecm_args  # noqa: E402
from scout import run  # noqa: E402


def run_workflow():
    # Run ecm_prep.py
    opts = ecm_args(
        ["--add_typ_eff", "--rp_persist", "--alt_regions_option", "EMM"]
    )
    ecm_prep.main(opts)

    # Run run.py
    opts = run.parse_args([])
    run.main(opts)


if __name__ == "__main__":
    run_workflow()
