from contextlib import asynccontextmanager
from copy import deepcopy
import csv
import io
import json
import threading
from urllib.parse import urlparse
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, Response
from .schemas import Profile, ScenarioInput, AdvanceInput, BranchInput, ObservationInput, ImportInput, Assumptions
from .storage import Store
from .engine import initial_state, simulate, sensitivity, DECISIONS, ENGINE_VERSION
from .narrative import TemplateNarrativeProvider

LOCK = threading.RLock()
provider = TemplateNarrativeProvider()


def create_app(directory=None):
  @asynccontextmanager
  async def lifespan(app):
    app.state.store = Store(directory)
    with app.state.store.engine.begin() as connection:
      if not app.state.store.all(connection, 'profiles'):
        profile = Profile().model_dump()
        identifier = app.state.store.add(connection, 'profiles', profile)
        app.state.store.profile_parts(connection, identifier, profile)
    yield
    app.state.store.engine.dispose()

  app = FastAPI(title='LifeSim', version=ENGINE_VERSION, lifespan=lifespan)

  @app.middleware('http')
  async def local_boundary(request: Request, call_next):
    allowed = {'localhost', '127.0.0.1', 'testserver'}
    if request.url.hostname not in allowed:
      return JSONResponse({'detail': 'Local access only.'}, status_code=403)
    origin = request.headers.get('origin')
    if origin and urlparse(origin).hostname not in allowed:
      return JSONResponse({'detail': 'Foreign origins are not allowed.'}, status_code=403)
    if request.headers.get('sec-fetch-site') == 'cross-site':
      return JSONResponse({'detail': 'Cross-site requests are not allowed.'}, status_code=403)
    size = request.headers.get('content-length', '0')
    if not size.isdigit() or int(size) > 600000:
      return JSONResponse({'detail': 'Request exceeds 600 KB limit.'}, status_code=413)
    if request.method in ['POST', 'PUT', 'PATCH']:
      body = await request.body()
      if len(body) > 600000:
        return JSONResponse({'detail': 'Request exceeds 600 KB limit.'}, status_code=413)
    response = await call_next(request)
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'no-referrer'
    response.headers['Cache-Control'] = 'no-store'
    return response

  def store(): return app.state.store

  def require(connection, table, identifier):
    record = store().get(connection, table, identifier)
    if not record: raise HTTPException(404, 'Record not found.')
    return record

  def scenario_view(record):
    return {'id': record['id'], 'profile_id': record['profile_id'], 'parent_id': record['parent_id'], **record['payload']}

  def create_scenario(connection, profile_id, name, seed, assumptions=None, campaign=True, parent=None, month=0, inherited=None):
    profile = inherited['profile'] if inherited else require(connection, 'profiles', profile_id)['payload']
    state = deepcopy(inherited['state']) if inherited else initial_state(Profile.model_validate(profile))
    payload = {'name': name, 'seed': seed, 'assumptions': assumptions or profile['assumptions'], 'campaign': campaign,
      'profile': profile, 'starting_state': state, 'state': state, 'fork_month': month,
      'journal': deepcopy(inherited['journal']) if inherited else [], 'latest_run': None, 'engine_version': ENGINE_VERSION}
    identifier = store().add(connection, 'scenarios', payload, profile_id=profile_id, parent_id=parent)
    store().add(connection, 'life_states', state, scenario_id=identifier)
    return scenario_view(require(connection, 'scenarios', identifier))

  def history(connection, scenario):
    states = {scenario['starting_state']['month']: scenario['starting_state']}
    for run in store().all(connection, 'simulation_runs', scenario_id=scenario['id']):
      for snapshot in store().all(connection, 'monthly_snapshots', run_id=run['id']):
        states[snapshot['month']] = snapshot['payload']
    return [states[month] for month in sorted(states)]

  @app.get('/api/health')
  def health(): return {'status': 'ok', 'engine_version': ENGINE_VERSION}

  @app.get('/api/bootstrap')
  def bootstrap():
    with store().engine.connect() as connection:
      return {'profiles': [{'id': row['id'], **row['payload']} for row in store().all(connection, 'profiles')],
        'scenarios': [scenario_view(row) for row in store().all(connection, 'scenarios')],
        'decisions': [{'id': key, 'title': values[0], 'description': values[1]} for key, values in DECISIONS.items()], 'engine_version': ENGINE_VERSION}

  @app.post('/api/profiles')
  def add_profile(profile: Profile):
    with LOCK, store().engine.begin() as connection:
      payload = profile.model_dump()
      identifier = store().add(connection, 'profiles', payload)
      store().profile_parts(connection, identifier, payload)
      return {'id': identifier, **payload}

  @app.put('/api/profiles/{identifier}')
  def edit_profile(identifier: str, profile: Profile):
    with LOCK, store().engine.begin() as connection:
      require(connection, 'profiles', identifier)
      payload = profile.model_dump()
      store().replace(connection, 'profiles', identifier, payload)
      store().profile_parts(connection, identifier, payload)
      return {'id': identifier, **payload}

  @app.post('/api/scenarios')
  def new_scenario(data: ScenarioInput):
    with LOCK, store().engine.begin() as connection:
      return create_scenario(connection, data.profile_id, data.name, data.seed, data.assumptions.model_dump() if data.assumptions else None, data.campaign)

  @app.get('/api/scenarios/{identifier}')
  def get_scenario(identifier: str):
    with store().engine.connect() as connection:
      scenario = scenario_view(require(connection, 'scenarios', identifier))
      result = require(connection, 'simulation_runs', scenario['latest_run'])['payload'] if scenario['latest_run'] else None
      return {'scenario': scenario, 'history': history(connection, scenario), 'run': result}

  @app.post('/api/scenarios/{identifier}/advance')
  def advance(identifier: str, data: AdvanceInput):
    with LOCK, store().engine.begin() as connection:
      scenario = scenario_view(require(connection, 'scenarios', identifier))
      if scenario['campaign'] and data.runs != 1:
        raise HTTPException(422, 'Game turns use one deterministic path. Use the Studio for Monte Carlo.')
      limit = 60 if scenario['campaign'] else 240
      if scenario['state']['month']+data.months > limit:
        raise HTTPException(422, f'This timeline ends at month {limit}. Create a Studio projection for a longer horizon.')
      profile = Profile.model_validate(scenario['profile'])
      assumptions = Assumptions.model_validate(scenario['assumptions'])
      starting = deepcopy(scenario['state'])
      result = simulate(profile, starting, assumptions, data.decision, data.months, data.runs, scenario['seed'])
      result['starting_state'] = starting
      result['profile'] = scenario['profile']
      result['assumptions'] = assumptions.model_dump()
      result['engine_version'] = ENGINE_VERSION
      result['decision'] = data.decision
      result['months'] = data.months
      decisions = [entry['decision'] for entry in scenario['journal']] + [data.decision]
      result['reports'] = {label: provider.generate(profile, starting, path[-1], assumptions, decisions) for label, path in result['trajectories'].items()}
      result['sensitivity'] = sensitivity(profile, starting, assumptions, data.decision, data.months, scenario['seed'])
      run_id = store().add(connection, 'simulation_runs', result, scenario_id=identifier)
      for snapshot in result['trajectories']['central']:
        store().add(connection, 'monthly_snapshots', snapshot, run_id=run_id, month=snapshot['month'])
        if snapshot['event_cost']:
          store().add(connection, 'game_events', {'month': snapshot['month'], 'type': 'operations_disruption', 'cost': snapshot['event_cost']}, run_id=run_id)
      for label, report in result['reports'].items():
        store().add(connection, 'narrative_reports', report, run_id=run_id, trajectory=label)
      entry = {'month': starting['month'], 'decision': data.decision, 'title': DECISIONS[data.decision][0], 'run_id': run_id}
      store().add(connection, 'decisions', entry, run_id=run_id)
      payload = require(connection, 'scenarios', identifier)['payload']
      payload.update(state=result['trajectories']['central'][-1], latest_run=run_id, journal=payload['journal']+[entry])
      store().replace(connection, 'scenarios', identifier, payload)
      store().add(connection, 'life_states', payload['state'], scenario_id=identifier)
      return {'scenario': scenario_view(require(connection, 'scenarios', identifier)), 'run': result, 'history': history(connection, scenario_view(require(connection, 'scenarios', identifier)))}

  @app.post('/api/scenarios/{identifier}/branch')
  def branch(identifier: str, data: BranchInput):
    with LOCK, store().engine.begin() as connection:
      parent = scenario_view(require(connection, 'scenarios', identifier))
      state = next((item for item in history(connection, parent) if item['month'] == data.month), None)
      if state is None: raise HTTPException(422, 'Choose an available historical month.')
      inherited = {'profile': parent['profile'], 'state': state, 'journal': [entry for entry in parent['journal'] if entry['month'] < data.month]}
      return create_scenario(connection, parent['profile_id'], data.name, parent['seed'], parent['assumptions'], parent['campaign'], identifier, data.month, inherited)

  @app.post('/api/observations')
  def add_observation(data: ObservationInput):
    with LOCK, store().engine.begin() as connection:
      require(connection, 'profiles', data.profile_id)
      identifier = store().add(connection, 'actual_observations', data.model_dump(), profile_id=data.profile_id)
      return {'id': identifier, **data.model_dump()}

  @app.get('/api/observations/{profile_id}')
  def observations(profile_id: str):
    with store().engine.connect() as connection:
      require(connection, 'profiles', profile_id)
      return [{'id': row['id'], **row['payload']} for row in store().all(connection, 'actual_observations', profile_id=profile_id)]

  @app.get('/api/export')
  def export_workspace():
    with store().engine.connect() as connection:
      return {'format_version': 1, 'engine_version': ENGINE_VERSION, 'tables': {name: store().all(connection, name) for name in store().tables if name != 'schema_migrations'}}

  @app.get('/api/profiles/{identifier}/export')
  def export_profile(identifier: str, format: str = 'json'):
    with store().engine.connect() as connection:
      payload = require(connection, 'profiles', identifier)['payload']
      if format == 'json': return payload
      if format != 'csv': raise HTTPException(422, 'Use json or csv.')
      buffer = io.StringIO()
      writer = csv.writer(buffer)
      writer.writerow(['field', 'value'])
      writer.writerows((key, json.dumps(value)) for key, value in payload.items())
      return Response(buffer.getvalue(), media_type='text/csv')

  @app.post('/api/import')
  def import_profile(data: ImportInput):
    try:
      if data.format == 'json':
        payload = json.loads(data.content)
      else:
        reader = csv.DictReader(io.StringIO(data.content))
        if reader.fieldnames != ['field', 'value']: raise ValueError('CSV needs field,value headers.')
        payload = {}
        for row in reader:
          if row['field'] in payload: raise ValueError('Duplicate CSV field.')
          payload[row['field']] = json.loads(row['value'])
      profile = Profile.model_validate(payload)
    except (ValueError, TypeError, KeyError, RecursionError):
      raise HTTPException(422, 'Invalid profile. Use an exported JSON or field,value CSV profile with valid values.')
    return add_profile(profile)

  @app.delete('/api/data')
  def delete_data():
    with LOCK, store().engine.begin() as connection:
      store().clear(connection)
    return {'deleted': True}

  return app


app = create_app()
