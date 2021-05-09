# ============================================================================
# Load required packages and files
# ============================================================================

# Define function to load required packages
package_loader <- function(pkg_list) {
  options(warn=-1) # Suppress sometimes misleading package load warning messages
  # For Windows users, install packages in a directory with administrator priveleges
  if (Sys.info()[1]=="Windows"){
  	# Find Windows user name
  	user_name = Sys.getenv("USERNAME")
  	# Create directory for package install (default used by R GUI)
  	dir_path = file.path('C:', 'Users', user_name, 'Documents','R', 'win-library')
  	dir.create(dir_path, showWarnings = FALSE, recursive = TRUE)
  }else{dir_path = NULL}
  # Run through and install/load required packages	
  for(pkg_name in pkg_list){
    # require returns TRUE invisibly if it was able to load package from either the
    # default R library path or, in the case of a Windows user, a personal path that the user
    # has administrator rights for 
    if (!require(pkg_name, character.only = TRUE, quietly = TRUE, warn.conflicts=FALSE) &&
	    !require(pkg_name, lib.loc = dir_path, character.only = TRUE,
               quietly = TRUE, warn.conflicts=FALSE)){
      # If package was not able to be loaded then download/install using default mirror, notify user
      message("Installing R package ", pkg_name)
      install.packages(pkg_name, repos='http://cran.us.r-project.org', lib = dir_path, quiet=TRUE)
      # Try alternate install mirror if first mirror didn't install package to library directory
      if (!require(pkg_name, lib.loc = dir_path, character.only = TRUE,
                   quietly = TRUE, warn.conflicts=FALSE)){
	  	install.packages(pkg_name, repos='http://cran.cnr.berkeley.edu', lib = dir_path, quiet=TRUE)
	  }
      # Load package after installing
      library(pkg_name, character.only = TRUE, quietly=TRUE, warn.conflicts=FALSE, lib.loc = dir_path)
    }
  }
}

# Load indicated packages
package_loader(c("RColorBrewer", "rjson", "WriteXLS", "stringr", "TeachingDemos", "scales"))

# Get current working directory path
base_dir = getwd()
# Import uncompeted ECM energy, carbon, and cost data
uncompete_results<-fromJSON(file = file.path(base_dir, 'supporting_data','ecm_prep.json'))
# Import competed ECM energy, carbon, and cost data
compete_results_ecms<-fromJSON(file = file.path(base_dir, 'results','ecm_results.json'))
#.Import competed energy, carbon, and cost data summed across all ECMs
compete_results_agg<-fromJSON(file = file.path(base_dir, 'results','agg_results.json'))
# Combine aggregate and individual-level ECM results
compete_results<-c(compete_results_agg, compete_results_ecms)

# ============================================================================
# Set high-level variables needed across multiple plot types
# ============================================================================

# Set ECM adoption scenarios
adopt_scenarios <- c('Max adoption potential')
# Set ECM competition scenarios
comp_schemes <- c('uncompeted', 'competed')
# Set full list of ECM names from results file
meas_names <- names(compete_results)
# Set list of ECM names excluding 'All ECMs' (representing results summed across all ECMs)
# and the high-level information about site-source energy calculations (stored in 'Energy Output Type' key)
meas_names_no_all <- meas_names[(meas_names!= "All ECMs" & meas_names!= "Energy Output Type")]
# Order the list of ECM names excluding 'All ECMs'
meas_names_no_all <- meas_names_no_all[order(meas_names_no_all)]
# Combine the 'All ECMs' name with the ordered list of the individual ECM names
meas_names <- c('All ECMs', meas_names_no_all)
# Set years in modeling time horizon and reorganize in ascending order
years<-row.names(as.matrix(
  compete_results[[meas_names[1]]]$'Markets and Savings (Overall)'[[
  adopt_scenarios[1]]]$'Baseline Energy Use (MMBtu)'))
# Set an intended starting and ending year for the plotted results
start_yr = 2015
end_yr = max(years)


# Set the years to take a 'snapshot' of certain results in;
# if the measure set was prepared with public cost adders, set
# this year to 2020, as these adders are reflective of current/
# near term utility conditions from EPA data; also flag for the particular
# type of public cost adder (low/high), if any
if (grepl("PHC", meas_names[2], fixed=TRUE) == TRUE){
  snap_yr = "2020"
  snap_yr_set = c("2020")
  if (grepl("low", meas_names[2], fixed=TRUE) == TRUE){
      phc_flag = "low"
  }else{
      phc_flag = "high"
  }
}else{
  snap_yr = "2050"
  snap_yr_set = c("2030", "2050")
  phc_flag = FALSE}

# Filter and order the year range
years<-years[(years>=start_yr)&(years<=end_yr)]
years<-years[order(years)]

# Set list of possible climate zones and associated colors/legend entries for aggregate savings
# and cost effectiveness plots

# Set various region names lists
aia_reg_names <- c("AIA CZ1", "AIA CZ2", "AIA CZ3", "AIA CZ4", "AIA CZ5")
emm_reg_names <- c(
  'TRE', 'FRCC', 'MISW', 'MISC', 'MISE', 'MISS',
  'ISNE', 'NYCW', 'NYUP', 'PJME', 'PJMW', 'PJMC',
  'PJMD', 'SRCA', 'SRSE', 'SRCE', 'SPPS', 'SPPC',
  'SPPN', 'SRSG', 'CANO', 'CASO', 'NWPP', 'RMRG', 'BASN')
state_names <- c(
  'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'DC', 'FL',
  'GA', 'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME',
  'MD', 'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH',
  'NJ', 'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI',
  'SC', 'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI',
  'WY')

# Pull czones from first available ECM
czones_test = toString(compete_results[[meas_names[2]]]$'Filter Variables'$'Applicable Regions')
# Check for AIA regional breakouts; if not there, check for EMM regional breakouts;
# if not there, assume state breakouts
if (grepl("AIA", czones_test, fixed=TRUE) == TRUE){
  # Set region legend names
  czones_out<-aia_reg_names
  # Set region legend colors
  czones_out_col<-brewer.pal(length(czones_out), "Dark2")
  czones_out_lgnd<-czones_out
  # Set alternate region flags
  emm_flag = FALSE
  state_flag = FALSE
}else if (any(grepl(paste(emm_reg_names, collapse="|"), czones_test) == TRUE)){
  # Set region legend names
  czones_out<-emm_reg_names
  # Set region legend colors; in the EMM case, extend the color list to
  # accomodate the larger number of region categories
  czones_out_col<-colorRampPalette(brewer.pal(8, "Dark2"))(length(czones_out))
  czones_out_lgnd<-czones_out
  # Set alternate region flags
  emm_flag = TRUE
  state_flag = FALSE
}else{
  # Set region legend names
  czones_out<-state_names
  # Set region legend colors; in the state case, extend the color list to
  # accomodate the larger number of region categories
  czones_out_col<-colorRampPalette(brewer.pal(8, "Dark2"))(length(czones_out))
  czones_out_lgnd<-czones_out
  # Set alternate region flags
  emm_flag = FALSE
  state_flag = TRUE 
}


# Set list of possible building classes and associated colors for aggregate savings plot
bclasses_out_agg<-c('Residential (New)', 'Residential (Existing)',
                'Commercial (New)', 'Commercial (Existing)')
bclasses_out_agg_col<-brewer.pal(length(bclasses_out_agg), "Dark2")
# Set list of possible building classes and associated shapes/legend entries for
# cost effectiveness plot
bclasses_out_finmets<-c(
	list(c('Residential (New)', 'Residential (Existing)')),
    list(c('Commercial (New)', 'Commercial (Existing)')))
bclasses_out_finmets_shp<-c(21, 22)
bclasses_out_finmets_lgnd<-c('Residential', 'Commercial')
# Set list of possible end uses and associated colors/legend entries for
# aggregate savings plot
euses_out_agg<-c('Heating (Equip.)', 'Cooling (Equip.)', 'Heating (Env.)', 'Cooling (Env.)',
	'Ventilation', 'Lighting', 'Water Heating', 'Refrigeration', 'Cooking', 'Electronics', 'Other')
euses_out_agg_col<-brewer.pal(length(euses_out_agg), "Paired")
# Set list of possible end use names from the raw data and associated colors/legend entries for
# cost effectiveness plot
euses_out_finmets<-c(
	list(c('Heating (Equip.)', 'Cooling (Equip.)', 'Ventilation')),
	list(c('Heating (Env.)', 'Cooling (Env.)')),
	list('Lighting'),
    list('Water Heating'), list('Refrigeration'), list('Cooking'),
    list('Computers and Electronics'), list('Other'))
euses_out_finmets_col<-brewer.pal(length(euses_out_finmets), "Dark2")
euses_out_finmets_lgnd<-c(
  'HVAC', 'Envelope', 'Lighting', 'Water Heating', 'Refrigeration',
  'Cooking', 'Electronics', 'Other')

# Determine axis label parameters to use across plots

