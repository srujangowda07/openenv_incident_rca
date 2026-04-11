---
title: Incident RCA Env
sdk: docker
app_port: 7860
base_path: /web
---

# IncidentRCAEnv

OpenEnv-compliant RL environment for training and evaluating agents on incident response and root cause analysis in production-like microservice systems.

Built for the Meta x Hugging Face x PyTorch OpenEnv Hackathon 2026.

IncidentRCAEnv simulates realistic outage investigation with logs, metrics, traces, and service dependencies under partial observability.
It matters because production debugging quality directly impacts reliability, incident cost, and on-call engineer load.
What makes it unique: deterministic multi-step evaluation with strict action semantics, reward shaping, and reproducible grading.

## Live Demo

- Hugging Face Space: https://huggingface.co/spaces/srujan0001/env_incident_rca
- Web UI: https://srujan0001-env-incident-rca.hf.space/web/
- GitHub: https://github.com/srujangowda07/openenv_incident_rca

## Problem Statement

Production outages directly impact reliability, cost, and engineering productivity. Engineers must analyze logs, metrics, and dependencies under time pressure to identify root causes.

This environment models incident response using a controlled, deterministic microservice system. It enables training and evaluating agents that can diagnose failures through structured investigation rather than guesswork.

## Why This Is Challenging

- **Partial observability** — agents do not see the full system state upfront
- **Multi-step reasoning** — diagnosis requires sequential investigation
- **Dependency tracing** — failures propagate across services
- **Noisy signals** — not all observations directly indicate the root cause
- **Efficiency trade-offs** — excessive actions reduce the final score

## Example Investigation (Step-by-step)

A realistic investigation flow mirrors SRE debugging:

1. **query_logs** (`grep_logs`) on the alerting service to identify first-order symptoms.
2. **trace_dependency** (`query_dependencies`) to follow upstream/downstream blast radius.
3. **check_metrics** (`query_metrics`) on likely failing services for confirmation signals.
4. **identify root cause** by combining log signatures + metric anomalies + dependency path.
5. **submit diagnosis** (`submit_diagnosis`) with `root_cause_service` and `cause_type`.

This sequence rewards evidence-driven diagnosis and penalizes guesswork/repetition.

## Environment Design

### Observation Space

The agent receives a structured JSON observation at each step:

| Field | Type | Description |
|---|---|---|
| `step` | int | Current step number |
| `max_steps` | int | Step budget for the task |
| `task_id` | str | Task identifier |
| `task_description` | str | Incident description |
| `alerts` | list[dict] | Active alerts triggering investigation |
| `tool_result` | dict \| null | Output of the last action |
| `history` | list[dict] | Recent actions and outcomes |
| `available_actions` | list[str] | Valid actions |
| `done` | bool | Episode completion flag |

The environment is partially observable — agents must use actions to uncover relevant information. Observations are revealed incrementally based on what the agent investigates.

The environment does not expose the root cause directly — agents must infer it through interaction.

### Action Space

Five atomic actions represent real-world debugging tools:

| Action | Required Parameters | Description |
|---|---|---|
| `grep_logs` | `service`, `keyword` | Search logs for a service |
| `query_metrics` | `service`, `metric_name` | Retrieve a specific metric |
| `fetch_traces` | `request_id` | Retrieve a distributed trace |
| `query_dependencies` | `service` | Get upstream and downstream dependencies |
| `submit_diagnosis` | `root_cause_service`, `cause_type` | Submit final diagnosis (ends episode) |

All parameters are required and strictly validated. Invalid or missing parameters result in a `-0.10` penalty.

## Reward Function

Rewards are step-based and fully deterministic.

