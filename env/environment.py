import sqlite3
import threading
from typing import Optional
from env.models import Observation, Action, Reward
from env.database import get_connection, get_schema_string
from env.reward import compute_reward
from tasks import TASKS

class SQLEnvironment:
    MAX_STEPS = 10

    def __init__(self, task_id: str = "task1"):
        if task_id not in TASKS:
            raise ValueError(f"Unknown task_id: {task_id}")
        self.task_id = task_id
        self.task_info = TASKS[task_id]
        self.conn = get_connection()
        self.ground_truth = self.task_info["ground_truth"](self.conn)
        self.step_count = 0
        self.score_so_far = 0.0
        self.last_query = None
        self.last_result = None
        self.last_error = None

    def reset(self) -> Observation:
        self.conn.close()
        self.conn = get_connection()
        self.ground_truth = self.task_info["ground_truth"](self.conn)
        self.step_count = 0
        self.score_so_far = 0.0
        self.last_query = None
        self.last_result = None
        self.last_error = None
        
        return self._get_observation()

    def step(self, action: Action) -> tuple[Observation, Reward, bool, dict]:
        self.step_count += 1
        self.last_query = action.sql_query
        
        result, error = self._execute_query(action.sql_query)
        self.last_result = str(result) if result is not None else None
        self.last_error = error

        reward = compute_reward(
            sql_query=action.sql_query,
            execution_result=result,
            execution_error=error,
            ground_truth=self.ground_truth,
            conn=self.conn,
            step_count=self.step_count
        )
        
        self.score_so_far += reward.value
        
        done = (self.step_count >= self.MAX_STEPS) or reward.result_correct
        
        obs = self._get_observation()
        info = {
            "task_id": self.task_id,
            "step": self.step_count,
            "done_reason": "max_steps" if self.step_count >= self.MAX_STEPS else ("success" if reward.result_correct else "none")
        }
        
        return obs, reward, done, info

    def state(self) -> dict:
        return {
            "task_id": self.task_id,
            "step_count": self.step_count,
            "score_so_far": self.score_so_far,
            "max_steps": self.MAX_STEPS,
            "current_task_description": self.task_info["description"],
            "done": (self.step_count >= self.MAX_STEPS) or (self.score_so_far > 0),
            "last_query": self.last_query,
            "last_error": self.last_error
        }

    def _get_observation(self) -> Observation:
        return Observation(
            task_id=self.task_id,
            task_description=self.task_info["description"],
            schema_info=get_schema_string(),
            last_query=self.last_query,
            last_result=self.last_result,
            last_error=self.last_error,
            step_count=self.step_count,
            max_steps=self.MAX_STEPS,
            score_so_far=self.score_so_far
        )

    def _execute_query(self, sql: str) -> tuple[Optional[list], Optional[str]]:
        result = None
        error = None
        cursor = self.conn.cursor()
        
        def run_query():
            nonlocal result, error
            try:
                cursor.execute(sql)
                if cursor.description:
                    columns = [desc[0] for desc in cursor.description]
                    result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                else:
                    result = []
            except Exception as e:
                error = str(e)

        thread = threading.Thread(target=run_query)
        thread.start()
        thread.join(timeout=5.0)
        
        if thread.is_alive():
            error = "Execution timeout: query took more than 5 seconds"
        
        return result, error
