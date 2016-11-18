.. Substitutions
.. |CO2| replace:: CO\ :sub:`2`

.. _tutorials:

Tutorials
=========


.. _tuts-1:

Tutorial 1: Creating and editing ECMs
-------------------------------------

Before beginning this tutorial, it is recommended that you review the :ref:`list of parameters <ecm-contents>` in an ECM definition.

The examples in this tutorial will demonstrate how to write new ECMs so that they will be compliant with all relevant formatting requirements and provide the :ref:`needed information <ecm-contents>` about a technology in the structure expected by the Scout analysis engine. These examples are *not* exhaustive descriptions of all of the detailed options available to specify an ECM. A detailed outline of all of the options and combinations available for an ECM is available in section (add link). In addition, this tutorial includes information about how to :ref:`edit existing ECMs <editing-ecms>` and :ref:`define package ECMs <package-ecms>`.

.. CREATE A SECTION FOR THE DOCUMENTATION THAT OUTLINES EVERY POSSIBLE COMBINATION OF SPECIFICATIONS FOR AN ECM, ESPECIALLY IN TERMS OF SPECIFYING PROBABILITY DISTRIBUTIONS OF VARIOUS TYPES, AND SPECIFYING C/P/L AT VARYING LEVELS OF DETAIL/SPECIFICITY

Reference versions of the new ECMs are provided for download to check one's own work following completion of the examples.

Each new ECM created should be saved in a separate file. To add new or edited ECMs to the analysis, the files should be placed in the "ecm_definitions" directory. Further details regarding where ECM definitions should be saved and how to ensure that they are included in new analyses are included in :ref:`Tutorial 2 <tuts-2>`.

JSON syntax basics
~~~~~~~~~~~~~~~~~~

