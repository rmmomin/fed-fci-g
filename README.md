# Federal Reserve Financial Conditions Index (FCI-G)

This repository contains R and Python implementations for calculating the Federal Reserve's Financial Conditions Index - General (FCI-G), a measure of U.S. financial conditions.

## Overview

The FCI-G tracks financial conditions based on seven key variables:
- Federal Funds Rate (FFR)
- 10-Year Treasury Rate
- Mortgage Rate
- BBB Corporate Bond Rate
- Stock Market Performance
- House Prices
- Dollar Valuation

The index is calculated using quarterly (3-month) differences of these drivers, weighted according to the methodology described in Ajello et al. (2023).

## Repository Structure

```
.
├── data/                   # CSV data files
│   ├── fci_g_public_monthly_1yr.csv
│   ├── fci_g_public_monthly_3yr.csv
│   ├── fci_g_public_quarterly_1yr.csv
│   └── fci_g_public_quarterly_3yr.csv
├── docs/                   # Documentation
│   ├── The Fed - A New Index to Measure U.S. Financial Conditions.pdf
│   └── fcg-i_data_definitions_508-3281.pdf
├── python/                 # Python implementation
│   ├── calculate_fci.py
│   ├── utility_functions.py
│   ├── input_data.csv
│   ├── multipliers.csv
│   └── requirements.txt
├── scripts/                # R scripts
│   ├── input_data.csv
│   ├── multipliers.csv
│   ├── public_fci_publicrelease.R
│   └── utility_functions_publicrelease.R
└── README.md
```

## Prerequisites

### R Implementation

The following R packages are required:
- doParallel
- lubridate
- tidyverse
- foreach
- timeDate

Install them using:
```r
install.packages(c("doParallel", "lubridate", "tidyverse", "foreach", "timeDate"))
```

### Python Implementation

Python 3.7 or higher is required. Install dependencies using:
```bash
cd python
pip install -r requirements.txt
```

Required packages:
- pandas (>=1.3.0)
- numpy (>=1.21.0)
- python-dateutil (>=2.8.0)

## Usage

### Python Implementation

1. Navigate to the `python/` directory
2. Ensure `input_data.csv` contains your data:
   - First column: dates
   - First row: variable names in code-compatible order
   - Data cells: quarterly (3-month) differences of drivers
3. Run the main script:
   ```bash
   python calculate_fci.py
   ```

#### Configuration Options

- Set `quarterly = True` in the script to generate quarterly versions of the index
- The script processes data at monthly or daily frequency
- Adjust the number of parallel processing cores by modifying the `num_cores` parameter

#### Output Files

The script generates:
- `threeyearFCI_output.csv` - 3-year FCI with decomposition
- `oneyearFCI_output.csv` - 1-year FCI with decomposition
- `threeyearFCI_output_quarterly.csv` - Quarterly 3-year FCI (if `quarterly = True`)
- `oneyearFCI_output_quarterly.csv` - Quarterly 1-year FCI (if `quarterly = True`)

### R Implementation

1. Navigate to the `scripts/` directory
2. Ensure `input_data.csv` contains your data:
   - First column: dates
   - First row: variable names in code-compatible order
   - Data cells: quarterly (3-month) differences of drivers
3. Run the main script:
   ```r
   source("public_fci_publicrelease.R")
   ```

#### Configuration Options

- Set `quarterly = TRUE` in the script to generate quarterly versions of the index
- The script processes data at monthly or daily frequency
- Adjust the number of parallel processing cores by modifying `makeCluster(4)`

#### Output Files

The script generates:
- `threeyearFCI_output.csv` - 3-year FCI with decomposition
- `oneyearFCI_output.csv` - 1-year FCI with decomposition
- `threeyearFCI_output_quarterly.csv` - Quarterly 3-year FCI (if `quarterly = TRUE`)
- `oneyearFCI_output_quarterly.csv` - Quarterly 1-year FCI (if `quarterly = TRUE`)

## Data Files

The `data/` directory contains pre-calculated FCI-G values:
- Monthly indices (1-year and 3-year versions)
- Quarterly indices (1-year and 3-year versions)

## Documentation

The `docs/` directory contains:
- Technical paper: "A New Index to Measure U.S. Financial Conditions"
- Data definitions and methodology documentation

## Reference

Ajello, Andrea, et al. (2023). "A New Index to Measure U.S. Financial Conditions." Federal Reserve Board FEDS Notes.

## License

This is a public release from the Federal Reserve Board.
