import sys
sys.path.insert(0, '.')
from graders.grader import grade
from environment.scenario_generator import ScenarioGenerator

gen = ScenarioGenerator(seed=42)
tasks = ['easy_001', 'easy_002', 'easy_003', 'medium_001', 'hard_001']
all_ok = True
total = 0

for tid in tasks:
    sc  = gen.generate(tid)
    rc  = sc['root_cause']

    cases = {
        'PERFECT': grade({'scenario':{'root_cause':rc},'final_state':{'diagnosed_service':rc['service'],'diagnosed_cause':rc['cause_type'],'action_history':[{'action':'grep_logs','parameters':{'service':rc['service']},'result':{}}]},'info':{'invalid_actions':0}}),
        'PARTIAL': grade({'scenario':{'root_cause':rc},'final_state':{'diagnosed_service':rc['service'],'diagnosed_cause':'wrong','action_history':[{'action':'grep_logs','parameters':{'service':rc['service']},'result':{}}]},'info':{'invalid_actions':0}}),
        'WRONG':   grade({'scenario':{'root_cause':rc},'final_state':{'diagnosed_service':'bad','diagnosed_cause':'bad','action_history':[]},'info':{'invalid_actions':5}}),
    }

    for label, score in cases.items():
        ok = 0.1 <= score <= 0.9
        all_ok = all_ok and ok
        total += 1
        tag = 'PASS' if ok else 'FAIL'
        sys.stdout.write(f"{tag} | {tid} | {label} | score={score:.4f}\n")
        sys.stdout.flush()

sys.stdout.write("---\n")
sys.stdout.write(f"RESULT: {total}/15 checked | ALL_VALID={all_ok}\n")
sys.stdout.flush()
