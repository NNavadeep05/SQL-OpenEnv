"""
Baseline inference script.
Usage: python inference.py
Requires: OPENAI_API_KEY environment variable
Optionally: BASE_URL env var (default: http://localhost:7860)
"""

import json
import os

import requests
from openai import OpenAI

REQUEST_TIMEOUT = 30

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


def post_json(session: requests.Session, url: str, payload: dict) -> dict:
    response = session.post(url, json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object from {url}, got {type(data).__name__}")
    return data


def extract_sql(response) -> str:
    choices = getattr(response, "choices", None) or []
    if not choices:
        raise ValueError("Model response did not include any choices")

    message = getattr(choices[0], "message", None)
    content = getattr(message, "content", None)
    if not isinstance(content, str) or not content.strip():
        raise ValueError("Model response content was empty")

    sql = content.strip()
    if sql.startswith("```sql"):
        sql = sql[6:]
    elif sql.startswith("```"):
        sql = sql[3:]
    if sql.endswith("```"):
        sql = sql[:-3]
    return sql.strip()


def run_task(task_id: str) -> float:
    base_url = os.getenv("BASE_URL", "http://localhost:7860")
    api_key = os.getenv("OPENAI_API_KEY")

    try:
        if not api_key:
            raise ValueError("OPENAI_API_KEY is not set")

        client = OpenAI(api_key=api_key)
        session = requests.Session()

        # 1. POST /reset
        res = post_json(session, f"{base_url}/reset", {"task_id": task_id})
        if "task_description" not in res:
            raise ValueError("Reset response is missing observation fields")

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
            
            sql = extract_sql(response)
            if not sql:
                raise ValueError("Parsed SQL was empty")

            # POST /step
            step_res = post_json(session, f"{base_url}/step", {"sql_query": sql})
            if "observation" not in step_res:
                raise ValueError("Step response is missing observation")

            obs = step_res["observation"]
            if step_res.get("done"):
                break

        # POST /grader
        grade_res = post_json(session, f"{base_url}/grader", {"task_id": task_id})
        score = grade_res.get("score", 0.0)
        return float(score)
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
