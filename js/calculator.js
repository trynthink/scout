$(document).ready(function(){

	// Preload climate zone map image so that the popover appears in the
	// correct location when clicked
	if (document.images) {
		cz_map_image = new Image();
		cz_map_image.src = "resources/climatezone-lg.jpg";
	}

	// Define upper and lower bounds for movement of affixed panel
	$('#calc-panel').affix({
		offset: {
			top: $('.jumbotron').outerHeight(),
			bottom: $('#footer').outerHeight(true)
		}
	});

	// Enable tooltips
	$(function () {
	  $('[data-toggle="tooltip"]').tooltip();
	});

	// Enable specific popover (for AIA climate zone image)
	var AIA_CZ_image_HTML = '<img width="100%" src="resources/climatezone-lg.jpg">';
	$('#AIA-CZ-popover').popover({placement: 'right', content: AIA_CZ_image_HTML, html: true, container: 'body'});

	// Store needed data about site-to-source conversions and CO2 emissions
	// from the appropriate JSON database
	var ss_el, ss_ng, ss_ot, co2_el, co2_ng, co2_ot;
	$.getJSON('ss_co2_conversions.json', function(data){
		ss_el = data['electricity (grid)']['site to source conversion'];
		co2_el = data['electricity (grid)']['CO2 intensity'];
		co2_ng = data['natural gas']['CO2 intensity'];
		co2_ot = data['other']['CO2 intensity'];
	});

	// Generate #proj-year drop down list

	// From today's date, get the current year minus one (year), which will be
	// the earliest baseline year available in the calculator
	var intended_year = new Date().getFullYear() - 1;

	// Identify the default year (to be selected when the page loads) 
	// and the last year in the list
	var default_year = 2030;
	var max_year = 2040;

	// Generate array of years to appear in the drop down
	var yr_array = [];
	for (var i = 0; i <= (max_year - intended_year); i++) {
		year = intended_year + i; // Calculate the year using the iterator
		yr_array.push(year);
	}

	// Populate the drop down menu and set the default year
	populateDropdown('proj-year', '', yr_array, yr_array);
	$('#proj-year').val(default_year);



	// Initialize variables with lists to be converted to selections
	// as needed in the market definition form
	var res_bldg_types = ['Single-family Homes', 'Multi-family Homes', 'Mobile Homes']
	var res_bldg_types_values = ['single family home', 'multi family home', 'mobile home']
	var com_bldg_types = ['Assembly', 'Education', 'Food Sales', 'Food Service', 'Health Care', 'Lodging', 'Mercantile/Service', 'Small Office', 'Large Office', 'Warehouse', 'Other']
	var com_bldg_types_values = ['assembly', 'education', 'food sales', 'food service', 'health care', 'lodging', 'mercantile/service', 'small office', 'large office', 'warehouse', 'other']

	var com_end_use = ['Heating', 'Cooling', 'Water Heating', 'Ventilation', 'Cooking', 'Lighting', 'Refrigeration', 'Computers', 'Office Electronics', 'Other Electric Loads'];
	var com_end_use_values = ['heating', 'cooling', 'water heating', 'ventilation', 'cooking', 'lighting', 'refrigeration', 'PCs', 'non-PC office equipment', 'MELs'];
	// Freezers, Dishwashers, Clothes Washers
	var res_end_use = ['Heating', 'Secondary Heating', 'Cooling', 'Fans and Pumps', 'Ceiling Fans', 'Lighting', 'Water Heating', 'Refrigeration', 'Cooking', 'Clothes Drying', 'Home Entertainment', 'Computers', 'Other'];
	var res_end_use_values = ['heating', 'secondary heating', 'cooling', 'fans & pumps', 'ceiling fan', 'lighting', 'water heating', 'refrigeration', 'cooking', 'drying', 'TVs', 'computers', 'other (grid electric)'];

	var envelope = ['Windows (Conduction)', 'Windows (Radiation)', 'Walls', 'Roof', 'Ground', 'Infiltration', 'Equipment Heat Gain']; //, 'People Heat Gain'];
	var envelope_values = ['windows conduction', 'windows solar', 'wall', 'roof', 'ground', 'infiltration', 'equipment gain']; //, 'people gain'];

	var fuel_type = ['Electricity', 'Natural Gas', 'Distillate', 'Solar', 'Other', 'Propane/LPG'];
	var fuel_type_values = ['electricity (grid)', 'natural gas', 'distillate', 'solar', 'other fuel', 'other fuel'];
	var heating_FT = [0, 1, 2, 4]; // Selection of applicable fuel types for each residential end use
	var sec_heating_FT = [0, 1, 2, 4];
	var cooling_FT = [0, 1];
	var water_heating_FT = [0, 1, 2, 5, 3]; // 'other fuel' corresponds to only LPG
	var cooking_FT = [0, 1, 5]; // 'other fuel' corresponds to only LPG
	var drying_FT = [0, 1];
	
		// For heating, secondary heating, and cooling for residential
		// buildings, the equipment list must be defined for each fuel type
	var heating_equip = ['Boiler', 'Air-Source Heat Pump', 'Ground-Source Heat Pump', 'Furnace', 'Boiler', 'Heat Pump', 'Furnace', 'Boiler', 'Furnace (Kerosene)', 'Furnace (LPG)', 'Wood Stove', 'Resistance'];
	var heating_equip_values = ['boiler (electric)', 'ASHP', 'GSHP', 'furnace (NG)', 'boiler (NG)', 'NGHP', 'furnace (distillate)', 'boiler (distillate)', 'furnace (kerosene)', 'furnace (LPG)', 'stove (wood)', 'resistance'];
	var heating_equip_el = [0, 1, 2];
	var heating_equip_ng = [3, 4, 5];
	var heating_equip_ds = [6, 7];
	var heating_equip_ot = [8, 9, 10, 11];

	var sec_heating_equip = ['Kerosene Heater', 'Wood Heater', 'LPG Heater', 'Coal Heater']; // FOR ALL FUEL TYPES EXCEPT OTHER, THE EQUIPMENT IS 'non-specific'
	var sec_heating_equip_values = ['secondary heating (kerosene)', 'secondary heating (wood)', 'secondary heating (LPG)', 'secondary heating (coal)'];

	var cooling_equip = ['Central AC', 'Room/Window AC', 'Air-Source Heat Pump', 'Ground-Source Heat Pump', 'Heat Pump'];
	var cooling_equip_values = ['central AC', 'room AC', 'ASHP', 'GSHP', 'NGHP'];
	var cooling_equip_el = [0, 1, 2, 3];
	var cooling_equip_ng = [4];

	var lighting = ['General Service Lamp (Incandescent)', 'General Service Lamp (CFL)', 'General Service Lamp (LED)', 'Linear Fluorescent (T-12)', 'Linear Fluorescent (T-8)', 'Linear Fluorescent (LED Drop-in)', 'Reflector (Incandescent)', 'Reflector (CFL)', 'Reflector (Halogen)', 'Reflector (LED)', 'External (Incandescent)', 'External (CFL)', 'External (High-pressure Sodium)', 'External (LED)'];
	var lighting_values = ['general service (incandescent)', 'general service (CFL)', 'general service (LED)', 'linear fluorescent (T-12)', 'linear fluorescent (T-8)', 'linear fluorescent (LED)', 'reflector (incandescent)', 'reflector (CFL)', 'reflector (halogen)', 'reflector (LED)', 'external (incandescent)', 'external (CFL)', 'external (high pressure sodium)', 'external (LED)'];

	var entertainment = ['TVs', 'Set-top Boxes', 'DVD Players', 'Home Theater Systems', 'Video Game Systems'];
	var entertainment_values = ['TV', 'set top box', 'DVD', 'home theater & audio', 'video game consoles'];

	var computers = ['Desktops', 'Laptops', 'Monitors/Displays', 'Network Equipment'];
	var computers_values = ['desktop PC', 'laptop PC', 'monitors', 'network equipment'];

	var other = ['Clothes Washing', 'Dishwashers', 'Freezers', 'Other Electric Loads'];
	var other_values = ['clothes washing', 'dishwasher', 'freezers', 'other MELs'];

	// More predefined vectors for commercial buildings
	var com_envelope = ['Windows (Conduction)', 'Windows (Radiation)', 'Walls', 'Roof', 'Ground', 'Floor', 'Infiltration', 'Ventilation', 'Equipment Heat Gain', 'Lighting Heat Gain'];
	var com_envelope_values = ['windows conduction', 'windows solar', 'wall', 'roof', 'ground', 'floor', 'infiltration', 'ventilation', 'equipment gain', 'lighting gain'];

	var com_fuel_type = ['Electricity', 'Natural Gas', 'Distillate'];
	var com_fuel_type_values = ['electricity', 'natural gas', 'distillate'];
	// N.B. Heating and water heating have data reported for all three fuel types
	var com_cooling_FT = [0, 1];
	var com_cooking_FT = [0, 1];

	var com_mels_type = ['Security Systems', 'Elevators', 'Escalators', 'Non-road Electric Vehicles', 'Coffee Brewers', 'Kitchen Ventilation', 'Laundry Equipment', 'Laboratory Refrigeration', 'Fume Hoods', 'Medical Imaging Systems', 'Video Displays', 'Large Video Displays'];
	var com_mels_type_values = ['security systems', 'elevators', 'escalators', 'non-road electric vehicles', 'coffee brewers', 'kitchen ventilation', 'laundry', 'lab fridges and freezers', 'fume hoods', 'medical imaging', 'video displays', 'large video displays'];

	var com_heating_equip = ['Boiler', 'Resistance Heating', 'Ground-Source Heat Pump', 'Air-Source Heat Pump', 'Boiler', 'Furnace', 'Engine-driven Heat Pump', 'Residential-type Heat Pump', 'Boiler', 'Furnace'];
	var com_heating_equip_values = ['elec_boiler', 'electric_res-heat', 'comm_GSHP-heat', 'rooftop_ASHP-heat', 'gas_boiler', 'gas_furnace', 'gas_eng-driven_RTHP-heat', 'res_type_gasHP-heat', 'oil_boiler', 'oil_furnace'];
	var com_heating_equip_el = [0, 1, 2, 3];
	var com_heating_equip_ng = [4, 5, 6, 7];
	var com_heating_equip_ds = [8, 9];

	var com_cooling_equip = ['Centrifugal Chiller', 'Reciprocating Chiller', 'Screw Chiller', 'Scroll Chiller', 'Ground-Source Heat Pump', 'Air-Source Heat Pump', 'Residential-type Central AC', 'Rooftop AC', 'Wall/Window Room AC', 'Chiller', 'Engine-driven AC', 'Engine-driven Heat Pump', 'Residential-type Heat Pump'];
	var com_cooling_equip_values = ['centrifugal_chiller', 'reciprocating_chiller', 'screw_chiller', 'scroll_chiller', 'comm_GSHP-cool', 'rooftop_ASHP-cool', 'res_type_central_AC', 'rooftop_AC', 'wall-window_room_AC', 'gas_chiller', 'gas_eng-driven_RTAC', 'gas_eng-driven_RTHP-cool', 'res_type_gasHP-cool'];
	var com_cooling_equip_el = [0, 1, 2, 3, 4, 5, 6, 7, 8];
	var com_cooling_equip_ng = [9, 10, 11, 12];

	var com_water_heating_equip = ['Storage Water Heater', 'Heat Pump Water Heater', 'Solar Water Heater', 'Booster Water Heater', 'Storage Water Heater', 'Booster Water Heater', 'Instant Water Heater', 'Storage Water Heater'];
	var com_water_heating_equip_values = ['elec_water_heater', 'HP water heater', 'Solar water heater', 'elec_booster_water_heater', 'gas_water_heater', 'gas_booster_WH', 'gas_instantaneous_WH', 'oil_water_heater'];
	var com_water_heating_equip_el = [0, 1, 2, 3];
	var com_water_heating_equip_ng = [4, 5, 6];
	var com_water_heating_equip_ds = [7];

	var com_lighting = ['General Service Lamp (Incandescent)', 'General Service Lamp (CFL)', 'Edison-style Lamp', 'Linear Fluorescent (T-5)', 'Linear Fluorescent (T-8)', 'Linear Fluorescent (T-12)', 'Linear Fluorescent (LED Drop-in)', 'Low Bay Lamp', 'Low Bay Lamp (LED)', 'High Bay Lamp', 'High Bay Lamp (LED)'];
	var com_lighting_values = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10];
	var com_lighting_indices = [[5,0,7,4], [1,2], [6,27], [8], [9,10,11,12,13,18,19,36], [14,16,17], [28], [21,22,24,31,34,3], [25,30], [15,20,32,33,35,23], [26,29]];
	var com_lighting_items = ['100W incand', '23W CFL', '26W CFL', '2L F54T5HO LB', '70W HIR PAR-38', '72W incand', '90W Halogen Edison', '90W Halogen PAR-38', 'F28T5', 'F28T8 HE', 'F28T8 HE w/ OS', 'F28T8 HE w/ OS_SR', 'F28T8 HE w/ SR', 'F32T8', 'F34T12', 'F54T5 HO_HB', 'F96T12 ES mag', 'F96T12 mag', 'F96T8', 'F96T8 HE', 'F96T8 HO_HB', 'F96T8 HO_LB', 'HPS 100_LB', 'HPS 150_HB', 'HPS 70_LB', 'LED 100 HPS_LB', 'LED 150 HPS_HB', 'LED Edison', 'LED T8', 'LED_HB', 'LED_LB', 'MH 175_LB', 'MH 250_HB', 'MH 400_HB', 'MV 175_LB', 'MV 400_HB', 'T8 F32 EEMag (e)'];
	
	var com_ventilation_equip = ['Constant Air Volume Systems', 'Variable Air Volume Systems'];
	var com_ventilation_equip_values = ['CAV_Vent', 'VAV_Vent'];

	var com_refrigeration_equip = ['Supermarket Display Case', 'Supermarket Condenser', 'Supermarket Compressor Rack', 'Reach-in Refrigerator', 'Reach-in Freezer', 'Walk-in Refrigerator', 'Walk-in Freezer', 'Beverage Merchandiser', 'Vending Machine', 'Ice Machine'];
	var com_refrigeration_equip_values = ['Supermkt_display_case', 'Supermkt_condenser', 'Supermkt_compressor_rack', 'Reach-in_refrig', 'Reach-in_freezer', 'Walk-In_refrig', 'Walk-In_freezer', 'Bevrg_Mchndsr', 'Vend_Machine', 'Ice_machine'];



	// Get selection for projection year (capturing initial selection also)
	var proj_year = $('#proj-year').val();
	$('#proj-year').on('change', function (){
		proj_year = $('#proj-year').val();
	});

	// Get selection(s) for climate zone
	var climate_zone; // variable with global scope for later use
	$('#climate-zone').on('change', function(){
		// Clear climate zones from list
		climate_zone = [];

		// Record all selected climate zones in an array
		$.each($('input:checkbox:checked', '#climate-zone'), function(){climate_zone.push($(this).val());});
	});

	// Initialize variable for the list of selected building types
	var selected_buildings;

	// Define variable to record status of selection (selection = 1)
	var buildings_selection_status = 0;

	// Detect selected radio button (residential/commercial buildings)
	// and respond accordingly
	$(document).on('change', '#building-radio', function(){
		// Identify element of radio button selected
		var bldg_class_radio_selected = $('input[name=bldg-class]:checked').val();

		// Clear drop down menu
		$('#end-use').empty();

		// Clear all subsequent/child content
		$('.subtype').remove();

		// Update the status variable
		buildings_selection_status = 0;

		if (bldg_class_radio_selected === 'residential') {
			// Clear the contents of the selection list
			$('#bldg-types').empty();

			// // Clear the contents of the selected_buildings list
			// selected_buildings = null;

			// Add residential building types to the selection list
			populateDropdown('bldg-types', null, res_bldg_types, res_bldg_types_values);
		}
		else {
			// Clear the contents of the selection list
			$('#bldg-types').empty();

			// // Clear the contents of the selected_buildings list
			// selected_buildings = null;

			// Add commercial building types to the selection list
			populateDropdown('bldg-types', null, com_bldg_types, com_bldg_types_values);
		}
	});

	// Building type selection actions
	$('#bldg-types').on('change', function (){
		
		// Put the selected building types into a list
		selected_buildings = $('#bldg-types').val();

		// Clear end use drop down when no building types are selected
		if (selected_buildings === null) {
			// Clear drop down menu
			$('#end-use').empty();

			// Clear all subsequent/child content
			$('.subtype').remove();

			// Update the status variable
			buildings_selection_status = 0;
		}

		// If at least one building type is selected and none were selected 
		// before, update the list of end use categories
		if (selected_buildings !== null && selected_buildings !== undefined) {
			if (buildings_selection_status === 0) {
				// Initialize drop down menu contents
				var end_use_dropdown = '<option disabled selected> -- Select an End Use -- </option>';

				// Update the status variable
				buildings_selection_status = 1;

				// Populate the selected drop down menu in the DOM with choices
				// appropriate for the building class selected
				if ($('input[name=bldg-class]:checked').val() === 'residential'){
					populateDropdown('end-use', end_use_dropdown, res_end_use, res_end_use_values);
				}
				else {
					populateDropdown('end-use', end_use_dropdown, com_end_use, com_end_use_values);
				}
			}
		}		
	});

	var selected_end_use; // Revised global scope

	// End use selection actions (generating further selections)
	$('#end-use').change(function(){
		// Identify selected end use
		selected_end_use = $('#end-use').val();

		// CLEAR OUT ANY ADDED DROPDOWN OR SELECTION MENUS - anything with the subtype class
		$('.subtype').remove();

		// Define next set of actions based on whether residential or
		// commercial buildings are selected
		if ($('input[name=bldg-class]:checked').val() === 'residential') {
			// Generate appropriate selections (if any) for the selected end use
			if (selected_end_use === 'heating' || selected_end_use === 'secondary heating' || selected_end_use === 'cooling') {
				
				// Specify HTML for equipment/envelope radio button
				eqEnvRadioBtn = "<div class='row row-end-use subtype' id='eq-env-radio'>"
								+ "<div class='col-md-12'>"
								+ "<div class='btn-group' data-toggle='buttons'>"
								+ "<label class='btn btn-default'><input type='radio' autocomplete='off' name='eq-env' value='supply'>Equipment</label>"
								+ "<label class='btn btn-default'><input type='radio' autocomplete='off' name='eq-env' value='demand'>Envelope</label>"
								+ "</div>"
								+ "</div>"
								+ "</div>";

				// Insert radio button in appropriate location
				$('#end-use-row').after(eqEnvRadioBtn);
			}
			else if (selected_end_use === 'water heating' || selected_end_use === 'cooking' || selected_end_use === 'drying') {
				// Identify the appropriate fuel types to display for the selected end use
				// Need to create new variable for the ID for each possible dropdown
				// since some selected_end_use values have spaces, which aren't
				// allowed in IDs
				if (selected_end_use === 'water heating') {var ft_select = water_heating_FT;}
				else if (selected_end_use === 'cooking') {var ft_select = cooking_FT;}
				else {var ft_select = drying_FT;}

				// (Re)define variable to hold choices in dropdown
				var ft_dropdown = '<option disabled selected> -- Select a Fuel Type -- </option>';

				// Populate the selected drop down menu in the DOM with choices
				generateDropdown('last', '#end-use-row', ft_dropdown, fuel_type, fuel_type_values, ft_select);
			}
			else if (selected_end_use === 'lighting') {
				// Add lighting technology type buttons to HTML DOM
				generateButtonGroup('last-tt', '#end-use-row', lighting, lighting_values);
			}
			else if (selected_end_use === 'TVs') {
				// Add entertainment technology type buttons to HTML DOM
				generateButtonGroup('last-tt', '#end-use-row', entertainment, entertainment_values);
			}
			else if (selected_end_use === 'computers') {
				// Add computers technology type buttons to HTML DOM
				generateButtonGroup('last-tt', '#end-use-row', computers, computers_values);
			}
			else if (selected_end_use === 'other (grid electric)') {
				// Add other technology type buttons to HTML DOM
				generateButtonGroup('last-tt', '#end-use-row', other, other_values);
			}
			// else terminal categories (fans & pumps, ceiling fan, 
			// refrigeration), no action required
		}
		else {
			// Generate appropriate selections (if any) for the selected end use
			if (selected_end_use === 'heating' || selected_end_use === 'cooling') {
				
				// Specify HTML for equipment/envelope radio button
				eqEnvRadioBtn = "<div class='row row-end-use subtype' id='eq-env-radio'>"
								+ "<div class='col-md-12'>"
								+ "<div class='btn-group' data-toggle='buttons'>"
								+ "<label class='btn btn-default'><input type='radio' autocomplete='off' name='eq-env' value='supply'>Equipment</label>"
								+ "<label class='btn btn-default'><input type='radio' autocomplete='off' name='eq-env' value='demand'>Envelope</label>"
								+ "</div>"
								+ "</div>"
								+ "</div>";

				// Insert radio button in appropriate location
				$('#end-use-row').after(eqEnvRadioBtn);
			}
			else if (selected_end_use === 'water heating') {
				// (Re)define drop down text and generate appropriate drop down in the DOM
				var ft_dropdown = '<option disabled selected> -- Select a Fuel Type -- </option>';
				generateDropdown('fuel-type', '#end-use-row', ft_dropdown, com_fuel_type, com_fuel_type_values);
			}
			else if (selected_end_use === 'cooking') {
				// (Re)define drop down text and generate appropriate drop down in the DOM
				var ft_dropdown = '<option disabled selected> -- Select a Fuel Type -- </option>';
				generateDropdown('last', '#end-use-row', ft_dropdown, com_fuel_type, com_fuel_type_values, com_cooking_FT);
			}
			else if (selected_end_use === 'ventilation') {
				// Add ventilation equipment type buttons to the DOM
				generateButtonGroup('last-tt', '#end-use-row', com_ventilation_equip, com_ventilation_equip_values);
			}
			else if (selected_end_use === 'lighting') {
				// Add lighting bulb/fixture type buttons to the DOM
				generateButtonGroup('last-tt', '#end-use-row', com_lighting, com_lighting_values);
			}
			else if (selected_end_use === 'refrigeration') {
				// Add refrigeration equipment type buttons to the DOM
				generateButtonGroup('last-tt', '#end-use-row', com_refrigeration_equip, com_refrigeration_equip_values);
			}
			else if (selected_end_use === 'MELs') {
				// Add drop down of miscellaneous electric loads to the DOM
				var init_dropdown_text = '<option disabled selected> -- Select an Equipment Type -- </option>';
				generateDropdown('last', '#end-use-row', init_dropdown_text, com_mels_type, com_mels_type_values);
			}
			// else terminal categories (PCs, office equipment), no action required		
		}
	});

	// Detect selected radio button (equipment/envelope) 
	// and respond accordingly
	$(document).on('change', '#eq-env-radio', function(){
		// Identify element of radio button selected
		var radio_selection = $('input[name=eq-env]:checked').val();

		if (radio_selection === 'demand') {
			// Remove any equipment content
			$('.row.subtype.supply').remove();

			// Add envelope buttons to HTML DOM, with the buttons determined
			// by the building class
			if ($('input[name=bldg-class]:checked').val() === 'residential') {
				generateButtonGroup('env-buttons', '#eq-env-radio', envelope, envelope_values);
			}
			else {
				generateButtonGroup('env-buttons', '#eq-env-radio', com_envelope, com_envelope_values);
			}			

			// Add 'envelope' class to button group just added so that it
			// will be removed automatically if the radio button selection
			// is changed from envelope to equipment
			$('#env-buttons').addClass(radio_selection);
		}
		else {
			// Remove any envelope content
			$('.row.subtype.demand').remove();

			// (Re)define variable to hold choices in dropdown
			var ft_dropdown = '<option disabled selected> -- Select a Fuel Type -- </option>';

			// Generate dropdown menu for fuel types based on the building class
			// (residential/commercial) and the selected end use
			if ($('input[name=bldg-class]:checked').val() === 'residential') {
				// Identify the appropriate fuel types to display for the selected end use
				if (selected_end_use === 'heating') {var ft_select = heating_FT;}
				else if (selected_end_use === 'secondary heating') {var ft_select = sec_heating_FT;}
				else {var ft_select = cooling_FT;}

				// Populate the selected drop down menu in the DOM with choices
				generateDropdown('fuel-type', '#eq-env-radio', ft_dropdown, fuel_type, fuel_type_values, ft_select);
			}
			else {
				// For commercial buildings, populate the selected drop down
				// menu in the DOM based on the selected end use
				if (selected_end_use === 'heating') {
					generateDropdown('fuel-type', '#eq-env-radio', ft_dropdown, com_fuel_type, com_fuel_type_values);
				}
				else {
					generateDropdown('fuel-type', '#eq-env-radio', ft_dropdown, com_fuel_type, com_fuel_type_values, com_cooling_FT);
				}
			}

			// Add 'equipment' class to dropdown just added so that it
			// will be removed automatically if the radio button selection
			// is changed from equipment to envelope
			$('#fuel-type').addClass('supply');
		}
	});

	// Detect selected fuel type (for HVAC end uses and water heating in
	// commercial buildings) and display the appropriate technology types
	$(document).on('change', '#fuel-type', function(){
		// Determine what fuel type was selected
		var the_fuel = $('option:selected', '#fuel-type').val();
		
		// Clear any existing equipment type buttons
		$('#eq-buttons').remove();

		// Add the appropriate buttons to the appropriate HTML DOM element
		// based on the building class, end use, and fuel type selection
		if ($('input[name=bldg-class]:checked').val() === 'residential') {
			if (selected_end_use === 'heating') {
				if (the_fuel === 'electricity (grid)') {var eq_select = heating_equip_el;}
				else if (the_fuel === 'natural gas') {var eq_select = heating_equip_ng;}
				else if (the_fuel === 'distillate') {var eq_select = heating_equip_ds;}
				else {var eq_select = heating_equip_ot;}

				// Add heating equipment type buttons to HTML DOM
				generateButtonGroup('eq-buttons', '#fuel-type', heating_equip, heating_equip_values, eq_select);
			}
			else if (selected_end_use === 'secondary heating') {
				if (the_fuel === 'other fuel') {
					// Add secondary heating equipment type buttons to HTML DOM
					generateButtonGroup('eq-buttons', '#fuel-type', sec_heating_equip, sec_heating_equip_values);
				}
			}
			else {
				if (the_fuel === 'electricity (grid)') {var eq_select = cooling_equip_el;}
				else {var eq_select = cooling_equip_ng;}

				// Add cooling equipment type buttons to HTML DOM
				generateButtonGroup('eq-buttons', '#fuel-type', cooling_equip, cooling_equip_values, eq_select);
			}
		}
		else {
			if (selected_end_use === 'heating') {
				// Depending on the fuel type, add the appropriate group of
				// buttons to the DOM using the generateButtonGroup function
				if (the_fuel === 'electricity') {generateButtonGroup('eq-buttons', '#fuel-type', com_heating_equip, com_heating_equip_values, com_heating_equip_el);}
				else if (the_fuel === 'natural gas') {generateButtonGroup('eq-buttons', '#fuel-type', com_heating_equip, com_heating_equip_values, com_heating_equip_ng);}
				else {generateButtonGroup('eq-buttons', '#fuel-type', com_heating_equip, com_heating_equip_values, com_heating_equip_ds);}
			}
			else if (selected_end_use === 'cooling') {
				if (the_fuel === 'electricity') {generateButtonGroup('eq-buttons', '#fuel-type', com_cooling_equip, com_cooling_equip_values, com_cooling_equip_el);}
				else {generateButtonGroup('eq-buttons', '#fuel-type', com_cooling_equip, com_cooling_equip_values, com_cooling_equip_ng);}
			}
			else { // water heating
				if (the_fuel === 'electricity') {generateButtonGroup('eq-buttons', '#fuel-type', com_water_heating_equip, com_water_heating_equip_values, com_water_heating_equip_el);}
				else if (the_fuel === 'natural gas') {generateButtonGroup('eq-buttons', '#fuel-type', com_water_heating_equip, com_water_heating_equip_values, com_water_heating_equip_ng);}
				else {generateButtonGroup('eq-buttons', '#fuel-type', com_water_heating_equip, com_water_heating_equip_values, com_water_heating_equip_ds);}
			}
		}

		// Add 'equipment' class to button group just added so that it will be
		// removed automatically if the radio button selection is changed from
		// equipment to envelope
		$('#eq-buttons').addClass('supply');
	});


////////////////////////////////////////////////////////////////////////////////
// None of this has to happen until the update button is clicked, but for
// later support of possible dynamic updating, it should be done in real time

	// Detect selected tech types (for HVAC end uses), both equipment and envelope
	var hvac_tt; // global scope variable for later use
	$(document).on('change', '#env-buttons', function(){
		// Clear tech types from list
		hvac_tt = [];

		// Record all currently selected tech types in the array
		$.each($('input:checkbox:checked', '#env-buttons'), function(){hvac_tt.push($(this).val());});
	});	
	$(document).on('change', '#eq-buttons', function(){
		// Clear tech types from list
		hvac_tt = [];

		// Record all currently selected tech types in the array
		$.each($('input:checkbox:checked', '#eq-buttons'), function(){hvac_tt.push($(this).val());});
	});	
	

	// Detect selected fuel type (for fuel type-only end uses)
	// Detect selected tech types (for other end uses)
	var ft_only_sel; // moved to global scope
	var other_tt; // global scope variable for later use

	$(document).on('change', '#last', function(){
		ft_only_sel = $('option:selected', '#last').val();
	});

	$(document).on('change', '#last-tt', function(){
		// Clear tech types from list
		other_tt = [];

		// Record all currently selected tech types in the array
		$.each($('input:checkbox:checked', '#last-tt'), function(){other_tt.push($(this).val());});
	});

////////////////////////////////////////////////////////////////////////////////


	// Query database and update total when update button is clicked
	$('#update').on('click', function(){
		// Declare/reset total
		var total_energy = 0;
		var total_co2 = 0;
		
		// Disable update button while request is pending
		$('#update').attr('disabled', true);

		if ($('input[name=bldg-class]:checked').val() === 'residential') {
			// Sum the totals for the selected residential data
			$.getJSON('data/res2015_microsegments_out.json', function(data){
				
				// Enable update button inside "success handler" on query completion
				$('#update').attr('disabled', false);

				// Redeclaration of this variable to ensure that the list is correct
				// and complete - otherwise the list is often incomplete
				var selected_buildings = $('#bldg-types').val();

				// Define intermediate quantity variable to store each quantity to
				// be added to the total
				var amtToAdd = 0;

				// Identify appropriate query based on the end use
				if (selected_end_use === 'heating' || selected_end_use === 'secondary heating' || selected_end_use === 'cooling') {
					// [climate zone][building type][fuel type][end use][supply/demand][tech type]['energy'][year]

					// Redeclaring these variables since they did not retain their
					// values from the global scope
					var HVAC_FT = $('option:selected', '#fuel-type').val(); 
					var radio_selection = $('input[name=eq-env]:checked').val();

					// Define function call based on radio_selection (supply or demand)
					if (radio_selection === 'supply') {
						// For all fuel types except 'other fuel', the tech type is 'non-specific' (secondary heating, equipment/demand only)
						if (HVAC_FT !== 'other fuel' && selected_end_use === 'secondary heating') {
							hvac_tt = ['non-specific'];
						}
						var energy_conv = primaryEnergyConversion(HVAC_FT, proj_year);
						var co2_conv = CO2Conversion(HVAC_FT, proj_year);
						// Loop over all climate zones selected
						for (var a = 0; a < climate_zone.length; a++) {
							// Loop over all building types selected
							for (var i = 0; i < selected_buildings.length; i++) {
								// Loop over all tech types selected
								for (var j = 0; j < hvac_tt.length; j++) {
									amtToAdd = data[climate_zone[a]][selected_buildings[i]][HVAC_FT][selected_end_use][radio_selection][hvac_tt[j]]['energy'][proj_year] * energy_conv;
									total_energy += amtToAdd;
									total_co2 += amtToAdd/1e9 * co2_conv;
								}
							}
						}
					}
					else {
						// Identify the applicable fuel types
						if (selected_end_use === 'heating') {var ft_select_f = heating_FT;}
						else if (selected_end_use === 'secondary heating') {var ft_select_f = sec_heating_FT;}
						else {var ft_select_f = cooling_FT;}

						// Loop over all climate zones selected
						for (var a = 0; a < climate_zone.length; a++) {
							// For demand, loop over all possible fuel types
							for (var k = 0; k < ft_select_f.length; k++) {
								var energy_conv = primaryEnergyConversion(fuel_type_values[ft_select_f[k]], proj_year);
								var co2_conv = CO2Conversion(ft_select_f[k], proj_year);
								// Loop over all building types selected
								for (var i = 0; i < selected_buildings.length; i++) {
									// Loop over all tech types selected
									for (var j = 0; j < hvac_tt.length; j++) {
										amtToAdd = data[climate_zone[a]][selected_buildings[i]][fuel_type_values[ft_select_f[k]]][selected_end_use][radio_selection][hvac_tt[j]]['energy'][proj_year] * energy_conv;
										total_energy += amtToAdd;
										total_co2 += amtToAdd/1e9 * co2_conv;
									}
								}
							}
						}
					}
				}
				else if (selected_end_use === 'water heating') {
					var energy_conv = primaryEnergyConversion(ft_only_sel, proj_year);
					var co2_conv = CO2Conversion(ft_only_sel, proj_year);

					// Define function call based on the fuel type
					if (ft_only_sel === 'electricity (grid)') {
						// Loop over all climate zones selected
						for (var a = 0; a < climate_zone.length; a++) {
							// Loop over all building types selected
							for (var i = 0; i < selected_buildings.length; i++) {
								amtToAdd = data[climate_zone[a]][selected_buildings[i]][ft_only_sel][selected_end_use]['electric WH']['energy'][proj_year] * energy_conv;
								total_energy += amtToAdd;
								total_co2 += amtToAdd/1e9 * co2_conv;
							}
						}
					}
					else if (ft_only_sel === 'solar') {
						// Loop over all climate zones selected
						for (var a = 0; a < climate_zone.length; a++) {
							// Loop over all building types selected
							for (var i = 0; i < selected_buildings.length; i++) {
								amtToAdd = data[climate_zone[a]][selected_buildings[i]]['electricity (grid)'][selected_end_use]['solar WH']['energy'][proj_year] * energy_conv;
								total_energy += amtToAdd;
								total_co2 += amtToAdd/1e9 * co2_conv;
							}
						}
					}
					else {
						// Loop over all climate zones selected
						for (var a = 0; a < climate_zone.length; a++) {
							// Loop over all building types selected
							for (var i = 0; i < selected_buildings.length; i++) {
								amtToAdd = data[climate_zone[a]][selected_buildings[i]][ft_only_sel][selected_end_use]['energy'][proj_year] * energy_conv;
								total_energy += amtToAdd;
								total_co2 += amtToAdd/1e9 * co2_conv;
							}
						}
					}
				}
				else if (selected_end_use === 'water heating' || selected_end_use === 'cooking' || selected_end_use === 'drying') {
					// [climate zone][building type][fuel type][end use]['energy'][year]

					var energy_conv = primaryEnergyConversion(ft_only_sel, proj_year);
					var co2_conv = CO2Conversion(ft_only_sel, proj_year);
					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// Loop over all building types selected
						for (var i = 0; i < selected_buildings.length; i++) {
							amtToAdd = data[climate_zone[a]][selected_buildings[i]][ft_only_sel][selected_end_use]['energy'][proj_year] * energy_conv;
							total_energy += amtToAdd;
							total_co2 += amtToAdd/1e9 * co2_conv;
						}
					}
				}
				else if (selected_end_use === 'lighting' || selected_end_use === 'computers' || selected_end_use === 'TVs' || selected_end_use === 'other (grid electric)') {
					// [climate zone][building type]['electricity (grid)'][end use][tech type]['energy'][year]

					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// Loop over all building types selected
						for (var i = 0; i < selected_buildings.length; i++) {
							// Loop over all tech types selected
							for (var j = 0; j < other_tt.length; j++) {
								amtToAdd = data[climate_zone[a]][selected_buildings[i]]['electricity (grid)'][selected_end_use][other_tt[j]]['energy'][proj_year] * ss_el[proj_year];
								total_energy += amtToAdd;
								total_co2 += amtToAdd/1e9 * co2_el[proj_year];
							}
						}
					}
				}
				else {
					// [climate zone][building type]['electricity (grid)'][end use]['energy'][year]

					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// Loop over all building types selected
						for (var i = 0; i < selected_buildings.length; i++) {
							amtToAdd = data[climate_zone[a]][selected_buildings[i]]['electricity (grid)'][selected_end_use]['energy'][proj_year] * ss_el[proj_year];
							total_energy += amtToAdd;
							total_co2 += amtToAdd/1e9 * co2_el[proj_year];
						}
					}
				}

				// Update total energy number displayed - rounded to 1 decimal place
				// Also, note conversion from MBTU to TBTU
				$('#energy-num').text(Math.round(total_energy/1e5)/10);

				// Update total CO2 number displayed - rounded to 1 decimal place
				$('#carbon-num').text(Math.round(total_co2*1e3)/1e3);
			});
		}
		else {
			// Sum the totals for the selected residential data
			$.getJSON('data/com2015_microsegments_out.json', function(data){
				
				// Enable update button inside "success handler" on query completion
				$('#update').attr('disabled', false);

				// Redeclaration of this variable to ensure that the list is correct
				// and complete - otherwise the list is often incomplete
				var selected_buildings = $('#bldg-types').val();

				// Define intermediate quantity variable to store each quantity to
				// be added to the total
				var amtToAdd = 0;

				// Identify appropriate query based on the end use
				if (selected_end_use === 'heating' || selected_end_use === 'cooling') {
					// [climate zone][building type][fuel type][end use][supply/demand][tech type][year]

					// Redeclaring these variables since they did not retain their
					// values from the global scope
					var the_fuel = $('option:selected', '#fuel-type').val(); 
					var radio_selection = $('input[name=eq-env]:checked').val();

					// Define function call based on radio_selection (supply or demand)
					if (radio_selection === 'supply') {

						var energy_conv = primaryEnergyConversion(the_fuel, proj_year);
						var co2_conv = CO2Conversion(the_fuel, proj_year);
						// Loop over all climate zones selected
						for (var a = 0; a < climate_zone.length; a++) {
							// Loop over all building types selected
							for (var i = 0; i < selected_buildings.length; i++) {
								// Loop over all tech types selected
								for (var j = 0; j < hvac_tt.length; j++) {
									amtToAdd = data[climate_zone[a]][selected_buildings[i]][the_fuel][selected_end_use][radio_selection][hvac_tt[j]][proj_year] * energy_conv;
									total_energy += amtToAdd;
									total_co2 += amtToAdd/1e3 * co2_conv;
								}
							}
						}
					}
					else { // Demand
						// Identify the applicable fuel types
						if (selected_end_use === 'heating') {var ft_select_f = [0, 1, 2];}
						else {var ft_select_f = cooling_FT;}

						// Loop over all climate zones selected
						for (var a = 0; a < climate_zone.length; a++) {
							// For demand, loop over all possible fuel types
							for (var k = 0; k < ft_select_f.length; k++) {
								var energy_conv = primaryEnergyConversion(com_fuel_type_values[ft_select_f[k]], proj_year);
								var co2_conv = CO2Conversion(ft_select_f[k], proj_year);
								// Loop over all building types selected
								for (var i = 0; i < selected_buildings.length; i++) {
									// Loop over all tech types selected
									for (var j = 0; j < hvac_tt.length; j++) {
										amtToAdd = data[climate_zone[a]][selected_buildings[i]][com_fuel_type_values[ft_select_f[k]]][selected_end_use][radio_selection][hvac_tt[j]][proj_year] * energy_conv;
										total_energy += amtToAdd;
										total_co2 += amtToAdd/1e3 * co2_conv;
									}
								}
							}
						}
					}
				}
				else if (selected_end_use === 'water heating') {
					// [climate zone][building type][fuel type][end use][tech type][year]

					// Identify the selected fuel type
					var the_fuel = $('option:selected', '#fuel-type').val();

					var energy_conv = primaryEnergyConversion(the_fuel, proj_year);
					var co2_conv = CO2Conversion(the_fuel, proj_year);

					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// Loop over all building types selected
						for (var i = 0; i < selected_buildings.length; i++) {
							// Loop over all tech types selected
							for (var j = 0; j < hvac_tt.length; j++) {
								amtToAdd = data[climate_zone[a]][selected_buildings[i]][the_fuel][selected_end_use][hvac_tt[j]][proj_year] * energy_conv;
								total_energy += amtToAdd;
								total_co2 += amtToAdd/1e3 * co2_conv;
							}
						}
					}
				}
				else if (selected_end_use === 'cooking') {
					// [climate zone][building type][fuel type][end use][year]

					var energy_conv = primaryEnergyConversion(ft_only_sel, proj_year);
					var co2_conv = CO2Conversion(ft_only_sel, proj_year);
					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// Loop over all building types selected
						for (var i = 0; i < selected_buildings.length; i++) {
							amtToAdd = data[climate_zone[a]][selected_buildings[i]][ft_only_sel][selected_end_use][proj_year] * energy_conv;
							total_energy += amtToAdd;
							total_co2 += amtToAdd/1e3 * co2_conv;
						}
					}
				}
				else if (selected_end_use === 'lighting') {
					// [climate zone][building type]['electricity'][end use][tech type][year]

          // Loop over all climate zones selected
          for (var a = 0; a < climate_zone.length; a++) {
            // Loop over all building types selected
            for (var i = 0; i < selected_buildings.length; i++) {
              // Select lighting subtype lists by group
              for (var j = 0; j < other_tt.length; j++) {
                for (var q = 0; q < com_lighting_indices[other_tt[j]].length; q++) {
                  amtToAdd = data[climate_zone[a]][selected_buildings[i]]['electricity'][selected_end_use][com_lighting_items[com_lighting_indices[other_tt[j]][q]]][proj_year] * ss_el[proj_year];
                  total_energy += amtToAdd;
                  total_co2 += amtToAdd/1e3 * co2_el[proj_year];
                }
              }
            }
          }
				}
				else if (selected_end_use === 'ventilation' || selected_end_use === 'refrigeration') {
					// [climate zone][building type]['electricity'][end use][tech type][year]

					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// Loop over all building types selected
						for (var i = 0; i < selected_buildings.length; i++) {
							// Loop over all tech types selected
							for (var j = 0; j < other_tt.length; j++) {
								amtToAdd = data[climate_zone[a]][selected_buildings[i]]['electricity'][selected_end_use][other_tt[j]][proj_year] * ss_el[proj_year];
								total_energy += amtToAdd;
								total_co2 += amtToAdd/1e3 * co2_el[proj_year];
							}
						}
					}
				}
				else if (selected_end_use === 'MELs') {
					// [climate zone][building type]['electricity']['MELs'][MEL type][year]

					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// Loop over all building types selected
						for (var i = 0; i < selected_buildings.length; i++) {
							amtToAdd = data[climate_zone[a]][selected_buildings[i]]['electricity'][selected_end_use][ft_only_sel][proj_year] * ss_el[proj_year];
							total_energy += amtToAdd;
							total_co2 += amtToAdd/1e3 * co2_el[proj_year];
						}
					}
				}
				else { // PCs and Non-PC Office Equipment
					// [climate zone][building type]['electricity'][end use][year]

					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// Loop over all building types selected
						for (var i = 0; i < selected_buildings.length; i++) {
							amtToAdd = data[climate_zone[a]][selected_buildings[i]]['electricity'][selected_end_use][proj_year] * ss_el[proj_year];
							total_energy += amtToAdd;
							total_co2 += amtToAdd/1e3 * co2_el[proj_year];
						}
					}
				}

				// Update total energy number displayed - rounding to 1 decimal place
				$('#energy-num').text(Math.round(total_energy*10)/10);

				// Update total CO2 number displayed - rounding to 1 decimal place
				$('#carbon-num').text(Math.round(total_co2*10)/10);
			});
		}
	});

	





	//////////////////////////////////////////////////////////////////////////////
	// Functions

	// Extract site to source energy conversion parameter based on fuel type and
	// the projection year selected by the user
	function primaryEnergyConversion(fuel_type, year) {
		// Look up the appropriate data based on the user's inputs and return the
		// reported primary energy conversion factor
		if (fuel_type === 'electricity (grid)' || fuel_type === 'electricity') { return ss_el[year]; }
		else { return 1; }
	}

	// Extract CO2 emissions intensity factor (from primary energy in quads
	// to million metric tons CO2) based on fuel type and the projection
	// year selected by the user
	function CO2Conversion(fuel_type, year) {
		// Look up the appropriate data based on the user's inputs and return the
		// reported CO2 emissions intensity factor
		if (fuel_type === 'electricity (grid)' || fuel_type === 'electricity') { return co2_el[year]; }
		else if (fuel_type === 'natural gas') { return co2_ng[year]; }
		else { return co2_ot[year]; }
	}

	// Insert a formatted 'row' div for a blank drop down menu into the HTML DOM 
	// with specified id tags for the row and content
	function insertNextDropdown(rowID, contentID, placementID) {
		// Generate HTML content for a new row with given ids for the row div
		// and the select object
		insertionText = "<div class='row row-end-use subtype' id='" + rowID +"'>"
						+ "<div class='col-md-12'>"
						+ "<select class='form-control' id='" + contentID + "'></select>"
						+ "</div>"
						+ "</div>";

		// Insert HTML content with custom tags
		$(placementID).after(insertionText);
	};

	// Insert a formatted 'row' div for a set of buttons into the HTML DOM 
	// with specified id tags for the row and content
	function insertNextButtonGroup(rowID, contentID, placementID) {
		// Generate HTML content for a new row with given ids for the row div
		// and the btn-group div
		insertionText = "<div class='row row-end-use subtype' id='" + rowID +"'>"
						+ "<div class='col-md-12'>"
						+ "<div class='btn-group-vertical' data-toggle='buttons' id='" + contentID + "'>"
						+ "</div>"
						+ "</div>"
						+ "</div>";

		// Insert HTML content with custom tags
		$(placementID).after(insertionText);
	}

	// Take name and value arrays (what appears to the user, and the keys used
	// in the JSON file, respectively) and insert them into the DOM at the
	// specified location to populate a drop down menu; support both direct 
	// use of arrays and also arrays subset by the specified index array
	function populateDropdown(contentID, content, names, values, index) {
		// index is an optional argument

		// Add to the initialized string the buttons to be generated
		if (typeof index === 'undefined') {
			for (var i = 0; i < names.length; i++) {
				content += '<option value="' + values[i] + '">' + names[i] + '</option>';
			}
		}
		else {
			for (var i = 0; i < index.length; i++) {
				content += '<option value="' + values[index[i]] + '">' + names[index[i]] + '</option>';
			}
		}
	
		// Insert content to HTML DOM at the location specified by contentID
		$('#' + contentID).append(content);
	}

	// Take name and value arrays (what appears to the user, and the keys used
	// in the JSON file, respectively) and insert them into the DOM at the
	// specified location to populate a button group; support both direct 
	// use of arrays and also arrays subset by the specified index array
	function populateButtonGroup(contentID, names, values, index) {
		// index is an optional argument

		// Initialize variable to hold new content
		var content = '';

		// Add to the initialized string the buttons to be generated
		if (typeof index === 'undefined') {
			for (var i = 0; i < names.length; i++) {
				content += '<label class="btn btn-default"><input type="checkbox" autocomplete="off" value="' + values[i] + '">' + names[i] + '</label>';
			}
		}
		else {
			for (var i = 0; i < index.length; i++) {
				content += '<label class="btn btn-default"><input type="checkbox" autocomplete="off" value="' + values[index[i]] + '">' + names[index[i]] + '</label>';
			}
		}

		// Insert content to HTML DOM at the location specified by contentID
		$('#' + contentID).append(content);
	}

	// Combine the insert and populate functions into a single function that
	// eliminates the need to define an ID for the button or select group
	// and removes the temporary ID needed between the two functions from the
	// DOM as a cleanup step before finishing
	function generateDropdown(rowID, placementID, content, names, values, index) {
		// index is an optional argument

		// Define temporary ID solely for use by the insert and populate functions
		var contentID = 'temporary-id';
		insertNextDropdown(rowID, contentID, placementID);
		populateDropdown(contentID, content, names, values, index);
		
		// Remove the temporary ID from the DOM
		$('#' + contentID).removeAttr('id');
	}

	function generateButtonGroup(rowID, placementID, names, values, index) {
		// index is an optional argument

		// Define temporary ID solely for use by the insert and populate functions
		var contentID = 'temporary-id';
		insertNextButtonGroup(rowID, contentID, placementID);
		populateButtonGroup(contentID, names, values, index);

		// Remove the temporary ID from the DOM
		$('#' + contentID).removeAttr('id');
	}

});