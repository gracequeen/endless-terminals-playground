FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install pytest

RUN mkdir -p /home/user/inventory && chmod 0777 /home/user && chmod 0777 /home/user/inventory

RUN python3 << 'PYSCRIPT'
import random
import csv
import io

random.seed(42)

# Configuration based on task requirements
TOTAL_ROWS = 846  # excluding header
MM_DD_YYYY_COUNT = 312
YYYY_MM_DD_COUNT = 401
DD_MM_YYYY_COUNT = 89
UNPARSEABLE_DATE_COUNT = 4
DOLLAR_SIGN_PRICES = 23
DECIMAL_PRICES = 156
NEGATIVE_PRICES = 7
DUPLICATE_IDS = 19
SWAPPED_COLUMNS = 12
EMPTY_REQUIRED = 6
MALFORMED_CSV = 4

# Locations
locations = ["Warehouse A", "Warehouse B", "Office 101", "Office 202", "Storage Room", "IT Closet", "Building C", "Remote Site"]

# Product names
products = [
    "Laptop Dell XPS", "Monitor 27inch", "Keyboard Mechanical", "Mouse Wireless",
    "Standing Desk Pro", "Office Chair Ergonomic", "Webcam HD", "Headset Bluetooth",
    "Docking Station", "USB Hub", "External SSD", "Network Switch",
    "Printer LaserJet", "Scanner Flatbed", "Projector 4K", "Whiteboard Digital",
    "Server Rack", "UPS Battery", "Cable Management Kit", "Phone VoIP"
]

def gen_serial(idx):
    letters = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ', k=3))
    return f"SN-{letters}-{idx:05d}"

def gen_mm_dd_yyyy():
    y = random.randint(2015, 2023)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return f"{m:02d}/{d:02d}/{y}"

def gen_yyyy_mm_dd():
    y = random.randint(2015, 2023)
    m = random.randint(1, 12)
    d = random.randint(1, 28)
    return f"{y}-{m:02d}-{d:02d}"

def gen_dd_mm_yyyy():
    y = random.randint(2015, 2023)
    m = random.randint(1, 12)
    d = random.randint(13, 28)  # day > 12 to be unambiguous
    return f"{d:02d}.{m:02d}.{y}"

def gen_unparseable_date():
    # Truly unparseable dates
    bad_dates = ["2020-13-45", "00/00/0000", "invalid-date", "32.13.2020"]
    return random.choice(bad_dates)

