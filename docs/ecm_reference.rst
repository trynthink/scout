.. |br| raw:: html

   <br />

.. |tooltip| raw:: html

   <span class="tooltip">

.. |chunk-b| raw:: html

   <span class="tooltip chunk"><b>

.. |close| raw:: html

   </b></span></span>

.. _ecm-def-reference:

ECM Definition Reference
========================

In some parts of the definition of an ECM, specific values must be entered for the ECM to be valid and successfully included in an analysis. In particular, the installed cost and energy efficiency units used must match exactly with the expected units for a given building sector, end use, and technology type. These units are defined by the EIA Annual Energy Outlook data used to define the baseline technology cost, efficiency, and lifetime.

.. _ecm-applicable-baseline-market:

Applicable baseline market options
----------------------------------

For each of the keys in the applicable baseline market definition, only specific entries are expected and allowable. This section outlines those acceptable entries for each of the keys.

For some keys, there are shorthand summary values that can be used when all or a large group of more specific values for that key apply. For example, if all of the climate zones should be included in the applicable baseline market, the value "all" can be specified instead of typing out each climate zone name in a list. These shorthand values are provided after the semi-colon in the lists below. Additional notes might also be provided to further clarify the different summary values available for a given key. More information regarding the use of these shorthand values is in the :ref:`ecm-features-shorthand` section.

.. _ecm-baseline_climate-zone:

Climate zone
~~~~~~~~~~~~

|tooltip| AIA_CZ1 |chunk-b| AIA Climate Zone 1 |close|, |tooltip| AIA_CZ2 |chunk-b| AIA Climate Zone 2 |close|, |tooltip| AIA_CZ3 |chunk-b| AIA Climate Zone 3 |close|, |tooltip| AIA_CZ4 |chunk-b| AIA Climate Zone 4 |close|, |tooltip| AIA_CZ5 |chunk-b| AIA Climate Zone 5 |close|; all

.. figure:: https://www.eia.gov/consumption/residential/reports/images/climatezone-lg.jpg

   Map of American Institute of Architects (AIA) climate zones for the continental U.S., Alaska, and Hawaii.

.. _ecm-baseline_building-type:

Building type
~~~~~~~~~~~~~

**Residential:** single family home, multi family home, mobile home; all residential

**Commercial:** assembly, education, food sales, food service, health care, lodging, large office, small office, mercantile/service, warehouse, other; all commercial

.. note::

   "all" can be used instead of specifying both "all residential" and "all commercial" if all residential *and* commercial building types apply.

.. _ecm-baseline_structure-type:

Structure type
~~~~~~~~~~~~~~

new, existing; all

.. _ecm-baseline_fuel-type:

Fuel type
~~~~~~~~~

**Residential:** electricity, natural gas, distillate, other fuel; all

**Commercial:** electricity, natural gas, distillate; all

.. _ecm-baseline_end-use:

End use
~~~~~~~

The end use names appear verbatim in the first column of the tables for residential and commercial buildings.

.. note::

   While "all" is available for specifying all of the end uses in residential and/or commercial buildings (depending on the building types selected), its use should be limited to ECMs where a single technology can credibly affect all energy use in the building. Using the "all" option for end uses also significantly increases computational expense, and that expense will scale exponentially if uncertainty is present on any of the ECMs in the analysis.

**Residential**

+-----------------------+-------------+-------------+------------+------------+
|        End Use        |                       Fuel Type                     |
+                       +-------------+-------------+------------+------------+
|                       | electricity | natural gas | distillate | other fuel |
+=======================+=============+=============+============+============+
| heating               |      X      |      X      |      X     |      X     |
+-----------------------+-------------+-------------+------------+------------+
| secondary heating     |      X      |      X      |      X     |      X     |
+-----------------------+-------------+-------------+------------+------------+
| cooling               |      X      |      X      |            |            |
+-----------------------+-------------+-------------+------------+------------+
| water heating         |      X      |      X      |      X     |      X     |
+-----------------------+-------------+-------------+------------+------------+
| cooking               |      X      |      X      |            |      X     |
+-----------------------+-------------+-------------+------------+------------+
| drying                |      X      |      X      |            |      X     |
+-----------------------+-------------+-------------+------------+------------+
| lighting              |      X      |             |            |            |
+-----------------------+-------------+-------------+------------+------------+
| refrigeration         |      X      |             |            |            |
+-----------------------+-------------+-------------+------------+------------+
| fans & pumps          |      X      |             |            |            |
+-----------------------+-------------+-------------+------------+------------+
| computers             |      X      |             |            |            |
+-----------------------+-------------+-------------+------------+------------+
| TVs                   |      X      |             |            |            |
+-----------------------+-------------+-------------+------------+------------+
| other (grid electric) |      X      |             |            |            |
+-----------------------+-------------+-------------+------------+------------+
| all                   |      X      |      X      |      X     |      X     |
+-----------------------+-------------+-------------+------------+------------+

