FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/etl/data/raw && \
    mkdir -p /home/user/etl/data/processed && \
    mkdir -p /home/user/etl/venv/bin && \
    mkdir -p /home/user/etl/venv/lib/python3.10/site-packages

RUN cat <<'EOF' > /home/user/etl/run.sh
#!/bin/bash
cd /home/user/etl
source venv/bin/activate
python3 ingest.py
EOF
RUN chmod +x /home/user/etl/run.sh

RUN cat <<'EOF' > /home/user/etl/ingest.py
import pandas as pd
import pyarrow
import pyarrow.parquet as pq
from transforms import clean_records

def main():
    # Read raw data
    df = pd.read_csv('data/raw/records.csv')

    # Transform
    df_clean = clean_records(df)

    # Write to parquet
    df_clean.to_parquet('data/processed/output.parquet', index=False)
    print(f"Successfully processed {len(df_clean)} records")

if __name__ == "__main__":
    main()
EOF

RUN cat <<'EOF' > /home/user/etl/transforms.py
import pandas as pd
import numpy as np

def clean_records(df):
    """Clean records by removing invalid status entries."""
    # Filter out rows where status is 'invalid'
    df_clean = df[df['status'] != 'invalid'].copy()

    # Convert value column to numeric, coercing errors
    df_clean['value'] = pd.to_numeric(df_clean['value'], errors='coerce')

    # Fill any NaN values in value column with 0
    df_clean['value'] = df_clean['value'].fillna(0)

    return df_clean
EOF

RUN cat <<'EOF' > /home/user/etl/requirements.txt
pandas==2.1.0
pyarrow==14.0.1
numpy==1.26.0
EOF

RUN python3 <<'PYSCRIPT'
import csv
import random
from datetime import datetime, timedelta

random.seed(42)

statuses = ['valid', 'valid', 'valid', 'valid', 'invalid']  # ~20% invalid
base_time = datetime(2024, 1, 1, 0, 0, 0)

with open('/home/user/etl/data/raw/records.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'timestamp', 'value', 'status'])

    for i in range(1, 501):
        record_id = i
        timestamp = (base_time + timedelta(minutes=i*5)).isoformat()
        value = round(random.uniform(10.0, 1000.0), 2)
        status = random.choice(statuses)
        writer.writerow([record_id, timestamp, value, status])
PYSCRIPT

RUN cat <<'EOF' > /home/user/etl/venv/pyvenv.cfg
home = /usr/local/python3.11-old
include-system-site-packages = false
version = 3.11.0
EOF

RUN cat <<'EOF' > /home/user/etl/venv/bin/activate
# This file must be used with "source bin/activate" *from bash*
# you cannot run it directly

deactivate () {
    # reset old environment variables
    if [ -n "${_OLD_VIRTUAL_PATH:-}" ] ; then
        PATH="${_OLD_VIRTUAL_PATH:-}"
        export PATH
        unset _OLD_VIRTUAL_PATH
    fi
    if [ -n "${_OLD_VIRTUAL_PYTHONHOME:-}" ] ; then
        PYTHONHOME="${_OLD_VIRTUAL_PYTHONHOME:-}"
        export PYTHONHOME
        unset _OLD_VIRTUAL_PYTHONHOME
    fi

    if [ -n "${BASH:-}" -o -n "${ZSH_VERSION:-}" ] ; then
        hash -r 2> /dev/null
    fi

    if [ -n "${_OLD_VIRTUAL_PS1:-}" ] ; then
        PS1="${_OLD_VIRTUAL_PS1:-}"
        export PS1
        unset _OLD_VIRTUAL_PS1
    fi

    unset VIRTUAL_ENV
    if [ ! "${1:-}" = "nondestructive" ] ; then
        unset -f deactivate
    fi
}

deactivate nondestructive

VIRTUAL_ENV="/home/user/etl/venv"
export VIRTUAL_ENV

_OLD_VIRTUAL_PATH="$PATH"
PATH="$VIRTUAL_ENV/bin:$PATH"
export PATH

if [ -z "${VIRTUAL_ENV_DISABLE_PROMPT:-}" ] ; then
    _OLD_VIRTUAL_PS1="${PS1:-}"
    PS1="(venv) ${PS1:-}"
    export PS1
fi

if [ -n "${BASH:-}" -o -n "${ZSH_VERSION:-}" ] ; then
    hash -r 2> /dev/null
fi
EOF

RUN cat <<'EOF' > /home/user/etl/venv/bin/python3
#!/bin/bash
echo "Error: Python installation not found at /usr/local/python3.11-old"
echo "The Python interpreter for this virtual environment was not found."
exit 1
EOF
RUN chmod +x /home/user/etl/venv/bin/python3

RUN ln -s /home/user/etl/venv/bin/python3 /home/user/etl/venv/bin/python

RUN chown -R 1000:1000 /home/user && chmod -R 0777 /home/user

WORKDIR /home/user

CMD ["/bin/bash"]
