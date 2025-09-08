import pandas as pd

CDIV_MAX = 9
BLDG_MAX = 3
EUSES = ["HEAT", "COOL"]

# Segment -> category aggregation (intermediate keys)
RESSTOCK_SEGMENT_TO_CATEGORY = {
    # Windows / skylights
    "windows_conduction": "WIND_COND",
    "skylights_conduction": "WIND_COND",
    "windows_solar": "WIND_SOL",
    "skylights_solar": "WIND_SOL",
    # Roof / ceilings
    "roofs": "ROOF",
    "ceilings": "ROOF",
    # Walls / opaque
    "walls": "WALL",
    "foundation_walls": "WALL",
    "rim_joists": "WALL",
    "doors": "WALL",
    # Infiltration / ventilation
    "infiltration": "INFIL",
    "mechanical_ventilation": "INFIL",
    "natural_ventilation": "INFIL",
    # Ground contact
    "slabs": "GRND",
    "floors": "GRND",
    # Internal/equipment gains
    "internal_gains": "EQUIP",
    "internal_mass": "EQUIP",
    "lighting": "EQUIP",
    "whole_house_fan": "EQUIP",
    "ducts": "EQUIP",
}
# Final categories -> Scout component label strings expected downstream
CATEGORY_TO_SCOUT_COMPONENT = {
    "WIND_COND": "windows conduction",
    "WIND_SOL": "windows solar",
    "ROOF": "roof",
    "WALL": "wall",
    "INFIL": "infiltration",
    "PEOPLE": "people",
 # fixed 0
    "GRND": "ground",
    "EQUIP": "equipment",
}

CDIV_MAPPING = {
        "new england": 1,
        "middle atlantic": 2,
        "east north central": 3,
        "west north central": 4,
        "south atlantic": 5,
        "east south central": 6,
        "west south central": 7,
        "mountain": 8,
        "pacific": 9,
    }

BLDG_MAPPING = {
   '50 or more Unit': 'multi family home',
   'Single-Family Detached': 'single family home',
   'Single-Family Attached': 'single family home',
   'Mobile Home': 'mobile home',
   '20 to 49 Unit': 'multi family home',
   '5 to 9 Unit': 'multi family home',
   '3 or 4 Unit': 'multi family home',
   '2 Unit': 'multi family home',
   '10 to 19 Unit': 'multi family home',
   'nan': None
}

BLDG_CODE = {
    'single family home': 1,
    'multi family home': 2,
    'mobile home': 3,
}