.. ceiling fans are currently not shown

**Commercial**

+-------------------------+-------------+-------------+------------+
|        End Use          |                Fuel Type               |
+                         +-------------+-------------+------------+
|                         | electricity | natural gas | distillate |
+=========================+=============+=============+============+
| heating                 |      X      |      X      |      X     |
+-------------------------+-------------+-------------+------------+
| cooling                 |      X      |      X      |            |
+-------------------------+-------------+-------------+------------+
| ventilation             |      X      |             |            |
+-------------------------+-------------+-------------+------------+
| water heating           |      X      |      X      |      X     |
+-------------------------+-------------+-------------+------------+
| lighting                |      X      |             |            |
+-------------------------+-------------+-------------+------------+
| refrigeration           |      X      |             |            |
+-------------------------+-------------+-------------+------------+
| cooking                 |      X      |      X      |            |
+-------------------------+-------------+-------------+------------+
| all                     |      X      |      X      |      X     |
+-------------------------+-------------+-------------+------------+

.. | PCs                     |      X      |             |            |
   +-------------------------+-------------+-------------+------------+
   | non-PC office equipment |      X      |             |            |
   +-------------------------+-------------+-------------+------------+
   | MELs                    |      X      |             |            |
   +-------------------------+-------------+-------------+------------+

.. _ecm-baseline_technology:

Technology
~~~~~~~~~~

Technology names appear verbatim. The lighting technology names are in the body of the table, categorized by illumination technology (e.g., incandescent, fluorescent) and application or fixture type.

.. note::

   "all" is available as an option to specify all of the technology names that apply to all of the building types, fuel types, and end uses specified for the applicable baseline market. In addition, "all" can be made specific to a particular end use by specifying "all" followed by the end use name -- "all heating" or "all water heating," for example. This shorthand will capture all of the technologies in the named end use that apply to the building types and fuel types included in the applicable baseline market. For example, if the building type is "single family homes" and the fuel type is specified as ["electricity", "natural gas"] then "all heating" will include all of the heating technologies for residential buildings that use electricity or natural gas.

**Residential -- Supply**

* heating

   * electricity: |tooltip| ASHP |chunk-b| air-source heat pump |close|, |tooltip| GSHP |chunk-b| ground-source heat pump |close|, boiler (electric)
   * natural gas: |tooltip| NGHP |chunk-b| air-source natural gas heat pump |close|, boiler (NG), furnace (NG)
   * distillate: boiler (distillate), furnace (distillate)
   * other fuel: resistance, furnace (kerosene), stove (wood), furnace (LPG)

* secondary heating

   * electricity: non-specific
   * natural gas: non-specific
   * distillate: non-specific
   * other fuel: secondary heating (wood), secondary heating (coal), secondary heating (kerosene), secondary heating (LPG)

* cooling

   * electricity: room AC, |tooltip| ASHP |chunk-b| air-source heat pump |close|, |tooltip| GSHP |chunk-b| ground-source heat pump |close|, central AC
   * natural gas: |tooltip| NGHP |chunk-b| air-source natural gas heat pump |close|

* water heating

   * electricity: electric WH, solar WH
   * natural gas: ``null``
   * distillate: ``null``
   * other fuel: ``null``

* cooking

   * all fuel types: ``null``

* drying

   * all fuel types: ``null``

* lighting

+-------------------+---------------------------------+-------------------------------+--------------------------+
|                   |                                        Bulb Type                                           |
+                   +---------------------------------+-------------------------------+--------------------------+
| Fixture Type      |      incandescent/halogen       |          fluorescent          |            LED           |
+===================+=================================+===============================+==========================+
| general service   | general service (incandescent)  | general service (CFL)         | general service (LED)    |
+-------------------+---------------------------------+-------------------------------+--------------------------+
| reflector         | reflector (incandescent) |br|   | reflector (CFL)               | reflector (LED)          |
|                   | reflector (halogen)             |                               |                          |
+-------------------+---------------------------------+-------------------------------+--------------------------+
| linear fixture    |                                 | linear fluorescent (T-8) |br| | linear fluorescent (LED) |
|                   |                                 | linear fluorescent (T-12)     |                          |
+-------------------+---------------------------------+-------------------------------+--------------------------+
| exterior          | external (incandescent) |br|    | external (CFL)                | external (LED)           |
|                   | external (high pressure sodium) |                               |                          |
+-------------------+---------------------------------+-------------------------------+--------------------------+

* refrigeration: ``null``

