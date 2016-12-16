ECM JSON Schema
===============

This section outlines the elements of a JSON file that defines an energy conservation measure (ECM) -- a technology included for analysis with Scout. More details about ECMs can be found in the :ref:`Analysis Approach <analysis-step-1>` and :ref:`Tutorial 1 <tuts-1>` sections.

Each sub-section corresponds to a single key in the JSON. The details provided for each key include the parent and child fields, valid data types, a brief description of the field, and one or more illustrative examples. Parent keys are above and child keys are below the current key in the hierarchy of a JSON file. ::

   {"parent key": {
      "current key": {
         "child key": "value"}}}

The data type "none" indicates that ``null`` is a valid value for that key. The parent "root" indicates that it is at the top of the hierarchy, that is, there are no parents for that key.

.. _json-name:

name
----

* **Parents:** root
* **Children:** none
* **Type:** string

A descriptive name of the technology defined in the ECM. If possible, the name length should be kept to under 55 characters including spaces. ::

   {...
    "name": "Residential Natural Gas HPWH",
    ...}

.. _json-climate_zone:

climate_zone
------------

* **Parents:** root
* **Children:** none
* **Type:** string, list

Either a single climate zone or list of climate zones to which the ECM applies. The climate zone strings must come from the list of :ref:`valid entries <ecm-baseline_climate-zone>` in the :ref:`ecm-def-reference`. ::

   {...
    "climate_zone": ["AIA_CZ2", "AIA_CZ3"],
    ...}

.. _json-bldg_type:

bldg_type
---------

* **Parents:** root
* **Children:** none
* **Type:** string, list

A single building type or a list of residential and/or commercial building types in which the ECM could be installed. The building types specified must be from the list of :ref:`valid entries <ecm-baseline_building-type>` in the :ref:`ecm-def-reference`. ::

   {...
    "bldg_type": "all residential",
    ...}

.. _json-structure_type:

structure_type
--------------

* **Parents:** root
* **Children:** none
* **Type:** string, list

The structure type indicates whether the technology described by the ECM is suitable for application in new construction, completed/existing buildings, or both. :ref:`Valid structure types <ecm-baseline_structure-type>` are limited to ``new``, ``existing``, or a list with both structure types. ::

   {...
    "structure_type": "new",
    ...}

.. tip::

   If the ECM technology can be applied to both new construction and existing buildings but with differing energy performance, installed costs, and/or service life, those differing values should be specified explicitly in the :ref:`json-energy_efficiency`, :ref:`json-installed_cost`, and/or :ref:`json-product_lifetime` fields.

.. _json-fuel_type:

fuel_type
---------

* **Parents:** root
* **Children:** none
* **Type:** string, list

The fuel type(s) should correspond to the energy source(s) used by the technology described in the ECM, and can be specified as a string for a single fuel type or as a list to include multiple fuel types. The fuel type(s) should be drawn from the list of valid fuel types. ::

   {...
    "fuel_type": "electricity",
    ...}

.. tip::

   If the ECM describes a technology that does not use energy directly but affects the energy use of the building, i.e., windows and building envelope, the fuel type should be specified as ``all``.

.. tip::

   If :ref:`fuel switching <json-fuel_switch_to>` is included in the ECM definition, then the fuel types listed should include all fuel types corresponding to equipment or technologies that can be supplanted by the technology described in the ECM.

.. _json-end_use:

end_use
-------

* **Parents:** root
* **Children:** none
* **Type:** string, list

The end use corresponds to the type of building function that is served by the technology described in the ECM. The end use can be specified as a single string or, if multiple end uses apply, as a list. The valid end uses depend on the building type(s) and fuel type(s) specified, as indicated in the :ref:`end use tables <ecm-baseline_end-use>` in the :ref:`ecm-def-reference`. ::

   {...
    "end_use": ["heating", "cooling"],
    ...}

.. MORE CLARIFICATION MAY BE NEEDED HERE REGARDING VALID END USES WHEN BOTH RESIDENTIAL AND COMMERCIAL BUILDING TYPES ARE SPECIFIED

