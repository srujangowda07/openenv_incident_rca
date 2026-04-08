from graders.grader import IncidentRCAGrader


def grade(episode: dict) -> float:
    try:
        result = IncidentRCAGrader().grade(episode)
        return max(0.05, min(0.95, float(result.score)))
    except Exception:
        return 0.05