* fans and pumps: ``null``

* computers: desktop PC, laptop PC, network equipment, monitors

* TVs: home theater & audio, set top box, video game consoles, DVD, TV

* other (grid electric): dishwasher, other MELs, clothes washing, freezers

**Residential -- Demand**

roof, wall, infiltration, ground, windows solar, windows conduction, equipment gain, people gain

**Commercial -- Supply**

* heating

   * electricity: |tooltip| electric_res-heat |chunk-b| electric resistance heat |close|, |tooltip| comm_GSHP-heat |chunk-b| commercial ground-source heat pump |close|, |tooltip| rooftop_ASHP-heat |chunk-b| rooftop air-source heat pump |close|, |tooltip| elec_boiler |chunk-b| electric boiler |close|
   * natural gas: |tooltip| gas_eng-driven_RTHP-heat |chunk-b| natural gas engine-driven rooftop heat pump |close|, |tooltip| res_type_gasHP-heat |chunk-b| residential-style natural gas heat pump |close|, gas_boiler, gas_furnace
   * distillate: oil_boiler, oil_furnace

* cooling

   * electricity: rooftop_AC, scroll_chiller, res_type_central_AC, reciprocating_chiller, |tooltip| comm_GSHP-cool |chunk-b| commercial ground-source heat pump |close|, centrifugal_chiller, |tooltip| rooftop_ASHP-cool |chunk-b| rooftop air-source heat pump |close|, wall-window_room_AC, screw_chiller
   * natural gas: |tooltip| gas_eng-driven_RTAC |chunk-b| natural gas engine-driven rooftop AC |close|, gas_chiller, |tooltip| res_type_gasHP-cool |chunk-b| residential-style natural gas heat pump |close|, |tooltip| gas_eng-driven_RTHP-cool |chunk-b| natural gas engine-driven rooftop heat pump |close|

* ventilation: |tooltip| CAV_Vent |chunk-b| constant air volume ventilation system |close|, |tooltip| VAV_Vent |chunk-b| variable air volume ventilation system |close|

* water heating

   * electricity: Solar water heater, HP water heater, elec_booster_water_heater, elec_water_heater
   * natural gas: gas_water_heater, gas_instantaneous_WH, gas_booster_WH
   * distillate: oil_water_heater

* lighting

.. tip::

   For linear fluorescent bulbs, the specification is given in the form FxTy, where x represents the wattage of the bulb and y indicates the diameter of the bulb. SR = full spectrum, HE = high efficiency, ES = energy saving.

+---------------------+-------------------------+--------------------------+-------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------+
|                     |                                        Bulb Type                                                                                                                                                                                                               |
+                     +-------------------------+--------------------------+-------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------+
| Fixture Type        |  incandescent/halogen   |      fluorescent         |                                       HID                                           |                                                       LED                                                           |
+=====================+=========================+==========================+=====================================================================================+=====================================================================================================================+
| general service     | 72W incand |br|         | 23W CFL |br|             |                                                                                     | LED Edison |br|                                                                                                     |
|                     | 100W incand |br|        | 26W CFL |br|             |                                                                                     |                                                                                                                     |
|                     | 70W HIR PAR-38 |br|     |                          |                                                                                     |                                                                                                                     |
|                     | 90W Halogen PAR-38 |br| |                          |                                                                                     |                                                                                                                     |
|                     | 90W Halogen Edison |br| |                          |                                                                                     |                                                                                                                     |
+---------------------+-------------------------+--------------------------+-------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------+
| linear fixture      |                         | F28T5 |br|               |                                                                                     | LED T8                                                                                                              |
|                     |                         | F28T8 HE |br|            |                                                                                     |                                                                                                                     |
|                     |                         | F28T8 HE w/ OS |br|      |                                                                                     |                                                                                                                     |
|                     |                         | F28T8 HE w/ SR |br|      |                                                                                     |                                                                                                                     |
|                     |                         | F28T8 HE w/ OS & SR |br| |                                                                                     |                                                                                                                     |
|                     |                         | F32T8 |br|               |                                                                                     |                                                                                                                     |
|                     |                         | F96T8 |br|               |                                                                                     |                                                                                                                     |
|                     |                         | F96T8 HE |br|            |                                                                                     |                                                                                                                     |
|                     |                         | F34T12 |br|              |                                                                                     |                                                                                                                     |
|                     |                         | F96T12 mag |br|          |                                                                                     |                                                                                                                     |
|                     |                         | F96T12 ES mag |br|       |                                                                                     |                                                                                                                     |
|                     |                         | T8 F32 EEMag (e) |br|    |                                                                                     |                                                                                                                     |
+---------------------+-------------------------+--------------------------+-------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------+
| low bay             |                         | F96T8 HO_LB |br|         | |tooltip| HPS 70_LB |chunk-b| high pressure sodium 70W low bay lamp |close| |br|    | |tooltip| LED_LB |chunk-b| LED low bay lamp |close| |br|                                                            |
|                     |                         | 2L F54T5HO LB |br|       | |tooltip| HPS 100_LB |chunk-b| high pressure sodium 100W low bay lamp |close| |br|  | |tooltip| LED 100 HPS_LB |chunk-b| LED drop-in replacement for 100W high pressure sodium low bay lamp |close| |br|  |
|                     |                         |                          | |tooltip| MH 175_LB |chunk-b| metal halide 175W low bay lamp |close| |br|           |                                                                                                                     |
|                     |                         |                          | |tooltip| MV 175_LB |chunk-b| mercury vapor 175W low bay lamp |close| |br|          |                                                                                                                     |
+---------------------+-------------------------+--------------------------+-------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------+
| high bay            |                         | F54T5 HO_HB |br|         | |tooltip| HPS 150_HB |chunk-b| high pressure sodium 150W high bay lamp |close| |br| | |tooltip| LED_HB |chunk-b| LED high bay lamp |close| |br|                                                           |
|                     |                         | F96T8 HO_HB |br|         | |tooltip| MH 250_HB |chunk-b| metal halide 250W high bay lamp |close| |br|          | |tooltip| LED 150 HPS_HB |chunk-b| LED drop-in replacement for 150W high pressure sodium high bay lamp |close| |br| |
|                     |                         |                          | |tooltip| MH 400_HB |chunk-b| metal halide 400W high bay lamp |close| |br|          |                                                                                                                     |
|                     |                         |                          | |tooltip| MV 400_HB |chunk-b| mercury vapor 400W high bay lamp |close| |br|         |                                                                                                                     |
+---------------------+-------------------------+--------------------------+-------------------------------------------------------------------------------------+---------------------------------------------------------------------------------------------------------------------+

