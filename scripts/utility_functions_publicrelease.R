#Setup function that adds linked list pointers to input data to improve fci-g calculation speed
prepare_inputs = function(delta_data){
  #######################################
  # Inputs:
  # delta_data (dataframe) - A dataframe containing all of the dates and data
  ########################################
  # Outputs:
  # delta_data (dataframe) - A dataframe containing all of the dates and data
  # stored (boolean) - Indicator for if dates have been saved. 
  # date_stored (dataframe) - A dataframe containing all of the true dates of the data to be appended later
  
  
  is_mdy <- grepl("^\\d{1,2}/\\d{1,2}/\\d{4}$", delta_data$date[[1]])
  if(is_mdy){delta_data$date <- mdy(delta_data$date)}
  else{delta_data$date <- as.Date(delta_data$date)}
  date_stored = NULL
  stored = FALSE
  if (all(diff(month(delta_data$date)) %in% c(1,-11))) {
    # If it's monthly, convert dates to the last day of the month
    date_stored <- delta_data$date
    stored = TRUE
    delta_data <- delta_data %>%
      mutate(date = ceiling_date(date, "month") - 1)
  } 
  
  if (ncol(delta_data) != 16) {
    dates <- data.frame("date" = delta_data[, 1])
    df <- data.frame(matrix(NA, ncol=8, nrow=nrow(dates)))
    dates = cbind(dates, df)
    colnames(dates) <- c('date', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8')
  }else{
    dates <- delta_data[, 1:9]
    delta_data <- delta_data[, c(1, 10:16)]
    }
  
  dates <- generatelists(dates)
  delta_data <- dates %>%
    left_join(delta_data, by = "date")
  return(list(V1 = delta_data, V2 = stored, V3 = date_stored))
}

#Checks to make sure the input_data has been changed correctly
check_input <- function(input_df) {
  if (any(is.na(input_df))) {
    warning("ATTENTION: Please use the empty sample data file provided to build your dataset, according to the technical appendix of the FEDS Note (Ajello et al., 2023)")
    stop("NA value found")  # Terminate the R session with an error status
  }
}

#Gives the time components used to calculate the fci-g for a given date .
#Can be used to quickly generate the time decomposition of the fci-g for a given date.
history = function(i, delta_data){
  #######################################
  # Inputs: 
  # i (int) - The row index of the date you want to find the fci-g for  
  ########################################
  # Outputs: 
  # hist (dataframe) -  A 13x8 dataframe that contains the component's data at each of the lag periods
  
  oldindex = i
  j=1
  count = 0
  endofm = FALSE
  if(check_EndOfM(delta_data, i)){
    endofm = TRUE
    j=8
  }
  dayt = day(delta_data[i, 1])
  hist = delta_data[i, -c(2:9)]
  while(count<12){
    count <- count + 1
    index <- delta_data[oldindex, j+1]
    hist <- rbind(hist, delta_data[index, -c(2:9)])
    oldindex <- index
    j = dayt - day(delta_data[index, 1])+1
    if(endofm){
      j=8
    }
    else if(abs(j)>9){
      j = j+31
    }
  }
  return(hist)
}

#Critical function for the generatelists function. Finds the closest date at or before the date three months before the input date
threemonthdate = function(date_table, date, j, endofm, dayt){
  #######################################
  # Inputs:
  # date_table (dataframe) - A dataframe containing all of the dates and their linked list nodes
  # date (Date) - The input date from which we want to find the date 3 months prior
  # j (int) - How many days we are currently shifted from the day we are searching for
  # endofm (bool) - Boolean indicator for if we are searching for end of month dates  
  # dayt (int) - The integer of the day we are looking up   
  ########################################
  # Outputs: 
  # (int) -  Row index of the found date
  
  if(endofm){
    searchdate = ((as.Date(format(date, "%Y-%m-01"))) %m-% months(2) - days(1)) #Date we want to find date closest to
    threedate = max(date_table$date[date_table$date <= searchdate]) #Actually found date. Just the latest date of all dates before or at the search date. 
  }
  else{
    searchdate = ((as.Date(format((date + days(j-1)), "%Y-%m-01"))+days(dayt-1)) %m-% months(3))
    if((month(date)-month(searchdate))%%12==2 && dayt >15){
      searchdate <- searchdate %m-% months(1)
    }
    threedate = max(date_table$date[date_table$date <= searchdate])
  }
  return(which(date_table[,1]==threedate))
}

#Function for the generatelists function that finds the next business day from the given date. 
check_EndOfM <- function(date_table, i) {
  #######################################
  # Inputs:
  # date_table (dataframe) - A dataframe containing all of the dates
  # i (int) - Row index of date to be checked
  ########################################
  # Outputs:
  # (boolean) - True if date is end of month, false otherwise
  
  current_date <- as.timeDate(date_table[i, 1])
  if(i == nrow(date_table)){
    next_business_day <- current_date + days(1)
    while (!isBizday(next_business_day, holidays = holidayNYSE(), wday = 1:5)) {
      next_business_day <- next_business_day + days(1)
    }
  }else{
    next_business_day <- date_table[i+1, 1]
  }
  if((month(next_business_day)-month(current_date)) %in% c(1,-11)){ 
    return(TRUE)
  }
  return(FALSE)
}

#Function that generates linked lists for the fci-g dates. 
generatelists = function(date_table){
  #######################################
  # Inputs:
  # date_table (dataframe) - A dataframe containing all of the dates
  ########################################
  # Outputs:
  # date_table (dataframe) - Same dataframe containing all of the dates now with their linked list nodes

  i <- tail(which(is.na(date_table$V1)), 1) #Finds the row with most recent date without a node
  j=1 
  endofm = FALSE
  if(check_EndOfM(date_table, i)){ #Check if the date is the end of the month by seeing if month changes by subtracting a day. 
    endofm = TRUE
    j=8 
    date_table[i, 2] = 0
  }
  if(date_table[i, 1] < min(date_table$date) %m+% months(3)){return(date_table)}
  dayt = day(date_table[i, 1])
  while(!is.null(i)){
    index = threemonthdate(date_table, date_table[i,1], j, endofm, dayt) #finds the index of date three months before
    date_table[i, j+1] = index #Stores the index of the 3 month before date into one of the adress columns of the current date
    j = dayt - day(date_table[index, 1])+1 #calculate shift
    if(endofm){
      j=8
    }
    else if(abs(j)>9){
      j = j+31 #If we search for the start of the month and find the closest date is the end of the previous month, we add 31 (number of days in biggest month) to correct the sift. 
    }
    if (date_table[index, 1] < min(date_table$date) %m+% months(3)){ #Check if we reached the end of linked list
      #Instantiate all variables for another round
      i = tail(which(is.na(date_table$V1)), 1)
      j=1
      endofm = FALSE
      if(check_EndOfM(date_table, i)){
        endofm = TRUE
        j=8
        date_table[i, 2] = 0
      }
      dayt = day(date_table[i, 1])
      if(date_table[i, 1] < min(date_table$date) %m+% months(3)){return(date_table)}
    }
    else{ #continue down the list
      i = index
    }
  }
}

#Function to turn monthly indices into quarterly indices
makeQuarterly = function(monthly_data){
  #######################################
  # Inputs:
  # monthly_data (dataframe) - A dataframe containing data in monthly frequency. There must be a 'date' column
  ########################################
  # Outputs:
  # quarterly_data (dataframe) - A dataframe containing input data in quarterly frequency
  
  quarterly_data = monthly_data %>% 
    mutate(Quarter = zoo::as.yearqtr(date)) %>%  # Create a quarter column
    group_by(Quarter)  %>%  # Group by quarter
    slice(n()) %>%
    ungroup() %>%
    select(-Quarter)
  return(quarterly_data)
}