```
Action                           Reward    Condition
────────────────────────────────────────────────────────────────
submit_diagnosis (perfect)       +1.00     correct service and cause type
submit_diagnosis (partial)       +0.50     correct service, wrong cause type
submit_diagnosis (wrong)         -0.50     incorrect service

grep_logs        (cascade)       +0.05     service is in the failure cascade
query_metrics    (cascade)       +0.05     service is in the failure cascade
fetch_traces     (root cause)    +0.10     trace implicates root cause service
query_dependencies (cascade)     +0.05     service is in the failure cascade

repeated action                  -0.10     exact same call made twice
invalid action                   -0.10     missing required parameter or unknown service
step penalty                     -0.01     applied every step
```

This design ensures:
- Agents must follow a correct reasoning path.
- Efficient behavior is rewarded.
- Reward hacking through repetition is prevented.

## Tasks

### Easy — Single-service failures (≤3 services, 15 steps)

| Task | Scenario | Root Cause |
|---|---|---|
| `easy_001` | API gateway returning 502 errors | `postgres-primary` — connection pool exhausted |
| `easy_002` | Payment service pods crashing | `payment-service` — memory leak, unbounded cache |
| `easy_003` | Logging service not ingesting | `logging-service` — disk full, log rotation disabled |
| `easy_004` | Redis container crash loop | `redis-cache` — persistence file corruption |
| `easy_005` | Storage node disk capacity 100% | `storage-node-3` — clean job failure |
| `easy_006` | Auth-service unreachable on port 8080 | `auth-service` — TargetPort mismatch in k8s service |
| `easy_007` | Billing DB authentication failure | `billing-db` — password rotation without secret update |

---

### Medium — Dependency cascade (6–7 services, 25 steps)

| Task | Scenario | Root Cause |
|---|---|---|
| `medium_001` | Two services degraded simultaneously | `mysql-primary` — schema migration dropped index |
| `medium_002` | Connection pool saturation under load | `order-service` — peak traffic exceeded default |
| `medium_003` | Steady heap growth in engine | `recommendation-engine` — static reference leak |
| `medium_004` | API Gateway TLS certificate expired | `api-gateway` — cert-manager renewal challenge fail |
| `medium_005` | Internal DNS resolution failure | `internal-proxy` — CoreDNS configmap corruption |

---

### Hard — Complex cascading failure (10 services, 40 steps, red herrings)

| Task | Scenario | Root Cause |
|---|---|---|
| `hard_001` | Five services failing simultaneously | `redis-cluster` — split-brain from network partition |
| `hard_002` | Data inconsistency in user reporting | `mysql-repl` — Innodb index corruption |
| `hard_003` | Etcd cluster split-brain | `etcd` — multi-AZ link failure |
| `hard_004` | Inconsistent k8s mesh routing | `gateway` — Istio config drift during deployment |
| `hard_005` | Global throttle-service overflow | `throttle-svc` — integer overflow in token bucket |

## Grader

This project natively utilizes a dual-grading system to optimize reliability and API costs:

**1. Production Grader (Hackathon Validator)**
The official Phase 2 OpenEnv platform evaluates trajectories directly via its internal LLM, reading `openenv.yaml`. It analyzes the agent's interaction logic, tool usage, investigation quality, and diagnostic correctness to yield a strict dynamically-ranged score between 0.1 and 0.9.

**2. Local Testing Grader (`grader.py`)**
For high-speed baseline testing, evaluation runs securely via a hardcoded deterministic Python system without pinging LLMs. It compares structural diagnosis against the exact scenario ground truth.

| Dimension | Weight | Local Criteria |
|---|---|---|
| Root cause service | 0.50 | Exact match on service name |
| Cause type | 0.30 | Exact match (only awarded if service is also correct) |
| Tool evidence | 0.20 | Agent queried root cause service before diagnosing |
| Penalties | var. | `-0.10` per invalid action · `-0.20` for wrong diagnosis |

**Pass threshold: 0.60 / 0.90**

## Score Distribution

To abide by platform rules against purely discrete perfect/failure matrices, we restrict scores strictly within [0.1, 0.9]:

| Agent Quality | Score Range |
|---|---|
| Incorrect (random/guessing) | 0.10 – 0.40 |
| Partial (finds service, wrong cause) | 0.45 – 0.60 |
| Correct but Inefficient (poor tools) | 0.65 – 0.80 |
| Excellent (correct + cause + efficient) | 0.85 – 0.90 |

