"""
FastAPI application for Incident RCA OpenEnv environment.
"""

from openenv.core.env_server.http_server import create_app

try:
    from incident_rca_env.models import ActionModel, ObservationModel
    from incident_rca_env.server.incident_rca_env_environment import (
        IncidentRCAEnvironment,
    )
except ImportError:
    # Fallback for local execution
    from models import ActionModel, ObservationModel
    from server.incident_rca_env_environment import IncidentRCAEnvironment


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
    env_name="incident_rca_env",
    max_concurrent_envs=1,
)


def main():
    """Run server locally."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()