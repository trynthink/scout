.. Substitutions
.. |--| unicode:: U+2013   .. en dash
.. |---| unicode:: U+2014  .. em dash, trimming surrounding whitespace
   :trim:

.. _tutorials:

Local Execution Tutorials
=========================

.. _tuts-1:

Tutorial 1: Creating and editing ECMs
-------------------------------------

Before beginning this tutorial, it is recommended that you review the :ref:`list of parameters <ecm-contents>` in an ECM definition.

The :ref:`json-schema` should always be in your back pocket as a reference. This section includes brief descriptions, allowable options, and examples for each of the fields in an ECM definition. You might want to have it open in a separate tab in your browser while you complete this tutorial, and any time you're authoring or editing an ECM. 

The example in this tutorial will demonstrate how to write new ECMs so that they will be compliant with all relevant formatting requirements and provide the :ref:`needed information <ecm-contents>` about a technology in the structure expected by the Scout analysis engine. This example is intentionally plain to illustrate the basic features of an ECM definition and is *not* an exhaustive description of all of the detailed options available to specify an ECM. These additional options are presented in the :ref:`ecm-features` section, and the :ref:`json-schema` has detailed specifications for each field in an ECM definition. In addition, this tutorial includes information about how to :ref:`edit existing ECMs <editing-ecms>` and :ref:`define package ECMs <package-ecms>`.

As a starting point for writing new ECMs, an empty ECM definition file is available for :download:`download </examples/blank_ecm.json>`. Reference versions of the tutorial ECMs are also provided for download to check one's own work following completion of the examples.

Each new ECM created should be saved in a separate file. To add new or edited ECMs to the analysis, the files should be placed in the |html-filepath| ./ecm_definitions |html-fp-end| directory. Further details regarding where ECM definitions should be saved and how to ensure that they are included in new analyses are included in :ref:`Tutorial 2 <tuts-2>`.

JSON syntax basics
~~~~~~~~~~~~~~~~~~