* refrigeration: Reach-in_freezer, Supermkt_compressor_rack, Walk-In_freezer, Supermkt_display_case, Walk-In_refrig, Reach-in_refrig, Supermkt_condenser, Ice_machine, Vend_Machine, |tooltip| Bevrg_Mchndsr |chunk-b| beverage merchandiser |close|

* cooking

   * electricity: |tooltip| Range, Electric-induction, 4 burner, oven, 1 |chunk-b| electric range with induction-style cooktop |close|; |tooltip| Range, Electric, 4 burner, oven, 11-inch gr |chunk-b| electric range with standard coil or ceramic cooktop |close|
   * natural gas: |tooltip| Range, Gas, 4 powered burners, convect. oven |chunk-b| natural gas range with convection oven |close| ; |tooltip| Range, Gas, 4 burner, oven, 11-inch griddle |chunk-b| natural gas range with standard oven |close|

.. * PCs
.. * non-PC office equipment
.. * MELs: lab fridges and freezers, non-road electric vehicles, kitchen ventilation, escalators, distribution transformers, large video displays, video displays, elevators, laundry, medical imaging, coffee brewers, fume hoods, security systems

**Commercial -- Demand**

roof, wall, ground, floor, infiltration, ventilation, windows conduction, windows solar, lighting gain, equipment gain, people gain, other heat gain

.. _ecm-performance-units:
.. _ecm-energy-efficiency-units:

Energy efficiency units
-----------------------

**Residential -- Equipment (Supply)**

   * Heating

     * Boilers and furnaces (AFUE)
     * All other equipment types (COP)

   * Cooling (COP)
   * Water heating (EF)
   * Refrigeration (kWh/yr)
   * Cooking

     * Electricity (kWh/yr)
     * Natural gas (TEff)
     * LPG (TEff)

   * Drying (EF)
   * Lighting (lm/W)
   * Other (grid electric)

     * Clothes washing (kWh/cycle)
     * Dishwasher (EF)
     * Freezers (kWh/yr)

..   * Ceiling fan (W)
   * Fans & pumps (HP/W)
   * TVs (W)
   * Computers (W)
   * Secondary heating
      * Electricity (COP)
      * All other fuel types (AFUE)

**Commercial -- Equipment (Supply)**

   * Heating (BTU out/BTU in)
   * Cooling (BTU out/BTU in)
   * Water heating (BTU out/BTU in)
   * Ventilation (cfm-hr/BTU in)
   * Cooking (BTU out/BTU in)
   * Lighting (lm/W)
   * Refrigeration (BTU out/BTU in)

..   * PCs
..   * Non-PC office equipment
..   * MELs

**Residential and Commercial -- Sensors and Controls (Supply)**

   * All sensors and controls ECMs (relative savings (constant) *or* relative savings (dynamic))

