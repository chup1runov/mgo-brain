# MGO Brain Roadmap

## v0.1.0 — Software foundation

- [x] Canonical signal model and 80-signal registry.
- [x] Vehicle state machine and simulator.
- [x] Start/trip detection.
- [x] SQLite persistence.
- [x] REST/WebSocket/API foundation.
- [x] Docker + CI.

## v0.2.0 — Fault and health simulator

- [x] Nine fault-injection scenarios.
- [x] Deterministic fault rules.
- [x] ACTIVE → CLEARED lifecycle.
- [x] ENGINE / CVT / ELECTRICAL / TYRES / BRAKES health.
- [x] Honest UNKNOWN state for uninstrumented subsystems.
- [x] Fault-lab API/dashboard.

## v0.3.0 — Historical analytics

- [x] Streaming flat trip telemetry.
- [x] Parquet/ZSTD trip finalization.
- [x] DuckDB analytics.
- [x] Reference + rolling baselines.
- [x] 20-sample qualification period.
- [x] Exclude unhealthy samples from reference learning.
- [x] Baseline rebuild after restart.
- [x] Anomaly scoring.
- [x] Compare-trip API.
- [x] Stored post-trip reports.
- [x] Running-only trip aggregation.

## v0.4.0 — Complete local UI (current)

- [x] HOME.
- [x] ENGINE.
- [x] CVT.
- [x] POWER / ELECTRICAL.
- [x] TRIPS with reports and comparison.
- [x] SERVICE.
- [x] LAB/debug/fault laboratory.
- [x] PWA manifest + icon.
- [x] Offline application shell.
- [x] Dynamic API/WebSocket data excluded from stale-cache fallback.
- [x] Responsive mobile/desktop navigation.

## v0.5 — Hardware abstraction

- [ ] Formal SourceAdapter protocol.
- [ ] Simulator migrated behind SourceAdapter.
- [ ] SocketCAN receive-only adapter.
- [ ] DBC loader/decoder.
- [ ] SensorHub CAN protocol.
- [ ] Modbus/RS485 input adapter.
- [ ] Battery-monitor adapter.
- [ ] TPMS adapter.
- [ ] GNSS/IMU adapter.
- [ ] Source selection by configuration.

## Hardware survey milestone

- [ ] Photograph BFI/fuse-box wiring.
- [ ] Identify factory CAN twisted pair.
- [ ] Confirm bus resistance and bitrate.
- [ ] Record first listen-only CAN dumps.
- [ ] Map door, D/N/R, brake, lights, speed and fuel one action at a time.
- [ ] Create first `MGO4_CAN.dbc`.

## v0.6 — First real vehicle data

- [ ] AutoPi installed with protected power.
- [ ] Factory CAN connected listen-only.
- [ ] Real speed/gear/body signals normalized.
- [ ] Logging verified over multiple trips.

## v0.7 — Engine and power instrumentation

- [ ] Battery current/SoC monitor.
- [ ] RPM source.
- [ ] Independent coolant temperature.
- [ ] Oil pressure and oil temperature.
- [ ] Glow-current measurement.
- [ ] Starter-current/high-rate voltage capture.
- [ ] Alternator characterization.

## v0.8 — CVT / condition monitoring

- [ ] Primary/secondary CVT temperature.
- [ ] Gearbox temperature.
- [ ] RPM-speed CVT model.
- [ ] CVT baseline drift detection.
- [ ] Engine vibration node.
- [ ] Body-vs-engine vibration separation.

## v0.9 — Peripheral monitoring

- [ ] TPMS ×4.
- [ ] Brake thermal comparison.
- [ ] Cabin temperature/humidity/CO2.
- [ ] Water ingress sensors.
- [ ] Camera/event timestamps.

## v1.0 — Operational MGO Brain

- [ ] automatic startup/shutdown;
- [ ] MGO Brain failure cannot prevent normal vehicle operation;
- [ ] factory CAN read passively;
- [ ] Sensor CAN operational;
- [ ] trip/start/service history retained;
- [ ] RPM, speed, coolant, oil pressure/temp, electrical power and CVT observability;
- [ ] deterministic local critical alarms;
- [ ] learned reference/rolling baselines;
- [ ] mobile local dashboard;
- [ ] AI uses structured telemetry + documentation + service history;
- [ ] useful core operation without Internet access.
