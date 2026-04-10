from __future__ import annotations
from dataclasses import dataclass
from environment.canonical import normalize_cause_type, normalize_service

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


@dataclass
class GradeResult:
    score: float
    breakdown: dict
    passed: bool
    feedback: str


class IncidentRCAGrader:
    """
    Deterministic grader.  Score range: 0.10 – 0.90.
    Dimensions and weights match openenv.yaml exactly:

        root_cause_service  0.50
        cause_type          0.30  (only if service is correct)
        tool_evidence       0.20  (queried root cause service before diagnosing)
        penalties           variable (invalid actions, wrong diagnosis)

    Pass threshold: 0.60
    """

    PASS_THRESHOLD = 0.60

    W_SERVICE  = 0.50
    W_CAUSE    = 0.30
    W_EVIDENCE = 0.20
    W_PENALTY_PER_INVALID   = 0.10
    W_PENALTY_WRONG_SERVICE = 0.20
    MIN_SCORE_STRICT = 0.10
    MAX_SCORE_STRICT = 0.90

    def grade(self, episode: dict) -> GradeResult:
        try:
            breakdown: dict[str, float] = {}
            breakdown["root_cause_service"] = self._score_service(episode)
            breakdown["cause_type"]         = self._score_cause_type(episode)
            breakdown["tool_evidence"]      = self._score_evidence(episode)
            breakdown["penalties"]          = self._score_penalties(episode)

            raw_total = sum(breakdown.values())
            total = max(self.MIN_SCORE_STRICT, min(self.MAX_SCORE_STRICT, raw_total))

            return GradeResult(
                score=total,
                breakdown=breakdown,
                passed=total >= self.PASS_THRESHOLD,
                feedback=self._generate_feedback(breakdown, episode),
            )
        except Exception as e:
            return GradeResult(
                score=0.10,
                breakdown={
                    "root_cause_service": 0.10,
                    "cause_type": 0.10,
                    "tool_evidence": 0.10,
                    "penalties": 0.00,
                },
                passed=False,
                feedback=f"grader fallback due to error: {e}",
            )

    def _score_service(self, episode: dict) -> float:
        scenario = episode.get("scenario", {}) or {}
        root_cause = scenario.get("root_cause", {}) or {}
        final_state = episode.get("final_state", {}) or {}
        ground_truth = normalize_service(root_cause.get("service", ""))
        diagnosed    = normalize_service(final_state.get("diagnosed_service") or "")
        return self.W_SERVICE if diagnosed == ground_truth else 0.00

    def _score_cause_type(self, episode: dict) -> float:
        scenario = episode.get("scenario", {}) or {}
        root_cause = scenario.get("root_cause", {}) or {}
        final_state = episode.get("final_state", {}) or {}
        ground_truth_svc   = normalize_service(root_cause.get("service", ""))
        diagnosed_svc      = normalize_service(final_state.get("diagnosed_service") or "")

        if diagnosed_svc != ground_truth_svc:
            return 0.00

        ground_truth_cause = normalize_cause_type(
            root_cause.get("cause_type", "")
        )
        diagnosed_cause    = normalize_cause_type(
            final_state.get("diagnosed_cause") or ""
        )
        return self.W_CAUSE if diagnosed_cause == ground_truth_cause else 0.00

    def _score_evidence(self, episode: dict) -> float:
        scenario = episode.get("scenario", {}) or {}
        root_cause = scenario.get("root_cause", {}) or {}
        final_state = episode.get("final_state", {}) or {}
        ground_truth_svc = normalize_service(root_cause.get("service", ""))

        for entry in final_state.get("action_history", []) or []:
            if entry.get("action") == "submit_diagnosis":
                continue

            # Direct service parameter match.
            params = entry.get("parameters", {})
            if normalize_service(params.get("service") or "") == ground_truth_svc:
                return self.W_EVIDENCE

            # Trace result that mentions the root cause service.
            if entry.get("action") == "fetch_traces":
                result = entry.get("result") or {}
                if isinstance(result, dict):
                    for span in result.get("trace", []):
                        svc_match   = ground_truth_svc in normalize_service(span.get("service", ""))
                        error_match = ground_truth_svc in span.get("error", "").lower()
                        if svc_match or error_match:
                            return self.W_EVIDENCE

        return 0.00

    def _score_penalties(self, episode: dict) -> float:
        penalty = 0.0

        info = episode.get("info", {}) or {}
        scenario = episode.get("scenario", {}) or {}
        root_cause = scenario.get("root_cause", {}) or {}
        final_state = episode.get("final_state", {}) or {}

        invalid = info.get("invalid_actions", 0)
        penalty -= invalid * self.W_PENALTY_PER_INVALID

        ground_truth_svc = normalize_service(root_cause.get("service", ""))
        diagnosed        = normalize_service(final_state.get("diagnosed_service") or "")
        if diagnosed and diagnosed != ground_truth_svc:
            penalty -= self.W_PENALTY_WRONG_SERVICE

        return penalty

    @staticmethod
    def _generate_feedback(breakdown: dict, episode: dict) -> str:
        scenario = episode.get("scenario", {}) or {}
        rca = scenario.get("root_cause", {}) or {}
        rca_service = rca.get("service", "unknown")
        rca_cause = rca.get("cause_type", "unknown")
        final_state = episode.get("final_state", {}) or {}
        info = episode.get("info", {}) or {}
        lines = []

        if breakdown.get("root_cause_service", 0.0) == 0.0:
            lines.append(f"wrong root cause service — correct: '{rca_service}'")

        if breakdown.get("cause_type", 0.0) == 0.0:
            if breakdown.get("root_cause_service", 0.0) > 0.0:
                # Service was correct but cause was wrong.
                diagnosed_cause = final_state.get("diagnosed_cause") or "(none)"
                lines.append(
                    f"cause type mismatch — got: '{diagnosed_cause}', "
                    f"correct: '{rca_cause}'"
                )

        if breakdown.get("tool_evidence", 0.0) == 0.0:
            lines.append(
                f"no tool evidence for root cause service '{rca_service}' before diagnosis"
            )

        invalid = info.get("invalid_actions", 0)
        if invalid > 0:
            lines.append(f"{invalid} invalid action(s) (-{invalid * 0.10:.2f})")

        return " | ".join(lines) if lines else "correct"


def grade(payload: dict) -> GradeResult:
    """
    OpenEnv entry point for grading.
    Attempts to use IncidentRCAGrader for a full evaluation.
    """
    try:
        # Standard OpenEnv passes the episode data as the payload.
        # We delegate to the more sophisticated IncidentRCAGrader.
        return IncidentRCAGrader().grade(payload)
    except Exception as e:
        # Fallback in case of catastrophic failure
        return GradeResult(
            score=0.10,
            breakdown={"error": 1.0},
            passed=False,
            feedback=f"Critical grader failure: {e}",
        )
