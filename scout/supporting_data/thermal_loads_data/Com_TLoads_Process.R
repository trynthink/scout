# ==============================================================================
# COMMERCIAL THERMAL LOADS DATA PROCESSING SCRIPT
# ==============================================================================
# This script processes base thermal loads data for commercial buildings and 
# converts it from climate zone-based to census division-based organization
# for use in building energy modeling and analysis.
#
# Input: Com_TLoads_Base.csv - Base thermal loads data by climate zone
# Output: Com_TLoads_PrepFinal.txt - Processed thermal loads by census division
#         Com_Cdiv_Czone_ConvertTablePrep.txt - Conversion factors
#         Com_Cdiv_Czone_ConvertTablePrep_Rev.txt - Reverse conversion factors
# ==============================================================================

# Set working directory to the thermal loads data folder
setwd('e:/git/scout/scout/supporting_data/thermal_loads_data')

# Read in the base CSV file containing thermal loads data
# This file contains thermal load components organized by:
# - Climate zone (columns 1-5: AIA Climate Zones 1-5)
# - Building type (column 2: building type index 1-10)
# - End use (column 3: heating=1, cooling=2)
# - Floor area (column 4: weighted floor area for this combination)
# - Thermal load components (columns 5-16: 12 different load components)
com_comp_names <- (read.csv('Com_TLoads_Base.csv',header=TRUE))
header = names(com_comp_names)  # Store column names for later use
com_comp <- as.matrix(com_comp_names)  # Convert to matrix for easier processing

# ==============================================================================
# PROCESSING PARAMETERS
# ==============================================================================
# Define the dimensions of the data processing:
cmax = 5        # Number of AIA climate zones (1-5)
cdivmax = 9     # Number of US census divisions (1-9)
bldgmax = 10    # Number of building types in base data (1-10)
                # Note: Building type 1 (Assembly) is derived later
eusemax = 2     # Number of end uses (1=heating, 2=cooling)

# Initialize counter for tracking position in output matrix
counter = 1

# ==============================================================================
# PHASE 1: PROCESS BUILDING TYPES 2-10 (SKIP TYPE 1 - ASSEMBLY)
# ==============================================================================
# Create matrix to store final weighted thermal load components
# Rows: cmax * (bldgmax-1) * eusemax = 5 * 9 * 2 = 90 combinations
# Columns: 16 total (3 for indices + 1 for area + 12 for thermal load components)
finalmat = matrix(NA,cmax*(bldgmax-1)*eusemax,16)

# Process each combination of building type (2-10), climate zone (1-5), and end use (1-2)
# Building type 1 (Assembly) is skipped here and will be derived later as an average
for (b in 2:bldgmax){      # Building types 2-10
  for (c in 1:cmax){       # Climate zones 1-5    
    for (e in 1:eusemax){  # End uses 1-2 (heating/cooling)
    
      # Filter data for current combination of climate zone, building type, and end use
      filtermat = com_comp[((com_comp[,1]==c)&(com_comp[,2]==b)&(com_comp[,3]==e)),]
      
      # Calculate total floor area for this combination (for weighting)
      areasum = sum(filtermat[,4])
      
      # Initialize matrix to store individual row weights
      rowweights = matrix(NA,nrow(filtermat),1)
      
      # Store the identifying indices and total area in final matrix
      finalmat[counter,1:3] = c(c,b,e)  # Climate zone, building type, end use
      finalmat[counter,4] = areasum      # Total floor area
      
      # Initialize matrix to store weighted thermal load components
      rowadd1 = matrix(NA,nrow(filtermat),12)
      
      # Calculate area-weighted thermal load components
      for (r in 1:nrow(filtermat)){
        # Weight = individual area / total area for this combination
        rowweights[r] = filtermat[r,4]/areasum
        
        # Apply weight to thermal load components (columns 5-16 in original data)
        rowadd1[r,] = rowweights[r] * filtermat[r,5:(ncol(filtermat)-1)]
      }
    
      # Sum weighted components across all rows for this combination
      rowadd2 = colSums(rowadd1)
      
      # Normalize so components sum to 1.0 (convert to fractions)
      rowaddfin = rowadd2/sum(rowadd2)      
      
      # Store normalized thermal load fractions in final matrix (rounded to 4 decimals)
      finalmat[counter,5:ncol(finalmat)] = round(rowaddfin,4)
    
      # Move to next row in output matrix
      counter = counter + 1
    
    } 
  }  
}

# ==============================================================================
# PHASE 2: CREATE DERIVED BUILDING TYPES (ASSEMBLY AND OTHER)
# ==============================================================================
# Reset counter for processing derived building types
counter = 1

