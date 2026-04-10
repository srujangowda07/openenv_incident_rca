from openenv.core.env_server.types import Action, Observation
from pydantic import BaseModel, Field
from typing import List, Dict, Optional


from typing import Union

class ActionModel(Action):
    action_type: str = Field(
        ...,
        description="Type of action: grep_logs, query_metrics, fetch_traces, query_dependencies, submit_diagnosis",
    )
    parameters: Union[Dict, str] = Field(
        default_factory=dict,
        description="Action-specific parameters",
    )


class ObservationModel(Observation):
    step: int = Field(default=0)
    max_steps: int = Field(default=25)
    task_id: str = Field(default="")
    task_description: str = Field(default="")
    alerts: List[Dict] = Field(default_factory=list)
    tool_result: Optional[Dict] = Field(default=None)
    history: List[Dict] = Field(default_factory=list)
    available_actions: List[str] = Field(default_factory=list)
    # done, reward, metadata are inherited from Observation base


class RewardModel(BaseModel):
    total: float = Field(default=0.0)
    breakdown: Dict[str, float] = Field(default_factory=dict)
    reason: str = Field(default="")


class InfoModel(BaseModel):
    ground_truth_root_cause: Optional[Dict] = Field(default=None)
    steps_taken: int = Field(default=0)
    tools_used: List[str] = Field(default_factory=list)
    invalid_actions: int = Field(default=0)
    cumulative_reward: float = Field(default=0.0)


class TaskDetail(BaseModel):
    id: str
    name: str
    difficulty: str
    max_steps: int
    description: str
    grader: str
    has_grader: bool


class TaskResponse(BaseModel):
    tasks: List[TaskDetail]
    total: int
    tasks_with_graders: int
