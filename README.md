# MGO Brain v0.1

Software-first prototype of the MGO Brain project for a Microcar M.Go / F8 0.5 (2017) with Progress ACT / Lombardini LDW502.

This version deliberately does **not** control the vehicle. It simulates sensor/CAN input, normalizes it into canonical signals, detects starts/trips, runs deterministic safety rules, stores events in SQLite, and exposes a local API + live dashboard.

## What works in v0.1

- Canonical signal model with quality/source metadata.
- Machine-readable v1 signal registry with 80 planned/simulated channels and source priorities.
- Initial maintenance-plan registry from the Progress ACT/MGO documentation.
- Vehicle state machine: OFF → ACC → IGNITION → PREHEAT → CRANKING → ENGINE_RUNNING/DRIVING → OFF.
- Built-in M.Go simulator (no hardware required).
- FastAPI local API.
- WebSocket live telemetry.
- SQLite event/start/trip metadata store.
- JSONL per-trip telemetry capture.
- Deterministic rules for oil-warning, overheating, under/over-voltage.
- First adaptive baseline metrics for cold-start duration and minimum crank voltage.
- AI-context endpoint that returns concise structured context rather than raw telemetry.
- Minimal mobile-friendly dashboard.

## Run

```bash
git clone https://github.com/chup1runov/mgo-brain.git
cd mgo-brain
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e .
uvicorn mgo_brain.main:app --host 0.0.0.0 --port 8080
```

Open: `http://localhost:8080/`

Or run with Docker:

```bash
docker build -t mgo-brain .
docker run --rm -p 8080:8080 mgo-brain
```

The simulator loops continuously. A complete simulated start/drive/stop cycle takes roughly one minute.

## API

- `GET /health`
- `GET /api/v1/state`
- `GET /api/v1/events`
- `GET /api/v1/trips`
- `GET /api/v1/starts`
- `GET /api/v1/health-summary`
- `GET /api/v1/ai/context`
- `GET /api/v1/spec/signals`
- `GET /api/v1/spec/maintenance`
- `WS  /ws/live`

## Architecture

```text
SourceAdapter (simulator now; CAN/SensorHub later)
        ↓
Normalizer / canonical signal names
        ↓
VehicleState + state machine
        ↓
Trip/Start detectors ──→ SQLite + trip telemetry
        ↓
Rules engine + baseline/anomaly layer
        ↓
REST/WebSocket API
        ↓
Dashboard / future AI gateway
```

## Canonical signals already modeled

Examples:

- `vehicle.speed`
- `vehicle.speed_gps`
- `engine.rpm`
- `engine.coolant_temp`
- `engine.oil_temp`
- `engine.oil_pressure`
- `engine.oil_warning`
- `engine.overheat_warning`
- `engine.glow_active`
- `engine.starter_active`
- `electrical.battery_voltage`
- `electrical.battery_current`
- `electrical.battery_soc`
- `transmission.gear`
- `transmission.cvt_ratio`
- `fuel.level`
- `body.driver_door`
- `controls.brake`
- `controls.parking_brake`
- `environment.ambient_temp`

## Hardware adapters planned next

The source interface is intentionally generic. Later adapters can be added independently for:

1. AutoPi/SocketCAN (`can.bfi`).
2. ESP32 SensorHub over CAN (`sensorhub.can`).
3. RS485/Modbus digital inputs.
4. Oil pressure/temperature sensor.
5. Coolant temperature sensor.
6. RPM pickup.
7. SmartShunt / battery monitor.
8. TPMS, vibration and cabin sensors.

## Safety boundary

MGO Brain v0.1 is read/observe-only. Future hardware should preserve this rule for vehicle-critical functions. Critical warnings must remain local and deterministic; AI is explanatory, not the sole safety mechanism.

## Project docs

- [Architecture](docs/ARCHITECTURE.md)
- [Roadmap](docs/ROADMAP.md)
- [Project handoff / continuation context](docs/PROJECT_HANDOFF.md)
- [Changelog](CHANGELOG.md)

## Development

```bash
pip install -e '.[dev]'
python -m compileall -q mgo_brain tests
pytest -q
```

GitHub Actions runs the compile/test suite on Python 3.11, 3.12 and 3.13 for pushes to `main` and pull requests.