.. tip::

   If the ECM is describing a technology that affects the heating and cooling load of a building, such as insulation, windows, or an air barrier, the end uses should be given as ``["heating", "cooling"]``.

.. _json-technology:

technology
----------

* **Parents:** root
* **Children:** none
* **Type:** string, list

The technology field lists the specific technologies or device types that can be replaced by the technology described by the ECM. A complete listing of :ref:`valid technology names <ecm-baseline_technology>` is provided in the :ref:`ecm-def-reference`. ::

   {...
    "technology": ["HP water heater", "elec_water_heater", "electric WH"],
    ...}

.. MORE CLARIFICATION MAY BE NEEDED HERE REGARDING HOW TO LIST TECHNOLOGIES AND WHAT TECHNOLOGIES CAN BE VALID WHEN MULTIPLE END USES APPLY

.. _json-market_entry_year:

market_entry_year
-----------------

* **Parents:** root
* **Children:** none
* **Type:** int, none

The market entry year specifies the year that the ECM entered or is expected to enter the market. The year should be given as an integer in the format YYYY. ``null`` is also an acceptable value for the market entry year, and is interpreted to mean that the ECM is available in the first year simulated in Scout. ::

   {...
    "market_entry_year": 2019,
    ...}

.. _json-market_entry_year_source:

market_entry_year_source
------------------------

* **Parents:** root
* **Children:** :ref:`json-notes`, :ref:`json-source_data`
* **Type:** dict, none

