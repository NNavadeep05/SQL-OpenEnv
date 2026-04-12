"""
SQL OpenEnv baseline inference script.

Required environment variables:
- API_BASE_URL: API endpoint for the LLM proxy.
- API_KEY: API key for the LLM proxy.
- MODEL_NAME: model identifier to use for inference.
- ENV_BASE_URL: SQL OpenEnv server URL.
"""

from __future__ import annotations

import json
import os
from typing import Any

import requests
from openai import OpenAI

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "meta-llama/Llama-3.1-8B-Instruct")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:7860")

REQUEST_TIMEOUT = 30
TASK_IDS = ["task1", "task2", "task3"]

SYSTEM_PROMPT = """You are an expert SQL developer.
You will be given a database schema and a task description.
Your job is to write a SQL SELECT query that accomplishes the task.
Respond with ONLY the SQL query, nothing else. No markdown, no explanation.
Start your response directly with SELECT."""


def log_event(kind: str, payload: dict[str, Any]) -> None:
    print(f"[{kind}] {json.dumps(payload, separators=(',', ':'), ensure_ascii=True)}", flush=True)


def build_prompt(obs: dict[str, Any]) -> str:
    prompt = (
        f"Schema:\n{obs.get('schema_info', '')}\n\n"
        f"Task:\n{obs.get('task_description', '')}\n\n"
        f"Step: {obs.get('step_count', 0)}"
    )
    if obs.get("last_query"):
        prompt += f"\n\nLast Query: {obs['last_query']}"
        if obs.get("last_result"):
            prompt += f"\nLast Result: {str(obs['last_result'])[:1000]}"
        if obs.get("last_error"):
            prompt += f"\nLast Error: {obs['last_error']}"
    return prompt[:2000]


def post_json(session: requests.Session, path: str, payload: dict[str, Any]) -> dict[str, Any]:
    response = session.post(f"{ENV_BASE_URL}{path}", json=payload, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object from {path}, got {type(data).__name__}")
    return data


def extract_sql(response: Any) -> str:
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


def generate_sql(client: OpenAI, obs: dict[str, Any]) -> str:
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": build_prompt(obs)},
        ],
    )
    sql = extract_sql(response)
    if not sql:
        raise ValueError("Parsed SQL was empty")
    return sql


def run_task(client: OpenAI | None, session: requests.Session, task_id: str, task_index: int, total_tasks: int) -> float:
    log_event("START", {
        "task_id": task_id,
        "task_index": task_index,
        "total_tasks": total_tasks,
        "model_name": MODEL_NAME,
        "api_base_url": API_BASE_URL,
    })

    step_count = 0
    try:
        obs = post_json(session, "/reset", {"task_id": task_id})
        max_steps = int(obs.get("max_steps", 10))
    except Exception as exc:
        log_event("END", {"task_id": task_id, "score": 0.0, "steps": 0, "status": "error", "error": str(exc)})
        return 0.0

    while step_count < max_steps:
        step_count += 1
        sql_query = "SELECT 1"
        step_error = None

        try:
            if client is None:
                raise ValueError("No client available")
            sql_query = generate_sql(client, obs)
        except Exception as exc:
            step_error = str(exc)

        done = False
        reward_value = 0.0

        try:
            step_res = post_json(session, "/step", {"sql_query": sql_query})
            obs = step_res.get("observation", obs)
            reward = step_res.get("reward", {}) if isinstance(step_res.get("reward"), dict) else {}
            reward_value = float(reward.get("value", 0.0))
            done = bool(step_res.get("done", False))
        except Exception as exc:
            step_error = str(exc)
            done = True

        step_payload = {
            "task_id": task_id,
            "step": step_count,
            "sql_query": sql_query,
            "reward": reward_value,
            "done": done,
        }
        if step_error:
            step_payload["error"] = step_error
        log_event("STEP", step_payload)

        if done:
            break

    score = 0.0
    end_status = "ok"
    end_error = None
    try:
        grade_res = post_json(session, "/grader", {"task_id": task_id})
        score = float(grade_res.get("score", 0.0))
    except Exception as exc:
        end_status = "error"
        end_error = str(exc)

    end_payload = {"task_id": task_id, "score": score, "steps": step_count, "status": end_status}
    if end_error:
        end_payload["error"] = end_error
    log_event("END", end_payload)
    return score


def main() -> dict[str, float]:
    client = None
    try:
        api_key = API_KEY or "no-key"
        api_base = API_BASE_URL.rstrip("/") + "/"
        client = OpenAI(base_url=api_base, api_key=api_key)
    except Exception as exc:
        print(f"[ERROR] Failed to create client: {exc}", flush=True)

    session = requests.Session()
    scores: dict[str, float] = {}

    for index, task_id in enumerate(TASK_IDS, start=1):
        try:
            scores[task_id] = run_task(client, session, task_id, index, len(TASK_IDS))
        except Exception as exc:
            print(f"[ERROR] Task {task_id} failed: {exc}", flush=True)
            scores[task_id] = 0.0

    scores["mean"] = sum(v for k, v in scores.items() if k != "mean") / len(TASK_IDS)
    return scores


if __name__ == "__main__":
    main()
