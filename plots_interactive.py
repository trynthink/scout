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
from plots_utilities import ECM_RESULTS


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
        elif opt in ("--ecm_results"):
            ecm_results = arg
        elif opt in ("--ecm_prep"):
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

    ############################################################################
    # Import the Data sets
    print(f"Importing data from {ecm_prep}")
    ecm_prep = ECM_PREP(path = ecm_prep)
    print(ecm_prep)

    print(f"Importing data from {ecm_results}")
    ecm_results = ECM_RESULTS(path = ecm_results)

    print(ecm_results)

    ############################################################################
    # build useful things for ui
    #ecms = [{"label" : l, "value" : l} for l in set(ecm_results.financial_metrics.ecm)]
    #years = [y for y in set(ecm_results.mas_by_category.year)]
    #years.sort()

    ############################################################################
    # run the dash app
    #print("Launching dash app")
    #app.run_server(port = port, debug = debug)



################################################################################
#                                 End of File                                  #
################################################################################

