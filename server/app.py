from openenv.core.env_server.http_server import create_app

try:
    from ..models import ActionModel, ObservationModel
    from .incident_rca_env_environment import IncidentRCAEnvironment
except ImportError:
    from models import ActionModel, ObservationModel
    from server.incident_rca_env_environment import IncidentRCAEnvironment


def main():
    app = create_app(
        IncidentRCAEnvironment,
        ActionModel,
        ObservationModel,
        env_name="incident_rca_env",
        max_concurrent_envs=1,
    )

    @app.get("/")
    def root():
        return {"status": "running"}

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = main()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.app:app", host="0.0.0.0", port=7860)