# MGO Brain v0.5.6

MGO Brain is a read/observe-first telemetry, diagnostics and digital-twin project for a **Microcar M.Go / F8 0.5 (2017)** with **Progress ACT / Lombardini LDW502**.

It deliberately does **not** control the vehicle. Vehicle-critical OEM systems remain independent.

## Current release: v0.5.6

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

v0.5.1 adds differential CAN research: baseline vs one-action candump, ranked IDs/bytes and a safe message-only DBC draft.

```bash
mgo-survey baseline.log action.log --label driver_door_open --json-out analysis.json --dbc-out draft.dbc
```

See [CAN Survey Toolkit](docs/CAN_SURVEY.md).

### Commissioning & replay

v0.5.2 adds receive-only CAN recording, offline replay and persistent research sessions.

```bash
mgo-can-record --channel can0 --seconds 10 --output capture.log
mgo-can-replay capture.log --speed 0
mgo-survey-session baseline.log action.log --label driver_door_open
```

See [Commissioning & Replay](docs/COMMISSIONING.md).

### Deployment Pack

v0.5.3 prepares MGO Brain to run as an appliance on a Linux vehicle computer:

- environment-controlled runtime paths;
- systemd auto-start;
- Avahi HTTP advertisement;
- `mgo-doctor`;
- `mgo-backup`;
- SQLite-safe backup.

See [deployment/README.md](deployment/README.md).

### Dedicated display

v0.5.4 adds `mgo-kiosk`: wait for backend health, then open Chromium/Chrome full-screen. The display remains only a client.

See [Dedicated Display](docs/KIOSK.md).

### Numeric signal discovery

v0.5.5 compares timed CAN logs with an external reference series such as GPS speed, testing 8/16-bit signed/unsigned LE/BE hypotheses and ranking correlation/scaling candidates.

```bash
mgo-discover-numeric drive.log gps_speed.csv --label vehicle_speed_gps
```

See [Numeric Signal Discovery](docs/NUMERIC_DISCOVERY.md).

### Repository engineering pack

v0.5.6 adds the durable MGO Brain project canon: safety/evidence policies, vehicle baseline, BOM, installation/runbooks, ADRs, privacy/testing/recovery docs and standard GitHub project files.

## Hardware safety boundary

- `SocketCANTransport` exposes receive only; it has no transmit method.
- The OS must configure the factory CAN interface **listen-only** during discovery.
- No factory CAN termination is assumed or added by software.
- Factory pins, colors, bitrates and CAN IDs remain undefined until measured on this MGO.
- MGO Brain must remain removable without affecting normal vehicle operation.

## Run in simulator mode

```bash
git clone https://github.com/chup1runov/mgo-brain.git
cd mgo-brain
python -m venv .venv
source .venv/bin/activate
pip install -e '.[analytics]'
uvicorn mgo_brain.main:app --host 0.0.0.0 --port 8080
```

Install hardware/development extras with:

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

## Repository canon

GitHub is the durable source of truth for substantial **MGO Brain** knowledge. Read [PROJECT.md](PROJECT.md) and the [documentation index](docs/INDEX.md).

## Documentation

- [Documentation index](docs/INDEX.md)
- [Project canon](PROJECT.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Hardware adapters](docs/HARDWARE_ADAPTERS.md)
- [Local UI](docs/UI.md)
- [Fault laboratory](docs/FAULT_LAB.md)
- [Roadmap](docs/ROADMAP.md)
- [Project handoff](docs/PROJECT_HANDOFF.md)
- [Changelog](CHANGELOG.md)
