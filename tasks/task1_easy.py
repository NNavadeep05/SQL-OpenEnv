TASK_ID = "task1"
DIFFICULTY = "easy"
DESCRIPTION = """
Find all employees in the Engineering department.
Return their name and salary, ordered by salary descending.
Expected columns: name, salary
"""

GROUND_TRUTH_QUERY = """
SELECT e.name, e.salary 
FROM employees e
JOIN departments d ON e.department_id = d.id
WHERE d.name = 'Engineering'
ORDER BY e.salary DESC
"""

def get_ground_truth(conn) -> list:
    cursor = conn.cursor()
    cursor.execute(GROUND_TRUTH_QUERY)
    columns = [desc[0] for desc in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]

def grade(final_observation, episode_history) -> float:
    any_syntax_valid = False
    for action, reward in episode_history:
        if reward.get("result_correct"):
            return 1.0
        if reward.get("syntax_valid"):
            any_syntax_valid = True
    
    if any_syntax_valid:
        return 0.5
    return 0.0