ALL_COLS = ['Unnamed: 0',
'building_id',
'job_id',
'started_at',
'completed_at',
'completed_status',
'apply_upgrade.applicable',
'apply_upgrade.upgrade_name',
'apply_upgrade.reference_scenario',
'build_existing_model.ahs_region',
'build_existing_model.aiannh_area',
'build_existing_model.applicable',
'build_existing_model.area_median_income',
'build_existing_model.ashrae_iecc_climate_zone_2004',
'build_existing_model.ashrae_iecc_climate_zone_2004_2_a_split',
'build_existing_model.bathroom_spot_vent_hour',
'build_existing_model.bedrooms',
'build_existing_model.building_america_climate_zone',
'build_existing_model.cec_climate_zone',
'build_existing_model.ceiling_fan',
'build_existing_model.census_division',
'build_existing_model.census_division_recs',
'build_existing_model.census_region',
'build_existing_model.city',
'build_existing_model.clothes_dryer',
'build_existing_model.clothes_washer',
'build_existing_model.clothes_washer_presence',
'build_existing_model.cooking_range',
'build_existing_model.cooling_setpoint',
'build_existing_model.cooling_setpoint_has_offset',
'build_existing_model.cooling_setpoint_offset_magnitude',
'build_existing_model.cooling_setpoint_offset_period',
'build_existing_model.corridor',
'build_existing_model.county',
'build_existing_model.county_and_puma',
'build_existing_model.dehumidifier',
'build_existing_model.dishwasher',
'build_existing_model.door_area',
'build_existing_model.doors',
'build_existing_model.ducts',
'build_existing_model.eaves',
'build_existing_model.electric_vehicle',
'build_existing_model.federal_poverty_level',
'build_existing_model.generation_and_emissions_assessment_region',
'build_existing_model.geometry_attic_type',
'build_existing_model.geometry_building_horizontal_location_mf',
'build_existing_model.geometry_building_horizontal_location_sfa',
'build_existing_model.geometry_building_level_mf',
'build_existing_model.geometry_building_number_units_mf',
'build_existing_model.geometry_building_number_units_sfa',
'build_existing_model.geometry_building_type_acs',
'build_existing_model.geometry_building_type_height',
'build_existing_model.geometry_building_type_recs',
'build_existing_model.geometry_floor_area',
'build_existing_model.geometry_floor_area_bin',
'build_existing_model.geometry_foundation_type',
'build_existing_model.geometry_garage',
'build_existing_model.geometry_stories',
'build_existing_model.geometry_stories_low_rise',
'build_existing_model.geometry_story_bin',
'build_existing_model.geometry_wall_exterior_finish',
'build_existing_model.geometry_wall_type',
'build_existing_model.has_pv',
'build_existing_model.heating_fuel',
'build_existing_model.heating_setpoint',
'build_existing_model.heating_setpoint_has_offset',
'build_existing_model.heating_setpoint_offset_magnitude',
'build_existing_model.heating_setpoint_offset_period',
'build_existing_model.holiday_lighting',
'build_existing_model.hot_water_distribution',
'build_existing_model.hot_water_fixtures',
'build_existing_model.household_has_tribal_persons',
'build_existing_model.hvac_cooling_efficiency',
'build_existing_model.hvac_cooling_partial_space_conditioning',
'build_existing_model.hvac_cooling_type',
'build_existing_model.hvac_has_ducts',
'build_existing_model.hvac_has_shared_system',
'build_existing_model.hvac_has_zonal_electric_heating',
'build_existing_model.hvac_heating_efficiency',
'build_existing_model.hvac_heating_type',
'build_existing_model.hvac_heating_type_and_fuel',
'build_existing_model.hvac_secondary_heating_efficiency',
'build_existing_model.hvac_secondary_heating_type_and_fuel',
'build_existing_model.hvac_shared_efficiencies',
'build_existing_model.hvac_system_is_faulted',
'build_existing_model.hvac_system_single_speed_ac_airflow',
'build_existing_model.hvac_system_single_speed_ac_charge',
'build_existing_model.hvac_system_single_speed_ashp_airflow',
'build_existing_model.hvac_system_single_speed_ashp_charge',
'build_existing_model.income',
'build_existing_model.income_recs_2015',
'build_existing_model.income_recs_2020',
'build_existing_model.infiltration',
'build_existing_model.insulation_ceiling',
'build_existing_model.insulation_floor',
'build_existing_model.insulation_foundation_wall',
'build_existing_model.insulation_rim_joist',
'build_existing_model.insulation_roof',
'build_existing_model.insulation_slab',
'build_existing_model.insulation_wall',
'build_existing_model.interior_shading',
'build_existing_model.iso_rto_region',
'build_existing_model.lighting',
'build_existing_model.lighting_interior_use',
'build_existing_model.lighting_other_use',
'build_existing_model.location_region',
'build_existing_model.mechanical_ventilation',
'build_existing_model.misc_extra_refrigerator',
'build_existing_model.misc_freezer',
'build_existing_model.misc_gas_fireplace',
'build_existing_model.misc_gas_grill',
'build_existing_model.misc_gas_lighting',
'build_existing_model.misc_hot_tub_spa',
'build_existing_model.misc_pool',
'build_existing_model.misc_pool_heater',
'build_existing_model.misc_pool_pump',
'build_existing_model.misc_well_pump',
'build_existing_model.natural_ventilation',
'build_existing_model.neighbors',
'build_existing_model.occupants',
'build_existing_model.orientation',
'build_existing_model.overhangs',
'build_existing_model.plug_load_diversity',
'build_existing_model.plug_loads',
'build_existing_model.puma',
'build_existing_model.puma_metro_status',
'build_existing_model.pv_orientation',
'build_existing_model.pv_system_size',
'build_existing_model.radiant_barrier',
'build_existing_model.range_spot_vent_hour',
'build_existing_model.reeds_balancing_area',
'build_existing_model.refrigerator',
'build_existing_model.roof_material',
'build_existing_model.sample_weight',
'build_existing_model.simulation_control_run_period_begin_day_of_month',
'build_existing_model.simulation_control_run_period_begin_month',
'build_existing_model.simulation_control_run_period_calendar_year',
'build_existing_model.simulation_control_run_period_end_day_of_month',
'build_existing_model.simulation_control_run_period_end_month',
'build_existing_model.simulation_control_timestep',
'build_existing_model.solar_hot_water',
'build_existing_model.state',
'build_existing_model.tenure',
'build_existing_model.units_represented',
'build_existing_model.usage_level',
'build_existing_model.vacancy_status',
'build_existing_model.vintage',
'build_existing_model.vintage_acs',
'build_existing_model.water_heater_efficiency',
'build_existing_model.water_heater_fuel',
'build_existing_model.water_heater_in_unit',
'build_existing_model.weather_file_city',
'build_existing_model.weather_file_latitude',
'build_existing_model.weather_file_longitude',
'build_existing_model.window_areas',
'build_existing_model.windows',
'report_simulation_output.add_timeseries_dst_column',
'report_simulation_output.add_timeseries_utc_column',
'report_simulation_output.applicable',
'report_simulation_output.component_load_cooling_ceilings_m_btu',
'report_simulation_output.component_load_cooling_doors_m_btu',
'report_simulation_output.component_load_cooling_ducts_m_btu',
'report_simulation_output.component_load_cooling_floors_m_btu',
'report_simulation_output.component_load_cooling_foundation_walls_m_btu',
'report_simulation_output.component_load_cooling_infiltration_m_btu',
'report_simulation_output.component_load_cooling_internal_gains_m_btu',
'report_simulation_output.component_load_cooling_internal_mass_m_btu',
'report_simulation_output.component_load_cooling_lighting_m_btu',
'report_simulation_output.component_load_cooling_mechanical_ventilation_m_btu',
'report_simulation_output.component_load_cooling_natural_ventilation_m_btu',
'report_simulation_output.component_load_cooling_rim_joists_m_btu',
'report_simulation_output.component_load_cooling_roofs_m_btu',
'report_simulation_output.component_load_cooling_skylights_conduction_m_btu',
'report_simulation_output.component_load_cooling_skylights_solar_m_btu',
'report_simulation_output.component_load_cooling_slabs_m_btu',
'report_simulation_output.component_load_cooling_walls_m_btu',
'report_simulation_output.component_load_cooling_whole_house_fan_m_btu',
'report_simulation_output.component_load_cooling_windows_conduction_m_btu',
'report_simulation_output.component_load_cooling_windows_solar_m_btu',
'report_simulation_output.component_load_heating_ceilings_m_btu',
'report_simulation_output.component_load_heating_doors_m_btu',
'report_simulation_output.component_load_heating_ducts_m_btu',
'report_simulation_output.component_load_heating_floors_m_btu',
'report_simulation_output.component_load_heating_foundation_walls_m_btu',
'report_simulation_output.component_load_heating_infiltration_m_btu',
'report_simulation_output.component_load_heating_internal_gains_m_btu',
'report_simulation_output.component_load_heating_internal_mass_m_btu',
'report_simulation_output.component_load_heating_lighting_m_btu',
'report_simulation_output.component_load_heating_mechanical_ventilation_m_btu',
'report_simulation_output.component_load_heating_natural_ventilation_m_btu',
'report_simulation_output.component_load_heating_rim_joists_m_btu',
'report_simulation_output.component_load_heating_roofs_m_btu',
'report_simulation_output.component_load_heating_skylights_conduction_m_btu',
'report_simulation_output.component_load_heating_skylights_solar_m_btu',
'report_simulation_output.component_load_heating_slabs_m_btu',
'report_simulation_output.component_load_heating_walls_m_btu',
'report_simulation_output.component_load_heating_whole_house_fan_m_btu',
'report_simulation_output.component_load_heating_windows_conduction_m_btu',
'report_simulation_output.component_load_heating_windows_solar_m_btu',
'report_simulation_output.end_use_coal_clothes_dryer_m_btu',
'report_simulation_output.end_use_coal_fireplace_m_btu',
'report_simulation_output.end_use_coal_generator_m_btu',
'report_simulation_output.end_use_coal_grill_m_btu',
'report_simulation_output.end_use_coal_heating_heat_pump_backup_m_btu',
'report_simulation_output.end_use_coal_heating_m_btu',
'report_simulation_output.end_use_coal_hot_water_m_btu',
'report_simulation_output.end_use_coal_lighting_m_btu',
'report_simulation_output.end_use_coal_mech_vent_preheating_m_btu',
'report_simulation_output.end_use_coal_range_oven_m_btu',
'report_simulation_output.end_use_electricity_battery_m_btu',
'report_simulation_output.end_use_electricity_ceiling_fan_m_btu',
'report_simulation_output.end_use_electricity_clothes_dryer_m_btu',
'report_simulation_output.end_use_electricity_clothes_washer_m_btu',
'report_simulation_output.end_use_electricity_cooling_fans_pumps_m_btu',
'report_simulation_output.end_use_electricity_cooling_m_btu',
'report_simulation_output.end_use_electricity_dehumidifier_m_btu',
'report_simulation_output.end_use_electricity_dishwasher_m_btu',
'report_simulation_output.end_use_electricity_electric_vehicle_charging_m_btu',
'report_simulation_output.end_use_electricity_freezer_m_btu',
'report_simulation_output.end_use_electricity_generator_m_btu',
'report_simulation_output.end_use_electricity_heating_fans_pumps_m_btu',
'report_simulation_output.end_use_electricity_heating_heat_pump_backup_m_btu',
'report_simulation_output.end_use_electricity_heating_m_btu',
'report_simulation_output.end_use_electricity_hot_tub_heater_m_btu',
'report_simulation_output.end_use_electricity_hot_tub_pump_m_btu',
'report_simulation_output.end_use_electricity_hot_water_m_btu',
'report_simulation_output.end_use_electricity_hot_water_recirc_pump_m_btu',
'report_simulation_output.end_use_electricity_hot_water_solar_thermal_pump_m_btu',
'report_simulation_output.end_use_electricity_lighting_exterior_m_btu',
'report_simulation_output.end_use_electricity_lighting_garage_m_btu',
'report_simulation_output.end_use_electricity_lighting_interior_m_btu',
'report_simulation_output.end_use_electricity_mech_vent_m_btu',
'report_simulation_output.end_use_electricity_mech_vent_precooling_m_btu',
'report_simulation_output.end_use_electricity_mech_vent_preheating_m_btu',
'report_simulation_output.end_use_electricity_plug_loads_m_btu',
'report_simulation_output.end_use_electricity_pool_heater_m_btu',
'report_simulation_output.end_use_electricity_pool_pump_m_btu',
'report_simulation_output.end_use_electricity_pv_m_btu',
'report_simulation_output.end_use_electricity_range_oven_m_btu',
'report_simulation_output.end_use_electricity_refrigerator_m_btu',
'report_simulation_output.end_use_electricity_television_m_btu',
'report_simulation_output.end_use_electricity_well_pump_m_btu',
'report_simulation_output.end_use_electricity_whole_house_fan_m_btu',
'report_simulation_output.end_use_fuel_oil_clothes_dryer_m_btu',
'report_simulation_output.end_use_fuel_oil_fireplace_m_btu',
'report_simulation_output.end_use_fuel_oil_generator_m_btu',
'report_simulation_output.end_use_fuel_oil_grill_m_btu',
'report_simulation_output.end_use_fuel_oil_heating_heat_pump_backup_m_btu',
'report_simulation_output.end_use_fuel_oil_heating_m_btu',
'report_simulation_output.end_use_fuel_oil_hot_water_m_btu',
'report_simulation_output.end_use_fuel_oil_lighting_m_btu',
'report_simulation_output.end_use_fuel_oil_mech_vent_preheating_m_btu',
'report_simulation_output.end_use_fuel_oil_range_oven_m_btu',
'report_simulation_output.end_use_natural_gas_clothes_dryer_m_btu',
'report_simulation_output.end_use_natural_gas_fireplace_m_btu',
'report_simulation_output.end_use_natural_gas_generator_m_btu',
'report_simulation_output.end_use_natural_gas_grill_m_btu',
'report_simulation_output.end_use_natural_gas_heating_heat_pump_backup_m_btu',
'report_simulation_output.end_use_natural_gas_heating_m_btu',
'report_simulation_output.end_use_natural_gas_hot_tub_heater_m_btu',
'report_simulation_output.end_use_natural_gas_hot_water_m_btu',
'report_simulation_output.end_use_natural_gas_lighting_m_btu',
'report_simulation_output.end_use_natural_gas_mech_vent_preheating_m_btu',
'report_simulation_output.end_use_natural_gas_pool_heater_m_btu',
'report_simulation_output.end_use_natural_gas_range_oven_m_btu',
'report_simulation_output.end_use_propane_clothes_dryer_m_btu',
'report_simulation_output.end_use_propane_fireplace_m_btu',
'report_simulation_output.end_use_propane_generator_m_btu',
'report_simulation_output.end_use_propane_grill_m_btu',
'report_simulation_output.end_use_propane_heating_heat_pump_backup_m_btu',
'report_simulation_output.end_use_propane_heating_m_btu',
'report_simulation_output.end_use_propane_hot_water_m_btu',
'report_simulation_output.end_use_propane_lighting_m_btu',
'report_simulation_output.end_use_propane_mech_vent_preheating_m_btu',
'report_simulation_output.end_use_propane_range_oven_m_btu',
'report_simulation_output.end_use_wood_cord_clothes_dryer_m_btu',
'report_simulation_output.end_use_wood_cord_fireplace_m_btu',
'report_simulation_output.end_use_wood_cord_generator_m_btu',
'report_simulation_output.end_use_wood_cord_grill_m_btu',
'report_simulation_output.end_use_wood_cord_heating_heat_pump_backup_m_btu',
'report_simulation_output.end_use_wood_cord_heating_m_btu',
'report_simulation_output.end_use_wood_cord_hot_water_m_btu',
'report_simulation_output.end_use_wood_cord_lighting_m_btu',
'report_simulation_output.end_use_wood_cord_mech_vent_preheating_m_btu',
'report_simulation_output.end_use_wood_cord_range_oven_m_btu',
'report_simulation_output.end_use_wood_pellets_clothes_dryer_m_btu',
'report_simulation_output.end_use_wood_pellets_fireplace_m_btu',
'report_simulation_output.end_use_wood_pellets_generator_m_btu',
'report_simulation_output.end_use_wood_pellets_grill_m_btu',
'report_simulation_output.end_use_wood_pellets_heating_heat_pump_backup_m_btu',
'report_simulation_output.end_use_wood_pellets_heating_m_btu',
'report_simulation_output.end_use_wood_pellets_hot_water_m_btu',
'report_simulation_output.end_use_wood_pellets_lighting_m_btu',
'report_simulation_output.end_use_wood_pellets_mech_vent_preheating_m_btu',
'report_simulation_output.end_use_wood_pellets_range_oven_m_btu',
'report_simulation_output.energy_use_net_m_btu',
'report_simulation_output.energy_use_total_m_btu',
'report_simulation_output.fuel_use_coal_total_m_btu',
'report_simulation_output.fuel_use_electricity_net_m_btu',
'report_simulation_output.fuel_use_electricity_total_m_btu',
'report_simulation_output.fuel_use_fuel_oil_total_m_btu',
'report_simulation_output.fuel_use_natural_gas_total_m_btu',
'report_simulation_output.fuel_use_propane_total_m_btu',
'report_simulation_output.fuel_use_wood_cord_total_m_btu',
'report_simulation_output.fuel_use_wood_pellets_total_m_btu',
'report_simulation_output.hot_water_clothes_washer_gal',
'report_simulation_output.hot_water_dishwasher_gal',
'report_simulation_output.hot_water_distribution_waste_gal',
'report_simulation_output.hot_water_fixtures_gal',
'report_simulation_output.hvac_capacity_cooling_btu_h',
'report_simulation_output.hvac_capacity_heat_pump_backup_btu_h',
'report_simulation_output.hvac_capacity_heating_btu_h',
'report_simulation_output.hvac_design_load_cooling_latent_ducts_btu_h',
'report_simulation_output.hvac_design_load_cooling_latent_infiltration_ventilation_btu_h',
'report_simulation_output.hvac_design_load_cooling_latent_internal_gains_btu_h',
'report_simulation_output.hvac_design_load_cooling_latent_total_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_ceilings_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_doors_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_ducts_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_floors_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_infiltration_ventilation_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_internal_gains_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_roofs_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_skylights_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_slabs_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_total_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_walls_btu_h',
'report_simulation_output.hvac_design_load_cooling_sensible_windows_btu_h',
'report_simulation_output.hvac_design_load_heating_ceilings_btu_h',
'report_simulation_output.hvac_design_load_heating_doors_btu_h',
'report_simulation_output.hvac_design_load_heating_ducts_btu_h',
'report_simulation_output.hvac_design_load_heating_floors_btu_h',
'report_simulation_output.hvac_design_load_heating_infiltration_ventilation_btu_h',
'report_simulation_output.hvac_design_load_heating_roofs_btu_h',
'report_simulation_output.hvac_design_load_heating_skylights_btu_h',
'report_simulation_output.hvac_design_load_heating_slabs_btu_h',
'report_simulation_output.hvac_design_load_heating_total_btu_h',
'report_simulation_output.hvac_design_load_heating_walls_btu_h',
'report_simulation_output.hvac_design_load_heating_windows_btu_h',
'report_simulation_output.hvac_design_temperature_cooling_f',
'report_simulation_output.hvac_design_temperature_heating_f',
'report_simulation_output.include_timeseries_airflows',
'report_simulation_output.include_timeseries_component_loads',
'report_simulation_output.include_timeseries_emission_end_uses',
'report_simulation_output.include_timeseries_emission_fuels',
'report_simulation_output.include_timeseries_emissions',
'report_simulation_output.include_timeseries_end_use_consumptions',
'report_simulation_output.include_timeseries_fuel_consumptions',
'report_simulation_output.include_timeseries_hot_water_uses',
'report_simulation_output.include_timeseries_total_consumptions',
'report_simulation_output.include_timeseries_total_loads',
'report_simulation_output.include_timeseries_unmet_hours',
'report_simulation_output.include_timeseries_weather',
'report_simulation_output.include_timeseries_zone_temperatures',
'report_simulation_output.load_cooling_delivered_m_btu',
'report_simulation_output.load_heating_delivered_m_btu',
'report_simulation_output.load_hot_water_delivered_m_btu',
'report_simulation_output.load_hot_water_desuperheater_m_btu',
'report_simulation_output.load_hot_water_solar_thermal_m_btu',
'report_simulation_output.load_hot_water_tank_losses_m_btu',
'report_simulation_output.output_format',
'report_simulation_output.peak_electricity_summer_total_w',
'report_simulation_output.peak_electricity_winter_total_w',
'report_simulation_output.peak_load_cooling_delivered_k_btu_hr',
'report_simulation_output.peak_load_heating_delivered_k_btu_hr',
'report_simulation_output.timeseries_frequency',
'report_simulation_output.timeseries_num_decimal_places',
'report_simulation_output.timeseries_timestamp_convention',
'report_simulation_output.unmet_hours_cooling_hr',
'report_simulation_output.unmet_hours_heating_hr',
'upgrade_costs.applicable',
'upgrade_costs.debug',
'upgrade_costs.door_area_ft_2',
'upgrade_costs.duct_unconditioned_surface_area_ft_2',
'upgrade_costs.floor_area_attic_ft_2',
'upgrade_costs.floor_area_attic_insulation_increase_ft_2_delta_r_value',
'upgrade_costs.floor_area_conditioned_ft_2',
'upgrade_costs.floor_area_conditioned_infiltration_reduction_ft_2_delta_ach_50',
'upgrade_costs.floor_area_foundation_ft_2',
'upgrade_costs.floor_area_lighting_ft_2',
'upgrade_costs.flow_rate_mechanical_ventilation_cfm',
'upgrade_costs.rim_joist_area_above_grade_exterior_ft_2',
'upgrade_costs.roof_area_ft_2',
'upgrade_costs.size_cooling_system_primary_k_btu_h',
'upgrade_costs.size_heat_pump_backup_primary_k_btu_h',
'upgrade_costs.size_heating_system_primary_k_btu_h',
'upgrade_costs.size_heating_system_secondary_k_btu_h',
'upgrade_costs.size_water_heater_gal',
'upgrade_costs.slab_perimeter_exposed_conditioned_ft',
'upgrade_costs.upgrade_cost_usd',
'upgrade_costs.wall_area_above_grade_conditioned_ft_2',
'upgrade_costs.wall_area_above_grade_exterior_ft_2',
'upgrade_costs.wall_area_below_grade_ft_2',
'upgrade_costs.window_area_ft_2',
'report_utility_bills.applicable',
'report_utility_bills.output_format',
'report_simulation_output.component_load_cooling_total_m_btu',
'report_simulation_output.component_load_heating_total_m_btu',
'report_simulation_output.component_load_cooling_residual',
'report_simulation_output.component_load_heating_residual',
'BLDG']

