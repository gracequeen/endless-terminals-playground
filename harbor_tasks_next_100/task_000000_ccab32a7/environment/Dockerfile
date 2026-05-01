FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    coreutils \
    gawk \
    sed \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/data && chmod 0777 /home/user && chmod 0777 /home/user/data

RUN python3 << 'PYEOF'
import random
import datetime

random.seed(42)

statuses = ['pending', 'completed', 'shipped', 'cancelled', 'processing']

with open('/home/user/data/orders.csv', 'w', encoding='utf-8', newline='\n') as f:
    f.write('order_id,customer_id,order_date,total_amount,status\n')

    for i in range(1, 50001):
        order_id = 1000000 + i
        customer_id = random.randint(10000, 99999)

        start_date = datetime.date(2022, 1, 1)
        random_days = random.randint(0, 730)
        order_date = start_date + datetime.timedelta(days=random_days)

        total_amount = round(random.uniform(5.00, 5000.00), 2)

        status = random.choice(statuses)

        f.write(f'{order_id},{customer_id},{order_date},{total_amount},{status}\n')
PYEOF

RUN chmod 644 /home/user/data/orders.csv

WORKDIR /home/user

CMD ["/bin/bash"]
