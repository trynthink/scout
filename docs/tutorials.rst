.. _tutorials:

Tutorials
=========


.. _tuts-1_new-ECMs:

Part 1: Creating a new ECM
--------------------------

Before beginning this tutorial, it is recommended that you review the :ref:`list of required and optional parameters <ecm-contents>` in an ECM definition.

The examples in this tutorial will demonstrate how to write new ECMs so that they will be compliant with all relevant formatting requirements and provide the :ref:`needed information <ecm-contents>` about a technology in the structure expected by the Scout analysis engine. These examples are *not* exhaustive descriptions of all of the detailed options available to specify an ECM. A detailed outline of all of the options and combinations available for an ECM is available in section (add link).

.. CREATE A SECTION FOR THE DOCUMENTATION THAT OUTLINES EVERY POSSIBLE COMBINATION OF SPECIFICATIONS FOR AN ECM, ESPECIALLY IN TERMS OF SPECIFYING PROBABILITY DISTRIBUTIONS OF VARIOUS TYPES, AND SPECIFYING C/P/L AT VARYING LEVELS OF DETAIL/SPECIFICITY

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

.. In this tutorial, we will create two different ECMs. We will begin with an ECM that has a relatively simple cost and performance specification. The second example ECM will demonstrate more complex definitions for cost and performance and employ some optional measure features. Following these two examples, we recommend reviewing the `measure database`_ to see further examples of different kinds of ECMs. 

.. measure database:

.. CREATE A KEY PAIR INDEX FOR ECM DEFINITIONS (OR AT LEAST FOR THE BASELINE MARKET DEFINITION)


ECM 1 – Commercial LED troffers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The required information for defining this ECM will be covered in the same order as the :ref:`list of required and optional parameters <ecm-contents>` in the :ref:`analysis-approach` section.

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

The applicable baseline market parameters specify the climate zones, building types, and other elements that define to what portion of energy use the ECM applies.

LED troffers can be installed in buildings in any climate zone, and apply to all commercial building types. To simplify entry, "all" can be used to specify climate zones (instead of writing a list of all climate zones), and "all," "all residential," or "all commercial" can be used to specify building types. ::

   {...
    "climate_zone": "all",
    "bldg_type": "all commercial",
    ...}

ECMs can apply to only new construction, only retrofits, or all buildings both new and existing. This is specified under the "structure_type" key with the values "new," "retrofit," or "all," respectively. LED troffers can be installed in new construction and retrofits. ::

   {...
    "structure_type": "all",
    ...}

The end use(s) for an ECM are separated into primary end uses, those that are applicable to the technology itself, and secondary end uses, which are those end uses that are affected by changes in the energy use from the ECM. In the case where there are no secondary end uses affected, the key must still be included, but the value should be set to ``null``. The end use names are the same as the residential__ and commercial__ end uses specified in the AEO. The primary end use for LED troffers is lighting. Changing from fluorescent bulbs typically found in troffers will reduce the heat output from the fixture, thus reducing the cooling load (and increase the heating load, if any) for the building. As a result, the secondary end uses for LED troffers are "heating" and "cooling". ::

   {...
    "end_use": {
      "primary": "lighting",
      "secondary": ["cooling", "heating"]},
    ...}

.. __: https://www.eia.gov/forecasts/aeo/data/browser/#/?id=4-AEO2016&cases=ref2016~ref_no_cpp&sourcekey=0
.. __: https://www.eia.gov/forecasts/aeo/data/browser/#/?id=5-AEO2016&cases=ref2016~ref_no_cpp&sourcekey=0

Parallel to the structure for the end use data, there must be "primary" and "secondary" keys specifying the fuel type for an ECM. The primary fuel types specified should correspond to the primary end use(s) already specified, and similarly for the secondary fuel types corresponding to those end uses. If no secondary end uses are specified, the secondary fuel type key should have the value ``null``. If multiple fuel types apply for either category, primary or secondary, they can be specified in a list, as shown in the example for secondary fuel types. In the case of LED troffers, electricity is the only relevant primary fuel type. The secondary fuel types include all fuel types applicable to heating and cooling. ::

   {...
    "fuel_type": {
      "primary": "electricity",
      "secondary": "all"},
    ...}

.. BY THE DESCRIPTION BELOW, IS A DAYLIGHTING MEASURE A "DEMAND" MEASURE? IS THAT CORRECT? DOES THIS EXPLANATION NEED TO BE MODIFIED?
.. CONFIRM THAT IT DOES NOT MATTER IF "SUPPLY" OR "DEMAND" IS USED FOR SECONDARY HEATING AND COOLING

