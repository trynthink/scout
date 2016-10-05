.. _tlcomponents:

Heating and Cooling Load Components
===================================

This section describes the purpose and derivation of the thermal load components files for :repo_file:`residential <Res_TLoads_Final.txt>` and :repo_file:`commercial <Com_TLoads_Final.txt>` buildings.

.. _tlcomponents_overview:

Overview
--------

Energy conservation measures (ECMs) evaluated by Scout yield savings on either the supply or the demand side of energy consumption. As an example of the former, consider the replacement of electric heating and cooling equipment with a more efficient heat pump: in this case, the new heat pump reduces the amount of electricity needed to provide a fixed amount of heating/cooling to a building space. As the absolute heating/cooling *load* is unchanged, the ECM’s energy savings come from the more efficient manner in which the heating/cooling is supplied.

Conversely, a demand side ECM reduces the absolute load that must be met for a given end use, leaving the supply for that end use unchanged. An example of such a ECM is highly insulating window replacements: in offering improved resistance against thermal conduction from the space to the outdoors, the replacement reduces the amount of heating energy that must be added to the space to maintain a comfortable air temperature, allowing demand side energy savings.

This section focuses on the evaluation of demand side ECMs for the heating and cooling end uses. Here, we might be interested how much national heating and/or cooling energy could be saved through the highly insulating window replacements previously mentioned, or by other ECMs relating to the building envelope such as adding insulation or shading devices, amongst many others. In these cases, estimations of energy savings require an understanding of how a building’s heating/cooling energy use is partitioned. For example, were we to evaluate the heating energy savings potential of highly insulating windows, we would first need to know the amount of heating energy that is lost through a building's windows to the outdoors (which the insulating window would reduce). This figure is obtained by multiplying a building’s total heating energy use by the percentage of heating load attributable to conduction losses through windows, referred to subsequently as the heating load "component” for window conduction.

While the energy use part of this calculation is easily drawn from the U.S. Energy Information Administration (EIA) `Annual Energy Outlook (AEO)`_, establishing heating and cooling load component values for a range of building types and geographical regions is less straightforward. To improve the transparency of this process, the section below outlines the steps that were used to derive a new set of thermal load components for each of the AEO residential and commercial building types, across all nine U.S. census regions. This approach yields two files, :repo_file:`Res_TLoads_Final.txt` and :repo_file:`Com_TLoads_Final.txt`.

.. _Annual Energy Outlook (AEO): http://www.eia.gov/forecasts/aeo/index.cfm

Thermal load components data are drawn in large part from two simulation studies of residential and commercial buildings by :repo_file:`Huang, Hanford, and Yang (1999) <1999 Residential heating and cooling loads component analysis.pdf>` and :repo_file:`Huang and Franconi (1999) <1999 Commercial heating and cooling loads component analysis.pdf>`, respectively. The residential study uses parametric computer simulations of 112 single-family and 63 multi-family residential building prototypes to quantify the contributions of building components such as roofs, walls, windows, infiltration, outside air, lighting, equipment, and people to the aggregate heating and cooling loads in U.S. residential buildings; the commercial study does the same for aggregate commercial heating and cooling loads using computer simulations of 120 commercial building prototypes.

.. _tlcomponents_derivation:

Deriving Heating & Cooling Load Components
------------------------------------------

The residential and commercial building thermal load component values are derived from the data in the simulation study publications.

1. Identify relevant tables in the residential and commercial simulation studies.

* Residential: Component Loads Tables, pages C3–C11.

    * Simulations cover all three AEO residential building types and nine U.S. census regions, for heating and cooling end uses separately.
    * Baseline tables include unnecessary sub-groupings of residential thermal loads data, including by building vintage and for multiple cities within each census division.
    * Each simulated building type/location combination has an associated number of buildings in the U.S. stock reported with it for weighting purposes.
 
* Commercial: Tables 18-23, pages 39-44.

    * Simulations cover nine of eleven AEO commercial building types and a city in each of the five AIA climate zones for heating and cooling end uses separately.
    * Baseline tables include unnecessary sub-groupings of commercial thermal loads data, including by building vintage and in some cases by size classes that do not correspond to AEO (i.e., large/small retail).
    * Each simulated building type/location combination has an associated floor space square footage in the U.S. stock reported with it for weighting purposes.
    * Map commercial table building types to AEO building types.
        * Retail -> Merch./Service
        * Hotel -> Lodging
        * Fast/sit down restaurants -> Food Service
        * Supermarket -> Food Sales
        * School -> Education
        * Hospital -> Healthcare
        * Lg./Sm. Office, Warehouse -> Same in AEO

2. Translate PDF table information to text tables.

* Manually input data from the PDF publications, as in :repo_file:`Res_TLoads_Base.csv` and :repo_file:`Com_TLoads_Base.csv`.

3. Condense CSV tables into final set of thermal load components data using an R script.

*R pseudocode*

    #. Import \*_Base CSV file.
    #. Find subset of CSV rows associated with each unique combination of census division (residential) or climate division (commercial), AEO building type, and heating or cooling end use.
    #. For each subset of rows, calculate a weighted average of the thermal load components across all rows using the number of buildings (residential) or square footage floor space (commercial) associated with each row to establish weighting factors.
    #. Combine the thermal load components calculated for each unique combination of census/climate, AEO building type, and end use into a master table.
    #. Calculate thermal load components for missing AEO building types using a weighted combination of similar and available AEO building types (*commercial only*).

        * The missing “Assembly” commercial building type is created as a floor area weighted combination of “Education”, “Small Office”, and “Merch/Service” building types.
        * The missing “Other” commercial building type is created as a floor area weighted combination of “Lodging”, “Large Office”, and “Warehouse” building types.
    
    #. Translate AIA climate zone geographical breakdowns to census division breakdowns (*commercial only*).
    
        * Map U.S. commercial floor area in each AIA climate zone to floor area in each census division using Commercial Building Energy Consumption Survey (CBECS) `raw data`__.
        * Conversion factors for mapping AIA climate zone to census division for both residential and commercial buildings are available from :repo_file:`Res_Cdiv_Czone_ConvertTable_Final.txt` and :repo_file:`Com_Cdiv_Czone_ConvertTable_Final.txt`. Note that residential data were drawn from the Residential Energy Consumption Survey (RECS) `raw data`__.

    #. Write the final thermal load components table to a text file.

4. :repo_file:`Res_TLoads_Final.txt` and :repo_file:`Com_TLoads_Final.txt` files contain final thermal loads components broken down by census division, AEO building type, and heating/cooling end use for further analysis.

.. Anonymous links for content under R pseudocode bullet
.. __: http://www.eia.gov/consumption/commercial/data/2003/index.cfm?view=microdata
.. __: http://www.eia.gov/consumption/residential/data/2009/index.cfm?view=microdata

.. _tlcomponents_references:

References
----------
Huang J, Hanford J, Yang F. (1999). Residential heating and cooling loads component analysis (LBNL-44636). Berkeley, CA: Lawrence Berkeley National Laboratory.

Huang J, Franconi E. (1999). Commercial heating and cooling loads component analysis (LBNL-37208). Berkeley, CA: Lawrence Berkeley National Laboratory.
