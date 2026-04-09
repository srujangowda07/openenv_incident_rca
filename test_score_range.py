import sys
sys.path.insert(0, '.')
from graders.grader import grade
from environment.scenario_generator import ScenarioGenerator

gen = ScenarioGenerator(seed=42)
tasks = ['easy_001', 'easy_002', 'easy_003', 'medium_001', 'hard_001']

all_ok = True
rows = []

for tid in tasks:
    sc = gen.generate(tid)
    rc = sc['root_cause']

    # Scenario 1: PERFECT - correct service + cause + evidence
    perfect = grade({
        'scenario': {'root_cause': rc},
        'final_state': {
            'diagnosed_service': rc['service'],
            'diagnosed_cause': rc['cause_type'],
            'action_history': [{'action': 'grep_logs', 'parameters': {'service': rc['service']}, 'result': {}}]
        },
        'info': {'invalid_actions': 0}
    })

    # Scenario 2: PARTIAL - correct service, wrong cause
    partial = grade({
        'scenario': {'root_cause': rc},
        'final_state': {
            'diagnosed_service': rc['service'],
            'diagnosed_cause': 'wrong-cause',
            'action_history': [{'action': 'grep_logs', 'parameters': {'service': rc['service']}, 'result': {}}]
        },
        'info': {'invalid_actions': 0}
    })

    # Scenario 3: WRONG - wrong service, wrong cause, 5 invalid actions
    wrong = grade({
        'scenario': {'root_cause': rc},
        'final_state': {
            'diagnosed_service': 'totally-wrong',
            'diagnosed_cause': 'totally-wrong',
            'action_history': []
        },
        'info': {'invalid_actions': 5}
    })

    for label, score in [('PERFECT', perfect), ('PARTIAL', partial), ('WRONG', wrong)]:
        valid = 0.1 <= score <= 0.9 and score != 0.0 and score != 1.0
        all_ok = all_ok and valid
        rows.append((tid, label, score, valid))

print()
print('Task              | Scenario | Score  | In [0.1, 0.9]?')
print('-' * 55)
for tid, label, score, ok in rows:
    print(f'{tid:<17} | {label:<8} | {score:.4f} | {"YES" if ok else "FAIL!!"}')
print('-' * 55)
print(f'FINAL: {"ALL 15 SCORES VALID (0.1 to 0.9)" if all_ok else "SOME SCORES OUT OF RANGE - CHECK ABOVE"}')
