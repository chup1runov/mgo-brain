# MGO Brain v0.5.4

MGO Brain is a read/observe-first telemetry, diagnostics and digital-twin project for a **Microcar M.Go / F8 0.5 (2017)** with **Progress ACT / Lombardini LDW502**.

It deliberately does **not** control the vehicle. Vehicle-critical OEM systems remain independent.

## Current release: v0.5.4

v0.5 introduces the hardware-abstraction layer. The diagnostic core no longer depends directly on the simulator: every real or simulated input becomes a partial `SourceUpdate`, is merged by `StateAggregator`, and only then becomes the canonical `VehicleState` consumed by rules, health, history, UI and AI.

### Source architecture

```text
Simulator / factory CAN / Sensor CAN / Modbus / SmartShunt / TPMS / GNSS-IMU
                              ↓
                         SourceAdapter
                              ↓
                           SourceMux
                              ↓
                        StateAggregator
                              ↓
                         VehicleState
                              ↓
rules / health / trips / baselines / analytics / UI / AI
```

Implemented source boundaries:

- simulator adapter;
- receive-only SocketCAN transport API;
- lazy DBC decoder with canonical-signal mapping;
- SensorHub CAN v1 codec/adapter;
- Modbus RTU digital and analog input adapters;
- VE.Direct text parser/adapter for future battery monitor;
- generic TPMS adapter;
- generic GNSS/IMU adapter;
- multi-source fan-in (`SourceMux`);
- quality/freshness-aware `StateAggregator`;
- configurable source selection in `config/sources.json`.

Preferred-source fallback is freshness-aware. A higher-priority CAN value wins while fresh; if it becomes stale, a fresh lower-priority source can take over. STALE/MISSING/INVALID signals are not treated as live by the vehicle state machine or subsystem readiness checks.

### CAN Survey Toolkit

v0.5.1 adds a differential CAN research tool. Paste or load a baseline candump and a one-action candump in LAB; MGO Brain ranks IDs/bytes most correlated with the action and produces a safe message-only DBC draft.

CLI:

```bash
mgo-survey baseline.log action.log --label driver_door_open --json-out analysis.json --dbc-out draft.dbc
```

See [CAN Survey Toolkit](docs/CAN_SURVEY.md).

### Commissioning & replay

v0.5.2 adds a receive-only CAN recorder, offline candump replay and persistent research sessions. This means a first PKB839 CAN capture can be replayed and decoded later without the vehicle.

Commands:

```bash
mgo-can-record --channel can0 --seconds 10 --output capture.log
mgo-can-replay capture.log --speed 0
mgo-survey-session baseline.log action.log --label driver_door_open
```

See [Commissioning & Replay](docs/COMMISSIONING.md).

### Deployment Pack

v0.5.3 prepares MGO Brain to run as an appliance on a Linux vehicle computer:

- runtime data/config directories controlled by environment variables;
- systemd auto-start template;
- Avahi HTTP advertisement for local discovery;
- `mgo-doctor` runtime/preflight checks;
- `mgo-backup` consistent data/config backup;
- SQLite is backed up through SQLite's backup API rather than copying a live database file.

Default deployed layout:

```text
/opt/mgo-brain      code + venv
/etc/mgo-brain      reviewed configuration
/var/lib/mgo-brain  SQLite / Parquet / CAN survey sessions
```

See [deployment/README.md](deployment/README.md).

### Dedicated display

v0.5.4 adds an optional full-screen display launcher. `mgo-kiosk` waits for the backend health endpoint, discovers Chromium/Chrome and starts the dashboard in kiosk mode.

```text
boot → MGO Brain service → /health ready → Chromium kiosk → dashboard
```

The PWA supports `?kiosk=1` and requests Screen Wake Lock when supported. A dedicated display remains only a client: logging and diagnostics continue if the browser restarts.

See [Dedicated Display](docs/KIOSK.md).

## Hardware safety boundary


- `SocketCANTransport` exposes receive only; it has no transmit method.
- The operating system must still configure the factory CAN interface in **listen-only** mode before use.
- No factory CAN termination is assumed or added by software.
- Factory pins, colors, bitrates and CAN IDs remain undefined until measured on PKB839.
- MGO Brain must remain removable without affecting normal vehicle operation.

## Run in simulator mode

Default `config/sources.json` enables only the simulator:

```bash
git clone https://github.com/chup1runov/mgo-brain.git
cd mgo-brain
python -m venv .venv
source .venv/bin/activate
pip install -e '.[analytics]'
uvicorn mgo_brain.main:app --host 0.0.0.0 --port 8080
```

Install optional hardware libraries when developing hardware adapters:

```bash
pip install -e '.[dev,analytics,hardware]'
```

## Main API

- `GET /health`
- `GET /api/v1/state`
- `GET /api/v1/sources`
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
- `WS /ws/live`

## Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Hardware adapters](docs/HARDWARE_ADAPTERS.md)
- [Local UI](docs/UI.md)
- [Fault laboratory](docs/FAULT_LAB.md)
- [Roadmap](docs/ROADMAP.md)
- [Project handoff](docs/PROJECT_HANDOFF.md)
- [Changelog](CHANGELOG.md)
