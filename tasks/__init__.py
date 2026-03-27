from tasks.task1_easy import TASK_ID as TASK1_ID, DESCRIPTION as TASK1_DESC, grade as grade_task1, get_ground_truth as gt_task1, DIFFICULTY as TASK1_DIFF
from tasks.task2_medium import TASK_ID as TASK2_ID, DESCRIPTION as TASK2_DESC, grade as grade_task2, get_ground_truth as gt_task2, DIFFICULTY as TASK2_DIFF
from tasks.task3_hard import TASK_ID as TASK3_ID, DESCRIPTION as TASK3_DESC, grade as grade_task3, get_ground_truth as gt_task3, DIFFICULTY as TASK3_DIFF

TASKS = {
    "task1": {"id": TASK1_ID, "description": TASK1_DESC, "difficulty": TASK1_DIFF, "grade": grade_task1, "ground_truth": gt_task1},
    "task2": {"id": TASK2_ID, "description": TASK2_DESC, "difficulty": TASK2_DIFF, "grade": grade_task2, "ground_truth": gt_task2},
    "task3": {"id": TASK3_ID, "description": TASK3_DESC, "difficulty": TASK3_DIFF, "grade": grade_task3, "ground_truth": gt_task3},
}

ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "sql_query": {
            "type": "string",
            "description": "A valid SQL SELECT query to execute against the database"
        }
    },
    "required": ["sql_query"]
}