## Design Principles

- **Deterministic** — same input produces the same output every run
- **Minimal** — five actions, no redundancy, clear semantics
- **Causal** — realistic cause–effect relationships across services
- **Measurable** — every action has a defined impact on score
- **Reproducible** — fixed seeds ensure consistent evaluation

## System Flow

1. Environment initializes a deterministic incident scenario
2. Agent observes alerts and limited context
3. Agent performs investigation actions (logs, metrics, traces, dependencies)
4. Environment reveals information incrementally based on each action
5. Agent submits final diagnosis
6. Grader evaluates correctness and reasoning evidence

## Architecture

![Visual Architecture](assets/architecture.png)

## System Architecture (Simple Flow)

```text
Agent -> API -> OpenEnv -> Env -> Grader
```

- **Agent** decides the next investigation action.
- **API** receives/returns structured action-observation payloads.
- **OpenEnv** enforces environment interface and runtime contracts.
- **Env** executes incident logic (`reset`, `step`, `state`).
- **Grader** computes deterministic final scoring.

## What Makes This Environment Unique

- **Production realism with strict structure**: outages are modeled across logs, metrics, traces, and service dependencies.
- **Deterministic benchmarking**: same seed, same trajectory, reproducible scores.
- **Reasoning-first evaluation**: rewards evidence collection, not just final guesses.
- **Action discipline**: penalties for invalid/repeated actions enforce investigation quality.
- **OpenEnv-native deployment**: validate/push workflow works directly for reproducible evaluation.

## Environment Variables

The following environment variables are required:

- `API_BASE_URL` — endpoint of the LLM provider
- `MODEL_NAME` — model identifier
- `HF_TOKEN` — API key for authentication
- `TASK_ID` — task identifier to run
- `SEED` — optional run seed

Valid `TASK_ID` values:
- **Easy**: `easy_001` to `easy_007`
- **Medium**: `medium_001` to `medium_005`
- **Hard**: `hard_001` to `hard_005`

Example `.env` configuration:
```env
API_BASE_URL=https://integrate.api.nvidia.com/v1
MODEL_NAME=meta/llama-3.3-70b-instruct
HF_TOKEN=your_nvidia_api_key

TASK_ID=easy_001
SEED=42
```

## Quickstart

```bash
git clone https://github.com/srujangowda07/openenv_incident_rca.git
cd openenv_incident_rca

# install dependencies
uv sync

# run server
uvicorn incident_rca_env.server.app:app --host 0.0.0.0 --port 7860

# validate environment
openenv validate

# run agent (optional)
python inference.py
```

### Python SDK

```python
from incident_rca_env.environment.env import IncidentRCAEnv
from incident_rca_env.models import ActionModel

env = IncidentRCAEnv(task_id="easy_001", seed=42)
obs = env.reset("easy_001")

# Investigate
action = ActionModel(
    action_type="grep_logs",
    parameters={"service": "postgres-primary", "keyword": "connection"},
)
obs, reward, done, info = env.step(action)
print(f"Reward: {reward:+.3f}")

# Query a metric
action = ActionModel(
    action_type="query_metrics",
    parameters={"service": "postgres-primary", "metric_name": "active_connections"},
)
obs, reward, done, info = env.step(action)

# Submit diagnosis (ends episode)
action = ActionModel(
    action_type="submit_diagnosis",
    parameters={
        "root_cause_service": "postgres-primary",
        "cause_type": "connection pool exhausted",
    },
)
obs, reward, done, info = env.step(action)
print(f"Final reward: {reward:+.3f}")
print("Ground truth:", info.ground_truth_root_cause)
```

## Baseline Results (Deterministic Policy)

We use a deterministic scripted baseline (no LLM) to ensure:

* reproducibility across runs
* stable evaluation (no API variability)
* fair comparison against reasoning-based agents