The technology type specifies whether the ECM applies to "supply" or "demand." If the ECM affects devices or equipment that use energy directly, the technology type is "supply." If the ECM affects the need for devices or equipment to provide services (e.g., heating, cooling, lighting), the technology type is "demand." For the "heating" and "cooling" end use, a heat pump ECM is of the "supply" technology type, while an R-8/in rigid insulation board ECM is of the "demand" technology type. The "demand" technology type can only apply to the heating and cooling end uses. Again there are "primary" and "secondary" keys, which should be used to indicate the technology type for the respective end uses. If there are no secondary end uses, the secondary technology type value should be set to ``null``. LED troffers are a technology that improves the efficiency of lighting technologies, thus it is of the supply technology type. The secondary heating and cooling effects can be coded as either supply or demand (since they are equalized within the analysis engine). ::

   {...
    "technology_type": {
      "primary": "supply",
      "secondary": "supply"},
    ...}

.. IS IT CORRECT THAT AN "ALL HEATING" SPECIFICATION WILL BE LIMITED TO TECHNOLOGIES FOR THE CURRENT FUEL TYPE UNLESS FUEL SWITCHING IS SPECIFIED (AND THEN THE HEATING TECHNOLOGIES FROM OTHER FUEL TYPES ARE AUTOMATICALLY APPLIED)?

The technology specification drills down further into the specific technologies or device types that apply to the primary and secondary end uses for the ECM. The specific technology names correspond to the names of residential__ and commercial__ thermal load components for the "demand" technology type. On the supply side, technology names generally correspond to major equipment types used in the AEO_ [#]_.

 In some cases, an ECM might be able to replace all of the currently used technologies for its end use and fuel type. For example, a highly efficient thermoelastic heat pump might be able to replace all current electric heating and cooling technologies. In that case, the primary technologies can be listed as "all heating" and "all cooling." 

 For this example, LED troffers are likely to replace linear fluorescent bulbs, the typical bulb type for troffers. There are many lighting types for commercial buildings, but we will include all of the lighting types that are specified as F\_\_T\_\_, including those with additional modifying text. For the secondary technologies, we can include all heating and cooling. ::

   {...
    "technology": {
      "primary": ["F28T8 HE w/ OS", "F28T8 HE w/ SR", "F96T8", "F96T12 mag", "F96T8 HE", "F28T8 HE w/ OS & SR", "F28T5", "F28T8 HE", "F32T8", "F96T12 ES mag", "F34T12", "T8 F32 EEMag (e)"]],
      "secondary": ["all heating", "all cooling"]},
    ...}

.. __: https://github.com/trynthink/scout/blob/master/1999%20Residential%20heating%20and%20cooling%20loads%20component%20analysis.pdf
.. __: https://github.com/trynthink/scout/blob/master/1999%20Commercial%20heating%20and%20cooling%20loads%20component%20analysis.pdf
.. _AEO: https://www.eia.gov/analysis/studies/buildings/equipcosts/pdf/full.pdf


Market Entry and Exit Year
**************************

The market entry year represents the year the technology is or will be available for purchase and installation. Some ECMs might be prospective, representing technologies not currently available. Others might represent technologies currently commercially available. The market entry year should reflect the current status of the technology described in the ECM. Similarly, the market exit year represents the year the technology is expected to be withdrawn from the market. The market entry year and exit year both require source information. As much as is practicable, a :ref:`high quality<ecm-sources>` reference should be used for both values. If no source is available, such as for a technology that is still quite far from commercialization, a brief explanatory note should be provided for the market entry year source. If it is anticipated that the product will not be withdrawn from the market prior to the end of the model :ref:`time horizon <2010-2040 projection>`, the exit year should be given as ``null`` and the source should be given as ``NA``.

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
    "market_exit_year_source": "NA",
    ...}


Performance
***********

.. ADD EXPLANATION OF HOW TO USE SECONDARY FIELDS
.. UNSURE OF HOW TO EXPLAIN HOW TO CONFIGURE OPENSTUDIO MEASURE (AND DO WE EXPECT USERS TO DO THAT) TO PROVIDE THE INFORMATION HERE


The energy performance or efficiency of the ECM must be specified in three parts: the quantitative performance (only the value(s)), the units of the performance value(s) provided, and source(s) that support the indicated performance information. 

The units specified are expected to be consistent with the units for each end use outlined in the :ref:`ECM Definition Reference <ecm-performance-units>` section.

