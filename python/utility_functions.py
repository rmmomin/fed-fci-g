"""
Utility functions for FCI-G (Financial Conditions Index) calculation.

This module provides helper functions for processing financial data,
generating linked lists for date lookups, and converting between
monthly and quarterly frequencies.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import warnings


def prepare_inputs(delta_data):
    """
    Setup function that adds linked list pointers to input data to improve FCI-G calculation speed.

    Parameters:
    -----------
    delta_data : pd.DataFrame
        A dataframe containing all of the dates and data

    Returns:
    --------
    dict
        Dictionary with:
        - 'V1': Processed dataframe with linked list pointers
        - 'V2': Boolean indicator for if dates have been saved
        - 'V3': Original dates (if monthly data)
    """
    # Parse dates
    delta_data = delta_data.copy()

    # Try to detect date format
    first_date = str(delta_data['date'].iloc[0])
    if '/' in first_date:
        delta_data['date'] = pd.to_datetime(delta_data['date'], format='%m/%d/%Y')
    else:
        delta_data['date'] = pd.to_datetime(delta_data['date'])

    date_stored = None
    stored = False

    # Check if data is monthly
    month_diffs = delta_data['date'].diff().dt.days
    is_monthly = all((month_diffs[1:] >= 28) & (month_diffs[1:] <= 31))

    if is_monthly:
        # If it's monthly, convert dates to the last day of the month
        date_stored = delta_data['date'].copy()
        stored = True
        delta_data['date'] = delta_data['date'] + pd.offsets.MonthEnd(0)

    # Prepare date table structure
    if len(delta_data.columns) != 16:
        dates = pd.DataFrame({
            'date': delta_data['date'],
            'V1': np.nan, 'V2': np.nan, 'V3': np.nan, 'V4': np.nan,
            'V5': np.nan, 'V6': np.nan, 'V7': np.nan, 'V8': np.nan
        })
    else:
        dates = delta_data.iloc[:, :9].copy()
        dates.columns = ['date', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8']
        delta_data = delta_data.iloc[:, [0] + list(range(9, 16))].copy()

    # Generate linked lists
    dates = generatelists(dates)

    # Merge back with original data
    delta_data = dates.merge(delta_data, on='date', how='left')

    return {
        'V1': delta_data,
        'V2': stored,
        'V3': date_stored
    }


def check_input(input_df):
    """
    Checks to make sure the input_data has been changed correctly.

    Parameters:
    -----------
    input_df : pd.DataFrame
        Input dataframe to validate

    Raises:
    -------
    ValueError
        If NA values are found in the input
    """
    if input_df.isna().any().any():
        warnings.warn("ATTENTION: Please use the empty sample data file provided to build your dataset, "
                     "according to the technical appendix of the FEDS Note (Ajello et al., 2023)")
        raise ValueError("NA value found")


def history(i, delta_data):
    """
    Gives the time components used to calculate the FCI-G for a given date.
    Can be used to quickly generate the time decomposition of the FCI-G for a given date.

    Parameters:
    -----------
    i : int
        The row index of the date you want to find the FCI-G for
    delta_data : pd.DataFrame
        Dataframe with dates and linked list pointers

    Returns:
    --------
    pd.DataFrame
        A 13x8 dataframe that contains the component's data at each of the lag periods
    """
    oldindex = i
    j = 1
    count = 0
    endofm = False

    if check_EndOfM(delta_data, i):
        endofm = True
        j = 8

    dayt = delta_data.iloc[i]['date'].day

    # Start with current row, excluding linked list columns (V1-V8)
    hist = delta_data.iloc[[i]].drop(columns=['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8'])

    while count < 12:
        count += 1
        index = int(delta_data.iloc[oldindex][f'V{j}'])
        hist = pd.concat([hist, delta_data.iloc[[index]].drop(columns=['V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8'])],
                        ignore_index=True)
        oldindex = index
        j = dayt - delta_data.iloc[index]['date'].day + 1

        if endofm:
            j = 8
        elif abs(j) > 9:
            j = j + 31

    return hist


def threemonthdate(date_table, date, j, endofm, dayt):
    """
    Critical function for the generatelists function.
    Finds the closest date at or before the date three months before the input date.

    Parameters:
    -----------
    date_table : pd.DataFrame
        A dataframe containing all of the dates and their linked list nodes
    date : datetime
        The input date from which we want to find the date 3 months prior
    j : int
        How many days we are currently shifted from the day we are searching for
    endofm : bool
        Boolean indicator for if we are searching for end of month dates
    dayt : int
        The integer of the day we are looking up

    Returns:
    --------
    int
        Row index of the found date
    """
    if endofm:
        # Date we want to find date closest to
        first_of_month = date.replace(day=1)
        searchdate = first_of_month - relativedelta(months=2) - timedelta(days=1)
        # Actually found date
        threedate = date_table[date_table['date'] <= searchdate]['date'].max()
    else:
        adjusted_date = date + timedelta(days=j-1)
        first_of_adjusted = adjusted_date.replace(day=1)
        searchdate = (first_of_adjusted + timedelta(days=dayt-1)) - relativedelta(months=3)

        month_diff = (date.month - searchdate.month) % 12
        if month_diff == 2 and dayt > 15:
            searchdate = searchdate - relativedelta(months=1)

        threedate = date_table[date_table['date'] <= searchdate]['date'].max()

    return date_table[date_table['date'] == threedate].index[0]


def check_EndOfM(date_table, i):
    """
    Function that checks if a date is the end of month.

    Parameters:
    -----------
    date_table : pd.DataFrame
        A dataframe containing all of the dates
    i : int
        Row index of date to be checked

    Returns:
    --------
    bool
        True if date is end of month, false otherwise
    """
    current_date = date_table.iloc[i]['date']

    if i == len(date_table) - 1:
        # Check if adding one day changes the month
        next_day = current_date + timedelta(days=1)
    else:
        next_day = date_table.iloc[i+1]['date']

    month_diff = (next_day.month - current_date.month) % 12
    if month_diff in [1, -11]:
        return True

    return False


def generatelists(date_table):
    """
    Function that generates linked lists for the FCI-G dates.

    Parameters:
    -----------
    date_table : pd.DataFrame
        A dataframe containing all of the dates

    Returns:
    --------
    pd.DataFrame
        Same dataframe containing all of the dates now with their linked list nodes
    """
    date_table = date_table.copy()

    # Find the row with most recent date without a node
    na_indices = date_table[date_table['V1'].isna()].index
    if len(na_indices) == 0:
        return date_table

    i = na_indices[-1]
    j = 1
    endofm = False

    if check_EndOfM(date_table, i):
        endofm = True
        j = 8
        date_table.at[i, 'V1'] = 0

    min_date_plus_3m = date_table['date'].min() + relativedelta(months=3)
    if date_table.iloc[i]['date'] < min_date_plus_3m:
        return date_table

    dayt = date_table.iloc[i]['date'].day

    while i is not None:
        # Find the index of date three months before
        index = threemonthdate(date_table, date_table.iloc[i]['date'], j, endofm, dayt)

        # Store the index of the 3 month before date
        date_table.at[i, f'V{j}'] = index

        # Calculate shift
        j = dayt - date_table.iloc[index]['date'].day + 1

        if endofm:
            j = 8
        elif abs(j) > 9:
            j = j + 31

        # Check if we reached the end of linked list
        if date_table.iloc[index]['date'] < min_date_plus_3m:
            # Instantiate all variables for another round
            na_indices = date_table[date_table['V1'].isna()].index
            if len(na_indices) == 0:
                return date_table

            i = na_indices[-1]
            j = 1
            endofm = False

            if check_EndOfM(date_table, i):
                endofm = True
                j = 8
                date_table.at[i, 'V1'] = 0

            dayt = date_table.iloc[i]['date'].day

            if date_table.iloc[i]['date'] < min_date_plus_3m:
                return date_table
        else:
            # Continue down the list
            i = index

    return date_table


def makeQuarterly(monthly_data):
    """
    Function to turn monthly indices into quarterly indices.

    Parameters:
    -----------
    monthly_data : pd.DataFrame
        A dataframe containing data in monthly frequency. There must be a 'date' column

    Returns:
    --------
    pd.DataFrame
        A dataframe containing input data in quarterly frequency
    """
    quarterly_data = monthly_data.copy()
    quarterly_data['Quarter'] = pd.PeriodIndex(quarterly_data['date'], freq='Q')
    quarterly_data = quarterly_data.groupby('Quarter').tail(1).drop(columns=['Quarter'])
    quarterly_data = quarterly_data.reset_index(drop=True)

    return quarterly_data
