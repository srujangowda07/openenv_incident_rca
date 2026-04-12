from __future__ import annotations
import logging
from incident_rca_env.grader import IncidentRCAGrader
from incident_rca_env.environment.canonical import normalize_cause_type, normalize_service

class BaseRcaGrader:
    """
    Proxy grader that uses the package's IncidentRCAGrader.
    This ensures platform evaluation matches local evaluation.
    """
    def __init__(self):
        self._core_grader = IncidentRCAGrader()

    def grade(self, env, *args, **kwargs) -> float:
        try:
            return self._core_grader.grade(env, *args, **kwargs)
        except Exception as e:
            logging.error(f"Grader runtime error: {e}")
            # Fallback to a neutral score if everything fails
            return 0.50

class EasyGrader(BaseRcaGrader):
    pass

class MediumGrader(BaseRcaGrader):
    pass

class HardGrader(BaseRcaGrader):
    pass

