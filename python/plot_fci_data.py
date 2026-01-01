#!/usr/bin/env python3
"""
Plot FCI-G (Financial Conditions Index - Growth) Data

This script creates visualizations of the FCI-G index including:
1. Main FCI-G index (1-year and 3-year lookback)
2. Component decomposition

Usage:
    python plot_fci_data.py
"""

import os
import csv
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def read_fci_data(filepath):
    """Read FCI data from CSV file."""
    data = {'date': [], 'fci': [], 'ffr': [], 'treasury_10yr': [],
            'mortgage': [], 'bbb': [], 'stock_market': [],
            'house_prices': [], 'dollar': []}

    with open(filepath, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        # Find the FCI column (varies between files)
        fci_col = [h for h in headers if 'FCI-G' in h][0]

        for row in reader:
            data['date'].append(datetime.strptime(row['date'], '%Y-%m-%d'))
            data['fci'].append(float(row[fci_col]))
            data['ffr'].append(float(row['FFR']))
            data['treasury_10yr'].append(float(row['10Yr Treasury']))
            data['mortgage'].append(float(row['Mortgage Rate']))
            data['bbb'].append(float(row['BBB']))
            data['stock_market'].append(float(row['Stock Market']))
            data['house_prices'].append(float(row['House Prices']))
            data['dollar'].append(float(row['Dollar']))

    return data


def plot_fci_index(data_1yr, data_3yr, output_path):
    """Plot FCI-G index comparison (1-year vs 3-year)."""
    fig, ax = plt.subplots(figsize=(12, 6))

    # Plot both indices
    ax.plot(data_3yr['date'], data_3yr['fci'], color='#1f77b4',
            linewidth=1.2, label='FCI-G (3-year lookback)')
    ax.plot(data_1yr['date'], data_1yr['fci'], color='#ff7f0e',
            linewidth=1.2, alpha=0.8, label='FCI-G (1-year lookback)')

    # Add zero line
    ax.axhline(y=0, color='black', linewidth=0.5, linestyle='-')

    # Shade regions
    ax.fill_between(data_3yr['date'], data_3yr['fci'], 0,
                    where=[v > 0 for v in data_3yr['fci']],
                    color='#e74c3c', alpha=0.2, label='Tighter conditions')
    ax.fill_between(data_3yr['date'], data_3yr['fci'], 0,
                    where=[v <= 0 for v in data_3yr['fci']],
                    color='#2ecc71', alpha=0.2, label='Looser conditions')

    # Formatting
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('FCI-G Index', fontsize=11)
    ax.set_title('Federal Reserve Financial Conditions Index (FCI-G)', fontsize=14)

    # Format x-axis
    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))

    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper right')

    ax.text(0.01, 0.02, 'Source: Federal Reserve Board',
            transform=ax.transAxes, fontsize=8, color='gray')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def plot_fci_components(data, output_path):
    """Plot FCI-G component decomposition as stacked area chart."""
    fig, ax = plt.subplots(figsize=(12, 7))

    components = [
        ('ffr', 'Fed Funds Rate', '#1f77b4'),
        ('treasury_10yr', '10Yr Treasury', '#ff7f0e'),
        ('mortgage', 'Mortgage Rate', '#2ca02c'),
        ('bbb', 'BBB Spread', '#d62728'),
        ('stock_market', 'Stock Market', '#9467bd'),
        ('house_prices', 'House Prices', '#8c564b'),
        ('dollar', 'Dollar', '#e377c2'),
    ]

    # Plot each component as a line
    for key, label, color in components:
        ax.plot(data['date'], data[key], label=label, color=color,
                linewidth=1, alpha=0.8)

    # Plot total FCI
    ax.plot(data['date'], data['fci'], label='FCI-G Total', color='black',
            linewidth=2)

    # Add zero line
    ax.axhline(y=0, color='black', linewidth=0.5, linestyle='--')

    # Formatting
    ax.set_xlabel('Date', fontsize=11)
    ax.set_ylabel('Contribution to FCI-G', fontsize=11)
    ax.set_title('FCI-G Component Decomposition (3-year lookback)', fontsize=14)

    ax.xaxis.set_major_locator(mdates.YearLocator(5))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))
    ax.xaxis.set_minor_locator(mdates.YearLocator(1))

    ax.grid(True, alpha=0.3)
    ax.legend(loc='upper left', ncol=2, fontsize=9)

    ax.text(0.01, 0.02, 'Source: Federal Reserve Board',
            transform=ax.transAxes, fontsize=8, color='gray')

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def main():
    """Main function to plot FCI data."""
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    data_dir = os.path.join(repo_root, 'data')
    figures_dir = os.path.join(repo_root, 'figures')

    # Read data
    print("Reading FCI-G data...")
    data_1yr = read_fci_data(os.path.join(data_dir, 'fci_g_public_monthly_1yr.csv'))
    data_3yr = read_fci_data(os.path.join(data_dir, 'fci_g_public_monthly_3yr.csv'))

    print(f"  1-year: {len(data_1yr['date'])} observations")
    print(f"  3-year: {len(data_3yr['date'])} observations")
    print(f"  Date range: {data_3yr['date'][0].strftime('%Y-%m-%d')} to {data_3yr['date'][-1].strftime('%Y-%m-%d')}")

    # Create plots
    print("\nGenerating plots...")
    plot_fci_index(data_1yr, data_3yr,
                   os.path.join(figures_dir, 'fci_g_index.png'))
    plot_fci_components(data_3yr,
                        os.path.join(figures_dir, 'fci_g_components.png'))

    print("\nDone!")


if __name__ == "__main__":
    main()