EUSES = ["HEAT", "COOL"]
final_data = pd.DataFrame()

def convert(df):
    weight_column = df["build_existing_model.sample_weight"]
    # unique_bldg_types = df["build_existing_model.geometry_building_type_acs"].unique()
    # print("Unique building types:",unique_bldg_types)
    df["BLDG"] = df["build_existing_model.geometry_building_type_acs"].map(BLDG_MAPPING)
    df["BLDG"] = df["BLDG"].map(BLDG_CODE)
    # print all unique values in df["CDIV"]
    unique_cdivs = df["build_existing_model.census_division"].unique()
    print("Unique census divisions:",unique_cdivs)
    df["CDIV"] = df["build_existing_model.census_division"].str.lower().map(CDIV_MAPPING)
    df["NBLDGS"] = weight_column
    print("Number of None in BLDG:",df["BLDG"].isna().sum())
    return df

def convert_to_thermalLoads(data: pd.DataFrame, final_data: pd.DataFrame) -> None:

    categories = sorted(set(RESSTOCK_SEGMENT_TO_CATEGORY.values()))
    if "PEOPLE" not in categories:
        categories.append("PEOPLE")
    
    for cdiv in range(1, CDIV_MAX+1):
        for bldg in range(1, BLDG_MAX+1):
            for euse in EUSES:
                subset = data[
                    (data["CDIV"] == cdiv) & (data["BLDG"] == bldg)
                ]

                euse_lower = "heating" if euse == "HEAT" else "cooling"
                keep_cols = [
                    c
                    for c in subset.columns
                    if (
                        "component_load_" + euse_lower in str(c).lower()
                        or c in ["CDIV", "BLDG", "NBLDGS"]
                    )
                ]
                subset = subset[keep_cols]

                # Compute weights and prepare a category accumulator
                sum_bldgs = subset["NBLDGS"].sum()
                # Per-row weight; if sum is zero, set weight to 0 (vector of zeros via broadcasting)
                row_weight = subset["NBLDGS"] / sum_bldgs if sum_bldgs > 0 else 0.0

                # Accumulate weighted totals per category in this dict
                cat_weighted = {cat: 0.0 for cat in categories}
                # PEOPLE is explicitly zero per your comment
                cat_weighted["PEOPLE"] = 0.0

                for segment, category in RESSTOCK_SEGMENT_TO_CATEGORY.items():
                    seg_cols = [
                        col
                        for col in subset.columns
                        if ("component_load_" + euse_lower in str(col).lower())
                        and (segment in str(col).lower())
                    ]

                    # Row-wise sum across all matched segment columns 
                    seg_row_sum = subset[seg_cols].sum(axis=1)
                    seg_weighted_value = float((seg_row_sum * row_weight).sum())
                    cat_weighted[category] += seg_weighted_value


                final_data = pd.concat([final_data, pd.DataFrame({
                    "CDIV": cdiv,
                    "BLDG": bldg,
                    "EUSE": euse,
                    "SUM_NBLDGS": sum_bldgs
                }, index=[0])], ignore_index=True)

                # weighted thermal components (compute scalar weighted averages per row)
                row_mask = (
                    (final_data["CDIV"] == cdiv)
                    & (final_data["BLDG"] == bldg)
                    & (final_data["EUSE"] == euse)
                )

                for cat, val in cat_weighted.items():
                    final_data.loc[row_mask, cat] = val


                # Normalize to shares (fractions of total)
                share_components = [c for c in categories if c != "TOTAL"]

                # Sum across share components for just this row (Series of length 1)
                row_total = final_data.loc[row_mask, share_components].sum(axis=1)

                # Normalize only if positive (avoid divide-by-zero)
                if not row_total.empty and float(row_total.iloc[0]) > 0:
                    final_data.loc[row_mask, share_components] = (
                        final_data.loc[row_mask, share_components].div(row_total.values, axis=0)
                    )



    # Save to CSV with tab separator and txt extension
    final_data.to_csv("scout/supporting_data/thermal_loads_data/thermalLoads_data.txt", sep="\t", index=False)



    

def main():
    df = pd.read_csv("scout/supporting_data/thermal_loads_data/results_up00_update.csv",
low_memory=False)
    df = convert(df)
    convert_to_thermalLoads(df, final_data)
    print("Conversion complete!")

if __name__ == "__main__":
    main()