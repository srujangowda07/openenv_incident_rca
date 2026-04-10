"""
Deep audit script — checks for ALL silent killers that could fail platform validation.
Run: python deep_audit.py
"""
import sys
import traceback
import yaml
import importlib
from pathlib import Path

ROOT = Path(__file__).parent
PASS = []
FAIL = []


def check(name, fn):
    try:
        result = fn()
        if result is True or result is None:
            PASS.append(name)
            print(f"  PASS  {name}")
        else:
            FAIL.append((name, str(result)))
            print(f"  FAIL  {name}: {result}")
    except Exception as e:
        FAIL.append((name, str(e)))
        print(f"  FAIL  {name}: {e}")


print("\n=== DEEP SILENT KILLER AUDIT ===\n")

# ── 1. YAML structure ───────────────────────────────────────────
print("[1] openenv.yaml")
cfg = yaml.safe_load((ROOT / "openenv.yaml").read_text(encoding="utf-8"))

check("spec_version present", lambda: True if "spec_version" in cfg else "MISSING spec_version")
check("name present", lambda: True if cfg.get("name") else "MISSING name")
check("tasks is a list", lambda: True if isinstance(cfg.get("tasks"), list) else f"tasks type={type(cfg.get('tasks')).__name__}")
check("17 tasks defined", lambda: True if len(cfg.get("tasks", [])) == 17 else f"got {len(cfg.get('tasks', []))} tasks")
check("3 difficulty levels", lambda: True if len({t.get("difficulty") for t in cfg.get("tasks", [])}) == 3 else "not 3 difficulties")

tasks = cfg.get("tasks", [])
for t in tasks:
    tid = t.get("id", "?")
    check(f"task '{tid}' has grader field", lambda t=t, tid=tid: True if t.get("grader") else f"MISSING grader on {tid}")
    check(f"task '{tid}' grader is entrypoint", lambda t=t, tid=tid:
        True if ":" in str(t.get("grader", "")) else f"grader is NOT a python entrypoint: '{t.get('grader')}'")

# ── 2. Grader importability ─────────────────────────────────────
print("\n[2] graders.grader:grade importability")

def check_grader_import():
    mod = importlib.import_module("graders.grader")
    fn = getattr(mod, "grade", None)
    if fn is None or not callable(fn):
        return "grade() not callable in graders.grader"
    # Actually call it with a minimal payload
    result = fn({"scenario": {"root_cause": {"service": "test-svc", "cause_type": "test"}},
                 "final_state": {"diagnosed_service": "test-svc", "diagnosed_cause": "test", "action_history": []},
                 "info": {"invalid_actions": 0}})
    if not hasattr(result, "score"):
        return f"grade() returned {type(result).__name__} (expected GradeResult)"
    if not (0.0 <= result.score <= 1.0):
        return f"score {result.score} out of [0, 1]"
    return True

check("graders.grader:grade imports and runs", check_grader_import)

# ── 3. Server app imports ────────────────────────────────────────
print("\n[3] server.app imports")

def check_app_import():
    mod = importlib.import_module("server.app")
    app = getattr(mod, "app", None)
    if app is None:
        return "server.app has no 'app' object"
    main_fn = getattr(mod, "main", None)
    if main_fn is None or not callable(main_fn):
        return "server.app has no callable main()"
    return True

check("server.app imports OK (app + main)", check_app_import)

# ── 4. Environment class ─────────────────────────────────────────
print("\n[4] IncidentRCAEnvironment")

def check_env_reset():
    from server.incident_rca_env_environment import IncidentRCAEnvironment
    env = IncidentRCAEnvironment()
    obs = env.reset()
    if obs is None:
        return "reset() returned None"
    if not hasattr(obs, "done"):
        return "ObservationModel missing 'done'"
    if not hasattr(obs, "reward"):
        return "ObservationModel missing 'reward'"
    if not hasattr(obs, "metadata"):
        return "ObservationModel missing 'metadata'"
    if obs.reward is None:
        return "reset() obs.reward is None (should be 0.0)"
    if obs.metadata is None:
        return "reset() obs.metadata is None (should be {})"
    return True

check("reset() returns valid ObservationModel", check_env_reset)

