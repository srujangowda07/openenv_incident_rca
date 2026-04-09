from fastapi import FastAPI
from openenv.core.env_server.http_server import create_app
from models import ActionModel, ObservationModel
from server.incident_rca_env_environment import IncidentRCAEnvironment


def main():
    base_app = FastAPI()

    @base_app.get("/")
    def root():
        return {"status": "running"}

    @base_app.get("/health")
    def health():
        return {"status": "ok"}

    env_app = create_app(
        IncidentRCAEnvironment,
        ActionModel,
        ObservationModel,
        env_name="incident_rca_env",
        max_concurrent_envs=1,
    )

    base_app.mount("/", env_app)

    return base_app


app = main()