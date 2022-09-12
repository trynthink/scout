import sys, getopt
import os.path
from plots_utilities import ECM_PREP
from plots_utilities import ECM_RESULTS


################################################################################
# Define some help documentation which will be conditionally shown to the end
# user.
help_usage = "Usage: emf_aggregation.py [options]"
help_options = """
Options:
  -h --help          Print this help and exit
  --ecm_prep=FILE    Path to a ecm_prep.json FILE, the results of ecm_prep.py
  --ecm_results=FILE Path to a ecm_results.json FILE, the results of run.py
"""

if __name__ == "__main__":
    # get command line args
    try:
        opts, args = getopt.getopt(sys.argv[1:], "h:", ["help", "ecm_results=", "ecm_prep="])
    except getopt.GetoptError:
        print(help_usage)
        print("Get more details by running: plots_interactive.py -h")
        sys.exit(2)

    # set default values for command line arguments
    ecm_prep_path    = "./supporting_data/ecm_prep.json"
    ecm_results_path = "./results/ecm_results.json"

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_usage)
            print(help_options)
            sys.exit()
        elif opt in ("--ecm_results"):
            ecm_results_path = arg
        elif opt in ("--ecm_prep"):
            ecm_prep_path = arg

    if not os.path.exists(ecm_prep_path):
        print(f"{ecm_prep_path} can not be reached or does not exist.")
        sys.exit(1)
    if not os.path.exists(ecm_results_path):
        print(f"{ecm_results_path} can not be reached or does not exist.")
        sys.exit(1)

    ############################################################################
    # Import the Data sets
    # print(f"Importing data from {ecm_prep_path}")
    # ecm_prep = ECM_PREP(path = ecm_prep_path)

    print(f"Importing data from {ecm_results_path}")
    ecm_results = ECM_RESULTS(path = ecm_results_path)

    #print(f"Building data set for Unompeted versus Competed metrics")
    #ecm_prep_v_results = ECM_PREP_VS_RESULTS(ecm_prep, ecm_results)

    print(ecm_results)