def check_env_health():
    from server.incident_rca_env_environment import IncidentRCAEnvironment
    from openenv.core.env_server.types import EnvironmentMetadata
    env = IncidentRCAEnvironment()
    meta = env.get_metadata()
    if not isinstance(meta, EnvironmentMetadata):
        return f"get_metadata() returns {type(meta).__name__} (expected EnvironmentMetadata)"
    if not meta.name:
        return "metadata.name is empty"
    if not meta.description:
        return "metadata.description is empty"
    return True

check("get_metadata() returns EnvironmentMetadata", check_env_health)

def check_env_state():
    from server.incident_rca_env_environment import IncidentRCAEnvironment
    from openenv.core.env_server.types import State
    env = IncidentRCAEnvironment()
    env.reset()
    s = env.state
    if not isinstance(s, State):
        return f"state is {type(s).__name__} (expected State)"
    return True

check("state property returns State object", check_env_state)

# ── 5. Models inherit from OpenEnv base ─────────────────────────
print("\n[5] Pydantic model compliance")

def check_action_model():
    from models import ActionModel
    from openenv.core.env_server.types import Action
    if not issubclass(ActionModel, Action):
        return f"ActionModel does NOT inherit from openenv Action"
    return True

def check_obs_model():
    from models import ObservationModel
    from openenv.core.env_server.types import Observation
    if not issubclass(ObservationModel, Observation):
        return f"ObservationModel does NOT inherit from openenv Observation"
    return True

check("ActionModel inherits from openenv Action", check_action_model)
check("ObservationModel inherits from openenv Observation", check_obs_model)

# ── 6. pyproject.toml ───────────────────────────────────────────
print("\n[6] pyproject.toml")

try:
    import tomllib
except ImportError:
    import tomli as tomllib

def check_pyproject():
    data = tomllib.loads((ROOT / "pyproject.toml").read_bytes().decode())
    scripts = data.get("project", {}).get("scripts", {})
    if "server" not in scripts:
        return "MISSING [project.scripts] server entry"
    if ":main" not in scripts["server"]:
        return f"server entry '{scripts['server']}' does not reference :main"
    deps = [d.lower() for d in data.get("project", {}).get("dependencies", [])]
    has_openenv = any("openenv" in d for d in deps)
    if not has_openenv:
        return "MISSING openenv/openenv-core in dependencies"
    return True

check("pyproject.toml scripts + deps OK", check_pyproject)

# ── 7. Dockerfile ───────────────────────────────────────────────
print("\n[7] Dockerfile")

def check_dockerfile():
    content = (ROOT / "Dockerfile").read_text()
    issues = []
    if "EXPOSE 7860" not in content and "EXPOSE 8000" not in content:
        issues.append("no EXPOSE directive")
    if "HEALTHCHECK" not in content:
        issues.append("no HEALTHCHECK")
    if "server.app:app" not in content:
        issues.append("CMD does not reference server.app:app")
    if "PYTHONPATH" not in content:
        issues.append("PYTHONPATH not set")
    return True if not issues else " | ".join(issues)

check("Dockerfile structure OK", check_dockerfile)

# ── 8. Required files ───────────────────────────────────────────
print("\n[8] Required files")
for fname in ["openenv.yaml", "Dockerfile", "README.md", "pyproject.toml", "uv.lock",
              "server/app.py", "graders/grader.py", "models.py", "graders/__init__.py"]:
    check(f"{fname} exists", lambda f=fname: True if (ROOT / f).exists() else f"MISSING: {f}")

# ── 9. README.md app_port ───────────────────────────────────────
print("\n[9] README.md")

def check_readme():
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    issues = []
    if "app_port:" not in content and "sdk_version:" not in content:
        issues.append("README may be missing HuggingFace Space header")
    if "7860" not in content:
        issues.append("port 7860 not mentioned in README")
    return True if not issues else " | ".join(issues)

check("README has HF Space header with port 7860", check_readme)

# ── Summary ─────────────────────────────────────────────────────
total = len(PASS) + len(FAIL)
print(f"\n{'='*50}")
print(f"  {len(PASS)}/{total} checks passed")
if FAIL:
    print(f"\n  FAILURES FOUND ({len(FAIL)}):")
    for name, err in FAIL:
        print(f"    - {name}: {err}")
    sys.exit(1)
else:
    print("  All checks passed. No silent killers found.")
