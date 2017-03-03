.. _overview:

An Overview of Scout
====================

.. _overview-who-what:

What is Scout and who should use it?
------------------------------------

* Scout is a software program that estimates the national energy savings, avoided |CO2| emissions, and operating cost impact potential of various :ref:`energy conservation measures (ECMs) <overview-ecms>` in the U.S. residential and commercial building sectors.
* With Scout, users can explore both the savings impact and cost-effectiveness of ECMs under multiple adoption scenarios across the entire U.S. or a subset of climate zone(s).
* Scout can help organizations with large building energy efficiency programs or portfolios frame their high-level program benefits and costs. Researchers, building managers, architects/engineers, and the general public can also use Scout to determine where certain energy-saving technologies or approaches of interest fit into the larger U.S. market for building energy efficiency.
* Scout is under active development by the U.S. Department of Energy Building Technologies Office (BTO). The software can be downloaded or forked_ from the `GitHub repository`_, however users are encouraged to wait until an initial release of the software is made.

.. _forked: https://help.github.com/articles/fork-a-repo/
.. _GitHub repository: https://www.github.com/trynthink/scout

.. _overview-results:

Results specify U.S. energy, |CO2|, and cost savings
----------------------------------------------------

* Scout yields the following national-scale results for individual ECMs:

   * primary energy savings (in quadrillion Btus),
   * avoided |CO2| emissions (in million metric tons),
   * operational cost savings, and
   * per unit cost effectiveness, expressed by multiple financial metrics including `internal rate of return (IRR)`_, `simple payback`_, `cost of conserved energy (CCE)`_, and cost of conserved |CO2| (CCC) (conceptually equivalent to CCE, but should be compared with |CO2| prices).

* Results may be aggregated across multiple ECMs and filtered by variables such as climate zone, building type/vintage, and end use.

.. _internal rate of return (IRR): https://docs.scipy.org/doc/numpy/reference/generated/numpy.irr.html
.. _simple payback: https://beopt.nrel.gov/sites/beopt.nrel.gov/files/help/Simple_Payback.htm
.. _cost of conserved energy (CCE): https://eetd.lbl.gov/ee/price-graphic.html

.. _overview-ecms:

Scout ECMs and their baseline markets
-------------------------------------

* ECMs represent building technologies or operational approaches that improve upon the unit efficiency and/or lifetime operational costs of the comparable incumbent or “business-as-usual” technology or approach.
* :ref:`ECMs are characterized <analysis-step-1>` by their energy efficiency, installed cost, lifetime, and applicable baseline markets; whether they add-on to or fully replace the service of a “business-as-usual” technology; whether they involve fuel switching; and their year of market entry and exit.
* The :ref:`applicable baseline market <ecm-applicable-baseline-market>` for an ECM enumerates all of the :ref:`climate zones <json-climate_zone>`, :ref:`building types <json-bldg_type>`, :ref:`structure types <json-structure_type>`, :ref:`end uses <json-end_use>`, :ref:`fuel types <json-fuel_type>`, and :ref:`technologies <json-technology>` that are relevant to an ECM.
* ECM definitions can include distinct cost, efficiency, and lifetime values for each climate zone, building type, fuel type, end use, and/or technology type; probability distributions may also be placed on ECM cost, efficiency, and lifetime inputs.

.. _overview-adoption:

ECMs are adopted one of two ways
--------------------------------

There are two different scenarios that are used to represent consumer adoption of an ECM.

* The technical potential scenario assumes that as soon as an ECM is introduced, the entire baseline market instantaneously and completely switches to the new ECM, and the ECM retains a complete sales monopoly in subsequent years. Results from this scenario represent the maximum impact an ECM could have, limited only by baseline market size. 
* The max adoption potential scenario assumes an ECM is only able to capture the portion of its baseline market associated with new construction and retrofit or replacement of existing equipment in a given year. Results from this scenario represent an ECM’s maximum impact considering typical building and equipment turnover and generally show a gradual accumulation of ECM savings over time.

.. _overview-competition:

Competition of overlapping ECM markets
--------------------------------------

* In cases where multiple ECMs apply to the same baseline market, the market is apportioned among the competing ECMs based on each ECM’s incremental capital costs and operating cost savings.
* In general, ECMs with lower incremental capital costs and higher operating cost savings will capture a greater share of a baseline market being competed. The importance of capital and operating cost savings on market share are weighted differently depending on the end use affected.
* ECM competition is needed to ensure there is no double-counting of energy, |CO2|, and operating cost savings impacts when aggregating results across multiple ECMs.