All of the ECMs for Scout are stored in a JSON_-formatted file. JSON files are human-readable (they appear as plain text) and are structured as (nested) pairs of keys and values, separated by a colon and enclosed with braces. [#]_ ::

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

.. ADD A NOTE EXPLAINING THAT KEY STRINGS MUST MATCH EXACTLY WITH WHAT IS EXPECTED - NO SPACES, NO SWITCHING _ WITH -

We will use these general formatting guidelines to write new ECMs.

.. In this tutorial, we will create two different ECMs. We will begin with an ECM that has a relatively simple cost and performance specification. The second example ECM will demonstrate more complex definitions for cost and performance and employ some optional ECM features. Following these two examples, we recommend reviewing the `ECM database`_ to see further examples of different kinds of ECMs.

.. ECM database:

.. CREATE A KEY PAIR INDEX FOR ECM DEFINITIONS (OR AT LEAST FOR THE BASELINE MARKET DEFINITION)

.. _example-ecm-1:

New ECM 1 – Commercial LED troffers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The required information for defining this ECM will be covered in the same order as the :ref:`list of parameters <ecm-contents>` in the :ref:`analysis-approach` section.

For this example, we will be creating an ECM for LED troffers for commercial buildings. Troffers are square or rectangular light fixtures designed to be used in a modular dropped ceiling grid commonly seen in offices and other commercial spaces.

The finished ECM specification is available to :download:`download </examples/led_troffers.json>` for reference.

To begin, the ECM should be given a short, but descriptive name. Details regarding the characteristics of the technology that will be included elsewhere in the ECM definition, such as the cost, performance, or lifetime, need not be included in the title. The key for the name is simply ``name``. ::

   {"name": "LED Troffers"}

.. note::
   In this tutorial, JSON entries will be shown with leading and trailing ellipses to indicate that there is additional data in the ECM definition that appears before and/or after the text of interest. ::

      {...
       "key_text": "value",
       ...}


Applicable Baseline Market
**************************

The applicable baseline market parameters specify the climate zones, building types, and other elements that define to what portion of energy use the ECM applies. The exact climate zone and building type options are outlined in the :ref:`ecm-baseline_climate-zone` and :ref:`ecm-baseline_building-type` sections of the :ref:`ecm-def-reference`.

LED troffers can be installed in buildings in any climate zone, and apply to all commercial building types. To simplify entry, "all" can be used to specify climate zones (instead of writing a list of all climate zones), and "all," "all residential," or "all commercial" can be used to specify building types. ::

   {...
    "climate_zone": "all",
    "bldg_type": "all commercial",
    ...}

ECMs can apply to only new construction, only retrofits, or all buildings both new and existing. This is specified under the "structure_type" key with the values "new," "retrofit," or "all," respectively. LED troffers can be installed in new construction and retrofits. ::

   {...
    "structure_type": "all",
    ...}

The end use(s) for an ECM are separated into primary end uses, those that are applicable to the technology itself, and secondary end uses, which are those end uses that are affected by changes in the energy use from the ECM. The end use names are the same as the residential__ and commercial__ end uses specified in the AEO, and are listed for convenience in the :ref:`ecm-baseline_end-use` reference section. In the case where there are no secondary end uses affected, the key must still be included, but the value should be set to ``null``. The primary end use for LED troffers is lighting. Changing from fluorescent bulbs typically found in troffers will reduce the heat output from the fixture, thus reducing the cooling load and increasing the heating load for the building. These changes in heating and cooling energy use qualify as secondary end uses. In general, these secondary end uses are handled automatically without being specified and the secondary field value can be set to ``null``. The specific cases where secondary effects are automatically added are outlined in the corresponding section (add link). ::

   {...
    "end_use": {
      "primary": "lighting",
      "secondary": null},
    ...}

.. __: https://www.eia.gov/forecasts/aeo/data/browser/#/?id=4-AEO2016&cases=ref2016~ref_no_cpp&sourcekey=0
.. __: https://www.eia.gov/forecasts/aeo/data/browser/#/?id=5-AEO2016&cases=ref2016~ref_no_cpp&sourcekey=0

Parallel to the structure for the end use data, there must be "primary" and "secondary" keys specifying the fuel type for an ECM. The primary fuel types specified should correspond to the primary end use(s) already specified, and similarly for the secondary fuel types corresponding to those end uses. If no secondary end uses are specified, the secondary fuel type key should have the value ``null``. If multiple fuel types apply for either category, primary or secondary, they can be specified with a list. In the case of LED troffers, electricity is the only relevant primary fuel type. The secondary fuel types will be handled automatically. ::

   {...
    "fuel_type": {
      "primary": "electricity",
      "secondary": null},
    ...}

The technology type specifies whether the ECM applies to the "supply" of service or the "demand" of services. If the ECM affects devices or equipment that use energy directly, the technology type is "supply." If an ECM affects the quantity of heating and/or cooling service required but does not directly modify the efficiency of the heating and/or cooling equipment, the technology type is "demand." For the "heating" and "cooling" end uses, a heat pump ECM is of the "supply" technology type, while an R-8/in rigid insulation board ECM is of the "demand" technology type. Again there are "primary" and "secondary" keys, which should be used to indicate the technology type for the respective end uses. If there are no secondary end uses or if they will be defined automatically, the secondary technology type value should be set to ``null``. LED troffers are a technology that improves the efficiency of lighting technologies, thus it is of the supply technology type. ::

   {...
    "technology_type": {
      "primary": "supply",
      "secondary": null},
    ...}

The technology field drills down further into the specific technologies or device types that apply to the primary and secondary end uses for the ECM. The specific technology names are different for supply-side and demand-side energy use. The residential__ and commercial__ thermal load components are the technology names for the "demand" technology type. Technology names for the "supply" technology type generally correspond to major equipment types used in the AEO_ [#]_. All of the technology names are listed by building sector (residential or commercial) and technology type in the :ref:`relevant section <ecm-baseline_technology>` of the :ref:`ecm-def-reference`.

In some cases, an ECM might be able to replace all of the currently used technologies for its end use and fuel type. For example, a highly efficient thermoelastic heat pump might be able to replace all current electric heating and cooling technologies. If the end uses have been specified as "heating" and "cooling" and the fuel type as "electricity," then the primary technologies can be specified simply with "all." A technology list can also be specified with a mix of shorthand end use references (e.g., "all lighting") and specific technology names, such as ``["all heating", "F28T8 HE w/ OS", "F28T8 HE w/ SR"]``.

For this example, LED troffers are likely to replace linear fluorescent bulbs, the typical bulb type for troffers. There are many lighting types for commercial buildings, but we will include all of the lighting types that are specified as F\_\_T\_\_, including those with additional modifying text. ::

   {...
    "technology": {
      "primary": ["F28T8 HE w/ OS", "F28T8 HE w/ SR", "F96T8", "F96T12 mag", "F96T8 HE", "F28T8 HE w/ OS & SR", "F28T5", "F28T8 HE", "F32T8", "F96T12 ES mag", "F34T12", "T8 F32 EEMag (e)"],
      "secondary": null},
    ...}

.. __: https://github.com/trynthink/scout/blob/master/1999%20Residential%20heating%20and%20cooling%20loads%20component%20analysis.pdf
.. __: https://github.com/trynthink/scout/blob/master/1999%20Commercial%20heating%20and%20cooling%20loads%20component%20analysis.pdf
.. _AEO: https://www.eia.gov/analysis/studies/buildings/equipcosts/pdf/full.pdf


Market Entry and Exit Year
**************************

The market entry year represents the year the technology is or will be available for purchase and installation. Some ECMs might be prospective, representing technologies not currently available. Others might represent technologies currently commercially available. The market entry year should reflect the current status of the technology described in the ECM. Similarly, the market exit year represents the year the technology is expected to be withdrawn from the market. The market entry year and exit year both require source information. As much as is practicable, a :ref:`high quality<ecm-sources>` reference should be used for both values. If no source is available, such as for a technology that is still quite far from commercialization, a brief explanatory note should be provided for the market entry year source. If it is anticipated that the product will not be withdrawn from the market prior to the end of the model :ref:`time horizon <2010-2040 projection>`, the exit year and source should be given as ``null``.

LED troffers are currently commercially available with a range of performance, cost, and lifetime ratings. It is likely that while LED troffers will not, in general, exit the market within the model :ref:`time horizon <2010-2040 projection>`, LED troffers with cost and performance similar to this ECM are not likely to remain competitive through 2040. It will, however, be left to the analysis to determine whether more advanced lighting products enter the market and supplant this ECM, rather than specifying a market exit year. ::

   {...
    "market_entry_year": 2015,
    "market_entry_year_source": {
      "notes": "",
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


Performance
***********

The energy performance or efficiency of the ECM must be specified in three parts: the quantitative performance (only the value(s)), the units of the performance value(s) provided, and source(s) that support the indicated performance information. There are fields to specify the energy savings associated with secondary effects. If applicable, the performance value(s) should be reported in units of "relative savings (constant)," denoting a reduction in energy use *relative* to the baseline, with a *constant* percentage improvement, even as the baseline improves over time. The fields for secondary effects should be set to ``null`` if they do not apply or will be filled in automatically.

The units specified are expected to be consistent with the units for each end use outlined in the :ref:`ECM Definition Reference <ecm-performance-units>` section.

The source(s) for the performance data should be credible sources, such as :ref:`those outlined <ecm-sources>` in the :ref:`analysis-approach` section. The source information should be provided using only the fields shown in the example.

If appropriate, the performance can be specified with a different value for each end use, climate zone, building type, or building vintage that is in the applicable baseline market. Source information should be provided as appropriate for the level of detail used in the performance specification. If each of the performance data come from different sources, each source should be specified separately using the same nested dict structure. It is also acceptable to provide a single source if all of the performance data come from that source. This detailed performance specification approach is demonstrated in the :ref:`second ECM example <example-ecm-2>`.

For the example of LED troffers, all lighting data should be provided in the units of lumens per Watt (denoted "lm/W"). LED troffers performance information is based on the `High Efficiency Troffer Performance Specification`_. ::

   {...
    "energy_efficiency": {
      "primary": 120,
      "secondary": null},
    "energy_efficiency_units": {
      "primary": "lm/W",
      "secondary": null},
    "energy_efficiency_source": {
      "notes": "Augmented by data from the DesignLights Consortium Qualified Products List (https://www.designlights.org/qpl).",
      "source_data": [{
         "title": "High Efficiency Troffer Performance Specification, Version 5.0",
         "author": "",
         "organization": "U.S. Department of Energy",
         "year": 2015,
         "pages": null,
         "URL": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf"}]},
    ...}


Installed Cost
**************

The absolute installed cost must be specified for the ECM, including the cost value, units, and reference source. The cost units should be specified according to :ref:`the relevant section <ecm-installed-cost-units>` of the :ref:`ecm-def-reference`, noting that residential and commercial equipment have different units, and that sensors and controls ECMs also have different units from other equipment types.

If applicable to the ECM, separate cost values can be provided for residential and commercial building types. Units should match the level of specificity in the values, and source information should be included for all values articulated, if separate sources are used for different building types.

For LED troffers, costs are estimated based on an assumption of a single fixture providing 4800 lm, with installation requiring two hours and two people at a fully-burdened cost of $100/person/hr. ::

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

The lifetime of the ECM, or the expected amount of time that the ECM technology will last before requiring replacement, is specified using a structure identical to the installed cost. Again, the lifetime value, units, and source information must be specified for the corresponding keys. The units should always be in years, ideally as integer values greater than 0. LED troffers have rated lifetimes on the order of 50,000 hours, though the `High Efficiency Troffer Performance Specification`_ requires a minimum lifetime of 68,000 hours. The values for lighting lifetimes should be based on assumptions regarding actual use conditions (i.e., number of hours per day), and the "notes" value in the source specification should include that assumption. The LED troffers in this example are assumed to operate 12 hours per day. ::

   {...
    "product_lifetime": 15,
    "product_lifetime_units": "years",
    "product_lifetime_source": {
      "notes": "Calculated from 68,000 hrs assuming 12 hr/day operation.",
      "source_data": [{
         "title": "High Efficiency Troffer Performance Specification, Version 5.0",
         "author": "",
         "organization": "U.S. Department of Energy",
         "year": 2015,
         "pages": null,
         "URL": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf"}]},
    ...}

.. _High Efficiency Troffer Performance Specification: https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf


Other Fields
************

ECMs may directly replace the service of an existing device already installed (and the default product installed in new construction), such as an ECM for an electric cold-climate heat pump, which would replace existing electric heating systems. Alternately, ECMs may enhance the performance of an existing technology, such as a window film that improves the solar heat gain coefficient of an existing window, or an HVAC controls system that improves the operation of an existing HVAC system. The particular type for the ECM must be specified as either ``"full service"`` or ``"add-on"``, respectively. LED troffers would replace existing troffers that use linear fluorescent bulbs, providing an equivalent building service (lighting) using less energy. The LED troffers ECM is thus denoted as "full service." ::

   {...
    "measure_type": "full service",
    ...}

Two keys are provided for ECM authors to provide additional details about the measure specified. The "_description" field should include a one to two sentence description of the ECM, including additional references for further details regarding the technology if it is especially novel or unusual. The "_notes" field can be used for explanatory notes regarding the technologies that are expected to be replaced by the ECM and any notable assumptions made in the specification of the ECM not captured in another field. ::

   {...
    "_description": "LED troffers for commercial modular dropped ceiling grids that are a replacement for the entire troffer luminaire for linear fluorescent bulbs, not a retrofit kit or linear LED bulbs that slot into existing troffers.",
    "_notes": "Energy performance is specified for the luminaire, not the base lamp.",
    ...}

Basic contact information regarding the author of a new ECM should be added to the fields under the "_added_by" key. ::

   {...
    "_added_by": {
      "name": "Carmen Sandiego",
      "organization": "Super Appliances, Inc.",
      "email": "carmen.sandiego@superappliances.com",
      "timestamp": "2015-07-14 11:49:57 UTC"},
    ...}

.. Date and time of New Horizons flyby of Pluto

.. _example-ecm-1-optional-entries:

"Optional" Entries
******************

These "optional" fields must be included in the ECM definition, but can be set to a value of ``null`` if they are not relevant to the ECM.

If the ECM applies to only a portion of the energy use in an applicable baseline market, even after specifying the particular end use, fuel type, and technologies that are relevant, a scaling value can be added to the ECM definition to specify what fraction of the applicable baseline market is truly applicable to that ECM. A source must be provided for the scaling fraction following the same general format used for other ECM data, but with an additional "fraction_derivation" key. The fraction derivation is a string that explains how the scaling value(s) were calculated. The source information is especially important for these data, and must be fully specified or the ECM will not be included in the analysis. Further detail regarding scaling fractions can be found in the :ref:`second ECM example <example-ecm-2-optional-entries>`.

Multiple different scaling fraction values can be specified if the ECM applies to multiple building types or climate zones. The sources should be provided with equal specificity if multiple sources were required to obtain the various scaling fraction values.

When creating a new measure, it is important to carefully specify the applicable baseline market to avoid the use of the market scaling fraction parameter, if at all possible. If the scaling fraction is not used, the value and the source should be set to ``null``.

No market scaling fraction is required for the LED troffers ECM. ::

   {...
    "market_scaling_fractions": null,
    "market_scaling_fractions_source": null,
    ...}

If the ECM is intended to supplant technologies with multiple fuel types, the fuel type of the ECM itself should be specified. For example, if an electric heat pump water heater is expected to replace existing electric *and* natural gas water heaters, the "fuel_switch_to" option should be set to the fuel type of the ECM itself: "electricity." If fuel switching is indicated, the applicable baseline market should include the fuel types and technologies that can be supplanted by the ECM. All lighting uses only electricity, so this option is not relevant to LED troffers. ::

   {...
    "fuel_switch_to": null,
     ...}

.. note::
   If a value other than ``null`` is provided for the fuel type of the ECM, the primary fuel types selected for the applicable baseline market should include all of the fuel types that can be switched away from when employing the ECM in a building.

When updating an existing ECM, the identifying information for the contributor should be provided in the "_updated_by" field instead of the "_added_by" field. ::

   {...
    "_updated_by": {
      "name": null,
      "organization": null,
      "email": null,
      "timestamp": null},
    ...}


.. _example-ecm-2:

New ECM 2 – Thermoelastic heat pump
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This ECM describes thermoelastic heat pump technology for residential and commercial applications. Thermoelastic heating and cooling uses a shape memory (i.e., returns to its original shape when no force is applied) metal alloy that absorbs or releases heat when deformed (stretched or compressed). ::

   {"name": "Thermoelastic Heat Pump",
    ...}

The finished ECM specification is available to :download:`download </examples/thermoelastic_hp.json>` for reference.

The discussion in this example will generally focus on the specific features of this ECM. A more introductory discussion of the features of an ECM definition can be found in the :ref:`first example <example-ecm-1>`.


Applicable Baseline Market
**************************

The applicable baseline market parameters specify the climate zones, building types, and other elements that define to what portion of energy use the ECM applies.

The thermoelastic heat pump conceived for this example can be used in residential and commercial buildings, but will have different performance specifications for each building sector. As in the first ECM example, "all" can be used to simplify the specification instead of listing each building type and climate zone explicitly. The structure type (new or retrofit) can also be specified using the "all" shortcut. ::

   {...
    "climate_zone": "all",
    "bldg_type": "all",
    "structure_type": "all",
    ...}

The end use(s) specified for an ECM can be given as a list, if appropriate. Again, primary end uses apply to the technology itself, while secondary end uses are those affected by changes in energy use as a result of the ECM. In many cases, the secondary end uses are treated automatically based on the primary end uses specified (add link). Using the end use names specified for residential__ and commercial__ buildings in the AEO, the thermoelastic heat pump ECM is specified with both "heating" and "cooling" primary end uses in a list. Secondary end uses are not applicable in this case, thus the value is set to ``null``. ECMs that affect supply-side heating and cooling require updating of the energy use associated with demand-side heating and cooling, but this adjustment process is done automatically (add link). ::

   {...
    "end_use": {
      "primary": ["heating", "cooling"],
      "secondary": null},
    ...}

.. __: https://www.eia.gov/forecasts/aeo/data/browser/#/?id=4-AEO2016&cases=ref2016~ref_no_cpp&sourcekey=0
.. __: https://www.eia.gov/forecasts/aeo/data/browser/#/?id=5-AEO2016&cases=ref2016~ref_no_cpp&sourcekey=0

Parallel to the structure for the end use data, there must be "primary" and "secondary" keys specifying the fuel type for an ECM. The primary and secondary fuel types correspond to the end uses listed under the same keys. As with end uses, fuel types can be specified with a list. Thermoelastic heat pumps use electricity to deform the shape memory metal and absorb or release heat. ::

   {...
    "fuel_type": {
      "primary": "electricity",
      "secondary": null},
    ...}

The technology type specifies whether the ECM applies to the "supply" of service or the "demand" of services. If the ECM affects devices or equipment that use energy directly, the technology type is "supply." If an ECM affects the quantity of heating and/or cooling service required but does not directly modify the efficiency of the heating and/or cooling equipment, the technology type is "demand." For the "heating" and "cooling" end uses, a heat pump ECM is of the "supply" technology type, while an R-8/in rigid insulation board ECM is of the "demand" technology type. Thermoelastic heat pumps are a "supply" technology. ::

   {...
    "technology_type": {
      "primary": "supply",
      "secondary": null},
    ...}

The technology field lists the specific technologies or device types that can be replaced by the technology described by the ECM. In some cases, an ECM might be able to replace the full range of incumbent technologies in its end use categories, while in others, only specific technologies might be subject to replacement. There are shortcut technology names available for each end use (e.g., "all heating" or "all lighting") and "all" can be used to indicate all technologies for the end uses specified for the ECM. A highly efficient thermoelastic heat pump, for the purposes of this ECM, can replace other similar air-source heat pump technologies and central AC or rooftop AC systems. ::

   {...
    "technology": {
      "primary": ["central AC", "ASHP", "rooftop_ASHP-heat", "rooftop_ASHP-cool", "rooftop_AC"],
      "secondary": null},
    ...}


Market Entry and Exit Year
**************************

The market entry and exit year represent the first and last year the technology described by the ECM is expected to be available. If the ECM will have a lower installed cost or improved performance after its initial market entry, another ECM should be created that reflects the improved version of the product. Thermoelastic heat pumps are a technology currently under development that might be available in future years. A market entry year of 2020 is an estimate, since the development path of the technology is unknown. This uncertainty is indicated in the note provided for the entry year source. As with the LED troffers example, the market exit year is not specified, not because the particular technology described in this ECM will necessarily be available through the end of the model :ref:`time horizon <2010-2040 projection>`, but because it is left to the model to determine whether the technology is competitive with later entrants. ::

   {...
    "market_entry_year": 2020,
    "market_entry_year_source": {
      "notes": "Market entry year is based on the low Technology Readiness Level of the technology at the time the ECM was added.",
      "source_data": null},
    "market_exit_year": null,
    "market_exit_year_source": "NA",
    "market_scaling_fractions": null,
    "market_scaling_fractions_source": "NA",
    ...}


Performance
***********

.. ARE THERE MORE GENERAL COMMENTS TO BE MADE ABOUT THE ORDER IN WHICH THE ENERGY EFFICIENCY SUB-FIELDS MUST BE SPECIFIED?
.. ADD MORE DETAIL ABOUT WHERE ENERGYPLUS FILES COME FROM; WHAT SPECIFIC FILE FROM THE SIMULATION IS REQUIRED

Each ECM definition includes quantitative energy efficiency or energy performance values and the units and source information for those values. Each of these parameters is specified in a separate field. Both the energy efficiency and units should have second level keys for primary and secondary effects from the ECM. Performance data should be derived from :ref:`credible sources <ecm-sources>` and the units must be consistent with those outlined in the :ref:`ECM Definition Reference <ecm-performance-units>` section.

Performance values can be specified with different values by end use, climate zone, building type, or building vintage. In addition, the performance values for commercial buildings can be specified with data from an :ref:`EnergyPlus simulation <analysis-step-2-energyplus>`. The thermoelastic heat pump ECM applies to both residential and commercial buildings, and EnergyPlus simulation results will be used to specify the performance for commercial buildings. Since both the energy efficiency and units data require "primary" and "secondary" keys, the residential and commercial data should be specified under those keys using the simplified building type keys "all residential" and "all commercial."

The EnergyPlus data file should be placed in the directory "energyplus_data" and the file name should be given as the value for the appropriate key. When EnergyPlus data are being used, the units should always be "relative savings (constant)." Using an EnergyPlus data file disables the automatic calculation of the secondary effects of an ECM because these secondary effects should be captured in the EnergyPlus simulation results. If secondary end uses apply to the ECM and EnergyPlus data are used to specify the performance, all of the *secondary* end use, fuel type, and other baseline market parameters must be specified for the performance. If no secondary effects apply, the "secondary" key for performance should be specified as ``null`` similar to other unused fields in the ECM.

The source(s) for the performance data should be credible sources, such as :ref:`those outlined <ecm-sources>` in the :ref:`analysis-approach` section. The source information should be provided using only the fields shown in the example. The pages where the data can be found in the source can be provided as a single number or as a list of two numbers, e.g., [93, 95], if the data are spread across multiple pages. If page numbers are not applicable, the field should have the value ``null``. ::

   {...
    "energy_efficiency": {
      "primary": {
         "all residential": 6,
         "all commercial": {"EnergyPlus file": "thermoelastic_heat_pumps.csv"}},
      "secondary": null},
    "energy_efficiency_units": {
      "primary": {
         "all residential": "COP",
         "all commercial": "relative savings (constant)"},
      "secondary": null},
    "energy_efficiency_source": {
      "notes": null,
      "source_data":[{
         "title": "Energy Savings Potential and RD&D Opportunities for Non-Vapor Compression HVAC Technologies",
         "author": "Navigant Consulting",
         "organization": "Navigant Consulting",
         "year": 2014,
         "pages": 107,
         "URL": "http://energy.gov/sites/prod/files/2014/03/f12/Non-Vapor%20Compression%20HVAC%20Report.pdf"}]},
    ...}


Installed Cost
**************

The installed cost is specified in a structure similar to the energy performance. The cost units must match those indicated in the :ref:`ECM Definition Reference <ecm-installed-cost-units>` section. For the thermoelastic heat pump ECM, the cost should be specified separately for residential and commercial buildings since the expected installed cost is different and the heating and cooling cost units are different.

While the installed cost data are specified separately for residential and commercial buildings, the data come from the same source, but on different pages. The pages information can thus be specified with separate keys for "all residential" and "all commercial," paralleling the structure for the installed cost and units data. ::

   {...
    "installed_cost": {
      "all residential": 5300,
      "all commercial": 283},
    "cost_units": {
      "all residential": "2015$/unit",
      "all commercial": "2015$/kBtu/h cooling"},
   "installed_cost_source": {
      "notes": "Numbers based on 'High' case and installed costs for existing/retrofit scenario.",
      "source_data": [{
         "title": "Updated Buildings Sector Appliance and Equipment Costs and Efficiencies",
         "author": "U.S. Energy Information Administration (EIA)",
         "organization": "U.S. Energy Information Administration (EIA)",
         "year": 2015,
         "pages": {
            "all residential": 37,
            "all commercial": 103},
         "URL": "https://www.eia.gov/analysis/studies/buildings/equipcosts/pdf/full.pdf"}]},
    ...}


Lifetime
********

The lifetime of the ECM, or the expected amount of time that the ECM technology will last before requiring replacement, is specified using a structure identical to the installed cost. Again, the lifetime value, units, and source information must be specified for the corresponding keys. The units should always be in years, ideally as integer values greater than 0. Since thermoelastic heat pumps are not yet commercially available, the lifetime is estimated based on the range of lifetimes for central AC equipment given in the EIA AEO data for residential buildings. This assumption is described in the "notes" section of the source information. ::

   {...
    "product_lifetime": 14,
    "product_lifetime_units": "years",
    "product_lifetime_source": {
      "notes": "Median of minimum and maximum lifetime listed for residential central AC equipment in 'rsclass.txt'.",
      "source_data": [{
         "title": "Residential Demand Module of the National Energy Modeling System: Model Documentation 2014", 
         "author": "U.S. Energy Information Administration (EIA)",
         "organization": "U.S. Energy Information Administration (EIA)",
         "year": 2014,
         "pages": 28,
         "URL": "https://www.eia.gov/forecasts/aeo/nems/documentation/residential/pdf/m067(2014).pdf"}]},
    ...}


Other Fields
************

Thermoelectric heat pumps would replace the service of existing heating and/or cooling systems, such as central AC systems, rooftop units (RTUs), or traditional vapor-compression cycle air-source heat pumps, thus this is a "full service" type ECM. Other ECMs, like sensors and controls, that augment the performance of heating and cooling, lighting, or other building system(s) are considered "add-on" type ECMs. ::

   {...
    "measure_type": "full service",
    ...}

Two keys are provided for ECM authors to provide additional details about the measure specified. The "_description" field describes briefly the technology or product described by the ECM, and the "_notes" field includes any explanatory notes regarding the technologies that the ECM can replace or any other notable assumptions regarding the ECM that are not already captured elsewhere in the definition. ::

   "_description": "A heat pump that uses shape memory alloy (SMA) to absorb heat from, or reject heat to, the surroundings as the SMA is elongated or compressed.",
   "_notes": "Assumed to be a drop-in replacement for existing residential and commercial electric heating/cooling systems.",

Basic contact information regarding the author of a new ECM should be added to the fields under the "_added_by" key. ::

   {...
    "_added_by": {
      "name": "Elaine Fairchilde",
      "organization": "Make-Believe Engineering",
      "email": "fairchildee@mb-engineering.com",
      "timestamp": "2011-07-08 15:29:17 UTC"},
    ...}

.. Launch time of STS-135, final NASA Space Shuttle mission

There is also an "_updated_by" key that follows the same structure as "_added_by" but should be left blank if the ECM is new. ::

   {...
    "_updated_by": {
      "name": null,
      "organization": null,
      "email": null,
      "timestamp": null},
    ...}


.. _example-ecm-2-optional-entries:

"Optional" Entries
******************

In addition to the entries already presented that are expected in any new ECM definition, there are several additional fields that must be included, but can be specified as ``null`` or used to further customize the ECM.

If the ECM is to include fuel switching, the fuel type of the ECM itself would be specified under the "fuel_switch_to" key. The fuel type strings used should match those used in the fuel type in the applicable baseline market. Though it would be possible to include fuel switching in the definition for thermoelastic heat pumps, it is being excluded in this case. If it were in use, the value would be "electricity." ::

   {...
    "fuel_switch_to": null,
    ...}

After using the "technology" keys to specify the technologies that an ECM can replace, it might be appropriate to specify a value that further reduces the size of the applicable baseline market accessed by an ECM. For thermoelastic heat pumps in residential buildings, the heat pump can only replace the energy use of the entire heating and cooling system if it is either a) already a heat pump system or b) has central AC and an electric heating system of some type. To restrict the ECM to only the portion of homes that have central AC and electric heating, a scaling fraction is calculated using EIA data and applied specifically to the "central AC" portion of the applicable baseline market.

Since the scaling fraction is not derived from the EIA data used to provide a common baseline across all ECMs in Scout, it is especially important that the source information be correct and complete. When reading the ECM, if a scaling fraction is specified, the source fields are reviewed to ensure that either a) a "title," "author," "organization," and "year" are specified or b) a URL from an acceptable source [#]_ is provided. Additionally, the "fraction_derivation" field, which should include an explanation of how the fraction provided was calculated, must also be specified. If any of these required fields are missing, the ECM will not be :ref:`prepared for analysis <tuts-2>`. Always ensure that the information in the source, including the "fraction_derivation" is sufficiently detailed that the scaling fraction can be re-derived. ::

   {...
    "market_scaling_fractions": {"central AC": 0.356},
    "market_scaling_fractions_source": {
      "central AC": {
         "title": "RECS 2009",
         "author": "U.S. Energy Information Administration (EIA)",
         "organization": "U.S. Energy Information Administration (EIA)",
         "year": "2009",
         "pages": null,
         "URL": "https://www.eia.gov/consumption/residential/data/2009/index.cfm?view=microdata",
         "fraction_derivation": "14,942,604 total residential cooled sq.ft. filtered for electric heating"}},
    ...}

Additional discussion regarding the use of the market scaling fraction can be found in the :ref:`first example ECM <example-ecm-1-optional-entries>`.


.. _editing-ecms:

Editing existing ECMs
~~~~~~~~~~~~~~~~~~~~~

All of the ECM definitions are stored in the "ecm_definitions" folder. To edit any of the existing ECMs, open that folder and then open the JSON file for the ECM of interest. Make any desired changes, save, and close the edited file. Like new ECMs, all edited ECMs must be prepared following :ref:`Tutorial 2 <tuts-2>`.

Making changes to the existing ECMs will necessarily overwrite previous versions of those ECMs. If both the original and revised version of an ECM are desired for subsequent analysis, make a copy of the original JSON file (copy and paste the file in the same directory) and rename the copied JSON file with an informative differentiating name. When revising the copied JSON file with the new desired parameters, take care to ensure that the ECM name is updated as well, as no two ECMs can share the same file name or name given in the JSON.


.. _package-ecms:

Creating and editing package ECMs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Package ECMs are not actually unique ECMs, rather, they are combinations of existing ECMs specified by the user. Existing ECMs can be included in multiple different packages; there is no limit to the number of packages to which a single ECM may be added.

.. ADD EXPLANATION OF HOW TO SPECIFY ENERGY COST REDUCTIONS OR OTHER CHANGES APPLICABLE TO PACKAGE ECMs

Package ECMs are specified in the "package_ecms.json" file, located in the "ecm_definitions" folder. Within that JSON file, each ECM package should be specified with a unique name as the key, and a list of ECM names separated by commas as the corresponding value. The individual ECM names should match exactly with the values of the "name" field for each of the ECMs added to the package. All of the intended packages should be specified in the "package_ecms.json" file. For example, the contents of the file should take the following form if there are three desired packages, with three, two, and four ECMs, respectively. ::

   {
      "Name of the first package": ["ECM 1 name", "ECM 2 name", "ECM 3 name"],
      "Name of the second package": ["ECM 4 name", "ECM 1 name"],
      "Name of the third package": ["ECM 5 name", "ECM 3 name", "ECM 6 name", "ECM 2 name"]
   }


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

As each ECM is processed by "ecm_prep.py", the ECM name is printed to the command window within a message indicating that it has been updated successfully. If any exceptions (errors) occur, the module will stop running and the exception will be printed to the command window with some additional information to indicate where the exception occurred within "ecm_prep.py." The error message printed should provide some indication of where the error occurred and in what ECM. This information can be used to narrow the troubleshooting effort.

If "ecm_prep.py" runs successfully, a message with the total runtime will be printed to the console window. The names of the ECMs updated will be added to ``run_setup.json``, a file that indicates which ECMs should be included in :ref:`the analysis <analysis-step-3>`. The total baseline and efficient energy, |CO2|, and cost data for those ECMs that were just added or revised are added to the "competition_data" folder, where there appear separate compressed files for each ECM. High-level summary data for all prepared ECMs are added to the ``ecm_prep.json`` file in the "supporting_data" folder. These files are then used by the ECM competition routine, outlined in :ref:`Tutorial 3 <tuts-3>`.

If exceptions are generated, the text that appears in the command window should indicate the general location or nature of the error. Common causes of errors include extraneous commas at the end of lists, typos in or completely missing keys within an ECM definition, invalid values (for valid keys) in the specification of the applicable baseline market, and units for the installed cost or energy performance that do not match the baseline cost and performance data in the ECM.


.. _tuts-3:

Tutorial 3: Running an analysis
-------------------------------

Once the ECMs have been pre-processed following the steps in :ref:`Tutorial 2 <tuts-2>`, the uncompeted and competed financial metrics and energy, |CO2|, and cost savings can be calculated for each ECM. Competition determines the portion of the applicable baseline market affected by ECMs that have identical or partially overlapping applicable baseline markets. The calculations and ECM competition are performed by ``run.py`` following the outline in :ref:`Step 3 <analysis-step-3>` of the analysis approach section.

If some ECMs should be excluded from a given analysis, these ECMs can be specified in the "run_setup.json" file. All of the existing ECMs should appear in this file under *only* one of two keys, "active" and "inactive." Each of these keys should be followed by a list (enclosed by brackets). If all ECMs are in the active list, the "inactive" value should be an empty list. As new ECMs are added and pre-processed, their names are added to the "active" list. Any ECMs that were edited after being moved to the inactive list will be automatically moved back to the active list. To exclude one or more ECMs from the analysis, simply copy and paste their names from the "active" to the "inactive" list, and reverse the process to restore ECMs that have been excluded. 

.. tip::

   When editing the "run_setup.json" file, be especially careful that there are commas separating each of the ECMs in the "active" and "inactive" lists, and that there is no comma after the last ECM in either list.

To run the uncompeted and competed ECM calculations, open a Terminal window (Mac) or command prompt (Windows) if one is not already open. If you're working in a new command window, navigate to the Scout project directory (shown with the example location ``Documents/projects/scout-run_scheme``). If your command window is already set to that folder/directory, the first line of the commands are not needed. Finally, run "run.py" as a Python script.

**Windows** ::

   cd Documents\projects\scout-run_scheme
   py -3 run.py

**Mac** ::

   cd Documents/projects/scout-run_scheme
   python3 run.py

While executing, "run.py" will print updates to the command window. This text is principally to assure users that the analysis is proceeding apace.

Once complete, the command window will return to an open prompt. The complete competed and uncompeted ECM data are stored in the "ecm_results.json" file located in the "results" folder. While the JSON results file can be reviewed directly, :ref:`Tutorial 4 <tuts-4>` explains how the data can be converted into plots.


.. _tuts-4:

Tutorial 4: Viewing and understanding outputs
---------------------------------------------

Generating/Updating Figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~

The uncompeted and competed ECM results can be converted into graphical form using R. To begin, open R (sometimes called R GUI) from the Applications folder (Mac) or the Start Menu (Windows). Like a Terminal window or command prompt, R will need to be switched to the project directory. The plot generation script can then be run. ::

   setwd('~/Documents/projects/scout-run_scheme')
   source('plots.R')

An additional package is required to run the plot generation R script. Running the script should install the package automatically. If it does not, additional troubleshooting may be required. [#]_

The plot image files can be found in the "plots" folder inside the "results" folder. The plots are separated into folders by :ref:`adoption scenario <ECM diffusion>`.

Interpreting Results Figures
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Each PDF file includes a single plot for each ECM, with the modeling horizon (years 2009 through 2040) on the x-axis and the parameter indicated in the PDF file name on the y-axis -- energy, cost, or |CO2| emissions. A legend is included at the end of the figures on the last page of each PDF.

The y-axis scale for each figure is adjusted automatically to be appropriate for the data shown. Care should be taken when inspecting two adjacent plots, since what looks like a similar energy or |CO2| savings at a glance, might in fact be quite different depending on the y-axes. The y-axis markings must be used to determine the magnitudes in the plots and to compare between plots.

Interpretation of the results figures is facilitated with relevant comparisons of pairs of lines. 

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

.. _associative arrays: https://en.wikipedia.org/wiki/Associative_array
.. _Python dictionaries: https://docs.python.org/3/tutorial/datastructures.html#dictionaries

.. REPLACE DICTONARIES LINK WITH SPHINX-LIKE REFERENCE

.. rubric:: Footnotes

.. [#] These key-value pairs enclosed with curly braces are called `associative arrays`_, and JSON files use syntax for these arrays that is similar to `Python dictionaries`_.
.. [#] Note that this document does not cover lighting, where varying bulb types are used, or Miscellaneous Electric Loads (MELs), which are not broken into specific technologies in the Annual Energy Outlook.
.. [#] Acceptable domains include eia.gov, doe.gov, energy.gov, data.gov, energystar.gov, epa.gov, census.gov, pnnl.gov, lbl.gov, nrel.gov, sciencedirect.com, costar.com, and navigantresearch.com.
.. [#] If the warning "there is no package called 'rjson'" appears in the R Console window, try running the script again. If the warning is repeated, the rjson package should be added manually. From the Packages menu, (Windows) select Install package(s)... or (Mac) from the Packages & Data menu, select Package Installer and click the Get List button in the Package Installer window. If prompted, select a repository from which to download packages. On Windows, select "rjson" from the list of packages that appears. On a Mac, search in the list for "rjson," click the "Install Dependencies" checkbox, and click the "Install Selected" button. When installation is complete, close the Package Installer window.
.. [#] When ECMs are competed against each other, demand-side heating and cooling ECMs that improve the performance of the building envelope reduce the energy required to meet heating and cooling needs (supply-side energy), and that reduction in energy requirements for heating and cooling is reflected in a reduced baseline for supply-side heating and cooling ECMs. At the same time, supply-side heating and cooling ECMs that are more efficient reduce the energy used to provide heating and cooling services, thus reducing the baseline energy for demand-side ECMs. The description of :ref:`ECM competition <ecm-competition>` in Step 3 of the analysis approach section includes further details regarding supply-side and demand-side heating and cooling energy use balancing.
