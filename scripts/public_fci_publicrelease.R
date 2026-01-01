#install.packages("doParallel","lubridate","tidyverse","foreach", "timeDate")
setwd(dirname(rstudioapi::getActiveDocumentContext()$path)) #Assumes Rstudio is being used. If not or if there is a bug, comment out this line and uncomment the next line
#setwd("Path") #Replace path with file directory of scripts. 
library(doParallel)
library(lubridate)
library(tidyverse)
library(foreach)
library(timeDate)
source("utility_functions_publicrelease.R")

quarterly = FALSE #Indicator to generate a quarterly index. Set to TRUE if you would like a quarterly version of the FCI-G

#A sample data file is provided with sample dates (first column), variable names in code-compatible order (first row), and blank entries.
#Each data cell should include quarterly (3-month) differences of drivers, as described in the Technical Appendix of Feds Note (Ajello et al, 2023)
#Code can process data at monthly or daily frequency.
input_data <-  read.csv(file = "input_data.csv") 
check_input(input_data)
input_results <- prepare_inputs(input_data) 
input_data <- input_results$V1 #Dataframe can be saved and appended to to improve future calculation speed
multipliers <- read.csv(file = "multipliers.csv") # A 20x7 dataframe. Each column is a different input variables weights, the rows correspond to progressively older quarters

cl <- makeCluster(4)
registerDoParallel(cl)
FCI_decomp <- data.frame(matrix(NA, nrow = 0, ncol = 15))
firstdate <- min(input_data$date[input_data$date >= (input_data$date[1] + years(3))])

results <- foreach(i = nrow(input_data):which(input_data$date == firstdate), .packages = c("lubridate", "timeDate")) %dopar% {
  hist = history(i, input_data) #Creates dataframe of lagged dates data
  
  threeyear = data.frame(colSums(hist[1:12, 2:8]*multipliers[1:12, ])) #Multiplies all the data by the corresponding multiplier, then adds the rows (the lagged dates) up
  oneyear = data.frame(colSums(hist[1:4, 2:8]*multipliers[1:4, ])) #Multiplies just the 4 most recent lagged dates
  irow = data.frame(date = input_data[i,1], t(as.matrix(threeyear)), t(as.matrix(oneyear))) #Combines all the data into one row
  
  return(irow)
}
FCI_decomp <- do.call(rbind, results)
stopCluster(cl)

# Reverse the row order
FCI_decomp <- FCI_decomp[nrow(FCI_decomp):1, ]

# Rename the row names to just the row number
rownames(FCI_decomp) <- 1:nrow(FCI_decomp)

FCI_decomp$date <- as.Date(FCI_decomp$date,origin='1970-01-01')
output_decomp = FCI_decomp %>% filter(date >= as.Date('1990-01-01')) %>% select(1:15)
output_decomp[,2:15] = -1*output_decomp[,2:15]
names(output_decomp) = c("date","ffr","t10yr","mortrate","bbbrate","stockmkt","houseprices","dollarval","ffr1yr","t10yr1yr","mortrate","bbbrate","stockmkt","houseprices","dollarval")

FCI_daily <- data.frame(FCI_decomp$date,rowSums(FCI_decomp[,2:8]),rowSums(FCI_decomp[,9:15]))
colnames(FCI_daily) <- c("date","fci3val","fci1val")
FCI_daily = FCI_daily %>% filter(date >= as.Date("1990-01-01"))
FCI_daily[,2:3] = -1*FCI_daily[,2:3]

threeyearFCI_output = full_join(FCI_daily[, 1:2],output_decomp[,1:8],by='date')
oneyearFCI_output = full_join(FCI_daily[, c(1,3)],output_decomp[,c(1, 9:15)],by='date')

if(input_results$V2){
  final_dates <- data.frame(date = input_results$V3) %>% filter(date >= as.Date("1990-01-01"))
  threeyearFCI_output[, 1] <- head(final_dates, nrow(threeyearFCI_output))
  oneyearFCI_output[, 1] <- head(final_dates, nrow(oneyearFCI_output))
}
write.csv(threeyearFCI_output, file = "threeyearFCI_output.csv", row.names = FALSE)
write.csv(oneyearFCI_output, file = "oneyearFCI_output.csv", row.names = FALSE)
rmlist <- c("threeyearFCI_output", "oneyearFCI_output")
if(quarterly){
  threeyearFCI_output_quarterly <- makeQuarterly(threeyearFCI_output)
  oneyearFCI_output_quarterly <- makeQuarterly(oneyearFCI_output)
  write.csv(threeyearFCI_output_quarterly, file = "threeyearFCI_output_quarterly.csv", row.names = FALSE)
  write.csv(oneyearFCI_output_quarterly, file = "oneyearFCI_output_quarterly.csv", row.names = FALSE)
  rmlist <- c(rmlist, "threeyearFCI_output_quarterly", "oneyearFCI_output_quarterly")
}
rm(list=setdiff(ls(), rmlist))