The market entry year source indicates the reference from which the market entry year for the ECM was derived. If the market entry year is ``null``, the source can also be given as ``null`` without the dict (see :ref:`json-market_exit_year_source`). ::

   {...
    "market_entry_year_source": {
      "notes": "",
      "source_data": [{
         "title": "High Efficiency Troffer Performance Specification, Version 5.0",
         "author": "",
         "organization": "U.S. Department of Energy",
         "year": 2015,
         "pages": null,
         "URL": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf"}]},
    ...}

.. _json-market_exit_year:

market_exit_year
----------------

* **Parents:** root
* **Children:** none
* **Type:** int, none

The market exit year indicates the final year that the technology described in the ECM is available for purchase. The year should be formatted as YYYY. ``null`` is also an acceptable market exit year value, and is interpreted as the technology remaining available through the final year simulated in Scout. ::

   {...
    "market_exit_year": null,
    ...}

.. _json-market_exit_year_source:

market_exit_year_source
-----------------------

* **Parents:** root
* **Children:** :ref:`json-notes`, :ref:`json-source_data`
* **Type:** dict, none

The market exit year source indicates the original source for the exit year specified for the ECM. The field is  formatted identically to the :ref:`json-market_entry_year_source` field. If the market exit year is ``null``, the source can also be given as ``null`` without the dict. ::

   {...
    "market_exit_year_source": null,
    ...}

.. _json-energy_efficiency:

energy_efficiency
-----------------

* **Parents:** root
* **Children:** (optional) values of :ref:`json-climate_zone`, :ref:`json-bldg_type`, :ref:`json-structure_type`, :ref:`json-end_use`
* **Type:** float, dict

The energy efficiency value(s) define the energy performance of the technology being described by the ECM. The numeric values should be given such that they correspond to the required units given in the :ref:`json-energy_efficiency_units` field. ::

   {...
    "energy_efficiency": 2.8,
    ...}

If it is appropriate for the technology described by the ECM, the energy efficiency can be specified more precisely using one or more of the optional child fields. The values should then be reported in a dict where the keys correspond to the applicable child fields. If multiple levels of specificity are desired, the hierarchy of the nested keys can be chosen for convenience. ::

   {...
    "energy_efficiency": {
      "heating": {
         "AIA_CZ1": {
            "all residential": 1.32,
            "small office": 1.11},
         "AIA_CZ2": {
            "all residential": 1.38,
            "small office": 1.15},
         "AIA_CZ3": {
            "all residential": 1.44,
            "small office": 1.18},
         "AIA_CZ4": {
            "all residential": 1.54,
            "small office": 1.21},
         "AIA_CZ5": {
            "all residential": 1.6,
            "small office": 1.25}},
      "cooling": {
         "AIA_CZ1": {
            "all residential": 2.2,
            "small office": 2.03},
         "AIA_CZ2": {
            "all residential": 2.16,
            "small office": 1.96},
         "AIA_CZ3": {
            "all residential": 2.11,
            "small office": 1.9},
         "AIA_CZ4": {
            "all residential": 2.02,
            "small office": 1.86},
         "AIA_CZ5": {
            "all residential": 1.9
            "small office": 1.77}}},
    ...}

.. _json-energy_efficiency_units:

energy_efficiency_units
-----------------------

* **Parents:** root
* **Children:** (optional) matching :ref:`json-energy_efficiency`
* **Type:** string, dict

This field specifies the units of the reported energy efficiency values for the ECM. The correct energy efficiency units depend on the building type, end use, and in some cases, equipment type of the technology described by the ECM. The units can be determined using the :ref:`list of energy efficiency units <ecm-energy-efficiency-units>` in the :ref:`ecm-def-reference`. ::
   
   {...
    "energy_efficiency_units": "COP",
    ...}

In cases where the energy efficiency is specified with one or more of the optional keys, if the units are the same for all values, the units can still be reported with a single string. If the units are different for some of the keys used, a dict with a structure parallel to the energy efficiency data should be used to report the units. (Energy efficiency units are not a function of climate zone and do not have to be specified with a climate zone breakdown even if the efficiency varies by climate zone.) ::

   {...
    "energy_efficiency_units": {
      "heating": {
         "all residential": "COP",
         "small office": "BTU out/BTU in"},
      "cooling": {
         "all residential": "COP",
         "small office": "BTU out/BTU in"}},
    ...}

.. _json-energy_efficiency_source:

energy_efficiency_source
------------------------

* **Parents:** root
* **Children:** :ref:`json-notes`, :ref:`json-source_data`
* **Type:** dict

This key is used to specify the source of the ECM's energy efficiency (i.e., energy performance) values. The :ref:`json-source_data` field description explains how to specify multiple sources. Any details regarding the relationship between the values in the source(s) and the values in the ECM definition should be supplied in the :ref:`json-notes` field. ::

   {...
    "energy_efficiency_source": {
      "notes": "Minimum Luminaire Efficiency value reported in section 1.4, sub-section II.a.2.a.",
      "source_data": [{
         "title": "High Efficiency Troffer Performance Specification, Version 5.0",
         "author": "",
         "organization": "U.S. Department of Energy",
         "year": 2015,
         "pages": 5,
         "URL": "https://betterbuildingssolutioncenter.energy.gov/sites/default/files/attachments/High%20Efficiency%20Troffer%20Performance%20Specification.pdf"}]},
    ...}

.. _json-installed_cost:

installed_cost
--------------

* **Parents:** root
* **Children:** (optional) values from :ref:`json-bldg_type`, :ref:`json-structure_type`
* **Type:** int, dict

The installed cost field represents the typical total cost of the technology and installation of the technology into a building. Costs should be specified such that they are consistent with the :ref:`required units <ecm-installed-cost-units>` for the type of technology described by the ECM. ::

   {...
    "installed cost": 14,
    ...}

Since installation costs can vary by building type (implicitly by building square footage) and whether the technology is being installed as part of new construction or as a replacement of existing equipment or renovation of an existing building, the costs can be specified in a dict using the indicated optional child fields. The keys should match exactly with the allowable values for each of those fields. ::

   {...
    "installed_cost": {
      "all residential": 8,
      "all commercial": 10},
    ...}

The installed costs can be specified with detail beyond what is shown using the additional optional child field types, as illustrated for the :ref:`json-energy_efficiency` field. The order of the hierarchy for the child fields is at the user's discretion.

.. _json-cost_units:

cost_units
----------

.. CAN COST UNITS ALSO BE A SUBSET OF THE LEVEL OF SPECIFICITY USED FOR THE INSTALLED COST VALUES?

* **Parents:** root
* **Children:** (optional) matching :ref:`json-installed_cost`
* **Type:** string, dict

Cost units correspond to the installed cost given for the ECM. The cost units should match the :ref:`required units <ecm-installed-cost-units>` based the type of technology described by the ECM. ::

   {...
    "cost_units": "$/1000 lm",
    }

If there is only a single cost value, a single units value should be given; if the installed cost is specified by one or more of the optional keys and the various installed costs have different units, the cost units should be specified with the same dict structure as the costs. (Cost units are not a function of climate zone and do not have to be specified with a climate zone breakdown even if the costs vary by climate zone.) ::

   {...
    "cost_units": {
      "all residential": "$/unit",
      "all commercial": "$/1000 lm"},
    ...}

.. _json-installed_cost_source:

installed_cost_source
---------------------

* **Parents:** root
* **Children:** :ref:`json-notes`, :ref:`json-source_data`
* **Type:** dict

This key is used to specify the source of the ECM's installed cost values. The :ref:`json-source_data` field description explains how to specify multiple sources. Any details regarding the relationship between the values in the source(s) and the values in the ECM definition should be supplied in the :ref:`json-notes` field. ::

   {...
    "installed_cost_source": {
      "notes": "Table 6.3, average of values reported in Total Installed Cost column for the Gas Storage water heater equipment type.",
      "source_data": [{
         "title": "Energy Savings Potential and RD&D Opportunities for Commercial Building Appliances (2015 Update)",
         "author": "Navigant Consulting; William Goetzler, Matt Guernsey, Kevin Foley, Jim Young, Greg Chung",
         "organization": "U.S. Department of Energy",
         "year": 2016,
         "pages": 80,
         "URL": "http://energy.gov/sites/prod/files/2016/06/f32/DOE-BTO%20Comml%20Appl%20Report%20-%20Full%20Report_0.pdf"}]},
    ...}

.. _json-product_lifetime:

product_lifetime
----------------

* **Parents:** root
* **Children:** (optional) values from :ref:`json-bldg_type`
* **Type:** int, dict

The product lifetime is the expected usable life of the technology described by the ECM in years. The lifetime value should be an integer greater than 0. ::

   {...
    "product_lifetime": 3,
    ...}

The product lifetime can be specified by building type, if appropriate for the ECM. The building types are the keys in the lifetime dict and should match the types listed in the :ref:`json-bldg_type` field. ::

   {...
    "product_lifetime": {
      "single family home": 10,
      "small office": 7,
      "mercantile/service": 6},
    ...}

.. _json-product_lifetime_units:

product_lifetime_units
----------------------

* **Parents:** root
* **Children:** none
* **Type:** string

The product lifetime units are years. This field is included largely to ensure that the correct units were used when specifying the product lifetime. ::

   {...
    "product_lifetime_units": "years",
    ...}

.. _json-product_lifetime_source:

product_lifetime_source
-----------------------

* **Parents:** root
* **Children:** :ref:`json-notes`, :ref:`json-source_data`
* **Type:** dict

This key is used to specify the source of the ECM's product lifetime values. The :ref:`json-source_data` field description explains how to specify multiple sources. Any details regarding the relationship between the values in the source and the values in the ECM definition should be supplied in the :ref:`json-notes` field. ::

   {...
    "product_lifetime_source": {
      "notes": "Table C-2, Lamp Life column, average of A-Type, Track Lighting, and Downlights Incandescent Omni rows; converted to years assuming an average use of 8 hours/day.",
      "source_data": [{
         "title": "Energy Savings Forecast for Solid-State Lighting in General Illumination Applications",
         "author": "Navigant Consulting; Julie Penning, Kelsey Stober, Victor Taylor, Mary Yamada",
         "organization": "U.S. Department of Energy",
         "year": 2016,
         "pages": 65,
         "URL": "http://energy.gov/sites/prod/files/2016/09/f33/energysavingsforecast16_2.pdf"}]},
    ...}

.. _json-measure_type:

measure_type
------------

* **Parents:** root
* **Children:** none
* **Type:** string

This field is used to specify whether the technology described by the ECM could be substituted for a component already installed in buildings, such as an electric cold-climate heat pump being substituted for an electric furnace and central AC system, or enhance the performance of an existing component, such as a window film applied to an existing window or an HVAC controls system that improves the performance of existing HVAC equipment. The measure type is then either ``"full service"`` or ``"add-on"``, respectively. ::

   {...
    "measure_type": "full service",
    ...}

.. _json-fuel_switch_to:

fuel_switch_to
--------------

* **Parents:** root
* **Children:** none
* **Type:** string, list

If the ECM is intended to replace comparable building components that use one of multiple fuel types, such as both electric and natural gas water heaters, this field should identify the fuel type of the technology described by the ECM. The fuel type should match exactly with one of the :ref:`fuel types <ecm-baseline_fuel-type>` listed in the :ref:`ecm-def-reference`. If the value of :ref:`json-fuel_type` is a single fuel type that matches the technology described by the ECM, this filed can be given as ``null``. ::

   {...
    "fuel_switch_to": "natural gas",
    ...}

.. _json-market_scaling_fractions:

market_scaling_fractions
------------------------

* **Parents:** root
* **Children:** (optional) values from :ref:`json-climate_zone`, :ref:`json-bldg_type`, :ref:`json-end_use`
* **Type:** int, dict, none

The market scaling fraction is used to further reduce the energy use of the applicable baseline market [#]_ specified for an ECM whose technology corresponds to only a fraction of that market. The market scaling fraction value should be between 0 and 1, representing the desired fraction of the baseline market. If the ECM does not need a market scaling fraction, the field should be given the value ``null``. ::

   {...
    "market_scaling_fractions": 0.18,
    ...}

Market scaling fractions can be separately specified using the optional child fields if relevant to the technology described by the ECM, if the fields are part of the applicable baseline market, and if appropriate source information is provided. ::

   {...
    "market_scaling_fractions": {
      "all residential": 0.54,
      "all commercial": 0.36},
    ...}

.. _json-market_scaling_fractions_source:

market_scaling_fractions_source
-------------------------------

* **Parents:** root
* **Children:** :ref:`json-notes`, :ref:`json-fraction_derivation`, :ref:`json-source_data`
* **Type:** dict, none

The market scaling fractions source identifies the sources that were used to determine the market scaling fraction, including the exact method for deriving the fraction. If the :ref:`json-market_scaling_fractions` field is ``null``, the source should also be specified as ``null``. ::

   {...
    "market_scaling_fractions_source": {
      "notes": "Data from Figure 4.4.",
      "fraction_derivation": "Sum of 2015 data for LED - Connected Lighting, LED - Controls, and Conventional Lighting - Controls.",
      "source_data": [{
         "title": "Energy Savings Forecast for Solid-State Lighting in General Illumination Applications",
         "author": "Navigant Consulting; Julie Penning, Kelsey Stober, Victor Taylor, Mary Yamada",
         "organization": "U.S. Department of Energy",
         "year": 2016,
         "pages": 23,
         "URL": "http://energy.gov/sites/prod/files/2016/09/f33/energysavingsforecast16_2.pdf"}]},
    ...}

.. _json-_description:

_description
------------

* **Parents:** root
* **Children:** none
* **Type:** string

A one to two sentence description of the ECM. If the ECM is prospective, i.e., describing a technology still being researched, the description should include URLs or other identifying information for additional references that contain further details about the technology. ::

   {...
    "_description": "LED troffers for commercial modular dropped ceiling grids that are a replacement for the entire troffer luminaire for linear fluorescent bulbs, not a retrofit kit or linear LED bulbs that slot into existing troffers.",
    ...}

.. _json-_notes:

_notes
------

* **Parents:** root
* **Children:** none
* **Type:** string

A text field that can be used for explanatory notes regarding the technologies that can be replaced by the ECM, any notable assumptions made in the specification of the ECM, or any other relevant information about the ECM that is not captured by any other field. ::

   {...
    "_notes": "Energy performance is specified for the luminaire, not the base lamp.",
    ...}

.. _json-_added_by:

_added_by
---------

* **Parents:** root
* **Children:** :ref:`json-ecm-author-name`, :ref:`json-ecm-author-organization`, :ref:`json-ecm-author-email`, :ref:`json-ecm-author-timestamp`
* **Type:** dict

A dict containing basic information about the user that originally created the ECM. ::

   {...
    "_added_by": {
      "name": "Maureen Baruch Kilda",
      "organization": "U.S. Department of Energy",
      "email": "maureen.b.kilda@hq.doe.gov",
      "timestamp": "2016-01-28 21:17:35 UTC"}
    ...}

.. _json-_updated_by:

_updated_by
-----------

* **Parents:** root
* **Children:** :ref:`json-ecm-author-name`, :ref:`json-ecm-author-organization`, :ref:`json-ecm-author-email`, :ref:`json-ecm-author-timestamp`
* **Type:** dict

A dict containing basic information that identifies the user that last updated the ECM, identical in structure to the dict in the :ref:`json-_added_by` field. ``null`` if the ECM has never been modified. ::

   {...
    "_updated_by": ``null``
    ...}

.. NOTE THAT THE USE OF NULL HERE IS NOT CONSISTENT WITH WHAT IS SHOWN IN THE TUTORIALS AND MIGHT NOT PASS EXISTING TESTS IN ecm_prep.py

.. _json-notes:

notes
-----

* **Parents:** :ref:`json-market_entry_year_source`, :ref:`json-market_exit_year_source`, :ref:`json-energy_efficiency_source`, :ref:`json-installed_cost_source`, :ref:`json-product_lifetime_source`, :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** string

The notes field should include the exact location of the specific information used from the source(s) identified. The location information should include the table or figure number, and if the value is drawn from tabular data, the applicable row and column heading(s). The notes should also outline any calculations performed to convert from the values found in the source(s) to the value used in the ECM definition, including unit conversions and methods for combining multiple values (e.g., averaging, market share-weighted averaging). Any other assumptions regarding the derivation of the related value in the ECM definition should also be included. ::

   {...
    "notes": "Value drawn from Table 1 for the Ventless or Vented Electric, Standard product type. For clothes drying, the expected units of EF (Energy Factor) are equivalent to lbs/kWh.",
    ...}

.. _json-fraction_derivation:

fraction_derivation
-------------------

* **Parents:** :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** string

For the market scaling fractions, this field should provide a description of how the values were calculated. The description should have enough detail for another user to be able to easily repeat the calculations. ::

   {...
    "fraction_derivation": "Sum of 2015 data for LED - Connected Lighting, LED - Controls, and Conventional Lighting - Controls.",
    ...}

.. _json-source_data:

source_data
-----------

* **Parents:** :ref:`json-market_entry_year_source`, :ref:`json-market_exit_year_source`, :ref:`json-energy_efficiency_source`, :ref:`json-installed_cost_source`, :ref:`json-product_lifetime_source`, :ref:`json-market_scaling_fractions_source`
* **Children:** :ref:`json-title`, :ref:`json-author`, :ref:`json-organization`, :ref:`json-year`, :ref:`json-pages`, :ref:`json-URL`
* **Type:** list

A list that encloses one or more dicts, where each dict corresponds to a single source and includes all of the child fields listed. ::

   {...
    "source_data": [{
      "title": "ENERGY STAR Program Requirements: Product Specification for Clothes Dryers",
      "author": null,
      "organization": "U.S. Environmental Protection Agency",
      "year": 2014,
      "pages": "2-3",
      "URL": "https://www.energystar.gov/sites/default/files/specs//ENERGY%20STAR%20Final%20Version%201%200%20Clothes%20Dryers%20Program%20Requirements.pdf"}],
   ...}

.. _json-title:

title
-----

* **Parents:** :ref:`json-source_data`
* **Children:** none
* **Type:** string

The title of the source document. ::

   {...
    "title": "ENERGY STAR Program Requirements: Product Specification for Clothes Dryers",
    ...}

.. _json-author:

author
------

* **Parents:** :ref:`json-source_data`
* **Children:** none
* **Type:** string, none

The names of the author(s) of the publication, if any are identified. If no authors are listed, ``null`` or an empty string are acceptable values for this field if no authors are identified by name in the source. ::

   {...
    "author": null,
    ...}

.. _json-organization:

organization
------------

* **Parents:** :ref:`json-source_data`
* **Children:** none
* **Type:** string

The journal publication, organization, or other entity that released the source article, report, specification, test result, or other reference. ::

   {...
    "organization": "U.S. Environmental Protection Agency",
    ...}

.. _json-year:

year
----

* **Parents:** :ref:`json-source_data`
* **Children:** none
* **Type:** int

The year that the source was published or last updated. ::

   {...
    "year": 2014,
    ...}

.. _json-pages:

pages
-----

* **Parents:** :ref:`json-source_data`
* **Children:** none
* **Type:** int, string, none

The page number(s) of the information in the source document, if applicable. If the source is not divided into pages, this entry can have the value ``null``. If the relevant information can be found on a single page, the page number should be given as an integer. If the information is divided across several pages or a range of pages, the page numbers should be given as a string. ::

   {...
    "pages": "24, 26-29, 37",
    ...}

.. _json-URL:

URL
---

* **Parents:** :ref:`json-source_data`
* **Children:** none
* **Type:** string

The URL where the source can be found on the internet. The URL should point directly to the original source file, if possible. ::

   {...
    "URL": "https://www.energystar.gov/sites/default/files/specs//ENERGY%20STAR%20Final%20Version%201%200%20Clothes%20Dryers%20Program%20Requirements.pdf",
    ...}

.. _json-ecm-author-name:

name
----

* **Parents:** :ref:`json-_updated_by`, :ref:`json-_added_by`,
* **Children:** none
* **Type:** string

The name of the author of the initial definition or latest changes to the ECM. ::

   {...
    "name": "Maureen Adams",
    ...}

.. _json-ecm-author-organization:

organization
------------

* **Parents:** :ref:`json-_updated_by`, :ref:`json-_added_by`,
* **Children:** none
* **Type:** string

The organization or employer with which the :ref:`named <json-ecm-author-name>` author is affiliated. ::

   {...
    "organization": "U.S. Department of Energy",
    ....}

.. _json-ecm-author-email:

email
-----

* **Parents:** :ref:`json-_updated_by`, :ref:`json-_added_by`,
* **Children:** none
* **Type:** string

The email address of the :ref:`named <json-ecm-author-name>` author. ::

   {...
    "email": "james.clipper@ee.doe.gov",
    ...}

.. _json-ecm-author-timestamp:

timestamp
---------

* **Parents:** :ref:`json-_updated_by`, :ref:`json-_added_by`,
* **Children:** none
* **Type:** string

The date and time at which the relevant changes were completed. The entry should be formatted as YYYY-MM-DD HH\:MM\:SS, with the time reported in 24-hour `Universal Coordinated Time (UTC)`_ if possible. ::

   {...
    "timestamp": "2014-03-27 14:36:18 UTC",
    ...}

.. _Universal Coordinated Time (UTC): http://www.nhc.noaa.gov/aboututc.shtml

.. rubric:: Footnotes

.. [#] The applicable baseline market is comprised of the :ref:`json-climate_zone`, :ref:`json-bldg_type`, :ref:`json-structure_type`, :ref:`json-end_use`, :ref:`json-fuel_type`, and :ref:`json-technology` fields.