# Create "Assembly" building type (type 1) as area-weighted average of:
# - Education (type 2)
# - Small Office (type 8) 
# - Mercantile/Service (type 9)
# This represents buildings like theaters, auditoriums, convention centers
assemblymat_base = finalmat[((finalmat[,2]==2)|(finalmat[,2]==8)|(finalmat[,2]==9)),]
assemblymat_fin = matrix(NA,10,ncol(finalmat))  # 5 climate zones * 2 end uses = 10 rows

# Create "Other" building type (type 11) as area-weighted average of:
# - Lodging (type 6)
# - Large Office (type 7)
# - Warehouse (type 10)
# This represents miscellaneous commercial building types not otherwise categorized
othermat_base = finalmat[((finalmat[,2]==6)|(finalmat[,2]==7)|(finalmat[,2]==10)),]
othermat_fin = matrix(NA,10,ncol(finalmat))    # 5 climate zones * 2 end uses = 10 rows

# Process both derived building types
for (b in 1:2){            # b=1: Assembly, b=2: Other
  for (c in 1:cmax){       # Climate zones 1-5
    for (e in 1:eusemax){  # End uses 1-2 (heating/cooling)
      
      # Select appropriate base data depending on which derived type we're creating
      if (b==1){      
        # Processing Assembly building type (average of Education, Sm Office, Merch/Service)
        filtermat = assemblymat_base
        filtermat = filtermat[((filtermat[,1]==c)&(filtermat[,3]==e)),]
      }else{     
        # Reset counter when starting Other building type processing
        if ((c==1)&(e==1)){
        counter = 1
        }
        
        # Processing Other building type (average of Lodging, Lg Office, Warehouse)
        filtermat = othermat_base
        filtermat = filtermat[((filtermat[,1]==c)&(filtermat[,3]==e)),]
      }
      
      # Calculate area-weighted average thermal load components
      # Same methodology as Phase 1, but averaging across the 3 contributing building types
      areasum = sum(filtermat[,4])  # Total area across contributing building types
      rowweights = matrix(NA,nrow(filtermat),1)
      rowadd1 = matrix(NA,nrow(filtermat),12)
      
      # Weight each contributing building type by its relative area
      for (r in 1:nrow(filtermat)){
        rowweights[r] = filtermat[r,4]/areasum
        rowadd1[r,] = rowweights[r] * filtermat[r,5:(ncol(filtermat))]
      }
      
      # Sum weighted components and normalize to fractions
      rowadd2 = colSums(rowadd1)
      rowaddfin = rowadd2/sum(rowadd2)      
      
      # Store results in appropriate output matrix
      if (b==1){      
        # Assembly building type gets index 1
        assemblymat_fin[counter,1:3] = c(c,1,e)
        assemblymat_fin[counter,5:ncol(finalmat)] = round(rowaddfin,4)   
      }else{     
        # Other building type gets index 11
        othermat_fin[counter,1:3] = c(c,11,e)
        othermat_fin[counter,5:ncol(finalmat)] = round(rowaddfin,4)
      }
      counter = counter + 1      
  } 
} 
}

# Combine all building types into final matrix:
# - Assembly (type 1) - derived
# - Building types 2-10 - from original data  
# - Other (type 11) - derived
# Final order: Assembly, then types 2-10, then Other
finalmat <- rbind(assemblymat_fin,finalmat,othermat_fin)

# ==============================================================================
# PHASE 3: CONVERT FROM CLIMATE ZONES TO CENSUS DIVISIONS
# ==============================================================================
# The data is currently organized by AIA climate zones (1-5), but the Scout model
# needs data organized by US Census divisions (1-9). This section converts between
# the two geographic systems using floor area weights from CBECS survey data.

# Load 2003 CBECS (Commercial Buildings Energy Consumption Survey) raw data
# This provides the statistical relationship between climate zones and census divisions
cbecs <- read.csv('2003_CBECS_RawData.csv',header=TRUE)

# Extract relevant columns for the conversion:
# CENDIV8: Census division (1-9)
# CLIMATE8: Climate zone (1-5) 
# SQFT8: Building square footage
# ADJWT8: Statistical weight for survey sample
cdivision<-cbecs$CENDIV8
climzone<-cbecs$CLIMATE8
sqfeet<-cbecs$SQFT8*cbecs$ADJWT8  # Weighted square footage

# Create cross-tabulation table: Census divisions (rows) vs Climate zones (columns)
# Each cell contains total weighted floor area for that division/zone combination
conversion_table<-tapply(sqfeet,list(cdivision,climzone),sum)

# Replace NA values with 0 (represents combinations that don't exist)
conversion_table[is.na(conversion_table)]<-0

# Remove column 6+ representing buildings over 1 million sq ft (no assigned climate zone)
conversion_table<-conversion_table[,1:5]

# Convert absolute areas to fractions within each census division
# Each row will sum to 1.0, showing the climate zone distribution within that division
conversion_table_frac<-matrix(NA,nrow(conversion_table),ncol(conversion_table))

