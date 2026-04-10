"""
Simulates the platform Phase 2 validator logic for 'Not enough tasks with graders'.
Run: python simulate_platform_validator.py
"""
# -*- coding: utf-8 -*-
import yaml
import sys
import importlib

print("=" * 60)
print("PLATFORM PHASE 2 VALIDATOR SIMULATION")
print("=" * 60)

# Step 1: Load the YAML
with open("openenv.yaml") as f:
    cfg = yaml.safe_load(f)

print("\n[1] YAML structure check")
print(f"    tasks type: {type(cfg.get('tasks')).__name__}")
tasks_raw = cfg.get("tasks", [])
print(f"    tasks count: {len(tasks_raw)}")

# Step 2: Check if 'graders' key exists at top level
print("\n[2] Graders section check")
graders = cfg.get("graders", {})
print(f"    graders key present: {'graders' in cfg}")
print(f"    grader names: {list(graders.keys()) if isinstance(graders, dict) else 'N/A'}")

# Step 3: Walk each task and check grader linkage
print("\n[3] Per-task grader linkage check")
tasks_with_graders = []
tasks_without_graders = []

if isinstance(tasks_raw, list):
    for task in tasks_raw:
        tid = task.get("id", "???")
        g = task.get("grader", None)
        if not g:
            tasks_without_graders.append(tid)
            print(f"    FAIL {tid}: NO grader field")
        else:
            resolved = False
            if ":" in str(g):
                # Python entrypoint format (e.g. graders.grader:grade)
                try:
                    module_path, func_name = g.rsplit(":", 1)
                    mod = importlib.import_module(module_path)
                    fn = getattr(mod, func_name, None)
                    resolved = fn is not None and callable(fn)
                    if not resolved:
                        print(f"    FAIL {tid}: grader='{g}' entrypoint found but function missing")
                except Exception as e:
                    resolved = False
                    print(f"    FAIL {tid}: grader='{g}' ENTRYPOINT UNRESOLVABLE: {e}")
            elif isinstance(graders, dict) and g in graders:
                # Named reference (e.g. rca_grader)
                named = graders[g]
                ep = named.get("entrypoint", "")
                if ":" in ep:
                    try:
                        module_path, func_name = ep.rsplit(":", 1)
                        mod = importlib.import_module(module_path)
                        fn = getattr(mod, func_name, None)
                        resolved = fn is not None and callable(fn)
                        if not resolved:
                            print(f"    FAIL {tid}: graders.{g}.entrypoint='{ep}' function not callable")
                    except Exception as e:
                        resolved = False
                        print(f"    FAIL {tid}: grader='{g}' -> '{ep}' UNRESOLVABLE: {e}")
                else:
                    resolved = False
                    print(f"    FAIL {tid}: grader='{g}' exists but has no valid entrypoint")
            else:
                resolved = False
                print(f"    FAIL {tid}: grader='{g}' NOT FOUND in graders section")

            if resolved:
                tasks_with_graders.append(tid)
                print(f"    PASS {tid}: grader='{g}' -> RESOLVED OK")
            else:
                tasks_without_graders.append(tid)

elif isinstance(tasks_raw, dict):
    for tid, task in tasks_raw.items():
        g = task.get("grader", None)
        if g:
            tasks_with_graders.append(tid)
            print(f"    PASS {tid}: grader='{g}'")
        else:
            tasks_without_graders.append(tid)
            print(f"    FAIL {tid}: NO grader field")

# Step 4: Final verdict
print(f"\n[4] RESULTS")
print(f"    Tasks with valid graders:  {len(tasks_with_graders)}")
print(f"    Tasks without graders:     {len(tasks_without_graders)}")
print(f"    Tasks failing: {tasks_without_graders[:10] if tasks_without_graders else 'None'}")
print()
if len(tasks_with_graders) >= 3:
    print("    >>> PASS: Would pass Phase 2 'Not enough tasks with graders'")
else:
    print("    >>> FAIL: Would FAIL Phase 2 'Not enough tasks with graders'")
    sys.exit(1)
