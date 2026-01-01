#!/usr/bin/env python3
"""
Federal Reserve Financial Conditions Index (FCI-G) Calculator

This script calculates the FCI-G index based on quarterly differences of
seven key financial variables, weighted according to the methodology described
in Ajello et al. (2023).

The script processes data at monthly or daily frequency and generates both
3-year and 1-year FCI indices with decomposition by component.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime
from multiprocessing import Pool, cpu_count
from functools import partial
import warnings

# Import utility functions
from utility_functions import (
    prepare_inputs, check_input, history, makeQuarterly
)


def calculate_fci_for_row(i, input_data, multipliers):
    """
    Calculate FCI for a single row (date).

    Parameters:
    -----------
    i : int
        Row index
    input_data : pd.DataFrame
        Input data with dates and financial variables
    multipliers : pd.DataFrame
        Multiplier weights for each variable

    Returns:
    --------
    dict
        Dictionary containing date and calculated values
    """
    # Creates dataframe of lagged dates data
    hist = history(i, input_data)

    # Get the data columns (excluding date and V1-V8 columns)
    data_cols = [col for col in hist.columns if col not in ['date', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8']]

    # Multiplies all the data by the corresponding multiplier, then adds the rows (the lagged dates) up
    threeyear = (hist.iloc[0:12][data_cols] * multipliers.iloc[0:12].values).sum()

    # Multiplies just the 4 most recent lagged dates
    oneyear = (hist.iloc[0:4][data_cols] * multipliers.iloc[0:4].values).sum()

    # Combines all the data into one row
    result = {'date': input_data.iloc[i]['date']}

    # Add three-year values
    for idx, col in enumerate(data_cols):
        result[f'threeyear_{col}'] = threeyear.iloc[idx]

    # Add one-year values
    for idx, col in enumerate(data_cols):
        result[f'oneyear_{col}'] = oneyear.iloc[idx]

    return result


def main():
    """
    Main function to calculate FCI-G index.
    """
    # Change to the script directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    # Configuration
    quarterly = False  # Set to True if you would like a quarterly version of the FCI-G

    # Read input data
    print("Reading input data...")
    input_data = pd.read_csv("input_data.csv")

    # Check input data
    check_input(input_data)

    # Prepare inputs
    print("Preparing inputs...")
    input_results = prepare_inputs(input_data)
    input_data = input_results['V1']

    # Read multipliers
    multipliers = pd.read_csv("multipliers.csv", index_col=0)

    # Calculate FCI using parallel processing
    print("Calculating FCI (this may take a few minutes)...")

    # Determine date range
    min_date = input_data['date'].min()
    firstdate = input_data[input_data['date'] >= (min_date + pd.DateOffset(years=3))]['date'].min()
    first_idx = input_data[input_data['date'] == firstdate].index[0]

    # Create list of indices to process
    indices = list(range(len(input_data)-1, first_idx-1, -1))

    # Use multiprocessing to speed up calculation
    num_cores = min(4, cpu_count())  # Use up to 4 cores

    with Pool(num_cores) as pool:
        results = pool.map(
            partial(calculate_fci_for_row, input_data=input_data, multipliers=multipliers),
            indices
        )

    # Convert results to DataFrame
    FCI_decomp = pd.DataFrame(results)

    # Reverse the row order (results are in reverse chronological order)
    FCI_decomp = FCI_decomp.iloc[::-1].reset_index(drop=True)

    # Extract column names
    data_cols = [col for col in input_data.columns if col not in ['date', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6', 'V7', 'V8']]

    # Create output decomposition
    output_decomp = FCI_decomp[FCI_decomp['date'] >= pd.Timestamp('1990-01-01')].copy()

    # Multiply by -1 (sign convention)
    threeyear_cols = [f'threeyear_{col}' for col in data_cols]
    oneyear_cols = [f'oneyear_{col}' for col in data_cols]
    output_decomp[threeyear_cols + oneyear_cols] = -1 * output_decomp[threeyear_cols + oneyear_cols]

    # Calculate FCI values (sum of components)
    FCI_daily = pd.DataFrame({
        'date': FCI_decomp['date'],
        'fci3val': -1 * FCI_decomp[threeyear_cols].sum(axis=1),
        'fci1val': -1 * FCI_decomp[oneyear_cols].sum(axis=1)
    })
    FCI_daily = FCI_daily[FCI_daily['date'] >= pd.Timestamp('1990-01-01')].reset_index(drop=True)

    # Rename columns for output
    rename_map = {}
    for i, col in enumerate(data_cols):
        rename_map[f'threeyear_{col}'] = col
        rename_map[f'oneyear_{col}'] = col

    # Create three-year FCI output
    threeyearFCI_output = pd.merge(
        FCI_daily[['date', 'fci3val']],
        output_decomp[['date'] + threeyear_cols].rename(columns=rename_map),
        on='date'
    )

    # Create one-year FCI output
    oneyearFCI_output = pd.merge(
        FCI_daily[['date', 'fci1val']],
        output_decomp[['date'] + oneyear_cols].rename(columns=rename_map),
        on='date'
    )

    # Restore original dates if they were stored
    if input_results['V2']:
        final_dates = pd.DataFrame({'date': input_results['V3']})
        final_dates = final_dates[final_dates['date'] >= pd.Timestamp('1990-01-01')].reset_index(drop=True)
        threeyearFCI_output['date'] = final_dates['date'].iloc[:len(threeyearFCI_output)]
        oneyearFCI_output['date'] = final_dates['date'].iloc[:len(oneyearFCI_output)]

    # Write output files
    print("Writing output files...")
    threeyearFCI_output.to_csv("threeyearFCI_output.csv", index=False)
    oneyearFCI_output.to_csv("oneyearFCI_output.csv", index=False)
    print("  - threeyearFCI_output.csv")
    print("  - oneyearFCI_output.csv")

    # Generate quarterly versions if requested
    if quarterly:
        print("Generating quarterly versions...")
        threeyearFCI_output_quarterly = makeQuarterly(threeyearFCI_output)
        oneyearFCI_output_quarterly = makeQuarterly(oneyearFCI_output)
        threeyearFCI_output_quarterly.to_csv("threeyearFCI_output_quarterly.csv", index=False)
        oneyearFCI_output_quarterly.to_csv("oneyearFCI_output_quarterly.csv", index=False)
        print("  - threeyearFCI_output_quarterly.csv")
        print("  - oneyearFCI_output_quarterly.csv")

    print("\nFCI calculation complete!")


if __name__ == "__main__":
    main()
