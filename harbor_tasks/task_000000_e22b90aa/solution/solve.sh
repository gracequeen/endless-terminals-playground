#!/bin/bash
# Auto-generated solve script
set -e

ls -la /home/user/pipeline/
cat /home/user/pipeline/run.sh
cat /home/user/pipeline/extract.py
cat /home/user/pipeline/transform.py
ls -la /home/user/pipeline/raw/
head -5 /home/user/pipeline/raw/sensor_a.csv /home/user/pipeline/raw/sensor_c.csv
head -2 /home/user/pipeline/raw/sensor_*.csv
wc -l /home/user/pipeline/raw/sensor_c.csv
cat /home/user/pipeline/transform.py | head -30
sed -i 's/def parse_timestamps(df):/def parse_timestamps(df):\n    """Parse recorded_at strings to datetime objects, handling multiple formats."""\n    # First try ISO format (YYYY-MM-DD HH:MM:SS)\n    df["recorded_at"] = pd.to_datetime(\n        df["recorded_at"],\n        format="%Y-%m-%d %H:%M:%S",\n        errors="coerce"\n    )\n    # For any NaT values, try European format (DD\/MM\/YYYY HH:MM:SS)\n    nat_mask = df["recorded_at"].isna()\n    if nat_mask.any():\n        # Get original string values from a fresh read - we need to preserve them\n        # Instead, let us use a different approach with mixed format parsing\n        pass\n    return df\n\ndef parse_timestamps_old(df):/' /home/user/pipeline/transform.py
cat /home/user/pipeline/transform.py
cat > /home/user/pipeline/transform.py << 'EOF'
#!/usr/bin/env python3
"""
Transform stage: Read from staging/, apply transformations, write to processed/.
Includes unit conversions and datetime parsing.
"""

import os
import pandas as pd
from pathlib import Path
from datetime import datetime

STAGING_DIR = Path(__file__).parent / "staging"
PROCESSED_DIR = Path(__file__).parent / "processed"

def convert_units(df):
    """Apply unit conversions where needed."""
    # Convert Celsius to Kelvin for temperature sensors
    mask = df['unit'] == 'celsius'
    df.loc[mask, 'value'] = df.loc[mask, 'value'] + 273.15
    df.loc[mask, 'unit'] = 'kelvin'
    return df

def parse_timestamps(df):
    """Parse recorded_at strings to datetime objects, handling multiple formats."""
    # Keep original string values
    original_values = df['recorded_at'].copy()
    
    # First try ISO format (YYYY-MM-DD HH:MM:SS)
    df['recorded_at'] = pd.to_datetime(
        df['recorded_at'],
        format="%Y-%m-%d %H:%M:%S",
        errors='coerce'
    )
    
    # For any NaT values, try European format (DD/MM/YYYY HH:MM:SS)
    nat_mask = df['recorded_at'].isna()
    if nat_mask.any():
        df.loc[nat_mask, 'recorded_at'] = pd.to_datetime(
            original_values[nat_mask],
            format="%d/%m/%Y %H:%M:%S",
            errors='coerce'
        )
    
    return df

def transform():
    """Read from staging/, transform, and write to processed/."""
    PROCESSED_DIR.mkdir(exist_ok=True)

    parquet_files = list(STAGING_DIR.glob("*.parquet"))
    if not parquet_files:
        raise ValueError(f"No parquet files found in {STAGING_DIR}")

    for parquet_file in parquet_files:
        print(f"Transforming {parquet_file.name}...")
        df = pd.read_parquet(parquet_file)

        # Apply transformations
        df = parse_timestamps(df)
        df = convert_units(df)

        # Write to processed
        output_file = PROCESSED_DIR / parquet_file.name
        df.to_parquet(output_file, index=False)
        print(f"  -> Written to {output_file.name}")

if __name__ == "__main__":
    transform()
    print("Transform stage complete.")
EOF
cat /home/user/pipeline/load.py
cd /home/user/pipeline && bash run.sh
python3 -c "import pandas as pd; df = pd.read_parquet('/home/user/pipeline/output/merged.parquet'); print('Total rows:', len(df)); print('NaT count in recorded_at:', df['recorded_at'].isna().sum()); print('Sample of recorded_at values:'); print(df['recorded_at'].head(10))"
python3 -c "import pandas as pd; df = pd.read_parquet('/home/user/pipeline/output/merged.parquet'); sensor_c = df[df['sensor_id'].str.startswith('sensor_c')]; print('Sensor C rows:', len(sensor_c)); print('NaT count:', sensor_c['recorded_at'].isna().sum()); print('Sample:'); print(sensor_c[['sensor_id', 'recorded_at', 'value']].head())"
