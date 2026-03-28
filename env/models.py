from pydantic import BaseModel
from typing import Optional

class Observation(BaseModel):
    task_id: str
    task_description: str
    schema_info: str
    last_query: Optional[str] = None
    last_result: Optional[str] = None
    last_error: Optional[str] = None
    step_count: int
    max_steps: int
    score_so_far: float

class Action(BaseModel):
    sql_query: str

class Reward(BaseModel):
    value: float
    syntax_valid: bool
    schema_correct: bool
    result_correct: bool
    efficiency_bonus: bool
    penalty_applied: bool
    breakdown: dict
