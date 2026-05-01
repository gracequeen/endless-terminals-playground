FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    make \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/reports/raw \
    && mkdir -p /home/user/reports/cleaned \
    && mkdir -p /home/user/reports/final

RUN cat <<'EOF' > /home/user/reports/raw/sales_q1.csv
 product , quantity , price 
Widget A,100,19.99
Widget B,50,29.99
Gadget X,75,49.99
EOF

RUN cat <<'EOF' > /home/user/reports/raw/sales_q2.csv
 product , quantity , price 
Widget A,120,19.99
Widget C,80,39.99
Gadget Y,60,59.99
EOF

RUN cat <<'EOF' > /home/user/reports/raw/inventory.csv
 item , stock , warehouse 
Widget A,500,North
Widget B,300,South
Gadget X,200,North
EOF

RUN cat <<'EOF' > /home/user/reports/clean.py
#!/usr/bin/env python3
"""
Clean a CSV file by stripping whitespace from headers.
Usage: python clean.py <input_path> <output_path>
"""
import sys
import csv

def main():
    if len(sys.argv) != 3:
        print("Usage: python clean.py <input_path> <output_path>", file=sys.stderr)
        sys.exit(1)

    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, 'r', newline='') as infile:
        reader = csv.reader(infile)
        rows = list(reader)

    if rows:
        # Strip whitespace from headers (first row)
        rows[0] = [header.strip() for header in rows[0]]

    with open(output_path, 'w', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerows(rows)

if __name__ == "__main__":
    main()
EOF

RUN cat <<'EOF' > /home/user/reports/aggregate.py
#!/usr/bin/env python3
"""
Aggregate all CSV files in cleaned/ directory and write to final/summary.csv.
Usage: python aggregate.py
"""
import os
import csv
import glob

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    cleaned_dir = os.path.join(script_dir, 'cleaned')
    final_dir = os.path.join(script_dir, 'final')
    output_path = os.path.join(final_dir, 'summary.csv')

    csv_files = sorted(glob.glob(os.path.join(cleaned_dir, '*.csv')))

    if not csv_files:
        print("No CSV files found in cleaned/")
        return

    all_rows = []
    headers = None

    for csv_file in csv_files:
        with open(csv_file, 'r', newline='') as f:
            reader = csv.reader(f)
            rows = list(reader)
            if rows:
                if headers is None:
                    headers = rows[0]
                    all_rows.append(headers)
                # Add data rows (skip header if we already have one)
                for row in rows[1:]:
                    all_rows.append(row)

    os.makedirs(final_dir, exist_ok=True)

    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(all_rows)

    print(f"Aggregated {len(csv_files)} files into {output_path}")

if __name__ == "__main__":
    main()
EOF

RUN chmod 0755 /home/user/reports/clean.py /home/user/reports/aggregate.py

RUN chmod -R 0777 /home/user/reports

WORKDIR /home/user

CMD ["/bin/bash"]
