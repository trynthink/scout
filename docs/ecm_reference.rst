.. Substitutions
.. |ft2| replace:: ft\ :sup:`2`

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
   * Cooking ($/|ft2| floor)
   * Heating, cooling, water heating, and refrigeration ($/kBtu/h service, e.g., $/kBtu/h heating)   

**Residential and Commercial -- Sensors and Controls (Supply)**

   * Sensor networks ($/node)
   * Occupant-centered controls ($/occupant)
   * All other controls ECMs ($/|ft2| floor)

**Residential and Commercial -- Envelope Components (Demand)**

   * Windows ($/|ft2| glazing)
   * Walls ($/|ft2| wall)
   * Roof ($/|ft2| roof)
   * Floor/ground ($/|ft2| footprint)

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

**Residential and Commercial -- Envelope Components (Demand)**

   * Windows conduction (R value)
   * Windows solar (SHGC)
   * Wall, roof, and ground (R value)
   * Infiltration

     * Residential (ACH)
     * Commercial (CFM/ft^2 @ 0.3 in. w.c.)