| Task       | Score      | Pass |
| ---------- | ---------- | ---- |
| easy_001   | ~0.65–0.75 | ✓    |
| easy_002   | ~0.60–0.70 | ✓    |
| easy_003   | ~0.60–0.70 | ✓    |
| medium_001 | ~0.50–0.65 | ✓    |
| hard_001   | ~0.40–0.55 | ✗    |

### Interpretation

* Baseline reliably identifies root cause services
* Often fails to infer exact cause types
* Performance degrades on multi-service cascades

This provides a stable lower bound for evaluating agent reasoning ability.

## Agent Performance (LLM-based)

Using a reasoning-driven LLM agent:

| Task   | Score      | Steps |
| ------ | ---------- | ----- |
| easy   | ~0.95–1.00 | 3–5   |
| medium | ~0.95–1.00 | 5–8   |
| hard   | ~0.95–1.00 | 3–7   |

### Key Observations

* Correct root cause identification across all tasks
* Efficient investigation (low step count)
* Robust handling of cascading failures

### Comparison

| System   | Avg Score |
| -------- | --------- |
| Baseline | ~0.60     |
| Agent    | ~0.95     |

→ The agent significantly outperforms the baseline by leveraging multi-step reasoning across logs, metrics, and dependencies.

## Project Structure

```text
.
├── models.py                   # Required by OpenEnv, re-exports from package
├── openenv.yaml                # Environment schema and tasks
├── Dockerfile                  # Container image definition
├── pyproject.toml              # Project metadata & dependencies
├── inference.py                # LLM agent inference script
├── validate.py                 # Structure validation script
├── verify_tasks.py             # Task verification script
└── incident_rca_env/           # Main package
    ├── __init__.py
    ├── grader.py               # Deterministic grade calculator
    ├── models.py               # Core Pydantic models
    ├── environment/            # Core RL environment logic
    │   ├── __init__.py
    │   ├── env.py              # IncidentRCAEnv implementation
    │   ├── canonical.py
    │   ├── reward_shaper.py
    │   ├── scenario_generator.py
    │   └── state_manager.py
    ├── server/                 # FastAPI / OpenEnv interface
    │   ├── __init__.py
    │   ├── app.py              # Main API entrypoint
    │   └── incident_rca_env_environment.py # Environment platform wrapper
    └── tasks/                  # Task definitions
        ├── __init__.py
        └── task_definitions.py
```

### OpenEnv Note: Missing Models Compliance
A critical requirement of the OpenEnv CLI validation (`openenv push`) is the existence of a pure `models.py` file directly at the root of the repository. Because this project utilizes a professional namespace package structure (`incident_rca_env/`), an intentional root-level `models.py` is bundled strictly as a re-export layer: `from incident_rca_env.models import *`. This ensures full compliance with the strict OpenEnv schema parser without compromising clean project architecture.

## OpenEnv Integration

This environment is fully compatible with OpenEnv:

* Standard reset / step / state API
* HTTP server via FastAPI
* Deployable via Hugging Face Spaces
* Compatible with EnvClient for evaluation

Validation:

```bash
openenv validate → PASSED
```

Deployment:

```bash
openenv push --repo-id <your-repo>
```

## Evaluation Compatibility

This environment fully conforms to OpenEnv Phase 2 requirements:

* Supports `env.reset(task_id)` API
* Supports multi-step interaction via `env.step(action)`
* Includes ≥3 tasks with deterministic graders
* Grader returns a float score (0–1)
* Fully containerized and reproducible

## Why This Matters (Real World Impact)

This project focuses on evaluating reasoning quality, not just final answers. It provides a structured, reproducible benchmark for training agents that can navigate multi-step diagnostic workflows — the same workflows on-call engineers perform under pressure during production incidents.

A well-trained agent that reduces mean time to resolution (MTTR), even marginally, translates directly to fewer outages, lower costs, and less engineer burnout.

This environment prioritizes reliable evaluation over complexity, making it a strong benchmark for reasoning-driven agents.
