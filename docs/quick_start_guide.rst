.. Substitutions
.. |cmd| unicode:: U+2318

.. _quick-start-guide:

Quick Start Guide
=================

If you're new to Scout, this is the right place to get started. Steps for running a Scout analysis from start to finish are listed below; additional guidance on certain steps can be found in linked tutorials.

.. _qsg-installation-step:

1. Setup Scout and prerequisites
--------------------------------

`Download the latest version of Scout`_ and follow the :ref:`install-guide` to configure the programs required for Scout to run.

.. Note::
   If you'd like to execute the full set of standard Scout measures (ECMs) that are included with the installation in the folder |html-filepath| ./ecm_definitions\ |html-fp-end|, download the file |html-filepath| Latest_BM_Shapes.zip |html-fp-end| `here`_ and unzip/add its contents to the folder |html-filepath| ./ecm_definitions/energyplus_data/savings_shapes\ |html-fp-end|.  

.. _qsg-create-ecm-step:

2. Create new ECM definition(s) (optional)
------------------------------------------

Visit the Scout web interface’s `ECM Summaries Page`_. Register and/or sign in to your Scout account using the "Register" or "Sign In" button at the top right of the page. Once signed in, click the "Add ECM" dropdown at the top right of the page and select the "Write New ECM" option. Follow the steps for generating a new ECM definition; the ECM definition file will be downloaded to your computer. Move the downloaded ECM to the |html-filepath| ./ecm_definitions |html-fp-end| folder (see Web Interface :ref:`tuts-2-web` for additional guidance).

Alternatively, follow Local Execution :ref:`tuts-1` to develop your own ECM definition(s) using a text editor.

.. _qsg-cmdline-step:

3. Open the command line interface
----------------------------------

Open a Terminal window (Mac) [#]_ or command prompt (Windows) [#]_ and navigate to the Scout project directory (shown with the example location |html-filepath| ./Documents/projects/scout-0.1\ |html-fp-end| – substitute the path to your Scout directory) by entering the following command line argument:

**Windows** ::

   cd Documents\projects\scout-0.1

**Mac** ::

   cd Documents/projects/scout-0.1

.. _qsg-ecm-prep-step:

4. Run using project configuration file(s) (optional)
-----------------------------------------------------
Scout scnearios can be defined by directly passing arguments to Python scripts, or with the use of a .yml configuration file, which stores argument values in a consistent, trackable manner. This approach also provides the benefit of storing argument values to both core modules of Scout, ecm_prep.py and run.py. Guidance on creating configuration files is found in :ref:`tuts-2`. To run a single scenario, enter the following command line arguments, where <my_config.yml> refers to a custom configuration file:

**Windows** ::

   py -3 scout/ecm_prep.py --yaml <my_config.yml>
   py -3 scout/run.py --yaml <my_config.yml>

**Mac** ::

   python3 scout/ecm_prep.py --yaml <my_config.yml>
   python3 scout/run.py --yaml <my_config.yml>

.. note::
   If running scenarios with a configuration file, then steps 4-6 in the Quick Start Guide are not needed.

Running multiple configuration files
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Batches of configuration files can also be run with the use of the run_batch.py module. This automatically runs both ecm_prep.py and run.py for a set of configuration files in a common directory. To run files in a batch, enter the following command line argument, where <config_directory> refers to a directory containing a set of custom configuration files (see :ref:`tuts-2-batch` for further guidance):

**Windows** ::

   py -3 scout/run_batch.py --batch <config_directory>

**Mac** ::

   python3 scout/run_batch.py --batch <config_directory>


5. Prepare ECMs for analysis
----------------------------

To prepare measures for :ref:`EIA Electricity Market Module (EMM) <emm-reg>` regions, enter the following command line argument (see Local Execution :ref:`tuts-3` for additional guidance and execution :ref:`options <tuts-3-cmd-opts>`):

**Windows** ::

   py -3 scout/ecm_prep.py

**Mac** ::

   python3 scout/ecm_prep.py


.. Note::
   The standard set of ECM definitions included in |html-filepath| ./ecm_definitions |html-fp-end| requires the EMM region setting to execute. Only new or edited ECM definitions are updated in this step.

.. tip::
   Preparing the full set of standard ECM definitions in |html-filepath| ./ecm_definitions |html-fp-end| will take several minutes. For a quicker test run, consider restricting the contents of this folder to just one or a handful of measures of interest while setting the contents of the file |html-filepath| ./ecm_definitions/package_ecms.json |html-fp-end| to a blank list |html-filepath| []\ |html-fp-end|.  

.. _qsg-modify-active-ecm-step:

6. Modify active list of ECMs (optional)
----------------------------------------

Enter the following command line argument (see Local Execution :ref:`tuts-ecm-list-setup` for additional guidance):

**Windows** ::

   py -3 scout/run_setup.py

**Mac** ::

   python3 scout/run_setup.py

.. _qsg-run-analysis-step:

7. Run analysis on active ECMs
------------------------------

Enter the following command line argument (see Local Execution :ref:`tuts-analysis` for additional guidance and execution :ref:`options <tuts-5-cmd-opts>`):

**Windows** ::

   py -3 scout/run.py

**Mac** ::

   python3 scout/run.py

.. _qsg-view-results-step:

8. View results plots and data
------------------------------

.. Visit the Scout web interface’s `Analysis Results Page`_. Click the "Custom Results" dropdown arrow towards the top right of the page, then click "Upload File" to upload results from your Scout run in the previous step (data found in |html-filepath| ./results/plots/ecm_results.json |html-fp-end|). Once the data are uploaded, click through the "Energy," "|CO2|," "Cost," and "Financial Metrics" tabs towards the top of the page to interactively visualize your results (see Web Interface :ref:`tuts-3-web` for additional guidance).

Open the |html-filepath| ./results/plots |html-fp-end| folder to view local plots of your results and access underlying data in Excel (see Local Execution :ref:`tuts-results` for additional guidance). Local plots are organized in folders by :ref:`adoption scenario <overview-adoption>` and :ref:`plotted metric of interest <overview-results>` (i.e., |html-filepath| ./results/plots/(adoption scenario)/(metric of interest)\ |html-fp-end|). Raw data for each adoption scenario's plots are stored in the XLSX files beginning with "Summary_Data."


.. _Download the latest version of Scout: https://github.com/trynthink/scout/releases/latest

.. _here: https://doi.org/10.5281/zenodo.4602369

.. _ECM Summaries Page: https://scout.energy.gov/ecms.html

.. _Analysis Results Page: https://scout.energy.gov/energy.html

.. rubric:: Footnotes

.. [#] To open Terminal, press |cmd|\-space on your keyboard, begin typing "terminal" in the search bar that opens, and select Terminal from the list of programs that appear.
.. [#] To launch the command prompt, press Win+R on your keyboard, type "cmd" in the search bar that opens, and press Enter.
