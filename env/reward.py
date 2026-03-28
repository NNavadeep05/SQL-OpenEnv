import sqlite3
import re
from typing import Optional
from env.models import Reward

VALID_TABLES = ["employees", "departments", "projects", "employee_projects"]
VALID_COLUMNS = [
    "id", "name", "department_id", "salary", "hire_date", "manager_id",
    "budget", "location", "start_date", "end_date", "status",
    "employee_id", "project_id", "role", "hours_worked"
]

def compute_reward(
    sql_query: str,
    execution_result: Optional[list],
    execution_error: Optional[str],
    ground_truth: list,
    conn: sqlite3.Connection,
    step_count: int
) -> Reward:
    query_upper = sql_query.upper()
    destructive_keywords = ["DROP", "DELETE", "TRUNCATE", "UPDATE", "INSERT", "ALTER", "CREATE"]

    if any(keyword in query_upper for keyword in destructive_keywords):
        return Reward(
            value=-0.3, syntax_valid=False, schema_correct=False, result_correct=False,
            efficiency_bonus=False, penalty_applied=True, breakdown={"penalty": -0.3}
        )

    reward_value = 0.0
    breakdown = {}

    syntax_valid = (execution_error is None)
    if syntax_valid:
        reward_value += 0.10
        breakdown["syntax_valid"] = 0.10
    else:
        breakdown["syntax_valid"] = 0.0

    # Check both table names AND column names for a meaningful schema_correct signal
    query_lower = sql_query.lower()
    words = set(re.findall(r'\b[a-zA-Z_]\w*\b', query_lower))
    table_match = any(table in words for table in VALID_TABLES)
    column_match = any(col in words for col in VALID_COLUMNS)

    if table_match and column_match:
        schema_correct = True
        reward_value += 0.20
        breakdown["schema_correct"] = 0.20
    else:
        schema_correct = False
        breakdown["schema_correct"] = 0.0

    result_correct = False
    if syntax_valid and execution_result is not None:
        def stringify_row(row):
            return {str(k): str(v) for k, v in row.items()}

        ex_res = sorted([stringify_row(r) for r in execution_result], key=lambda x: str(x))
        gt_res = sorted([stringify_row(r) for r in ground_truth], key=lambda x: str(x))

        if ex_res == gt_res:
            result_correct = True
            reward_value += 0.50
            breakdown["result_correct"] = 0.50
        else:
            common = [row for row in ex_res if row in gt_res]
            if len(gt_res) > 0 and (len(common) / len(gt_res)) > 0.5:
                reward_value += 0.25
                breakdown["result_correct"] = 0.25
            else:
                breakdown["result_correct"] = 0.0
    else:
        breakdown["result_correct"] = 0.0

    efficiency_bonus = False
    if syntax_valid:
        try:
            cursor = conn.cursor()
            cursor.execute("EXPLAIN QUERY PLAN " + sql_query)
            plan = cursor.fetchall()
            plan_str = " ".join([str(row) for row in plan]).upper()
            if "SCAN" not in plan_str:
                efficiency_bonus = True
                reward_value += 0.20
                breakdown["efficiency_bonus"] = 0.20
            else:
                breakdown["efficiency_bonus"] = 0.0
        except:
            breakdown["efficiency_bonus"] = 0.0
    else:
        breakdown["efficiency_bonus"] = 0.0

    step_penalty = 0.0
    if step_count > 5:
        step_penalty = (step_count - 5) * 0.05
        reward_value -= step_penalty
    breakdown["step_penalty"] = -step_penalty

    reward_value = max(-1.0, min(1.0, reward_value))

    return Reward(
        value=reward_value,
        syntax_valid=syntax_valid,
        schema_correct=schema_correct,
        result_correct=result_correct,
        efficiency_bonus=efficiency_bonus,
        penalty_applied=False,
        breakdown=breakdown
    )