# Determine site vs. source energy and (if source) captured vs. fossil
# site-source conversion calculation methods, to write to label
if (compete_results_agg$`Energy Output Type`[1] == "site"){
  e_site_source = "Site Energy"
  ss_calc = ""
}else if (compete_results_agg$`Energy Output Type`[1] == "captured"){
  e_site_source = "Primary Energy"
  ss_calc = ", CE S-S"
}else{
  e_site_source = "Primary Energy"
  ss_calc = ", FF S-S"
}
# Case without TSV metrics - set conversion factors, units, and
# axis scaling factors for aggregate savings plots
if (compete_results_agg$`Energy Output Type`[2] == "NA"){ 
  # If results are EMM-resolved and public health cost adders
  # are not present, convert quads to TWh for reporting;
  # if results are state-resolved, used TBtu for reporting
  if ((emm_flag == TRUE)&(phc_flag == FALSE)){
    e_conv_emm_st = 293.07
    e_axis_units = "TWh"
  }else if (state_flag == TRUE){
    e_conv_emm_st = 1000
    e_axis_units = "TBtu"
  }else{
    e_conv_emm_st = 1
    e_axis_units = "Quads"
  }
  # No further conversions needed for CO2 or cost
  c_conv_emm = 1
  c_axis_units = "Mt"
  cs_conv_emm = 1
  cs_axis_units = "Billion $"
  # Set scaling for aggregate savings plots
  cex_ann_ax = 0.85
  cex_cum_ax = 0.85
  # No further TSV metric assumptions text to append
  append_txt = ")"
# Case with TSV metrics - set conversion factors, units, scaling factors
# for aggregate savings plots, and text to append to axis label indicating
# TSV metric assumptions
}else{
  # When TSV metrics are present, assume that GW (hourly savings, abbreviated in
  # the output as "Hr.") or GWh (multi-hour savings, abbreviated in the output as
  # "Prd.") is the correct energy unit to use (savings will generally be smaller)
  e_conv_emm_st = 293071.07
  if (compete_results_agg$`Energy Output Type`[1] == "Prd."){
    e_axis_units = "GWh"
  }else{
    e_axis_units = "GW"
  }
  # When TSV metrics are present, convert million metric tons to thousand metric
  # tons and billion $ to million $ (savings will generally be smaller)
  c_conv_emm = 1000
  c_axis_units = "Tt"
  cs_conv_emm = 1000
  cs_axis_units = "Million $"
  # Set scaling for aggregate savings plots (a bit lower than when there are no
  # TSV metrics, to accomodate additional axis label text for TSV assumptions)
  cex_ann_ax = 0.75
  cex_cum_ax = 0.75
  # Set text to append to axis label indicating key elements of the TSV metrics
  # assumptions
  append_txt = paste(paste(", ",
      compete_results_agg$`Energy Output Type`[2], " ",
      compete_results_agg$`Energy Output Type`[3], " ",
      compete_results_agg$`Energy Output Type`[4], " ",
      compete_results_agg$`Energy Output Type`[5], ")", sep=""))
}

# ============================================================================
# Set high-level variables needed to generate individual ECM plots
# ============================================================================

# Set names of plot files and axes
# Plot of individual ECM energy, carbon, and cost totals
file_names_ecms <- c('Total Energy', 'Total CO2', 'Total Cost')
plot_names_ecms <- c('Total Energy', expression("Total"~ CO[2]), 'Total Cost')
# Set individual ECM plot y axis labels
plot_axis_labels_ecm<-c(
    paste(e_site_source, ' (', e_axis_units, ss_calc, append_txt, sep=""),
    as.expression(bquote(CO[2] ~ "Emissions ("*.(c_axis_units)*.(append_txt))),
    paste('Energy Cost (', cs_axis_units, append_txt, sep=""))
# Set colors for uncompeted baseline, efficient and low/high results
plot_col_uc_base = "gray60"
plot_col_uc_eff = "gray80"
plot_col_uc_lowhigh = "gray90"

# Set variable names to use in accessing all uncompeted energy, carbon, and cost results from JSON data
var_names_uncompete <- c('energy', 'carbon', 'cost')
results_folder_names <- c('energy', 'co2', 'cost')
# Set output units for each variable type
var_units <- c(e_axis_units, c_axis_units, cs_axis_units)
# Set variable names to use in accessing competed baseline energy, carbon, and cost results from
# JSON data. Note that each variable potentially has a '(low)' and '(high)' variant in the JSON.
var_names_compete_base_m <- c(
  'Baseline Energy Use (MMBtu)', 'Baseline CO₂ Emissions (MMTons)', 'Baseline Energy Cost (USD)')
var_names_compete_base_l <- c(
  'Baseline Energy Use (low) (MMBtu)', 'Baseline CO₂ Emissions (low) (MMTons)',
  'Baseline Energy Cost (low) (USD)')
var_names_compete_base_h <- c(
  'Baseline Energy Use (high) (MMBtu)', 'Baseline CO₂ Emissions (high) (MMTons)',
  'Baseline Energy Cost (high) (USD)')
# Set variable names to use in accessing competed efficient energy, carbon, and cost results from
# JSON data. Note that each variable potentially has a '(low)' and '(high)' variant in the JSON.
var_names_compete_eff_m <- c(
  'Efficient Energy Use (MMBtu)', 'Efficient CO₂ Emissions (MMTons)', 'Efficient Energy Cost (USD)')
var_names_compete_eff_l <- c(
  'Efficient Energy Use (low) (MMBtu)', 'Efficient CO₂ Emissions (low) (MMTons)',
  'Efficient Energy Cost (low) (USD)') 
var_names_compete_eff_h <- c(
  'Efficient Energy Use (high) (MMBtu)', 'Efficient CO₂ Emissions (high) (MMTons)',
  'Efficient Energy Cost (high) (USD)')

# ============================================================================
# Set high-level variables needed to generate aggregated savings plots
# ============================================================================

# File names for aggregated ECM savings plots
plot_names_agg <- c('Total Energy Savings', 'Total Avoided CO2', 'Total Cost Savings')
# Titles for aggregated ECM savings plots
plot_titles_agg <- c('Energy Savings', expression("Avoided"~ CO[2]), 'Cost Savings')
# Set aggregate annual/cumulative savings plot y axis labels
plot_axis_labels_agg_ann<-c(
    paste('Annual ', e_site_source, ' Savings (', e_axis_units, ss_calc, append_txt, sep=""),
    as.expression(bquote("Annual Avoided"~ CO[2] ~ "Emissions ("*.(c_axis_units)*.(append_txt))),
    paste('Annual Energy Cost Savings (', cs_axis_units, append_txt, sep=""))
plot_axis_labels_agg_cum<-c(
    paste('Cumulative ', e_site_source, ' Savings (', e_axis_units, ss_calc, append_txt, sep=""),
    as.expression(bquote("Cumulative Avoided"~ CO[2] ~ "Emissions ("*.(c_axis_units)*.(append_txt))),
    paste('Cumulative Energy Cost Savings (', cs_axis_units, append_txt, sep=""))
# Set names of variables used to retrieve savings data to aggregate
var_names_compete_save <- c(
  'Energy Savings (MMBtu)', 'Avoided CO₂ Emissions (MMTons)', 'Energy Cost Savings (USD)')
# Set names of variables to filter aggregated savings
filter_var<-c('Climate Zone', 'Building Class', 'End Use')
# Set transparent background for legend
transparent_back<-alpha("white", 0.5)

# ============================================================================
# Set high-level variables needed to generate ECM cost effectiveness plots
# ============================================================================

# Names for ECM cost effectiveness plots
plot_names_finmets = c('Cost Effective Energy Savings', 'Cost Effective Avoided CO2',
                       'Cost Effective Operation Cost Savings') 
# X axis labels for cost effectiveness plots
plot_axis_labels_finmets_x<-c(
    paste(snap_yr, " ", e_site_source, ' Savings (Competed, ', e_axis_units, ss_calc, append_txt, sep=""),
    as.expression(bquote(.(snap_yr) ~ "Avoided" ~ CO[2] ~ "Emissions (Competed, "*.(c_axis_units)*.(append_txt))),
    paste(snap_yr, ' Energy Cost Savings (Competed, ', cs_axis_units, append_txt, sep=""))
# Y axis labels for cost effectiveness plots
plot_axis_labels_finmets_y<-c(
	"IRR (%)", "Payback (years)", "CCE ($/MMBtu saved)", expression("CCC ($/t" ~ CO[2] ~ " avoided)"))
# Financial metric titles
plot_title_labels_finmets<-c(
	"Internal Rate of Return (IRR)", "Simple Payback", "Cost of Conserved Energy (CCE)",
	expression("Cost of Conserved" ~ CO[2] ~ "(CCC)"))
# Default plot limits for each financial metric
plot_lims_finmets <- c(
	list(c(-50, 150)), list(c(0, 25)), list(c(-50, 150)), list(c(-500, 1000)))
# Cost effectiveness threshold lines for each financial metric
plot_ablines_finmets <- c(0, 5, 13, 73)
# Financial metric type and key names for retrieving JSON data on each
fin_metrics <- c('IRR (%)', 'Payback (years)', 'Cost of Conserved Energy ($/MMBtu saved)',
                 'Cost of Conserved CO₂ ($/MTon CO₂ avoided)')
# ============================================================================
# Set high-level variables needed to generate XLSX data
# ============================================================================
# Define cost-effectiveness metrics column names
xlsx_names_finmets <- c(paste("IRR (%),", snap_yr),
					    paste("Payback (years),", snap_yr),
					    paste("CCE ($/MMBtu saved),", snap_yr),
					    paste("CCC ($/tCO2 avoided),", snap_yr))

# ============================================================================
# Loop through all adoption scenarios, plotting variables, ECMs, and
# competition scenarios, gather data needed for plots, and implement plots 
# ============================================================================

