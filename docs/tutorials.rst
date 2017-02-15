.. _tutorials:

Tutorials
=========


.. _tuts-1:

Tutorial 1: Creating and editing ECMs
-------------------------------------

Before beginning this tutorial, it is recommended that you review the :ref:`list of parameters <ecm-contents>` in an ECM definition.

The :ref:`json-schema` should always be in your back pocket as a reference. This section includes brief descriptions, allowable options, and examples for each of the fields in an ECM definition. You might want to have it open in a separate tab in your browser while you complete this tutorial, and any time you're authoring or editing an ECM. 

The example in this tutorial will demonstrate how to write new ECMs so that they will be compliant with all relevant formatting requirements and provide the :ref:`needed information <ecm-contents>` about a technology in the structure expected by the Scout analysis engine. This example is intentionally plain to illustrate the basic features of an ECM definition and is *not* an exhaustive description of all of the detailed options available to specify an ECM. These additional options are presented in the :ref:`ecm-features` section, and the :ref:`json-schema` has detailed specifications for each field in an ECM definition. In addition, this tutorial includes information about how to :ref:`edit existing ECMs <editing-ecms>` and :ref:`define package ECMs <package-ecms>`.

As a starting point for writing new ECMs, an empty ECM definition file is available for :download:`download </examples/blank_ecm.json>`. Reference versions of the tutorial ECMs are also provided for download to check one's own work following completion of the examples.

Each new ECM created should be saved in a separate file. To add new or edited ECMs to the analysis, the files should be placed in the "ecm_definitions" directory. Further details regarding where ECM definitions should be saved and how to ensure that they are included in new analyses are included in :ref:`Tutorial 2 <tuts-2>`.

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

For this example, we will be creating an ECM for LED troffers for commercial buildings. Troffers are square or rectangular light fixtures designed to be used in a modular dropped ceiling grid commonly seen in offices and other commercial spaces.

The finished ECM specification is available to :download:`download </examples/led_troffers.json>` for reference.

To begin, the ECM should be given a short, but descriptive name. Details regarding the characteristics of the technology that will be included elsewhere in the ECM definition, such as the cost, efficiency, or lifetime, need not be included in the title. The key for the name is simply ``name``. ::

   {"name": "LED Troffers"}

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

For this example, LED troffers are likely to replace linear fluorescent bulbs, the typical bulb type in troffers. There are many lighting types for commercial buildings, but we will include all of the lighting types that are specified as F\_\_T\_\_, which correspond to linear fluorescent bulb types, including those with additional modifying text. ::

   {...
    "technology": ["F28T8 HE w/ OS", "F28T8 HE w/ SR", "F96T8", "F96T12 mag", "F96T8 HE", "F28T8 HE w/ OS & SR", "F28T5", "F28T8 HE", "F32T8", "F96T12 ES mag", "F34T12", "T8 F32 EEMag (e)"],
    ...}

.. __: https://github.com/trynthink/scout/blob/master/1999%20Residential%20heating%20and%20cooling%20loads%20component%20analysis.pdf
.. __: https://github.com/trynthink/scout/blob/master/1999%20Commercial%20heating%20and%20cooling%20loads%20component%20analysis.pdf
.. _AEO: https://www.eia.gov/analysis/studies/buildings/equipcosts/pdf/full.pdf


Market entry and exit year
**************************

The market entry year represents the year the technology is or will be available for purchase and installation. Some ECMs might be prospective, representing technologies not currently available. Others might represent technologies currently commercially available. The market entry year should reflect the current status of the technology described in the ECM. Similarly, the market exit year represents the year the technology is expected to be withdrawn from the market. If the technology described by an ECM will have a lower installed cost or improved energy efficiency after its initial market entry, another ECM should be created that reflects the improved version of the product, and the market exit year should not (in general) be used to force an older technology out of the market.

The market entry year and exit year both require source information. As much as is practicable, a :ref:`high quality<ecm-sources>` reference should be used for both values. If no source is available, such as for a technology that is still quite far from commercialization, a brief explanatory note should be provided for the market entry year source, and the :ref:`json-source_data` fields themselves can be given as ``null`` or with empty strings. If it is anticipated that the product will not be withdrawn from the market prior to the end of the model :ref:`time horizon <2010-2040 projection>`, the exit year and source should be given as ``null``.

LED troffers are currently commercially available with a range of efficiency, cost, and lifetime ratings. It is likely that while LED troffers will not, in general, exit the market within the model :ref:`time horizon <2010-2040 projection>`, LED troffers with cost and efficiency similar to this ECM are not likely to remain competitive through 2040. It will, however, be left to the analysis to determine whether more advanced lighting products enter the market and supplant this ECM, rather than specifying a market exit year. ::

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

There are many ways in which an ECM definition can be augmented, beyond the basic example already presented, to more fully characterize a technology. The subsequent sections explain how to implement the myriad options available to add more detail and complexity to your ECMs. Links to download example ECMs that illustrate the feature described are at the beginning of each section.

.. PHRASING

.. _ecm-features-shorthand:

Baseline market shorthand values
********************************

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
    "bldg_type": ["all residential", "small office", "mercantile/service"],
    ...}

The :ref:`ECM definition reference <ecm-applicable-baseline-market>` specifies whether these shorthand terms are available for each of the applicable baseline market fields and what shorthand strings are valid for each field.

