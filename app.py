from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from env.environment import SQLEnvironment
from env.models import Action
from tasks import TASKS, ACTION_SCHEMA
import os

app = FastAPI(title="SQL OpenEnv", version="1.0.0")

global_env = None
episode_history = []

class ResetRequest(BaseModel):
    task_id: str = "task1"

class StepRequest(BaseModel):
    sql_query: str

class GraderRequest(BaseModel):
    task_id: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reset")
def reset(request: ResetRequest):
    global global_env, episode_history
    try:
        global_env = SQLEnvironment(task_id=request.task_id)
        episode_history = []
        obs = global_env.reset()
        return obs.model_dump()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/step")
def step(request: StepRequest):
    global global_env, episode_history
    if global_env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized. Call /reset first.")

    action = Action(sql_query=request.sql_query)
    obs, reward, done, info = global_env.step(action)

    episode_history.append((action.model_dump(), reward.model_dump()))

    return {
        "observation": obs.model_dump(),
        "reward": reward.model_dump(),
        "done": done,
        "info": info
    }

@app.get("/state")
def state():
    if global_env is None:
        raise HTTPException(status_code=400, detail="Environment not initialized.")
    return global_env.state()

@app.get("/tasks")
def get_tasks():
    task_list = [{"id": k, "description": v["description"], "difficulty": v["difficulty"]} for k, v in TASKS.items()]
    return {"tasks": task_list, "action_schema": ACTION_SCHEMA}

@app.post("/grader")
def grader(request: GraderRequest):
    if request.task_id not in TASKS:
        raise HTTPException(status_code=400, detail=f"Unknown task_id: {request.task_id}")

    grade_fn = TASKS[request.task_id]["grade"]
    obs = global_env._get_observation() if global_env else None

    score = grade_fn(obs, episode_history)
    return {"task_id": request.task_id, "score": float(score), "max_score": 1.0}

@app.post("/baseline")
def baseline():
    if not os.getenv("OPENAI_API_KEY"):
        return {"error": "OPENAI_API_KEY not set"}

    try:
        scores = {}
        for task_id in ["task1", "task2", "task3"]:
            env = SQLEnvironment(task_id=task_id)
            local_history = []
            obs = env.reset()

            client_scores = _run_baseline_task(env, obs, local_history, task_id)
            grade_fn = TASKS[task_id]["grade"]
            final_obs = env._get_observation()
            scores[task_id] = float(grade_fn(final_obs, local_history))

        scores["mean"] = sum(v for k, v in scores.items() if k != "mean") / 3
        return scores
    except Exception as e:
        return {"error": str(e)}

def _run_baseline_task(env: SQLEnvironment, initial_obs, local_history: list, task_id: str) -> None:
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    SYSTEM_PROMPT = """You are an expert SQL developer.
You will be given a database schema and a task description.
Your job is to write a SQL SELECT query that accomplishes the task.
Respond with ONLY the SQL query, nothing else. No markdown, no explanation.
Start your response directly with SELECT."""

    obs = initial_obs
    for _ in range(10):
        obs_dict = obs.model_dump()
        prompt = f"Schema:\n{obs_dict.get('schema_info', '')}\n\nTask:\n{obs_dict.get('task_description', '')}\n\nStep: {obs_dict.get('step_count', 0)}"
        if obs_dict.get("last_query"):
            prompt += f"\n\nLast Query: {obs_dict['last_query']}"
            if obs_dict.get("last_result"):
                prompt += f"\nLast Result: {obs_dict['last_result'][:500]}"
            if obs_dict.get("last_error"):
                prompt += f"\nLast Error: {obs_dict['last_error']}"

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt[:2000]}
            ]
        )

        sql = response.choices[0].message.content.strip()
        if sql.startswith("```sql"):
            sql = sql[6:]
        if sql.endswith("```"):
            sql = sql[:-3]
        sql = sql.strip()

        action = Action(sql_query=sql)
        obs, reward, done, info = env.step(action)
        local_history.append((action.model_dump(), reward.model_dump()))

        if done:
            break

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
