# MGO Brain Project Handoff

## North Star

Turn a mechanically simple 2017 Microcar M.Go / F8 0.5 with Progress ACT / Lombardini LDW502 into a deeply observable vehicle without replacing or taking control of its factory safety-critical systems.

MGO Brain should combine factory signals, added sensors, trip/service history and local diagnostics into a single digital-twin-style interface. AI may explain and correlate evidence, but local deterministic logic remains responsible for critical alerts.

## Vehicle basis

- Vehicle: Microcar M.Go / F8 0.5, model year 2017.
- Engine: Progress ACT / Lombardini LDW502, 505 cm³ diesel.
- Drivetrain: front drive with CVT and D/N/R reduction gearbox.
- Factory diagnostics: Progress ACT does not provide the same normal OBD-II/engine-ECU path as the DCI variant.
- Factory body electronics: MGO4/P98 uses integrated BFI/fuse-box electronics and has a CAN-related harness in the parts documentation.

## Current software state

Current release: `v0.2.0`.

Working features:

- simulator-driven source;
- canonical vehicle signal model;
- signal quality/source metadata;
- 80-signal registry;
- vehicle mode inference;
- start/trip detectors;
- SQLite metadata persistence;
- JSONL trip telemetry;
- basic rule engine;
- starter/battery baselines;
- FastAPI REST API;
- WebSocket live telemetry;
- minimal dashboard;
- AI-context endpoint.
- nine fault-injection scenarios;
- ACTIVE → CLEARED alert lifecycle;
- subsystem health engine for ENGINE / CVT / ELECTRICAL / TYRES / BRAKES;
- fault-laboratory API and dashboard controls;
- 12 automated tests covering v0.1 core + v0.2 fault/health behavior.

## Hardware direction

Preferred central platform: AutoPi TMU CM4 or equivalent automotive Linux computer.

Planned topology:

1. CAN0: factory MGO BFI/CAN, initially listen-only.
2. CAN1: separate MGO Sensor CAN.
3. ESP32-S3 SensorHub for local acquisition.
4. Isolated digital inputs / RS485 modules for OEM 12 V states not recoverable from CAN.
5. Independent sensors for oil pressure/temp, coolant temperature, RPM if necessary, CVT temperatures, vibration, battery/power, TPMS and cabin/environment.
6. Phone/browser as UI, not as the primary always-on vehicle computer.

## Non-negotiable safety rules

- Do not guess factory pin numbers or wire colors.
- Do not transmit to factory CAN during discovery.
- Do not add termination to factory CAN until topology is measured.
- Do not make MGO Brain required for engine start, braking, gear selection, OEM oil/overheat warnings or other vehicle-critical functions.
- Added measurements should preserve OEM warnings and sensors where possible.
- Critical alarms must work without AI or Internet access.

## Immediate software priority

Continue with v0.3 before physical vehicle survey:

1. Parquet trip telemetry;
2. DuckDB local analytics;
3. reference + rolling baselines;
4. baseline qualification period;
5. trend/anomaly scoring;
6. compare-trip API;
7. post-trip report.

## Deferred physical milestone

When returning to the vehicle, perform a photographic/electrical survey around the BFI/fuse box, dashboard, D/N/R selector, battery, engine sensors, starter, alternator, glow system, gearbox and CVT. Confirm the factory CAN pair and bitrate before connecting a permanent interface.
