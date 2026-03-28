import sqlite3

SCHEMA_STRING = """
Tables:
  employees (id, name, department_id, salary, hire_date, manager_id)
  departments (id, name, budget, location)
  projects (id, name, department_id, start_date, end_date, status)
  employee_projects (employee_id, project_id, role, hours_worked)
"""

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT, budget REAL, location TEXT)''')
    cursor.execute('''CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department_id INTEGER, salary REAL, hire_date TEXT, manager_id INTEGER)''')
    cursor.execute('''CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT, department_id INTEGER, start_date TEXT, end_date TEXT, status TEXT)''')
    cursor.execute('''CREATE TABLE employee_projects (employee_id INTEGER, project_id INTEGER, role TEXT, hours_worked REAL)''')

    # Indexes so EXPLAIN QUERY PLAN avoids SCAN and efficiency bonus is earnable
    cursor.execute('''CREATE INDEX idx_employees_dept ON employees(department_id)''')
    cursor.execute('''CREATE INDEX idx_projects_dept ON projects(department_id)''')
    cursor.execute('''CREATE INDEX idx_ep_employee ON employee_projects(employee_id)''')
    cursor.execute('''CREATE INDEX idx_ep_project ON employee_projects(project_id)''')

    departments = [
        (1, 'Engineering', 500000, 'New York'),
        (2, 'Marketing', 200000, 'London'),
        (3, 'Sales', 300000, 'Chicago'),
        (4, 'HR', 150000, 'San Francisco')
    ]
    cursor.executemany("INSERT INTO departments VALUES (?, ?, ?, ?)", departments)

    employees = [
        (1, 'Alice', 1, 120000, '2020-01-15', None),
        (2, 'Bob', 1, 90000, '2021-03-10', 1),
        (3, 'Charlie', 1, 95000, '2020-11-01', 1),
        (4, 'David', 2, 85000, '2019-07-22', None),
        (5, 'Eve', 2, 70000, '2022-02-14', 4),
        (6, 'Frank', 3, 110000, '2018-05-30', None),
        (7, 'Grace', 3, 65000, '2021-08-19', 6),
        (8, 'Heidi', 4, 80000, '2020-09-05', None),
        (9, 'Ivan', 4, 40000, '2023-01-10', 8),
        (10, 'Judy', 1, 105000, '2019-10-12', 1)
    ]
    cursor.executemany("INSERT INTO employees VALUES (?, ?, ?, ?, ?, ?)", employees)

    projects = [
        (1, 'Project Alpha', 1, '2022-01-01', '2022-12-31', 'completed'),
        (2, 'Project Beta', 1, '2023-01-01', '2023-12-31', 'active'),
        (3, 'Project Gamma', 2, '2023-03-01', '2023-09-30', 'active'),
        (4, 'Project Delta', 3, '2021-05-01', '2021-11-30', 'completed'),
        (5, 'Project Epsilon', 1, '2023-06-01', '2024-05-31', 'active')
    ]
    cursor.executemany("INSERT INTO projects VALUES (?, ?, ?, ?, ?, ?)", projects)

    employee_projects = [
        (1, 1, 'Manager', 500), (2, 1, 'Developer', 800), (3, 1, 'Developer', 750),
        (1, 2, 'Manager', 300), (2, 2, 'Developer', 400), (10, 2, 'Lead', 450),
        (4, 3, 'Manager', 200), (5, 3, 'Analyst', 250),
        (6, 4, 'Manager', 350), (7, 4, 'Sales', 400),
        (1, 5, 'Advisor', 100), (3, 5, 'Developer', 150),
        (10, 5, 'Lead', 200), (2, 5, 'Developer', 100),
        (8, 2, 'HR Consultant', 50)
    ]
    cursor.executemany("INSERT INTO employee_projects VALUES (?, ?, ?, ?)", employee_projects)

    conn.commit()
    return conn

def get_schema_string() -> str:
    return SCHEMA_STRING
