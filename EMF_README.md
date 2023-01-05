EMF DATA PREP README
====================

To generate a file in the form required for upload to the [IIASA EMF 37 Scenario Explorer](https://data.ene.iiasa.ac.at/emf37-internal/#/workspaces), the following workflow is currently required.

```
$ python emf_aggregation.py
$ python emf_initial_file_reprocessor.py
$ python emf_iamc_file_restructure.py <relative path to spreadsheet output by emf_initial_file_reprocessor.py>
```

At the moment, this workflow is rigidly defined for a fixed set of results. It would be helpful if the user could define the desired results files (in addition to the baseline) to include in a given output file and the corresponding scenario name for each results file.