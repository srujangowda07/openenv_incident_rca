from __future__ import annotations

import json
import os
import time

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from openai import OpenAI

from incident_rca_env.environment.env import IncidentRCAEnv, ActionModel
from incident_rca_env.grader import IncidentRCAGrader
from incident_rca_env.tasks.task_definitions import list_tasks

# Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://integrate.api.nvidia.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "meta/llama-3.3-70b-instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
SEED = int(os.getenv("SEED", "42"))
ENV_NAME = "incident-rca-env"

# Score constants — validator strict range
SCORE_MIN = 0.01
SCORE_MAX = 0.99


# Logging helpers (flush=True on every call)
def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(
    step: int, action: str, reward: float, done: bool, error: str | None
) -> None:
    error_val = error if error else "null"
    done_val = "true" if done else "false"
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
        flush=True,
    )


def log_end(success: bool, steps: int, score: float, rewards: list[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards) if rewards else "0.00"
    success_val = "true" if success else "false"
    print(
        f"[END] success={success_val} steps={steps} score={score:.2f} "
        f"rewards={rewards_str}",
        flush=True,
    )


# Prompt builders
SYSTEM_PROMPT = """You are an expert Site Reliability Engineer performing incident response.
Diagnose the root cause service and failure type, then submit your diagnosis.

Allowed cause_type values:
- "connection pool exhausted"
- "memory leak OOMKilled"
- "disk full no log rotation"
- "missing index slow query"
- "cluster split-brain 2 nodes network partition"
- "persistence file corruption"
- "unbounded temporary files"
- "port misconfiguration"
- "database credentials failure"
- "tls certificate expiry"
- "dns misconfiguration"
- "index corruption"
- "config drift"
- "rate limiter failure"
- "unexpected service failure"

Available actions — respond ONLY with valid JSON:

grep_logs:
{"action_type": "grep_logs", "parameters": {"service": "<name>", "keyword": "<term>"}}

query_metrics:
{"action_type": "query_metrics", "parameters": {"service": "<name>", "metric_name": "<metric>"}}

fetch_traces:
{"action_type": "fetch_traces", "parameters": {"request_id": "<id>"}}

query_dependencies:
{"action_type": "query_dependencies", "parameters": {"service": "<name>"}}

submit_diagnosis:
{"action_type": "submit_diagnosis", "parameters": {"root_cause_service": "<name>", "cause_type": "<description>"}}

Rules:
- Output ONLY valid JSON. No explanation, no markdown, no extra text.
- All parameters are required. Missing parameters incur a penalty.
- metric_name is required for query_metrics.
- Do NOT repeat the same action with the same parameters.
- Avoid unnecessary actions — each step must provide new information.
- Call submit_diagnosis as soon as strong evidence is found.

Strategy:
1. Identify the alerting service from the "ALERTS" section.
2. Use query_dependencies on the alerting service to find its exact upstream dependencies.
3. IMPORTANT: Use EXACT service names as listed in the dependency graph (e.g., use 'mysql-repl' if listed, not just 'mysql').
4. If an upstream dependency exists, investigate it IMMEDIATELY. Trace the chain until you find the terminal service that has evidence of failure.
5. Do NOT diagnose a "victim" service (one that is just failing because its dependency is down). Only diagnose the root cause service.
6. Only call submit_diagnosis when you have physical evidence (from logs or metrics) of a specific failure mode in the list.
7. If logs of a suspected service are empty, check its metrics for saturation or errors.
"""


def _build_prompt(obs: dict, step: int) -> str:
    history_lines = ""
    for h in obs.get("history", [])[-3:]:
        history_lines += (
            f"\n  {h.get('action')}({h.get('parameters', {})}) "
            f"-> reward={h.get('reward', 0):+.2f}"
        )
    return (
        f"STEP {step} of {obs.get('max_steps', 25)}\n\n"
        f"TASK:\n{obs.get('task_description', '')}\n\n"
        f"ALERTS:\n{json.dumps(obs.get('alerts', []), indent=2)}\n\n"
        f"LAST TOOL RESULT:\n{json.dumps(obs.get('tool_result'), indent=2)}\n\n"
        f"HISTORY:{history_lines if history_lines else ' none'}\n\n"
        f"Respond with JSON only."
    )


# LLM client 
class ParseError(ValueError):
    pass


def _validate_config() -> None:
    if not API_BASE_URL or API_BASE_URL in ("", "base_url"):
        raise ValueError("API_BASE_URL is not set")
    if not MODEL_NAME or MODEL_NAME in ("", "model_name"):
        raise ValueError("MODEL_NAME is not set")
    if not HF_TOKEN:
        raise ValueError("HF_TOKEN is not set")


def _call_llm(messages: list[dict]) -> str:
    _validate_config()
    client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN, timeout=30.0)
    last_err = None
    backoff = 5.0
    for i in range(10):  
        try:
            resp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=messages,
                temperature=0.1,
                max_tokens=256,  
            )
            return resp.choices[0].message.content
        except Exception as e:
            last_err = e
            if "429" in str(e):
                time.sleep(backoff)
                backoff *= 2.0
            else:
                time.sleep(2.0)
    raise RuntimeError(f"LLM call failed after 10 retries: {last_err}")


