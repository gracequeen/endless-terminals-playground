FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    rsync \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user && chmod 0777 /home/user

RUN mkdir -p /home/user/reports/q1 \
    && mkdir -p /home/user/reports/q2 \
    && mkdir -p /home/user/backup

RUN echo "product,quantity,price" > /home/user/reports/summary.csv \
    && echo "Widget A,100,9.99" >> /home/user/reports/summary.csv \
    && echo "Widget B,250,14.99" >> /home/user/reports/summary.csv

RUN echo "date,product,amount,region" > /home/user/reports/q1/sales.csv \
    && echo "2024-01-15,Widget A,50,North" >> /home/user/reports/q1/sales.csv \
    && echo "2024-02-20,Widget B,75,South" >> /home/user/reports/q1/sales.csv

RUN echo "item,stock,warehouse" > /home/user/reports/q1/inventory.csv \
    && echo "Widget A,500,WH1" >> /home/user/reports/q1/inventory.csv \
    && echo "Widget B,300,WH2" >> /home/user/reports/q1/inventory.csv

RUN echo "date,product,amount,region" > /home/user/reports/q2/sales.csv \
    && echo "2024-04-10,Widget A,60,East" >> /home/user/reports/q2/sales.csv \
    && echo "2024-05-22,Widget B,90,West" >> /home/user/reports/q2/sales.csv

RUN echo "PK fake xlsx content scratch" > /home/user/reports/scratch.xlsx

RUN echo "PK fake xlsx content sales draft q1" > /home/user/reports/q1/sales_draft.xlsx

RUN echo "PK fake xlsx content notes q2" > /home/user/reports/q2/notes.xlsx

RUN chmod -R 0777 /home/user

WORKDIR /home/user

CMD ["/bin/bash"]
