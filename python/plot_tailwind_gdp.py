#!/usr/bin/env python3
"""
Tailwind vs GDP Growth Analysis

Creates visualizations analyzing the relationship between Tailwind (-FCI-G)
and Real GDP growth (q/q annualized):
1. Time-series plot with dual axes
2. Scatter plot with OLS regression fit

Sample: 2000Q1 onwards, excluding GFC (2007Q4-2009Q2) and pandemic (2020Q1-2020Q4)

Usage:
    python plot_tailwind_gdp.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm


# Configuration
START_QUARTER = pd.Period("2000Q1", freq="Q")
GFC_QUARTERS = pd.period_range("2007Q4", "2009Q2", freq="Q")
PANDEMIC_QUARTERS = pd.period_range("2020Q1", "2020Q4", freq="Q")

# Axis limits for alignment
LHS_YLIM = (-1.1, 1.8)  # Tailwind axis
RHS_YLIM = (-2, 7)       # GDP growth axis


def load_data(data_dir):
    """Load FCI-G and GDP growth data."""
    fcig = pd.read_csv(
        os.path.join(data_dir, 'fci_g_public_quarterly_3yr.csv'),
        parse_dates=['date']
    )
    gdp = pd.read_csv(
        os.path.join(data_dir, 'real_gdp_growth_qoq_annualized.csv'),
        parse_dates=['date']
    )

    fcig['q'] = fcig['date'].dt.to_period('Q')
    gdp['q'] = gdp['date'].dt.to_period('Q')

    df = (
        fcig.set_index('q')[['FCI-G Index (baseline)']]
        .rename(columns={'FCI-G Index (baseline)': 'fcig'})
        .join(
            gdp.set_index('q')[['real_gdp_growth_qoq_annualized']]
            .rename(columns={'real_gdp_growth_qoq_annualized': 'gdp_g'}),
            how='inner'
        )
        .sort_index()
    )
    df['tailwind'] = -df['fcig']

    return df


def prepare_samples(df):
    """Prepare time series and scatter samples, excluding crisis periods."""
    df = df.loc[df.index >= START_QUARTER].copy()
    df['excluded'] = df.index.isin(GFC_QUARTERS) | df.index.isin(PANDEMIC_QUARTERS)

    # Scatter sample excludes crises entirely
    scatter_sample = df.loc[~df['excluded'], ['fcig', 'tailwind', 'gdp_g']].dropna().copy()

    # Time series sets excluded periods to NaN (line breaks)
    ts_sample = df[['tailwind', 'gdp_g', 'excluded']].copy()
    ts_sample.loc[ts_sample['excluded'], ['tailwind', 'gdp_g']] = np.nan

    return ts_sample, scatter_sample, df['excluded']


def plot_timeseries(ts_sample, output_path):
    """Create dual-axis time series plot."""
    ts_plot = ts_sample.copy()
    ts_plot.index = ts_plot.index.to_timestamp(how='end')

    fig, ax1 = plt.subplots(figsize=(12, 6))
    ax2 = ax1.twinx()

    ax1.plot(ts_plot.index, ts_plot['tailwind'], color='tab:blue',
             linewidth=1.5, label='Tailwind = -FCI-G (LHS)')
    ax2.plot(ts_plot.index, ts_plot['gdp_g'], color='tab:orange',
             linewidth=1.5, label='Real GDP growth q/q ann. (RHS)')

    ax1.set_title('Tailwind (-FCI-G) vs Real GDP Growth (q/q annualized)\n'
                  'Sample: 2000Q1+; excl. GFC (2007Q4-2009Q2) & pandemic (2020Q1-2020Q4)',
                  fontsize=12)
    ax1.set_xlabel('Date', fontsize=11)
    ax1.set_ylabel('Tailwind = -FCI-G (index)', fontsize=11)
    ax2.set_ylabel('Real GDP growth (q/q annualized, %)', fontsize=11)

    ax1.set_ylim(LHS_YLIM)
    ax2.set_ylim(RHS_YLIM)

    # Combined legend
    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper right')

    ax1.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def plot_scatter(scatter_sample, output_path):
    """Create scatter plot with OLS regression line."""
    x = scatter_sample['tailwind']
    y = scatter_sample['gdp_g']
    corr = x.corr(y)

    # OLS fit
    fit = sm.OLS(y, sm.add_constant(x)).fit()
    a = fit.params['const']
    b = fit.params['tailwind']

    fig, ax = plt.subplots(figsize=(10, 7))
    ax.scatter(x, y, alpha=0.6, s=50)

    # Regression line
    xgrid = np.linspace(float(x.min()), float(x.max()), 200)
    ax.plot(xgrid, a + b * xgrid, color='tab:red', linewidth=2,
            label=f'OLS fit: y = {a:.2f} + {b:.2f}x')

    ax.axhline(0, color='black', linewidth=0.5)
    ax.axvline(0, color='black', linewidth=0.5)

    ax.set_title(f'Tailwind (-FCI-G) vs Real GDP Growth (q/q annualized)\n'
                 f'Sample: 2000Q1+ excl. GFC & pandemic | Corr={corr:.3f}, N={len(scatter_sample)}',
                 fontsize=12)
    ax.set_xlabel('Tailwind = -FCI-G (index)', fontsize=11)
    ax.set_ylabel('Real GDP growth (q/q annualized, %)', fontsize=11)

    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()

    return corr, len(scatter_sample)


def main():
    """Main function to run tailwind vs GDP analysis."""
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    data_dir = os.path.join(repo_root, 'data')
    figures_dir = os.path.join(repo_root, 'figures')
    results_dir = os.path.join(repo_root, 'results')

    print("Loading data...")
    df = load_data(data_dir)

    print("Preparing samples...")
    ts_sample, scatter_sample, excluded = prepare_samples(df)

    # Export data
    ts_export = ts_sample.reset_index().rename(columns={'q': 'quarter'})
    ts_export['quarter_end_date'] = ts_export['quarter'].dt.to_timestamp(how='end')
    ts_export.to_csv(os.path.join(results_dir, 'tailwind_gdp_timeseries_data.csv'), index=False)
    print(f"Saved: {os.path.join(results_dir, 'tailwind_gdp_timeseries_data.csv')}")

    sc_export = scatter_sample.reset_index().rename(columns={'q': 'quarter'})
    sc_export['quarter_end_date'] = sc_export['quarter'].dt.to_timestamp(how='end')
    sc_export.to_csv(os.path.join(results_dir, 'tailwind_gdp_scatter_data.csv'), index=False)
    print(f"Saved: {os.path.join(results_dir, 'tailwind_gdp_scatter_data.csv')}")

    # Generate plots
    print("\nGenerating plots...")
    plot_timeseries(ts_sample, os.path.join(figures_dir, 'tailwind_gdp_timeseries.png'))

    corr, n = plot_scatter(scatter_sample, os.path.join(figures_dir, 'tailwind_gdp_scatter.png'))

    print(f"\nAnalysis complete!")
    print(f"  Correlation: {corr:.3f}")
    print(f"  Sample size: {n}")


if __name__ == "__main__":
    main()
