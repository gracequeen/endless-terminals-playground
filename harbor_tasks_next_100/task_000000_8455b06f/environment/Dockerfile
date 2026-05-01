FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    sqlite3 \
    python3 \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install pytest

RUN mkdir -p /home/user/data && chmod 0777 /home/user && chmod 0777 /home/user/data

RUN sqlite3 /home/user/data/inventory.db "CREATE TABLE products (id INTEGER PRIMARY KEY, name TEXT, price REAL, quantity INTEGER);" && \
    sqlite3 /home/user/data/inventory.db "INSERT INTO products (name, price, quantity) VALUES ('Widget A', 19.99, 100);" && \
    sqlite3 /home/user/data/inventory.db "INSERT INTO products (name, price, quantity) VALUES ('Widget B', 29.99, 50);" && \
    sqlite3 /home/user/data/inventory.db "INSERT INTO products (name, price, quantity) VALUES ('Gadget X', 49.99, 25);" && \
    sqlite3 /home/user/data/inventory.db "INSERT INTO products (name, price, quantity) VALUES ('Gadget Y', 99.99, 10);" && \
    sqlite3 /home/user/data/inventory.db "INSERT INTO products (name, price, quantity) VALUES ('Tool Z', 14.99, 200);" && \
    chmod 0666 /home/user/data/inventory.db

WORKDIR /home/user

CMD ["/bin/bash"]
