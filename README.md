---
title: SQL OpenEnv
emoji: 🗄️
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
  - sql
  - database
  - reinforcement-learning
  - query-optimization
  - real-world
---

# SQL Query Optimization — OpenEnv Environment

> **OpenEnv Hackathon submission** · Built by [Navadeep Nandedapu](https://github.com/NNavadeep05) · IIT Kharagpur

A production-ready OpenEnv environment where AI agents learn to write and optimize SQL queries against a realistic relational database. Designed for the **OpenEnv Hackathon** organized by Meta PyTorch × Scaler × Hugging Face.

---

## Overview

This environment simulates a real-world database querying task that engineers and analysts perform daily. An AI agent receives a database schema and a natural language objective, submits SQL queries as actions, and receives shaped rewards based on syntax validity, schema correctness, result accuracy, and query efficiency.

The environment is built on an in-memory SQLite database with a realistic employee-department-project schema, and exposes a full OpenEnv-compliant HTTP API with three tasks of escalating difficulty.

---

## Environment Details

### Database Schema

```
employees     (id, name, department_id, salary, hire_date, manager_id)
departments   (id, name, budget, location)
projects      (id, name, department_id, start_date, end_date, status)
employee_projects (employee_id, project_id, role, hours_worked)
```

4 departments · 10 employees · 5 projects · 15 project assignments

### Observation Space

| Field | Type | Description |
|-------|------|-------------|
| `task_id` | string | Current task identifier |
| `task_description` | string | Natural language goal |
| `schema_info` | string | Full database schema |
| `last_query` | string \| null | Last SQL query submitted |
| `last_result` | string \| null | Result of last query |
| `last_error` | string \| null | Error message if query failed |
| `step_count` | integer | Steps taken in current episode |
| `max_steps` | integer | Episode length limit (10) |
| `score_so_far` | float | Cumulative reward this episode |

### Action Space

| Field | Type | Description |
|-------|------|-------------|
| `sql_query` | string | A valid SQL SELECT statement |

### Reward Structure

The reward function provides dense, non-sparse signal at every step:

| Signal | Value | Condition |
|--------|-------|-----------|
| Syntax valid | +0.10 | Query executes without error |
| Schema correct | +0.20 | References valid tables and columns |
| Result correct | +0.50 | Result set matches ground truth exactly |
| Partial match | +0.25 | >50% of rows match ground truth |
| Efficiency bonus | +0.20 | Query uses index (no full table scan) |
| Destructive query | −0.30 | DROP / DELETE / UPDATE / INSERT detected |
| Step penalty | −0.05 | Per step beyond step 5 |

All rewards clamped to `[−1.0, 1.0]`.

---

## Tasks

### Task 1 — Easy · Expected baseline score: ~0.82

**Objective:** Find all employees in the Engineering department, returning their name and salary ordered by salary descending.

**Expected columns:** `name`, `salary`

**Grader:** Exact result set match → 1.0 · Valid SQL attempted → 0.5 · No valid SQL → 0.0

---

### Task 2 — Medium · Expected baseline score: ~0.51

**Objective:** For each department, compute the total employee count and average salary. Return only departments where average salary exceeds 60,000, ordered by average salary descending, rounded to 2 decimal places.

**Expected columns:** `department_name`, `employee_count`, `avg_salary`

**Grader:** Exact match → 1.0 · Correct joins attempted → 0.6 · Valid SQL → 0.3 · No valid SQL → 0.0

---

### Task 3 — Hard · Expected baseline score: ~0.23

**Objective:** Find the top 3 employees by total hours worked across all projects. For each, return their name, department, total hours, and salary rank within their department (1 = highest). Include only employees who have worked on at least 2 distinct projects.

**Expected columns:** `name`, `department_name`, `total_hours`, `salary_rank`

**Grader:** Exact match → 1.0 · Window function used → 0.7 · Correct joins + grouping → 0.4 · Valid SQL → 0.2 · No valid SQL → 0.0

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/reset` | Initialize episode, returns initial observation |
| POST | `/step` | Submit SQL action, returns observation + reward |
| GET | `/state` | Current episode state |
| GET | `/tasks` | List all tasks and action schema |
| POST | `/grader` | Score a completed episode |
| POST | `/baseline` | Run GPT-4o-mini baseline against all 3 tasks |

---

## Baseline Scores

Baseline agent: **GPT-4o-mini** via OpenAI API

| Task | Difficulty | Score |
|------|-----------|-------|
| task1 | Easy | 0.82 |
| task2 | Medium | 0.51 |
| task3 | Hard | 0.23 |
| **mean** | — | **0.52** |

---

## Setup & Usage

### Local

```bash
pip install -r requirements.txt
python app.py
# Server starts on http://localhost:7860
```

### Docker

```bash
docker build -t sql-openenv .
docker run -p 7860:7860 -e OPENAI_API_KEY=your_key sql-openenv
```

### Quick Test

```bash
# Reset environment
curl -X POST http://localhost:7860/reset \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task1"}'

# Submit a query
curl -X POST http://localhost:7860/step \
  -H "Content-Type: application/json" \
  -d '{"sql_query": "SELECT e.name, e.salary FROM employees e JOIN departments d ON e.department_id = d.id WHERE d.name = '\''Engineering'\'' ORDER BY e.salary DESC"}'

# Get grader score
curl -X POST http://localhost:7860/grader \
  -H "Content-Type: application/json" \
  -d '{"task_id": "task1"}'
```

### Run Baseline Script

```bash
OPENAI_API_KEY=your_key BASE_URL=https://navadeep45-sql-openenv.hf.space \
  python baseline/inference.py
```

---

## Project Structure

```
sql-openenv/
├── env/
│   ├── environment.py     # Core OpenEnv class — step(), reset(), state()
│   ├── models.py          # Pydantic: Observation, Action, Reward
│   ├── database.py        # SQLite in-memory DB with fixed seed data
│   └── reward.py          # Reward shaping logic
├── tasks/
│   ├── task1_easy.py      # Easy task + deterministic grader
│   ├── task2_medium.py    # Medium task + deterministic grader
│   ├── task3_hard.py      # Hard task + deterministic grader
│   └── __init__.py        # Task registry
├── baseline/
│   └── inference.py       # GPT-4o-mini baseline runner
├── app.py                 # FastAPI server — all endpoints
├── openenv.yaml           # OpenEnv metadata spec
├── Dockerfile             # Container config
└── requirements.txt
```

---

## About

**Author:** Navadeep Nandedapu  
**Institute:** Indian Institute of Technology Kharagpur (IIT KGP)  
**Hackathon:** OpenEnv Hackathon — Round 1 · Meta PyTorch × Scaler × Hugging Face  
**HF Space:** [NaVaDeeP45/SQL-OpenEnv](https://huggingface.co/spaces/NaVaDeeP45/SQL-OpenEnv)  
**GitHub:** [NNavadeep05/SQL-OpenEnv](https://github.com/NNavadeep05/SQL-OpenEnv)
