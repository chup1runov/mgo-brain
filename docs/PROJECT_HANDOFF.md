# MGO Brain Project Handoff

## Canon

GitHub is the canonical TAVRELI / MGO Brain engineering record. Chat is a working environment, not the durable source of truth.

Start with:

- `TAVRELI.md`
- `docs/INDEX.md`
- `docs/PROJECT_STATE.md`
- `docs/ROADMAP.md`
- `docs/OPEN_QUESTIONS.md`

## North Star

Turn the 2017 Microcar M.Go / F8 0.5 with Progress ACT / Lombardini LDW502 into a deeply observable vehicle without replacing or controlling its factory safety-critical systems.

## Current release

`v0.5.6`

## Implemented software

- canonical signal / VehicleState model;
- simulator and fault lab;
- deterministic rules, alert lifecycle and subsystem health;
- SQLite metadata + Parquet/DuckDB historical analytics;
- reference/rolling baselines and reports;
- local PWA console;
- hardware SourceAdapter / SourceMux / StateAggregator;
- receive-only SocketCAN abstraction;
- DBC, SensorHub CAN, Modbus, VE.Direct, TPMS and GNSS/IMU integration boundaries;
- signal freshness / STALE handling and fallback;
- binary CAN Survey Toolkit;
- receive-only CAN recording and offline replay;
- persistent survey evidence sessions;
- deployment systemd/mDNS/doctor/backup pack;
- dedicated-display kiosk launcher;
- numeric CAN discovery against an external reference time series.

## Engineering canon added in v0.5.6

- TAVRELI repo-first policy;
- safety and evidence policies;
- vehicle baseline;
- hardware BOM / machine-readable hardware plan;
- installation plan;
- first vehicle day runbook;
- signal catalog semantics;
- unresolved questions registry;
- data/privacy and AI design;
- testing / release / recovery documentation;
- external references and glossary;
- architecture decision records;
- standard GitHub contribution/security/repository files;
- CI repository-canon test.

## Planned installed topology

1. AutoPi TMU CM4 or equivalent automotive Linux computer.
2. CAN0: factory MGO BFI/CAN, OS-configured listen-only during discovery.
3. CAN1: private Sensor CAN.
4. ESP32-S3 SensorHub.
5. Isolated Modbus/RS485 inputs when OEM states are not available over CAN.
6. Independent engine/CVT/power/TPMS/environment sensors as needed.
7. Phone/browser first; dedicated display optional later.

## Non-negotiable safety rules

- never guess factory pins/wire colors;
- never transmit to factory CAN during discovery;
- never assume/add CAN termination before measuring topology;
- MGO Brain must not be required for engine start, braking, gear selection or OEM critical warnings;
- critical alerts work without AI/Internet;
- historical analytics are outside the real-time safety path;
- stale data is not current evidence.

## Next milestone

The useful offline software/tooling work is largely complete. The next evidence-producing milestone requires the actual vehicle:

1. photograph BFI/fuse box and relevant harnesses;
2. identify candidate CAN pair;
3. measure bus resistance with power off;
4. determine bitrate;
5. configure Linux CAN listen-only;
6. record passive logs;
7. run controlled one-variable experiments;
8. begin the first evidence-backed `MGO4_CAN.dbc`.

After that, v0.6 begins first real vehicle data integration.
