$(document).ready(function(){

	////////////////////////////////////////////////////////////////////////////
	// Homepage
	////////////////////////////////////////////////////////////////////////////

	/////////////////////////////////////////////////////////////////////
	// Place text overlay on homepage based on the height of the jumbotron
	
	// Define function that positions text based on the jumbotron height
	function frontPageTextPosition() {
		$('.special').each(function(){
			$(this).css('margin-top', $(this).parents('.jumbotron').height()-$(this).height())
		});
	}; // end frontPageTextPosition

	// Call function to perform initial placement on page load
	frontPageTextPosition();

	// Call function when window is resized, but only after the 
	// specified number of milliseconds
	var resizeTimer = null;
	$(window).bind('resize', function(){
		if (resizeTimer) clearTimeout(resizeTimer);
		resizeTimer = setTimeout(frontPageTextPosition(), 100);
	});
	


	////////////////////////////////////////////////////////////////////////////
	// Dashboard
	////////////////////////////////////////////////////////////////////////////

	

	////////////////////////////////////////////////////////////////////////////
	// Measure Database
	////////////////////////////////////////////////////////////////////////////

	/////////////////////////////////////////////////////////////////////
	// Populate table of measures based on JSON data

	// Define function to convert data to table format
	function populateMeasuresTableFromJSON(measuresList) {
		// Desired data hard-coded in column appearance order
		var columns = ['name', 'energy_efficiency', 'energy_efficiency_units', 'component_cost', 'cost_units', 'installed_cost', 'cost_units', 'market_entry_year', 'product_lifetime'];

		// Reformat data from the JSON file by list item
		for (var i = 0 ; i < measuresList.length ; i++) {
			var row$ = $('<tr/>').attr({
					'data-toggle': 'modal',
					'data-id': i, // REPLACE WITH A FUNCTION INSERTING A UNIQUE IDENTIFIER
					'data-target':'#measureModal'
				});

			for (var colIndex = 0 ; colIndex < columns.length ; colIndex++) {
				var cellValue = measuresList[i][columns[colIndex]];
				row$.append($('<td/>').html(cellValue));
			}
			$('#measure-list').append(row$);
		}
	} // end populateMeasuresTableFromJSON

	// // Obtain data from JSON measure database to populate table
	// $.getJSON('measures.json', function(the_stuff){
	// 	populateMeasuresTableFromJSON(the_stuff)
	// });


	/////////////////////////////////////////////////////////////////////
	// Set up modal with measure details based on user-selected measure 
	
	// Configure modal content upon clicking a table row
	$('#measure-list').on('click', 'tr[data-target]', function(){
		// Identify data-id tag content for the table row clicked
		var getRowID = $(this).data('id');

		// INSERT AJAX CALL AND OTHER DETAILS HERE

		// Update modal content with text incorporating row ID
		$('#measureDetails').html($('<p>ID of row selected: ' + getRowID + '</p>'));
	});
	


	////////////////////////////////////////////////////////////////////////////
	// Market Calculator
	////////////////////////////////////////////////////////////////////////////

	


});