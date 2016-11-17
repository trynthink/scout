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

In some parts of the definition of an ECM, specific values must be entered for the ECM to be valid and successfully included in an analysis. In particular, the installed cost and performance units used must match exactly with the expected units for a given building sector, end use, and technology type. These units are defined by the EIA Annual Energy Outlook data used to define the baseline technology cost, performance, and lifetime.

.. _ecm-installed-cost-units:

Installed Cost Units
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

.. _ecm-performance-units:

Performance Units
-----------------

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

.. _ecm-applicable-baseline-market:

Applicable Baseline Market Options
----------------------------------

For each of the keys in the applicable baseline market definition, only specific entries are expected and allowable. This section outlines those acceptable entries for each of the keys.

For some keys, there are shorthand summary values that can be used when all or a large group of more specific values for that key apply. For example, if all of the climate zones should be included in the applicable baseline market, the value "all" can be specified instead of typing out each climate zone name in a list. These shorthand values are provided after the semi-colon in the lists below. Additional notes might also be provided to further clarify the different summary values available for a given key.

.. _ecm-baseline_climate-zone:

Climate Zone
~~~~~~~~~~~~

|tooltip| AIA_CZ1 |chunk-b| AIA Climate Zone 1 |close|, |tooltip| AIA_CZ2 |chunk-b| AIA Climate Zone 2 |close|, |tooltip| AIA_CZ3 |chunk-b| AIA Climate Zone 3 |close|, |tooltip| AIA_CZ4 |chunk-b| AIA Climate Zone 4 |close|, |tooltip| AIA_CZ5 |chunk-b| AIA Climate Zone 5 |close|; all

.. figure:: https://www.eia.gov/consumption/residential/reports/images/climatezone-lg.jpg

   Map of American Institute of Architects (AIA) climate zones for the continental U.S., Alaska, and Hawaii.

.. _ecm-baseline_building-type:

Building Type
~~~~~~~~~~~~~

**Residential:** single family home, multi family home, mobile home; all residential

**Commercial:** assembly, education, food sales, food service, health care, lodging, large office, small office, mercantile/service, warehouse, other; all commercial

.. note::

   "all" can be used instead of specifying both "all residential" and "all commercial" if all residential *and* commercial building types apply.

Structure Type
~~~~~~~~~~~~~~

new, existing

Fuel Type
~~~~~~~~~

**Residential:** electricity, natural gas, distillate, other fuel; all

**Commercial:** electricity, natural gas, distillate; all

.. _ecm-baseline_end-use:

End Use
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

Technology Type
~~~~~~~~~~~~~~~

supply, demand

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
