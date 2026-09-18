# MGO Brain v0.3

MGO Brain is a read/observe-first telemetry, diagnostics and digital-twin project for a **Microcar M.Go / F8 0.5 (2017)** with **Progress ACT / Lombardini LDW502**.

The current software can be developed without touching the vehicle. It simulates a complete start/drive/stop cycle, injects faults, normalizes telemetry into canonical signals, tracks alert lifecycles, evaluates subsystem health, stores trip/start history, builds historical baselines, and exposes a local API + dashboard.

It deliberately does **not** control the vehicle.

## Current release: v0.3.0

### Foundation

- canonical signal model with quality/source metadata;
- machine-readable registry of 80 planned/simulated channels;
- Progress ACT/MGO maintenance-plan registry;
- vehicle state machine: OFF → ACC → IGNITION → PREHEAT → CRANKING → IDLE/DRIVING → OFF;
- SQLite event/start/trip/report metadata;
- FastAPI REST API + WebSocket;
- local mobile-friendly dashboard;
- AI-context endpoint;
- Docker + GitHub Actions CI.

### Fault & health laboratory

Nine injectable scenarios are available:

- `weak_battery`
- `starter_degradation`
- `glow_fault`
- `alternator_undercharge`
- `alternator_overvoltage`
- `low_oil_pressure`
- `overheating`
- `cvt_slip`
- `cvt_overheat`

The diagnostic layer includes deterministic local rules, ACTIVE → CLEARED alert lifecycle, alert history, and subsystem health for ENGINE / CVT / ELECTRICAL / TYRES / BRAKES. Missing sensor sets report `UNKNOWN`, not a false `NORMAL`.

### Historical analytics

v0.3 adds:

- streaming flat JSONL while a trip is active;
- Parquet/ZSTD finalization when the analytics extra is installed;
- DuckDB-backed local historical analytics;
- a healthy **reference baseline** separated from the rolling 30-sample window;
- a 20-sample qualification period before anomaly judgments become active;
- exclusion of starts/trips with ATTENTION or CRITICAL diagnostic conditions from healthy reference learning;
- heuristic anomaly score + NORMAL / WATCH / ATTENTION state;
- persistent baseline rebuild from SQLite history after restart;
- trip comparison API;
- automatically stored post-trip reports;
- running-only aggregation so a stopped engine's 0 bar oil pressure cannot contaminate trip minimums.

Historical analytics are not part of the real-time safety path. If DuckDB/Parquet is unavailable, live rules, alerts and health evaluation continue to work.

## Run

```bash
git clone https://github.com/chup1runov/mgo-brain.git
cd mgo-brain
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e '.[analytics]'
uvicorn mgo_brain.main:app --host 0.0.0.0 --port 8080
```

Open: `http://localhost:8080/`

Or with Docker:

```bash
docker build -t mgo-brain .
docker run --rm -p 8080:8080 mgo-brain
```

## API

Core:

- `GET /health`
- `GET /api/v1/state`
- `GET /api/v1/events`
- `GET /api/v1/trips`
- `GET /api/v1/trips/{id}/report`
- `GET /api/v1/starts`
- `GET /api/v1/alerts`
- `GET /api/v1/health-summary`
- `GET /api/v1/ai/context`
- `GET /api/v1/baselines`
- `GET /api/v1/analytics/summary`
- `GET /api/v1/analytics/compare?trip_a=1&trip_b=2`
- `GET /api/v1/spec/signals`
- `GET /api/v1/spec/maintenance`
- `WS /ws/live`

Simulator laboratory:

- `GET /api/v1/simulator/faults`
- `POST /api/v1/simulator/faults/{name}/enable`
- `POST /api/v1/simulator/faults/{name}/disable`
- `POST /api/v1/simulator/faults/clear`

## Architecture

```text
Physical/simulated source
        ↓
Canonical signals + quality/source
        ↓
VehicleState + state machine
        ↓
Start/Trip detectors
        ↓
Deterministic Rules
        ↓
Alert lifecycle + Subsystem Health
        ↓
Reference baseline + Rolling baseline
        ↓
SQLite summaries + Parquet/DuckDB history
        ↓
REST / WebSocket / Dashboard / AI context
```

Future physical sources can replace the simulator without changing the consumers:

1. AutoPi / SocketCAN for factory BFI/CAN (listen-only first).
2. ESP32 SensorHub over a separate Sensor CAN.
3. RS485/Modbus isolated digital inputs.
4. Independent oil/coolant/RPM/CVT sensors.
5. Battery monitor, TPMS, vibration and cabin/environment sensors.

## Safety boundary

MGO Brain is not an ECU replacement. Vehicle-critical OEM functions remain independent. Failure or removal of MGO Brain must not prevent normal vehicle operation. Critical alerts must remain deterministic and local; AI is explanatory, not the sole safety mechanism.

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
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

The minimal local environment currently passes **18 tests** and skips the DuckDB-specific round-trip test when DuckDB is unavailable. GitHub CI installs the analytics extra, so the Parquet/DuckDB round-trip test is required there.
