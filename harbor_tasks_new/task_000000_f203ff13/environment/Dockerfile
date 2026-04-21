FROM ubuntu:22.04

# Install required packages
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Install pytest
RUN pip3 install pytest

# Create /home/user directory with appropriate permissions
RUN mkdir -p /home/user && chmod 0777 /home/user

# Create /home/user/company directory with appropriate permissions
RUN mkdir -p /home/user/company && chmod 0777 /home/user/company

# Create the SQLite database with the employees table and data
RUN sqlite3 /home/user/company/employees.db "CREATE TABLE employees ( \
    id INTEGER PRIMARY KEY, \
    name TEXT, \
    department TEXT, \
    email TEXT, \
    salary REAL, \
    hire_date TEXT, \
    manager_id INTEGER \
);" && \
sqlite3 /home/user/company/employees.db "INSERT INTO employees VALUES \
(1, 'Alice Johnson', 'Engineering', 'alice@company.com', 95000.00, '2019-03-15', NULL), \
(2, 'Bob Smith', 'Engineering', 'bob@company.com', 87000.00, '2020-06-01', 1), \
(3, 'Carol White', 'Engineering', 'carol@company.com', 145000.00, '2018-01-10', 1), \
(4, 'David Brown', 'Sales', 'david@company.com', 72000.00, '2021-02-20', 10), \
(5, 'Eve Davis', 'Sales', 'eve@company.com', 68000.00, '2022-07-12', 10), \
(6, 'Frank Miller', 'Sales', 'frank@company.com', 115000.00, '2017-11-05', 999), \
(7, 'Grace Lee', 'HR', 'grace@company.com', 62000.00, '2020-09-30', 9), \
(8, 'Henry Wilson', 'HR', 'henry@company.com', 58000.00, '2023-01-15', 9), \
(9, 'Ivy Chen', 'HR', 'ivy@company.com', 78000.00, '2016-04-22', NULL), \
(10, 'Jack Taylor', 'Sales', 'jack@company.com', 82000.00, '2019-08-08', 1), \
(11, 'Karen Moore', 'Engineering', 'karen@company.com', 91000.00, '2021-05-17', 1), \
(12, 'Leo Martinez', 'Finance', 'leo@company.com', 76000.00, '2020-03-03', 14), \
(13, 'Mia Garcia', 'Finance', 'mia@company.com', 71000.00, '2022-11-28', 14), \
(14, 'Noah Anderson', 'Finance', 'noah@company.com', 88000.00, '2018-07-19', NULL), \
(15, 'Olivia Thomas', 'Finance', 'olivia@company.com', 125000.00, '2015-12-01', 14), \
(16, 'Paul Jackson', 'Engineering', 'paul@company.com', 89000.00, '2023-04-10', 1), \
(17, 'Quinn Harris', 'Marketing', 'quinn@company.com', 65000.00, '2021-10-05', 500), \
(18, 'Rachel Clark', 'Marketing', 'rachel@company.com', 63000.00, '2022-02-14', 500), \
(19, 'Sam Lewis', 'Marketing', 'sam@company.com', 98000.00, '2019-06-20', NULL), \
(20, 'Tina Robinson', 'Engineering', 'bob@company.com', 92000.00, '2020-08-25', 1), \
(21, 'Uma Walker', 'HR', 'grace@company.com', 60000.00, '2023-03-08', 9), \
(22, 'Victor Hall', 'Sales', 'victor@company.com', 70000.00, '2021-12-12', 10), \
(23, 'Wendy Young', 'Finance', 'wendy@company.com', 73000.00, '2022-05-30', 14), \
(24, 'Xavier King', 'Marketing', 'xavier@company.com', 61000.00, '2023-07-01', 19);"

# Set proper permissions on the database file
RUN chmod 0666 /home/user/company/employees.db

# Set working directory
WORKDIR /home/user