**Residential and Commercial -- Envelope Components (Demand)**

   * Windows conduction (R value)
   * Windows solar (SHGC)
   * Wall, roof, and ground (R value)
   * Infiltration

     * Residential (ACH)
     * Commercial (CFM/ft^2 @ 0.3 in. w.c.)

.. _ecm-installed-cost-units:

Installed cost units
--------------------

**Residential -- Equipment (Supply)**

   * All equipment except sensors and controls ($/unit)

**Commercial -- Equipment (Supply)**

   * Ventilation ($/1000 CFM)
   * Lighting ($/1000 lm)
   * Cooking ($/ft^2 floor)
   * Heating, cooling, water heating, and refrigeration ($/kBtu/h service, e.g., $/kBtu/h heating)   

**Residential and Commercial -- Sensors and Controls (Supply)**

   * Sensor networks ($/node)
   * Occupant-centered controls ($/occupant)
   * All other controls ECMs ($/ft^2 floor)

**Residential and Commercial -- Envelope Components (Demand)**

   * Windows ($/ft^2 glazing)
   * Walls ($/ft^2 wall)
   * Roof ($/ft^2 roof)
   * Floor/ground ($/ft^2 footprint)


.. _json-schema:

ECM JSON schema
---------------

This section outlines the elements of a JSON file that defines an energy conservation measure (ECM) -- a technology included for analysis with Scout. More details about ECMs can be found in the :ref:`Analysis Approach <analysis-step-1>` and :ref:`Tutorial 1 <tuts-1>` sections.

Each sub-section corresponds to a single key in the JSON. The details provided for each key include the parent and child fields, valid data types, a brief description of the field, and one or more illustrative examples. Parent keys are above and child keys are below the current key in the hierarchy of a JSON file. ::

   {"parent key": {
      "current key": {
         "child key": "value"}}}

The data type "none" indicates that ``null`` is a valid value for that key. The parent "root" indicates that it is at the top of the hierarchy, that is, there are no parents for that key.

.. _json-name:

name
~~~~

* **Parents:** root
* **Children:** none
* **Type:** string

A descriptive name of the technology defined in the ECM. If possible, the name length should be kept to under 55 characters including spaces. The name should not be shared with any other ECM. ::

   {...
    "name": "Residential Natural Gas HPWH",
    ...}

.. _json-climate_zone:

climate_zone
~~~~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string, list

Either a single climate zone or list of climate zones to which the ECM applies. The climate zone strings must come from the list of :ref:`valid entries <ecm-baseline_climate-zone>` in the :ref:`ecm-def-reference`. ::

   {...
    "climate_zone": ["AIA_CZ2", "AIA_CZ3"],
    ...}

.. _json-bldg_type:

bldg_type
~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string, list

A single building type or a list of residential and/or commercial building types in which the ECM could be installed. The building types specified must be from the list of :ref:`valid entries <ecm-baseline_building-type>` in the :ref:`ecm-def-reference`. ::

   {...
    "bldg_type": "all residential",
    ...}

.. _json-structure_type:

structure_type
~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string, list

The structure type indicates whether the technology described by the ECM is suitable for application in new construction, completed/existing buildings, or both. :ref:`Valid structure types <ecm-baseline_structure-type>` are  ``new``, ``existing``, or ``all``, respectively. ::

   {...
    "structure_type": "new",
    ...}

.. tip::

   If the ECM technology can be applied to both new construction and existing buildings but with differing energy efficiency, installed costs, and/or service life, those differing values should be specified explicitly in the :ref:`json-energy_efficiency`, :ref:`json-installed_cost`, and/or :ref:`json-product_lifetime` fields. This specification method is explained in the :ref:`ecm-features-detailed-input` section.

.. _json-fuel_type:

fuel_type
~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string, list

The fuel type(s) should correspond to the energy source(s) used by the technology described in the ECM, and can be specified as a string for a single fuel type or as a list to include multiple fuel types. The fuel type(s) should be drawn from the :ref:`list of valid fuel types <ecm-baseline_fuel-type>`. ::

   {...
    "fuel_type": "electricity",
    ...}

.. tip::

   If the ECM describes a technology that does not use energy directly but affects the energy use of the building, i.e., windows and building envelope, the fuel type should be specified as ``all``.

.. tip::

   If :ref:`fuel switching <json-fuel_switch_to>` is included in the ECM definition, then the fuel types listed should include all fuel types corresponding to equipment or technologies that can be supplanted by the technology described in the ECM. Further information about using the :ref:`json-fuel_switch_to` field is in the :ref:`ecm-features-multiple-fuel-types` section.

.. _json-end_use:

