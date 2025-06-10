#!/usr/bin/env python3
"""
SDG&E GBD Processor - Configurable Version
Reads rates from JSON configuration file
"""

import os
import json
import pandas as pd
from datetime import datetime
import glob

class SDGEProcessor:
    def __init__(self, config_file='sdge_rates.json'):
        """Initialize processor with configuration file"""
        with open(config_file, 'r') as f:
            self.config = json.load(f)
        
        # Convert holiday strings to datetime objects
        self.holidays = [
            datetime.strptime(h, '%Y-%m-%d').date() 
            for h in self.config['holidays']
        ]
    
    def get_season(self, date):
        """Determine season based on month"""
        month = date.month
        if month in self.config['rates']['summer']['months']:
            return 'summer'
        return 'winter'
    
    def is_holiday(self, date):
        """Check if date is a holiday"""
        return date.date() in self.holidays
    
    def get_time_period(self, hour, is_weekend_holiday, month):
        """Determine time period based on hour and day type"""
        schedule = 'weekend_holiday' if is_weekend_holiday else 'weekday'
        periods = self.config['time_periods'][schedule]
        
        # Check each time period
        for period_name, hours_list in periods.items():
            if period_name == 'special_periods':
                continue
            for start, end in hours_list:
                if start <= hour < end:
                    return period_name.replace('_', '_')
        
        # Check special periods for weekdays
        if not is_weekend_holiday and 'special_periods' in periods:
            special = periods['special_periods']
            if month in special['months']:
                for start, end in special.get('super_off_peak_extra', []):
                    if start <= hour < end:
                        return 'super_off_peak'
        
        return 'off_peak'  # Default
    
    def process_file(self, filepath):
        """Process a single GBD file"""
        # Read metadata
        with open(filepath, 'r') as f:
            lines = f.readlines()
        
        # Find data start
        header_row = 0
        for i, line in enumerate(lines):
            if 'Meter Number,Date,Start Time' in line:
                header_row = i
                break
        
        # Read data
        df = pd.read_csv(filepath, skiprows=header_row)
        
        # Extract account info
        account_info = {
            'name': lines[0].split(',')[1].strip().strip('\r'),
            'address': lines[1].split(',')[1].strip().strip('\r'),
            'account_number': lines[2].split(',')[1].strip().strip('\r'),
            'meter_number': lines[6].split(',')[1].strip().strip('\r')
        }
        
        # Process timestamps
        df['DateTime'] = pd.to_datetime(df['Date'] + ' ' + df['Start Time'])
        df['Hour'] = df['DateTime'].dt.hour
        df['Weekday'] = df['DateTime'].dt.dayofweek
        df['IsWeekend'] = df['Weekday'].isin([5, 6])
        df['IsHoliday'] = df['DateTime'].apply(self.is_holiday)
        df['IsWeekendHoliday'] = df['IsWeekend'] | df['IsHoliday']
        
        # Determine season and time period
        df['Season'] = df['DateTime'].apply(self.get_season)
        df['Month'] = df['DateTime'].dt.month
        df['TimePeriod'] = df.apply(
            lambda row: self.get_time_period(
                row['Hour'], 
                row['IsWeekendHoliday'], 
                row['Month']
            ), 
            axis=1
        )
        
        # Apply rates
        df['Rate'] = df.apply(
            lambda row: self.config['rates'][row['Season']][row['TimePeriod']], 
            axis=1
        )
        
        # Calculate cost
        df['Net'] = df['Net'].astype(float)
        df['Cost'] = df['Net'] * df['Rate']
        
        # Add account info
        for key, value in account_info.items():
            df[key] = value
        
        return df, account_info
    
    def process_folder(self, input_folder, output_file):
        """Process all GBD files in folder"""
        all_data = []
        csv_files = glob.glob(os.path.join(input_folder, '*.csv'))
        
        if not csv_files:
            print(f"No CSV files found in {input_folder}")
            return
        
        print(f"Processing {len(csv_files)} files...")
        
        for csv_file in csv_files:
            print(f"\n{os.path.basename(csv_file)}:")
            try:
                df, account_info = self.process_file(csv_file)
                all_data.append(df)
                
                # Summary
                total_kwh = df['Net'].sum()
                total_cost = df['Cost'].sum()
                print(f"  Account: {account_info['name']}")
                print(f"  Usage: {total_kwh:.2f} kWh")
                print(f"  Cost: ${total_cost:.2f}")
                
            except Exception as e:
                print(f"  Error: {e}")
        
        if all_data:
            # Combine and save
            combined = pd.concat(all_data, ignore_index=True)
            
            # Output columns
            columns = [
                'name', 'address', 'account_number', 'meter_number',
                'DateTime', 'Consumption', 'Generation', 'Net',
                'Season', 'TimePeriod', 'Rate', 'Cost'
            ]
            
            combined[columns].to_csv(output_file, index=False)
            print(f"\nSaved to: {output_file}")
            
            # Total summary
            print(f"\nTOTAL SUMMARY:")
            print(f"Records: {len(combined):,}")
            print(f"Usage: {combined['Net'].sum():.2f} kWh")
            print(f"Cost: ${combined['Cost'].sum():.2f}")
            
            # By time period
            print("\nBy Time Period:")
            summary = combined.groupby('TimePeriod').agg({
                'Net': 'sum',
                'Cost': 'sum'
            }).round(2)
            for period, row in summary.iterrows():
                print(f"  {period}: {row['Net']:.2f} kWh, ${row['Cost']:.2f}")

if __name__ == "__main__":
    import sys
    
    # Default paths
    input_folder = sys.argv[1] if len(sys.argv) > 1 else "./gbd_data"
    output_file = sys.argv[2] if len(sys.argv) > 2 else "./processed_sdge_data.csv"
    config_file = sys.argv[3] if len(sys.argv) > 3 else "./sdge_rates.json"
    
    # Process
    processor = SDGEProcessor(config_file)
    processor.process_folder(input_folder, output_file)
