# ============================================================================
# Load required packages and files
# ============================================================================

# Load rjson for reading in JSON files
if(!require("rjson")){install.packages("rjson")}
require("rjson")
# Specify JSON file encoding
options("encoding" = "UTF-8")
# Load XLSX for writing out raw data to MS Excel
if(!require("xlsx")){install.packages("xlsx")}
require("xlsx")
# Get current working directory path
base_dir = getwd()
# Import uncompeted ECM energy, carbon, and cost data
uncompete_results<-fromJSON(file = file.path(base_dir, 'supporting_data','ecm_prep.json'))
# Import competed ECM energy, carbon, and cost data
compete_results<-fromJSON(file = file.path(base_dir, 'results','ecm_results.json'))

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
# Set output units for each variable type
var_units <- c('Quads', 'MMTons', 'Billion $')
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

# Set column names for Excel file
col_names_xlsx<- c('ECM Name', 'Results Scenario', 'Units', 'Climate Zones', 'Building Classes', 'End Uses', years)

# ============================================================================
# Generate plots for total energy, carbon, and cost
# ============================================================================

# Loop through all adoption scenarios
for (a in 1:length(adopt_scenarios)){

  # Set plot colors for competed baseline, efficient, and low/high results
  # (varies by adoption scenario); also set XLSX summary data file name for adoption scenario
  if (adopt_scenarios[a] == "Technical potential"){
    # Set plot colors
    plot_col_c_base = "midnightblue"
    plot_col_c_eff = "lightskyblue"
    plot_col_c_lowhigh = "lightskyblue"
    # Set XLSX summary data file name
    xlsx_file_name = file.path(base_dir, 'results', 'plots', 'tech_potential', "Summary_Data-TP.xlsx")
  }else{
    # Set plot colors
    plot_col_c_base = "red3"
    plot_col_c_eff = "pink"
    plot_col_c_lowhigh = "lightpink"
    # Set XLSX summary data file name
    xlsx_file_name = file.path(base_dir, 'results', 'plots', 'max_adopt_potential', "Summary_Data-MAP.xlsx")
  }
  
  # Loop through all plotting variables
  for (v in 1:length(var_names_uncompete)){

    # Initialize data frame to write to XLSX sheet (note: number of rows equals to
    # number of ECMs * number of results scenarios (baseline/efficient + competed/uncompeted) plus
    # two additional rows to accommodate baseline/efficient competed results summed across all ECMs)
    xlsx_data<-data.frame(matrix(ncol = length(col_names_xlsx),
                                 nrow = (length(meas_names)*4 + 2)))
    # Set column names for the XLSX sheet
    colnames(xlsx_data) = col_names_xlsx
    # Add variable units to the XLSX data frame
    xlsx_data[, 3] = rep(var_units[v], nrow(xlsx_data))

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
        plot_file_name = file.path(base_dir, 'results', 'plots', 'tech_potential', paste(plot_names[v],"-TP.pdf", sep=""))
      }else{
        plot_file_name = file.path(base_dir, 'results', 'plots', 'max_adopt_potential', paste(plot_names[v],"-MAP.pdf", sep = ""))
      }
    
      # Open PDF plot device
      pdf(plot_file_name,width=13,height=14)
      # Set number of rows and columns per page in PDF output
      par(mfrow=c(4,4))
      # Reconfigure space around each side of the plot for best fit
      par(mar=c(5.1,5.1,3.1,2.1))
    
    # Loop through all ECMs
    for (m in 1:length(meas_names)){
    
      # Add ECM name to XLSX data frame
      row_ind_start = (m-1)*4 + 1
      xlsx_data[row_ind_start:(row_ind_start + 3), 1] = meas_names[m]
      
      # Set applicable climate zones, end uses, and building classes for ECM and add to XLSX data frame
      czones = toString(compete_results[[meas_names[m]]]$'Filter Variables'$'Applicable Climate Zones')
      bldg_types = toString(compete_results[[meas_names[m]]]$'Filter Variables'$'Applicable Building Classes')
      end_uses = toString(compete_results[[meas_names[m]]]$'Filter Variables'$'Applicable End Uses')
      xlsx_data[row_ind_start:(row_ind_start + 3), 4] = czones
      xlsx_data[row_ind_start:(row_ind_start + 3), 5] = bldg_types
      xlsx_data[row_ind_start:(row_ind_start + 3), 6] = end_uses

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
          
        # Add name of results scenario (baseline/efficient + competed/uncompeted) to XLSX data frame
        xlsx_data[(row_ind_start + (cp-1)*2):(row_ind_start + (cp-1)*2 + 1), 2] = c(
          paste("Baseline ", comp_schemes[cp], sep = ""), paste("Efficient ", comp_schemes[cp], sep = ""))
        
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
        col_ind_start = ((cp-1)*(length(comp_schemes))) + 1
        col_ind_end = col_ind_start + 1 # note this accommodates baseline and efficient outcomes
        # Update results matrix with mean, low, and high baseline and efficient outcomes
        results[, col_ind_start:col_ind_end] = rbind(cbind(list(r_temp[1,]), list(r_temp[2,])),
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
      
      # Add ECM results to XLSX data frame
      xlsx_data[row_ind_start:(row_ind_start + 3), 7:ncol(xlsx_data)] = 
        rbind(base_uc, eff_uc_m, base_c, eff_uc_m)
      
      # Initialize or update summed results across all ECMs
      if (m == 1){
        base_c_all = base_c
        eff_c_m_all = eff_c_m
      }else{
        base_c_all = base_c_all + base_c
        eff_c_m_all = eff_c_m_all + eff_c_m
      }
      
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
      
      # Add ECM end use labels
      text(min(years), max(ylims), labels=paste("End Uses: ", end_uses, sep=""), col="gray50", pos=4)
    }
  
    # Add results across all ECMs to XLSX data frame
    row_ind_start = (length(meas_names))*4 + 1
    xlsx_data[row_ind_start:(row_ind_start + 1), 1] = "All ECMs"
    xlsx_data[row_ind_start:(row_ind_start+1), 2] = c("Baseline competed", "Efficient competed")
    # Add data to XLSX data frame
    xlsx_data[row_ind_start:(row_ind_start + 1), 7:ncol(xlsx_data)] = rbind(base_c_all, eff_c_m_all)
    
    # Plot results across all ECMs
    
    # Find the min. and max. values in the data to be plotted
    min_val = min(c(base_c_all, eff_c_m_all))
    max_val = max(c(base_c_all, eff_c_m_all))
    # Set limits of y axis for plot based on min. and max. values in data
    ylims = pretty(c(min_val-0.05*max_val, max_val+0.05*max_val))

    # Initialize the plot with uncompeted baseline results across all ECMs
    plot(years, base_c_all, typ='l', lwd=5, ylim = c(min(ylims), max(ylims)),
         xlab=NA, ylab=NA, col=plot_col_c_base, main = "All ECMs", xaxt="n", yaxt="n")
    # Add mean competed efficient results across all ECMs
    lines(years, eff_c_m_all, lwd=2, col=plot_col_c_eff)
    
    # Annotate the plot with 2030 savings figure
    # Find x and y values for annotation
    xval_2030 = 2030
    yval_2030_eff = eff_c_m_all[which(years=="2030")]
    yval_2030_base = base_c_all[which(years=="2030")]
    # Draw line segment connecting 2030 baseline and efficient results
    points(xval_2030, yval_2030_base, col="light green", pch = 1, cex=1.5, lwd=2.5)
    points(xval_2030, yval_2030_eff, col="light green", pch = 1, cex=1.5, lwd=2.5)
    segments(xval_2030, yval_2030_eff, xval_2030, yval_2030_base, col="green", lty=3)
    # Add 2030 savings figure
    text(xval_2030, yval_2030_eff - (yval_2030_eff - min(ylims))/7,
         paste(toString(sprintf("%.1f", yval_2030_base-yval_2030_eff)),
               toString(var_units[v]), sep=" "), pos = 1, col="green")
    
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

    # Add plot legend
    par(xpd=TRUE)
    plot(1, type="n", axes=F, xlab="", ylab="") # creates blank plot square for legend
    legend("top", legend=legend_param, lwd=lwd_param, col=col_param, lty=lty_param, 
       bty="n", border = FALSE, merge = TRUE, cex=1.15)
    # Close plot device
    dev.off()
    
    # Write data to XLSX sheet
    # First variable and adoption scenario - create XLSX file
    if (v == 1){
      write.xlsx(x = xlsx_data, file = xlsx_file_name,
                 sheetName = plot_names[v], row.names = FALSE, append = FALSE)
      # Subsequent variable and adoption scenario - add to XLSX file
      }else{
      write.xlsx(x = xlsx_data, file = xlsx_file_name,
                 sheetName = plot_names[v], row.names = FALSE, append = TRUE)
      }
  }
}
