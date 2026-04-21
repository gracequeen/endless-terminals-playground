I'm working on a support ticket where a user reported that our internal employee directory database is returning wrong results. The SQLite database is at /home/user/company/employees.db and it has a table called `employees` with columns (id INTEGER PRIMARY KEY, name TEXT, department TEXT, email TEXT, salary REAL, hire_date TEXT, manager_id INTEGER).

Here's what I need you to do:

1. First, I need you to find all employees who have a manager_id that doesn't correspond to any existing employee id in the table. These are orphaned records pointing to managers who don't exist. Write these to /home/user/company/orphaned_employees.txt with one employee name per line, sorted alphabetically.

2. The finance team noticed some salary discrepancies. Find all employees whose salary is more than 20% above the average salary of their own department. Create a report at /home/user/company/salary_outliers.csv with columns: id,name,department,salary,dept_average (where dept_average is rounded to 2 decimal places). Sort by department alphabetically, then by salary descending within each department. Include a header row.

3. We suspect there are duplicate email addresses which shouldn't happen. Find any email addresses that appear more than once and write them to /home/user/company/duplicate_emails.txt, one email per line, sorted alphabetically.

4. Finally, I need a department summary at /home/user/company/dept_summary.json as a JSON object where each key is a department name and the value is an object containing:
   - "count": number of employees
   - "avg_salary": average salary rounded to 2 decimal places
   - "oldest_hire": the earliest hire_date in YYYY-MM-DD format
   - "newest_hire": the latest hire_date in YYYY-MM-DD format

The JSON should be pretty-printed with 2-space indentation, and departments should appear in alphabetical order when the file is read top to bottom.

Don't modify the original database — just read from it and create the report files.
