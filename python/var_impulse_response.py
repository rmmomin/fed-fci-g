#!/usr/bin/env python3
"""
VAR Impulse Response Function Analysis

Estimates a full-sample VAR model to calculate Impulse Response Functions (IRF)
for GDP growth response to a tailwind (-FCI-G) shock.

Model:
- Bivariate VAR with tailwind and GDP growth
- Cholesky ordering: [tailwind, GDP growth]
- Lags selected by AIC (up to 8)
- Monte Carlo confidence bands (2000 replications)

Usage:
    python var_impulse_response.py
"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from statsmodels.tsa.api import VAR


# Configuration
DELTA_TAILWIND = 0.1      # Shock size: +0.10 in tailwind
SHOCK_QUARTER = pd.Period("2025Q4", freq="Q")
HORIZON = 12              # Forecast horizon (quarters)
MAX_LAGS = 8              # Maximum VAR lags for AIC selection
MC_REPLICATIONS = 2000    # Monte Carlo replications for error bands


def load_data(data_dir):
    """Load FCI-G and GDP growth data for VAR estimation."""
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


def estimate_var_irf(var_data):
    """
    Estimate VAR model and compute orthogonalized IRF.

    Returns:
        dict with IRF results, VAR lag order, and scaling information
    """
    # Prepare data for statsmodels (needs DatetimeIndex)
    var_ts = var_data[['tailwind', 'gdp_g']].dropna().copy()
    var_ts.index = var_ts.index.to_timestamp(how='end')

    # Estimate VAR with AIC-selected lag order
    model = VAR(var_ts)
    sel = model.select_order(maxlags=MAX_LAGS)
    p = int(sel.selected_orders['aic'])
    res = model.fit(p)

    # Compute IRF with Monte Carlo bands
    irf = res.irf(HORIZON)
    names = list(res.names)
    resp_idx = names.index('gdp_g')
    imp_idx = names.index('tailwind')

    orth = irf.orth_irfs
    lower, upper = irf.errband_mc(orth=True, repl=MC_REPLICATIONS, signif=0.05)

    # Extract GDP response to tailwind shock
    gdp_resp = orth[:, resp_idx, imp_idx]
    gdp_lo = lower[:, resp_idx, imp_idx]
    gdp_hi = upper[:, resp_idx, imp_idx]

    # Scale to desired shock size
    tailwind_impact = float(orth[0, imp_idx, imp_idx])
    scale = float(DELTA_TAILWIND / tailwind_impact)

    gdp_resp_scaled = gdp_resp * scale
    gdp_lo_scaled = gdp_lo * scale
    gdp_hi_scaled = gdp_hi * scale

    return {
        'gdp_resp': gdp_resp_scaled,
        'gdp_lo': gdp_lo_scaled,
        'gdp_hi': gdp_hi_scaled,
        'var_lags': p,
        'tailwind_impact': tailwind_impact,
        'scale': scale,
        'var_data': var_ts
    }


def compute_cumulative_effect(growth_irf):
    """Convert growth IRF to cumulative GDP level effect."""
    cum_log = np.cumsum(growth_irf / 400.0)
    return 100.0 * (np.exp(cum_log) - 1.0)


def create_results_dataframe(irf_results):
    """Create comprehensive results DataFrame."""
    horizons = np.arange(HORIZON + 1)
    quarters = [str(SHOCK_QUARTER + int(h)) for h in horizons]

    cum_pct = compute_cumulative_effect(irf_results['gdp_resp'])
    cum_pct_lo = compute_cumulative_effect(irf_results['gdp_lo'])
    cum_pct_hi = compute_cumulative_effect(irf_results['gdp_hi'])

    return pd.DataFrame({
        'h': horizons,
        'quarter': quarters,
        'shock_tailwind': DELTA_TAILWIND,
        'var_lags_p': irf_results['var_lags'],
        'tailwind_impact_h0_per_1orth': irf_results['tailwind_impact'],
        'scale_factor': irf_results['scale'],
        'gdp_growth_pp_qoq_ann': irf_results['gdp_resp'],
        'gdp_growth_pp_qoq_ann_lo95': irf_results['gdp_lo'],
        'gdp_growth_pp_qoq_ann_hi95': irf_results['gdp_hi'],
        'cum_gdp_level_pct': cum_pct,
        'cum_gdp_level_pct_lo95': cum_pct_lo,
        'cum_gdp_level_pct_hi95': cum_pct_hi,
    })


def plot_irf_growth(results_df, output_path):
    """Plot GDP growth impulse response."""
    fig, ax = plt.subplots(figsize=(10, 6))

    h = results_df['h'].values
    resp = results_df['gdp_growth_pp_qoq_ann'].values
    lo = results_df['gdp_growth_pp_qoq_ann_lo95'].values
    hi = results_df['gdp_growth_pp_qoq_ann_hi95'].values

    ax.plot(h, resp, color='#1f77b4', linewidth=2, marker='o',
            markersize=6, label='Point estimate')
    ax.fill_between(h, lo, hi, color='#1f77b4', alpha=0.2, label='95% CI')
    ax.axhline(0, color='black', linewidth=0.5, linestyle='--')

    ax.set_xlabel('Horizon (quarters)', fontsize=11)
    ax.set_ylabel('GDP Growth Response (pp, q/q ann.)', fontsize=11)
    ax.set_title(f'IRF: GDP Growth Response to +{DELTA_TAILWIND} Tailwind Shock',
                 fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def plot_irf_cumulative(results_df, output_path):
    """Plot cumulative GDP level effect."""
    fig, ax = plt.subplots(figsize=(10, 6))

    h = results_df['h'].values
    cum = results_df['cum_gdp_level_pct'].values
    lo = results_df['cum_gdp_level_pct_lo95'].values
    hi = results_df['cum_gdp_level_pct_hi95'].values

    ax.plot(h, cum, color='#2ca02c', linewidth=2, marker='o',
            markersize=6, label='Point estimate')
    ax.fill_between(h, lo, hi, color='#2ca02c', alpha=0.2, label='95% CI')
    ax.axhline(0, color='black', linewidth=0.5, linestyle='--')

    ax.set_xlabel('Horizon (quarters)', fontsize=11)
    ax.set_ylabel('Cumulative GDP Level Effect (%)', fontsize=11)
    ax.set_title(f'IRF: Cumulative GDP Level Effect of +{DELTA_TAILWIND} Tailwind Shock',
                 fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"Saved: {output_path}")
    plt.close()


def main():
    """Main function to run VAR impulse response analysis."""
    # Determine paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    data_dir = os.path.join(repo_root, 'data')
    figures_dir = os.path.join(repo_root, 'figures')
    results_dir = os.path.join(repo_root, 'results')

    print("Loading data...")
    df = load_data(data_dir)

    print("Estimating VAR model...")
    irf_results = estimate_var_irf(df)

    print(f"  VAR lags (AIC): {irf_results['var_lags']}")
    print(f"  Tailwind impact at h=0: {irf_results['tailwind_impact']:.4f}")
    print(f"  Scale factor: {irf_results['scale']:.4f}")

    # Create results DataFrame
    results_df = create_results_dataframe(irf_results)

    # Save estimation data
    var_data = irf_results['var_data'].reset_index()
    var_data.columns = ['date', 'tailwind', 'gdp_g']
    var_data.to_csv(os.path.join(results_dir, 'var_estimation_data.csv'), index=False)
    print(f"Saved: {os.path.join(results_dir, 'var_estimation_data.csv')}")

    # Save full IRF results
    results_df.to_csv(os.path.join(results_dir, 'var_irf_results.csv'), index=False)
    print(f"Saved: {os.path.join(results_dir, 'var_irf_results.csv')}")

    # Save summary table (h=0 to h=5)
    summary_cols = [
        'quarter', 'h', 'gdp_growth_pp_qoq_ann', 'gdp_growth_pp_qoq_ann_lo95',
        'gdp_growth_pp_qoq_ann_hi95', 'cum_gdp_level_pct',
        'cum_gdp_level_pct_lo95', 'cum_gdp_level_pct_hi95'
    ]
    summary_df = results_df.loc[results_df['h'].isin([0, 1, 2, 3, 4, 5]), summary_cols]
    summary_df.to_csv(os.path.join(results_dir, 'var_irf_summary_table.csv'), index=False)
    print(f"Saved: {os.path.join(results_dir, 'var_irf_summary_table.csv')}")

    # Generate plots
    print("\nGenerating plots...")
    plot_irf_growth(results_df, os.path.join(figures_dir, 'var_irf_growth.png'))
    plot_irf_cumulative(results_df, os.path.join(figures_dir, 'var_irf_cumulative.png'))

    print("\nAnalysis complete!")


if __name__ == "__main__":
    main()
