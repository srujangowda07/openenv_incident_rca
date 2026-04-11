from incident_rca_env.grader import IncidentRCAGrader
import math

def test_grader():
    grader = IncidentRCAGrader()
    print("Grader instantiated successfully.")
    
    # Mock environment/episode data
    mock_episode = {
        "scenario": {
            "root_cause": {"service": "api-gateway", "cause_type": "oom"}
        },
        "final_state": {
            "diagnosed_service": "api-gateway",
            "diagnosed_cause": "oom",
            "action_history": [
                {"action": "grep_logs", "parameters": {"service": "api-gateway"}, "result": {"logs": []}}
            ]
        },
        "info": {"invalid_actions": 0}
    }
    
    score = grader.grade(mock_episode)
    print(f"Computed score: {score}")
    
    assert isinstance(score, float), f"Score should be float, got {type(score)}"
    assert 0.0 <= score <= 1.0, f"Score out of bounds: {score}"
    
    print("CLASS-BASED GRADER COMPATIBLE WITH VALIDATOR")

if __name__ == "__main__":
    test_grader()
