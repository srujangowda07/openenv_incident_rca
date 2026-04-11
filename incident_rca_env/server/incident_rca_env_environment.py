from uuid import uuid4
from typing import Optional, Dict, Any

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from incident_rca_env.models import ActionModel, ObservationModel
from incident_rca_env.environment.env import IncidentRCAEnv


class IncidentRCAEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._env: Optional[IncidentRCAEnv] = None
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._cumulative_reward = 0.0

    def reset(self, config: Optional[Dict[str, Any]] = None) -> ObservationModel:
        config = config or {}

        # safely extract values
        episode_id = config.get("episode_id", str(uuid4()))
        seed = config.get("seed", None)
        task_id = (
            config.get("task_id")
            or config.get("task")
            or config.get("taskId")
            or "easy_001"
        )

        # reset internal state
        self._state = State(episode_id=episode_id, step_count=0)
        self._cumulative_reward = 0.0

        # create env safely
        try:
            self._env = IncidentRCAEnv(task_id=task_id, seed=seed)
            obs = self._env.reset()

            # Ensure compliance with platform schema (must not be null)
            obs.reward = 0.0
            obs.metadata = {}
            obs.done = False  # Reset should always be not done

            return obs

        except Exception as e:
            print(f"[RESET ERROR] {e}")
            raise RuntimeError(f"Reset failed: {str(e)}")

    def step(self, action: ActionModel) -> ObservationModel:
        if self._env is None:
            self.reset({})

        if self._env is None:
            return ObservationModel(done=True, reward=0.01, metadata={})

        obs, reward, done, info = self._env.step(action)

        # update state
        self._state.step_count += 1
        self._cumulative_reward += reward.total

        # ensure info consistency
        info.cumulative_reward = self._cumulative_reward
        info.steps_taken = self._state.step_count

        # OpenEnv HTTP serializer expects a single Observation object with reward/done.
        obs.done = done
        obs.reward = reward.total
        obs.metadata = {
            "reward_breakdown": reward.breakdown,
            "reward_reason": reward.reason,
            "info": info.model_dump() if hasattr(info, "model_dump") else {},
        }

        return obs

    @property
    def state(self) -> State:
        return self._state
