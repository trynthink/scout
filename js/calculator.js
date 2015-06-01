$(document).ready(function(){
	
	// Define upper and lower bounds for movement of affixed panel
	$('#calc-panel').affix({
		offset: {
			top: $('.jumbotron').outerHeight(),
			bottom: $('#footer').outerHeight(true)
		}
	});

	// Enable tooltips
	$(function () {
	  $('[data-toggle="tooltip"]').tooltip()
	})

	// Enable specific popover (for AIA climate zone image)
	var AIA_CZ_image_HTML = '<img width="100%" src="http://www.eia.gov/consumption/residential/reports/images/climatezone-lg.jpg">';
	$('#AIA-CZ-popover').popover({placement: 'right', content: AIA_CZ_image_HTML, html: true, container: 'body'});

	// Store needed data about site-to-source conversions and CO2 emissions
	// from the appropriate JSON database
	var ss_el, ss_ng, ss_ot, co2_el, co2_ng, co2_ot;
	$.getJSON('ss_co2_conversions.json', function(data){
		ss_el = data['electricity (grid)']['site to source conversion'];
		ss_ng = data['natural gas']['site to source conversion'];
		ss_ot = data['other']['site to source conversion'];
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
	populateDropdown('proj-year', '', yr_array, yr_array)
	$('#proj-year').val(default_year);



	// Initialize empty variables
	var resBuildings;
	var comBuildings;

	// Initialize variables with lists to be converted to selections
	// as needed in the market definition form
	var com_end_use = ['Heating', 'Ventilation', 'Cooling', 'Water Heating', 'Lighting', 'Cooking', 'Refrigeration', 'Computers', 'Electronics', 'Other'];
	var com_end_use_values;
	// Freezers, Dishwashers, Clothes Washers
	var res_end_use = ['Heating', 'Secondary Heating', 'Cooling', 'Fans and Pumps', 'Ceiling Fans', 'Lighting', 'Water Heating', 'Refrigeration', 'Cooking', 'Clothes Drying', 'Home Entertainment', 'Computers', 'Other'];
	var res_end_use_values = ['heating', 'secondary heating', 'cooling', 'fans & pumps', 'ceiling fan', 'lighting', 'water heating', 'refrigeration', 'cooking', 'drying', 'TVs', 'computers', 'other']

	var envelope = ['Windows (Conduction)', 'Windows (Radiation)', 'Walls', 'Roof', 'Ground', 'Infiltration'];
	var envelope_values = ['windows conduction', 'windows solar', 'wall', 'roof', 'ground', 'infiltration'];

	var fuel_type = ['Electricity', 'Natural Gas', 'Distillate', 'Solar', 'Other'];
	var fuel_type_values = ['electricity (grid)', 'natural gas', 'distillate', 'electricity (on site)', 'other fuel'];
	var heating_FT = [0, 1, 2, 4]; // Selection of applicable fuel types for each residential end use
	var sec_heating_FT = [0, 1, 2, 4];
	var cooling_FT = [0, 1];
	var water_heating_FT = [0, 1, 2, 3, 4];
	var cooking_FT = [0, 1, 4];
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
	var sec_heating_equip_values = ['secondary heating (kerosene)', 'secondary heating (wood)', 'secondary heating (LPG)', 'secondary heating (coal)']

	var cooling_equip = ['Central AC', 'Room/Window AC', 'Air-Source Heat Pump', 'Ground-Source Heat Pump', 'Heat Pump'];
	var cooling_equip_values = ['central AC', 'room AC', 'ASHP', 'GSHP', 'NGHP'];
	var cooling_equip_el = [0, 1, 2, 3];
	var cooling_equip_ng = [4];

	var lighting = ['General Service Lamp', 'Linear Fluorescent', 'Reflector', 'External/Outdoor Lighting'];
	var lighting_values = ['general service', 'linear fluorescent', 'reflector', 'external'];

	var entertainment = ['TVs', 'Set-top Boxes', 'DVD Players', 'Home Theater Systems', 'Video Game Systems'];
	var entertainment_values = ['TV', 'set top box', 'DVD', 'home theater & audio', 'video game consoles'];

	var computers = ['Desktops', 'Laptops', 'Monitors/Displays', 'Network Equipment'];
	var computers_values = ['desktop PC', 'laptop PC', 'monitors', 'network equipment'];

	var other = ['Clothes Washing', 'Dishwashers', 'Freezers', 'Other Electric Loads'];
	var other_values = ['clothes washing', 'dishwasher', 'freezers', 'other MELs'];


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

	// Define variable to record status of selection (selection = 1)
	var bldgs_selected = 0;

	// Building type selection actions
	$('#residential-bldgs').on('click', function (){
		
		// Put the selected residential building types into a list
		resBuildings = $('#residential-bldgs').val();

		// Clear end use drop down when no residential buildings are selected
		if (resBuildings === null) {
			// Clear drop down menu
			$('#end-use').empty();

			// Clear all subsequent/child content
			$('.subtype').remove();

			// Update the status variable
			bldgs_selected = 0;
		}

		// If at least one residential building type is selected and none were
		// selected before, update the list of end use categories
		if (resBuildings !== null && resBuildings !== undefined) {
			if (bldgs_selected === 0) {
				// Initialize drop down menu contents
				var end_use_dropdown = '<option disabled selected> -- Select an End Use -- </option>';

				// Update the status variable
				bldgs_selected = 1;

				// Populate the selected drop down menu in the DOM with choices
				populateDropdown('end-use', end_use_dropdown, res_end_use, res_end_use_values)
			}
		}		
	});

	var selected_end_use; // Revised global scope

	// End use selection actions (generating further selections)
	$('#end-use').change(function(){
		// Identify selected end use
		selected_end_use = $('#end-use').val();

		// CLEAR OUT ANY ADDED DROPDOWN OR SELECTION MENUS - anything with ID subtype
		$('.subtype').remove();

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
			$('#end-use-row').after(eqEnvRadioBtn)
		}
		else if (selected_end_use === 'water heating' || selected_end_use === 'cooking' || selected_end_use === 'drying') {
			// Identify the appropriate fuel types to display for the selected end use
			// Need to create new variable for the ID for each possible dropdown
			// since some selected_end_use values have spaces, which aren't
			// allowed in IDs
			if (selected_end_use === 'water heating') {var ft_select = water_heating_FT;}
			else if (selected_end_use === 'cooking') {var ft_select = cooking_FT;}
			else {var ft_select = drying_FT;}

			insertNextDropdown('last', 'ft-only-dd', '#end-use-row');

			// (Re)define variable to hold choices in dropdown
			var ft_dropdown = '<option disabled selected> -- Select a Fuel Type -- </option>';

			// Populate the selected drop down menu in the DOM with choices
			populateDropdown('ft-only-dd', ft_dropdown, fuel_type, fuel_type_values, ft_select);
		}
		else if (selected_end_use === 'lighting') {
			insertNextButtonGroup('last-tt', selected_end_use, '#end-use-row');

			// Add lighting technology type buttons to HTML DOM
			populateButtonGroup(selected_end_use, lighting, lighting_values);
		}
		else if (selected_end_use === 'TVs') {
			insertNextButtonGroup('last-tt', selected_end_use, '#end-use-row');

			// Add entertainment technology type buttons to HTML DOM
			populateButtonGroup(selected_end_use, entertainment, entertainment_values);
		}
		else if (selected_end_use === 'computers') {
			insertNextButtonGroup('last-tt', selected_end_use, '#end-use-row');

			// Add computers technology type buttons to HTML DOM
			populateButtonGroup(selected_end_use, computers, computers_values);
		}
		else if (selected_end_use === 'other') {
			// Create space for next dropdown
			insertNextButtonGroup('last-tt', selected_end_use, '#end-use-row');

			// Add other technology type buttons to HTML DOM
			populateButtonGroup(selected_end_use, other, other_values);
		}
		// else terminal categories (fans & pumps, ceiling fan, 
		// refrigeration), no action required
	});

	// Detect selected radio button (equipment/envelope) 
	// and respond accordingly
	$(document).on('change', '#eq-env-radio', function(){
		// Identify element of radio button selected
		var radio_selection = $('input[name=eq-env]:checked').val();

		if (radio_selection === 'demand') {
			// Remove any equipment content
			$('.row.subtype.supply').remove();

			// Create space for envelope buttons
			insertNextButtonGroup('env-buttons', radio_selection, '#eq-env-radio');

			// Add envelope buttons to HTML DOM
			populateButtonGroup(radio_selection, envelope, envelope_values);

			// Add 'envelope' class to button group just added so that it
			// will be removed automatically if the radio button selection
			// is changed from envelope to equipment
			$('#env-buttons').addClass(radio_selection);
		}
		else {
			// Remove any envelope content
			$('.row.subtype.demand').remove();

			// Create space for fuel type selection
			insertNextDropdown('fuel-type', 'HVAC', '#eq-env-radio');

			// Identify the appropriate fuel types to display for the selected end use
			if (selected_end_use === 'heating') {var ft_select = heating_FT;}
			else if (selected_end_use === 'secondary heating') {var ft_select = sec_heating_FT;}
			else {var ft_select = cooling_FT;}

			// (Re)define variable to hold choices in dropdown
			var ft_dropdown = '<option disabled selected> -- Select a Fuel Type -- </option>';

			// Populate the selected drop down menu in the DOM with choices
			populateDropdown('HVAC', ft_dropdown, fuel_type, fuel_type_values, ft_select);

			// Add 'equipment' class to dropdown just added so that it
			// will be removed automatically if the radio button selection
			// is changed from equipment to envelope
			$('#fuel-type').addClass('supply');
		}
	});

	// Detect selected fuel type (for HVAC end uses) and display the
	// appropriate technology types
	$(document).on('change', '#fuel-type', function(){
		// Determine what fuel type was selected
		var HVAC_FT = $('option:selected', '#fuel-type').val();
		
		// Clear any existing equipment type buttons
		$('#eq-buttons').remove();

		// Generate new button field for equipment types
		insertNextButtonGroup('eq-buttons', 'eq-buttons-list', '#fuel-type');

		// Add the appropriate buttons to the appropriate HTML DOM element
		if (selected_end_use === 'heating') {
			if (HVAC_FT === 'electricity (grid)') {var eq_select = heating_equip_el;}
			else if (HVAC_FT === 'natural gas') {var eq_select = heating_equip_ng;}
			else if (HVAC_FT === 'distillate') {var eq_select = heating_equip_ds;}
			else {var eq_select = heating_equip_ot;}

			// Add heating equipment type buttons to HTML DOM
			populateButtonGroup('eq-buttons-list', heating_equip, heating_equip_values, eq_select);
		}
		else if (selected_end_use === 'secondary heating') {
			if (HVAC_FT === 'other fuel') {
				// Add secondary heating equipment type buttons to HTML DOM
				populateButtonGroup('eq-buttons-list', sec_heating_equip, sec_heating_equip_values);
			}
		}
		else {
			if (HVAC_FT === 'electricity (grid)') {var eq_select = cooling_equip_el}
			else {var eq_select = cooling_equip_ng}

			// Add cooling equipment type buttons to HTML DOM
			populateButtonGroup('eq-buttons-list', cooling_equip, cooling_equip_values, eq_select);
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
		
		// Sum the totals for the selected data
		$.getJSON('microsegments_out.json', function(data){

			// Define intermediate quantity variable to store each quantity to
			// be added to the total
			var amtToAdd = 0;

			// Identify appropriate query based on the end use
			if (selected_end_use === 'heating' || selected_end_use === 'secondary heating' || selected_end_use === 'cooling') {
				// [climate zone][building type][fuel type][end use][supply/demand][tech type]['energy'][year]

				// SINCE GLOBAL SCOPING THESE VARIABLES DIDN'T MAKE THEM VISIBLE HERE
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
						for (var i = 0; i < resBuildings.length; i++) {
							// Loop over all tech types selected
							for (var j = 0; j < hvac_tt.length; j++) {
								amtToAdd = data[climate_zone[a]][resBuildings[i]][HVAC_FT][selected_end_use][radio_selection][hvac_tt[j]]['energy'][proj_year] * energy_conv;
								total_energy += amtToAdd;
								total_co2 += amtToAdd/1e9 * co2_conv;
							}
						}
					}
				}
				else {
					// Identify the applicable fuel types
					if (selected_end_use === 'heating') {var ft_select_f = heating_FT}
					else if (selected_end_use === 'secondary heating') {var ft_select_f = sec_heating_FT}
					else {var ft_select_f = cooling_FT}

					// Loop over all climate zones selected
					for (var a = 0; a < climate_zone.length; a++) {
						// For demand, loop over all possible fuel types
						for (var k = 0; k < ft_select_f.length; k++) {
							var energy_conv = primaryEnergyConversion(ft_select_f[k], proj_year);
							var co2_conv = CO2Conversion(ft_select_f[k], proj_year);
							// Loop over all building types selected
							for (var i = 0; i < resBuildings.length; i++) {
								// Loop over all tech types selected
								for (var j = 0; j < hvac_tt.length; j++) {
									amtToAdd = data[climate_zone[a]][resBuildings[i]][fuel_type_values[ft_select_f[k]]][selected_end_use][radio_selection][hvac_tt[j]]['energy'][proj_year] * energy_conv;
									total_energy += amtToAdd;
									total_co2 += amtToAdd/1e9 * co2_conv;
								}
							}
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
					for (var i = 0; i < resBuildings.length; i++) {
						amtToAdd = data[climate_zone[a]][resBuildings[i]][ft_only_sel][selected_end_use]['energy'][proj_year] * energy_conv;
						total_energy += amtToAdd;
						total_co2 += amtToAdd/1e9 * co2_conv;
					}
				}
			}
			else if (selected_end_use === 'lighting' || selected_end_use === 'computers' || selected_end_use === 'TVs' || selected_end_use === 'other') {
				// [climate zone][building type]['electricity (grid)'][end use][tech type]['energy'][year]

				// Loop over all climate zones selected
				for (var a = 0; a < climate_zone.length; a++) {
					// Loop over all building types selected
					for (var i = 0; i < resBuildings.length; i++) {
						// Loop over all tech types selected
						for (var j = 0; j < other_tt.length; j++) {
							amtToAdd = data[climate_zone[a]][resBuildings[i]]['electricity (grid)'][selected_end_use][other_tt[j]]['energy'][proj_year] * ss_el[proj_year];
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
					for (var i = 0; i < resBuildings.length; i++) {
						amtToAdd = data[climate_zone[a]][resBuildings[i]]['electricity (grid)'][selected_end_use]['energy'][proj_year] * ss_el[proj_year];
						total_energy += amtToAdd;
						total_co2 += amtToAdd/1e9 * co2_el[proj_year];
					}
				}
			}

			// Update total energy number displayed
			// NOTE CONVERSION FROM MMBTU TO QUADS
			// AND ROUNDING TO MAXIMUM OF 3 SIG FIGS
			$('#energy-num').text(Math.round(total_energy/1e6)/1e3);

			// Update total CO2 number displayed
			$('#carbon-num').text(Math.round(total_co2*1e3)/1e3);
		});
	});

	





	//////////////////////////////////////////////////////////////////////////////
	// Functions

	// // Extract site to source energy conversion parameter based on fuel type and
	// // the projection year selected by the user
	// function primaryEnergyConversion(fuel_type, year, callback) {
	// 	// Assess fuel type lookup parameter
	// 	if (fuel_type === 'electricity (grid)' || fuel_type === 'natural gas') { var lookup_ft = fuel_type; }
	// 	else { var lookup_ft = 'other'; }

	// 	// Look up the appropriate data based on the user's inputs and return the
	// 	// reported primary energy conversion factor
	// 	$.getJSON('ss_co2_conversions.json', function(data){
	// 		callback(data[lookup_ft]['site to source conversion'][year]);
	// 	});
	// };

	// Extract site to source energy conversion parameter based on fuel type and
	// the projection year selected by the user
	function primaryEnergyConversion(fuel_type, year) {
		// Look up the appropriate data based on the user's inputs and return the
		// reported primary energy conversion factor
		if (fuel_type === 'electricity (grid)') { return ss_el[year]; }
		else if (fuel_type === 'natural gas') { return ss_ng[year]; }
		else { return ss_ot[year]; }
	};

	// Extract CO2 emissions intensity factor (from primary energy in quads
	// to million metric tons CO2) based on fuel type and the projection
	// year selected by the user
	function CO2Conversion(fuel_type, year) {
		// Look up the appropriate data based on the user's inputs and return the
		// reported CO2 emissions intensity factor
		if (fuel_type === 'electricity (grid)') { return co2_el[year]; }
		else if (fuel_type === 'natural gas') { return co2_ng[year]; }
		else { return co2_ot[year]; }
	};

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
						+ "<div class='btn-group-vertical' data-toggle='buttons' id='" + contentID + "'></select>"
						+ "</div>"
						+ "</div>"
						+ "</div>";

		// Insert HTML content with custom tags
		$(placementID).after(insertionText);
	};


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
	};

});