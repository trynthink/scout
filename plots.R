# ============================================================================
# Load required packages and files
# ============================================================================
# Load rjson for reading in JSON files
require("rjson")
# Get current working directory path
base_dir = getwd()
# Import uncompeted ECM energy, carbon, and cost data
uncompete_results<-fromJSON(file = paste(base_dir, '/measures_data/meas_summary_data.json', sep=""))
# Import competed ECM energy, carbon, and cost data
compete_results<-fromJSON(file = paste(base_dir, '/engine_results/meas_engine_out.json', sep=""))

# ============================================================================
# Set high-level plotting parameters
# ============================================================================
# Set plot names
plot_names <- c('Total Energy', 'Total Carbon', 'Total Cost')
# Set plot axis labels
plot_axis_labels<-c('Primary Energy Use (Quads)', expression(CO[2] ~" Emissions (MMTons)"), 'Energy Cost (Billion $)')

# ============================================================================
# Set high-level ECM variables
# ============================================================================
# Set ECM adoption scenarios
adopt_scenarios <- c('Technical potential', 'Max adoption potential')
# Set ECM competition scenarios
comp_schemes <- c('uncompeted', 'competed')
# Set ECM names and order alphabetically
meas_names <- names(compete_results)
meas_names <- meas_names[order(meas_names)]
# Set years in modeling time horizon and reorganize in ascending order
years<-row.names(as.matrix(
  compete_results[[meas_names[1]]]$'Markets and Savings (Overall)'$'Technical potential'$'Baseline Energy Use (MMBtu)'))
years<-years[order(years)]
# Set variable names to use in accessing uncompeted energy, carbon, and cost results from JSON data
var_names_uncompete <- c('energy', 'carbon', 'cost')
# Set variable names to use in accessing competed baseline and efficient energy, carbon, and cost results from JSON data
var_names_compete_base <- c(
  'Baseline Energy Use (MMBtu)', 'Baseline CO₂ Emissions (MMTons)', 'Baseline Energy Cost (USD)') 
var_names_compete_eff <- c(
  'Efficient Energy Use (MMBtu)', 'Efficient CO₂ Emissions (MMTons)', 'Efficient Energy Cost (USD)') 