If these shorthand terms are used to specify the applicable baseline market fields, they can also be used for a :ref:`detailed input specification <ecm-features-detailed-input>` for energy efficiency, installed cost, or lifetime. For example, if an ECM applies to "all residential," "small office," and "lodging" building types, the installed cost could be specified separately for each of these building types. ::

   {...
    "installed_cost": {
      "all residential": 5530,
      "small office": 6190,
      "lodging": 6015},
    ...}

Separate installed costs can also be specified for each of the residential building types, even if they are indicated as a group using the "all residential" shorthand for the building type field. ::

   {...
    "bldg_type": ["all residential", "small office", "lodging"],
    ...
    "installed_cost": {
      "single family home": 5775,
      "multi family home": 5693,
      "mobile home": 5288,
      "small office": 6190,
      "lodging": 6015},
    ...}

.. _ecm-example-shorthand:

A whole building sub-metering ECM is available for download that illustrates the use of shorthand terms by employing the "all" shorthand term for most of the applicable baseline market fields (|baseline-market|) and the "all commercial" shorthand term as one of the building types and to define separate installed costs for the various building types that apply to the ECM. If you would like to see additional examples, many of the other examples available to download in this section use shorthand terms for one or more of their applicable baseline market fields.


.. _ecm-features-detailed-input:

Detailed input specification
****************************

:download:`Example <examples/Thermoelastic HP (Prospective).json>` -- Thermoelastic Heat Pump ECM (:ref:`Details <ecm-example-detailed-input>`)

The energy efficiency, installed cost, and lifetime values in an ECM definition can be specified as a point value or with separate values for one or more of the applicable baseline market keys (|baseline-market|). As shown in :numref:`table-detailed-input-options`, the allowable baseline market keys are different for the energy efficiency, installed cost, and lifetime values.

.. table:: The baseline market keys that can be used to provide a detailed specification of the energy efficiency, installed cost, or lifetime input fields in an ECM definition depend on which field is being specified.
   :name: table-detailed-input-options

   +----------------------------+-------------------------------+----------------------------+------------------------------+
   | Baseline Market Key        |       Energy Efficiency       |       Installed Cost       |       Product Lifetime       |
   +============================+===============================+============================+==============================+
   | :ref:`json-climate_zone`   |               X               |                            |                              |
   +----------------------------+-------------------------------+----------------------------+------------------------------+
   | :ref:`json-bldg_type`      |               X               |              X             |               X              |
   +----------------------------+-------------------------------+----------------------------+------------------------------+
   | :ref:`json-structure_type` |               X               |              X             |                              |
   +----------------------------+-------------------------------+----------------------------+------------------------------+
   | :ref:`json-end_use`        |               X               |                            |                              |
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

If a detailed input specification includes two or more baseline market keys, the keys should be placed in a nested dict structure. The order in which the keys are nested does not matter and is at the discretion of the user. Multi-function heat pumps, which provide heating, cooling, and water heating services, are an example of a case where a detailed energy efficiency specification by climate zone and end use might be appropriate. ::

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

