.. |br| raw:: html

   <br />

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

Climate Zone
~~~~~~~~~~~~

AIA_CZ1, AIA_CZ2, AIA_CZ3, AIA_CZ4, AIA_CZ5

Building Type
~~~~~~~~~~~~~

**Residential:** single family home, multi family home, mobile home

**Commercial:** assembly, education, food sales, food service, health care, lodging, large office, small office, mercantile/service, warehouse, other

Structure Type
~~~~~~~~~~~~~~

new, existing

Fuel Type
~~~~~~~~~

**Residential:** electricity, natural gas, distillate, other fuel

**Commercial:** electricity, natural gas, distillate

End Use
~~~~~~~

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

.. | PCs                     |      X      |             |            |
   +-------------------------+-------------+-------------+------------+
   | non-PC office equipment |      X      |             |            |
   +-------------------------+-------------+-------------+------------+
   | MELs                    |      X      |             |            |
   +-------------------------+-------------+-------------+------------+

Technology Type
~~~~~~~~~~~~~~~

supply, demand

Technology
~~~~~~~~~~

**Residential -- Supply**

* heating

   * electricity: ASHP, GSHP, boiler (electric)
   * natural gas: NGHP, boiler (NG), furnace (NG)
   * distillate: boiler (distillate), furnace (distillate)
   * other fuel: resistance, furnace (kerosene), stove (wood), furnace (LPG)

* secondary heating

   * electricity: non-specific
   * natural gas: non-specific
   * distillate: non-specific
   * other fuel: secondary heating (wood), secondary heating (coal), secondary heating (kerosene), secondary heating (LPG)

* cooling

   * electricity: room AC, ASHP, GSHP, central AC
   * natural gas: NGHP

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

roof, ground, windows solar, windows conduction, equipment gain, people gain, wall, infiltration

**Commercial -- Supply**

* heating

   * electricity: electric_res-heat, comm_GSHP-heat, rooftop_ASHP-heat, elec_boiler
   * natural gas: gas_eng-driven_RTHP-heat, res_type_gasHP-heat, gas_boiler, gas_furnace
   * distillate: oil_boiler, oil_furnace

* cooling

   * electricity: rooftop_AC, scroll_chiller, res_type_central_AC, reciprocating_chiller, comm_GSHP-cool, centrifugal_chiller, rooftop_ASHP-cool, wall-window_room_AC, screw_chiller
   * natural gas: gas_eng-driven_RTAC, gas_chiller, res_type_gasHP-cool, gas_eng-driven_RTHP-cool

* ventilation: CAV_Vent, VAV_Vent

* water heating

   * electricity: Solar water heater, HP water heater, elec_booster_water_heater, elec_water_heater
   * natural gas: gas_water_heater, gas_instantaneous_WH, gas_booster_WH
   * distillate: oil_water_heater

* lighting

+---------------------+-------------------------+--------------------------+-----------------+---------------------+
|                     |                                        Bulb Type                                           |
+                     +-------------------------+--------------------------+-----------------+---------------------+
| Fixture Type        | incandescent/halogen    |      fluorescent         |       HID       |         LED         |
+=====================+=========================+==========================+=================+=====================+
| general service     | 72W incand |br|         | 23W CFL |br|             |                 | LED Edison |br|     |
|                     | 100W incand |br|        | 26W CFL |br|             |                 |                     |
|                     | 70W HIR PAR-38 |br|     |                          |                 |                     |
|                     | 90W Halogen PAR-38 |br| |                          |                 |                     |
|                     | 90W Halogen Edison |br| |                          |                 |                     |
+---------------------+-------------------------+--------------------------+-----------------+---------------------+
| linear fixture      |                         | F28T5 |br|               |                 | LED_T8              |
|                     |                         | F28T8 HE |br|            |                 |                     |
|                     |                         | F28T8 HE w/ OS |br|      |                 |                     |
|                     |                         | F28T8 HE w/ SR |br|      |                 |                     |
|                     |                         | F28T8 HE w/ OS & SR |br| |                 |                     |
|                     |                         | F32T8 |br|               |                 |                     |
|                     |                         | F96T8 |br|               |                 |                     |
|                     |                         | F96T8 HE |br|            |                 |                     |
|                     |                         | F34T12 |br|              |                 |                     |
|                     |                         | F96T12 mag |br|          |                 |                     |
|                     |                         | F96T12 ES mag |br|       |                 |                     |
|                     |                         | T8 F32 EEMag (e) |br|    |                 |                     |
+---------------------+-------------------------+--------------------------+-----------------+---------------------+
| low bay             |                         | F96T8 HO_LB |br|         | HPS 70_LB |br|  | LED_LB |br|         |
|                     |                         | 2L F54T5HO LB |br|       | HPS 100_LB |br| | LED 100 HPS_LB |br| |
|                     |                         |                          | MH 175_LB |br|  |                     |
|                     |                         |                          | MV 175_LB |br|  |                     |
+---------------------+-------------------------+--------------------------+-----------------+---------------------+
| high bay            |                         | F54T5 HO_HB |br|         | HPS 150_HB |br| | LED_HB |br|         |
|                     |                         | F96T8 HO_HB |br|         | MH 250_HB |br|  | LED 150 HPS_HB |br| |
|                     |                         |                          | MH 400_HB |br|  |                     |
|                     |                         |                          | MV 400_HB |br|  |                     |
+---------------------+-------------------------+--------------------------+-----------------+---------------------+

* refrigeration: Reach-in_freezer, Supermkt_compressor_rack, Walk-In_freezer, Supermkt_display_case, Walk-In_refrig, Reach-in_refrig, Supermkt_condenser, Ice_machine, Vend_Machine, Bevrg_Mchndsr

* cooking

   * electricity: Range, Electric-induction, 4 burner, oven, 1; Range, Electric, 4 burner, oven, 11-inch gr
   * natural gas: Range, Gas, 4 powered burners, convect. oven; Range, Gas, 4 burner, oven, 11-inch griddle

.. * PCs
.. * non-PC office equipment
.. * MELs: lab fridges and freezers, non-road electric vehicles, kitchen ventilation, escalators, distribution transformers, large video displays, video displays, elevators, laundry, medical imaging, coffee brewers, fume hoods, security systems

**Commercial -- Demand**

roof, ground, lighting gain, windows conduction, equipment gain, floor, infiltration, people gain, windows solar, ventilation, other heat gain, wall
