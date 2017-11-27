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

.. _qsg-create-ecm-step:

2. Create new ECM definition(s) (optional)
------------------------------------------

Visit the Scout web interface’s `ECM Summaries Page`_. Click the "Add New ECM" button towards the top of the page and follow the steps for creating a new ECM definition; the ECM definition will be downloaded to your computer. Move the downloaded ECM to the |html-filepath| ./ecm_definitions |html-fp-end| folder (see Web Interface :ref:`tuts-2-web` for additional guidance).

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

4. Prepare ECMs for analysis
----------------------------

Enter the following command line argument (see Local Execution :ref:`tuts-2` for additional guidance):

**Windows** ::

   py -3 ecm_prep.py

**Mac** ::

   python3 ecm_prep.py

.. Note::
   Only new or edited ECM definitions are updated in this step.

.. _qsg-modify-active-ecm-step:

5. Modify active list of ECMs (optional)
----------------------------------------

Enter the following command line argument (see Local Execution :ref:`tuts-ecm-list-setup` for additional guidance):

**Windows** ::

   py -3 run_setup.py

**Mac** ::

   python3 run_setup.py

.. _qsg-run-analysis-step:

6. Run analysis on active ECMs
------------------------------

Enter the following command line argument (see Local Execution :ref:`tuts-analysis` for additional guidance):

**Windows** ::

   py -3 run.py

**Mac** ::

   python3 run.py

.. _qsg-view-results-step:

7. View results plots and data
------------------------------

Visit the Scout web interface’s `Analysis Results Page`_. Click the "Custom Results" dropdown arrow towards the top right of the page, then click "Upload File" to upload results from your Scout run in the previous step (data found in |html-filepath| ./results/plots/ecm_results.json |html-fp-end|). Once the data are uploaded, click through the "Energy," "|CO2|," "Cost," and "Financial Metrics" tabs towards the top of the page to interactively visualize your results (see Web Interface :ref:`tuts-3-web` for additional guidance).

Alternatively, open the |html-filepath| ./results/plots |html-fp-end| folder to view local plots of your results and access underlying data in Excel (see Local Execution :ref:`tuts-results` for additional guidance). Local plots are organized in folders by :ref:`adoption scenario <overview-adoption>` and :ref:`plotted metric of interest <overview-results>` (i.e., |html-filepath| ./results/plots/(adoption scenario)/(metric of interest)\ |html-fp-end|). Raw data for each adoption scenario's plots are stored in the XLSX files beginning with "Summary_Data."


.. _Download the latest version of Scout: https://github.com/trynthink/scout/releases/latest

.. _ECM Summaries Page: https://scout.energy.gov/ecms.html

.. _Analysis Results Page: https://scout.energy.gov/energy.html

.. rubric:: Footnotes

.. [#] To open Terminal, press |cmd|\-space on your keyboard, begin typing "terminal" in the search bar that opens, and select Terminal from the list of programs that appear.
.. [#] To launch the command prompt, press Win+R on your keyboard, type "cmd" in the search bar that opens, and press Enter.