def _parse_action(raw: str) -> ActionModel:
    valid_actions = {
        "grep_logs",
        "query_metrics",
        "fetch_traces",
        "query_dependencies",
        "submit_diagnosis",
    }
    raw = raw.strip().replace("```json", "").replace("```", "")
    start = raw.find("{")
    end = raw.rfind("}")
    if start == -1 or end == -1:
        raise ParseError("No JSON object found. Reply with ONLY a JSON object.")

    try:
        data = json.loads(raw[start : end + 1])
    except json.JSONDecodeError as exc:
        raise ParseError(
            f"Invalid JSON: {exc}. Fix syntax and reply with JSON only."
        ) from exc

    action_type = data.get("action_type")
    if not action_type:
        raise ParseError(
            'Missing "action_type". Example: {"action_type": "grep_logs", ...}'
        )
    if action_type not in valid_actions:
        raise ParseError(
            f'Unknown action_type "{action_type}". Valid: {sorted(valid_actions)}'
        )

    params = data.get("parameters", {})
    if action_type == "submit_diagnosis":
        if not params.get("root_cause_service") or not params.get("cause_type"):
            raise ParseError(
                "submit_diagnosis requires root_cause_service and cause_type."
            )
    if action_type == "query_metrics" and not params.get("metric_name"):
        raise ParseError("query_metrics requires service and metric_name.")

    return ActionModel(action_type=action_type, parameters=params)


def _format_action_str(action: ActionModel) -> str:
    parts = ", ".join(f"{k}={v}" for k, v in action.parameters.items())
    return f"{action.action_type}({parts})"


def _get_selected_tasks(all_tasks: list[dict]) -> list[dict]:
    max_tasks_env = os.getenv("MAX_TASKS")
    if max_tasks_env:
        try:
            limit = int(max_tasks_env)
            return all_tasks[:limit]
        except ValueError:
            pass

    # Default balanced selection: 3 Easy, 2 Medium, 2 Hard
    easy_tasks = [t for t in all_tasks if t["difficulty"] == "easy"][:3]
    medium_tasks = [t for t in all_tasks if t["difficulty"] == "medium"][:2]
    hard_tasks = [t for t in all_tasks if t["difficulty"] == "hard"][:2]
    
    selected = easy_tasks + medium_tasks + hard_tasks
    return selected


def main():
    all_tasks = list_tasks()
    tasks = _get_selected_tasks(all_tasks)
    grader = IncidentRCAGrader()

    for task in tasks:
        task_id = task["id"]
        log_start(task=task_id, env=ENV_NAME, model=MODEL_NAME)

        env = IncidentRCAEnv(task_id=task_id, seed=SEED)
        obs = env.reset()
        obs_dict = obs.model_dump()

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        rewards = []

        step = 0
        done = False
        info = None

        try:
            for step in range(1, task.get("max_steps", 25) + 1):
                if done:
                    break

                messages.append({"role": "user", "content": _build_prompt(obs_dict, step)})

                raw_response = _call_llm(messages)
                messages.append({"role": "assistant", "content": raw_response})

                try:
                    action = _parse_action(raw_response)
                except ParseError as pe:
                    log_step(step, "parse_error", 0.0, False, str(pe))
                    continue

                obs, reward, done, info = env.step(action)
                obs_dict = obs.model_dump()

                reward_val = getattr(reward, "total", 0.0)
                rewards.append(reward_val)
                action_str = _format_action_str(action)

                log_step(step, action_str, reward_val, done, None)

                if done:
                    break

        except Exception as e:
            log_step(step, "execution_error", 0.0, False, str(e))

        # Grade the episode
        try:
            score = grader.grade(env)
        except Exception:
            score = 0.01
            
        # Ensure score is within valid range strictly
        score = float(score)
        if score <= 0.0:
            score = 0.01
        if score >= 1.0:
            score = 0.99
            
        success = score >= 0.60
        log_end(
            success=success,
            steps=step,
            score=score,
            rewards=rewards,
        )


if __name__ == "__main__":
    main()
