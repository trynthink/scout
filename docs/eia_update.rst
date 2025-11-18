.. _eia-update:

EIA Updates
=================

Scout's residential and commercial baseline energy use is anchored to the
U.S. Energy Information Administration (EIA) Annual Energy Outlook (AEO).
When Scout is updated to a new AEO release, we use a small helper script to
compare Scout's internal microsegment totals against the official AEO tables.

The script lives in ``scout/AEO_update_helpers/baseline_comparison.py``.
At a high level it:

* loads Scout's processed AEO microsegments file (``mseg_res_com_cz.json``),
* aggregates energy use by building class, fuel type, and end use,
* queries the EIA AEO API for the matching time-series,
* compares Scout vs. EIA year-by-year, and
* prints summary tables showing any large differences.

Running the EIA update check
----------------------------

1. **Create a local `.env` file (not committed to git)** in the project root
   (the same folder as ``pyproject.toml``) with your EIA API key::

      EIA_API_KEY=YOUR_REAL_KEY_HERE

   You can request a free key from EIA at https://www.eia.gov/opendata/register.php.

2. **Install Scout and its dependencies** into a virtual environment
   (see :ref:`install-guide`).

3. **From the project root, run the helper script**, for example::

      python -m scout.AEO_update_helpers.baseline_comparison --year 2025

   Use ``--verbose`` to see the underlying API calls and any combinations where
   data are missing.

The output includes per-combination comparisons and simple roll-up tables by
building class and fuel type. These reports make it easier to confirm that
Scout's baseline matches the chosen AEO reference.