end_use
~~~~~~~

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
~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** int, none

The market entry year specifies the year that the ECM entered or is expected to enter the market. The year should be given as an integer in the format YYYY. ``null`` is also an acceptable value for the market entry year, and is interpreted to mean that the ECM is available in the first year simulated in Scout. ::

   {...
    "market_entry_year": 2019,
    ...}

.. _json-market_entry_year_source:

market_entry_year_source
~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** int, none

The market exit year indicates the final year that the technology described in the ECM is available for purchase. The year should be formatted as YYYY. ``null`` is also an acceptable market exit year value, and is interpreted as the technology remaining available through the final year simulated in Scout. ::

   {...
    "market_exit_year": null,
    ...}

.. _json-market_exit_year_source:

market_exit_year_source
~~~~~~~~~~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** :ref:`json-notes`, :ref:`json-source_data`
* **Type:** dict, none

The market exit year source indicates the original source for the exit year specified for the ECM. The field is  formatted identically to the :ref:`json-market_entry_year_source` field. If the market exit year is ``null``, the source can also be given as ``null`` without the dict. ::

   {...
    "market_exit_year_source": null,
    ...}

.. _json-energy_efficiency:

energy_efficiency
~~~~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** (optional) values of :ref:`json-climate_zone`, :ref:`json-bldg_type`, :ref:`json-structure_type`, :ref:`json-end_use`
* **Type:** float, dict

The energy efficiency value(s) define the energy performance of the technology being described by the ECM. The numeric values should be given such that they correspond to the required units given in the :ref:`json-energy_efficiency_units` field. ::

   {...
    "energy_efficiency": 2.8,
    ...}

If it is appropriate for the technology described by the ECM, the energy efficiency can be specified more precisely using one or more of the optional child fields. The values should then be reported in a dict where the keys correspond to the applicable child fields. If multiple levels of specificity are desired, the hierarchy of the nested keys can be chosen for convenience. Additional information regarding this specification method can be found in the :ref:`ecm-features-detailed-input` section. ::

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
~~~~~~~~~~~~~~~~~~~~~~~

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

.. Energy efficiency can also be specified with relative units, as described in the :ref:`ecm-features-relative-savings` section, using EnergyPlus data, explained in the :ref:`ecm-features-energyplus` section, or with probability distributions on some or all values, detailed in the :ref:`ecm-features-distributions` section.

Energy efficiency can also be specified with relative units, as described in the :ref:`ecm-features-relative-savings` section, or with probability distributions on some or all values, detailed in the :ref:`ecm-features-distributions` section.

.. _json-energy_efficiency_source:

energy_efficiency_source
~~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~

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

The installed costs can be specified with detail beyond what is shown using the additional optional child field types, as illustrated for the :ref:`json-energy_efficiency` field. The order of the hierarchy for the child fields is at the user's discretion. Further information about detailed structures for specifying the installed cost is in the :ref:`ecm-features-detailed-input` section.

.. _json-cost_units:

cost_units
~~~~~~~~~~

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
~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** (optional) values from :ref:`json-bldg_type`
* **Type:** int, dict

The product lifetime is the expected usable life of the technology described by the ECM in years. The lifetime value should be an integer greater than 0. ::

   {...
    "product_lifetime": 3,
    ...}

The product lifetime can be specified by building type, if appropriate for the ECM. The building types are the keys in the lifetime dict and should match the types listed in the :ref:`json-bldg_type` field. Additional information regarding this specification method can be found in the :ref:`ecm-features-detailed-input` section. ::

   {...
    "product_lifetime": {
      "single family home": 10,
      "small office": 7,
      "mercantile/service": 6},
    ...}

.. _json-product_lifetime_units:

product_lifetime_units
~~~~~~~~~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string

The product lifetime units are years. This field is included largely to ensure that the correct units were used when specifying the product lifetime. ::

   {...
    "product_lifetime_units": "years",
    ...}

.. _json-product_lifetime_source:

product_lifetime_source
~~~~~~~~~~~~~~~~~~~~~~~

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
~~~~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string

This field is used to specify whether the technology described by the ECM could be substituted for a component already installed in buildings, such as an electric cold-climate heat pump being substituted for an electric furnace and central AC system, or enhance the efficiency of an existing component, such as a window film applied to an existing window or an HVAC controls system that improves the efficiency of existing HVAC equipment. The measure type is then either ``"full service"`` or ``"add-on"``, respectively. Supplementary information and illustrative examples of the use of this field are available in the :ref:`ecm-features-measure-type` section. ::

   {...
    "measure_type": "full service",
    ...}

.. _json-fuel_switch_to:

fuel_switch_to
~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string, list

