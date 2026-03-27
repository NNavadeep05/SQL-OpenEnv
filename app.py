from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn
from env.environment import SQLEnvironment
from env.models import Action
from tasks import TASKS, ACTION_SCHEMA
from baseline.inference import run_task, main as run_baseline
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
        scores = run_baseline()
        return scores
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
