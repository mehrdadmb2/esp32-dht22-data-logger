#!/usr/bin/env python3
import os
from datetime import datetime

# Adjust this path if needed
data_dir = os.path.join(os.getcwd(), 'data', 'raw')

for filename in os.listdir(data_dir):
    if filename.lower().endswith(('.xls', '.xlsx')):
        # If your files already have timestamps, skip or adjust parsing here
        # This example renames all to current timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        new_name = f"{timestamp}.xlsx"
        os.rename(
            os.path.join(data_dir, filename),
            os.path.join(data_dir, new_name)
        )
        print(f"Renamed {filename} -> {new_name}")
