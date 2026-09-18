# MGO Brain Project Handoff

## North Star

Turn a mechanically simple 2017 Microcar M.Go / F8 0.5 with Progress ACT / Lombardini LDW502 into a deeply observable vehicle without replacing or taking control of its factory safety-critical systems.

MGO Brain combines factory signals, added sensors, trip/service history and local diagnostics into one digital-twin-style interface. AI may explain and correlate evidence, but local deterministic logic remains responsible for critical alerts.

## Vehicle basis

- Vehicle: Microcar M.Go / F8 0.5, model year 2017.
- Engine: Progress ACT / Lombardini LDW502, 505 cm³ diesel.
- Drivetrain: front drive with CVT and D/N/R reduction gearbox.
- Progress ACT does not expose the same normal OBD-II/engine-ECU path as the DCI variant.
- MGO4/P98 body electronics use integrated BFI/fuse-box electronics and a CAN-related harness documented in the parts catalogue.

## Current software state

Current release: `v0.3.0`.

Working features:

- simulator-driven source and canonical vehicle signal model;
- signal quality/source metadata and 80-signal registry;
- vehicle mode, start and trip detection;
- SQLite event/start/trip/report persistence;
- deterministic rules and nine injectable fault scenarios;
- ACTIVE → CLEARED alert lifecycle;
- subsystem health for ENGINE / CVT / ELECTRICAL / TYRES / BRAKES;
- streaming flat trip telemetry;
- Parquet/ZSTD finalization with DuckDB analytics;
- healthy reference baseline + rolling baseline;
- 20-sample baseline qualification;
- exclusion of ATTENTION/CRITICAL starts/trips from healthy reference learning;
- baseline rebuild after restart;
- anomaly scoring;
- compare-trip API;
- stored post-trip reports;
- REST API, WebSocket, dashboard and AI-context endpoint.

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
- Historical analytics must not sit in the real-time safety path.

## Immediate software priority

Continue with v0.4 before physical vehicle survey:

1. HOME screen.
2. ENGINE screen.
3. CVT screen.
4. ELECTRICAL screen.
5. TRIPS + post-trip reports UI.
6. SERVICE screen.
7. LAB/debug/fault-lab screen.
8. PWA/offline shell.

## Deferred physical milestone

When returning to the vehicle, perform a photographic/electrical survey around the BFI/fuse box, dashboard, D/N/R selector, battery, engine sensors, starter, alternator, glow system, gearbox and CVT. Confirm the factory CAN pair and bitrate before connecting a permanent interface.
