import sys
import os

# Add project root to path
sys.path.append(os.path.abspath("."))

from graders.grader import grade

def test_grader():
    print("Running grader robustness tests...")
    
    # Test case 1: Empty input
    s1 = grade({})
    print(f"Empty dict: {s1}")
    assert 0.1 <= s1 <= 0.9
    
    # Test case 2: None input
    s2 = grade(None)
    print(f"None input: {s2}")
    assert 0.1 <= s2 <= 0.9
    
    # Test case 3: Nested/Malformed output
    s3 = grade({"wrong_key": "data"})
    print(f"Malformed dict: {s3}")
    assert 0.1 <= s3 <= 0.9

    # Test case 4: Perfect score simulation (should be capped at 0.9)
    # Using a fake episode that causes high score
    perfect_episode = {
        "scenario": {
            "root_cause": {"service": "api", "cause_type": "oom"}
        },
        "final_state": {
            "diagnosed_service": "api",
            "diagnosed_cause": "oom",
            "action_history": [{"action": "grep_logs", "parameters": {"service": "api"}}]
        },
        "info": {"invalid_actions": 0}
    }
    s4 = grade(perfect_episode)
    print(f"Perfect episode: {s4}")
    assert 0.1 <= s4 <= 0.9
    assert s4 == 0.9 # Should be capped

    # Test case 5: Total failure simulation (should be capped at 0.1)
    fail_episode = {
        "scenario": {"root_cause": {"service": "a", "cause_type": "b"}},
        "final_state": {"diagnosed_service": "x", "diagnosed_cause": "y"},
        "info": {"invalid_actions": 10}
    }
    s5 = grade(fail_episode)
    print(f"Total failure: {s5}")
    assert 0.1 <= s5 <= 0.9
    assert s5 == 0.1 # Should be floor
    
    print("\n[SUCCESS] All score range checks passed (0.1 - 0.9)")

if __name__ == "__main__":
    test_grader()