def gen_price(with_dollar=False, with_decimal=True, negative=False):
    val = random.randint(5000, 500000) / 100  # 50.00 to 5000.00
    if negative:
        val = -val
    if with_dollar:
        if val >= 1000 or val <= -1000:
            formatted = f"${val:,.2f}"
        else:
            formatted = f"${val:.2f}"
    elif with_decimal:
        formatted = f"{val:.2f}"
    else:
        formatted = str(int(val * 100) // 100)
    return formatted

# Build the rows
rows = []
used_ids = set()
id_counter = 1

# Track which rows get which date format
date_format_pool = (
    ['mm_dd_yyyy'] * MM_DD_YYYY_COUNT +
    ['yyyy_mm_dd'] * YYYY_MM_DD_COUNT +
    ['dd_mm_yyyy'] * DD_MM_YYYY_COUNT +
    ['unparseable'] * UNPARSEABLE_DATE_COUNT
)
random.shuffle(date_format_pool)

# Track price formats
price_format_pool = (
    ['dollar'] * DOLLAR_SIGN_PRICES +
    ['decimal'] * DECIMAL_PRICES +
    ['negative'] * NEGATIVE_PRICES +
    ['integer'] * (TOTAL_ROWS - DOLLAR_SIGN_PRICES - DECIMAL_PRICES - NEGATIVE_PRICES - DUPLICATE_IDS)
)
random.shuffle(price_format_pool)

# Special rows indices
special_indices = set()

# Duplicate IDs - need 19 pairs (38 rows)
duplicate_base_ids = []
for i in range(DUPLICATE_IDS):
    duplicate_base_ids.append(f"AST-{i+300:05d}")

# Swapped columns indices
swapped_indices = set(random.sample(range(TOTAL_ROWS - DUPLICATE_IDS - EMPTY_REQUIRED - MALFORMED_CSV), SWAPPED_COLUMNS))

# Empty required fields indices
empty_indices = set(random.sample(range(TOTAL_ROWS - DUPLICATE_IDS - MALFORMED_CSV), EMPTY_REQUIRED)) - swapped_indices

# Malformed CSV indices
malformed_indices = set(random.sample(range(TOTAL_ROWS - DUPLICATE_IDS), MALFORMED_CSV)) - swapped_indices - empty_indices

# Specific records required by tests
specific_records = {
    'AST-00142': {'serial': 'SN-KVM-00142', 'purchase_date': '03/15/2019', 'price': '2345.99', 'name': 'Monitor 27inch', 'location': 'Office 101'},
    'AST-00847': {'serial': 'SN-PRO-00847', 'purchase_date': '2023-11-28', 'price': '899.00', 'name': 'Standing Desk Pro', 'location': 'Warehouse A'},
}

# AST-00333 is a duplicate case
duplicate_records_333 = [
    {'id': 'AST-00333', 'serial': 'SN-DUP-00333', 'purchase_date': '2021-01-10', 'price': '1500.00', 'name': 'Laptop Dell XPS', 'location': 'Office 202'},
    {'id': 'AST-00333', 'serial': 'SN-DUP-00333', 'purchase_date': '2022-06-15', 'price': '1500.00', 'name': 'Laptop Dell XPS', 'location': 'Office 202'},
]

# Generate regular rows
row_idx = 0
date_idx = 0
price_idx = 0

# First add specific required records
for asset_id, data in specific_records.items():
    rows.append([asset_id, data['name'], data['serial'], data['purchase_date'], data['price'], data['location']])
    used_ids.add(asset_id)
    row_idx += 1
    date_idx += 1
    price_idx += 1

# Add duplicate 333 records
for rec in duplicate_records_333:
    rows.append([rec['id'], rec['name'], rec['serial'], rec['purchase_date'], rec['price'], rec['location']])
    row_idx += 1
    date_idx += 1
    price_idx += 1

# Add other duplicates (18 more pairs since 333 is already added)
for i, dup_id in enumerate(duplicate_base_ids):
    if dup_id == 'AST-00333':
        continue
    # First occurrence
    serial = gen_serial(300 + i)
    name = random.choice(products)
    loc = random.choice(locations)
    date1 = f"{random.randint(2018, 2020)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    date2 = f"{random.randint(2021, 2023)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}"
    price = f"{random.randint(100, 5000)}.{random.randint(0,99):02d}"
    rows.append([dup_id, name, serial, date1, price, loc])
    rows.append([dup_id, name, serial, date2, price, loc])
    row_idx += 2
    date_idx += 2
    price_idx += 2

# Generate remaining rows
remaining = TOTAL_ROWS - row_idx
for i in range(remaining):
    while True:
        asset_id = f"AST-{id_counter:05d}"
        id_counter += 1
        if asset_id not in used_ids and asset_id not in [d for d in duplicate_base_ids]:
            break
    used_ids.add(asset_id)

    serial = gen_serial(id_counter)
    name = random.choice(products)
    loc = random.choice(locations)

    # Date format
    if date_idx < len(date_format_pool):
        df = date_format_pool[date_idx]
        date_idx += 1
    else:
        df = 'yyyy_mm_dd'

    if df == 'mm_dd_yyyy':
        date = gen_mm_dd_yyyy()
    elif df == 'yyyy_mm_dd':
        date = gen_yyyy_mm_dd()
    elif df == 'dd_mm_yyyy':
        date = gen_dd_mm_yyyy()
    else:
        date = gen_unparseable_date()

    # Price format
    if price_idx < len(price_format_pool):
        pf = price_format_pool[price_idx]
        price_idx += 1
    else:
        pf = 'integer'

    if pf == 'dollar':
        price = gen_price(with_dollar=True)
    elif pf == 'decimal':
        price = gen_price(with_decimal=True)
    elif pf == 'negative':
        price = gen_price(negative=True)
    else:
        price = gen_price(with_decimal=False)

    current_row_idx = len(rows)

    # Check for special cases
    if current_row_idx in swapped_indices:
        # Swap name and serial
        rows.append([asset_id, serial, name, date, price, loc])
    elif current_row_idx in empty_indices:
        # Empty required field
        if random.random() < 0.5:
            rows.append(['', name, serial, date, price, loc])  # empty id
        else:
            rows.append([asset_id, name, serial, date, '', loc])  # empty price
    elif current_row_idx in malformed_indices:
        # Malformed CSV - unescaped quote in name
        bad_name = f'Monitor "27 inch" Pro'
        rows.append([asset_id, bad_name, serial, date, price, loc])
    else:
        rows.append([asset_id, name, serial, date, price, loc])

# Shuffle rows (but keep header separate)
random.shuffle(rows)

# Write CSV
with open('/home/user/inventory/assets.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    writer.writerow(['id', 'name', 'serial', 'purchase_date', 'price', 'location'])
    for row in rows:
        writer.writerow(row)

print(f"Generated {len(rows)} data rows")
PYSCRIPT

RUN chmod 644 /home/user/inventory/assets.csv

USER root
RUN useradd -m -d /home/user -s /bin/bash user || true
RUN chown -R user:user /home/user

USER user
WORKDIR /home/user

CMD ["/bin/bash"]