# ============================================================================
# Generate plots for total energy, carbon, and cost
# ============================================================================
# Loop through all plotting variables
for (v in 1:length(var_names_uncompete)){
 
  # Set the file name for the plot
  plot_file_name = paste(base_dir, '/engine_results/', plot_names[v],".pdf", sep = "")
  # Open PDF plot device
  pdf(plot_file_name,width=13,height=14)
  # Set number of rows and columns per page in PDF output
  par(mfrow=c(4,4))
  # Reconfigure space around each side of the plot for best fit
  par(mar=c(5.1,5.1,3.1,2.1))
  
  # Loop through all ECMs
  for (m in 1:length(meas_names)){
    
    # Initialize results vector (length = 2 outputs (baseline and efficient) x 
    # 2 adoption scenarios x 2 competition schemes)
    results <- matrix(list(), 1, 2*length(adopt_scenarios)*length(comp_schemes))
    
    # Find the index for accessing the item in the list of uncompeted results that corresponds
    # to data for the current ECM. Note: competed results are accessed directly by ECM name,
    # and do not require an index
    for (uc in 1:length(uncompete_results)){
      if (uncompete_results[[uc]]$'name' == meas_names[m]){
        uc_name_ind = uc
      }
    }

    # Loop through all adoption scenarios
    for (a in 1:length(adopt_scenarios)){
      # Loop through competition schemes
      for (cp in 1:length(comp_schemes)){
        # Find data for uncompeted cost
        if ((comp_schemes[cp] == "uncompeted") & (var_names_uncompete[v] == "cost")){
          results_database = uncompete_results[[uc_name_ind]]$'markets'[[adopt_scenarios[a]]]$'master_mseg'[[var_names_uncompete[v]]]$'energy'$'total'
          results_val = cbind(list(results_database$'baseline'), list(results_database$'efficient'))
        # Find data for uncompeted energy or carbon
        }else if ((comp_schemes[cp] == "uncompeted") & (var_names_uncompete[v] != "cost")){
          results_database = uncompete_results[[uc_name_ind]]$'markets'[[adopt_scenarios[a]]]$'master_mseg'[[var_names_uncompete[v]]]$'total'
          results_val = cbind(list(results_database$'baseline'), list(results_database$'efficient'))
        # Find data for competed energy, carbon, and/or cost
        }else{
          results_database = compete_results[[meas_names[m]]]$'Markets and Savings (Overall)'[[adopt_scenarios[a]]]
          results_val = cbind(list(results_database[[var_names_compete_base[v]]]), list(results_database[[var_names_compete_eff[v]]]))
        }
        # Set the start and stop indexes to use in updating the vector of results
        ind_start = ((a-1)*(length(adopt_scenarios)^2)) + ((cp-1)*length(comp_schemes) + 1)
        ind_end = ind_start + 1 # note this accomodates 'baseline' and 'efficient' outcomes
        # Update results vector
        results[1, ind_start:ind_end] = results_val    
      }
    }
    
    # Set a factor to convert the results data to final plotting units
    # (quads (for energy), MMT (for carbon), and billion $ (for cost))
    if ((var_names_uncompete[v] == "energy") | (var_names_uncompete[v] == "cost")){
      unit_translate = 1/1000000000 # converts energy from MBtu -> quads or cost from $ -> billion $
    }else{
      unit_translate = 1 # carbon results data are already imported in MMT units
    }
    # Set baseline results (ordered by year)
    tp_uc_b = unlist(results[1])[order(rownames(as.matrix(unlist(results[1]))))] * unit_translate
    # Set efficient results for uncompeted technical potential case (ordered by year)
    tp_uc_e = unlist(results[2])[order(rownames(as.matrix(unlist(results[2]))))] * unit_translate
    # Set efficient results for competed technical potential case (ordered by year)
    tp_c_e = unlist(results[4])[order(rownames(as.matrix(unlist(results[4]))))] * unit_translate
    # Set efficient results for uncompeted max adoption potential case (ordered by year)
    map_uc_e = unlist(results[6])[order(rownames(as.matrix(unlist(results[6]))))] * unit_translate
    # Set efficient results for competed max adoption potential case (ordered by year)
    map_c_e = unlist(results[8])[order(rownames(as.matrix(unlist(results[8]))))] * unit_translate
    
    # Set limits of y axis for plot based on min and max values in data to be plotted
    ylims = pretty(c(min(tp_uc_e)-0.15*max(tp_uc_b),max(tp_uc_b)+0.15*max(tp_uc_b)))
    
    # Initiate plot region with baseline results
    plot(years, tp_uc_b, typ='l', lwd=4, ylim = c(min(ylims), max(ylims)),
         xlab=NA, ylab=NA, col="gray30", main = meas_names[m], xaxt="n", yaxt="n")
      
    # Add efficient uncompeted technical potential results
    lines(years, tp_uc_e, lwd=2.5, col="dodgerblue4")
    # Add efficient competed technical potential results
    lines(years, tp_c_e, lwd=2, col="dodgerblue", lty=6)
    # Add efficient uncompeted max adoption potential results
    lines(years, map_uc_e, lwd=2.5, col="firebrick4")
    # Add efficient competed max adoption potential
    lines(years, map_c_e, lwd=2, col="firebrick1", lty=6)
    
    # Add x and y axis labels
    mtext("Year", side=1, line=3.5, cex=0.925)
    mtext(plot_axis_labels[v], side=2, line=3.75, cex=0.925)
    # Add tick marks and labels to bottom and left axes
    axis(side=1, at=pretty(c(min(years), max(years))),
        labels=pretty(c(min(years), max(years))), cex.axis = 1.2)
    axis(side=2, at=ylims, labels = ylims, cex.axis = 1.2, las=1)
    # Add tick marks to top and right axes
    axis(side=3, at=pretty(c(min(years), max(years))), labels = NA)
    axis(side=4, at=ylims, labels = NA)
  }
  
  # Add plot legend
  par(xpd=TRUE)
  plot(1, type="n", axes=F, xlab="", ylab="") # creates blank plot square for legend
  legend("top", legend=c("Baseline", "Efficient (Max Adoption, Competed)", "Efficient (Max Adoption, Uncompeted)",
                         "Efficient (Technical Potential, Competed)", "Efficient (Technical Potential, Uncompeted)"),
         bty="n", fill=c(NA,NA,NA,NA,NA), border = FALSE, lwd=c(4,2,2.5,2,2.5), col=c(
           "gray30", "red", "dark red", "dodger blue", "midnight blue"), lty=c(1,6,1,6,1), merge = TRUE, cex=1.15)
  
  dev.off()
}
