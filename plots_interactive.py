#!/usr/bin/env python3

################################################################################
# file: plots_interactive.py
#
# define and run a dash application to allow end users to explore Scout
# diagnostic grpahics interactively.
#
################################################################################

import sys, getopt
import os.path
from plots_utilities import ECM_PREP


################################################################################
# Define to do if the file is run directory

# Define some help documentation which will be conditionally shown to the end
# user.
help_usage = "Usage: plots_interactive.py [options]"
help_options = """
Options:
  -h --help          Print this help and exit"
  -d --debug         If present, run the app with debug = True"
  -p --port=N        The port to run the dash app through"
  --ecm_prep=FILE    Path to a ecm_prep.json FILE, the results of ecm_prep.py"
  --ecm_results=FILE Path to a ecm_results.json FILE, the results of run.py"
"""


if __name__ == "__main__":

    # get command line options
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                "hdp:", ["help", "debug", "port=", "ecm_results=", "ecm_prep="])
    except getopt.GetoptError:
        print(help_usage)
        print("Get more details by running: plots_interactive.py -h")
        sys.exit(2)

    # set default values for command line arguments
    ecm_prep    = "./supporting_data/ecm_prep.json"
    ecm_results = "./results/ecm_results.json"
    debug       = False
    port        = 8050

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print(help_usage)
            print(help_options)
            sys.exit()
        elif opt in ("-r", "--ecm_results"):
            ecm_results = arg
        elif opt in ("-p", "--ecm_prep"):
            ecm_prep = arg
        elif opt in ("-d", "--debug"):
            debug = True
        elif opt in ("-p", "--port"):
            port = arg

    if not os.path.exists(ecm_prep):
        print(f"{ecm_prep} can not be reached or does not exist.")
        sys.exit(1)
    if not os.path.exists(ecm_results):
        print(f"{ecm_results} can not be reached or does not exist.")
        sys.exit(1)

    # Import the Data sets
    print(f"Importing data from {ecm_prep}")
    ecm_prep = ECM_PREP(path = ecm_prep)
    print(ecm_prep.info())
    print(f"\n\necm_prep.lifetime_baseline:\n {ecm_prep.lifetime_baseline}")
    print(f"\n\necm_prep.lifetime_measure:\n {ecm_prep.lifetime_measure}")
    print(f"\n\necm_prep.stock:\n {ecm_prep.stock}")
    print(f"\n\necm_prep.master_mseg:\n {ecm_prep.master_mseg}")
    print(f"\n\necm_prep.master_mseg_cost:\n {ecm_prep.master_mseg_cost}")
    print(f"\n\necm_prep.mseg_out_break:\n {ecm_prep.mseg_out_break}")

    print(f"Importing data from {ecm_results}")
    ecm_results




################################################################################
#                                 End of File                                  #
################################################################################

