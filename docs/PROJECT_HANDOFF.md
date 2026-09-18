# MGO Brain Project Handoff

## North Star

Turn the 2017 Microcar M.Go / F8 0.5 with Progress ACT / Lombardini LDW502 into a deeply observable vehicle without replacing or controlling its factory safety-critical systems.

## Vehicle basis
- Microcar M.Go / F8 0.5, 2017.
- Progress ACT / Lombardini LDW502, 505 cm³ diesel.
- CVT with D/N/R reduction gearbox.
- Progress ACT does not expose the same normal OBD-II engine path as the DCI version.
- MGO4/P98 documentation indicates BFI/fuse-box electronics and a CAN-related harness.

## Current release

`v0.5.5`

Software now includes:
- canonical signal/state model;
- simulator, fault lab and health engine;
- SQLite + Parquet/DuckDB history;
- reference/rolling baselines and reports;
- complete local PWA console;
- formal hardware source abstraction;
- SourceMux + StateAggregator;
- receive-only SocketCAN layer;
- DBC, SensorHub CAN, Modbus, VE.Direct, TPMS and GNSS/IMU adapter boundaries;
- source freshness/STALE handling;
- configuration-driven source selection;\n- CAN Survey Toolkit for baseline/action candump comparison and safe DBC draft generation;\n- receive-only CAN recorder and offline replay;\n- persistent survey-session evidence store with raw logs, analysis and DBC draft;\n- deployment pack with systemd, mDNS advertisement, doctor and backup tooling;\n- dedicated-display kiosk launcher and auto-restart service;\n- numeric CAN signal discovery against external reference time series.

## Planned installed topology

1. AutoPi TMU CM4 or equivalent Linux computer.
2. CAN0: factory MGO BFI/CAN, OS-configured listen-only during discovery.
3. CAN1: separate MGO Sensor CAN.
4. ESP32-S3 SensorHub.
5. Isolated Modbus/RS485 digital inputs for OEM 12 V states not found on CAN.
6. Independent engine/CVT/power/TPMS/environment sensors as needed.
7. Phone/browser as UI only.

## Non-negotiable safety rules
- Never guess factory pins/wire colors.
- Never transmit to factory CAN during discovery.
- Never assume/add termination before measuring topology.
- MGO Brain must not be required for engine start, braking, gear selection or OEM critical warnings.
- Critical alerts work without AI or Internet.
- Historical analytics are outside the real-time safety path.

## Next milestone

v0.5.5 also prepares numeric CAN reverse-engineering before real PKB839 logs are available. Next, perform the physical CAN/electrical survey on PKB839:

1. photograph BFI/fuse box and nearby harnesses;
2. identify candidate twisted CAN pair;
3. measure bus resistance with power off;
4. determine bitrate;
5. configure the Linux CAN interface listen-only;
6. record passive CAN logs;
7. perform one-variable experiments (door, D/N/R, brake, lights, speed, fuel);
8. begin `MGO4_CAN.dbc`.

After that, v0.6 replaces/augments the simulator with real normalized vehicle signals.
