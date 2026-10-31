# LifeSim

A local, narrative-first life simulator. The **Freedom by 50** campaign uses fictional data. No API key, external AI, remote assets, telemetry, or account connections.

## Start

On macOS, with dependencies installed, double-click **Start LifeSim.command** in this folder. It starts both servers and opens LifeSim in your browser. Keep its Terminal window open while using the app; press Control+C to stop.

For first-time setup or starting from a terminal:

```sh
cd lifesim
python3 -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
npm install --prefix frontend
./start.sh
```

Open http://127.0.0.1:5173. Both servers bind to localhost. Python 3.12+ and Node 22.12+ are required by the pinned dependencies (tested with Python 3.14 and Node 22). Stop with Ctrl+C. The launcher uses environment variables for optional configuration; see `.env.example` for names. It does not read secret files.

Choose **Enter campaign**, choose a decision, and simulate 12 months. Rewind to month 0, take a different decision, and compare both futures. The Studio supports 1/5/10/20-year projections and seeded Monte Carlo ensembles. Editing a profile affects new campaigns only.

SQLite data lives in `data/lifesim.sqlite3` (or `LIFESIM_DATA_DIR`). It survives browser and server restarts while this directory remains. Deleting the workspace deletes the data. Export before moving environments. Localhost is not a substitute for authentication: this MVP must not be exposed publicly.

## Checks

```sh
.venv/bin/python -m pytest backend/tests -q
npm --prefix frontend test
npm --prefix frontend run build
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for model formulas and limitations, and [CHECKLIST.md](CHECKLIST.md) for implementation status.
