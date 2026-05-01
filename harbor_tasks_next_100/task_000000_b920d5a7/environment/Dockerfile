FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    jq \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1

RUN pip3 install pytest

RUN mkdir -p /home/user/audit && chmod 0777 /home/user && chmod 0777 /home/user/audit

RUN python3 << 'PYEOF'
import json

payments = [
    {"txn_id": "TXN-20240301-0001", "amount": 1250.00, "merchant": "Acme Corp", "timestamp": "2024-03-01T09:14:22Z", "status": "completed"},
    {"txn_id": "TXN-20240301-0002", "amount": 89.99, "merchant": "Widget LLC", "timestamp": "2024-03-01T10:32:01Z", "status": "completed"},
    {"txn_id": "TXN-20240301-0003", "amount": 542.50, "merchant": "TechStart Inc", "timestamp": "2024-03-01T11:45:33Z", "status": "completed"},
    {"txn_id": "TXN-20240301-0004", "amount": 75.00, "merchant": "Coffee House", "timestamp": "2024-03-01T14:22:10Z", "status": "completed"},
    {"txn_id": "TXN-20240302-0001", "amount": 3200.00, "merchant": "Global Services", "timestamp": "2024-03-02T08:05:44Z", "status": "completed"},
    {"txn_id": "TXN-20240302-0002", "amount": 199.99, "merchant": "Electronics Plus", "timestamp": "2024-03-02T09:18:27Z", "status": "completed"},
    {"txn_id": "TXN-20240302-0003", "amount": 45.50, "merchant": "Quick Mart", "timestamp": "2024-03-02T12:33:55Z", "status": "completed"},
    {"txn_id": "TXN-20240303-0001", "amount": 890.25, "merchant": "Office Supplies Co", "timestamp": "2024-03-03T10:11:02Z", "status": "completed"},
    {"txn_id": "TXN-20240303-0002", "amount": 1500.00, "merchant": "Consulting Group", "timestamp": "2024-03-03T13:45:18Z", "status": "completed"},
    {"txn_id": "TXN-20240303-0003", "amount": 67.80, "merchant": "Lunch Spot", "timestamp": "2024-03-03T12:30:00Z", "status": "completed"},
    {"txn_id": "TXN-20240304-0001", "amount": 2100.00, "merchant": "Marketing Agency", "timestamp": "2024-03-04T09:00:15Z", "status": "completed"},
    {"txn_id": "TXN-20240304-0002", "amount": 350.75, "merchant": "Travel Booking", "timestamp": "2024-03-04T14:22:33Z", "status": "completed"},
    {"txn_id": "TXN-20240304-0003", "amount": 29.99, "merchant": "Subscription Service", "timestamp": "2024-03-04T00:01:00Z", "status": "completed"},
    {"txn_id": "TXN-20240305-0001", "amount": 4500.00, "merchant": "Software Vendor", "timestamp": "2024-03-05T11:30:45Z", "status": "completed"},
    {"txn_id": "TXN-20240305-0002", "amount": 125.00, "merchant": "Parking Services", "timestamp": "2024-03-05T08:15:22Z", "status": "completed"},
    {"txn_id": "TXN-20240306-0001", "amount": 780.00, "merchant": "Training Center", "timestamp": "2024-03-06T10:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240306-0002", "amount": 55.25, "merchant": "Gas Station", "timestamp": "2024-03-06T17:45:12Z", "status": "completed"},
    {"txn_id": "TXN-20240307-0001", "amount": 1875.50, "merchant": "Equipment Rental", "timestamp": "2024-03-07T09:30:00Z", "status": "completed"},
    {"txn_id": "TXN-20240307-0002", "amount": 420.00, "merchant": "Catering Co", "timestamp": "2024-03-07T12:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240308-0001", "amount": 99.00, "merchant": "Cloud Storage", "timestamp": "2024-03-08T00:00:01Z", "status": "completed"},
    {"txn_id": "TXN-20240308-0002", "amount": 2750.00, "merchant": "Legal Services", "timestamp": "2024-03-08T14:15:30Z", "status": "completed"},
    {"txn_id": "TXN-20240309-0001", "amount": 185.50, "merchant": "Office Cleaning", "timestamp": "2024-03-09T18:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240310-0001", "amount": 3100.00, "merchant": "IT Support", "timestamp": "2024-03-10T10:45:22Z", "status": "completed"},
    {"txn_id": "TXN-20240310-0002", "amount": 62.40, "merchant": "Courier Service", "timestamp": "2024-03-10T15:30:18Z", "status": "completed"},
    {"txn_id": "TXN-20240311-0001", "amount": 950.00, "merchant": "Printing Services", "timestamp": "2024-03-11T11:20:00Z", "status": "completed"},
    {"txn_id": "TXN-20240311-0002", "amount": 275.00, "merchant": "Team Lunch", "timestamp": "2024-03-11T13:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240312-0001", "amount": 5200.00, "merchant": "Annual License", "timestamp": "2024-03-12T09:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240312-0002", "amount": 88.88, "merchant": "Domain Renewal", "timestamp": "2024-03-12T10:15:45Z", "status": "completed"},
    {"txn_id": "TXN-20240313-0001", "amount": 1450.00, "merchant": "Security Audit", "timestamp": "2024-03-13T14:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240313-0002", "amount": 33.50, "merchant": "Snack Delivery", "timestamp": "2024-03-13T16:22:10Z", "status": "completed"},
    {"txn_id": "TXN-20240314-0001", "amount": 2200.00, "merchant": "HR Services", "timestamp": "2024-03-14T09:30:00Z", "status": "completed"},
    {"txn_id": "TXN-20240314-0002", "amount": 145.00, "merchant": "Phone Bill", "timestamp": "2024-03-14T00:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240315-0001", "amount": 675.25, "merchant": "Maintenance", "timestamp": "2024-03-15T11:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240315-0002", "amount": 1800.00, "merchant": "Advertising", "timestamp": "2024-03-15T13:45:30Z", "status": "completed"},
    {"txn_id": "TXN-20240316-0001", "amount": 49.99, "merchant": "App Store", "timestamp": "2024-03-16T08:22:15Z", "status": "completed"},
    {"txn_id": "TXN-20240317-0001", "amount": 3500.00, "merchant": "Conference Fee", "timestamp": "2024-03-17T10:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240318-0001", "amount": 225.00, "merchant": "Utilities", "timestamp": "2024-03-18T00:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240318-0002", "amount": 1125.75, "merchant": "Insurance", "timestamp": "2024-03-18T09:15:00Z", "status": "completed"},
    {"txn_id": "TXN-20240319-0001", "amount": 82.00, "merchant": "Taxi Service", "timestamp": "2024-03-19T19:30:22Z", "status": "completed"},
    {"txn_id": "TXN-20240319-0002", "amount": 4100.00, "merchant": "Contractor Pay", "timestamp": "2024-03-19T15:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240320-0001", "amount": 560.00, "merchant": "Web Hosting", "timestamp": "2024-03-20T00:00:01Z", "status": "completed"},
    {"txn_id": "TXN-20240320-0002", "amount": 1950.00, "merchant": "Design Agency", "timestamp": "2024-03-20T11:30:00Z", "status": "completed"},
    {"txn_id": "TXN-20240321-0001", "amount": 38.75, "merchant": "Office Snacks", "timestamp": "2024-03-21T14:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240321-0002", "amount": 2800.00, "merchant": "Accounting Firm", "timestamp": "2024-03-21T10:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240322-0001", "amount": 715.50, "merchant": "Event Venue", "timestamp": "2024-03-22T16:45:00Z", "status": "completed"},
    {"txn_id": "TXN-20240322-0002", "amount": 159.00, "merchant": "Internet Bill", "timestamp": "2024-03-22T00:00:00Z", "status": "completed"},
    {"txn_id": "TXN-20240323-0001", "amount": 6000.00, "merchant": "Quarterly Bonus", "timestamp": "2024-03-23T12:00:00Z", "status": "completed"}
]

with open('/home/user/audit/march_payments.json', 'w') as f:
    json.dump(payments, f, indent=2)
PYEOF

RUN chmod 0644 /home/user/audit/march_payments.json

WORKDIR /home/user

CMD ["/bin/bash"]
