TASK_ID = "task3"
DIFFICULTY = "hard"
DESCRIPTION = """
Find the top 3 employees by total hours worked across all projects.
For each, return their name, department name, total hours worked, and their 
salary rank within their department (1 = highest salary in dept).
Only include employees who have worked on at least 2 different projects.
Expected columns: name, department_name, total_hours, salary_rank
"""

GROUND_TRUTH_QUERY = """
WITH employee_hours AS (
    SELECT e.id, e.name, d.name as department_name, e.salary, e.department_id,
           SUM(ep.hours_worked) as total_hours,
           COUNT(DISTINCT ep.project_id) as project_count
    FROM employees e
    JOIN departments d ON e.department_id = d.id
    JOIN employee_projects ep ON e.id = ep.employee_id
    GROUP BY e.id, e.name, d.name, e.salary, e.department_id
    HAVING COUNT(DISTINCT ep.project_id) >= 2
),
ranked AS (
    SELECT name, department_name, total_hours,
           RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) as salary_rank
    FROM employee_hours
)
SELECT name, department_name, total_hours, salary_rank
FROM ranked
ORDER BY total_hours DESC
LIMIT 3
"""

def get_ground_truth(conn) -> list:
    cursor = conn.cursor()
    cursor.execute(GROUND_TRUTH_QUERY)
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def grade(final_observation, episode_history) -> float:
    any_syntax_valid = False
    used_window = False
    used_joins = False
    
    for action, reward in episode_history:
        if reward.get("result_correct"):
            return 1.0
        if reward.get("syntax_valid"):
            any_syntax_valid = True
            query = action.get("sql_query", "").upper()
            if "OVER" in query and "PARTITION" in query and ("WITH" in query or "(SELECT" in query):
                used_window = True
            if "JOIN" in query and "GROUP BY" in query:
                used_joins = True
                
    if used_window:
        return 0.7
    if used_joins:
        return 0.4
    if any_syntax_valid:
        return 0.2
    return 0.0
