"""
OpenEnv server entry point.

Key fixes applied:
1. Removed conflicting /health and / routes (OpenEnv framework already provides /health returning {"status": "healthy"})
2. The framework's env_app is mounted correctly as the primary app
3. Overrides get_metadata() on the Environment to expose tasks with graders
4. Adds a proper main() for multi-mode deployment compliance
"""
import uvicorn
from openenv.core.env_server.http_server import create_app
from openenv.core.env_server.types import EnvironmentMetadata
from models import ActionModel, ObservationModel
from server.incident_rca_env_environment import IncidentRCAEnvironment



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

IncidentRCAEnvironment.get_metadata = _get_metadata  


# Create the OpenEnv FastAPI app — this already provides:
#   GET  /health        -> {"status": "healthy"}
#   GET  /metadata      -> EnvironmentMetadata
#   GET  /schema        -> action/observation/state schemas
#   POST /reset         -> initial observation
#   POST /step          -> step result
#   GET  /state         -> current state
#   POST /mcp           -> JSON-RPC MCP endpoint
#   WS   /ws            -> WebSocket endpoint
app = create_app(
    IncidentRCAEnvironment,
    ActionModel,
    ObservationModel,
    env_name="incident_rca_env",
    max_concurrent_envs=1,
)


def main():
    """Main entry point for multi-mode deployment."""
    uvicorn.run(app, host="0.0.0.0", port=7860)


if __name__ == "__main__":
    main()