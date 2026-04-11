"""
FastAPI application for Incident RCA OpenEnv environment.
"""

from openenv.core.env_server.http_server import create_app

from incident_rca_env.models import ActionModel, ObservationModel
from incident_rca_env.server.incident_rca_env_environment import (
    IncidentRCAEnvironment,
)
from incident_rca_env.tasks.task_definitions import list_tasks


# Optional: attach metadata (safe)
from openenv.core.env_server.types import EnvironmentMetadata


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


IncidentRCAEnvironment.get_metadata = _get_metadata  # type: ignore


app = create_app(
    IncidentRCAEnvironment,
    ActionModel,
    ObservationModel,
    env_name="incident-rca-env",
    max_concurrent_envs=1,
)


@app.get("/tasks")
def get_tasks():
    return list_tasks()

@app.get("/v1/tasks")
def get_tasks_v1():
    return list_tasks()


def main():
    """Run server locally."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()