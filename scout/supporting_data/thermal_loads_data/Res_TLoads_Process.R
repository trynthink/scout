# ===============================================================================
# Residential Thermal Loads Processing Script
# ===============================================================================
# This script processes residential thermal loads data and creates conversion 
# tables for mapping between census divisions and climate zones.
#
# Part 1: Process residential thermal loads by building type and end use
# Part 2: Create census division to climate zone conversion tables from RECS data
# ===============================================================================

# Set working directory to the thermal loads data folder
setwd('e:/git/scout/scout/supporting_data/thermal_loads_data')

# ===============================================================================
# PART 1: RESIDENTIAL THERMAL LOADS PROCESSING
# ===============================================================================

# Read residential thermal loads base data
res_comp_names <- (read.csv('Res_TLoads_Base.csv',header=TRUE))
header = names(res_comp_names)  # Store column headers for later use
res_comp <- as.matrix(res_comp_names)  # Convert to matrix for easier indexing

# Define maximum dimensions for processing
cdivmax = 9   # Maximum number of census divisions (1-9)
bldgmax = 3   # Maximum number of building types (1-3)
eusemax = 2   # Maximum number of end uses (1-2: heating and cooling)

# Initialize counter for final matrix row indexing
counter = 1

# Initialize final output matrix 
# Dimensions: (9 census divisions × 3 building types × 2 end uses) × 12 columns
finalmat = matrix(NA,cdivmax*bldgmax*eusemax,12)

# Process thermal loads data for each combination of building type, census division, and end use
# Routine to establish weighted loads components for residential building types
for (b in 1:bldgmax){    # Loop through building types (1-3)
  for (c in 1:cdivmax){  # Loop through census divisions (1-9) 
    for (e in 1:eusemax){ # Loop through end uses (1-2: heating/cooling)
      
      # Select appropriate columns based on end use
      if (e == 1){   
        # End use 1 (heating): use columns 1-12
        startmat = res_comp[,1:12]
      }else{  
        # End use 2 (cooling): use columns 1-4 and 14-21
        startmat = cbind(res_comp[,1:4],res_comp[,14:21])
      }
        
      # Filter data for current building type and census division
      filtermat = startmat[((startmat[,1]==b)&(startmat[,2]==c)),]
      
      # Calculate total building stock for weighting
      bldgsum = sum(filtermat[,4])
      
      # Initialize matrix to store row weights
      rowweights = matrix(NA,nrow(filtermat),1)
      
      # Store census division, building type, and end use in final matrix
      finalmat[counter,1:3] = c(c,b,e)
      finalmat[counter,4] = bldgsum
      
      # Initialize matrix for weighted thermal load components
      rowadd1 = matrix(NA,nrow(filtermat),8)
      
      # Calculate weighted thermal load components for each row
      for (r in 1:nrow(filtermat)){
        # Calculate weight as proportion of total building stock
        rowweights[r] = filtermat[r,4]/bldgsum
        # Apply weight to thermal load components (columns 5 onward)
        rowadd1[r,] = rowweights[r] * filtermat[r,5:(ncol(filtermat))]
      }
      
      # Sum weighted components across all rows
      rowadd2 = colSums(rowadd1)
      
      # Normalize to create fractions that sum to 1.0
      rowaddfin = rowadd2/sum(rowadd2)      
      
      # Store normalized thermal load fractions in final matrix (rounded to 4 decimal places)
      finalmat[counter,5:ncol(finalmat)] = round(rowaddfin,4)
      
      # Increment counter for next row
      counter = counter + 1
    } 
  } 
}

# Add column names to final matrix and write to output file
colnames(finalmat)<-c(header[2],header[1],'ENDUSE',header[4:12])
write.table(finalmat,'Res_TLoads_PrepFinal.txt', row.names=FALSE)

# ===============================================================================
# PART 2: CENSUS DIVISION TO CLIMATE ZONE CONVERSION TABLES
# ===============================================================================

# Read 2009 Residential Energy Consumption Survey (RECS) raw data
recs <- read.csv('2009_RECS_RawData.csv',header=TRUE)

# Extract key variables from RECS data for conversion table creation
cdivision<-recs$DIVISION    # Census division assignments
climzone<-recs$AIA_Zone     # AIA climate zone assignments  
nhouses<-recs$NWEIGHT       # Number of houses (weighted sample counts)

# Create cross-tabulation of houses by census division and climate zone
conversion_table<-tapply(nhouses,list(cdivision,climzone),sum)

# Replace NA values with zeros (occurs when no houses exist for a combination)
conversion_table[is.na(conversion_table)]<-0

# Clean up data: consolidate census divisions 8 and 9, remove unassigned climate zones
# Combines Mountain divisions (8-9) and removes buildings over 1M sqft (no climate zone)
conversion_table<-rbind(conversion_table[1:7,],colSums(conversion_table[8:9,]),conversion_table[10,])

# Initialize matrix for fractional conversion table
conversion_table_frac<-matrix(NA,nrow(conversion_table),ncol(conversion_table))

# Calculate row-wise fractions (what fraction of each census division is in each climate zone)
for (r in 1:(nrow(conversion_table))){
  # Divide each census division's climate zone counts by the total for that division
  conversion_table_frac[r,]=round((conversion_table[r,]/rowSums(conversion_table)[r]),5)
}

# Add census division identifier column and set appropriate column names
conversion_table_frac = cbind(seq(1,9,by=1),conversion_table_frac)
colnames(conversion_table_frac) = c('CDIV','AIA_CZ1','AIA_CZ2','AIA_CZ3','AIA_CZ4','AIA_CZ5')

# Write primary conversion table (census division -> climate zone fractions)
write.table(conversion_table_frac,'Res_Cdiv_Czone_ConvertTablePrep.txt',row.names=FALSE)

# ===============================================================================
# CREATE REVERSE CONVERSION TABLE (CLIMATE ZONE -> CENSUS DIVISION FRACTIONS)
# ===============================================================================

# Initialize matrix for reverse fractional conversion table
conversion_table_frac_rev<-matrix(NA,nrow(conversion_table),ncol(conversion_table))

# Calculate column-wise fractions (what fraction of each climate zone is in each census division)
for (r in 1:(nrow(conversion_table))){
  # Divide each census division's climate zone counts by the total for that climate zone
  conversion_table_frac_rev[r,]=round((conversion_table[r,]/colSums(conversion_table)),5)
}

# Add census division identifier column and set appropriate column names
conversion_table_frac_rev = cbind(seq(1,9,by=1),conversion_table_frac_rev)
colnames(conversion_table_frac_rev) = c('CDIV','AIA_CZ1','AIA_CZ2','AIA_CZ3','AIA_CZ4','AIA_CZ5')

# Write reverse conversion table (climate zone -> census division fractions)
write.table(conversion_table_frac_rev,'Res_Cdiv_Czone_ConvertTablePrep_Rev.txt',row.names=FALSE)

# ===============================================================================
# SCRIPT COMPLETION
# ===============================================================================
# Output files created:
# 1. Res_TLoads_PrepFinal.txt - Processed thermal loads by building type and end use
# 2. Res_Cdiv_Czone_ConvertTablePrep.txt - Census division to climate zone fractions  
# 3. Res_Cdiv_Czone_ConvertTablePrep_Rev.txt - Climate zone to census division fractions
# ===============================================================================


