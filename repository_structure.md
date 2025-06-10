# Suggested GitHub Repository Structure

```
youpower-gbd-processor/
│
├── README.md                    # Main documentation
├── requirements.txt             # Python dependencies
├── .gitignore                  # Git ignore file
│
├── processors/                 # Rate processors for each utility
│   ├── __init__.py
│   ├── sdge_processor.py       # SDG&E processor (current)
│   ├── pge_processor.py        # PG&E processor (future)
│   └── sce_processor.py        # SCE processor (future)
│
├── scripts/                    # Main scripts
│   ├── process_gbd.py         # Main processing script
│   └── process_cli.py         # Command-line interface
│
├── config/                     # Configuration files
│   ├── sdge_rates.json        # SDG&E rate configuration
│   ├── pge_rates.json         # PG&E rate configuration
│   └── sce_rates.json         # SCE rate configuration
│
├── gbd_data/                   # Input folder (gitignored)
│   └── .gitkeep               # Keep folder in git
│
├── output/                     # Output folder (gitignored)
│   └── .gitkeep               # Keep folder in git
│
├── tests/                      # Unit tests
│   ├── __init__.py
│   ├── test_sdge.py
│   └── sample_data/           # Small test files
│       └── test_gbd.csv
│
└── docs/                       # Additional documentation
    ├── sdge_rates.md          # SDG&E rate details
    ├── pge_rates.md           # PG&E rate details
    └── sce_rates.md           # SCE rate details
```

## Workflow

1. **Scraper** deposits GBD CSV files in `gbd_data/` folder
2. **Processor** reads all CSV files from `gbd_data/`
3. **Output** is saved to `output/processed_[utility]_[date].csv`
4. **Results** can be uploaded to billing system

## GitHub Actions Workflow (Optional)

Create `.github/workflows/process_gbd.yml`:

```yaml
name: Process GBD Files

on:
  push:
    paths:
      - 'gbd_data/*.csv'
  workflow_dispatch:

jobs:
  process:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
    
    - name: Process GBD files
      run: |
        python scripts/process_gbd.py gbd_data/ -o output/processed_$(date +%Y%m%d).csv
    
    - name: Upload results
      uses: actions/upload-artifact@v3
      with:
        name: processed-data
        path: output/*.csv
```