If the ECM is intended to replace comparable building components that use one of multiple fuel types, such as both electric and natural gas water heaters, this field should identify the fuel type of the technology described by the ECM. The fuel type should match exactly with one of the :ref:`fuel types <ecm-baseline_fuel-type>` listed in the :ref:`ecm-def-reference`. If the value of :ref:`json-fuel_type` is a single fuel type that matches the technology described by the ECM, this filed can be given as ``null``. Additional information regarding the use of this field is available in the :ref:`ecm-features-multiple-fuel-types` section. ::

   {...
    "fuel_switch_to": "natural gas",
    ...}

.. _json-market_scaling_fractions:

market_scaling_fractions
~~~~~~~~~~~~~~~~~~~~~~~~

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
      "new": 1,
      "existing": 0.43},
    ...}

Further information regarding the use of market scaling fractions is in the :ref:`ecm-features-market-scaling-fractions` section.

.. _json-market_scaling_fractions_source:

market_scaling_fractions_source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* **Parents:** root
* **Children:** :ref:`json-title`, :ref:`json-author`, :ref:`json-organization`, :ref:`json-year`, :ref:`json-pages`, :ref:`json-URL`, :ref:`json-fraction_derivation`; none
* **Type:** dict, string, none

The market scaling fractions source identifies the sources that were used to determine the market scaling fraction, including the exact method for deriving the fraction. If the :ref:`json-market_scaling_fractions` field is ``null``, the source should also be specified as ``null``. ::

   {...
    "market_scaling_fractions_source": {
      "title": "Energy Savings Forecast for Solid-State Lighting in General Illumination Applications",
      "author": "Navigant Consulting; Julie Penning, Kelsey Stober, Victor Taylor, Mary Yamada",
      "organization": "U.S. Department of Energy",
      "year": 2016,
      "pages": 23,
      "URL": "http://energy.gov/sites/prod/files/2016/09/f33/energysavingsforecast16_2.pdf"},
      "fraction_derivation": "In Figure 4.4, sum of 2015 data for LED - Connected Lighting, LED - Controls, and Conventional Lighting - Controls."},
    ...}

Multiple scaling fraction values can share the same source so long as the calculation procedure for all of the values is provided in the :ref:`json-fraction_derivation` field, however, no more than one source is allowed for each scaling fraction value. If scaling fractions correspond to different sources, the source information can be given in a nested dict with the same top level structure as the scaling fractions themselves. If the market scaling fraction is set to 1 for one of the keys in the nested structure, the source information can be given as a string explaining any assumptions. ::

   {...
    "market_scaling_fractions_source": {
      "new": "Assumes that all new commercial buildings are constructed with BAS",
      "existing": {
         "title": "CBECS 2012 - Table B1. Summary table: total and means of floorspace, number of workers, and hours of operation, 2012",
         "author": "U.S. Energy Information Administration (EIA)",
         "organization": "U.S. Energy Information Administration (EIA)",
         "year": "2012",
         "URL": "http://www.eia.gov/consumption/commercial/data/2012/bc/cfm/b1.cfm",
         "fraction_derivation": "37051 ft^2 floor of commercial buildings with BAS / 87093 ft^2 floor total commercial buildings"}},
    ...}

.. _json-_description:

_description
~~~~~~~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string

A one to two sentence description of the ECM. If the ECM is prospective, i.e., describing a technology still being researched, the description should include URLs or other identifying information for additional references that contain further details about the technology. ::

   {...
    "_description": "LED troffers for commercial modular dropped ceiling grids that are a replacement for the entire troffer luminaire for linear fluorescent bulbs, not a retrofit kit or linear LED bulbs that slot into existing troffers.",
    ...}

.. _json-_notes:

_notes
~~~~~~

* **Parents:** root
* **Children:** none
* **Type:** string

A text field that can be used for explanatory notes regarding the technologies that can be replaced by the ECM, any notable assumptions made in the specification of the ECM, or any other relevant information about the ECM that is not captured by any other field. ::

   {...
    "_notes": "Energy efficiency is specified for the luminaire, not the base lamp.",
    ...}

.. _json-_added_by:

_added_by
~~~~~~~~~

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
~~~~~~~~~~~

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
~~~~~

* **Parents:** :ref:`json-market_entry_year_source`, :ref:`json-market_exit_year_source`, :ref:`json-energy_efficiency_source`, :ref:`json-installed_cost_source`, :ref:`json-product_lifetime_source`
* **Children:** none
* **Type:** string