As noted previously, the order does not matter, thus an equivalent specification of efficiency for the same ECM could be given by end use and then by climate zone. ::

   {...
    "energy_efficiency": {
      "heating": {
         "AIA_CZ1": 1.05,
         "AIA_CZ2": 1.15,
         "AIA_CZ3": 1.3,
         "AIA_CZ4": 1.4,
         "AIA_CZ5": 1.4},
      "cooling": {
         "AIA_CZ1": 1.3,
         "AIA_CZ2": 1.26,
         "AIA_CZ3": 1.21,
         "AIA_CZ4": 1.16,
         "AIA_CZ5": 1.07}
      "water heating": {
         "AIA_CZ1": 1.25,
         "AIA_CZ2": 1.31,
         "AIA_CZ3": 1.4,
         "AIA_CZ4": 1.57,
         "AIA_CZ5": 1.7}},
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

A thermoelastic heat pump ECM is available for download to illustrate the use of the detailed input specification approach for the installed cost data and units, as well as the page information for the installed cost source.


.. _ecm-features-relative-savings:

Relative energy efficiency units
********************************

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

An occupant-centered controls ECM available for download, like all controls ECMs, uses relative savings units. It also illustrates several other features discussed in this section, including :ref:`shorthand terms <ecm-features-shorthand>`, :ref:`detailed input specification <ecm-features-detailed-input>`, and the :ref:`add-on measure type <ecm-features-measure-type>`.


.. ecm-features-energyplus: (CONVERT BACK TO SECTION REFERENCE TAG)

.. EnergyPlus efficiency data
  **************************

.. For commercial building types, energy efficiency values can be specified using data from an :ref:`EnergyPlus simulation <analysis-step-2-energyplus>`. EnergyPlus simulation data include results for all of the energy uses that are affected by the ECM, including end uses that are not in the applicable baseline market for the ECM. These effects on other end uses are automatically incorporated into the final results for the ECM. EnergyPlus simulation data cannot be combined with :ref:`probability distributions <ecm-features-distributions>` on energy efficiency.

.. Results from EnergyPlus that can be used for energy efficiency inputs in ECMs are stored in CSV files. Each EnergyPlus CSV file is specific to a single building type and can include energy efficiency data for many simulated ECMs. These files should be placed in the directory "energyplus_data" (inside the "ecm_definitions" folder). To import energy efficiency data from these files, the user sets the "energy_efficiency" attribute for an ECM to a dict in a specific form: ``"energy_efficiency": {"EnergyPlus file": "ECM_name"}``. Here, "ECM_name" will determine which rows will be read in the EnergyPlus files. The "ECM_name" string should match exactly with the text in the "measure" column in the EnergyPlus CSV files corresponding to the relevant data. Only the EnergyPlus file(s) that correspond to an ECM's building type(s) will be read. When EnergyPlus data are being used, ECM energy efficiency units should always be "relative savings (constant)." 

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

The automated fault detection and diagnosis (AFDD) ECM available for download illustrates the use of the market scaling fraction to limit the applicability of the ECM to only buildings with building automation systems (BAS), since that is a prerequisite for the implementation of the AFDD technology described in the ECM.


.. _ecm-features-measure-type:

Add-on type ECMs
****************

:download:`Example <examples/Plug-and-Play Sensors (Prospective).json>` -- Plug-and-Play Sensors ECM (:ref:`Details <ecm-example-measure-type>`)

Technologies that affect the operation of or augment the efficiency of the existing components of a building must be defined differently in an ECM than technologies that replace a building component. Examples include sensors and control systems, window films, and daylighting systems. These technologies improve or affect the operation of another building system -- HVAC or other building equipment, windows, and lighting, respectively -- but do not replace those building systems.

For these technologies, several of the fields of the ECM must be configured slightly differently. First, the applicable baseline market should be set for the end uses and technologies that are affected by the technology, not those that describe the technology. For example, an automated fault detection and diagnosis (AFDD) system that affects heating and cooling systems should have the end uses "heating" and "cooling," not some type of electronics or miscellaneous electric load (MEL) end use. Second, the energy efficiency values should have :ref:`relative savings <ecm-features-relative-savings>`  units and the installed cost units should match those specified in the :ref:`ECM Definition Reference <ecm-installed-cost-units>`, noting that they are different for sensors and controls ECMs. Finally, the :ref:`json-measure_type` field should have the value ``"add-on"`` instead of ``"full service"``.

.. _ecm-example-measure-type:

A plug-and-play sensors ECM available to download to illustrate the use of the "add-on" ECM type.

.. <<< DOWNLOADABLE EXAMPLE >>> ADD A DAYLIGHTING ECM? (Daylighting needs market scaling fraction to reduce to lighting in the perimeter zone of buildings?)


.. _ecm-features-multiple-fuel-types:

Multiple fuel types
*******************

Some technologies, especially those that serve multiple end uses, might yield much greater energy savings if they are permitted to supplant technologies with different fuel types. Heat pumps, for example, can provide heating and cooling using a single fuel type (typically electricity), but could replace an HVAC system that uses different fuels for heating and cooling. The :ref:`json-fuel_switch_to` field, used in conjunction with the :ref:`json-fuel_type` field in the baseline market enables ECMs that serve multiple end uses and could replace technologies with various fuel types.

To configure these ECMs, the :ref:`json-fuel_type` field should be populated with a list of the fuel types that, for the applicable end uses, are able to be supplanted by the technology described by the ECM. The :ref:`json-fuel_switch_to` field should be set to the string for the fuel type of the technology itself. For example, an ECM that describes a natural gas-fired heat pump might be able to replace technologies that use electricity, natural gas, or distillate fuels. ::

   {...
    "fuel_type": ["electricity", "natural gas", "distillate"],
    ...
    "fuel_switch_to": "natural gas",
    ...}

.. <<< DOWNLOADABLE EXAMPLE >>>


.. _ecm-features-distributions:

Probability distributions
*************************

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

An ENERGY STAR LED bulbs ECM is available for download to illustrate the use of probability distributions, in that case, on installed cost and product lifetime.


.. _editing-ecms:

Editing existing ECMs
~~~~~~~~~~~~~~~~~~~~~

All of the ECM definitions are stored in the "ecm_definitions" folder. To edit any of the existing ECMs, open that folder and then open the JSON file for the ECM of interest. Make any desired changes, save, and close the edited file. Like new ECMs, all edited ECMs must be prepared following the steps in :ref:`Tutorial 2 <tuts-2>`.

Making changes to the existing ECMs will necessarily overwrite previous versions of those ECMs. If both the original and revised version of an ECM are desired for subsequent analysis, make a copy of the original JSON file (copy and paste the file in the same directory) and rename the copied JSON file with an informative differentiating name. When revising the copied JSON file with the new desired parameters, take care to ensure that the ECM name is updated as well. 

.. tip::
   No two ECMs can share the same file name *or* name given in the JSON.


.. _package-ecms:

Creating and editing package ECMs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Package ECMs are not actually unique ECMs, rather, they are combinations of existing (single technology) ECMs specified by the user. Existing ECMs can be included in multiple different packages; there is no limit to the number of packages to which a single ECM may be added. There is also no limit on the number of ECMs included in a package.

A package ECM might make sense, for example, in a case where a particular grouping of ECMs could reduce installation labor requirements, or where a combination of ECMs would yield better overall efficiency than if the ECMs were implemented separately. More specifically, a package ECM could be created from an air barrier ECM and an insulation ECM to represent performing an air barrier *and* insulation retrofit at `tenant fit-out`_ in a commercial building, which could reduce the labor cost and thus the combined total installed cost by installing both systems at the same time. If one or more building type-appropriate HVAC equipment ECMs are added to the air barrier and insulation package ECM, downsizing of the HVAC equipment could further reduce the combined total installed cost. The definition for each package includes fields to specify any improvements in cost and/or efficiency, if they apply. (Package ECMs could also include reductions in efficiency and/or increases in installed cost, but it is expected that those packages would not be of interest.)

.. _tenant fit-out: https://www.designingbuildings.co.uk/wiki/Fit_out_of_buildings

Package ECMs are specified in the "package_ecms.json" file, located in the "ecm_definitions" folder. A version of the "package_ecms.json" file with a single blank ECM package definition is available for :download:`download <examples/blank_package_ecms.json>`. 

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

All of the intended packages should be specified in the "package_ecms.json" file. For example, the contents of the file should take the following form if there are three desired packages, with three, two, and four ECMs, respectively. ::

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

The Scout analysis is divided into two steps, each with corresponding Python modules. In the first of these steps, discussed in this tutorial, the ECMs are pre-processed by retrieving the applicable baseline energy, |CO2|, and cost data from the input files (located in the supporting_data/stock_energy_tech_data directory) and calculating the uncompeted efficient energy, |CO2|, and cost values. This pre-processing step ensures that the computationally intensive process of parsing the input files to retrieve and calculate the relevant data is only performed once for each new or edited ECM.

Each new ECM that is written following the formatting and structure guidelines covered in :ref:`Tutorial 1 <tuts-1>` should be saved in a separate JSON file with an informative file name and placed in the "ecm_definitions" directory. If any changes to the package ECMs are desired, incorporating either or both new and existing ECMs, follow the instructions in the :ref:`package ECMs <package-ecms>` section to specify these packages. The pre-processing script can be run once these updates are complete.

To run the pre-processing script ``ecm_prep.py``, open a Terminal window (Mac) or command prompt (Windows), navigate to the Scout project directory (shown with the example location ``Documents/projects/scout-run_scheme``), and run the script.

**Windows** ::

   cd Documents\projects\scout-run_scheme
   py -3 ecm_prep.py

**Mac** ::

   cd Documents/projects/scout-run_scheme
   python3 ecm_prep.py

As each ECM is processed by "ecm_prep.py", the text "Updating ECM" and the ECM name are printed to the command window, followed by text indicating whether the ECM has been updated successfully. There may be some additional text printed to indicate whether the installed cost units in the ECM definition were converted to match the desired cost units for the analysis. If any exceptions (errors) occur, the module will stop running and the exception will be printed to the command window with some additional information to indicate where the exception occurred within "ecm_prep.py." The error message printed should provide some indication of where the error occurred and in what ECM. This information can be used to narrow the troubleshooting effort.

If "ecm_prep.py" runs successfully, a message with the total runtime will be printed to the console window. The names of the ECMs updated will be added to ``run_setup.json``, a file that indicates which ECMs should be included in :ref:`the analysis <analysis-step-3>`. The total baseline and efficient energy, |CO2|, and cost data for those ECMs that were just added or revised are added to the "competition_data" folder, where there appear separate compressed files for each ECM. High-level summary data for all prepared ECMs are added to the ``ecm_prep.json`` file in the "supporting_data" folder. These files are then used by the ECM competition routine, outlined in :ref:`Tutorial 4 <tuts-analysis>`.

If exceptions are generated, the text that appears in the command window should indicate the general location or nature of the error. Common causes of errors include extraneous commas at the end of lists, typos in or completely missing keys within an ECM definition, invalid values (for valid keys) in the specification of the applicable baseline market, and units for the installed cost or energy efficiency that do not match the baseline cost and efficiency data in the ECM.


.. _tuts-ecm-list-setup:

Tutorial 3: Modifying the active ECMs list
------------------------------------------

Prior to running an analysis, the list of ECMs that will be included in that analysis can be revised to suit your interests. For example, if your primary interest is in ECMs that are applicable to commercial buildings, you could choose to include only those ECMs in your analysis. 

The "active" (i.e., included in the analysis) and "inactive" (i.e., excluded from the analysis) ECMs are specified in the "run_setup.json" file. There are two ways to modify the lists of ECMs: by :ref:`manually editing them <ecm-list-setup-manual>` or :ref:`using the automatic configuration module <ecm-list-setup-automatic>`.

If you would like to run your analysis with all of the ECMs and have not previously edited the lists of active and inactive ECMs, you can skip these steps and go straight to :ref:`Tutorial 4 <tuts-analysis>`, as all ECMs are included by default.

.. tip::
   As new ECMs are added and pre-processed (by running ecm_prep.py), their names are added to the "active" list. Any ECMs that were edited after being moved to the inactive list will be automatically moved back to the active list by ecm_prep.py. 


.. _ecm-list-setup-automatic:

Automatic configuration
~~~~~~~~~~~~~~~~~~~~~~~

The automatic configuration module "run_setup.py" can perform a limited set of adjustments to the active and inactive ECM lists in "run_setup.json."

1. Move ECMs from the active to the inactive list, and vice versa, based on searching the ECM names for matches with user-provided keywords
2. Move ECMs from the active to the inactive list if they do not apply to the climate zone(s), building type, and/or structure type of interest

For each of the changes supported by the module, messages will be printed to the command window that will explain what information should be input by the user. When entering multiple values, all entries should be separated by commas. Any question can be skipped to ignore the filtering option by pressing the "enter" or "return" key.

For the first set of changes, moving ECMs by searching their names for matches with user-provided keywords, the user will be prompted to enter their desired keywords for each move separately, first for moving ECMs from the active to the inactive list, and then for the opposite move. Keyword matching is not case-sensitive and multiple keywords should be separated by commas. Potential inputs from the user might be, for example: ::

   ENERGY STAR, prospective, 20%

or ::

   iecc

If the user provides keywords for both moves (active to inactive and vice versa) and there are any ECMs that would be picked up by one or more keywords for the moves in each direction, the result would be an ECM being moved from active to inactive and then immediately back to active (or vice versa). For example, if the keyword "prospective" was provided for the move from active to inactive and "heat pump" for the move from inactive to active, an ECM with the name "Integrated Heat Pump (Prospective)" in either list would be matched by both keywords. To resolve these conflicts, the user would be prompted to decide whether each of these ECMs should end up in the active or inactive lists. 

Following these changes, the user will be asked whether additional ECMs should be moved to the inactive list if they are not applicable to the user's climate zone(s), building type, and/or structure type of interest. For example, a user will be prompted to select the building type (limited to only all residential or all commercial buildings) by number. ::

   1 - Residential
   2 - Commercial

If the user is only interested in residential buildings, they would input ::

   1

Before running the ECM active and inactive configuration module, it might be helpful to open "run_setup.json" and review the existing list of active and inactive ECMs. 

To run the module, open a Terminal window (Mac) or command prompt (Windows) if one is not already open. If you're working in a new command window, navigate to the Scout project directory (shown with the example location ``Documents/projects/scout-run_scheme``). If your command window is already set to that folder/directory, the first line of the commands are not needed. Run the module by starting Python with the module file name "run_setup.py."

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

The "run_setup.json" file specifies whether each ECM will be included in or excluded from an analysis. Like the ECM definition JSON files, this file can be opened in your text editor of choice and modified to change which ECMs are active and inactive.

All of the ECM names should appear in this file under *exactly* one of two keys, "active" or "inactive." Each of these keys should be followed by a list (enclosed by square brackets) with the desired ECM names. If all ECMs are in the active list, the "inactive" value should be an empty list. 

To exclude one or more ECMs from the analysis, copy and paste their names from the "active" to the "inactive" list, and reverse the process to restore ECMs that have been excluded. Each ECM name in the list should be separated from the next by a comma.

.. tip::

   When manually editing the "run_setup.json" file, be especially careful that there are commas separating each of the ECMs in the "active" and "inactive" lists, and that there is no comma after the last ECM in either list.


.. _tuts-analysis:

Tutorial 4: Running an analysis
-------------------------------

Once the ECMs have been pre-processed following the steps in :ref:`Tutorial 2 <tuts-2>`, the uncompeted and competed financial metrics and energy, |CO2|, and cost savings can be calculated for each ECM. Competition determines the portion of the applicable baseline market affected by ECMs that have identical or partially overlapping applicable baseline markets. The calculations and ECM competition are performed by ``run.py`` following the outline in :ref:`Step 3 <analysis-step-3>` of the analysis approach section.

To run the uncompeted and competed ECM calculations, open a Terminal window (Mac) or command prompt (Windows) if one is not already open. If you're working in a new command window, navigate to the Scout project directory (shown with the example location ``Documents/projects/scout-run_scheme``). If your command window is already set to that folder/directory, the first line of the commands are not needed. Finally, run "run.py" as a Python script.

**Windows** ::

   cd Documents\projects\scout-run_scheme
   py -3 run.py

**Mac** ::

   cd Documents/projects/scout-run_scheme
   python3 run.py

While executing, "run.py" will print updates to the command window indicating the current activity -- loading data, performing calculations for a particular adoption scenario with or without competition, executing ECM competition, or writing results to an output file. This text is principally to assure users that the analysis is proceeding apace.

Upon completion, the total runtime will be printed to the command window, followed by an open prompt awaiting another command. The complete competed and uncompeted ECM data are stored in the "ecm_results.json" file located in the "results" folder. While the JSON results file can be reviewed directly, :ref:`Tutorial 5 <tuts-results>` explains how the data can be converted into plots.


.. _tuts-results:

Tutorial 5: Viewing and understanding outputs
---------------------------------------------

Generating/updating figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The uncompeted and competed ECM results can be converted into graphical form using R. To begin, open R (sometimes called R GUI) from the Applications folder (Mac) or the Start Menu (Windows). Like a Terminal window or command prompt, R will need to be switched to the project directory. The plot generation script can then be run. ::

   setwd('~/Documents/projects/scout-run_scheme')
   source('plots.R')

Additional packages are required to run the plot generation R script. Running the script should install the packages automatically, though you may be prompted to choose a server from which to download the packages. If the packages do not install automatically, additional troubleshooting may be required. [#]_

.. NEED TO UPDATE THE FOOTNOTE WITH ADDITIONAL DETAILS ABOUT INSTALLING PACKAGES

The plot image files can be found in the "plots" folder inside the "results" folder. The plots are separated into folders by :ref:`adoption scenario <ECM diffusion>`.

Interpreting results figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The results are presented in three different types of figures. 

1. Both uncompeted and competed results for energy savings, avoided |CO2| emissions, and cost savings presented separately for each ECM.
2. Competed energy savings, avoided |CO2| emissions, and cost savings results aggregated by climate zone, building class, and end use.
3. Internal rate of return, simple payback, cost of conserved energy, and cost of conserved |CO2| plotted against competed energy savings, avoided |CO2| emissions, and cost savings.

The results are produced in separate folders for each :ref:`adoption scenario <ECM diffusion>` and sub-folders for the results measured against energy savings, avoided |CO2| emissions, and cost savings. Within each of these sub-folders, the three figure types each correspond to one of three PDF files.

For the first of the three figure types, the PDF file includes a single plot for each ECM, with the modeling horizon (years 2009 through 2040) on the x-axis and the parameter indicated in the PDF file name on the y-axis -- energy, cost, or |CO2| emissions. A legend is included at the end of the figures on the last page of each PDF.

The y-axis scale for each figure is adjusted automatically to be appropriate for the data shown. Care should be taken when inspecting two adjacent plots, since what look like a similar energy or |CO2| savings values at a glance, might in fact be quite different depending on the y-axes. The y-axis markings must be used to determine the magnitudes in the plots and to compare between plots.

Interpretation of these figures is facilitated with relevant comparisons of pairs of lines. 

* Uncompeted Baseline vs. Competed Baseline -- Represents the direct or indirect [#]_ effects of ECM competition on the total baseline market and associated energy, carbon, or cost that can be affected by each ECM. 
* Uncompeted Baseline vs. Uncompeted "Efficient" -- The potential for energy savings, cost savings, and avoided |CO2| emissions from the ECM in the absence of alternative technologies that provide the same services. 
* Competed Baseline vs. Competed "Efficient" -- The potential for energy savings, cost savings, and avoided |CO2| emissions from the ECM when other ECMs could provide equivalent service but with different energy/|CO2|/cost tradeoffs.

In addition to these comparisons, the uncertainty range (if applicable) around "efficient" results and the effect of uncertainty on competing ECMs should be examined.

.. _tech-potential-energy-plot-example:
.. figure:: images/total_energy_TP.*

   Primary energy use baselines, and improvements with the adoption of two ECMs – RTU Control Retrofit and Reduce Infiltration – are shown for the range of years in the model. The data shown are from the :ref:`technical potential <ECM diffusion>` adoption scenario, which is reflected in the large overnight energy use reductions when the ECM is applied to the baseline market. The data are derived from a model that included many ECMs besides those shown, thus the ECMs’ impacts change under :ref:`competition <ECM-competition>`. Note that for these figures, the primary energy use y-axis scale is different. For the RTU Control Retrofit ECM, the ECM is outcompeted by other commercial cooling ECMs, and its baseline and efficient energy use go to zero. The Reduce Infiltration ECM shows a reduced (but non-zero) baseline after adjusting for competition; this reflects both the direct impact of other demand-side heating and cooling ECMs capturing part of this ECM’s baseline market, as well as the indirect impact of supply-side heating and cooling ECMs reducing the total heating and cooling energy that can be lost through infiltration. Uncertainty in the results after competition arises due to uncertainty present in a competing ECM, but even after adjusting for competition, there are still some energy savings compared to the baseline. Large variations in the baseline in both ECMs prior to the current year are an artifact of NEMS, which is used for the AEO__ projections.

.. __: http://www.eia.gov/forecasts/aeo/

:numref:`tech-potential-energy-plot-example` shows two ECMs plotted with and without competition under the technical potential scenario. For the RTU Control Retrofit ECM, a gap is present between the uncompeted baseline (dark gray) and efficient (light gray) energy use, which indicates the energy savings potential of the ECM when the effects of competition with other ECMs are not considered. Note that in the absence of competition, the efficient case shows the overnight energy savings characteristic of the technical potential scenario. The competed baseline (dark blue) and efficient (light blue) energy are both zero for this ECM, which indicates that the ECM is not competitive with some other ECM that provides cooling for commercial buildings and was included in the same analysis. The up and down variations in the baselines prior to the current year appear in many other ECMs is indicative of adjustments made by EIA in the historical AEO data and should not be a subject of attention.

The Reduce Infiltration ECM similarly shows a gap between the uncompeted baseline and efficient energy use, which again indicates the energy savings potential of this ECM in the absence of competition with other ECMs. As with the RTU Control Retrofit ECM, the baseline and efficient energy use of the Reduce Infiltration ECM are scaled down following competition with other ECMs; these competing ECMs may be demand-side heating and cooling ECMs that directly capture part of the Reduce Infiltration ECM's baseline market, or could be supply-side heating and cooling ECMs that indirectly reduce the total amount of heating and cooling energy that can be lost through infiltration. Competition only slightly affects the Reduce Infiltration ECM’s energy use and energy savings potential. Note that uncertainty also appears in the plot for the Reduce Infiltration ECM, though only for the competed efficient result; this indicates there is uncertainty in a competing ECM, but not in this ECM.

In the second of the three figure types, each file contains the results summarized by :ref:`climate zone <json-climate_zone>`, building class [#]_, and :ref:`end use <json-end_use>`. The x-axis corresponds to the modeling horizon (years 2009 through 2040), and the y-axis corresponds to the parameter (energy, |CO2|, or cost) indicated in the file name. These plots summarize only the results with :ref:`ECM competition <ECM-competition>`. The dotted line on each plot corresponds to the right side y-axis and represents the cumulative results for all the ECMs shown. The line is the same for all three plots within a single PDF.

.. _aggregate-by-end-use-plot-example:
.. figure:: images/Total_Energy_Savings-MAP-Aggregate.*

   In this type of figure, primary energy use reductions are summarized by :ref:`end use <json-end_use>`, :ref:`climate zone <json-climate_zone>`, and building class for the maximum adoption potential scenario. Data are presented for each year in the modeling time horizon. Solid lines represent reductions in energy use for the year plotted, while the dotted black line corresponds to total cumulative avoided energy use up to the given year. These plots use the left and right side y-axes for annual and cumulative results, respectively. Similar figures are also generated to display |CO2| and energy cost results by end use, climate zone, and building class groupings. Each figure has a version that corresponds to one of the two :ref:`adoption scenarios <ECM diffusion>`, technical potential and maximum adoption potential. For this plot type, while the data are shown as lines instead of points, the line segments between each year are interpolated and do not represent actual model data.

:numref:`aggregate-by-end-use-plot-example` summarizes annual primary energy use reductions from the introduction of the ECMs included in a Scout analysis under the maximum adoption potential scenario. In general, these figures can be used to see at a glance the contributions from various end uses to overall results, as well as the distribution of results among building types and climate zones. While some end uses might appear to contribute more to the total annual or cumulative energy savings (or avoided |CO2| emissions or cost savings), the baseline energy use is different for each end use, and some end uses might appear to contribute more to the savings in part because their baseline energy use is greater. Similarly, while some building types or climate zones might show greater energy savings (or improvement in other metrics) than others, they may also have significantly different baseline energy use. In addition, these data are highly sensitive to the ECMs that are included in the analysis. While an introductory set of ECMs are provided with Scout, if your own additions to the ECMs are limited to a single end use, for example, it is reasonable to expect that greater reductions in energy use will come from that end use than other end uses.

In :numref:`aggregate-by-end-use-plot-example`, the spike in total energy savings and annual lighting energy savings from 2011 to 2012 comes from the introduction of a lighting ECM where the baseline lighting technology has a lifetime of less than one year. As a result, the entire stock of lighting equipment turns over in 2012. The replacement technology described by the ECM has a longer lifetime, thus the savings in 2013 are necessarily lower than 2012 since the newly replaced bulbs are still in service. For most end uses, ECMs and the baseline technologies have similar lifetimes, and thus as the ECMs diffuse into the equipment and building stock, the total savings from year to year will level-out, only yielding further increases as more efficient prospective ECMs become available in later years. The general pattern of concomitant increases in energy efficiency and bulb life for new lighting technologies means that as these technologies enter the market, the potential for energy savings in subsequent years is reduced by the dramatic reductions in lighting stock turnover.

In the version of the :numref:`aggregate-by-end-use-plot-example` that corresponds to the technical potential scenario, there are sharp increases in the energy savings in some end uses. These increases come from several key ECMs that have enough of a disparity in energy efficiency from the baseline technologies to yield dramatic overnight savings. These rapid increases are a result of the ECM adoption assumptions in the technical potential scenario, and should be viewed as an extreme upper bound on the potential for primary energy use reductions in the end uses, climate zones, and building classes shown.

For the third figure type, ECM cost-effectiveness is assessed using four financial metrics. One plot is generated for each of the financial metrics -- internal rate of return (IRR), simple payback, cost of conserved energy (CCE), and cost of conserved |CO2| (CCC). In each case, the applicable financial metric is on the y-axis, and energy savings, avoided |CO2| emissions, or energy cost savings are plotted on the x-axis. All of the data shown are drawn from a single year, which is indicated in the x-axis label.

.. _financial-metrics-example-plot:
.. figure:: images/Cost_Effective_Energy_Savings-MAP.*

   The four primary financial metrics calculated in Scout for each ECM, internal rate of return, simple payback, cost of conserved energy, and cost of conserved |CO2| are plotted on a single page to show the cost-effectiveness of all of the ECMs at a glance. These figures show data from the maximum adoption potential scenario. A similar set of figures is generated for the technical potential adoption scenario. Both figures show only data drawn from the results that include ECM competition. Each ECM is indicated by a single point in each plot area, and the shape, fill color, and outline color indicate the building type(s), end use(s), and climate zone(s), respectively, that apply to that ECM. The dotted horizontal line in each plot indicates a threshold or target above or below which the ECM is not cost-effective (based on that metric); this cost-effective region is highlighted in gray. The total cost-effective energy savings, avoided |CO2| emissions, or energy cost savings under each threshold value are reported at the top of each plot area. The five cost-effective ECMs with the greatest energy, |CO2|, or energy cost impacts are listed in the top left of each plot area.

:numref:`financial-metrics-example-plot` shows plots of the financial metrics calculated for each ECM. All of the metrics are plotted against energy savings results from the maximum adoption potential scenario for the year 2030. The data shown include the effects of :ref:`ECM competition <ECM-competition>`. The various financial metrics can be used to evaluate the potential cost-effectiveness of the ECMs included in an analysis. The relevance of each metric in evaluating ECM cost-effectiveness will depend on the various economic and non-economic (e.g., policy) factors that might impact the particular individual or organization using these results.

On each plot, a dotted horizontal line represents a target threshold for the given financial metric, and the cost-effective region above or below each threshold is highlighted in gray. Total cost-effective energy savings, avoided |CO2| emissions, or energy cost savings are reported in the top left corner of each plot area. The thresholds used are positive IRR, five year payback, the U.S. average retail electricity price, and the `Social Cost of Carbon`_ for IRR, simple payback, CCE, and CCC respectively. Above or below those lines, depending on whether higher or lower values are more favorable for that metric, the ECM might not be cost-effective in its target market. Acceptable thresholds for each financial metric vary by building owner and type, thus each threshold shown is an indication of the range around which an ECM might not be cost-effective.

In :numref:`financial-metrics-example-plot`, the ENERGY STAR Electric Storage Water Heating and prospective Occupant-Centered Controls ECMs generally show the largest cost-effective energy savings impacts relative to other ECMs. Note that the latter ECM uses performance and cost input values based on cost effective 2020 targets developed by the DOE Building Technologies Office; accordingly, it should look favorable in this plot relative to the other ECMs, which generally represent technologies that are currently commercially available. On average across all ECMs and financial metrics in :numref:`financial-metrics-example-plot`, about 3 quads of cost effective energy savings are achieved.

The shape, fill color, and outline color of each point indicate the applicable building type(s), end use(s), and climate zone(s) for each ECM shown on the plot. Comparing the relative locations of these various points might suggest where there are categories that are more generally cost-effective than others. In :numref:`financial-metrics-example-plot`, for example, the top five ECMs are predominantly of the residential building type across all financial metrics; moreover, HVAC shows up more than any other single end use category in the top five ECMs. As with the second figure type, however, such outcomes must be interpreted in light of the particular set of ECMs that underpin the analysis; in this example, this finding is partly explained by the prevalence of residential HVAC ECMs among the ECMs included in the analysis.

Viewing tabular outputs
~~~~~~~~~~~~~~~~~~~~~~~

The plot generation script in R also produces Excel-formatted files containing summaries of the results. The summary results for each adoption scenario are stored in the corresponding scenario folder within the results/plots directory. The structure of the results in the files corresponding to each scenario is identical. Each file has three tabs, corresponding to energy use, |CO2| emissions, and energy cost results. These results correspond to the data that are shown in the ECM-specific plots, as in :numref:`tech-potential-energy-plot-example`, and the tabular results can be used to create custom visualizations different from those automatically generated with plots.R.

.. tip::
   If you are experienced with R, you can also modify plots.R to tailor the figures to your preferences.

On each tab, the first six columns provide information about the ECM and the type of data reported in each row. The first column contains the name of the ECM for the data in each row and the fourth through sixth columns provide details regarding the climate zones, building classes, and end uses that apply to each ECM. The second column indicates the type of data in each row, and the third column provides the units of the values in the row. Each column beyond the sixth column corresponds to a year in the simulation, with the year for each column indicated in the header (i.e., first) row. 

For a given set of results data on a single tab, each ECM in the simulation appears in four rows. These four rows correspond to the uncompeted and competed baseline results, as well as the ("efficient") results with the ECM applied, again with and without competition. For each ECM, these rows correspond to the four primary lines that appear in the ECM-specific results figures, as in :numref:`tech-potential-energy-plot-example`. There are also two rows that report the sum of all ECMs for both the competed baseline and efficient cases. These rows are distinguished by not having any detail information in the fourth through sixth columns.

.. note::
   For each ECM in the results, in addition to the *total* energy use, |CO2| emissions, and energy cost results contained in the Excel files, the ecm_results.json file includes those results broken out by each of the applicable baseline market parameters -- |baseline-market| -- that apply to each ECM. These results breakdowns are provided for both the baseline and efficient cases (without and with the ECM applied, respectively).

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
.. [#] The size parameter specifies the number of samples to draw from the specified distribution. The number of samples is preset to be the same for all ECMs to ensure consistency. 
.. [#] If the warning "there is no package called 'rjson'" appears in the R Console window, try running the script again. If the warning is repeated, the rjson package should be added manually. From the Packages menu, (Windows) select Install package(s)... or (Mac) from the Packages & Data menu, select Package Installer and click the Get List button in the Package Installer window. If prompted, select a repository from which to download packages. On Windows, select "rjson" from the list of packages that appears. On a Mac, search in the list for "rjson," click the "Install Dependencies" checkbox, and click the "Install Selected" button. When installation is complete, close the Package Installer window.
.. [#] When ECMs are competed against each other, demand-side heating and cooling ECMs that improve the performance of the building envelope reduce the energy required to meet heating and cooling needs (supply-side energy), and that reduction in energy requirements for heating and cooling is reflected in a reduced baseline for supply-side heating and cooling ECMs. At the same time, supply-side heating and cooling ECMs that are more efficient reduce the energy used to provide heating and cooling services, thus reducing the baseline energy for demand-side ECMs. The description of :ref:`ECM competition <ecm-competition>` in Step 3 of the analysis approach section includes further details regarding supply-side and demand-side heating and cooling energy use balancing.
.. [#] Building class corresponds to the four combinations of :ref:`building type <json-bldg_type>` and :ref:`structure type <json-structure_type>`.
