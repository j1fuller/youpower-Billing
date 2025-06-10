# SDG&E Green Button Data Processor

A simple Python script to process SDG&E Green Button Data (GBD) CSV files and apply TOU-DR (Time-of-Use Domestic Residential) rates.

## Features

- Reads multiple GBD CSV files from a folder
- Automatically detects time periods (On-Peak, Off-Peak, Super Off-Peak)
- Applies correct seasonal rates (Summer/Winter)
- Handles weekends and holidays
- Outputs a single processed CSV with all calculations

## Requirements

```bash
pip install pandas
```

## Usage

1. Place all your GBD CSV files in a folder (default: `./gbd_data`)
2. Run the script:
   ```bash
   python sdge_gbd_processor.py
   ```
3. The processed data will be saved to `processed_sdge_data.csv`

## Configuration

Edit these variables in the script to change paths:
```python
INPUT_FOLDER = "./gbd_data"  # Folder containing GBD CSV files
OUTPUT_FILE = "./processed_sdge_data.csv"  # Output file
```

## Rate Structure (as of June 2025)

### Summer Rates (June 1 - October 31)
- On-Peak: $0.59908/kWh
- Off-Peak: $0.52754/kWh
- Super Off-Peak: $0.45000/kWh

### Winter Rates (November 1 - May 31)
- On-Peak: $0.58155/kWh
- Off-Peak: $0.51899/kWh
- Super Off-Peak: $0.50084/kWh

### Time Periods

**Weekdays:**
- On-Peak: 4:00 PM - 9:00 PM
- Off-Peak: 6:00 AM - 4:00 PM; 9:00 PM - midnight
- Super Off-Peak: Midnight - 6:00 AM; 10:00 AM - 2:00 PM (March & April only)

**Weekends & Holidays:**
- On-Peak: 4:00 PM - 9:00 PM
- Off-Peak: 2:00 PM - 4:00 PM; 9:00 PM - midnight
- Super Off-Peak: Midnight - 2:00 PM

## Output Format

The processed CSV includes:
- Account information (name, address, account number, meter number)
- Original data (DateTime, consumption, generation, net usage)
- Calculated fields (Season, TimePeriod, Rate, Cost)

## Example Output

```
name,address,account_number,meter_number,DateTime,Date,Start Time,Duration,Consumption,Generation,Net,Season,TimePeriod,Rate,Cost
R G CARNATION...,962 S MOLLISON...,210001211079,06330116,2025-05-01 00:00:00,2025-05-01,12:00 AM,15,0.01,0.0,0.01,winter,super_off_peak,0.50084,0.0050084
```

## Updating Rates

To update rates, modify the `RATES` dictionary in the script:
```python
RATES = {
    'summer': {
        'on_peak': 0.59908,
        'off_peak': 0.52754,
        'super_off_peak': 0.45000
    },
    'winter': {
        'on_peak': 0.58155,
        'off_peak': 0.51899,
        'super_off_peak': 0.50084
    }
}
```

## Holidays

The script includes 2025 holidays. Update the `HOLIDAYS` list as needed:
```python
HOLIDAYS = [
    '1/1/2025', '2/17/2025', '5/26/2025', '7/4/2025',
    '9/1/2025', '11/11/2025', '11/27/2025', '12/25/2025'
]
```
