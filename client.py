from openenv.core.env_client import EnvClient


def get_client(base_url: str = "http://localhost:8000"):
    """
    Minimal client for interacting with the environment.
    """
    return EnvClient(base_url=base_url)