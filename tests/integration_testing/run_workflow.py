from __future__ import annotations
from pathlib import Path
import io
import sys
import logging
import cProfile
import pstats

sys.path.append(str(Path(__file__).parent.parent.parent.parent))
sys.path.append(str(Path(__file__).parent.parent.parent))
from scout import ecm_prep  # noqa: E402
from scout.ecm_prep_args import ecm_args  # noqa: E402
from scout import run  # noqa: E402

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s: %(message)s",
    datefmt="%d-%b-%y %H:%M:%S",
)


def run_workflow() -> None:
    """Runs the full Scout workflow profiling ecm_prep.py and run.py seperately
    """

    results_dir = Path(__file__).parent / "results"
    
    # Run ecm_prep.py
    opts = ecm_args(["--alt_regions_option", "EMM"])
    run_with_profiler(ecm_prep.main, opts, results_dir / "profile_ecm_prep.csv")
    
    # Run run.py
    opts = run.parse_args([])
    run_with_profiler(run.main, opts, results_dir / "profile_run.csv")
    
def run_with_profiler(func: Callable[[argparse.Namespace], None], args: argparse.Namespace, output_file: pathlib.Path) -> None:
    """Runs a function wrapped in a profiler using the cProfile library

    Args:
        func (Callable[[argparse.Namespace], None]): A function that takes argsparse.Namespace arguments
        args (argparse.Namespace): The arguments to the function
        output_file (pathlib.Path): .csv filepath to write profiling stats 
    """
    pr = cProfile.Profile()
    pr.enable()
    func(args)
    pr.disable()
    write_profile_stats(pr, output_file)
    
def write_profile_stats(pr: cProfile.Profile, filepath: pathlib.Path) -> None:
    """Writes profile stats and stores a .csv file

    Args:
        pr (cProfile.Profile): Profile instance that has previously been enabled (pr.enable())
        filepath (pathlib.Path): .csv filepath to write profiling stats 
    """
    
    # Capture io stream
    result = io.StringIO()
    pstats.Stats(pr, stream=result).sort_stats('cumulative').print_stats()
    result = result.getvalue()

    # Parse stats and write to csv
    top_data, result = result.split("ncalls")
    top_data = "\n".join([line.strip() for line in top_data.split("\n")])
    result = "ncalls" + result
    result = "\n".join([",".join(line.rstrip().split(None, 5)) for line in result.split("\n")])
    result_out = top_data + result

    f = open(filepath, "w")
    f.write(result_out)
    f.close()
    logger.info(f"Wrote profiler stats to {filepath}")


if __name__ == "__main__":
    run_workflow()
