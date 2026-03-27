TASK_ID = "task2"
DIFFICULTY = "medium"
DESCRIPTION = """
For each department, find the total number of employees and the average salary.
Only include departments where the average salary is above 60000.
Return department name, employee count, and average salary rounded to 2 decimal places.
Expected columns: department_name, employee_count, avg_salary
"""

GROUND_TRUTH_QUERY = """
SELECT d.name as department_name, 
       COUNT(e.id) as employee_count,
       ROUND(AVG(e.salary), 2) as avg_salary
FROM departments d
JOIN employees e ON d.id = e.department_id
GROUP BY d.id, d.name
HAVING AVG(e.salary) > 60000
ORDER BY avg_salary DESC
"""

def get_ground_truth(conn) -> list:
    cursor = conn.cursor()
    cursor.execute(GROUND_TRUTH_QUERY)
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def grade(final_observation, episode_history) -> float:
    any_syntax_valid = False
    any_schema_correct = False
    for action, reward in episode_history:
        if reward.get("result_correct"):
            return 1.0
        if reward.get("schema_correct"):
            any_schema_correct = True
        if reward.get("syntax_valid"):
            any_syntax_valid = True
            
    if any_schema_correct:
        return 0.6
    if any_syntax_valid:
        return 0.3
    return 0.0
