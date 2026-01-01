#!/usr/bin/env python3
"""
Plot Real GDP Growth Data

This script reads the Real GDP Growth (Q/Q annualized) data and creates
a time series visualization.

Usage:
    python plot_gdp_data.py
"""

import os
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


# Configuration
INPUT_FILENAME = "real_gdp_growth_qoq_annualized.csv"
OUTPUT_FILENAME = "real_gdp_growth_qoq_annualized.png"


def read_data(filepath):
    """Read GDP data from CSV file."""
    dates = []
    values = []

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row['real_gdp_growth_qoq_annualized'] != '.':
                dates.append(datetime.strptime(row['date'], '%Y-%m-%d'))
                values.append(float(row['real_gdp_growth_qoq_annualized']))

    return dates, values


def main():
    """Main function to plot GDP data."""
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    input_path = os.path.join(repo_root, 'data', INPUT_FILENAME)
    output_path = os.path.join(repo_root, 'figures', OUTPUT_FILENAME)

    # Read data
    print(f"Reading data from {input_path}...")
    dates, values = read_data(input_path)

    # Create figure
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot data
    ax.plot(dates, values, color='#1f77b4', linewidth=0.8)

    # Add zero line
    ax.axhline(y=0, color='black', linewidth=0.5, linestyle='-')

    # Fill positive/negative areas
    ax.fill_between(dates, values, 0,
                    where=[v >= 0 for v in values],
                    color='#2ecc71', alpha=0.3, label='Positive Growth')
    ax.fill_between(dates, values, 0,
                    where=[v < 0 for v in values],
                    color='#e74c3c', alpha=0.3, label='Negative Growth')

    # Formatting
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Percent Change (Annualized)', fontsize=11)
    ax.set_title('Real GDP Growth (Quarter-over-Quarter, Annualized)', fontsize=14)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator(10))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.YearLocator(5))

    # Grid and legend
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right')

    # Add data source
    ax.text(0.01, 0.02, 'Source: FRED (A191RL1Q225SBEA)',
            transform=ax.transAxes, fontsize=8, color='gray')

    plt.tight_layout()

    # Save figure
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved figure to {output_path}")

    # Print summary stats
    print(f"\nData Summary:")
    print(f"  Date range: {dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}")
    print(f"  Observations: {len(values)}")
    print(f"  Mean: {sum(values) / len(values):.2f}%")
    print(f"  Min: {min(values):.2f}%")
    print(f"  Max: {max(values):.2f}%")


if __name__ == "__main__":
    main()
