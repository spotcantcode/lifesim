import json
import os
from pathlib import Path
from uuid import uuid4
from sqlalchemy import create_engine, MetaData, insert, select, update, delete, event
from sqlalchemy.engine import URL


class Store:
  def __init__(self, directory=None):
    directory = Path(directory or os.environ.get('LIFESIM_DATA_DIR') or Path(__file__).resolve().parents[2] / 'data')
    directory.mkdir(parents=True, exist_ok=True)
    self.engine = create_engine(URL.create('sqlite', database=str(directory/'lifesim.sqlite3')), connect_args={'check_same_thread': False})
    @event.listens_for(self.engine, 'connect')
    def configure(connection, _):
      connection.execute('PRAGMA foreign_keys=ON')
      connection.execute('PRAGMA busy_timeout=30000')
    with self.engine.connect() as connection:
      driver = connection.connection.driver_connection
      driver.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)')
      applied = {row[0] for row in driver.execute('SELECT version FROM schema_migrations')}
      for migration in sorted((Path(__file__).resolve().parents[1]/'migrations').glob('*.sql')):
        if int(migration.name.split('_')[0]) not in applied:
          driver.executescript(migration.read_text())
    metadata = MetaData()
    metadata.reflect(self.engine)
    self.tables = metadata.tables

  def add(self, connection, table, payload, **columns):
    identifier = str(uuid4())
    connection.execute(insert(self.tables[table]).values(id=identifier, payload=json.dumps(payload, allow_nan=False), **columns))
    return identifier

  def all(self, connection, table, **filters):
    query = select(self.tables[table])
    for key, value in filters.items():
      query = query.where(self.tables[table].c[key] == value)
    records = []
    for row in connection.execute(query).mappings():
      record = dict(row)
      record['payload'] = json.loads(record['payload']) if isinstance(record.get('payload'), str) else record.get('payload')
      records.append(record)
    return records

  def get(self, connection, table, identifier):
    return next(iter(self.all(connection, table, id=identifier)), None)

  def replace(self, connection, table, identifier, payload):
    if table not in ['profiles', 'scenarios']:
      raise ValueError('Historical records are immutable.')
    connection.execute(update(self.tables[table]).where(self.tables[table].c.id == identifier).values(payload=json.dumps(payload, allow_nan=False)))

  def profile_parts(self, connection, identifier, profile):
    for table, values in [('businesses', profile['businesses']), ('financial_accounts', profile['accounts']), ('goals', [{'description': value} for value in profile['goals']]), ('assumptions', [profile['assumptions']])]:
      connection.execute(delete(self.tables[table]).where(self.tables[table].c.profile_id == identifier))
      for value in values:
        self.add(connection, table, value, profile_id=identifier)

  def clear(self, connection):
    # SQLite cascades all descendants, including profiles' scenario trees.
    connection.execute(delete(self.tables['profiles']))