# Loop through all adoption scenarios
for (a in 1:length(adopt_scenarios)){

  # Set plot colors for competed baseline, efficient, and low/high results
  # (varies by adoption scenario); also set Excel summary data file name for adoption scenario
  if (adopt_scenarios[a] == "Technical potential"){
    # Set plot colors
    plot_col_c_base = "midnightblue"
    plot_col_c_eff = "lightskyblue"
    # # Set Excel summary data file name
    xlsx_file_name = file.path(base_dir, 'results', 'plots', 'tech_potential', "Summary_Data-TP.xlsx")
  }else{
    # Set plot colors
    plot_col_c_base = "red3"
    plot_col_c_eff = "pink"
    # # Set Excel summary data file name
    xlsx_file_name = file.path(base_dir, 'results', 'plots', 'max_adopt_potential',
                               "Summary_Data-MAP.xlsx")
  }
  
  # Preallocate list for variable names to be used later to export data
  # to xlsx-formatted Excel files
  xlsx_var_name_list <- vector("character", length=length(var_names_uncompete))

  # Loop through all plotting variables
  for (v in 1:length(var_names_uncompete)){

    # Finalize column names for the annual total energy, carbon, or cost results that are written
    # to the XLSX file
    xlsx_names_years = matrix(NA, length(years))
    for (yn in (1:length(xlsx_names_years))){
    	# Append variable units to each year name
    	xlsx_names_years[yn] = paste(years[yn], " (", var_units[v], ")", sep="")
    }
    
    # Define all column names for XLSX file
	col_names_xlsx<- c('ECM Name', 'Results Scenario', 'Climate Zones', 'Building Classes', 'End Uses',
					   xlsx_names_finmets, xlsx_names_years)

    # Initialize data frame to write to Excel worksheet (note: number of rows equals to
    # number of ECMs * number of results scenarios (baseline/efficient + competed/uncompeted) plus
    # two additional rows to accommodate baseline/efficient competed results summed across all ECMs)
    xlsx_data<-data.frame(matrix(ncol = length(col_names_xlsx),
                                nrow = (length(meas_names)*4 + 2)))
    # Set column names for the worksheet
    colnames(xlsx_data) = col_names_xlsx

    # Set a factor to convert the results data to final plotting units for given variable
    # (quads for energy, Mt for CO2, and billion $ for cost)
    if ((var_names_uncompete[v] == "energy") | (var_names_uncompete[v] == "cost")){
      unit_translate = 1/1000000000 # converts energy from MBtu -> quads or cost from $ -> billion $
        # Layer on a second conversion factor to handle cases where alternate EMM regions are used
        # (energy goes to TWh and/or TSV metrics are used (energy goes to GW/GWh, cost goes to million $))
        if (var_names_uncompete[v] == "energy"){
          unit_translate = unit_translate * e_conv_emm_st
        }else if (var_names_uncompete[v] == "cost"){
          unit_translate = unit_translate * cs_conv_emm
        }
      }else{
        unit_translate = 1 # CO2 results data are already imported in Mt units
        # Layer on a second conversion factor to handle cases where TSV metrics are used
        # (carbon goes to thousand metric tons)
        unit_translate = unit_translate * c_conv_emm
      }
    
    # Initialize a matrix for storing individual ECM energy, carbon, or cost totals (3 rows
    # accommodate mean, low, and high totals values; 4 columns accommodate 2 outputs
    # (baseline and efficient) x 2 adoption scenarios)
    results <- matrix(list(), 3, 2*length(comp_schemes))

    # Initialize a matrix for storing aggregated ECM savings results (3 rows accommodate
    # 3 filtering variables (climate zone, building class, end use); 3 columns accomodate
    # the possible name categories for each filtering variable, the aggregated savings data
    # associated with each of those categories, and the colors associated with those categories
    results_agg <- matrix(list(), length(filter_var), 3)
    # Initialize climate zone names, annual by-climate aggregated savings data, and line colors
    results_agg[1,1:3] <- c(list(czones_out),
                            list(rep(list(matrix(0, length(years))), length(czones_out))),
                            list(czones_out_col))
    # Initialize building class names, annual by-building aggregated savings data and line colors
    results_agg[2,1:3] <- c(list(bclasses_out_agg),
                            list(rep(list(matrix(0, length(years))), length(bclasses_out_agg))),
                            list(bclasses_out_agg_col))
    # Initialize end use names, annual by-end use aggregated savings data and line colors
    results_agg[3,1:3] <- c(list(euses_out_agg),
                            list(rep(list(matrix(0, length(years))), length(euses_out_agg))),
                            list(euses_out_agg_col))
                            
                            
    # Initialize a matrix for storing individual ECM financial metrics/savings and filter
    # variable data
    results_finmets <- matrix(list(), length(meas_names_no_all), (length(fin_metrics) + 4))
      
    # Initialize uncertainty flag for the adoption scenario 
    uncertainty = FALSE  
    # Set the file name for the plot based on the adoption scenario and plotting variable  
    if (adopt_scenarios[a] == 'Technical potential'){
      # ECM energy, carbon, and cost totals
      plot_file_name_ecms = file.path(
      	base_dir, 'results', 'plots', 'tech_potential', results_folder_names[v],
      	paste(file_names_ecms[v],"-TP", sep=""))
      # Aggregate energy, carbon, and cost savings
      plot_file_name_agg = file.path(
      	base_dir, 'results', 'plots', 'tech_potential', results_folder_names[v],
      	paste(plot_names_agg[v],"-TP", sep=""))
      # ECM cost effectiveness
      plot_file_name_finmets = file.path(
      	base_dir, 'results', 'plots', 'tech_potential', results_folder_names[v],
      	paste(plot_names_finmets[v],"-TP.pdf", sep=""))
      }else{
        # ECM energy, carbon, and cost totals
        plot_file_name_ecms = file.path(
        	base_dir, 'results', 'plots', 'max_adopt_potential', results_folder_names[v],
            paste(file_names_ecms[v],"-MAP", sep = ""))
        # Aggregate energy, carbon, and cost savings
        plot_file_name_agg = file.path(
        	base_dir, 'results', 'plots', 'max_adopt_potential', results_folder_names[v],
            paste(plot_names_agg[v],"-MAP", sep=""))
        # ECM cost effectiveness
        plot_file_name_finmets = file.path(
        	base_dir, 'results', 'plots', 'max_adopt_potential', results_folder_names[v],
            paste(plot_names_finmets[v],"-MAP.pdf", sep=""))
      }
    # Open PDF device for plotting each ECM's energy, carbon, or cost totals 
    pdf(paste(plot_file_name_ecms, "-byECM.pdf", sep=""),width=15.5,height=14)
    # Set number of rows and columns per page in PDF output
    par(mfrow=c(4,4))
    # Reconfigure space around each side of the plot for best fit
    par(mar=c(5.1,5.1,3.1,2.1))
    
    # Loop through all ECMs
    for (m in 1:length(meas_names)){
    
      # Add ECM name to Excel worksheet data frame
      
      # Set appropriate starting row for the ECM's data
      if (meas_names[m] == "All ECMs"){
      	# For the 'All ECMs' data, start at the beginning of the file
      	row_ind_start = 1
      }else{
      	# Otherwise, leave the first 4 rows for the 'All ECMs' total uncompeted/
      	# competed energy, carbon, and cost data, plus another 20 rows for 'All ECMs'
      	# energy, carbon, and cost savings totals, first summarized across all climate
      	# zones, building types, and end uses (1 row) and subsequently broken out by
      	# climate zone (5 rows), building type (4 rows), and end use (10 rows)
      	row_ind_start = (m-1)*4 + 1 + (1 + 5 + 4 + 10)
      }
      xlsx_data[row_ind_start:(row_ind_start + 3), 1] = meas_names[m]
      
      # Set applicable climate zones, end uses, and building classes for ECM
      # and add to Excel worksheet data frame
      czones = toString(compete_results[[meas_names[m]]]$'Filter Variables'$'Applicable Regions')
      bldg_types = toString(compete_results[[meas_names[m]]]$'Filter Variables'$'Applicable Building Classes')
      end_uses = toString(compete_results[[meas_names[m]]]$'Filter Variables'$'Applicable End Uses')
      xlsx_data[row_ind_start:(row_ind_start + 3), 3] = czones
      xlsx_data[row_ind_start:(row_ind_start + 3), 4] = bldg_types
      xlsx_data[row_ind_start:(row_ind_start + 3), 5] = end_uses
      
      # If there are more than three end use names, set a single end use name of 'Multiple' such that
      # the end use name label will fit easily within each plot region
      if (str_count(end_uses, ",") > 1){
        end_uses = "Multiple"
      }

      # Find the index for accessing the item in the list of uncompeted results that corresponds
      # to energy, carbon, or cost total data for the current ECM. Note: competed energy, carbon, and
      # cost totals are accessed directly by ECM name, and do not require an index
      for (uc in 1:length(uncompete_results)){
        if (uncompete_results[[uc]]$'name' == meas_names[m]){
          uc_name_ind = uc
        }
      }
      
      # Set the appropriate database of ECM financial metrics data (used across both competition schemes)
      results_database_finmets = compete_results[[meas_names[m]]]$'Financial Metrics'

      # Loop through all competition schemes
      for (cp in 1:length(comp_schemes)){
          
        # Add name of results scenario (baseline/efficient + competed/uncompeted)
        # to Excel worksheet data frame
        xlsx_data[(row_ind_start + (cp-1)*2):(row_ind_start + (cp-1)*2 + 1), 2] = c(
         paste("Baseline ", comp_schemes[cp], sep = ""), paste("Efficient ", comp_schemes[cp], sep = ""))
        
        # Set matrix for temporarily storing finalized baseline and efficient results
        r_temp <- matrix(NA, 6, length(years))  
        # Find data for uncompeted energy, carbon, and/or cost; exclude the 'All ECMs' case
        # (only competed data may be summed across all ECMs)
        if ((comp_schemes[cp] == "uncompeted")&(meas_names[m] != "All ECMs")){
          # Set the appropriate database of uncompeted energy, carbon, or cost totals
          # (access keys vary based on plotted variable)
          if (var_names_uncompete[v] != "cost"){
            results_database = 
              uncompete_results[[uc_name_ind]]$'markets'[[adopt_scenarios[a]]]$
              'master_mseg'[[var_names_uncompete[v]]]$'total' 
            }else{
              results_database = 
                uncompete_results[[uc_name_ind]]$'markets'[[adopt_scenarios[a]]]$
                'master_mseg'[[var_names_uncompete[v]]]$'energy'$'total'
            }
          # Order the uncompeted ECM energy, carbon, or cost totals by year and determine low/high
          # bounds on each total value (if applicable)
          for (yr in 1:length(years)){
            r_temp[1:3, yr] = results_database$'baseline'[years[yr]][[1]]
            # Set mean, low, and high values for case with ECM input/output uncertainty
            if (length(results_database$'efficient'[years[1]][[1]]) > 1){
              # Take mean of list of values from uncompeted results
              r_temp[4, yr] = mean(results_database$'efficient'[years[yr]][[1]])
              # Take 5th/95th percentiles of list of values from uncompeted results
              r_temp[5:6, yr] = quantile(results_database$'efficient'[years[yr]][[1]], c(0.05, 0.95))
              uncertainty = TRUE
              # Set mean, low, and high values for case without ECM input/output uncertainty
              # (all values equal to mean value)
              }else{
                r_temp[4:6, yr] = results_database$'efficient'[years[yr]][[1]]
              }
          }
        # Find data for competed energy, carbon, and/or cost
        }else{
          # Set the appropriate database of ECM competed energy, carbon, or cost totals
          results_database = compete_results[[meas_names[m]]]$
            'Markets and Savings (Overall)'[[adopt_scenarios[a]]]
          # Set the appropriate database of ECM competed energy, carbon, or cost totals
          # broken down by climate zone, building class, and end use; exclude the 'All ECMs'
          # case (breakdowns are not calculated for this case) 
          if (meas_names[m] != "All ECMs"){
	          # Set the appropriate database of ECM competed energy, carbon , or cost savings,
	          # which are broken out by each of the three filtering variables (climate zone,
	          # building class, end use)
	          results_database_agg = compete_results[[meas_names[m]]]$
	            'Markets and Savings (by Category)'[[adopt_scenarios[a]]][[var_names_compete_save[v]]]
	          # Set the appropriate database of ECM data for categorizing cost effectiveness outcomes
	          # based on climate zone, building type, and end use
	          results_database_filters = compete_results[[meas_names[m]]]$'Filter Variables'
	      }
          
          # Order competed ECM energy, carbon, or cost totals by year and determine low/high bounds
          # on each total value (if applicable)`
          for (yr in 1:length(years)){
            base_uncertain_check = sapply(c("Baseline", "low"), grepl, names(results_database))
            if (length(which((base_uncertain_check[,1]&base_uncertain_check[,2])==TRUE)>0)) {
              # Take mean value output directly from competed results
              r_temp[1, yr] = results_database[[var_names_compete_base_m[v]]][years[yr]][[1]]
              # Take 'low' value output directly from competed results (represents 5th percentile)
              r_temp[2, yr] = results_database[[var_names_compete_base_l[v]]][years[yr]][[1]]
              # Take 'high' value output directly from competed results (represents 5th percentile)
              r_temp[3, yr] = results_database[[var_names_compete_base_h[v]]][years[yr]][[1]]
              # Flag output uncertainty in the current plot
              uncertainty = TRUE
              # Set mean, low, and high values for case without ECM input/output uncertainty
              # (all values equal to mean value)
            }else{
              # Take 'low' value output directly from competed results (represents 5th percentile)
              r_temp[1:3, yr] = results_database[[var_names_compete_base_m[v]]][years[yr]][[1]]
            }
            
            # Set mean, low, and high values for case with ECM input/output uncertainty
            eff_uncertain_check = sapply(c("Efficient", "low"), grepl, names(results_database))
            if (length(which((eff_uncertain_check[,1]&eff_uncertain_check[,2])==TRUE)>0)) {
              # Take mean value output directly from competed results
              r_temp[4, yr] = results_database[[var_names_compete_eff_m[v]]][years[yr]][[1]]
              # Take 'low' value output directly from competed results (represents 5th percentile)
              r_temp[5, yr] = results_database[[var_names_compete_eff_l[v]]][years[yr]][[1]]
              # Take 'high' value output directly from competed results (represents 95th percentile)
              r_temp[6, yr] = results_database[[var_names_compete_eff_h[v]]][years[yr]][[1]]
              # Flag output uncertainty in the current plot
              uncertainty = TRUE
              # Set mean, low, and high values for case without ECM input/output uncertainty
              # (all values equal to mean value)
              }else{
                r_temp[4:6, yr] = results_database[[var_names_compete_eff_m[v]]][years[yr]][[1]]
              }
            # Find the amount of the ECM's energy, carbon, or cost savings that can be
            # attributed to each of the three aggregate savings filtering variables
            # (climate zone, building class, end use) and add those savings to the
            # aggregated total for each filter variable across all ECMs; exclude the 'All ECMs'
          	# case (filter variable breakdowns are not calculated for this case) 
            if (meas_names[m] != "All ECMs"){
	            # Loop through the three variables used to filter aggregated savings, each
	            # represented by a row in the 'results_agg' matrix
	            for (fv in (1:nrow(results_agg))){
	              # Set the name categories associated with the given savings filter
	              # variable (e.g., 'Residential (New)', 'Residential (Existing)', etc. for
	              # building class)
	              fv_opts <- results_agg[fv, 1][[1]]
	              
	              # Initialize a vector used to store the ECM's energy, carbon, or cost
	              # savings that are attributable to the given filter variable; this
	              # vector must be as long as the number of category names for the
	              # filter variable, so a savings total can be stored for each category  
	              add_val = matrix(0, length(fv_opts))
	              
	              # Retrieve the savings data for the ECM that is attributable to each
	              # filter variable name category. The data are stored in a three-level
	              # nested dict with climate zone at the top level, building class at
	              # the middle level, and end use at the bottom level. All three of these
	              # levels must be looped through to retrieve the savings data.
	              
	              # Loop through all climate zones
	              for (levone in (1:length(results_agg[1, 1][[1]]))){  
	                # Set the climate zone name to use in proceeding down to the
	                # building class level of the dict
	                czone = results_agg[1, 1][[1]][[levone]]
	                # Reduce the dict to the building class level
	                r_agg_temp = results_database_agg[[czone]]
	                # Loop through all building classes
	                for (levtwo in (1:length(results_agg[2, 1][[1]]))){
	                  # Set the building class name to use in proceeding down to the
	                  # end use level of the dict
	                  bldg = results_agg[2, 1][[1]][[levtwo]]
	                  # Reduce the dict to the end use level
	                  r_agg_temp = results_database_agg[[czone]][[bldg]]
	                  # Loop through all end uses
	                  for (levthree in (1:length(results_agg[3, 1][[1]]))){
	                    # Set the end use name to use in retrieving data values
	                    euse = results_agg[3, 1][[1]][[levthree]]
	                    # Reset the predefined 'Electronics' end use name (short for
	                    # later use in plot legends) to the longer 'Computers and Electronics'
	                    # name used in the dict
	                    if (euse == "Electronics"){
	                    	euse = "Computers and Electronics"
	                    }
	                    # Reduce the dict to the level of the retrieved data values
	                    r_agg_temp = results_database_agg[[czone]][[bldg]][[euse]]  
	                    
	                    # If data values exist, add them to the ECM's energy/carbon/cost
	                    # savings-by-filter variable vector initialized above
	                    if (length(r_agg_temp)>1){
	                      # Determine which index to use in adding the retrieved data to
	                      # the ECM's energy/carbon/cost savings-by-filter variable vector
	                      if (fv == 1){
	                        index = levone
	                      }else if (fv == 2){
	                        index = levtwo
	                      }else{
	                        index = levthree
	                      }
	                      # Add retrieved data to ECM's savings-by-filter variable vector;
                        # handle case where end use savings are further split out by
                        # fuel type ('Electric' vs. 'Non-Electric')
	                      if (length(r_agg_temp) == 2){
                          for (fuel in c("Electric", "Non-Electric")){
                            if (length(r_agg_temp[[fuel]])!=0){
                              add_val[index] = add_val[index] +
                                r_agg_temp[[fuel]][years[yr]][[1]]
                            }
                          }
                        }else{
                          add_val[index] = add_val[index] + r_agg_temp[years[yr]][[1]]
                        }
	                    }
	                  }                  
	                }  
	              }
	              # Add ECM's savings-by-filter variable vector data to the aggregated total for
	              # each filter variable across all ECMs
	              for (fvo in 1:length(fv_opts)){
	                results_agg[fv, 2][[1]][[fvo]][yr] = results_agg[fv, 2][[1]][[fvo]][yr] + add_val[fvo]
	              }
	            }
		        
		        # If cycling through the year in which snapshots of ECM cost effectiveness are taken,
		        # retrieve the ECM's competed financial metrics, savings, and filter variable data needed
		        # to develop those snapshots for the cost effectiveness plots
		        if (years[yr] == snap_yr){
		          # Retrieve ECM competed portfolio-level and consumer-level financial metrics data
		          for (fm in 1:length(fin_metrics)){
	          		# Multiply IRR fractions in JSON data by 100 to convert to final % units
	          		if ((fin_metrics[fm]) == "IRR (%)"){
	          			unit_translate_finmet = 100
	          		}else{
	          			unit_translate_finmet = 1	
	          		}
	          		# Consumer-level data are NOT keyed by adoption scenario
	          		results_finmets[(m - 1), fm][[1]] = 
	          		results_database_finmets[[fin_metrics[fm]]][[years[yr]]][[1]] * unit_translate_finmet
		          	# Replace all 99900 values with 999 (proxy for NaN)
		          	results_finmets[(m - 1), fm][[1]][results_finmets[(m - 1), fm][[1]] == 99900] = 999		 	
		          }
	
		          # Write ECM cost effectiveness metrics data to XLSX sheet
		          xlsx_data[row_ind_start:(row_ind_start + 3),
	              			6: (6 + length(plot_title_labels_finmets) - 1)] =
	              			as.matrix(results_finmets[(m - 1),1:4])

		          # Retrieve, ECM energy, carbon, or cost savings data, convert to final units
		          results_finmets[(m - 1), (length(fin_metrics)+1)][[1]] =
		          	results_database[[var_names_compete_save[v]]][years[yr]][[1]] * unit_translate
		          
		          # Determine the outline color, shape, and fill color parameters needed to
		          # distinguish ECM points on the cost effectiveness plots by their climate
		          # zone, building type, and end use categories
		          
		          # # Determine appropriate ECM point outline color for applicable climate
		          # # zones
		          # # Set ECM's applicable climate zones
		          # czones = results_database_filters$'Applicable Climate Zones'
		          # # Match applicable climate zones to climate zone names used in plotting
		          # czone_match = which(czones_out %in% czones)
		          # # If more than one climate zone name was matched, set the outline color
		          # # to gray, representative of 'Multiple' applicable climate zones; otherwise
		          # # set to the point outline color appropriate to the matched climate zone
		          # if (length(czone_match)>1){
		          	# results_finmets[(m - 1), 6] = "gray50"
		          # }else{
		          	# results_finmets[(m - 1), 6] = czones_out_col[czone_match]
		          # }
		          # Determine appropriate ECM point shape for applicable building type
		          # Set ECM's applicable building type
		          bldg = results_database_filters$'Applicable Building Classes'
		          # Match applicable building classes to building type names used in plotting
		          bldg_match = matrix(NA, length(bclasses_out_finmets))
		          for (b in 1:length(bclasses_out_finmets)){
		          	if (length(which(bldg%in%bclasses_out_finmets[[b]][[1]])>0)){
		          		bldg_match[b] = b
		          	}
		          }
		          # If more than one building type name was matched, set the point shape to
		          # a triangle, representative of 'Multiple' applicable building types;
		          # otherwise set to the point shape appropriate for the matched building type
		          if (length(bldg_match[is.finite(bldg_match)])>1){
		          	results_finmets[(m - 1), 7] = 24
		          }else{
		          	results_finmets[(m - 1), 7] = bclasses_out_finmets_shp[bldg_match[is.finite(bldg_match)]]
		          } 
				  # Determine appropriate ECM point fill color for applicable end uses
		          # Set ECM's applicable end uses
		          euse = results_database_filters$'Applicable End Uses'
		          # Match applicable end uses to end use names used in plotting
		          euse_match = matrix(NA, length(euses_out_finmets))
		          for (e in 1:length(euses_out_finmets)){
		          	if (length(which(euse%in% euses_out_finmets[[e]])>0)){
		          		euse_match[e] = e
		          	}
		          }
		          # If more than one end use name was matched, set the point fill color to
		          # gray, representative of 'Multiple' applicable end uses; otherwise set
		          # to the point fill color appropriate for the matched end use
		          if (length(euse_match[is.finite(euse_match)])>1){
		          	results_finmets[(m - 1), 8] ="gray50"
		          }else{
		          	results_finmets[(m - 1), 8] = euses_out_finmets_col[euse_match[is.finite(euse_match)]]
		          }
		       }
          	}
          }	
        }

        # Set the column start and stop indexes to use in updating the matrix of ECM
        # energy, carbon or cost totals
        col_ind_start = ((cp-1)*(length(comp_schemes))) + 1
        col_ind_end = col_ind_start + 1 # note this accommodates baseline and efficient outcomes
        # Update results matrix with mean, low, and high baseline and efficient outcomes
        results[, col_ind_start:col_ind_end] = rbind(
          cbind(list(r_temp[1,]), list(r_temp[4,])),
          cbind(list(r_temp[2,]), list(r_temp[5,])),
          cbind(list(r_temp[3,]), list(r_temp[6,])))
      }

      # Set uncompeted and competed baseline energy, carbon, or cost totals for given
      # adoption scenario, plotting variable, and ECM (mean and low/high values
      # for competed case)  
      base_uc = unlist(results[1, 1]) * unit_translate
      base_c_m = unlist(results[1, 3]) * unit_translate
      base_c_l = unlist(results[2, 3]) * unit_translate
      base_c_h = unlist(results[3, 3]) * unit_translate
      # Set uncompeted and competed efficient energy, carbon, or cost totals for
      # adoption scenario, plotting variable, and ECM (mean and low/high values)
      eff_uc_m = unlist(results[1, 2]) * unit_translate
      eff_uc_l = unlist(results[2, 2]) * unit_translate
      eff_uc_h = unlist(results[3, 2]) * unit_translate
      eff_c_m = unlist(results[1, 4]) * unit_translate
      eff_c_l = unlist(results[2, 4]) * unit_translate
      eff_c_h = unlist(results[3, 4]) * unit_translate
      
      # Add annual ECM energy, carbon, or cost totals to XLSX worksheet data frame
      xlsx_data[row_ind_start:(row_ind_start + 3),
                (6 + (length(plot_title_labels_finmets))):ncol(xlsx_data)] = 
                rbind(base_uc, eff_uc_m, base_c_m, eff_c_m)
            
      # Find the min. and max. values in the ECM energy, carbon, or cost totals data
      # to be plotted
      min_val = min(c(base_uc, base_c_m, base_c_l, base_c_h,
                      eff_uc_m, eff_uc_l, eff_uc_h,
                      eff_c_m, eff_c_l, eff_c_h))
      max_val = max(c(base_uc, base_c_m, base_c_l, base_c_h, 
                      eff_uc_m, eff_uc_l, eff_uc_h,
                      eff_c_m, eff_c_l, eff_c_h))
      # Set limits of y axis for plot based on min. and max. values in data
      ylims = pretty(c(min_val-0.05*max_val, max_val+0.05*max_val))

      # Initialize the plot with uncompeted baseline ECM energy, carbon, or cost totals
      plot(years, base_uc, typ='l', lwd=5, ylim = c(min(ylims), max(ylims)),
           xlab=NA, ylab=NA, col=plot_col_uc_base, main = meas_names[m], xaxt="n", yaxt="n")

      # Determine legend parameters based on whether uncertainty is present in totals
      if (uncertainty == TRUE){
        # Set legend names for a plot with uncertainty in the ECM totals
        legend_param = c(
          "Baseline (Uncompeted)", "Baseline (Competed)",
          "Efficient (Uncompeted)", "Efficient (Competed)",
          "Baseline (Competed, 5th/95th PCT)", "Efficient (Uncompeted, 5th/95th PCT)",
          "Efficient (Competed, 5th/95th PCT)")
        col_param = c(plot_col_uc_base, plot_col_c_base, plot_col_uc_eff,
                      plot_col_c_eff, plot_col_c_base,
                      plot_col_uc_eff, plot_col_c_eff)
        lwd_param = c(5, 3.5, 3, 2, rep(1, 3))
        lty_param = c(rep(1, 4), rep(6, 3))
        }else{
          # Set legend names for a plot with no uncertainty in the ECM totals
          legend_param = c("AEO Baseline (Uncompeted)", "AEO Baseline (Competed)",
                           "Efficient (Uncompeted)", "Efficient (Competed)")
          col_param = c(plot_col_uc_base, plot_col_c_base, plot_col_uc_eff, plot_col_c_eff)
          lwd_param = c(5, 3.5, 3, 2)
          lty_param = rep(1, 4)  
        }

      # Add low/high bounds on uncompeted and competed baseline and efficient
      # ECM energy, carbon, or cost totals, if applicable
      if (uncertainty == TRUE){
          lines(years, eff_uc_l, lwd=1, lty=6, col=plot_col_uc_eff)
          lines(years, eff_uc_h, lwd=1, lty=6, col=plot_col_uc_eff)
          lines(years, base_c_l, lwd=1, lty=6 , col=plot_col_c_base)
          lines(years, base_c_h, lwd=1, lty=6 , col=plot_col_c_base)
          lines(years, eff_c_l, lwd=1, lty=6 , col=plot_col_c_eff)
          lines(years, eff_c_h, lwd=1, lty=6 , col=plot_col_c_eff)
      }

      # Add mean uncompeted efficient ECM energy, carbon, or cost totals
      lines(years, eff_uc_m, lwd=3, col=plot_col_uc_eff)
      # Add mean competed baseline results
      lines(years, base_c_m, lwd=3.5, col=plot_col_c_base)
      # Add mean competed efficient results
      lines(years, eff_c_m, lwd=2, col=plot_col_c_eff)
      
      # Add x and y axis labels
      mtext("Year", side=1, line=3.5, cex=0.925)
      mtext(plot_axis_labels_ecm[v], side=2, line=3.65, cex=0.925)
      # Add tick marks and labels to bottom and left axes
      axis(side=1, at=pretty(c(min(years), max(years))),
           labels=pretty(c(min(years), max(years))), cex.axis = 1.15)
      axis(side=2, at=ylims, labels = ylims, cex.axis = 1.15, las=1)
      # Add tick marks to top and right axes
      axis(side=3, at=pretty(c(min(years), max(years))), labels = NA)
      axis(side=4, at=ylims, labels = NA)
      # Annotate total savings in a snapshot years for the 'All ECMs' case;
      # otherwise, annotate the applicable ECM end uses         
      if (meas_names[m] == "All ECMs"){
      # Annotate the plot with snapshot year total savings figure
	    # Find x and y values for annotation
	    for (s in 1:length(snap_yr_set)){
		    # Set the x value for annotation point
        xval_snap = as.numeric(snap_yr_set[s])
		    # Set x value for annotation label
        if (as.numeric(snap_yr_set[s])>2045){
          # For later years, set the label to the left of the x val;
          # otherwise, set the label under the x val
          xlab_pos = 2
		    }else{
		    	xlab_pos = 1
		    }
		    # Set y values for annotation point
        yval_snap_eff = eff_c_m[which(years==snap_yr_set[s])]
		    yval_snap_base = base_c_m[which(years== snap_yr_set[s])]
		    # Draw line segment connecting snapshot year baseline and efficient results
		    points(xval_snap, yval_snap_base, col="forestgreen", pch = 1, cex=1.5, lwd=2.5)
		    points(xval_snap, yval_snap_eff, col="forestgreen", pch = 1, cex=1.5, lwd=2.5)
		    segments(xval_snap, yval_snap_eff, xval_snap, yval_snap_base, col="forestgreen", lty=3)
		    # Add snapshot year savings figure
		    text(xval_snap, yval_snap_eff - (yval_snap_eff - min(ylims))/7,
		         paste(toString(sprintf("%.1f", yval_snap_base-yval_snap_eff)),
		               toString(var_units[v]), sep=" "), pos = xlab_pos, col="forestgreen")
		    }
	    }else{
	  	# Add ECM end use labels
      text(min(years), max(ylims), labels=paste("End Uses: ", end_uses, sep=""), col="gray50",
           pos=4, cex=0.93)
	    }
      # If needed, add disclaimer about the use of public health costs
      if (var_names_uncompete[v] == "cost" & phc_flag != FALSE){
        # Set increment to use in plotting disclaimer text
        ylim_inc = (max(ylims) - min(ylims))*0.05
        if (phc_flag == "low"){
          text(min(years), min(ylims), labels=
            "* Reflects low EPA health benefits - ignore results after 2025",
            col="red", pos=4, cex=0.85)
        }else{
          text(min(years), min(ylims), labels=
            "* Reflects high EPA health benefits - ignore results after 2025",
            col="red", pos=4, cex=0.85)
        }
      }
    }
    # Add legend for all individual ECM plots
    par(xpd=TRUE)
    plot(1, type="n", axes=F, xlab="", ylab="") # creates blank plot square for legend
    legend("top", legend=legend_param, lwd=lwd_param, col=col_param, lty=lty_param, 
       bty="n", border = FALSE, merge = TRUE, cex=1.15)
    # Close plot device
    dev.off()
  
    # Plot annual and cumulative energy, carbon, and cost savings across all ECMs,
    # filtered by climate zone, building class, and end use
	
	# Generate single PDF device to plot aggregate savings under all three filters
	pdf(paste(plot_file_name_agg,"-Aggregate", ".pdf", sep=""),width=8.5,height=11)
    # Set number of rows and columns per page in PDF output
    par(mfrow=c(3,1))
    # Reconfigure space around each side of the plot for best fit
    par(mar=c(5.1, 7.1, 3.1, 7.1))
    
    # Set the first XLSX row number for writing aggregated savings results; note that 
    # these results are ultimately written to the 19 rows that follow the
    # 'All ECMs' total energy, carbon, and cost results written above (19 = 1 row
    # for total savings across climate zones, building types, and end uses, 5 rows for
    # savings by climate zone, 4 rows for savings by building type, and 9 rows
    # for savings by end use)
    agg_row_ind = 5
    
    # Loop through all three savings filter variables and add plot of aggregated savings
    # under each filter to the PDF device
    for (f in (1:nrow(results_agg))){
      # Initialize vector for storing total annual savings across all category names
      # for the given filter variable
      total_ann = matrix(0, length(years))
      # Initialize vector for storing ranks of annual savings for each category
      # for the given filter variable
      total_ranks = matrix(0, length(results_agg[f, 2][[1]]))
      # Initialize matrix for determining min./max. y values in plot
      min_max_ann = matrix(0, length(results_agg[f, 2][[1]]), 2)
      
      # Loop through all categories under the filter variable and add aggregate savings
      # under that category to the total aggregate savings for the given filter variable  
      for (cat in (1:length(results_agg[f, 2][[1]]))){
        # Add annual savings for category to total annual savings
        total_ann = total_ann + results_agg[f, 2][[1]][[cat]]*unit_translate
		# Add maximum value of annual savings for category, for ranking purposes
        total_ranks[cat] = max(results_agg[f, 2][[1]][[cat]]*unit_translate)
        # Record min./max. y values for category
        min_max_ann[cat, 1:2] = c(min(results_agg[f, 2][[1]][[cat]]*unit_translate), 
        					          max(results_agg[f, 2][[1]][[cat]]*unit_translate))
      }
      
      # Use the total annual savings data to develop total cumulative savings
      
      # Initialize vector for storing total cumulative savings across all category names
      total_cum = matrix(0, length(total_ann))
      # Loop through each year in the total annual savings data and develop a total
      # cumulative savings value for that year
      for (yr in (1:length(total_ann))){
      	# For first year, total cumulative savings equals total annual savings; in
      	# subsequent years, total cumulative savings equals total annual savings
      	# plus total cumulative savings for the year before
      	if (yr == 1){
      		total_cum[yr] = total_ann[yr]
      	}else{
      		total_cum[yr] = total_ann[yr] + total_cum[yr-1]
      	}	
      }
      
      # Plot total annual/cumulative savings and savings by filter variable category
      
      # Develop x limits for the plot
      xlim = pretty(c(min(years), max(years)))
      
      # Develop y limits for total cumulative savings
      min_val_cum = min(total_cum)
      max_val_cum = max(total_cum)
      ylim_cum = round(pretty(c(min_val_cum, max_val_cum)), 2)
      
      # Develop y limits for total annual savings
      max_val_ann = max(c(min_max_ann[,2], max(total_ann)))
      min_val_ann = min(c(min_max_ann[,1], min(total_ann)))
      # Force very small negative min. y value to zero
      if ((max_val_ann > 0) & ((abs(min_val_ann)/max_val_ann) < 0.01)){
      	min_val_ann = 0
      }
      ylim_ann = round(pretty(c(min_val_ann, max_val_ann)), 2)       
      # Initialize plot region for total cumulative savings
      plot(1, typ="n", xlim = c(min(xlim), max(xlim)),
           ylim = c(min(ylim_cum), max(ylim_cum)),
           main = bquote(bold(.(plot_titles_agg[v][[1]])~ 'by'~ .(filter_var[f]))),
           axes=FALSE, xlab=NA, ylab=NA)
      # Add total cumulative savings line
      lines(years, total_cum, col="gray50", lwd=4, lty=3)
      # Add x axis tick marks and axis labels
      axis(side=1, at=pretty(c(min(years), max(years))),
           labels=pretty(c(min(years), max(years))), cex.axis = 1.25)
      mtext("Year", side=1, line=3.25, cex=0.9)  
      # Add y axis tick marks and axis labels for total cumulative savings
      axis(side=4, at=ylim_cum, labels = ylim_cum, cex.axis = 1.25, las=1)
      mtext(plot_axis_labels_agg_cum[v], side=4, line=4, cex=cex_cum_ax) 
      
      # Add plot of total annual savings and savings by filter variable category name
      par(new=TRUE)
      
      # Initialize plot region for total annual savings and savings by filter
      # variable category
      plot(years, total_ann, typ='l',
           xlim = c(min(xlim), max(xlim)), ylim = c(min(ylim_ann), max(ylim_ann)),
           xlab=NA, ylab=NA, col="gray30", main = NA,
           xaxt="n", yaxt="n", lwd=4)
      
      # Add total aggregate savings data across all climate zones, building types, and
      # end uses to the data frame that will be written to the XLSX file; do so only if the
      # first savings filter variable is being looped through, as the total aggregate
      # savings values do not change across filter variables
      if (f == 1){
      	# Set ECM name to 'All ECMs' and results scenario to baseline minus efficient
      	xlsx_data[agg_row_ind, 1:2] = c("All ECMs", "Baseline competed - efficient competed")
      	# When updating total aggregate savings, each filter variable cell in the XLSX is
      	# flagged 'All' (since the total values pertain to all filter variable categories)
      	xlsx_data[agg_row_ind, 3:5] = rep("All", 3)
      	# Add the total aggregate savings values to the appropriate row/column range
      	xlsx_data[agg_row_ind,
                  (6 + (length(plot_title_labels_finmets))):ncol(xlsx_data)] = total_ann
      	# Increment the XLSX row to write to by one 
      	agg_row_ind = agg_row_ind + 1
      	# Set the columns in the XLSX that are active/inactive for the current filter variable
      	col_active = 3
      	col_inactive = c(4, 5)
      # If the second or third savings filter variable is being looped through, do not
      # write out total aggregate savings estimates to XLSX, but do flag the column in the XLSX
      # where the relevant filter variable information will be written
      }else if (f==2){
      	# Set the columns in the XLSX that are active for the current filter variable
      	col_active = 4
      	# Set the columns in the XLSX that correspond to the inactive filter variables (
      	# 'All' values will be written to these columns)
      	col_inactive = c(3, 5)
      }else if (f==3){
      	# Set the columns in the XLSX that are active for the current filter variable
      	col_active = 5
      	# Set the columns in the XLSX that correspond to the inactive filter variables (
      	# 'All' values will be written to these columns)
      	col_inactive = c(3, 4)
      }
      # Loop through each filter variable category name to add to plot
      for (catnm in (1:(length(results_agg[f, 2][[1]])))){
        # Add lines for savings by filter variable category
        lines(years, results_agg[f, 2][[1]][[catnm]]*unit_translate,
          	  col=results_agg[f, 3][[1]][catnm], lwd=2)
        
        # Add aggregate savings results broken out by filter variable to the data frame
        # that will be written to the XLSX file
        
        # Set ECM name to 'All ECMs' and results scenario to baseline minus efficient
        xlsx_data[agg_row_ind, 1:2] = c("All ECMs", "Baseline competed - efficient competed")
        # Set the currently active filter variable category name (e.g., 'AIA CZ1,'
        # 'Ventilation,' etc.)
        xlsx_data[agg_row_ind, col_active] = results_agg[f, 1][[1]][catnm]
        # Set inactive filter variable values to 'All'
        xlsx_data[agg_row_ind, col_inactive] = rep("All", 2)
        # Add aggregate savings values broken out by the current filter variable category
        # to the appropriate row/column range
        xlsx_data[agg_row_ind, (6 + (length(plot_title_labels_finmets))):ncol(xlsx_data)] = 
        		results_agg[f, 2][[1]][[catnm]]*unit_translate 
        # Increment the XLSX row to write to by one
        agg_row_ind = agg_row_ind + 1	     	  	  
      }
      # Add y axis labels for total annual savings and savings by filter variable category
      axis(side=2, at=ylim_ann, labels = ylim_ann, cex.axis = 1.25, las=1)
      mtext(plot_axis_labels_agg_ann[v], side=2, line=4, cex=cex_ann_ax) 
      
      # Add a legend
      
      # Set legend names
      legend_entries = c('Total (Annual)', 'Total (Cumulative)',
      					 results_agg[f, 1][[1]][order(total_ranks, decreasing=TRUE)])
      # Set legend colors
      color_entries = c(
      	'gray30', 'gray50',
      	results_agg[f, 3][[1]][order(total_ranks, decreasing=TRUE)])
      # If needed, set parameter to scale down plot legend for EMM regions (relevant
      # only for the first filter variable, region)
      if ((emm_flag == TRUE) & (f == 1)){
        cex_agg_leg = 0.7
        ncol_leg = 1
      }else if ((state_flag == TRUE) & (f == 1)){
        cex_agg_leg = 0.7
        ncol_leg = 2
      }else{
        cex_agg_leg = 0.95
        ncol_leg = 1
      }
      # Find plot extremes for setting legend position
      plot_extremes <- par("usr")
      # Plot legend
      legend((plot_extremes[1] + abs(plot_extremes[2] - plot_extremes[1])*0.005),
             (plot_extremes[4] - abs(plot_extremes[4] - plot_extremes[3])*0.005),
      	     legend=legend_entries,
      		 lwd=c(4, 4, rep(2, (length(legend_entries) - 2))),
             col=color_entries, lty=c(1, 3, rep(1, (length(legend_entries)-2))), 
       		 bg=transparent_back, box.col="NA", cex=cex_agg_leg, ncol=ncol_leg)
      # If needed, add disclaimer about the use of public health costs
      if (var_names_uncompete[v] == "cost" & phc_flag != FALSE){
        if (phc_flag == "low"){
          text(max(xlim), max(ylim_ann), labels=
            "* Reflects low EPA health benefits - ignore results after 2025",
            col="red", pos=2, cex=0.85)
        }else{
          text(max(xlim), max(ylim_ann), labels=
            "* Reflects high EPA health benefits - ignore results after 2025",
            col="red", pos=2, cex=0.85)
        }
      }

    }
    dev.off()
    
    # Plot ECM cost effectiveness under multiple financial metrics
        
    # Open single PDF device for plotting ECM cost effectiveness under
    # all four financial metrics
    pdf(plot_file_name_finmets,width=11,height=8.5)
    # Set number of rows and columns per page in PDF output
    par(mfrow=c(2,2))
    # Reconfigure space around each side of the plot for best fit
    par(mar=c(5.1,5.1,3.1,2.1))
 
    # Loop through each financial metric and add cost effectiveness plot for financial
    # metric to open PDF device
    for (fmp in 1:length(fin_metrics)){
 
    	# Find the top 5 cost effective ECMs, as judged by the cost effectiveness
    	# threshold for the given financial metric and the ECM's energy, carbon, or
    	# cost savings value in the cost effectiveness snapshot year
    	
    	# First, find the ECMs that meet the cost effectiveness threshold (note: for 
    	# IRR 'cost effective' is above the threshold, for all other metrics
    	# 'cost effective' is below the threshold); restrict only to ECMs with
    	# a cost effectiveness result inside the -500 < y < 500 range
    	if (fmp==1){
    		restrict = which(
    		(results_finmets[, fmp] >= plot_ablines_finmets[fmp]) &
    		(results_finmets[, fmp] > -500 & results_finmets[, fmp] < 500))
    	}else{
    		restrict = which(
    		(results_finmets[, fmp] <= plot_ablines_finmets[fmp]) &
    		(results_finmets[, fmp] > -500 & results_finmets[, fmp] < 500))
     	}
		# Set vector of cost effective savings results
      	results_restrict<-unlist(results_finmets[, 5])[restrict]
      	# Sum total cost effective savings
      	total_save <- sum(results_restrict[results_restrict>=0])

      	# Second, find the ranking of those ECMs that meet the cost effectiveness
      	# threshold
      	order = order(results_restrict, decreasing=TRUE)   

    	# Finally, record the index numbers of the filtered/ranked ECMs
    	final_index = restrict[order]
    	# Handle cases where there are less than 5 cost effective ECMs to rank
    	if (length(meas_names_no_all[final_index])<5){
    		ecm_length = length(meas_names_no_all[final_index])
    	}else{
    		ecm_length = 5
    	}
    	# Set top 5 ECM names (add rank number next to each name)
    	meas_names_lgnd = meas_names_no_all[final_index][1:ecm_length]
    	for (mn in 1:length(meas_names_lgnd)){
    		meas_names_lgnd[mn] = paste(toString(mn), meas_names_lgnd[mn], sep=" ")
    	}
    	# Set x axis savings values for top 5 ECMs
    	label_vals_x = unlist(results_finmets[, 5])[final_index][1:ecm_length]
    	# Set y axis financial metrics values for top 5 ECMs
    	label_vals_y = unlist(results_finmets[, fmp])[final_index][1:ecm_length]
    	
    	# Set y limits for the plot
    	# Ensure that all of the top 5 ECMs' y values are accomodated by the default
    	# y axis range for each financial metric type; if not, adjust y axis range
    	# to accomodate out of range y values for top 5 ECMs
    	# Adjust top of range as needed
    	if ((is.finite(max(label_vals_y))) & (max(label_vals_y)>max(plot_lims_finmets[[fmp]]))){
    		plot_lims_finmets[[fmp]][2] = max(label_vals_y) # + 0.5*max(label_vals_y)
    	}
    	# Adjust bottom of range as needed
    	if ((is.finite(min(label_vals_y))) & (min(label_vals_y)<min(plot_lims_finmets[[fmp]]))){
    		plot_lims_finmets[[fmp]][1] = min(label_vals_y) # + 0.5*min(label_vals_y)
    	} 
    	# Make pretty labels for y axis range
    	ylim_fm = pretty(plot_lims_finmets[[fmp]])
	
    	# Ensure that results to be plotted are all within the final y axis range, and that no
    	# NA values are included in the results
    	results_finmets_filtr = results_finmets[(
    		results_finmets[, fmp]<=max(ylim_fm) & results_finmets[, fmp]>= min(ylim_fm) &
    		is.finite(unlist(results_finmets[, fmp]))), ]
    	
   		if (length(results_finmets_filtr) > 0){
	   		# Retrieve the data needed to set x and y limits for the plot and plot individual
	   		# ECM points, handling cases with one ECM or multiple ECMs 
	    	if (length(dim(results_finmets_filtr))>0){
	    		# Set x limits for the plot
	    		xlim = pretty(c(0, max(unlist(results_finmets_filtr[,5]))))
	    		# Retrieve x and y coordinates from matrix
	    		results_x <- results_finmets_filtr[, 5]
	    		results_y <- results_finmets_filtr[, fmp]
	    		# Retrieve point formatting parameters from matrix
	    		# results_col<- unlist(results_finmets_filtr[, 6])
	    		results_pch<- unlist(results_finmets_filtr[, 7])
	    		results_bg<- unlist(results_finmets_filtr[, 8])
	    		# Check for cases where points overlap with the top 5 ECM names listed in upper right
	    		overlap_chk <- results_finmets_filtr[
	    			(results_finmets_filtr[, fmp]>0.67*max(ylim_fm) &
	    			 results_finmets_filtr[, 5]>0.5*max(xlim)), ]
	    	}else{
	    		# Set x limits for the plot
	    		xlim = pretty(c(0, max(unlist(results_finmets_filtr[5]))))
	    		# Retrieve x and y coordinates from vector
	    		results_x <- results_finmets_filtr[5]
	    		results_y <- results_finmets_filtr[fmp]
	    		# Retrieve point formatting parameters from vector
	    		# results_col<- unlist(results_finmets_filtr[6])
	    		results_pch<- unlist(results_finmets_filtr[7])
	    		results_bg<- unlist(results_finmets_filtr[8])
	    		# Check for cases where points overlap with the top 5 ECM names listed in upper right
	    		overlap_chk <- results_finmets_filtr[
	    			(results_finmets_filtr[fmp]>0.67*max(ylim_fm) &
	    			 results_finmets_filtr[5]>0.5*max(xlim))]
	    	}
	    	
	    	# If there are overlaps between any points and the top 5 ECM names in the upper right
	    	# of the plot, extend the y axis upper limit to mitigate the overlaps
	    	if (length(overlap_chk)>0){
	    		ylim_fm = pretty(c(min(ylim_fm), max(ylim_fm) + 0.5*max(ylim_fm)))
	    	}
	
	   		# Initialize plot region for ECM cost effectiveness 
	    	plot(1, typ='n', xlim = c(min(xlim), max(xlim)),
	    	     ylim = c(min(ylim_fm), max(ylim_fm)), xlab=NA, ylab=NA,
	    	     main = plot_title_labels_finmets[fmp], xaxt="n", yaxt="n")
	    	# Determine the plot region boundaries
	    	plot_extremes <- par("usr")
	    	# Add a polygon (going all the way to the boundaries) to
	    	# distinguish the 'cost effective' region on each plot; again,
	    	# IRR 'cost effectiveness' is above the threshold value, while
	    	# 'cost effectiveness' under all other metrics is under the threshold value
	    	if (fmp==1){
	    		polygon(
	    			c(rep(min(plot_extremes[1:2]), 2),
	    			  rep(max(plot_extremes[1:2]), 2)),
	    			c(plot_ablines_finmets[fmp],
	    			  rep(max(plot_extremes[3:4]), 2),
	    			  plot_ablines_finmets[fmp]),
	    			col="gray95", border=FALSE)
	    	}else{
	    		polygon(
	    			c(rep(min(plot_extremes[1:2]), 2),
	    			  rep(max(plot_extremes[1:2]),2)),
	    			c(min(plot_extremes[3:4]),
	    			  rep(plot_ablines_finmets[fmp], 2),
	    			  min(plot_extremes[3:4])),
	    			col="gray95", border=FALSE)	
	    	}
	    	# Add a line to distinguish the cost effectiveness threshold
	    	abline(h=plot_ablines_finmets[fmp], lwd=2, lty=3, col="gray50")
	     	# Add individual ECM points to the cost effectiveness plot
	     	points(results_x, results_y, col="gray70", pch=results_pch,
	     	       bg=results_bg, lwd=0.75, cex = 1.2)
      	# Add x axis tick marks and axis labels
      	axis(side=1, at=xlim, labels=xlim, cex.axis=1.25)
      	mtext(plot_axis_labels_finmets_x[v], side=1, line=3.25, cex=0.9) 
      	# Add y axis tick marks and axis labels
      	axis(side=2, at=ylim_fm, labels=ylim_fm, cex.axis = 1.25, las=1)
		  	# Add label with total cost effective savings
		  	label_text = paste('Cost effective impact:', toString(sprintf("%.1f", total_save)),
		  	                   var_units[v], sep=" ")
        # Set increment to use in plotting cost effective savings text
        ylim_inc = (max(ylim_fm) - min(ylim_fm))*0.05
	      shadowtext(0-max(xlim)/50, max(ylim_fm) - 0.25*ylim_inc, label_text, cex=0.85,
	      	           bg="gray98", col="black", pos=4, offset=0, r=0.2)
        # If needed, add disclaimer about the use of public health costs below
        # the cost effective savings text
        if (var_names_uncompete[v] == "cost" & phc_flag != FALSE){
          if (phc_flag == "low"){
            shadowtext(0-max(xlim)/50, max(ylim_fm)-1.25*ylim_inc, labels=
              "* Reflects low EPA health benefits",
              col="red", pos=4, cex=0.85, bg="gray98", offset=0, r=0.2)
            shadowtext(0-max(xlim)/50, max(ylim_fm)-2.25*ylim_inc, labels=
              "  - ignore results after 2025",
              col="red", pos=4, cex=0.85, bg="gray98", offset=0, r=0.2)
          }else{
            shadowtext(0-max(xlim)/50, max(ylim_fm)-1.25*ylim_inc, labels=
              "* Reflects high EPA health benefits",
              col="red", pos=4, cex=0.85, bg="gray98", offset=0, r=0.2)
            shadowtext(0-max(xlim)/50, max(ylim_fm)-2.25*ylim_inc, labels=
              "  - ignore results after 2025",
              col="red", pos=4, cex=0.85, bg="gray98", offset=0, r=0.2)
          }
        }
	     	mtext(plot_axis_labels_finmets_y[fmp], side=2, line=3.75, cex=0.9)
	     	if (is.finite(max(label_vals_y))){
	      	# Add number ranking labels to top 5 ECM points
	     	 	text(label_vals_x, label_vals_y,
	     	       labels = seq(1, length(label_vals_x)), pos=3, cex=0.6, col="black")
	     	 	# Add a legend with top 5 ECM names; scale this legend down when public
          # health benefits have been considered, in which case ECM names tend to
          # be longer
	     	 	if (var_names_uncompete[v] == "cost" & phc_flag != FALSE){
            cex_ce_leg = 0.7
          }else{
            cex_ce_leg = 0.85
          }
          legend("topright", border=FALSE, bty="n", col=FALSE, bg=FALSE, lwd=FALSE,
                     legend = meas_names_lgnd, cex=cex_ce_leg)
	      }
	    }
    }
    
    # Add a series of legends to the second page of the PDF device that distinguish
    # the applicable climate zone, building type, and end use of each ECM point on
    # the plot by point outline color, shape, and fill color, respectively
    # Initialize a blank plot region to put the legends in 
    plot(1, type="n", axes=F, xlab="", ylab="") # creates blank plot square for legend
    # Add legend for applicable climate zone
    # legend("topleft", legend = c(czones_out_lgnd, 'Multiple'),
           # pt.lwd = rep(1, length(czones_out_lgnd) + 1), pt.cex = 1.2,
           # pt.bg = rep(NA, length(czones_out_lgnd) + 1),
           # col = c(czones_out_col, "gray50"),
           # pch = rep(21, length(czones_out_lgnd) + 1),
           # bty="n", cex=0.8, title=expression(bold('Climate Zone'))) 
    # Add legend for applicable building type
    legend("topleft", legend = c(bclasses_out_finmets_lgnd, 'Multiple'),
           col = rep("black", length(bclasses_out_finmets_lgnd) + 1),
           pt.lwd = rep(1, length(bclasses_out_finmets_lgnd) + 1),
           pt.bg = rep("black", length(bclasses_out_finmets_lgnd) + 1),
           pt.cex = 1.1, pch = c(bclasses_out_finmets_shp, 24),
           bty="n", cex=0.8, title=expression(bold('Building Type')))  
    # Add legend for applicable end use
    legend("top", legend = c(euses_out_finmets_lgnd, 'Multiple'),
          pt.lwd = rep(1, length(euses_out_finmets_lgnd) + 1),
          pt.cex = 1.2, col = c(euses_out_finmets_col, "gray50"),
          pch = rep(16, length(euses_out_finmets_lgnd) + 1),
          bty="n", cex=0.8, title=expression(bold('End Use')))  
    dev.off()

    # Create variable name to store data to be written to one worksheet
    # of an Excel spreadsheet
    xlsx_unique_var_name <- paste("dataset", v, sep="")

    # Add variable name to a list of variable names that will indicate to the
    # WriteXLS function the data to be written to the Excel spreadsheet
    xlsx_var_name_list[v] <- xlsx_unique_var_name

    # Assign current data to the variable name generated and stored for use
    # in writing out the Excel data. Note: throw out the first two rows in the
    # data, which are dedicated to uncompeted energy, carbon, and cost results
    # summed across all ECMs (these results are not meaningful)
    assign(xlsx_unique_var_name, xlsx_data[3:nrow(xlsx_data), 1:ncol(xlsx_data)])
  }

  # Write data to Excel xlsx-formatted spreadsheet with worksheets
  # named using the SheetNames attribute
  WriteXLS(xlsx_var_name_list, ExcelFileName = xlsx_file_name, SheetNames = file_names_ecms)
}
