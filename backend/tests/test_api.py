import json
from fastapi.testclient import TestClient
from backend.app.main import create_app


def setup_campaign(client):
  profile = client.get('/api/bootstrap').json()['profiles'][0]
  response = client.post('/api/scenarios', json={'profile_id': profile['id'], 'name': 'Freedom by 50'})
  assert response.status_code == 200, response.text
  return profile, response.json()


def test_complete_vertical_slice_and_restart(tmp_path):
  with TestClient(create_app(tmp_path)) as client:
    profile, original = setup_campaign(client)
    first = client.post(f"/api/scenarios/{original['id']}/advance", json={'decision': 'expand_owner', 'months': 12}).json()
    assert first['scenario']['state']['month'] == 12
    assert first['scenario']['state']['work_hours'] == 57
    branch = client.post(f"/api/scenarios/{original['id']}/branch", json={'month': 0, 'name': 'Hire instead'}).json()
    alternate = client.post(f"/api/scenarios/{branch['id']}/advance", json={'decision': 'hire_manager', 'months': 12}).json()
    assert alternate['scenario']['state']['work_hours'] == 30
    assert alternate['scenario']['state']['net_worth'] != first['scenario']['state']['net_worth']
    assert client.get(f"/api/scenarios/{original['id']}").json() == first
    exported = client.get('/api/export').json()
    assert len(exported['tables']['simulation_runs']) == 2
    assert len(exported['tables']['monthly_snapshots']) == 24
    assert len(exported['tables']['game_events']) == 2
    assert len(exported['tables']['narrative_reports']) == 6
  with TestClient(create_app(tmp_path)) as restarted:
    assert restarted.get(f"/api/scenarios/{branch['id']}").json() == alternate
    assert len(restarted.get('/api/bootstrap').json()['scenarios']) == 2


def test_historical_profile_and_completed_runs_do_not_change(tmp_path):
  with TestClient(create_app(tmp_path)) as client:
    profile, scenario = setup_campaign(client)
    first = client.post(f"/api/scenarios/{scenario['id']}/advance", json={'months': 1}).json()
    old = client.get('/api/export').json()['tables']['simulation_runs'][0]
    identifier = profile.pop('id')
    profile['monthly_expenses'] = 9000
    assert client.put(f'/api/profiles/{identifier}', json=profile).status_code == 200
    assert client.get(f"/api/scenarios/{scenario['id']}").json()['scenario']['profile']['monthly_expenses'] == 4500
    client.post(f"/api/scenarios/{scenario['id']}/advance", json={'months': 1})
    assert client.get('/api/export').json()['tables']['simulation_runs'][0] == old
    historical = client.post(f"/api/scenarios/{scenario['id']}/branch", json={'month': 1}).json()
    assert historical['state'] == first['scenario']['state']


def test_json_csv_roundtrips_and_invalid_imports(tmp_path):
  with TestClient(create_app(tmp_path)) as client:
    profile, _ = setup_campaign(client)
    for format in ['json', 'csv']:
      response = client.get(f"/api/profiles/{profile['id']}/export?format={format}")
      imported = client.post('/api/import', json={'format': format, 'content': response.text})
      assert imported.status_code == 200, imported.text
      assert imported.json()['accounts'] == profile['accounts']
    assert client.post('/api/import', json={'format': 'json', 'content': '{bad'}).status_code == 422
    assert client.post('/api/import', json={'format': 'json', 'content': json.dumps({'age': -5})}).status_code == 422
    assert client.post('/api/import', json={'format': 'csv', 'content': 'field,value\nname,"\"x\""\nname,"\"y\""'}).status_code == 422
    assert client.post('/api/import', json={'format': 'json', 'content': json.dumps({'name': 'x'*501000})}).status_code == 422


def test_local_boundary_delete_and_actual_observations(tmp_path):
  with TestClient(create_app(tmp_path)) as client:
    profile, scenario = setup_campaign(client)
    assert client.post('/api/scenarios', headers={'origin': 'https://attacker.example'}, json={'profile_id': profile['id']}).status_code == 403
    assert client.get('/api/bootstrap', headers={'host': 'evil.example'}).status_code == 403
    assert client.post('/api/observations', json={'profile_id': profile['id'], 'month': '2026-10', 'note': 'Synthetic observation'}).status_code == 200
    assert len(client.get(f"/api/observations/{profile['id']}").json()) == 1
    assert client.get(f"/api/scenarios/{scenario['id']}").json()['scenario']['state']['month'] == 0
    assert client.delete('/api/data').status_code == 200
    assert client.get('/api/bootstrap').json()['profiles'] == []
    assert all(len(rows) == 0 for rows in client.get('/api/export').json()['tables'].values())


def test_campaign_limits_studio_horizons_and_replay(tmp_path):
  with TestClient(create_app(tmp_path)) as client:
    profile, scenario = setup_campaign(client)
    assert client.post(f"/api/scenarios/{scenario['id']}/advance", json={'months': 61}).status_code == 422
    assert client.post(f"/api/scenarios/{scenario['id']}/advance", json={'months': 1, 'runs': 100}).status_code == 422
    for _ in range(60):
      response = client.post(f"/api/scenarios/{scenario['id']}/advance", json={'months': 1, 'decision': 'maintain'})
      assert response.status_code == 200, response.text
    assert response.json()['scenario']['state']['month'] == 60
    assert client.post(f"/api/scenarios/{scenario['id']}/advance", json={'months': 1}).status_code == 422
    projection = client.post('/api/scenarios', json={'profile_id': profile['id'], 'campaign': False, 'seed': 19}).json()
    long_run = client.post(f"/api/scenarios/{projection['id']}/advance", json={'months': 240, 'runs': 100}).json()
    assert long_run['scenario']['state']['month'] == 240
    assert long_run['run']['summary']['runs'] == 100
    from backend.app.engine import simulate
    from backend.app.schemas import Profile, Assumptions
    saved = long_run['run']
    replay = simulate(Profile.model_validate(saved['profile']), saved['starting_state'], Assumptions.model_validate(saved['assumptions']), saved['decision'], saved['months'], saved['summary']['runs'], saved['summary']['seed'])
    assert replay['trajectories'] == saved['trajectories']
