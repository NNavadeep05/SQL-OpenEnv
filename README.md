# SQL Query Optimization — OpenEnv Environment

## Overview
This is a comprehensive OpenEnv-compliant environment designed to train AI agents in writing and optimizing SQL queries. Built on an in-memory SQLite database, it evaluates agents based on syntax validity, schema adherence, outcome correctness, and query efficiency. 

It is highly useful for training RL agents as it provides non-sparse, detailed, shaped rewards at every step, allowing models to learn incremental improvements while protecting state boundaries. The continuous feedback loop helps an agent quickly identify common SQL errors and adjust query plans, avoiding expensive full table scans.

## Observation Space
The `Observation` model tracks the agent's current interaction context:
- `task_id` (string): Current task identifier.
- `task_description` (string): Natural language description of what to fetch.
- `schema_info` (string): Full database schema dump.
- `last_query` (string, nullable): The last complete SQL query submitted.
- `last_result` (string, nullable): Parsed result of the latest execution, stringified for simple processing.
- `last_error` (string, nullable): Python traceback or error if the last request failed parsing/execution.
- `step_count` (integer): How many actions evaluated this episode.
- `max_steps` (integer): The bound (10) preventing infinite episodes.
- `score_so_far` (number): The cumulative ongoing reward tally.

## Action Space
The structured action to take within the loop:
- `sql_query` (string): A valid SQL SELECT statement.

## Reward Structure
The evaluator determines shaped scalar returns clamped securely against range `[-1.0, 1.0]`:
- Syntax valid: +0.10
- Schema correct: +0.20
- Result correct: +0.50
- Efficiency bonus: +0.20
- Destructive query: -0.30
- Step penalty (>5 steps): -0.05 per step

## Tasks
### Task 1 (Easy) - ~0.8 expected baseline score
Write a simple SQL command fetching employees associated directly with the Engineering department layout, sorting primarily by income.
### Task 2 (Medium) - ~0.5 expected baseline score  
Determine comprehensive statistics across interconnected relational domains matching an aggregate HAVING condition.
### Task 3 (Hard) - ~0.2 expected baseline score
Compile ranked representations using CTE formulations and PARTITION calculations mapped onto complex hours worked variables.

## Setup & Usage
### Local
```bash
pip install -r requirements.txt
python app.py
```
### Docker
```bash
docker build -t sql-openenv .
docker run -p 7860:7860 -e OPENAI_API_KEY=your_key sql-openenv
```
### Run Baseline
```bash
OPENAI_API_KEY=your_key python baseline/inference.py
```

## Baseline Scores
| Task | Difficulty | Baseline Score (GPT-4o-mini) |
|------|-----------|------------------------------|
| task1 | Easy | 0.82 |
| task2 | Medium | 0.51 |
| task3 | Hard | 0.23 |
| mean | - | 0.52 |
