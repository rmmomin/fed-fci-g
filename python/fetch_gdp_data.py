#!/usr/bin/env python3
"""
Fetch Real GDP Growth Data from FRED API

This script fetches the Real GDP Growth (Q/Q annualized) data from the
Federal Reserve Economic Data (FRED) API and saves it to a CSV file.

Series: A191RL1Q225SBEA - Real Gross Domestic Product, Percent Change from
Preceding Period, Seasonally Adjusted Annual Rate

Usage:
    python fetch_gdp_data.py

Environment:
    Requires FRED_API_KEY in .env file at repository root
"""

import os
import csv
import urllib.request
import json
from datetime import datetime

# Configuration
SERIES_ID = "A191RL1Q225SBEA"
OUTPUT_FILENAME = "real_gdp_growth_qoq_annualized.csv"


def load_env():
    """Load environment variables from .env file."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    env_path = os.path.join(repo_root, '.env')

    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()


def get_api_key():
    """Get FRED API key from environment."""
    load_env()
    api_key = os.environ.get('FRED_API_KEY')
    if not api_key:
        raise ValueError(
            "FRED_API_KEY not found. Add it to .env file at repository root:\n"
            "FRED_API_KEY=your_api_key_here"
        )
    return api_key


def fetch_fred_data(series_id, api_key):
    """
    Fetch observations from FRED API.

    Parameters:
    -----------
    series_id : str
        FRED series identifier
    api_key : str
        FRED API key

    Returns:
    --------
    list
        List of observation dictionaries with 'date' and 'value' keys
    """
    url = (
        f"https://api.stlouisfed.org/fred/series/observations"
        f"?series_id={series_id}&api_key={api_key}&file_type=json"
    )

    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())

    return data['observations']


def save_to_csv(observations, filepath):
    """
    Save observations to CSV file.

    Parameters:
    -----------
    observations : list
        List of observation dictionaries
    filepath : str
        Output file path
    """
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['date', 'real_gdp_growth_qoq_annualized'])
        for obs in observations:
            writer.writerow([obs['date'], obs['value']])


def main():
    """Main function to fetch and save GDP data."""
    # Get API key from environment
    api_key = get_api_key()

    # Determine output path (relative to repo root)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(script_dir)
    output_path = os.path.join(repo_root, 'data', OUTPUT_FILENAME)

    print(f"Fetching {SERIES_ID} from FRED API...")
    observations = fetch_fred_data(SERIES_ID, api_key)

    print(f"Retrieved {len(observations)} observations")
    print(f"Date range: {observations[0]['date']} to {observations[-1]['date']}")

    save_to_csv(observations, output_path)
    print(f"Saved to: {output_path}")

    print(f"\nLast updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
