#!/usr/bin/env python3
"""
SDG&E GBD Processor - Command Line Version
"""

import argparse
import sys
from sdge_gbd_processor import process_gbd_files

def main():
    parser = argparse.ArgumentParser(
        description='Process SDG&E Green Button Data files and apply TOU-DR rates'
    )
    
    parser.add_argument(
        'input_folder',
        help='Folder containing GBD CSV files'
    )
    
    parser.add_argument(
        '-o', '--output',
        default='./processed_sdge_data.csv',
        help='Output CSV file path (default: ./processed_sdge_data.csv)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed processing information'
    )
    
    args = parser.parse_args()
    
    # Process the files
    try:
        process_gbd_files(args.input_folder, args.output)
        print(f"\nSuccess! Processed data saved to: {args.output}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
