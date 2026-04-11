from __future__ import annotations

from pathlib import Path

import yaml


MAX_STEPS_BY_DIFFICULTY = {
    "easy": 15,
    "medium": 25,
    "hard": 40,
}


def _difficulty_from_task_id(task_id: str) -> str:
    return task_id.split("_", 1)[0]


def _build_task_record(task: dict) -> dict:
    task_id = task["id"]
    difficulty = _difficulty_from_task_id(task_id)
    max_steps = task.get("max_steps") or MAX_STEPS_BY_DIFFICULTY.get(difficulty, 25)
    
    raw_grader = task.get("grader")
    if isinstance(raw_grader, str):
        grader = raw_grader
    else:
        raw_grader = raw_grader or {}
        grader = {
            "type": raw_grader.get("type") or "llm",
            "prompt_template": raw_grader.get("prompt_template") or (
                "Score the agent 0.9 if fully correct, 0.5 if partially correct, 0.1 otherwise. Output only a number."
            ),
        }

    return {
        "id": task_id,
        "grader": grader,
        "has_grader": True,
        "name": task.get("name", task_id.replace("_", " ").title()),
        "difficulty": difficulty,
        "max_steps": max_steps,
        "description": task.get("description", ""),
        "actions": task.get("actions", []),
        "max_reward": task.get("max_reward", 1.0),
    }


import os

def _load_tasks_from_openenv() -> dict[str, dict]:
    possible_paths = [
        Path(os.environ.get("OPENENV_YAML_PATH", "openenv.yaml")).resolve(),
        Path.cwd() / "openenv.yaml",
        Path(__file__).resolve().parents[2] / "openenv.yaml",
        Path("/app/openenv.yaml"),  # CRITICAL FIX
    ]

    cfg_path = None
    for path in possible_paths:
        if path.exists():
            cfg_path = path
            break

    if cfg_path is None:
        raise FileNotFoundError(
            "openenv.yaml not found in any expected location:\n"
            + "\n".join(str(p) for p in possible_paths)
        )

    print(f"[DEBUG] Loading openenv.yaml from: {cfg_path}")

    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    tasks = cfg.get("tasks", [])

    if not tasks:
        raise ValueError("No tasks found in openenv.yaml")

    return {task["id"]: _build_task_record(task) for task in tasks}


TASKS = _load_tasks_from_openenv()


def get_task(task_id: str) -> dict:
    if task_id not in TASKS:
        raise KeyError(f"Task '{task_id}' not found. Available: {list(TASKS.keys())}")
    return TASKS[task_id]


def list_tasks(difficulty: str | None = None) -> list[dict]:
    tasks = list(TASKS.values())
    if difficulty:
        tasks = [t for t in tasks if t["difficulty"] == difficulty]
    return tasks
