#!/usr/bin/env python3
"""
SDG&E Green Button Data Processor
Processes raw GBD CSV files and applies TOU-DR rates
"""

import os
import pandas as pd
from datetime import datetime
import glob

# SDG&E TOU-DR Rates (as of June 2025)
RATES = {
    'summer': {  # June 1 - October 31
        'on_peak': 0.59908,
        'off_peak': 0.52754,
        'super_off_peak': 0.45000
    },
    'winter': {  # November 1 - May 31
        'on_peak': 0.58155,
        'off_peak': 0.51899,
        'super_off_peak': 0.50084
    }
}

# Holidays for 2025 (from rate schedule)
HOLIDAYS = [
    '1/1/2025', '2/17/2025', '5/26/2025', '7/4/2025',
    '9/1/2025', '11/11/2025', '11/27/2025', '12/25/2025'
]

def parse_gbd_file(filepath):
    """Read GBD CSV and extract interval data"""
    # Read file to find where data starts
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    # Find the header row (contains "Meter Number,Date,Start Time")
    header_row = 0
    for i, line in enumerate(lines):
        if 'Meter Number,Date,Start Time' in line:
            header_row = i
            break
    
    # Read the actual data starting from header row
    df = pd.read_csv(filepath, skiprows=header_row)
    
    # Extract account info from top of file
    account_info = {
        'name': lines[0].split(',')[1].strip(),
        'address': lines[1].split(',')[1].strip(),
        'account_number': lines[2].split(',')[1].strip(),
        'meter_number': lines[6].split(',')[1].strip()
    }
    
    return df, account_info

def get_season(date):
    """Determine if date is summer or winter"""
    month = date.month
    if 6 <= month <= 10:
        return 'summer'
    return 'winter'

def is_holiday(date):
    """Check if date is a holiday"""
    date_str = date.strftime('%-m/%-d/%Y')
    return date_str in HOLIDAYS

def get_time_period(date, time, is_weekend_holiday):
    """Determine time period based on date, time, and day type"""
    hour = time.hour
    month = date.month
    
    if is_weekend_holiday:
        # Weekend/Holiday schedule
        if 16 <= hour < 21:  # 4pm-9pm
            return 'on_peak'
        elif (14 <= hour < 16) or (21 <= hour < 24):  # 2pm-4pm or 9pm-midnight
            return 'off_peak'
        else:  # midnight-2pm
            return 'super_off_peak'
    else:
        # Weekday schedule
        if 16 <= hour < 21:  # 4pm-9pm
            return 'on_peak'
        elif (6 <= hour < 16) or (21 <= hour < 24):  # 6am-4pm or 9pm-midnight
            # Special case for March/April
            if month in [3, 4] and 10 <= hour < 14:  # 10am-2pm in March/April
                return 'super_off_peak'
            return 'off_peak'
        else:  # midnight-6am
            return 'super_off_peak'

def process_gbd_files(input_folder, output_file):
    """Process all GBD files in folder and output single CSV"""
    all_data = []
    
    # Find all CSV files in folder
    csv_files = glob.glob(os.path.join(input_folder, '*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in {input_folder}")
        return
    
    print(f"Found {len(csv_files)} CSV files to process")
    
    for csv_file in csv_files:
        print(f"\nProcessing: {os.path.basename(csv_file)}")
        
        try:
            # Parse the GBD file
            df, account_info = parse_gbd_file(csv_file)
            
            # Convert date and time columns
            df['Date'] = pd.to_datetime(df['Date'])
            df['Time'] = pd.to_datetime(df['Start Time'], format='%I:%M %p').dt.time
            df['DateTime'] = pd.to_datetime(df['Date'].astype(str) + ' ' + df['Start Time'])
            
            # Determine day type
            df['Weekday'] = df['Date'].dt.dayofweek  # 0=Monday, 6=Sunday
            df['IsWeekend'] = df['Weekday'].isin([5, 6])
            df['IsHoliday'] = df['Date'].apply(is_holiday)
            df['IsWeekendHoliday'] = df['IsWeekend'] | df['IsHoliday']
            
            # Determine season and time period
            df['Season'] = df['Date'].apply(get_season)
            df['TimePeriod'] = df.apply(
                lambda row: get_time_period(row['Date'], row['Time'], row['IsWeekendHoliday']), 
                axis=1
            )
            
            # Apply rates
            df['Rate'] = df.apply(
                lambda row: RATES[row['Season']][row['TimePeriod']], 
                axis=1
            )
            
            # Calculate cost (using Net column)
            df['Cost'] = df['Net'].astype(float) * df['Rate']
            
            # Add account info
            for key, value in account_info.items():
                df[key] = value
            
            # Add to collection
            all_data.append(df)
            
            # Summary for this file
            total_usage = df['Net'].astype(float).sum()
            total_cost = df['Cost'].sum()
            print(f"  Total Usage: {total_usage:.2f} kWh")
            print(f"  Total Cost: ${total_cost:.2f}")
            
        except Exception as e:
            print(f"  Error processing file: {e}")
            continue
    
    if all_data:
        # Combine all data
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Select output columns
        output_columns = [
            'name', 'address', 'account_number', 'meter_number',
            'DateTime', 'Date', 'Start Time', 'Duration',
            'Consumption', 'Generation', 'Net',
            'Season', 'TimePeriod', 'Rate', 'Cost'
        ]
        
        # Save to CSV
        combined_df[output_columns].to_csv(output_file, index=False)
        print(f"\nProcessed data saved to: {output_file}")
        
        # Overall summary
        print(f"\nOverall Summary:")
        print(f"Total records: {len(combined_df)}")
        print(f"Total usage: {combined_df['Net'].astype(float).sum():.2f} kWh")
        print(f"Total cost: ${combined_df['Cost'].sum():.2f}")
        
        # Cost breakdown by time period
        print(f"\nCost breakdown by time period:")
        cost_summary = combined_df.groupby('TimePeriod')['Cost'].sum()
        for period, cost in cost_summary.items():
            print(f"  {period}: ${cost:.2f}")
    else:
        print("No data was successfully processed")

if __name__ == "__main__":
    # Configuration
    INPUT_FOLDER = "./gbd_data"  # Folder containing GBD CSV files
    OUTPUT_FILE = "./processed_sdge_data.csv"  # Output file
    
    # Process files
    process_gbd_files(INPUT_FOLDER, OUTPUT_FILE)