Each ECM for Scout is stored in a JSON_-formatted file. JSON files are human-readable (they appear as plain text) and are structured as (nested) pairs of *keys* and *values*, separated by a colon and enclosed with braces. [#]_ ::

   {"key": "value"}

.. warning::
   JSON files have important `formatting rules`_ that must be strictly observed. JSON files that do not follow these rules are "invalid" and cannot be used by any program.

.. _formatting rules:
.. _JSON: http://www.json.org

Keys are *always* text – both letters and numbers are acceptable – enclosed in double quotes. Values can take one of several forms, such as numbers, boolean values (i.e., true, false), or lists (multiple values separated by commas and enclosed in brackets). A value must always be provided for each key. ::

   {"temperature": 450}
   {"activated": true}
   {"preferred colors": ["red", "green", "blue"]}
   {"reported heights": [1.79, 1.83, 1.64, 1.91]}

There can be multiple key-value pairs at the same level, separated by commas. ::

   {"name": "HAL", "model": 9000, "service date": "1992-01-12"}

Values can also be additional key-value pairs, thus creating a nested structure. ::

   {"vehicle 1": {"make": "Ford", "model": "F-150"}}
   {"name": "HAL", "model": 9000, "service date": "1992-01-12",
    "manufacturing location": {"country": "US", "state": "IL", "city": "Urbana"}}

Among key-value pairs at the same level, the order of entries does not matter.

We will use these formatting guidelines to write new ECMs.


.. _example-ecm-1:

Your first ECM definition
~~~~~~~~~~~~~~~~~~~~~~~~~

The required information for defining this ECM will be covered in the same order as the :ref:`list of parameters <ecm-contents>` in the :ref:`analysis-approach` section. For all of the fields in the ECM definition, details regarding acceptable values, structure, and formatting are provided in the :ref:`ECM JSON schema <json-schema>`.

If after completing this tutorial you feel that you would benefit from looking at additional ECM definitions, you can browse the :repo_file:`ECM definition JSON files <ecm_definitions>` available on GitHub.

For this example, we will be creating an ECM for LED troffers for commercial buildings. Troffers are square or rectangular light fixtures designed to be used in a modular dropped ceiling grid commonly seen in offices and other commercial spaces.

The finished ECM specification is available to :download:`download </examples/led_troffers.json>` for reference.

To begin, the ECM should be given a descriptive name less than 40 characters long (including spaces). Details regarding the characteristics of the technology that will be included elsewhere in the ECM definition, such as the cost, efficiency, or lifetime, need not be included in the name. The key for the name is simply ``name``. ::

   {"name": "LED Troffers"}

If the ECM describes a technology currently under development, the name should contain the word "Prospective" in parentheses. If the ECM describes or is derived from a published standard or specification, its version number or year should be included in the name.

.. note::
   In this tutorial, JSON entries will be shown with leading and trailing ellipses to indicate that there is additional data in the ECM definition that appears before and/or after the text of interest. ::

      {...
       "key_text": "value",
       ...}


Applicable baseline market
**************************

The applicable baseline market parameters specify the climate zones, building types, structure types, end uses, fuel types, and specific technologies for the ECM. 

The climate zone(s) can be given as a single string, if only one climate zone applies, or as a list if a few climate zones apply. The climate zone entry options are outlined in the :ref:`ecm-baseline_climate-zone` section, and formatting details are in the :ref:`applicable section <json-climate_zone>` of the JSON schema. If the ECM is suitable for all climate zones, the shorthand string ``"all"`` can be used in place of a list of all of the climate zone names. These shorthand terms are discussed further in the :ref:`ecm-features-shorthand` section. 

LED troffers can be installed in buildings in any climate zone, and for convenience, the available shorthand term will be used in place of a list of all of the climate zone names. ::

   {...
    "climate_zone": "all",
    ...}

Building type options include specific residential and commercial building types, given in the :ref:`ecm-baseline_building-type` section, as well as several shorthand terms. A single string, list of strings, or shorthand value(s) are all allowable entries, as indicated in the :ref:`json-bldg_type` field reference. 

Though LED troffers are most commonly found in office and other small commercial settings, they are found to some limited extent in most types of commercial buildings. Rather than limiting the ECM to only some building types, the technology field will be used to restrict the applicability of the ECM to only the energy used by lighting types that could be replaced by LED troffers. ::

   {...
    "bldg_type": "all commercial",
    ...}

ECMs can apply to only new construction, only existing buildings, or all buildings both new and existing. This is specified under the :ref:`json-structure_type` key with the values "new," "existing," or "all," respectively. 

LED troffers can be installed in both new construction and existing buildings, thus the "all" shorthand is used. ::

   {...
    "structure_type": "all",
    ...}

The end use(s) correspond to the major building functions or other energy uses provided by the technology described in the ECM. End uses can be specified as a single string or, if multiple end uses apply, as a list. The acceptable formats for the end use(s) are in the :ref:`ECM JSON schema <json-end_use>` and the acceptable values are listed in the :ref:`ecm-baseline_end-use` ECM reference section. [#]_ If the ECM describes a technology that affects the thermal load of a building (e.g., insulation), the end use should be given as "heating" and "cooling" in a list.

The only applicable end use for LED troffers is lighting. Changing from fluorescent bulbs typically found in troffers to LEDs will reduce the heat output from the fixture, thus reducing the cooling load and increasing the heating load for the building. These changes in heating and cooling energy use that arise from changes to lighting systems in commercial buildings are accounted for automatically in the energy use calculations for the ECM. ::

   {...
    "end_use": "lighting",
    ...}

The fuel type generally corresponds to the energy source used for the technology described by an ECM -- natural gas for a natural gas heat pump and electricity for an air-source heat pump, for example. The fuel type should be consistent with the end use(s) already specified, based on the :ref:`end use reference tables <ecm-baseline_end-use>`. Fuel types are listed in the :ref:`ecm-baseline_fuel-type` ECM reference section, and can be specified as a single entry or a list if multiple fuel types are relevant (as indicated in the :ref:`ECM JSON schema <json-fuel_type>`). If the ECM describes a technology that affects the thermal load of a building (e.g., insulation), the fuel type should be given as "all" because heating and cooling energy from all fuel types could be affected by those types of technologies.

In the case of LED troffers, electricity is the only relevant fuel type. ::

   {...
    "fuel_type": "electricity",
    ...}

The technology field drills down into the specific technologies or device types that apply to the end use(s) for the ECM. In some cases, an ECM might be able to replace the full range of incumbent technologies in its end use categories, while in others, only specific technologies might be subject to replacement. As indicated in the :ref:`ECM JSON schema <json-technology>`, applicable technologies can be given as a single string, a list of technology names, or using :ref:`shorthand values <ecm-features-shorthand>`. If applicable, a technology list can also be specified with a mix of shorthand end use references (e.g., "all lighting") and specific technology names, such as ``["all heating", "F28T8 HE w/ OS", "F28T8 HE w/ SR"]``.

All of the technology names are listed by building sector (residential or commercial) and technology type (supply or demand) in the :ref:`relevant section <ecm-baseline_technology>` of the :ref:`ecm-def-reference`. In general, the residential__ and commercial__ thermal load components are the technology names for demand-side energy use, and are relevant for ECMs that apply to the building envelope or windows. Technology names for supply-side energy use generally correspond to major equipment types used in the AEO_ [#]_ and are relevant for ECMs that are describing those types of equipment within a building. 

For this example, LED troffers are likely to replace linear fluorescent bulbs, the typical bulb type in troffers. There are many lighting types for commercial buildings, but we will include all of the lighting types that are specified as T\_\_F\_\_, which correspond to linear fluorescent bulb types, including those with additional modifying text. ::

   {...
    "technology": ["T5 F28", "T8 F28 High-efficiency/High-Output", "T8 F32 Commodity", "T8 F59 High Efficiency", "T8 F59 Typical Efficiency", "T8 F96 High Output"],
    ...}

.. __: https://github.com/trynthink/scout/blob/master/1999%20Residential%20heating%20and%20cooling%20loads%20component%20analysis.pdf
.. __: https://github.com/trynthink/scout/blob/master/1999%20Commercial%20heating%20and%20cooling%20loads%20component%20analysis.pdf
.. _AEO: https://www.eia.gov/analysis/studies/buildings/equipcosts/pdf/full.pdf


Market entry and exit year
**************************

The market entry year represents the year the technology is or will be available for purchase and installation. Some ECMs might be prospective, representing technologies not currently available. Others might represent technologies currently commercially available. The market entry year should reflect the current status of the technology described in the ECM. Similarly, the market exit year represents the year the technology is expected to be withdrawn from the market. If the technology described by an ECM will have a lower installed cost or improved energy efficiency after its initial market entry, another ECM should be created that reflects the improved version of the product, and the market exit year should not (in general) be used to force an older technology out of the market.

The market entry year and exit year both require source information. As much as is practicable, a :ref:`high quality<ecm-sources>` reference should be used for both values. If no source is available, such as for a technology that is still quite far from commercialization, a brief explanatory note should be provided for the market entry year source, and the :ref:`json-source_data` fields themselves can be given as ``null`` or with empty strings. If it is anticipated that the product will not be withdrawn from the market prior to the end of the model :ref:`time horizon <2013-2050 projection>`, the exit year and source should be given as ``null``.

LED troffers are currently commercially available with a range of efficiency, cost, and lifetime ratings. It is likely that while LED troffers will not, in general, exit the market within the model :ref:`time horizon <2013-2050 projection>`, LED troffers with cost and efficiency similar to this ECM are not likely to remain competitive through 2040. It will, however, be left to the analysis to determine whether more advanced lighting products enter the market and supplant this ECM, rather than specifying a market exit year. ::

   {...
    "market_entry_year": 2015,
    "market_entry_year_source": {
      "notes": "The source suggests that technologies described in the document are available on the market by its release date.",
      "source_data": [{
         "title": "High Efficiency Troffer Performance Specification, Version 5.0",
         "author": "",
         "organization": "U.S. Department of Energy",
         "year": 2015,
         "pages": null,
         "URL": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf"}]},
    "market_exit_year": null,
    "market_exit_year_source": null,
    ...}

.. _efficiency:

Energy efficiency
*****************

The energy efficiency of the ECM must be specified in three parts: the quantitative efficiency (only the value(s)), the units of the efficiency value(s) provided, and source(s) that support the indicated efficiency information. Each of these parameters is specified in a separate field. 

The units specified are expected to be consistent with the units for each end use outlined in the :ref:`ECM Definition Reference <ecm-performance-units>` section.

The source(s) for the efficiency data should be credible sources, such as :ref:`those outlined <ecm-sources>` in the :ref:`analysis-approach` section. The source information should be provided using only the fields shown in the example and should include sufficient information so that the value(s) can be quickly identified from the sources listed. Additional detail regarding the acceptable form for entries in the source are linked to from the :ref:`json-source_data` entry in the ECM JSON schema.

For the example of LED troffers, all lighting data should be provided in the units of lumens per Watt (denoted "lm/W"). LED troffers efficiency information is based on the `High Efficiency Troffer Performance Specification`_. ::

   {...
    "energy_efficiency": 120,
    "energy_efficiency_units": "lm/W",
    "energy_efficiency_source": {
      "notes": "Initial efficiency value taken from source section II.a.2.a. Efficiency value increased slightly based on efficacy values for fixtures categorized as '2x4 Luminaires for Ambient Lighting of Interior Commercial Spaces' in the DesignLights Consortium Qualified Products List (https://www.designlights.org/qpl).",
      "source_data": [{
         "title": "High Efficiency Troffer Performance Specification, Version 5.0",
         "author": "",
         "organization": "U.S. Department of Energy",
         "year": 2015,
         "pages": 5,
         "URL": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf"}]},
    ...}

.. Many additional options exist that enable more complex definitions of energy efficiency, such as incorporating :ref:`probability distributions <ecm-features-distributions>`, providing a :ref:`detailed efficiency breakdown <ecm-features-detailed-input>` by elements of the applicable baseline market, using :ref:`EnergyPlus simulation data <ecm-features-energyplus>`, and using :ref:`relative instead of absolute units <ecm-features-relative-savings>`. Detailed examples for all of the options are in the :ref:`ecm-features` section.

Many additional options exist that enable more complex definitions of energy efficiency, such as incorporating :ref:`probability distributions <ecm-features-distributions>`, providing a :ref:`detailed efficiency breakdown <ecm-features-detailed-input>` by elements of the applicable baseline market, and using :ref:`relative instead of absolute units <ecm-features-relative-savings>`. Detailed examples for all of the options are in the :ref:`ecm-features` section.


.. _first-ecm-installed-cost:

Installed cost
**************

The absolute installed cost must be specified for the ECM, including the cost value, units, and reference source. The cost units should be specified according to :ref:`the relevant section <ecm-installed-cost-units>` of the :ref:`ecm-def-reference`, noting that residential and commercial equipment have different units, and that sensors and controls ECMs also have different units from other equipment types. The source information should be provided using the same keys and structure as the energy efficiency source. For ECMs that describe technologies not yet commercialized, assumptions incorporated into the installed cost estimate should be described in the :ref:`json-notes` section of the source.

If applicable to the ECM, separate cost values can be provided by building type and structure type, as described in the :ref:`ecm-features-detailed-input` section. Probability distributions can also be used instead of point values for the cost, using the format outlined in the :ref:`ecm-features-distributions` section.

For LED troffers, costs are estimated based on an assumption of a single fixture providing 4800 lm, with installation requiring two hours and two people at a fully-burdened cost of $100/person/hr. The assumptions are articulated using the :ref:`json-notes` key under the :ref:`json-installed_cost_source` key.::

   {...
    "installed_cost": 233.33,
    "cost_units": "$/1000 lm",
    "installed_cost_source": {
      "notes": "Assumes single fixture provides 4800 lm; requires 2 hour install with 2 people at a fully-burdened cost of $100/person/hr. Luminaire cost based on a range of retail prices found for luminaires with similar specifications found online in October 2016.",
      "source_data": [{
         "title": "",
         "author": "",
         "organization": "",
         "year": null,
         "pages": null,
         "URL": ""}]},
    ...}


Lifetime
********

The lifetime of the ECM, or the expected amount of time that the ECM technology will last before requiring replacement, is specified using a structure identical to the installed cost. Again, the lifetime value, units, and source information must be specified for the corresponding keys. The product lifetime can also be specified with a :ref:`probability distribution <ecm-features-distributions>` and/or :ref:`different values by building type <ecm-features-detailed-input>`. The units should always be in years, ideally as integer values greater than 0. The source information follows the same format as for the energy efficiency and installed cost. For ECMs that describe technologies not yet commercialized, assumptions in the lifetime estimate should be explained in the :ref:`json-notes` section of the source.

LED troffers have rated lifetimes on the order of 50,000 hours, though the `High Efficiency Troffer Performance Specification`_ requires a minimum lifetime of 68,000 hours. The values for lighting lifetimes should be based on assumptions regarding actual use conditions (i.e., number of hours per day), and the :ref:`json-notes` value in the source specification should include that assumption. The LED troffers in this example are assumed to operate 12 hours per day. ::

   {...
    "product_lifetime": 15,
    "product_lifetime_units": "years",
    "product_lifetime_source": {
      "notes": "Calculated from 68,000 hrs, stated as item II.c.i, assuming 12 hr/day operation.",
      "source_data": [{
         "title": "High Efficiency Troffer Performance Specification, Version 5.0",
         "author": "",
         "organization": "U.S. Department of Energy",
         "year": 2015,
         "pages": 5,
         "URL": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf"}]},
    ...}

.. _High Efficiency Troffer Performance Specification: https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf

.. _first-ecm-other-fields:

Other fields
************

The :ref:`json-measure_type` field indicates whether an ECM directly replaces the service of an existing device or building component or improves the efficiency of an existing technology. Examples include a cold-climate heat pump replacing existing electric heating and cooling systems and a window film that decreases solar heat gain, respectively. Further discussion of how to use the :ref:`json-measure_type` field and illustrative examples are in the :ref:`ecm-features-measure-type` section.

LED troffers would replace existing troffers that use linear fluorescent bulbs, providing an equivalent building service (lighting) using less energy. The LED troffers ECM is thus denoted as "full service." ::

   {...
    "measure_type": "full service",
    ...}

If the ECM is intended to supplant technologies with multiple fuel types, those fuel types are specified in the :ref:`json-fuel_type` value, and the fuel type of the ECM itself is specified in the :ref:`json-fuel_switch_to` field. This field is explained further, with illustrative examples in the :ref:`ecm-features-multiple-fuel-types` section. When not applicable, this field should be given the value ``null``.

All lighting uses only electricity, so this option is not relevant to LED troffers. ::

   {...
    "fuel_switch_to": null,
     ...}

If the ECM applies to only a portion of the energy use in an applicable baseline market, even after specifying the particular end use, fuel type, and technologies that are relevant, a scaling value can be added to the ECM definition to specify what fraction of the applicable baseline market is truly applicable to that ECM. 

When creating a new ECM, it is important to carefully specify the applicable baseline market to avoid the use of the market scaling fraction parameter, if at all possible. If the scaling fraction is not used, the value and the source should be set to ``null``. Details regarding the use of the market scaling fraction can be found in the :ref:`ecm-features-market-scaling-fractions` section.

No market scaling fraction is required for the LED troffers ECM. ::

   {...
    "market_scaling_fractions": null,
    "market_scaling_fractions_source": null,
    ...}

Two keys are provided for ECM authors to provide additional details about the technology specified. The :ref:`json-_description` field should include a one to two sentence description of the ECM, including additional references for further details regarding the technology if it is especially novel or unusual. The :ref:`json-_notes` field can be used for explanatory notes regarding the technologies that are expected to be replaced by the ECM and any notable assumptions made in the specification of the ECM not captured in another field. ::

   {...
    "_description": "LED troffers for commercial modular dropped ceiling grids that are a replacement for the entire troffer luminaire for linear fluorescent bulbs, not a retrofit kit or linear LED bulbs that slot into existing troffers.",
    "_notes": "Energy efficiency is specified for the luminaire, not the base lamp.",
    ...}

Basic contact information regarding the author of a new ECM should be added to the fields under the :ref:`json-_added_by` key. ::

   {...
    "_added_by": {
      "name": "Carmen Sandiego",
      "organization": "Super Appliances, Inc.",
      "email": "carmen.sandiego@superappliances.com",
      "timestamp": "2015-07-14 11:49:57 UTC"},
    ...}

.. Date and time of New Horizons flyby of Pluto

When updating an existing ECM, the identifying information for the contributor should be provided in the :ref:`json-_updated_by` field instead of the "_added_by" field. If the ECM is new, the child keys in the "_updated_by" section should be given ``null`` values. ::

   {...
    "_updated_by": {
      "name": null,
      "organization": null,
      "email": null,
      "timestamp": null},
    ...}

The LED troffers ECM that you've now written can be simulated with Scout by following the steps in subsequent tutorials. Many technologies will have ECM definitions like the one you just created, but some technologies, like sensors and controls and windows and opaque envelope products, will have definitions that are subtly different. Sensors and controls ECMs augment the efficiency of existing equipment in the stock, rather than replacing existing and supplanting new equipment. To get a feel for what these types of add-on technologies look like as an ECM, you can :download:`download <examples/AFDD (Prospective).json>` and review an Automated Fault Detection and Diagnosis (AFDD) ECM. Additional information about sensors and controls ECMs can be found in the :ref:`ecm-features-measure-type` section. Windows and opaque envelope technologies reduce demand for heating and cooling instead of increasing the efficiency of the supply of heating and cooling. An ECM for the ENERGY STAR windows version 6 specification is available to :download:`download <examples/ENERGY STAR Windows v. 6.0.json>` to illustrate demand-reducing ECMs.


.. _ecm-features:

Additional ECM features
~~~~~~~~~~~~~~~~~~~~~~~

There are many ways in which an ECM definition can be augmented, beyond the basic example already presented, to more fully characterize a technology. The subsequent sections explain how to implement the myriad options available to add more detail and complexity to your ECMs. Links to download example ECMs that illustrate the feature described are included in each section.

.. _ecm-features-tsv:

Time sensitive valuation
************************

In certain cases, ECMs might affect baseline energy loads differently depending on the time of day, necessitating time sensitive valuation of efficiency impacts. :numref:`tsv-ecm-diagram` demonstrates four possible types of time sensitive ECM impacts.

.. _tsv-ecm-diagram:
.. figure:: images/TSV_ECMs.*

   The effect of time sensitive ECM features on baseline energy load shapes are represented as a light gray curve in each of the plots. Time sensitive ECM features include (clockwise from top left): conventional efficiency, where an efficiency improvement is constrained to certain hours of the day; peak shaving and valley filling, where peaks in the load shape are reduced and/or troughs in the load shape are filled in; load shaping, where a load shape is uniformly flattened or redistributed to reflect a custom load shape; and load shifting, where loads shed during a certain hour range are redistributed to an earlier time of day or the entire load shape is shifted earlier by a certain number of hours.

Such time sensitive ECM features are specified using the :ref:`json-time_sensitive_valuation` parameter, which adheres to the following general format: ::

   {...
    "time_sensitive_valuation": {
      <time sensitive feature>: {<feature details>}},
    ...}

Each time sensitive ECM feature is further described below with illustrative example ECMs. 

.. _ecm-download-com-peak:

:download:`Example <examples/Commercial AC (Peak Elimination).json>` -- Commercial AC (Peak Elimination) ECM (:ref:`Details <ecm-example-com-peak>`)

The first type of time sensitive ECM feature restricts the impact of a conventional efficiency measure to certain hours of the day using :ref:`json-start` and :ref:`json-stop` parameters. ::

   {...
    "time_sensitive_valuation": {
      "conventional": {"start": 12, "stop": 20}},
    ...}

These settings constrain ECM efficiency impacts indicated by the :ref:`json-energy_efficiency` parameter to a specific time period |---| in this example, 12PM--8PM. Such a capability may be useful, for example, in exploring the total energy use, |CO2| emissions, and operating costs associated with a particular utility definition of the peak load period. This :ref:`json-time_sensitive_valuation` setting works in combination with the energy efficiency specified separately in the ECM definition. In this example, the above :ref:`json-time_sensitive_valuation` settings are combined with a 100% energy use reduction. ::

   {...
    "energy_efficiency": 1,
    "energy_efficiency_units": "relative savings (constant)",
    ...}

This particular combination of :ref:`json-time_sensitive_valuation` and :ref:`json-energy_efficiency` settings yields the total avoided energy, |CO2| emissions, and operating costs resulting from *eliminating* peak period energy use.

.. _ecm-example-com-peak:

A commercial peak elimination ECM is :ref:`available for download <ecm-download-com-peak>`.

.. _ecm-download-com-shave:

:download:`Example <examples/Commercial AC (Peak Shave).json>` -- Commercial AC (Peak Shave) ECM (:ref:`Details <ecm-example-com-shave>`)

The second type of time sensitive ECM feature either sheds a fixed percentage of peak energy load off a baseline load shape or fills in troughs in the baseline load shape; these effects may be restricted to certain hours of the day or applied across the entire day.

Given the following peak shaving settings, which include use of the :ref:`json-peak_fraction` parameter, loads are reduced to *at maximum* 75% of the peak load between 12PM--8PM. ::

   {...
    "time_sensitive_valuation": {
      "shave": {"start": 12, "stop": 20, "peak_fraction": 0.75}},
    ...}

Given the following valley filling settings, loads are increased to *at minimum* 50% of the peak load between 12PM-8PM. ::

   {...
    "time_sensitive_valuation": {
      "fill": {"start": 12, "stop": 20, "peak_fraction": 0.5}},
    ...}

.. _ecm-example-com-shave:

A commercial peak shaving ECM is :ref:`available for download <ecm-download-com-shave>`.

.. _ecm-download-com-shift:

:download:`Example <examples/Commercial AC (Shift).json>` -- Commercial AC (Load Shift) ECM (:ref:`Details <ecm-example-com-shift>`)

The third type of time sensitive ECM feature shifts baseline energy loads from one time of day to another, either by redistributing loads shed during a certain hour range to earlier times of day or by shifting the entire baseline energy load shape earlier by a certain number of hours.

In the first case, :ref:`json-start` and :ref:`json-stop` parameters are used to determine the hour range from which to shift load reductions; an :ref:`json-offset_hrs_earlier` parameter is then used to determine which hour range to redistribute the load reductions to. ::

   {...
    "time_sensitive_valuation": {
      "shift": {"start": 12, "stop": 20, "offset_hrs_earlier": 12}},
    ...} 

These settings take any load reductions between 12PM--8PM |---| determined by the ECM's :ref:`json-energy_efficiency` parameter setting |---| and evenly redistribute the reductions across the hours of 12AM--8AM, or 12 hours earlier in the day.

In the second case, no start and stop times are given for the time sensitive feature. ::

   {...
    "time_sensitive_valuation": {
      "shift": {"start": null, "stop": null, "offset_hrs_earlier": 12}},
    ...}

These settings shift the *entire* baseline load shape earlier by 12 hours.

.. tip::
   In cases where no time constraints are desired on a time sensitive ECM feature, users may exclude the :ref:`json-start` and :ref:`json-stop` parameters entirely (in lieu of setting them to null values).

.. _ecm-example-com-shift:

A commercial load shifting ECM that demonstrates the load shifting settings from the first case above is :ref:`available for download <ecm-download-com-shift>`.

.. _ecm-download-com-flatten:

:download:`Example <examples/Commercial AC (Flatten).json>` -- Commercial AC (Load Flatten) ECM (:ref:`Details <ecm-example-com-shape>`)

.. _ecm-download-com-shape:

:download:`Example <examples/Commercial AC (Shape).json>` -- Commercial AC (Custom Load Shape) ECM (:ref:`Details <ecm-example-com-shape>`)

The final type of time sensitive ECM feature reshapes the baseline energy load by uniformly flattening the load or rescaling it to represent a user-defined custom load shape. 

The :ref:`json-flatten_fraction` parameter is used to flatten a baseline energy load shape. ::

   {...
    "time_sensitive_valuation": {
      "shape": {"start": null, "stop": null, "flatten_fraction": 0.5}},
    ...}

These settings result in all loads above the daily average being reduced by 50% of the difference between the load and the average, and all loads below the daily average being increased by 50% of the difference between the load and the average. In this case, no time constraints have been placed on the flattening operation, though it is possible to do so using the :ref:`json-start` and :ref:`json-stop` parameters. When a time interval is provided, the calculated average and resulting load reshaping are limited to the specified interval.

The :ref:`json-custom-load` parameter is used to set a custom load shape. ::

   {...
    "time_sensitive_valuation": {
      "shape": {
        "custom_load": [0.79, 0.70, 0.61, 0.56, 0.52, 0.52, 0.54, 0.58, 0.63, 0.67, 0.69, 0.71,
                        0.71, 0.71, 0.76, 0.76, 0.80, 0.85, 0.90, 0.95, 0.99, 1, 0.96, 0.88]}},
    ...}

Here, custom load shaping fractions are specified in a list for all 24 hours of the day. Each number in the list represents the hourly load's fraction of maximum daily load. In the above settings, for example, the load for the first hour of the day is 79% of the maximum daily load, which occurs in hour 22.

Alternatively, the :ref:`json-custom-save` parameter can be used to set a custom load savings shape. :: 

   {...
    "time_sensitive_valuation": {
      "shape": {
        "custom_savings": [0.5, 0.5, 0.5, 0.5, 0.5, 0.6, 1, 1.3, 1.4, 1.5, 1.6, 1.8,
        	           1.9, 2, 1, 0.5, 0.75, 0.75, 0.75, 0.75, 0.5, 0.5, 0.5, 0.5]}},
    ...}

As in the :ref:`json-custom-load` case, custom load savings fractions are specified in a list for all 24 hours of the day. In this case, each number in the list represents the fraction of hourly baseline load that an ECM saves. In the above settings, for example, the ECM reduces the load for the first hour of the day by 50%. Note that savings fractions may be specified as greater than 1 to represent the effects of on-site energy generation on a building's overall load profile.

.. _ecm-example-com-shape:

A commercial load flattening ECM is :ref:`available for download <ecm-download-com-flatten>`, as is a :ref:`commercial custom load shaping ECM <ecm-download-com-shape>`.

.. _ecm-download-com-multiple:

:download:`Example <examples/Commercial AC (Multiple TSV).json>` -- Commercial AC (Multiple TSV) ECM (:ref:`Details <ecm-example-com-multiple>`)

Finally, it is possible to define ECMs that combine multiple time sensitive features at once |---| e.g., an ECM that both shifts and shapes load. ::

   {...
    "time_sensitive_valuation": {
      "shift": {"start": 12, "stop": 20, "offset_hrs_earlier": 10},
      "shape": {"start": null, "stop": null, "flatten_fraction": 0.5}},
    ...}

These settings take any load reductions between 12PM-8PM |---| again defined by the ECM's :ref:`json-energy_efficiency` parameter setting |---| and redistribute them evenly across the hours of 12AM-8AM; subsequently, the resulting load shape is flattened to reduce the difference between all hourly loads and the average hourly load by 50%.

.. note::
   When multiple time sensitive features are specified for an ECM, the assumed order of implementation is: 1) conventional efficiency, 2) peak shave or valley fill, 3) load shift, and 4) load reshape.

Source information for time sensitive ECM features is specified using the :ref:`json-time_sensitive_valuation_source` field. In cases where multiple time sensitive features are indicated and the sources differ across each feature, the source information can be provided using the same nested dict structure as the time sensitive features themselves, as shown below.::

  {...
    "time_sensitive_valuation_source": {
      "shift": {
        "notes": {...},
        "source_data": {...}},
      "shape": {
        "notes": {...},
        "source_data": {...}}},
    ...}

.. _ecm-example-com-multiple:

A commercial load shifting and reshaping ECM is :ref:`available for download <ecm-download-com-multiple>`.

.. _ecm-features-shorthand:

Baseline market shorthand values
********************************

.. _ecm-download-shorthand:

:download:`Example <examples/Whole Building Submetering (Prospective).json>` -- Whole Building Sub-metering ECM (:ref:`Details <ecm-example-shorthand>`)

If an ECM applies to multiple building types, end uses, or other applicable baseline market categories [#]_, the specification of the baseline market and, in some cases, other fields, can be greatly simplified by using shorthand strings. When specifying the applicable baseline market, for example, an ECM might represent a technology that can be installed in any residential building, indicated with the "all residential" string for the building type key. ::

   {...
    "bldg_type": "all residential",
    ...}

Similarly, an ECM that applies to any climate zone can use "all" as the value for the climate zone key. ::

   {...
    "climate_zone": "all",
    ...}

These shorthand terms, when they encompass only a subset of the valid entries for a given field (e.g., "all commercial," which does not include any residential building types), can also be mixed in a list with other valid entries for that field. ::

   {...
    "bldg_type": ["all residential", "small office", "lodging"],
    ...}

The :ref:`ECM definition reference <ecm-applicable-baseline-market>` specifies whether these shorthand terms are available for each of the applicable baseline market fields and what shorthand strings are valid for each field.

If these shorthand terms are used to specify the applicable baseline market fields, the energy efficiency, installed cost, and lifetime may be specified with a single value. For example, if an ECM applies to "all residential," "small office," and "lodging" building types, they could all share the same installed cost. ::

   {...
    "bldg_type": ["all residential", "small office", "lodging"],
    ...
    "installed cost": 5825,
    ...}

.. _shorthand-detailed-input-specification:

Alternately, a :ref:`detailed input specification <ecm-features-detailed-input>` for energy efficiency, installed cost, or lifetime can be used. Using the same building types example, if a detailed input specification is used for the installed cost, a cost value must be given for *all* of the specified building types. ::

   {...
    "installed_cost": {
      "all residential": 5530,
      "small office": 6190,
      "lodging": 6015},
    ...}

Again using the same example, separate installed costs can also be specified for each of the residential building types, even if they are indicated as a group in the building type field using the "all residential" shorthand. ::

   {...
    "installed_cost": {
      "single family home": 5775,
      "multi family home": 5693,
      "mobile home": 5288,
      "small office": 6190,
      "lodging": 6015},
    ...}

.. _ecm-example-shorthand:

A whole building sub-metering ECM is :ref:`available for download <ecm-download-shorthand>` that illustrates the use of shorthand terms by employing the "all" shorthand term for most of the applicable baseline market fields (|baseline-market|) and the "all commercial" shorthand term as one of the building types and to define separate installed costs for the various building types that apply to the ECM. If you would like to see additional examples, many of the other examples available to download in this section use shorthand terms for one or more of their applicable baseline market fields.


.. _ecm-features-detailed-input:

Detailed input specification
****************************

.. _ecm-download-detailed-input:

:download:`Example <examples/Thermoelastic HP (Prospective).json>` -- Thermoelastic Heat Pump ECM (:ref:`Details <ecm-example-detailed-input>`)

The energy efficiency, installed cost, and lifetime values in an ECM definition can be specified as a point value or with separate values for one or more of the following applicable baseline market keys: :ref:`json-climate_zone`, :ref:`json-bldg_type`, :ref:`json-end_use` and :ref:`json-structure_type`. As shown in :numref:`table-detailed-input-options`, the allowable baseline market keys are different for the energy efficiency, installed cost, and lifetime values.

.. table:: The baseline market keys that can be used to provide a detailed specification of the energy efficiency, installed cost, or lifetime input fields in an ECM definition depend on which field is being specified.
   :name: table-detailed-input-options

   +----------------------------+-------------------------------+----------------------------+------------------------------+
   | Baseline Market Key        |       Energy Efficiency       |       Installed Cost       |       Product Lifetime       |
   +============================+===============================+============================+==============================+
   | :ref:`json-climate_zone`   |               X               |                            |                              |
   +----------------------------+-------------------------------+----------------------------+------------------------------+
   | :ref:`json-bldg_type`      |               X               |              X             |               X              |
   +----------------------------+-------------------------------+----------------------------+------------------------------+
   | :ref:`json-end_use`        |               X               |                            |                              |
   +----------------------------+-------------------------------+----------------------------+------------------------------+
   | :ref:`json-structure_type` |               X               |              X             |                              |
   +----------------------------+-------------------------------+----------------------------+------------------------------+
   

A detailed input specification for any of the fields should consist of a dict with keys from the desired baseline market field(s) and the appropriate values given for each key. For example, an HVAC-related ECM, such as a central AC unit, will generally have efficiency that varies by :ref:`climate zone <json-climate_zone>`, which can be captured in the energy efficiency input specification. ::

   {...
    "energy_efficiency": {
      "AIA_CZ1": 1.6,
      "AIA_CZ2": 1.54,
      "AIA_CZ3": 1.47,
      "AIA_CZ4": 1.4,
      "AIA_CZ5": 1.28},
    ...}

.. note::
   If a detailed input specification is used, all of the applicable baseline market keys *must* be given and have a corresponding value. For example, an ECM that applies to three building types and has a detailed input specification for installed cost must have a cost value for all three building types. (Exceptions may apply if the partial shortcuts "all residential" and "all commercial" are used -- see the :ref:`baseline market shorthand values <shorthand-detailed-input-specification>` documentation.)

ECMs that describe technologies that perform functions across multiple end uses will necessarily require an energy efficiency definition that is specified by fuel type. Air-source heat pumps, which provide both heating and cooling, are an example of such a technology. ::

   {...
    "energy_efficiency": {
      "heating": 1.2,
      "cooling": 1.4},
    ...}

For an ECM that applies to both new and existing buildings, the installed cost might vary for those :ref:`structure types <json-structure_type>` due to differences in the number of labor hours required to install the technology as a building is being constructed versus an installation that begins with teardown and requires more careful cleanup and management of dust and noise. ::

   {...
    "installed_cost": {
      "new": 26,
      "existing": 29},
    ...}

If a detailed input specification includes two or more baseline market keys, the keys should be placed in a nested dict structure adhering to the following key hierarchy: :ref:`json-climate_zone`, :ref:`json-bldg_type`, :ref:`json-end_use` and :ref:`json-structure_type`. Multi-function heat pumps, which provide heating, cooling, and water heating services, are an example of a case where a detailed energy efficiency specification by climate zone and end use might be appropriate. ::

   {...
    "energy_efficiency": {
      "AIA_CZ1": {
         "heating": 1.05,
         "cooling": 1.3,
         "water heating": 1.25},
      "AIA_CZ2": {
         "heating": 1.15,
         "cooling": 1.26,
         "water heating": 1.31},
      "AIA_CZ3": {
         "heating": 1.3,
         "cooling": 1.21,
         "water heating": 1.4},
      "AIA_CZ4": {
         "heating": 1.4,
         "cooling": 1.16,
         "water heating": 1.57},
      "AIA_CZ5": {
         "heating": 1.4,
         "cooling": 1.07,
         "water heating": 1.7}},
    ...}

If an input has a detailed specification, the units need not be given in an identical dict structure. The units can be specified using the simplest required structure, including as a single string, while matching the required units specified for :ref:`energy efficiency <ecm-energy-efficiency-units>` and :ref:`installed cost <ecm-installed-cost-units>`. Product lifetime units can always be given as a single string since all lifetime values should be in years. For the first example, energy efficiency units will not vary across climate zones. ::

   {...
    "energy_efficiency_units": "COP",
    ...}

Similarly, in the third example, installed cost units for a given technology will not vary by building structure type. ::

   {...
    "installed_cost_units": "$/ft^2 wall",
    ...}

In the second example, while the energy efficiency units are generally different for each end use, the :ref:`energy efficiency units reference <ecm-energy-efficiency-units>` shows that heating (from a heat pump) and cooling have the same units, thus the units do not need to be specified by end use for this particular case. ::

   {...
    "energy_efficiency_units": "COP",
    ...}

In the fourth example, where the energy efficiency is specified by climate zone and end use, the units will only vary by end use, thus the units dict does not need to be identical in structure to the energy efficiency dict, and can be specified using only the end uses. ::

   {...
    "energy_efficiency_units": {
      "heating": "COP",
      "cooling": "COP",
      "water heating": "EF"},
    ...}

.. While all of the examples shown use absolute units, :ref:`relative savings values <ecm-features-relative-savings>`, :ref:`EnergyPlus energy efficiency data <ecm-features-energyplus>` (for commercial buildings), and :ref:`probability distributions <ecm-features-distributions>` can also be used with detailed input specifications. If an ECM can be described using one or more :ref:`shorthand terms <ecm-features-shorthand>`, these strings can be used as keys for a detailed input specification; this ability is particularly helpful when using the "all residential" and/or "all commercial" building type shorthand strings.

While all of the examples shown use absolute units, :ref:`relative savings values <ecm-features-relative-savings>` and :ref:`probability distributions <ecm-features-distributions>` can also be used with detailed input specifications. If an ECM can be described using one or more :ref:`shorthand terms <ecm-features-shorthand>`, these strings can be used as keys for a detailed input specification; this ability is particularly helpful when using the "all residential" and/or "all commercial" building type shorthand strings.

When a detailed input specification is given, the corresponding source information need not be specified in the same type of nested dict format, particularly if all of the data are drawn from a single source. Even if multiple sources are required, all of the sources may be given with separate dicts in a single list under the :ref:`json-source_data` key, along with an explanation of what data are drawn from each source given in the :ref:`json-notes` field.

Finally, any ECM that includes one or more detailed input specifications should have some discussion of the detailed specification and any underlying assumptions included in either the :ref:`json-_notes` field in the JSON or the :ref:`json-notes` field for the source information for each detailed input specification. As the complexity of the specification increases, the detail of the explanation should similarly increase.

.. _ecm-example-detailed-input:

A thermoelastic heat pump ECM is :ref:`available for download <ecm-download-detailed-input>` to illustrate the use of the detailed input specification approach for the installed cost data and units, as well as the page information for the installed cost source.


.. _ecm-features-relative-savings:

Relative energy efficiency units
********************************

.. _ecm-download-relative-savings:

:download:`Example <examples/Occupant-Centered Controls (Prospective).json>` -- Occupant-centered Controls ECM (:ref:`Details <ecm-example-relative-savings>`)

In addition to the absolute units used in the :ref:`initial example <example-ecm-1>`, any ECM can have energy efficiency specified with the units "relative savings (constant)" or "relative savings (dynamic)". In either case, the energy efficiency value should be given as a decimal value between 0 and 1, corresponding to the percentage improvement from the baseline (i.e., the existing stock) -- a value of 0.2 corresponds to a 20% energy savings relative to the baseline.

.. note::
   Absolute efficiency units are preferred (except for sensors and controls ECMs). Absolute units are more commonly reported in test results and product specifications. In addition, using relative savings leaves some uncertainty regarding whether there are discrepancies between the baseline used to calculate the savings percentage and the baseline in Scout.

.. note
   Absolute efficiency units are preferred (except for sensors and controls ECMs and when :ref:`using EnergyPlus data <ecm-features-energyplus>`). Absolute units are more commonly reported in test results and product specifications. In addition, using relative savings leaves some uncertainty regarding whether there are discrepancies between the baseline used to calculate the savings percentage and the baseline in Scout.

When the units are "relative savings (constant)," the value that is given is assumed to be the same in every year, independent of improvement in the efficiency of technologies comprising the baseline. That is, an "energy_efficiency" value of 0.3 with the units "relative savings (constant)" means that the ECM will achieve a 30% reduction in energy use compared to the baseline in the current year and a 30% reduction in energy use compared to the baseline in all future years.

If "relative savings (dynamic)" is used, the percentage savings are reduced in future years to account for efficiency improvements in the baseline. These reductions are calculated relative to an anchor year, which is the year for which the specified savings percentage was calculated. The anchor year is specified as an integer along with the units string in a list. (In the example shown, 2014 is the anchor year.) ::

   {...
    "energy_efficiency_units": ["relative savings (dynamic)", 2014],
    ...}

Relative units can be combined with :ref:`detailed input specifications <ecm-features-detailed-input>`. ::

   {...
    "energy_efficiency": {
      "AIA_CZ1": 0.13,
      "AIA_CZ2": 0.127,
      "AIA_CZ3": 0.123,
      "AIA_CZ4": 0.118,
      "AIA_CZ5": 0.11},
    "energy_efficiency_units": "relative savings (constant)",
    ...}

If appropriate for a given ECM, absolute and relative units can also be mixed in a :ref:`detailed input specification <ecm-features-detailed-input>`. ::

   {...
    "energy_efficiency": {
      "heating": 1.2,
      "cooling": 0.25},
    "energy_efficiency_units": {
      "heating": "COP",
      "cooling": ["relative savings (dynamic)", 2016]},
    ...}

.. _ecm-example-relative-savings:

An occupant-centered controls ECM :ref:`available for download <ecm-download-relative-savings>`, like all controls ECMs, uses relative savings units. It also illustrates several other features discussed in this section, including :ref:`shorthand terms <ecm-features-shorthand>`, :ref:`detailed input specification <ecm-features-detailed-input>`, and the :ref:`add-on measure type <ecm-features-measure-type>`.


.. ecm-features-energyplus: (CONVERT BACK TO SECTION REFERENCE TAG)

.. EnergyPlus efficiency data
  **************************

.. For commercial building types, energy efficiency values can be specified using data from an :ref:`EnergyPlus simulation <analysis-step-2-energyplus>`. EnergyPlus simulation data include results for all of the energy uses that are affected by the ECM, including end uses that are not in the applicable baseline market for the ECM. These effects on other end uses are automatically incorporated into the final results for the ECM. EnergyPlus simulation data cannot be combined with :ref:`probability distributions <ecm-features-distributions>` on energy efficiency.

.. Results from EnergyPlus that can be used for energy efficiency inputs in ECMs are stored in CSV files. Each EnergyPlus CSV file is specific to a single building type and can include energy efficiency data for many simulated ECMs. These files should be placed in the \html-filepath| ./ecm_definitions/energyplus_data |html-fp-end| directory. To import energy efficiency data from these files, the user sets the "energy_efficiency" attribute for an ECM to a dict in a specific form: ``"energy_efficiency": {"EnergyPlus file": "ECM_name"}``. Here, "ECM_name" will determine which rows will be read in the EnergyPlus files. The "ECM_name" string should match exactly with the text in the "measure" column in the EnergyPlus CSV files corresponding to the relevant data. Only the EnergyPlus file(s) that correspond to an ECM's building type(s) will be read. When EnergyPlus data are being used, ECM energy efficiency units should always be "relative savings (constant)." 

.. The source(s) for the energy efficiency data that were used as inputs to the EnergyPlus simulations should be indicated in the :ref:`json-energy_efficiency_source` field. The data should be drawn from credible sources, such as :ref:`those outlined <ecm-sources>` in the :ref:`analysis-approach` section. Information about the source(s) should be included in the ECM definition in the same format as when EnergyPlus data are not used.

.. An LED troffers ECM is used to illustrate the format for specifying EnergyPlus simulation data for the energy efficiency. LED troffers are an ideal technology to simulate using EnergyPlus, as the significant reduction in waste heat generated by LED lamps compared to fluorescent and incandescent lamps can have an effect on the HVAC energy use in a building, an effect captured by the EnergyPlus simulation. ::
   {...
    "energy_efficiency": {"EnergyPlus file": "LED_troffers"},
    "energy_efficiency_units": "relative savings (constant)",
    "energy_efficiency_source": {
      "notes": "Initial efficiency value taken from source section II.a.2.a. Efficiency value increased slightly based on efficacy values for fixtures categorized as "2x4 Luminaires for Ambient Lighting of Interior Commercial Spaces" in the DesignLights Consortium Qualified Products List (https://www.designlights.org/qpl).",
      "source_data": [{
         "title": "High Efficiency Troffer Performance Specification, Version 5.0",
         "author": "",
         "organization": "U.S. Department of Energy",
         "year": 2015,
         "pages": 5,
         "URL": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf"}]},
    ...}

.. Window and opaque envelope (i.e., insulation and air sealing) ECMs are also ideal for EnergyPlus simulation, as they similarly will have an effect on HVAC operation by reducing the heading and cooling load in a building and the potential energy savings are affected by whether or not equipment is resized to correspond to the reduced loads.

.. In both of these cases, solid state lighting and window and envelope technologies, without EnergyPlus simulation data Scout will automatically account for the energy use effects from changes in heating and cooling loads. Using results from EnergyPlus can only improve the accuracy of this accounting.

.. In some cases, an ECM could apply to both residential and commercial buildings. Since EnergyPlus data can only be used to specify energy efficiency for commercial buildings, the energy efficiency values can be specified separately for residential and commercial buildings using the :ref:`detailed input specification <ecm-features-detailed-input>` approach. For example, a thermoelastic heat pump might apply to all building types, with some differences in efficiency. EnergyPlus simulation data can be used to specify the efficiency for commercial buildings, while residential unit efficiency can be specified with absolute or relative values or a probability distribution. For the purposes of this example, energy efficiency is assumed to be uniform across residential building types and the EnergyPlus simulation results address commercial buildings, thus the efficiency can be specified under the :ref:`simplified building type keys <ecm-features-shorthand>` "all residential" and "all commercial." Because heat pumps provide both heating and cooling service but generally with different efficiencies, separate values are given for the heating and cooling end use for residential buildings. ::
   {...
    "energy_efficiency": {
      "all residential": {
         "heating": 6,
         "cooling": 5.3},
      "all commercial": {"EnergyPlus file": "thermoelastic_heat_pumps"}},
    "energy_efficiency_units": {
      "all residential": "COP",
      "all commercial": "relative savings (constant)"},
    "energy_efficiency_source": {
      "notes": "Estimate for heating COP from Takeuchi. Estimate for cooling COP reduced relative to heating with the unproven assumption that more waste thermal energy will need to be rejected in cooling mode operation (this assumption was made primarily for the purpose of illustrating an ECM definition with mixed EnergyPlus efficiency data).",
      "source_data":[{
         "title": "Energy Savings Potential and RD&D Opportunities for Non-Vapor Compression HVAC Technologies",
         "author": "Navigant Consulting",
         "organization": "U.S. Department of Energy",
         "year": 2014,
         "pages": 107,
         "URL": "http://energy.gov/sites/prod/files/2014/03/f12/Non-Vapor%20Compression%20HVAC%20Report.pdf"}]},
    ...}

.. <<< DOWNLOADABLE EXAMPLE >>>


.. _ecm-features-market-scaling-fractions:

Market scaling fractions
************************

.. _ecm-download-market-scaling-fractions:

:download:`Example <examples/AFDD (Prospective).json>` -- Automated Fault Detection and Diagnosis ECM (:ref:`Details <ecm-example-market-scaling-fractions>`)

If an ECM applies to only a portion of the energy use in an applicable baseline market, even after specifying the particular building type, end use, fuel type, and technologies that are relevant, the market scaling fraction can be used to specify the fraction of the applicable baseline market that is truly applicable to that ECM. The market scaling fraction thus reduces the size of all or a portion of the applicable baseline market beyond what is achievable using only the baseline market fields. All scaling fraction values should be between greater than 0 and less than 1, where a value of 0.4, for example, indicates that 40% of the baseline market selected applies to that ECM.

.. note::
   When creating a new ECM, it is important to carefully specify the applicable baseline market to avoid the use of the market scaling fraction parameter, if at all possible.

Since the scaling fraction is not derived from the EIA data used to provide a common baseline across all ECMs in Scout, source information must be provided, and it is especially important that the source information be correct and complete. The market scaling fraction source information should be supplied as a dict corresponding to a single source. If multiple values derived from multiple sources are reported, source information can be provided using the same nested dict structure as the scaling fractions themselves. The source field for the market scaling fraction has keys similar to those under the "source_data" key associated with other ECM data, but with an additional :ref:`json-fraction_derivation` key. The fraction derivation is a string that should include an explanation of how the scaling value(s) are calculated from the source(s) given.

When :ref:`preparing the ECM for analysis <tuts-2>`, if a scaling fraction is specified, the source fields are automatically reviewed to ensure that either a) a "title," "author," "organization," and "year" are specified or b) a URL from an acceptable source [#]_ is provided. While these are the minimum requirements, the source information fields should be filled out as completely as possible. Additionally, the "fraction_derivation" field is checked for the presence of some explanatory text. If any of these required fields are missing, the ECM will not be included in the :ref:`prepared ECMs <tuts-2>`. 

As an example, for a multi-function fuel-fired heat pump ECM for commercial building applications, if the system is to provide space heating and cooling and water heating services, it is most readily installed in a building that already has some non-electric energy supply. If it is assumed that any building with a non-electric heating system would be a viable installation target for this technology, market scaling fractions can be applied to restrict the baseline market to correspond with that assumption. ::

   {...
    "market_scaling_fractions": {
      "cooling": 0.53,
      "water heating": 0.53},
    "market_scaling_fractions_source": {
      "title": "2012 Commercial Buildings Energy Consumption Survey (CBECS) Public Use Microdata",
      "author": "U.S. Energy Information Administration (EIA)",
      "organization": "",
      "year": "2016",
      "URL": "http://www.eia.gov/consumption/commercial/data/2012/index.php?view=microdata",
      "fraction_derivation": "Assuming that only buildings with natural gas or propane heating can be retrofitted with a multi-function fuel-fired heat pump, 53.1% of commercial building floor space in CBECS is from buildings with natural gas or propane primary heating systems."},
    ...}

As shown in the example, if the ECM applies to multiple building types, climate zones, or technologies, for example, different scaling fraction values can be supplied for some or all of the baseline market. The method for specifying multiple scaling fraction values is similar to that outlined in the :ref:`ecm-features-detailed-input` sub-section. This detailed breakdown of the market scaling fraction can only include keys that are included in the applicable baseline market. For example, if the applicable baseline market includes only residential buildings, no commercial building types should appear in the market scaling fraction breakdown. If all residential buildings are in the applicable baseline market, however, the market scaling fractions can be separately specified for each residential building type.

.. _ecm-example-market-scaling-fractions:

The automated fault detection and diagnosis (AFDD) ECM :ref:`available for download <ecm-download-market-scaling-fractions>` illustrates the use of the market scaling fraction to limit the applicability of the ECM to only buildings with building automation systems (BAS), since that is a prerequisite for the implementation of the AFDD technology described in the ECM.


.. _ecm-features-measure-type:

Add-on type ECMs
****************

.. _ecm-download-measure-type:

:download:`Example <examples/Plug-and-Play Sensors (Prospective).json>` -- Plug-and-Play Sensors ECM (:ref:`Details <ecm-example-measure-type>`)

Technologies that affect the operation of or augment the efficiency of the existing components of a building must be defined differently in an ECM than technologies that replace a building component. Examples include sensors and control systems, window films, and daylighting systems. These technologies improve or affect the operation of another building system -- HVAC or other building equipment, windows, and lighting, respectively -- but do not replace those building systems.

For these technologies, several of the fields of the ECM must be configured slightly differently. First, the applicable baseline market should be set for the end uses and technologies that are affected by the technology, not those that describe the technology. For example, an automated fault detection and diagnosis (AFDD) system that affects heating and cooling systems should have the end uses "heating" and "cooling," not some type of electronics or miscellaneous electric load (MEL) end use. Second, the energy efficiency values should have :ref:`relative savings <ecm-features-relative-savings>`  units and the installed cost units should match those specified in the :ref:`ECM Definition Reference <ecm-installed-cost-units>`, noting that they are different for sensors and controls ECMs. Finally, the :ref:`json-measure_type` field should have the value ``"add-on"`` instead of ``"full service"``.

.. _ecm-example-measure-type:

A plug-and-play sensors ECM is :ref:`available to download <ecm-download-measure-type>` to illustrate the use of the "add-on" ECM type.

.. <<< DOWNLOADABLE EXAMPLE >>> ADD A DAYLIGHTING ECM? (Daylighting needs market scaling fraction to reduce to lighting in the perimeter zone of buildings?)


.. _ecm-features-multiple-fuel-types:

Multiple fuel types
*******************

.. _ecm-download-multiple-fuel-types:

:download:`Example <examples/Residential Thermoelectric HPWH (Prospective).json>` -- Thermoelectric Heat Pump Water Heater (:ref:`Details <ecm-example-multiple-fuel-types>`)

Some technologies, especially those that serve multiple end uses, might yield much greater energy savings if they are permitted to supplant technologies with different fuel types. Heat pumps, for example, can provide heating and cooling using a single fuel type (typically electricity), but could replace an HVAC system that uses different fuels for heating and cooling. The :ref:`json-fuel_switch_to` field, used in conjunction with the :ref:`json-fuel_type` field in the baseline market enables ECMs that serve multiple end uses and could replace technologies with various fuel types.

To configure these ECMs, the :ref:`json-fuel_type` field should be populated with a list of the fuel types that, for the applicable end uses, are able to be supplanted by the technology described by the ECM. The :ref:`json-fuel_switch_to` field should be set to the string for the fuel type of the technology itself. For example, an ECM that describes a natural gas-fired heat pump might be able to replace technologies that use electricity, natural gas, or distillate fuels. ::

   {...
    "fuel_type": ["electricity", "natural gas", "distillate"],
    ...
    "fuel_switch_to": "natural gas",
    ...}

If all of the fuel types apply, the :ref:`json-fuel_type` field can be specified using the ``"all"`` :ref:`shorthand value <ecm-features-shorthand>`.

.. _ecm-example-multiple-fuel-types:

A residential thermoelectric heat pump water heater is :ref:`available to download <ecm-download-multiple-fuel-types>` to illustrate the setup of the :ref:`json-fuel_type` and :ref:`json-fuel_switch_to` fields to denote, for this particular example, an electric water heater that can replace water heaters of all fuel types.

.. _ecm-features-retro-rate:

ECM-specific retrofit rate
**************************

.. _ecm-download-retro-rate:

:download:`Example <examples/led_troffers_high_retrofit.json>` -- LED Troffers (High Retrofit Rate) (:ref:`Details <ecm-example-retro-rate>`)

Certain ECMs may be targeted towards accelerating typical equipment retrofit rates - e.g., a persistent information campaign that improves consumer awareness of available incentives for replacing older appliances with ENERGY STAR alternatives. Alternatively, a user may simply wish to explore the sensitivity of ECM outcomes to variations in Scout's default equipment retrofit rate. [#]_

To configure such ECMs, the optional :ref:`json-retro_rate` field should be populated with a point value between 0 and 1 that represents the assumed retrofit rate for the ECM. For example, if an ECM is assumed to increase the rate of existing technology stock retrofits to 10% of the existing stock, this effect would be represented as follows. ::

   {...
    "retro_rate": 0.1,
    ...}

Alternatively, the user may place a probability distribution on this rate - see :ref:`ecm-features-distributions` for more details.

Supporting source information for the ECM-specific retrofit rate should be included in the ECM definition using the :ref:`json-retro_rate_source` field.

.. _ecm-example-retro-rate:

A second version of the :ref:`LED troffer example <example-ecm-1>` that assumes a higher retrofit rate (10%) is :ref:`available to download <ecm-download-retro-rate>`.

.. _ecm-features-distributions:

Probability distributions
*************************

.. _ecm-download-distributions:

:download:`Example <examples/ENERGY STAR LED Bulbs v. 1.2 c. 2012.json>` -- LED Bulbs ECM (:ref:`Details <ecm-example-distributions>`)

Probability distributions can be added to the installed cost, energy efficiency, and lifetime specified for ECMs to represent uncertainty or known, quantified variability in one or more of those values. In a single ECM, a probability distribution can be applied to any one or more of these parameters. Probability distributions cannot be specified for any other parameters in an ECM, such as the market entry or exit years, market scaling fractions, or to either the energy savings increase or cost reduction parameters in :ref:`package ECMs <package-ecms>`. 

Where permitted, probability distributions are specified using a list. The first entry in the list identifies the desired distribution. Subsequent entries in the list correspond to the required and optional parameters that define that distribution type, according to the `numpy.random module documentation`_, excluding the optional "size" parameter. [#]_ The |supported-distributions| distributions are currently supported. (Note that the normal and log-normal distributions' scale parameter is standard deviation, not variance.)

.. _numpy.random module documentation: https://docs.scipy.org/doc/numpy/reference/routines.random.html

For a given ECM, if the installed cost is known to vary uniformly between 1585 and 2230 $/unit, that range can be specified with a probability distribution. ::

   {...
    "installed_cost": ["uniform", 1585, 2230],
    ...}

Probability distributions can be specified in any location in the energy efficiency, installed cost, or product lifetime specification where a point value would otherwise be used. Distributions do not have to be provided for every value in a detailed specification if it is not relevant or there are insufficient supporting data. Different distributions can be used for each value if so desired. ::

   {...
    "energy_efficiency": {
      "heating": ["normal", 2.3, 0.4],
      "cooling": ["lognormal", 0.9, 0.2],
      "water heating": 1.15},
    ...}

.. _ecm-example-distributions:

An ENERGY STAR LED bulbs ECM is :ref:`available for download <ecm-download-distributions>` to illustrate the use of probability distributions, in that case, on installed cost and product lifetime.


.. _editing-ecms:

Editing existing ECMs
~~~~~~~~~~~~~~~~~~~~~

All of the ECM definitions are stored in the |html-filepath| ./ecm_definitions |html-fp-end| folder. To edit any of the existing ECMs, open that folder and then open the JSON file for the ECM of interest. Make any desired changes, save, and close the edited file. Like new ECMs, all edited ECMs must be prepared following the steps in :ref:`Tutorial 2 <tuts-2>`.

Making changes to the existing ECMs will necessarily overwrite previous versions of those ECMs. If both the original and revised version of an ECM are desired for subsequent analysis, make a copy of the original JSON file (copy and paste the file in the same directory) and rename the copied JSON file with an informative differentiating name. When revising the copied JSON file with the new desired parameters, take care to ensure that the ECM name is updated as well. 

.. tip::
   No two ECMs can share the same file name *or* name given in the JSON.


.. _package-ecms:

Creating and editing package ECMs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Package ECMs are not actually unique ECMs, rather, they are combinations of existing (single technology) ECMs specified by the user. Existing ECMs can be included in multiple different packages; there is no limit to the number of packages to which a single ECM may be added. There is also no limit on the number of ECMs included in a package.

A package ECM might make sense, for example, in a case where a particular grouping of ECMs could reduce installation labor requirements, or where a combination of ECMs would yield better overall efficiency than if the ECMs were implemented separately. More specifically, a package ECM could be created from an air barrier ECM and an insulation ECM to represent performing an air barrier *and* insulation retrofit at `tenant fit-out`_ in a commercial building, which could reduce the labor cost and thus the combined total installed cost by installing both systems at the same time. If one or more building type-appropriate HVAC equipment ECMs are added to the air barrier and insulation package ECM, downsizing of the HVAC equipment could further reduce the combined total installed cost. The definition for each package includes fields to specify any improvements in cost and/or efficiency, if they apply. (Package ECMs could also include reductions in efficiency and/or increases in installed cost, but it is expected that those packages would not be of interest.)

.. _tenant fit-out: https://www.designingbuildings.co.uk/wiki/Fit_out_of_buildings

Package ECMs are specified in the |html-filepath| package_ecms.json |html-fp-end| file, located in the |html-filepath| ./ecm_definitions |html-fp-end| folder. A version of the |html-filepath| package_ecms.json |html-fp-end| file with a single blank ECM package definition is available for :download:`download <examples/blank_package_ecms.json>`. 

In the package ECMs JSON definition file, each ECM package is specified in a separate dict with three keys: "name," "contributing_ECMs," and "benefits." The package "name" should be a unique name (from other packages and other individual ECMs). The "contributing_ECMs" should be a list of the ECM names to include in the package, separated by commas. The individual ECM names should match exactly with the "name" field in each of the ECM's JSON definition files. The "benefits" are specified in a dict with three keys, "energy savings increase," "cost reduction," and "source." The "energy savings increase" and "cost reduction" values should be fractions between 0 and 1 (in general) representing the percentage savings or cost changes. The energy savings increase can be assigned a value greater than 1, indicating an increase in energy savings of greater than 100%, but robust justification of such a significant improvement should be provided in the source information. If no benefits are relevant for one or both keys, the values can be given as ``null`` or ``0``. The source information for the efficiency or cost improvements are provided in a nested dict structure under the "source" key. The source information should have the same structure as in individual ECM definitions. This structure for a single package ECM that incorporates three ECMs and yields a cost reduction of 15% over the total for those three ECMs is then: ::

   {"name": "First package name", 
    "contributing_ECMs": ["ECM 1 name", "ECM 2 name", "ECM 3 name"],
    "benefits": {"energy savings increase": 0, "cost reduction": 0.15, "source": {
      "notes": "Information about how the indicated benefits value(s) were derived.",
      "source_data": [{
         "title": "The Title",
         "author": "Source Author",
         "organization": "Organization Name",
         "year": "2016",
         "pages": "15-17"}]
    }}}

All of the intended packages should be specified in the |html-filepath| package_ecms.json |html-fp-end| file. For example, the contents of the file should take the following form if there are three desired packages, with three, two, and four ECMs, respectively. ::

   [{"name": "First package name", 
     "contributing_ECMs": ["ECM 1 name", "ECM 2 name", "ECM 3 name"],
     "benefits": {"energy savings increase": 0, "cost reduction": 0.15, "source": {
        "notes": "Explanatory text related to source data and/or values given.",
        "source_data": [{
           "title": "Reference Title",
           "author": "Author Name(s)",
           "organization": "Organization Name",
           "year": "2016",
           "pages": null,
           "URL": "http://buildings.energy.gov/"}]}}},
    {"name": "Second package name", 
     "contributing_ECMs": ["ECM 4 name", "ECM 1 name"],
     "benefits": {"energy savings increase": 0.03, "cost reduction": 0.18, "source": {
        "notes": "Explanatory text regarding both energy savings and cost reduction values given.",
        "source_data": [{
           "title": "Reference Title",
           "author": "Author Name(s)",
           "organization": "Organization Name",
           "year": "2016",
           "pages": "238-239",
           "URL": "http://buildings.energy.gov/"}]}}},
    {"name": "Third package name", 
     "contributing_ECMs": ["ECM 5 name", "ECM 3 name", "ECM 6 name", "ECM 2 name"],
     "benefits": {"energy savings increase": 0.2, "cost reduction": 0, "source": {
        "notes": "Explanatory text related to source data and/or values given.",
        "source_data": [{
           "title": "Reference Title",
           "author": "Author Name(s)",
           "organization": "Organization Name",
           "year": "2016",
           "pages": "82",
           "URL": "http://buildings.energy.gov/"}]}}}]


.. _tuts-2:

Tutorial 2: Preparing ECMs for analysis
---------------------------------------

.. ADD LINKS TO INDICATED JSON INPUT FILES

The Scout analysis is divided into two steps, each with corresponding Python modules. In the first of these steps, discussed in this tutorial, the ECMs are pre-processed by retrieving the applicable baseline energy, |CO2|, and cost data from the input files (located in the |html-filepath| ./supporting_data/stock_energy_tech_data |html-fp-end| directory) and calculating the uncompeted efficient energy, |CO2|, and cost values. This pre-processing step ensures that the computationally intensive process of parsing the input files to retrieve and calculate the relevant data is only performed once for each new or edited ECM.

Each new ECM that is written following the formatting and structure guidelines covered in :ref:`Tutorial 1 <tuts-1>` should be saved in a separate JSON file with a brief but descriptive file name and placed in the |html-filepath| ./ecm_definitions |html-fp-end| directory. If any changes to the package ECMs are desired, incorporating either or both new and existing ECMs, follow the instructions in the :ref:`package ECMs <package-ecms>` section to specify these packages. The pre-processing script can be run once these updates are complete.

To run the pre-processing script |html-filepath| ecm_prep.py\ |html-fp-end|, open a Terminal window (Mac) or command prompt (Windows), navigate to the Scout project directory (shown with the example location |html-filepath| ./Documents/projects/scout-run_scheme\ |html-fp-end|), and run the script.

**Windows** ::

   cd Documents\projects\scout-run_scheme
   py -3 ecm_prep.py

**Mac** ::

   cd Documents/projects/scout-run_scheme
   python3 ecm_prep.py

.. tip::
   By default, ECMs are processed and yield results measured in primary, or source, energy, and the site-source conversion is calculated using the fossil fuel equivalence method. ECM processing can be switched to a site energy basis with the optional flag ``--site_energy`` and can be switched to the captured energy method for converting from site to source energy with the flag ``--captured_energy``. For example, ``python3 ecm_prep.py --captured-energy``. Further details on the difference between the fossil fuel equivalence and captured energy methods for calculating site-source conversion factors can be found in the DOE report `Accounting Methodology for Source Energy of Non-Combustible Renewable Electricity Generation`_.

.. _Accounting Methodology for Source Energy of Non-Combustible Renewable Electricity Generation: https://www.energy.gov/sites/prod/files/2016/10/f33/Source%20Energy%20Report%20-%20Final%20-%2010.21.16.pdf

.. tip::
   Using the optional flag ``--verbose`` (i.e., ``python3 ecm_prep.py --verbose``) will print all warning messages triggered during ECM preparation to the console.

As each ECM is processed by |html-filepath| ecm_prep.py\ |html-fp-end|, the text "Updating ECM" and the ECM name are printed to the command window, followed by text indicating whether the ECM has been updated successfully. There may be some additional text printed to indicate whether the installed cost units in the ECM definition were converted to match the desired cost units for the analysis. If any exceptions (errors) occur, the module will stop running and the exception will be printed to the command window with some additional information to indicate where the exception occurred within |html-filepath| ecm_prep.py\ |html-fp-end|. The error message printed should provide some indication of where the error occurred and in what ECM. This information can be used to narrow the troubleshooting effort.

If |html-filepath| ecm_prep.py |html-fp-end| runs successfully, a message with the total runtime will be printed to the console window. The names of the ECMs updated will be added to |html-filepath| run_setup.json\ |html-fp-end|, a file that indicates which ECMs should be included in :ref:`the analysis <tuts-analysis>`. The total baseline and efficient energy, |CO2|, and cost data for those ECMs that were just added or revised are added to the |html-filepath| ./supporting_data/ecm_competition_data |html-fp-end| folder, where there appear separate compressed files for each ECM. High-level summary data for all prepared ECMs are added to the |html-filepath| ecm_prep.json |html-fp-end| file in the |html-filepath| ./supporting_data |html-fp-end| folder. These files are then used by the ECM competition routine, outlined in :ref:`Tutorial 4 <tuts-analysis>`.

If exceptions are generated, the text that appears in the command window should indicate the general location or nature of the error. Common causes of errors include extraneous commas at the end of lists, typos in or completely missing keys within an ECM definition, invalid values (for valid keys) in the specification of the applicable baseline market, and units for the installed cost or energy efficiency that do not match the baseline cost and efficiency data in the ECM.


.. _tuts-ecm-list-setup:

Tutorial 3: Modifying the active ECMs list
------------------------------------------

Prior to running an analysis, the list of ECMs that will be included in that analysis can be revised to suit your interests. For example, if your primary interest is in ECMs that are applicable to commercial buildings, you could choose to include only those ECMs in your analysis. 

The "active" (i.e., included in the analysis) and "inactive" (i.e., excluded from the analysis) ECMs are specified in the |html-filepath| run_setup.json |html-fp-end| file. There are two ways to modify the lists of ECMs: by :ref:`manually editing them <ecm-list-setup-manual>` or :ref:`using the automatic configuration module <ecm-list-setup-automatic>`.

If you would like to run your analysis with all of the ECMs and have not previously edited the lists of active and inactive ECMs, you can skip these steps and go straight to :ref:`Tutorial 4 <tuts-analysis>`, as all ECMs are included by default.

.. tip::
   As new ECMs are added and pre-processed (by running |html-filepath| ecm_prep.py\ |html-fp-end|), their names are added to the "active" list. Any ECMs that were edited after being moved to the inactive list will be automatically moved back to the active list by |html-filepath| ecm_prep.py\ |html-fp-end|. 


.. _ecm-list-setup-automatic:

Automatic configuration
~~~~~~~~~~~~~~~~~~~~~~~

The automatic configuration module |html-filepath| run_setup.py |html-fp-end| can perform a limited set of adjustments to the active and inactive ECM lists in |html-filepath| run_setup.json\ |html-fp-end|.

1. Move ECMs from the active to the inactive list, and vice versa, based on searching the ECM names for matches with user-provided keywords
2. Move ECMs from the active to the inactive list if they do not apply to the climate zone(s), building type, and/or structure type of interest

For each of the changes supported by the module, messages will be printed to the command window that will explain what information should be input by the user. When entering multiple values, all entries should be separated by commas. Any question can be skipped to ignore the filtering option by pressing the "enter" or "return" key.

For the first set of changes, moving ECMs by searching their names for matches with user-provided keywords, the user will be prompted to enter their desired keywords for each move separately, first for moving ECMs from the active to the inactive list, and then for the opposite move. Keyword matching is not case-sensitive and multiple keywords should be separated by commas. Potential inputs from the user might be, for example: ::

   ENERGY STAR, prospective, 20%

or ::

   iecc

The user may invert the search for any keyword by adding a "!" character before the search term, for example: ::

   iecc, !ENERGY STAR

In this case, all ECM names that include "iecc" or do *not* include "ENERGY STAR" will be matched.

To restore all ECMs to the active list from the inactive list, when prompted for the inactive to active move, enter: ::

   \s

If the user provides keywords for both moves (active to inactive and vice versa) and there are any ECMs that would be picked up by one or more keywords for the moves in each direction, the result would be an ECM being moved from active to inactive and then immediately back to active (or vice versa). For example, if the keyword "prospective" was provided for the move from active to inactive and "heat pump" for the move from inactive to active, an ECM with the name "Integrated Heat Pump (Prospective)" in either list would be matched by both keywords. To resolve these conflicts, the user would be prompted to decide whether each of these ECMs should end up in the active or inactive lists. 

Following these changes, the user will be asked whether additional ECMs should be moved to the inactive list if they are not applicable to the user's climate zone(s), building type, and/or structure type of interest. For example, a user will be prompted to select the building type (limited to only all residential or all commercial buildings) by number. ::

   1 - Residential
   2 - Commercial

If the user is only interested in residential buildings, they would input ::

   1

Before running the ECM active and inactive configuration module, it might be helpful to open |html-filepath| run_setup.json |html-fp-end| and review the existing list of active and inactive ECMs. 

To run the module, open a Terminal window (Mac) or command prompt (Windows) if one is not already open. If you're working in a new command window, navigate to the Scout project directory (shown with the example location |html-filepath| ./Documents/projects/scout-run_scheme\ |html-fp-end|). If your command window is already set to that folder/directory, the first line of the commands are not needed. Run the module by starting Python with the module file name |html-filepath| run_setup.py\ |html-fp-end|.

**Windows** ::

   cd Documents\projects\scout-run_scheme
   py -3 run_setup.py

**Mac** ::

   cd Documents/projects/scout-run_scheme
   python3 run_setup.py

If desired, the :ref:`manual editing <ecm-list-setup-manual>` instructions can be used to perform any further fine tuning of the active and inactive ECM lists.


.. _ecm-list-setup-manual:

Manual configuration
~~~~~~~~~~~~~~~~~~~~

The |html-filepath| run_setup.json |html-fp-end| file specifies whether each ECM will be included in or excluded from an analysis. Like the ECM definition JSON files, this file can be opened in your text editor of choice and modified to change which ECMs are active and inactive.

All of the ECM names should appear in this file under *exactly* one of two keys, "active" or "inactive." Each of these keys should be followed by a list (enclosed by square brackets) with the desired ECM names. If all ECMs are in the active list, the "inactive" value should be an empty list. 

To exclude one or more ECMs from the analysis, copy and paste their names from the "active" to the "inactive" list, and reverse the process to restore ECMs that have been excluded. Each ECM name in the list should be separated from the next by a comma.

.. tip::

   When manually editing the |html-filepath| run_setup.json |html-fp-end| file, be especially careful that there are commas separating each of the ECMs in the "active" and "inactive" lists, and that there is no comma after the last ECM in either list.


.. _tuts-analysis:

Tutorial 4: Running an analysis
-------------------------------

Once the ECMs have been pre-processed following the steps in :ref:`Tutorial 2 <tuts-2>`, the uncompeted and competed financial metrics and energy, |CO2|, and cost savings can be calculated for each ECM. Competition determines the portion of the applicable baseline market affected by ECMs that have identical or partially overlapping applicable baseline markets. The calculations and ECM competition are performed by |html-filepath| run.py |html-fp-end| following the outline in :ref:`Step 3 <analysis-step-3>` of the analysis approach section.

To run the uncompeted and competed ECM calculations, open a Terminal window (Mac) or command prompt (Windows) if one is not already open. If you're working in a new command window, navigate to the Scout project directory (shown with the example location |html-filepath| ./Documents/projects/scout-run_scheme\ |html-fp-end|). If your command window is already set to that folder/directory, the first line of the commands are not needed. Finally, run |html-filepath| run.py |html-fp-end| as a Python script.

**Windows** ::

   cd Documents\projects\scout-run_scheme
   py -3 run.py

**Mac** ::

   cd Documents/projects/scout-run_scheme
   python3 run.py

.. tip::
   Using the optional flag ``--verbose`` (i.e., ``python3 run.py --verbose``) will print all warning messages triggered during analysis execution to the console.

While executing, |html-filepath| run.py |html-fp-end| will print updates to the command window indicating the current activity -- loading data, performing calculations for a particular adoption scenario with or without competition, executing ECM competition, writing results to an output file, and plotting results. This text is principally to assure users that the analysis is proceeding apace. Upon completion, the total runtime will be printed to the command window, followed by an open prompt awaiting another command. The complete competed and uncompeted ECM data are stored in the |html-filepath| ecm_results.json |html-fp-end| file located in the |html-filepath| ./results |html-fp-end| folder.

Uncompeted and competed ECM results are automatically converted into graphical form by |html-filepath| run.py |html-fp-end| using R. Output plots are organized in folders by :ref:`adoption scenario <overview-adoption>` and :ref:`plotted metric of interest <overview-results>` (i.e., |html-filepath| ./results/plots/(adoption scenario)/(metric of interest)\ |html-fp-end|). Raw data for each adoption scenario's plots are stored in the XLSX files beginning with "Summary_Data."

.. note::
   The first time you execute |html-filepath| run.py\ |html-fp-end|, any missing R packages needed to generate the plots will be installed. This installation process may take some time, but is only required once.  

.. _tuts-results:

Tutorial 5: Viewing and understanding outputs
---------------------------------------------

Interpreting results figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The results figures from the plot generation script |html-filepath| plots.R |html-fp-end| are generated for both :ref:`adoption scenarios <ECM diffusion>`, and for one of three "metrics of interest": primary energy use, |CO2| emissions, and energy operating cost. Within the |html-filepath| ./results/plots |html-fp-end| folder, the folder hierarchy reflects these six cases (two adoption scenarios and three metrics of interest). For each case, the results are presented in three different sets of figures.

.. Note that the extremely inelegant link substitution here is to get around the problem that reStructuredText does not support nested inline markup, thus preventing the use of the |CO2| substitution within a standard :ref:`text <pointer>` internal hyperlink; see the emphasized hyperlink example here: http://docutils.sourceforge.net/FAQ.html#is-nested-inline-markup-possible; see also http://stackoverflow.com/questions/4743845/format-text-in-a-link-in-restructuredtext

1. |Internal rate of return, simple payback, cost of conserved energy, and cost of conserved CO2 plotted against a metric of interest.|_
2. :ref:`A metric of interest aggregated by climate zone, building class, and end use. <results-aggregated>`
3. :ref:`Both uncompeted and competed results for a metric of interest presented separately for each ECM. <results-by-ecm>`

.. |Internal rate of return, simple payback, cost of conserved energy, and cost of conserved CO2 plotted against a metric of interest.| replace:: Internal rate of return, simple payback, cost of conserved energy, and cost of conserved CO\ :sub:`2` plotted against a metric of interest.

Within each of the plots sub-folders (i.e., |html-filepath| ./results/plots/(adoption scenario)/(metric of interest)\ |html-fp-end|), each of these sets of plots is contained within a single PDF file.

.. _Internal rate of return, simple payback, cost of conserved energy, and cost of conserved CO2 plotted against a metric of interest.:
.. _results-cost-effectiveness:

Cost-effectiveness figures
**************************

The cost-effectiveness figures have file names that begin with "Cost Effective," followed by the metric of interest and then the adoption scenario (coded as "TP" for technical potential or "MAP" for maximum adoption potential), for example, |html-filepath| Cost Effective Energy Savings-MAP.pdf\ |html-fp-end|.

Each PDF file contains four plots corresponding to the four financial metrics used to assess ECM cost-effectiveness: internal rate of return (IRR), simple payback, cost of conserved energy (CCE), and cost of conserved |CO2| (CCC). For each plot, the applicable financial metric is on the y-axis, and the *reductions* in the metric of interest -- energy *savings*, *avoided* |CO2| emissions, or energy cost *savings* -- are plotted on the x-axis. All of the data shown include ECM competition and are drawn from a single year, which is indicated in the x-axis label.

.. _financial-metrics-plot-example:
.. figure:: images/Cost_Effective_Energy_Savings-MAP.*

   Each cost-effectiveness figure shows all four cost-effectiveness metrics calculated in Scout for each ECM: internal rate of return, simple payback, cost of conserved energy, and cost of conserved |CO2|. For this example figure, data from the maximum adoption potential scenario, inclusive of the effects of ECM competition, are shown. Each point corresponds to a single ECM. ECM building type(s) and end use(s) are indicated by each point according to the legend. For the portfolio of ECMs analyzed for this example, the same ECMs generally appear in the list of cost-effective ECMs with the greatest savings, listed in order of total savings in the top right corner of each plot. Solid-state lighting (SSL) ECMs that appear in the other plots are missing from the internal rate of return plot because their calculated incremental installed cost is zero or near zero. Because those technologies have zero/near zero incremental cost, an internal rate of return either cannot be calculated for them or the calculated value is above the plot region's upper bound. Additionally, several of the ECMs that appear in the internal rate of return and simple payback plots are missing from the cost of conserved energy and |CO2| plots; the latter two metrics have a denominator of competed energy savings and avoided |CO2| emissions, and these values are zero or near zero for the missing ECMs. Total cost-effective savings, based on the thresholds for each cost-effective metric, indicated by dotted horizontal lines, are generally similar.

:numref:`financial-metrics-plot-example` shows an example of the cost-effectiveness figures. All of the cost-effectiveness metrics are plotted against reductions in the metric of interest drawn from a specific year and from one of the two adoption scenarios, 2030 energy savings from the maximum adoption scenario in the case of :numref:`financial-metrics-plot-example`. The data shown include the effects of :ref:`ECM competition <ECM-competition>`. The various financial metrics can be used to evaluate the potential cost-effectiveness of the ECMs included in an analysis. The relevance of each metric in evaluating ECM cost-effectiveness will depend on the various economic and non-economic (e.g., policy) factors that might impact the particular individual or organization using these results.

On each plot, a dotted horizontal line represents a target threshold for the given financial metric, and the cost-effective region above or below each threshold is highlighted in gray. The thresholds used are positive IRR, five year payback, the projected U.S. average retail electricity price in the year indicated on the x axis, and the `Social Cost of Carbon`_ in the year indicated on the x axis (2.5% average) for IRR, simple payback, CCE, and CCC respectively. Above or below those lines, depending on whether higher or lower values are more favorable for that metric, the ECM might not be cost-effective in its target market. Total cost-effective savings (from all of the ECMs) for the metric of interest shown in the figure are reported in the top left corner of each plot area. Cost-effectiveness thresholds used in the plots should not be considered "official guidance" or canonical, but rather are provided as a starting point for further investigation of the results. Acceptable thresholds for each financial metric vary by building owner and type, thus each threshold shown is an indication of the range around which an ECM might not be cost-effective.

The shape and fill color of each point indicate the applicable building type(s) and end use(s) for each ECM shown on the plot. Comparing the relative locations of these various points might suggest where there are categories that are more generally cost-effective than others. As with the :ref:`baseline market-aggregated figures <results-aggregated>`, outcomes must be interpreted in light of the particular set of ECMs included in the underlying analysis. In :numref:`financial-metrics-plot-example`, the top five ECMs pertain to HVAC, water heating, and lighting - each of which constitutes a major end use category with high energy cost savings potential across the residential and commercial building sectors. Generally speaking, ECMs with a high energy performance to cost ratio are most likely to appear in the top five list.


.. _results-aggregated:

Baseline market-aggregated figures
**********************************

The results figures with metrics of interest grouped by the baseline market parameters :ref:`climate zone <json-climate_zone>`, building class [#]_, and :ref:`end use <json-end_use>` have file names that begin with the metric of interest, followed by the adoption scenario (coded as "TP" for technical potential or "MAP" for maximum adoption potential), and ending with "-Aggregate," for example, |html-filepath| Total Energy Savings-MAP-Aggregate.pdf\ |html-fp-end|.

Each PDF contains three plot areas, one for each of the three baseline market parameters. The x-axis corresponds to the modeling time horizon (by default, years 2015 through 2040), and the y-axis corresponds to the *reductions* in the metric of interest -- energy *savings*, *avoided * |CO2| emissions, or energy cost *savings* -- indicated in the file name. These plots summarize only the results that account for :ref:`ECM competition <ECM-competition>`. The dotted line on each plot corresponds to the right side y-axis and represents the cumulative results for all the ECMs in the analysis. The line is the same for all three plots within a single PDF. For these figures, while the data are shown as lines instead of points, the data exist as point values for each year in the modeling time horizon and line segments between each year are interpolated and do not represent actual model data.

.. _aggregate-by-end-use-plot-example:
.. figure:: images/Total_Energy_Savings-MAP-Aggregate.*

   In this figure, primary energy use reductions are summarized by :ref:`end use <json-end_use>`, :ref:`climate zone <json-climate_zone>`, and building class for the maximum adoption potential scenario, including ECM competition. Data are presented for each year in the modeling time horizon (note: this analysis includes ECMs with 2010 market entry years; thus the start year is reset to 2010 from a default of 2015). The majority of total energy savings in 2010 comes from the introduction of a lighting ECM where the baseline lighting technology has a lifetime of less than one year, as can be seen in the end use breakdown plot. As a result of the short baseline lighting lifetime, the entire lighting stock turns over in 2010. After 2010, annual savings for the lighting end use decline through 2015 as baseline lighting efficiency gradually improves and no new lighting ECMs are introduced to the market. Total energy savings are the same for most climate zones except AIA climate zone 1, which has a lower population density and baseline energy use than the other climate zones. The range of results by building class is a result of the comparatively larger baseline energy use reduction potential for existing residential buildings and, before 2020, the poor energy performance of commercial ECMs relative to comparable baseline technologies. Annual energy savings generally increase over time for new buildings, as more new construction accumulates, and reach a ceiling or decline for the existing buildings that are gradually replaced by new construction.

In general, the figures like :numref:`aggregate-by-end-use-plot-example` can be used to see at a glance the contributions from various end uses to overall results, as well as the distribution of results among building types and climate zones. While some end uses might appear to contribute more to the total annual or cumulative energy savings (or avoided |CO2| emissions or cost savings), the baseline energy use is different for each end use, and some end uses might appear to contribute more to the savings in part because their baseline energy use is greater. Similarly, while some building types or climate zones might show greater energy savings (or improvement in other metrics) than others, they may also have significantly different baseline energy use. 

These results are highly sensitive to the ECMs that are included in the analysis. While an introductory set of ECMs are provided with Scout, if ECMs added by a user are limited to a single end use, for example, it is reasonable to expect that greater reductions in energy use will come from that end use than other end uses.

In the building class plot, differences in the potential savings from new and existing buildings are a result of the building stock being dominated by existing buildings, thus yielding much larger savings in early years of the modeling time horizon than from new buildings.

For most end uses, ECMs and the baseline technologies have similar lifetimes. As the ECMs in that end use diffuse into the equipment and building stock and comparable baseline technology efficiencies improve, the total savings will gradually reach a ceiling or decline year after year, only yielding further increases if more efficient prospective ECMs become available in subsequent years.

In the version of the :numref:`aggregate-by-end-use-plot-example` that shows energy savings under the technical potential scenario, there are sharp increases in the energy savings in some end uses. These increases come from several key ECMs that have enough of a disparity in energy efficiency from the baseline technologies to yield dramatic overnight savings. Such increases are a result of the ECM adoption assumptions in the technical potential scenario, and should be viewed as an extreme upper bound on the potential for primary energy use reductions in the end uses, climate zones, and building classes shown.


.. _results-by-ecm:

ECM-specific figures
********************

The figures with results for the metric of interest for each ECM included in the analysis all have file names that begin with the metric of interest, followed by the adoption scenario (coded as "TP" for technical potential or "MAP" for maximum adoption potential), and ending with "-byECM," for example, |html-filepath| Total Cost-MAP-byECM.pdf\ |html-fp-end|.

The PDF file includes a single plot for each ECM, with the modeling horizon (by default, years 2015 through 2040) on the x-axis and the parameter indicated in the PDF file name on the y-axis -- energy, cost, or |CO2| emissions. A legend is included at the end of the figure on the last page of each PDF. Immediately preceding the legend is a summary plot showing the combined effect of all of the ECMs included in the analysis. 

The y-axis scale for each plot is adjusted automatically to be appropriate for the data shown. Care should be taken when inspecting two adjacent plots, since what look like similar changes in energy, |CO2|, or operating cost values at a glance, might in fact be quite different depending on the y-axes. The y-axis markings must be used to determine the magnitudes in the plots and to compare between plots.

Except for the "All ECMs" plot (illustrated in :numref:`tech-potential-energy-plot-example`), each plot shows at least four data series. The two darker, thicker lines correspond to the baseline data with and without ECM competition effects (i.e., "competed" and "uncompeted," respectively) and represent the portion of all U.S. buildings' energy use (or |CO2| emissions or operating cost expenses) that could be affected by the introduction of the ECM shown in that plot. The two thinner, lighter lines correspond to the "efficient" results with and without ECM competition effects and reflect the impact of the introduction of the ECM on the baseline energy, |CO2| or operating cost. 

These figures are most readily interpreted by comparing relevant pairs of lines.

* **Uncompeted baseline and competed baseline** -- the direct or indirect [#]_ effects of ECM competition on the total baseline market and associated energy, |CO2|, or cost that can be affected by each ECM
* **Uncompeted baseline and uncompeted "efficient"** -- the potential for energy savings, cost savings, and avoided |CO2| emissions from the ECM in the absence of alternative technologies that provide the same services
* **Competed baseline and competed "efficient"** -- the potential for energy savings, cost savings, and avoided |CO2| emissions from the ECM when other ECMs could provide equivalent service but with different energy/|CO2|/cost tradeoffs

In addition to these comparisons, the uncertainty range (if applicable) around "efficient" results and the effect of that uncertainty on competing ECMs should be examined. :numref:`max-adopt-potential-energy-plot-example` illustrates results for an ECM that includes a probability distribution in its definition and the effect of that distribution on related ECMs.

.. _tech-potential-energy-plot-example:
.. figure:: images/Total_Energy-TP-byECM.*

   Primary energy use baselines, and improvements with the adoption of two ECMs -- ENERGY STAR Refrigerator v. 4.1 and Prospective AFDD + Submetering -- are shown for each year in the modeling time horizon (note: the ENERGY STAR refrigerator ECM has a 2010 market entry year; thus the start year is reset to 2010 from a default of 2015). The data shown are from the :ref:`technical potential <ECM diffusion>` adoption scenario, which is reflected in the abrupt single-year changes in energy use when the ECM enters the market. The data are derived from a model that included many ECMs besides those shown, thus the ECMs’ impacts change under :ref:`competition <ECM-competition>`. Affected end uses are shown at the top of each plot to help determine which ECMs might be competing with each other. The "All ECMs" figure on the right side shows the aggregate reductions in the metric of interest from all of the ECMs included in the analysis, and the dotted line at the year 2030 indicates the total savings in that year.

When comparing the uncompeted or competed results in plots like those shown in :numref:`tech-potential-energy-plot-example` and :numref:`max-adopt-potential-energy-plot-example`, a difference between the baseline (dark) and efficient (light) cases indicates a potential reduction in the metric of interest plotted. In the absence of competition, the efficient case for both ECMs in :numref:`tech-potential-energy-plot-example` show the immediate realization of the entire savings potential upon market entry (2010 and 2020 for the ENERGY STAR refrigerator and Prospective AFDD ECM, respectively), which is characteristic of the technical potential scenario. 

While for many categories, the uncompeted baseline will decline into the future as technology improvements and new standards improve the efficiency of the building and equipment stock, there may be cases where the baseline increases over time. In general, this trend arises due to increases in the size of the stock, increases in home square footage (for residential ECMs), or increases in the capacity or size of the equipment (e.g., increases in the interior volume of refrigerators) that outpace improvements in the performance of the applicable equipment or building envelope component. This type of trend in the baseline appears in :numref:`tech-potential-energy-plot-example` for both the ENERGY STAR refrigerator and Prospective AFDD ECMs. Results for some ECMs show large variations in the baseline for years prior to the current year. These variations are an artifact of the configuration of the National Energy Modeling System (NEMS), which is used to generate the AEO__ projections.

.. __: http://www.eia.gov/forecasts/aeo/

When ECM competition is introduced, the baseline reflects the year of market entry of each ECM and its competitiveness relative to the other ECMs included in the analysis. Prior to the market availability of an ECM, the competed baseline will reflect the portion of the market left over from competing ECMs. Once the ECM is available, it can begin to recapture some of the market, depending on its competitiveness. If the ECM is more competitive, then it will capture a greater portion of the total available market. If the competed baseline appears to follow the same trend as the uncompeted baseline, the ECM is not capturing any (or any more) of the available market. In :numref:`tech-potential-energy-plot-example`, the refrigerator ECM captures all of its potential market in its first year of availability, when no competing refrigerator ECMs are on the market; the potential market for this ECM is substantially reduced in 2015, with the introduction of an updated ENERGY STAR refrigerator ECM, and is all but eliminated in 2020, with the introduction of a prospective refrigerator ECM that satisfies aggressive cost and performance targets (competing refrigerator ECMs not shown). Conversely, the potential market for the Prospective AFDD ECM in :numref:`tech-potential-energy-plot-example` grows after its market introduction; this growth continues between 2020-2025, when the introduction of additional ECMs reduces the market share of ECMs that compete with the Prospective AFDD ECM, thus increasing its potential market.

.. _max-adopt-potential-energy-plot-example:
.. figure:: images/Total_Energy-MAP-byECM.*

   The ENERGY STAR Central AC ECM includes a probability distribution on one or more of the installed cost, efficiency, or product lifetime, which is reflected in the results. The 5th and 95th percentile bounds for each affected value are shown with dashed lines of the same color. The two ECMs shown on the left are combined into the package ECM on the right. The package ECM results reflect the effect of the probability distributions in the contributing ECMs.

The effect of probability distributions are reflected in the results of the ECMs that include them in their definitions, as well as in the competed results for any competing ECMs and in any packages that include the ECM. The effects of uncertainty will always appear in the results with the ECM applied (i.e., the "efficient" results), though if the spread of the distribution is quite small, it might be difficult to see the dashed lines showing those effects in plots :numref:`max-adopt-potential-energy-plot-example`. In addition, if a probability distribution is applied to the installed cost or energy efficiency of the ECM, it will create uncertainty in the capital and/or operating cost of the ECM, and thus will introduce uncertainty in :ref:`ECM competition <ECM-competition>`, which is reflected in the competed baseline for the ECM. The ENERGY STAR air conditioning ECM in :numref:`max-adopt-potential-energy-plot-example` shows this effect.


Viewing tabular outputs
~~~~~~~~~~~~~~~~~~~~~~~

The plot generation script in R also produces Excel-formatted files containing summaries of the results. The summary results for each adoption scenario are stored in the corresponding scenario folder within the |html-filepath| ./results/plots |html-fp-end| directory. The structure of the results in the files corresponding to each scenario is identical. Each file has three tabs, corresponding to energy use, |CO2| emissions, and energy cost results. These results correspond to the data that are shown in the ECM-specific plots, as in :numref:`tech-potential-energy-plot-example`, and the tabular results can be used to create custom visualizations different from those automatically generated with |html-filepath| plots.R\ |html-fp-end|.

.. tip::
   If you are experienced with R, you can also modify |html-filepath| plots.R |html-fp-end| to tailor the figures to your preferences.

On each tab, the first five columns provide information about the ECM and the type of data reported in each row. The first column contains the name of the ECM for the data in each row and the third through fifth columns provide details regarding the climate zones, building classes, and end uses that apply to each ECM. The second column indicates the type of data in each row -- one of the four series shown in :numref:`tech-potential-energy-plot-example`, the baseline and efficient results, with and without ECM competition. The sixth through ninth columns contain results for the financial metrics: internal rate of return (IRR), simple payback, cost of conserved energy (CCE), and cost of conserved |CO2| (CCC). When any of the financial metrics cannot be calculated (e.g., simple payback for a negative incremental capital cost, or negative energy cost savings) the metric will be reported as the value 999. The columns beyond the ninth column contain the results for the metric of interest (energy use, |CO2| emissions, or energy cost) indicated by the worksheet tab name. Each of those columns corresponds to a year in the simulation, with the year indicated in the first row. 

For a given set of results data on a single tab, each ECM included in the simulation appears in four rows that are distinguished by the ECM's name (listed under the "ECM Name" column). These four rows correspond to the uncompeted and competed baseline results, as well as the ("efficient") results with the ECM applied, again with and without competition. For each ECM, these rows correspond to the four primary lines that appear in the ECM-specific results figures, as in :numref:`tech-potential-energy-plot-example`.

In each results tab, rows 2-22 include results summed across the entire ECM portfolio (rows with "All ECMs" listed under the "ECM Name" column). The information in these 21 rows is interpreted as follows: rows 2-3 show competed baseline and efficient results summed across the entire ECM portfolio - these rows correspond to the two primary lines that appear in the "All ECMs" plot in the ECM-specific results figures; row 4 shows the difference between the competed baseline and efficient results shown in rows 2-3 ("Baseline - efficient"); and rows 5-22 break down the result shown in row 4 by climate zone (5 climate categories/rows), building type (4 building type categories/rows), and end use (9 end use categories/rows).

.. note::
   For each ECM in the results, in addition to the *total* energy use, |CO2| emissions, and energy cost results contained in the Excel files, the |html-filepath| ecm_results.json |html-fp-end| file includes those results broken out by each of the applicable baseline market parameters -- |baseline-market| -- that apply to each ECM. These results breakdowns are provided for both the baseline and efficient cases (without and with the ECM applied, respectively).

.. _associative arrays: https://en.wikipedia.org/wiki/Associative_array
.. _Python dictionaries: https://docs.python.org/3/tutorial/datastructures.html#dictionaries
.. __: https://www.eia.gov/forecasts/aeo/data/browser/#/?id=4-AEO2016&cases=ref2016~ref_no_cpp&sourcekey=0
.. __: https://www.eia.gov/forecasts/aeo/data/browser/#/?id=5-AEO2016&cases=ref2016~ref_no_cpp&sourcekey=0

.. REPLACE DICTONARIES LINK WITH SPHINX-LIKE REFERENCE

.. rubric:: Footnotes

.. [#] These key-value pairs enclosed with curly braces are called `associative arrays`_, and JSON files use syntax for these arrays that is similar to `Python dictionaries`_.
.. [#] The end uses also largely correspond to the residential__ and commercial__ end uses specified in the AEO.
.. [#] Note that this document does not cover lighting, where varying bulb types are used, or Miscellaneous Electric Loads (MELs), which are not broken into specific technologies in the Annual Energy Outlook.
.. [#] The "applicable baseline market" is comprised of the |baseline-market| fields.
.. [#] Acceptable domains include eia.gov, doe.gov, energy.gov, data.gov, energystar.gov, epa.gov, census.gov, pnnl.gov, lbl.gov, nrel.gov, sciencedirect.com, costar.com, and navigantresearch.com.
.. [#] The retrofit rate assumption only affects the :ref:`Maximum Adoption Potential <overview-adoption>` scenario results, in which realistic equipment turnover dynamics are considered.
.. [#] The size parameter specifies the number of samples to draw from the specified distribution. The number of samples is preset to be the same for all ECMs to ensure consistency. 
.. [#] If the warning "there is no package called 'foo'," where "foo" is a replaced by an actual package name, appears in the R Console window, try running the script again. If the warning is repeated, the indicated package should be added manually. From the Packages menu, (Windows) select Install package(s)... or (Mac) from the Packages & Data menu, select Package Installer and click the Get List button in the Package Installer window. If prompted, select a repository from which to download packages. On Windows, select the named package (i.e., "foo") from the list of packages that appears. On a Mac, search in the list for the named package (i.e., "foo"), click the "Install Dependencies" checkbox, and click the "Install Selected" button. When installation is complete, close the Package Installer window.
.. [#] Building class corresponds to the four combinations of :ref:`building type <json-bldg_type>` and :ref:`structure type <json-structure_type>`.
.. [#] When ECMs are competed against each other, demand-side heating and cooling ECMs that improve the performance of the building envelope reduce the energy required to meet heating and cooling needs (supply-side energy), and that reduction in energy requirements for heating and cooling is reflected in a reduced baseline for supply-side heating and cooling ECMs. At the same time, supply-side heating and cooling ECMs that are more efficient reduce the energy used to provide heating and cooling services, thus reducing the baseline energy for demand-side ECMs. The description of :ref:`ECM competition <ecm-competition>` in Step 3 of the analysis approach section includes further details regarding supply-side and demand-side heating and cooling energy use balancing.