The notes field should include the exact location of the specific information used from the source(s) identified. The location information should include the table or figure number, and if the value is drawn from tabular data, the applicable row and column heading(s). The notes should also outline any calculations performed to convert from the values found in the source(s) to the value used in the ECM definition, including unit conversions and methods for combining multiple values (e.g., averaging, market share-weighted averaging). Any other assumptions regarding the derivation of the related value in the ECM definition should also be included. ::

   {...
    "notes": "Value drawn from Table 1 for the Ventless or Vented Electric, Standard product type. For clothes drying, the expected units of EF (Energy Factor) are equivalent to lbs/kWh.",
    ...}

.. _json-fraction_derivation:

fraction_derivation
~~~~~~~~~~~~~~~~~~~

* **Parents:** :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** string

For the market scaling fractions, this field should provide a description of how the values were calculated. The description should have enough detail for another user to be able to easily repeat the calculations. ::

   {...
    "fraction_derivation": "Sum of 2015 data for LED - Connected Lighting, LED - Controls, and Conventional Lighting - Controls.",
    ...}

.. _json-source_data:

source_data
~~~~~~~~~~~

* **Parents:** :ref:`json-market_entry_year_source`, :ref:`json-market_exit_year_source`, :ref:`json-energy_efficiency_source`, :ref:`json-installed_cost_source`, :ref:`json-product_lifetime_source`
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
~~~~~

* **Parents:** :ref:`json-source_data`, :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** string

The title of the source document. ::

   {...
    "title": "ENERGY STAR Program Requirements: Product Specification for Clothes Dryers",
    ...}

.. _json-author:

author
~~~~~~

* **Parents:** :ref:`json-source_data`, :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** string, none

The names of the author(s) of the publication, if any are identified. If no authors are listed, ``null`` or an empty string are acceptable values for this field if no authors are identified by name in the source. ::

   {...
    "author": null,
    ...}

.. _json-organization:

organization
~~~~~~~~~~~~

* **Parents:** :ref:`json-source_data`, :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** string

The journal publication, organization, or other entity that released the source article, report, specification, test result, or other reference. ::

   {...
    "organization": "U.S. Environmental Protection Agency",
    ...}

.. _json-year:

year
~~~~

* **Parents:** :ref:`json-source_data`, :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** int

The year that the source was published or last updated. ::

   {...
    "year": 2014,
    ...}

.. _json-pages:

pages
~~~~~

* **Parents:** :ref:`json-source_data`, :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** int, string, none

The page number(s) of the information in the source document, if applicable. If the source is not divided into pages, this entry can have the value ``null``. If the relevant information can be found on a single page, the page number should be given as an integer. If the information is divided across several pages or a range of pages, the page numbers should be given as a string. ::

   {...
    "pages": "24, 26-29, 37",
    ...}

.. _json-URL:

URL
~~~

* **Parents:** :ref:`json-source_data`, :ref:`json-market_scaling_fractions_source`
* **Children:** none
* **Type:** string

The URL where the source can be found on the internet. The URL should point directly to the original source file, if possible. ::

   {...
    "URL": "https://www.energystar.gov/sites/default/files/specs//ENERGY%20STAR%20Final%20Version%201%200%20Clothes%20Dryers%20Program%20Requirements.pdf",
    ...}

.. _json-ecm-author-name:

name
~~~~

* **Parents:** :ref:`json-_updated_by`, :ref:`json-_added_by`,
* **Children:** none
* **Type:** string

The name of the author of the initial definition or latest changes to the ECM. ::

   {...
    "name": "Maureen Adams",
    ...}

.. _json-ecm-author-organization:

organization
~~~~~~~~~~~~

* **Parents:** :ref:`json-_updated_by`, :ref:`json-_added_by`,
* **Children:** none
* **Type:** string

The organization or employer with which the :ref:`named <json-ecm-author-name>` author is affiliated. ::

   {...
    "organization": "U.S. Department of Energy",
    ....}

.. _json-ecm-author-email:

email
~~~~~

* **Parents:** :ref:`json-_updated_by`, :ref:`json-_added_by`,
* **Children:** none
* **Type:** string

The email address of the :ref:`named <json-ecm-author-name>` author. ::

   {...
    "email": "james.clipper@ee.doe.gov",
    ...}

.. _json-ecm-author-timestamp:

timestamp
~~~~~~~~~

* **Parents:** :ref:`json-_updated_by`, :ref:`json-_added_by`,
* **Children:** none
* **Type:** string

The date and time at which the relevant changes were completed. The entry should be formatted as YYYY-MM-DD HH\:MM\:SS, with the time reported in 24-hour `Universal Coordinated Time (UTC)`_ if possible. ::

   {...
    "timestamp": "2014-03-27 14:36:18 UTC",
    ...}

.. _Universal Coordinated Time (UTC): http://www.nhc.noaa.gov/aboututc.shtml

.. rubric:: Footnotes

.. [#] The applicable baseline market is comprised of the |baseline-market| fields.