The source(s) for the performance data should be credible sources, such as :ref:`those outlined <ecm-sources>` in the :ref:`analysis-approach` section. The source information should be provided using only the fields shown in the example.

The performance can be specified with a different value for each end use, and also separated by residential and commercial buildings, if appropriate. Source information should be provided as appropriate for the level of detail used in the performance. If each of the performance data come from different sources, each source should be specified separately using the same nested dict structure. It is also acceptable to provide a single source if all of the performance data come from that source. This detailed performance specification approach is demonstrated in the second ECM example (add link).

All lighting data should be provided in the units of lumens per Watt (denoted "lm/W"). LED troffers performance information is based on the `High Efficiency Troffer Performance Specification`_. ::

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

The absolute installed cost must be specified for the ECM, including the cost value, units, and reference source. The cost units should be specified according to :ref:`this list <ecm-installed-cost-units>`, noting that residential and commercial equipment have different units, and that sensors and controls ECMs also have different units from other equipment types.

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

The lifetime of the ECM, or the expected amount of time that the ECM technology will last before requiring replacement, is specified using a structure identical to the installed cost. Again, the lifetime value, units, and source information must be specified for the corresponding keys. The units should always be in years, ideally as integer values greater than 0. LED troffers have rated lifetimes on the order of 50,000 hours, though the `High Efficiency Troffer Performance Specification`_ requires a minimum lifetime of 68,000 hours. ::

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
    "_notes": "Energy performance is specified for the luminare, not the base lamp.",
    ...}

Basic contact information regarding the author of a new ECM should be added to the fields under the "_added_by" key. ::

   {...
    "_added_by": {
      "name": "Carmen Sandiego",
      "organization": "Super Appliances, Inc.",
      "email": "carmen.sandiego@superappliances.com",
      "timestamp": "2009-10-12 12:53:19"},
    ...}


"Optional" Entries
******************

.. CONFIRM THAT ONLY ONE OF NULL OR NA ARE ACCEPTABLE FOR A GIVEN FIELD

These "optional" fields must be included in the ECM definition, but can be set to a value of ``null`` or ``"NA"``, as appropriate for the particular field, if they are not relevant to the ECM.

If the ECM applies to only a portion of the energy use in an applicable baseline market, even after specifying the particular end use, fuel type, and technologies that are relevant, a scaling value can be added to the ECM definition to specify what fraction of the applicable baseline market is truly applicable to that ECM. A source must be provided for the scaling fraction, following the same format used elsewhere, such as for the installed cost data.

Similar to the performance data, multiple different scaling fraction values can be specified if the ECM applies to multiple building types or climate zones. Again, the sources should be provided with equal specificity if multiple sources were required to obtain the various scaling fraction values.

.. CONFIRM THIS EXPLANATION OF MULTIPLE SCALING FRACTION VALUES IS CORRECT

When creating a new measure, it is important to carefully specify the applicable baseline market to avoid the use of the market scaling fraction parameter, if at all possible. If the scaling fraction is not used, it should have a ``null`` value, and the source should be set as ``"NA"``. 

No market scaling fraction is required for the LED troffers ECM. ::

   {...
    "market_scaling_fractions": null,
    "market_scaling_fractions_source": "NA",
    ...}

If the ECM is intended to supplant technologies with multiple fuel types, the fuel type of the ECM itself should be specified. For example, if an electric heat pump water heater is expected to replace existing electric *and* natural gas water heaters, the "fuel_switch_to" option should be set to the fuel type of the ECM itself: "electricity." All lighting uses only electricity, so this option is not relevant to LED troffers. ::

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


ECM 2 – Residential integrated heat pump
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~




.. _tuts-2_preparation:

Part 2: Preparing ECMs for analysis
-----------------------------------


.. _tuts-3_analysis:

Part 3: Running an analysis
---------------------------


.. _tuts-4_outputs:

Part 4: Viewing and understanding outputs
-----------------------------------------


.. _associative arrays: https://en.wikipedia.org/wiki/Associative_array
.. _Python dictionaries: https://docs.python.org/3/tutorial/datastructures.html#dictionaries

.. REPLACE DICTONARIES LINK WITH SPHINX-LIKE REFERENCE

.. rubric:: Footnotes

.. [#] These key-value pairs enclosed with curly braces are called `associative arrays`_, and JSON files use syntax for these arrays that is similar to `Python dictionaries`_.
.. [#] Note that this document does not cover lighting, where varying bulb types are used, or Miscellaneous Electric Loads (MELs), which are not broken into specific technologies in the Annual Energy Outlook.
