from uuid import uuid4
from typing import Optional

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

try:
    from ..models import ActionModel, ObservationModel, RewardModel, InfoModel
    from ..environment.env import IncidentRCAEnv
except ImportError:
    from models import ActionModel, ObservationModel, RewardModel, InfoModel
    from environment.env import IncidentRCAEnv


class IncidentRCAEnvironment(Environment):
    SUPPORTS_CONCURRENT_SESSIONS: bool = True

    def __init__(self):
        self._env: Optional[IncidentRCAEnv] = None
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._cumulative_reward = 0.0

    def reset(self) -> ObservationModel:
        # reset internal state
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._cumulative_reward = 0.0

        # create new env instance
        self._env = IncidentRCAEnv(task_id="easy_001", seed=None)

        return self._env.reset()

    def step(
        self, action: ActionModel
    ) -> tuple[ObservationModel, RewardModel, bool, InfoModel]:
        if self._env is None:
            raise RuntimeError("Call reset() before step()")

        obs, reward, done, info = self._env.step(action)

        # update state
        self._state.step_count += 1
        self._cumulative_reward += reward.total

        # ensure info consistency
        info.cumulative_reward = self._cumulative_reward
        info.steps_taken = self._state.step_count

        return obs, reward, done, info

    @property
    def state(self) -> State:
        return self._state