for (r in 1:(nrow(conversion_table))){
  # Calculate fraction: area in each climate zone / total area in this census division
  conversion_table_frac[r,]=round((conversion_table[r,]/sum(conversion_table[r,],na.rm=TRUE)),5)
}

# ==============================================================================
# PHASE 4: APPLY CONVERSION TO CREATE CENSUS DIVISION-BASED DATA
# ==============================================================================
# Create new matrix organized by census divisions instead of climate zones
# Size: cdivmax * (bldgmax+1) * eusemax = 9 * 11 * 2 = 198 combinations
finalmat_converted = matrix(NA,cdivmax*(bldgmax+1)*eusemax,ncol(finalmat))

# Calculate rows per census division (all building types * all end uses)
rowlength = eusemax*11 # End uses (2) times number of commercial building types (11)
rowstart = 0

# Process each census division
for (cd in 1:cdivmax){  
  
  # Calculate row indices for this census division's data
  rowend = rowstart + rowlength
  
  # Set census division index for all rows belonging to this division
  finalmat_converted[((rowstart+1):rowend),1] = rep(cd,rowlength)
  
  # Initialize matrix to store climate-zone-weighted results
  weighted_mat = matrix(NA,rowlength,(ncol(finalmat)-1))
  counter = 1
  
  # Process each building type and end use combination within this census division
  for (b in 1:(bldgmax+1)){  # All 11 building types (1,2-10,11)
    for (e in 1:eusemax){    # Both end uses (heating, cooling)
      
      # Get thermal load data for this building type and end use across all climate zones
      filtermat2 = finalmat[((finalmat[,2]==b)&(finalmat[,3]==e)),]
      
      # Get climate zone weights for this census division
      weights = conversion_table_frac[cd,]
      
      # Calculate weighted average thermal loads across climate zones
      # This gives us the thermal loads for this building/end use in this census division
      tloads_weighted = weights %*% filtermat2[,4:ncol(filtermat2)]    
      
      # Store building type, end use, weighted area, and weighted thermal load fractions
      weighted_mat[counter,] = c(filtermat2[1,2:3],  # Building type and end use (same across climate zones)
                                tloads_weighted[1],   # Total weighted area
                                round(tloads_weighted[2:length(tloads_weighted)],4))  # Thermal load fractions
      counter = counter + 1
    } 
  }
  
  # Store weighted results for this census division
  finalmat_converted[((rowstart+1):rowend),2:ncol(finalmat_converted)] = weighted_mat
  
  # Move to next census division
  rowstart = rowend 
}


# ==============================================================================
# PHASE 5: OUTPUT PROCESSED DATA FILES
# ==============================================================================

# Write out the main processed thermal loads data file
# This contains thermal load fractions organized by census division, building type, and end use
colnames(finalmat_converted)<-c('CDIV',header[2:(length(header)-1)])
write.table(finalmat_converted,'Com_TLoads_PrepFinal.txt', row.names=FALSE)

# Write out the census division to climate zone conversion table
# This shows what fraction of each census division's floor area falls in each climate zone
# Used for converting climate-zone-based data to census-division-based data
conversion_table_frac = cbind(seq(1,9,by=1),conversion_table_frac)
colnames(conversion_table_frac) = c('CDIV','AIA_CZ1','AIA_CZ2','AIA_CZ3','AIA_CZ4','AIA_CZ5')
write.table(conversion_table_frac,'Com_Cdiv_Czone_ConvertTablePrep.txt',row.names=FALSE)

# Create and write out the reverse conversion table
# This shows what fraction of each climate zone's floor area falls in each census division
# Used for converting census-division-based data back to climate-zone-based data
conversion_table_frac_rev<-matrix(NA,nrow(conversion_table),ncol(conversion_table))

for (r in 1:(nrow(conversion_table))){
  # Calculate fraction: area in this census division / total area in each climate zone
  conversion_table_frac_rev[r,]=round((conversion_table[r,]/colSums(conversion_table)),5)
}

# Write out reversed conversion table with appropriate column names
conversion_table_frac_rev = cbind(seq(1,9,by=1),conversion_table_frac_rev)
colnames(conversion_table_frac_rev) = c('CDIV','AIA_CZ1','AIA_CZ2','AIA_CZ3','AIA_CZ4','AIA_CZ5')
write.table(conversion_table_frac_rev,'Com_Cdiv_Czone_ConvertTablePrep_Rev.txt',row.names=FALSE)

# ==============================================================================
# PROCESSING COMPLETE
# ==============================================================================
# Summary of outputs:
# 1. Com_TLoads_PrepFinal.txt - Main thermal loads data by census division
# 2. Com_Cdiv_Czone_ConvertTablePrep.txt - Forward conversion factors
# 3. Com_Cdiv_Czone_ConvertTablePrep_Rev.txt - Reverse conversion factors
#
# The thermal loads data is now ready for use in the Scout building energy model
# which operates on census division geography rather than climate zones.
# ==============================================================================








