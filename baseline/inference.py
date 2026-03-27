"""
Baseline inference script. 
Usage: python baseline/inference.py
Requires: OPENAI_API_KEY environment variable
Optionally: BASE_URL env var (default: http://localhost:7860)
"""

import os
import json
import requests
from openai import OpenAI

SYSTEM_PROMPT = """You are an expert SQL developer. 
You will be given a database schema and a task description.
Your job is to write a SQL SELECT query that accomplishes the task.
Respond with ONLY the SQL query, nothing else. No markdown, no explanation.
Start your response directly with SELECT."""

def build_prompt(obs: dict) -> str:
    prompt = f"Schema:\n{obs.get('schema_info', '')}\n\nTask:\n{obs.get('task_description', '')}\n\nStep: {obs.get('step_count', 0)}"
    if obs.get('last_query'):
        prompt += f"\n\nLast Query: {obs['last_query']}"
        if obs.get('last_result'):
            prompt += f"\nLast Result: {obs['last_result'][:1000]}"
        if obs.get('last_error'):
            prompt += f"\nLast Error: {obs['last_error']}"
    return prompt[:2000]

def run_task(task_id: str) -> float:
    base_url = os.getenv("BASE_URL", "http://localhost:7860")
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    try:
        # 1. POST /reset
        res = requests.post(f"{base_url}/reset", json={"task_id": task_id}).json()
        
        obs = res
        for _ in range(10):
            # Build prompt
            prompt = build_prompt(obs)
            
            # Call GPT-4o-mini
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ]
            )
            
            sql = response.choices[0].message.content.strip()
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.endswith("```"):
                sql = sql[:-3]
            sql = sql.strip()
            
            # POST /step
            step_res = requests.post(f"{base_url}/step", json={"sql_query": sql}).json()
            obs = step_res["observation"]
            if step_res.get("done"):
                break
                
        # POST /grader
        grade_res = requests.post(f"{base_url}/grader", json={"task_id": task_id}).json()
        return grade_res.get("score", 0.0)
    except Exception as e:
        print(f"Error running {task_id}: {e}")
        return 0.0

def main():
    scores = {}
    for task_id in ["task1", "task2", "task3"]:
        print(f"Running {task_id}...")
        score = run_task(task_id)
        scores[task_id] = score
        print(f"  Score: {score:.3f}")
    
    mean = sum(scores.values()) / len(scores)
    scores["mean"] = mean
    print(f"\nBaseline Results:")
    print(json.dumps(scores, indent=2))
    return scores

if __name__ == "__main__":
    main()
