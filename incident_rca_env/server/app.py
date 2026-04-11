"""
OpenEnv server entry point.

Fixes applied:
1. Removed conflicting /health and / routes
2. Adds /tasks endpoint — required for Phase 2 hackathon validation
3. get_metadata() override returning proper name/description
4. main() entry point for multi-mode deployment compliance
"""

import yaml
import uvicorn
from pathlib import Path
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.types import EnvironmentMetadata
from incident_rca_env.models import ActionModel, ObservationModel, TaskDetail
from incident_rca_env.server.incident_rca_env_environment import IncidentRCAEnvironment


def _get_metadata(self) -> EnvironmentMetadata:
    return EnvironmentMetadata(
        name="incident-rca-env",
        description=(
            "Reinforcement learning environment for training AI agents to perform "
            "incident response and root cause analysis on production microservice systems."
        ),
        version="1.0.0",
        author="Srujan Gowda",
    )


IncidentRCAEnvironment.get_metadata = _get_metadata  # type: ignore[method-assign]


def _load_tasks_from_yaml() -> list:
    """Load tasks from task_definitions to ensure consistency."""
    from incident_rca_env.tasks.task_definitions import list_tasks
    return list_tasks()


# Create the base OpenEnv FastAPI app
app = create_app(
    IncidentRCAEnvironment,
    ActionModel,
    ObservationModel,
    env_name="incident_rca_env",
    max_concurrent_envs=1,
)


# --- Add /tasks endpoint ---
# The hackathon Phase 2 validator calls GET /tasks to verify tasks with graders.
_TASKS = _load_tasks_from_yaml()


@app.get(
    "/tasks",
    tags=["Environment Info"],
    summary="List all tasks",
    response_model=list[TaskDetail],
)
async def list_tasks():
    """
    Returns the loaded tasks.
    Each task includes its grader entrypoint, required for hackathon
    Phase 2 validation ('Not enough tasks with graders' check).
    """
    return _TASKS


def main():
    """Main entry point for multi-mode deployment."""
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()
