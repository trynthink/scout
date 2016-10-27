# ============================================================================
# Load required packages and files
# ============================================================================

# Load rjson for reading in JSON files
if(!require("rjson")){install.packages("rjson")}
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
# Set plot colors for uncompeted baseline, efficient and low/high results
plot_col_uc_base = "gray60"
plot_col_uc_eff = "gray80"
plot_col_uc_lowhigh = "gray90"

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
# Set variable names to use in accessing all uncompeted energy, carbon, and cost results from JSON data
var_names_uncompete <- c('energy', 'carbon', 'cost')
# Set variable names to use in accessing competed baseline energy, carbon, and cost results from JSON data
var_names_compete_base <- c(
  'Baseline Energy Use (MMBtu)', 'Baseline CO₂ Emissions (MMTons)', 'Baseline Energy Cost (USD)') 
# Set variable names to use in accessing competed efficient energy, carbon, and cost results from JSON data. Note
# that each variable potentially has a '(low)' and '(high)' variant in the JSON.
var_names_compete_eff_m <- c(
  'Efficient Energy Use (MMBtu)', 'Efficient CO₂ Emissions (MMTons)', 'Efficient Energy Cost (USD)')
var_names_compete_eff_l <- c(
  'Efficient Energy Use (low) (MMBtu)', 'Efficient CO₂ Emissions (low) (MMTons)', 'Efficient Energy Cost (low) (USD)') 
var_names_compete_eff_h <- c(
  'Efficient Energy Use (high) (MMBtu)', 'Efficient CO₂ Emissions (high) (MMTons)', 'Efficient Energy Cost (high) (USD)') 
# Initialize a matrix used to store baseline data for the uncompeted plot
# (to be included for reference in the competed plot)

# ============================================================================
# Generate plots for total energy, carbon, and cost
# ============================================================================

