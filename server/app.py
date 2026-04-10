from fastapi import FastAPI
from openenv.core.env_server.http_server import create_app
from models import ActionModel, ObservationModel
from server.incident_rca_env_environment import IncidentRCAEnvironment

# Create OpenEnv app
env_app = create_app(
    IncidentRCAEnvironment,
    ActionModel,
    ObservationModel,
    env_name="incident_rca_env",
    max_concurrent_envs=1,
)

# Create main app
app = FastAPI()

# Health routes (top-level)
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def root():
    return {"status": "running"}

app.mount("/", env_app)