# MGO Brain Project Handoff

## North Star

Turn a mechanically simple 2017 Microcar M.Go / F8 0.5 with Progress ACT / Lombardini LDW502 into a deeply observable vehicle without replacing or taking control of its factory safety-critical systems.

MGO Brain combines factory signals, added sensors, trip/service history and local diagnostics into one digital-twin-style interface. AI may explain and correlate evidence, but local deterministic logic remains responsible for critical alerts.

## Vehicle basis

- Microcar M.Go / F8 0.5, model year 2017.
- Progress ACT / Lombardini LDW502, 505 cm³ diesel.
- Front drive, CVT, D/N/R reduction gearbox.
- Progress ACT does not expose the same normal OBD-II/engine-ECU path as the DCI variant.
- MGO4/P98 documentation identifies integrated BFI/fuse-box electronics and a CAN-related harness.

## Current release

`v0.4.0`

Implemented:

- canonical signal/quality/source model;
- 80-signal registry;
- simulator and vehicle state machine;
- start/trip detection and SQLite persistence;
- deterministic rules and nine fault scenarios;
- ACTIVE/CLEARED alerts and subsystem health;
- Parquet/DuckDB historical analytics;
- healthy reference + rolling baselines with qualification;
- anomaly scoring and post-trip reports;
- trip comparison;
- complete local PWA console: HOME / ENGINE / CVT / POWER / TRIPS / SERVICE / LAB;
- simulator fault-lab UI and raw-state inspector.

## Hardware direction

Preferred central platform: AutoPi TMU CM4 or equivalent automotive Linux computer.

1. CAN0: factory MGO BFI/CAN, listen-only during discovery.
2. CAN1: separate MGO Sensor CAN.
3. ESP32-S3 SensorHub.
4. Isolated digital inputs / RS485 for OEM 12 V states not available via CAN.
5. Independent engine/CVT/power/TPMS/environment sensors as needed.
6. Phone/browser is UI, not the always-on vehicle computer.

## Non-negotiable safety rules

- Never guess factory pins or wire colors.
- Never transmit to factory CAN during discovery.
- Never add CAN termination until topology is measured.
- MGO Brain must not be required for engine start, braking, gear selection or OEM critical warnings.
- Preserve OEM warnings/sensors where possible.
- Critical alarms work without AI or Internet.
- Historical analytics are outside the real-time safety path.

## Immediate software priority

Continue with v0.5 before physical vehicle survey:

1. formal SourceAdapter interface;
2. migrate simulator behind that interface;
3. SocketCAN receive-only adapter;
4. DBC loader/decoder;
5. SensorHub CAN protocol;
6. Modbus/RS485 adapter;
7. battery, TPMS and GNSS/IMU adapter interfaces;
8. source selection/configuration.

## Deferred physical milestone

Later, photograph and electrically survey the BFI/fuse box, dashboard, D/N/R selector, battery, engine sensors, starter, alternator, glow system, gearbox and CVT. Confirm the factory CAN pair and bitrate before permanent connection.