# Loop through all adoption scenarios
for (a in 1:length(adopt_scenarios)){

  # Set plot colors for competed baseline, efficient, and low/high results
  # (varies by adoption scenario)
  if (adopt_scenarios[a] == "Technical potential"){
    plot_col_c_base = "midnightblue"
    plot_col_c_eff = "lightskyblue"
    plot_col_c_lowhigh = "lightskyblue"
  }else{
    plot_col_c_base = "red3"
    plot_col_c_eff = "pink"
    plot_col_c_lowhigh = "lightpink"
  }
  
  # Loop through all plotting variables
  for (v in 1:length(var_names_uncompete)){

    # Set a factor to convert the results data to final plotting units for given variable
    # (quads for energy, MMT for carbon, and billion $ for cost)
    if ((var_names_uncompete[v] == "energy") | (var_names_uncompete[v] == "cost")){
      unit_translate = 1/1000000000 # converts energy from MBtu -> quads or cost from $ -> billion $
      }else{
        unit_translate = 1 # carbon results data are already imported in MMT units
      }
    
      # Initialize results vector (3 rows accommodate mean, low, and high results values;
      # 4 columns accommodate 2 outputs (baseline and efficient) x 2 adoption scenarios)
      results <- matrix(list(), 3, 2*length(comp_schemes))
      # Initialize uncertainty flag for the adoption scenario
      uncertainty = FALSE
      # Set the file name for the plot based on the adoption scenario and plotting variable
      if (adopt_scenarios[a] == 'Technical potential'){
        plot_file_name = paste(base_dir, '/engine_results/plots/tech_potential/', plot_names[v],".pdf", sep = "")
      }else{
        plot_file_name = paste(base_dir, '/engine_results/plots/max_adopt_potential/', plot_names[v],".pdf", sep = "")
      }
    
      # Open PDF plot device
      pdf(plot_file_name,width=13,height=14)
      # Set number of rows and columns per page in PDF output
      par(mfrow=c(4,4))
      # Reconfigure space around each side of the plot for best fit
      par(mar=c(5.1,5.1,3.1,2.1))
    
    # Loop through all ECMs
    for (m in 1:length(meas_names)){
    
      # Find the index for accessing the item in the list of uncompeted results that corresponds
      # to data for the current ECM. Note: competed results are accessed directly by ECM name,
      # and do not require an index
      for (uc in 1:length(uncompete_results)){
        if (uncompete_results[[uc]]$'name' == meas_names[m]){
          uc_name_ind = uc
        }
      }

      # Loop through all competition schemes
      for (cp in 1:length(comp_schemes)){
          
        # Set matrix for temporarily storing finalized baseline and efficient results
        r_temp <- matrix(NA, 4, length(years))  
        # Find data for uncompeted energy, carbon, and/or cost
        if (comp_schemes[cp] == "uncompeted"){
          # Set the appropriate database of uncompeted results (access keys vary based on plotted variable)
          if (var_names_uncompete[v] != "cost"){
            results_database = 
              uncompete_results[[uc_name_ind]]$'markets'[[adopt_scenarios[a]]]$
              'master_mseg'[[var_names_uncompete[v]]]$'total' 
            }else{
              results_database = 
                uncompete_results[[uc_name_ind]]$'markets'[[adopt_scenarios[a]]]$
                'master_mseg'[[var_names_uncompete[v]]]$'energy'$'total'
            }
          # Order the uncompeted results by year and determine low/high bounds on each result value
          # (if applicable)
          for (yr in 1:length(years)){
            r_temp[1, yr] = results_database$'baseline'[years[yr]][[1]]
            # Set mean, low, and high values for case with ECM input/output uncertainty
            if (length(results_database$'efficient'[years[1]][[1]]) > 1){
              # Take mean of list of values from uncompeted results
              r_temp[2, yr] = mean(results_database$'efficient'[years[yr]][[1]])
              # Take 5th/95th percentiles of list of values from uncompeted results
              r_temp[3:4, yr] = quantile(results_database$'efficient'[years[yr]][[1]], c(0.05, 0.95))
              uncertainty = TRUE
              # Set mean, low, and high values for case without ECM input/output uncertainty
              # (all values equal to mean value)
              }else{
                r_temp[2:4, yr] = results_database$'efficient'[years[yr]][[1]]
              }
          }
        # Find data for competed energy, carbon, and/or cost
        }else{
          # Set the appropriate database of competed results
          results_database = compete_results[[meas_names[m]]]$
            'Markets and Savings (Overall)'[[adopt_scenarios[a]]]
          # Order the competed results by year and determine low/high bounds on each result value
          # (if applicable)
          for (yr in 1:length(years)){
            r_temp[1, yr] = results_database[[var_names_compete_base[v]]][years[yr]][[1]]
            # Set mean, low, and high values for case with ECM input/output uncertainty
            if (length(which(grepl('low', names(results_database))))>0) {
              # Take mean value output directly from competed results
              r_temp[2, yr] = results_database[[var_names_compete_eff_m[v]]][years[yr]][[1]]
              # Take 'low' value output directly from competed results (represents 5th percentile)
              r_temp[3, yr] = results_database[[var_names_compete_eff_l[v]]][years[yr]][[1]]
              # Take 'high' value output directly from competed results (represents 95th percentile)
              r_temp[4, yr] = results_database[[var_names_compete_eff_h[v]]][years[yr]][[1]]
              # Flag output uncertainty in the current plot
              uncertainty = TRUE
              # Set mean, low, and high values for case without ECM input/output uncertainty
              # (all values equal to mean value)
              }else{
                r_temp[2:4, yr] = results_database[[var_names_compete_eff_m[v]]][years[yr]][[1]]
              }
          }
        }
        # Set the column start and stop indexes to use in updating the matrix of results
        ind_start = ((cp-1)*(length(comp_schemes))) + 1
        ind_end = ind_start + 1 # note this accommodates baseline and efficient outcomes
        # Update results matrix with mean, low, and high baseline and efficient outcomes
        results[, ind_start:ind_end] = rbind(cbind(list(r_temp[1,]), list(r_temp[2,])),
                                             cbind(list(r_temp[1,]), list(r_temp[3,])),
                                             cbind(list(r_temp[1,]), list(r_temp[4,])))
      }

      # Set uncompeted and competed baseline results for given adoption scenario,
      # plotting variable, and ECM  
      base_uc = unlist(results[1, 1]) * unit_translate
      base_c = unlist(results[1, 3]) * unit_translate
      # Set uncompeted and competed efficient results for adoption scenario,
      # plotting variable, and ECM (mean and low/high values)
      eff_uc_m = unlist(results[1, 2]) * unit_translate
      eff_uc_l = unlist(results[2, 2]) * unit_translate
      eff_uc_h = unlist(results[3, 2]) * unit_translate
      eff_c_m = unlist(results[1, 4]) * unit_translate
      eff_c_l = unlist(results[2, 4]) * unit_translate
      eff_c_h = unlist(results[3, 4]) * unit_translate
      
      # Find the min. and max. values in the data to be plotted
      min_val = min(c(base_uc, base_c, eff_uc_m, eff_uc_l, eff_uc_h,
                      eff_c_m, eff_c_l, eff_c_h))
      max_val = max(c(base_uc, base_c, eff_uc_m, eff_uc_l, eff_uc_h,
                      eff_c_m, eff_c_l, eff_c_h))
      # Set limits of y axis for plot based on min. and max. values in data
      ylims = pretty(c(min_val-0.05*max_val, max_val+0.05*max_val))

      # Initialize the plot with uncompeted baseline results
      plot(years, base_uc, typ='l', lwd=5, ylim = c(min(ylims), max(ylims)),
           xlab=NA, ylab=NA, col=plot_col_uc_base, main = meas_names[m], xaxt="n", yaxt="n")
        
      # Determine legend parameters based on whether uncertainty is present in results
      if (uncertainty == TRUE){
        # Set legend parameters for a plot with uncertainty in the results
        legend_param = c(
          "Baseline (Uncompeted)", "Baseline (Competed)",
          "Efficient (Uncompeted)", "Efficient (Competed)",
          "Efficient (Uncompeted, 5th/95th PCT)", "Efficient (Competed, 5th/95th PCT)")
        col_param = c(plot_col_uc_base, plot_col_c_base, plot_col_uc_eff,
                      plot_col_c_eff, plot_col_uc_lowhigh, plot_col_c_lowhigh)
        lwd_param = c(5, 3, 3.5, rep(2, 4))
        lty_param = c(rep(1, 4), rep(3, 2))
        }else{
          # Set legend parameters for a plot with no uncertainty in the results
          legend_param = c("Baseline (Uncompeted)", "Baseline (Competed)",
                           "Efficient (Uncompeted)", "Efficient (Competed)")
          col_param = c(plot_col_uc_base, plot_col_c_base, plot_col_uc_eff, plot_col_c_eff)
          lwd_param = c(5, 3, 3.5, rep(2, 2))
          lty_param = rep(1, 4)  
        }
     
      # Add low/high bounds on uncompeted and competed baseline and efficient
      # results, if applicable
      if (uncertainty == TRUE){
        lines(years, eff_uc_l, lwd=2, lty=3, col=plot_col_uc_lowhigh)
        lines(years, eff_uc_h, lwd=2, lty=3, col=plot_col_uc_lowhigh)
        lines(years, eff_c_l, lwd=2, lty=3, col=plot_col_c_lowhigh)
        lines(years, eff_c_h, lwd=2, lty=3, col=plot_col_c_lowhigh)
      }
      # Add mean uncompeted efficient results
      lines(years, eff_uc_m, lwd=3, col=plot_col_uc_eff)
      # Add competed baseline results
      lines(years, base_c, lwd=3.5, col=plot_col_c_base)
      # Add mean competed efficient results
      lines(years, eff_c_m, lwd=2, col=plot_col_c_eff)
      
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
    legend("top", legend=legend_param, lwd=lwd_param, col=col_param, lty=lty_param, 
       bty="n", border = FALSE, merge = TRUE, cex=1.15)
    # Close plot device
    dev.off()
  }
}
