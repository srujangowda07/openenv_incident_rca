import yaml
from pathlib import Path
import sys

sys.path.insert(0, ".")

cfg = yaml.safe_load(Path("openenv.yaml").read_text(encoding="utf-8"))
tasks = cfg.get("tasks", [])
has_grader = [t for t in tasks if t.get("grader")]
print(f"Total tasks: {len(tasks)}")
print(f"Tasks with graders: {len(has_grader)}")
print(f"type:    {cfg.get('type')}")
print(f"runtime: {cfg.get('runtime')}")
print(f"app:     {cfg.get('app')}")
print(f"port:    {cfg.get('port')}")
print()

from server.app import _TASKS

print(f"/tasks endpoint returns: {len(_TASKS)} tasks")
print(f"tasks_with_graders: {sum(1 for t in _TASKS if t['has_grader'])}")
print(f"Sample task[0]: {_TASKS[0]}")
