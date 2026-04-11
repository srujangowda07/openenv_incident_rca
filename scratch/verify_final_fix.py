import sys
import os

# Ensure project root is in path
sys.path.insert(0, os.getcwd())

try:
    from grader import IncidentRCAGrader
    print("SUCCESS: Root-level grader import OK")
except ImportError as e:
    print(f"FAILURE: Root-level grader import failed: {e}")
    sys.exit(1)

def test_grader_logic():
    grader = IncidentRCAGrader()
    print("Grader instantiated successfully.")
    
    # Test case 1: Perfect score (should be 1.0)
    mock_episode_perfect = {
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
    
    score_perfect = grader.grade(mock_episode_perfect)
    print(f"Perfect match score: {score_perfect}")
    assert score_perfect == 1.0, f"Expected 1.0, got {score_perfect}"
    
    # Test case 2: Zero score (should be 0.0)
    # We'll simulate this by adding many invalid actions to trigger penalties
    mock_episode_zero = {
        "scenario": {
            "root_cause": {"service": "api-gateway", "cause_type": "oom"}
        },
        "final_state": {
            "diagnosed_service": "wrong-service",
            "diagnosed_cause": "wrong-cause",
            "action_history": []
        },
        "info": {"invalid_actions": 100} # massive penalty
    }
    
    score_zero = grader.grade(mock_episode_zero)
    print(f"Zero score (penalized) match: {score_zero}")
    assert score_zero == 0.0, f"Expected 0.0, got {score_zero}"
    
    assert isinstance(score_perfect, float), "Return type must be float"
    print("SYSTEM IS FULLY COMPATIBLE WITH HACKATHON VALIDATOR")

if __name__ == "__main__":
    test_grader_logic()
    
# YAML Verification Logic
import yaml
def test_yaml():
    with open("openenv.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    
    tasks = cfg.get("tasks", [])
    print(f"Found {len(tasks)} tasks.")
    assert len(tasks) >= 3, "Not enough tasks"
    
    for t in tasks:
        assert t.get("grader") == "grader:IncidentRCAGrader", f"Task {t['id']} has wrong grader path"
        assert t.get("actions") == [], f"Task {t['id']} missing actions: []"
        assert t.get("max_reward") == 1.0, f"Task {t['id']} missing max_reward: 1.0"
    
    print("YAML VALIDATION OK")

test_yaml()
