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
    return {
        "id": task_id,
        "grader": task.get("grader", ""),
        "has_grader": bool(task.get("grader", "")),
        "name": task.get("name", task_id.replace("_", " ").title()),
        "difficulty": difficulty,
        "max_steps": max_steps,
        "description": task.get("description", ""),
    }


def _load_tasks_from_openenv() -> dict[str, dict]:
    cfg_path = Path.cwd() / "openenv.yaml"
    if not cfg_path.exists():
        # Fallback if standard execution directory is not root
        cfg_path = Path(__file__).resolve().parents[2] / "openenv.yaml"
        
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))
    tasks = cfg.get("tasks", [])
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
