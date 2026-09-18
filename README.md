# MGO Brain v0.4

MGO Brain is a read/observe-first telemetry, diagnostics and digital-twin project for a **Microcar M.Go / F8 0.5 (2017)** with **Progress ACT / Lombardini LDW502**.

It deliberately does **not** control the vehicle. Vehicle-critical OEM systems remain independent.

## Current release: v0.4.0

### Software foundation

- canonical signal model with source/quality metadata;
- 80-signal registry;
- vehicle state machine and synthetic M.Go drive cycle;
- start/trip detection and SQLite metadata;
- deterministic safety rules;
- nine injectable fault scenarios;
- ACTIVE → CLEARED alert lifecycle;
- ENGINE / CVT / ELECTRICAL / TYRES / BRAKES health model;
- healthy reference + rolling historical baselines;
- 20-sample qualification period;
- Parquet/ZSTD trip telemetry with DuckDB analytics;
- trip comparison and stored post-trip reports;
- REST API, WebSocket and AI-context endpoint.

### Local vehicle console

v0.4 adds seven local views:

- **HOME** — speed/RPM, overall/subsystem health, active alerts, latest trip;
- **ENGINE** — coolant, oil, RPM, glow/starter data, starts and baselines;
- **CVT** — ratio/drift and primary/secondary temperatures;
- **POWER** — battery/current/SoC/alternator and electrical baselines;
- **TRIPS** — history, report viewer and two-trip comparison;
- **SERVICE** — documented maintenance-plan registry;
- **LAB** — simulator faults, analytics status, baselines and raw normalized state.

The web UI is an installable PWA. The service worker caches the application shell only; `/api/` and WebSocket vehicle data are never replaced by stale cached values.

## Run

```bash
git clone https://github.com/chup1runov/mgo-brain.git
cd mgo-brain
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e '.[analytics]'
uvicorn mgo_brain.main:app --host 0.0.0.0 --port 8080
```

Open `http://localhost:8080/`.

## Main API

- `GET /health`
- `GET /api/v1/state`
- `GET /api/v1/events`
- `GET /api/v1/alerts`
- `GET /api/v1/health-summary`
- `GET /api/v1/starts`
- `GET /api/v1/trips`
- `GET /api/v1/trips/{id}/report`
- `GET /api/v1/reports`
- `GET /api/v1/baselines`
- `GET /api/v1/analytics/summary`
- `GET /api/v1/analytics/compare?trip_a=1&trip_b=2`
- `GET /api/v1/ai/context`
- `GET /api/v1/spec/signals`
- `GET /api/v1/spec/maintenance`
- `WS /ws/live`

## Safety boundary

- factory CAN discovery is listen-only;
- factory pin numbers/wire colors are never guessed;
- MGO Brain must not be required for engine start, braking, gear selection or OEM oil/overheat warnings;
- critical alerts remain local/deterministic;
- AI is explanatory, not the sole safety mechanism;
- historical analytics are outside the real-time safety path.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Local UI](docs/UI.md)
- [Fault laboratory](docs/FAULT_LAB.md)
- [Roadmap](docs/ROADMAP.md)
- [Project handoff](docs/PROJECT_HANDOFF.md)
- [Changelog](CHANGELOG.md)

## Development

```bash
pip install -e '.[dev,analytics]'
python -m compileall -q mgo_brain tests
pytest -q
```

Local verification before push: **22 tests passed, 1 DuckDB-specific test skipped when DuckDB was unavailable locally**. GitHub CI installs the analytics extra and must run the complete suite on Python 3.11, 3.12 and 3.13.
