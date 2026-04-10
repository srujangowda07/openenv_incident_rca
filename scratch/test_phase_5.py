from environment.env import IncidentRCAEnv, ActionModel
env = IncidentRCAEnv('easy_001')
env.reset()
a1 = ActionModel(action_type='query_dependencies', parameters='{"service": "api-gateway"}')
env.step(a1)
a2 = ActionModel(action_type='fetch_traces', parameters='{"request_id": "test"}')
env.step(a2)
a3 = ActionModel(action_type='submit_diagnosis', parameters='{"root_cause_service": "postgres-primary", "cause_type": "connection pool exhausted"}')
obs, reward, done, info = env.step(a3)

print('done:', done)
print('reward:', reward)
print('error: None')

from graders.grader import grade
payload = {
    'scenario': {'root_cause': {'service': 'postgres-primary', 'cause_type': 'connection pool exhausted'}},
    'final_state': env.state(),
    'info': info.model_dump()
}
res = grade(payload)
print('score:', res.score)
print('passed:', res.passed)
