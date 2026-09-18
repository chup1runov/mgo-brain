# MGO Brain Roadmap

## v0.1.0 — Software foundation
- [x] Canonical signal model, simulator, state machine, persistence, REST/WebSocket, Docker/CI.

## v0.2.0 — Fault and health simulator
- [x] Nine fault scenarios, deterministic rules, alert lifecycle and subsystem health.

## v0.3.0 — Historical analytics
- [x] Parquet/DuckDB, reference/rolling baselines, anomaly scoring, reports and comparison.

## v0.4.0 — Complete local UI
- [x] HOME / ENGINE / CVT / POWER / TRIPS / SERVICE / LAB PWA.

## v0.5.0 — Hardware abstraction (current)
- [x] Formal `SourceAdapter` / `SourceUpdate` contract.
- [x] Simulator migrated behind SourceAdapter.
- [x] Multi-source `SourceMux`.
- [x] Freshness/quality-aware `StateAggregator`.
- [x] Preferred-source failover when the primary becomes stale.
- [x] STALE-aware vehicle state machine and subsystem readiness.
- [x] Receive-only SocketCAN transport API.
- [x] DBC loader/decoder with canonical mapping.
- [x] SensorHub CAN v1 protocol and adapter.
- [x] Modbus/RS485 digital-input adapter.
- [x] Modbus/RS485 analog-input adapter.
- [x] VE.Direct battery-monitor parser/adapter.
- [x] Generic TPMS adapter.
- [x] Generic GNSS/IMU adapter.
- [x] Source selection through `config/sources.json`.
- [x] Optional hardware dependency CI.

## v0.5.1 — CAN Survey Toolkit (current)
- [x] candump parser.
- [x] baseline/action differential comparison.
- [x] candidate CAN ID ranking.
- [x] changed-byte ranking with noise penalty.
- [x] presence-only ID detection.
- [x] safe message-only DBC draft.
- [x] browser LAB workflow.
- [x] `mgo-survey` CLI.

## v0.5.2 — Commissioning & Replay Toolkit (current)
- [x] Receive-only CAN recorder.
- [x] Standard candump formatting.
- [x] Offline candump replay transport.
- [x] Replay timing scale / no-delay mode.
- [x] Persistent survey-session evidence store.
- [x] Browser Save Survey Session workflow.
- [x] Survey-session API.
- [x] `mgo-can-record` CLI.
- [x] `mgo-can-replay` CLI.
- [x] `mgo-survey-session` CLI.
- [x] Recorder/replay/session round-trip tests.

## v0.5.3 — Deployment Pack (current)
- [x] Environment-based runtime paths.
- [x] Separate config/data directories.
- [x] systemd auto-start unit.
- [x] Avahi HTTP service descriptor.
- [x] `mgo-doctor` preflight diagnostics.
- [x] `mgo-backup` consistent backup.
- [x] SQLite online backup handling.
- [x] Deployment layout tests.

## Hardware survey milestone — next

- [ ] Photograph BFI/fuse-box wiring.
- [ ] Identify factory CAN twisted pair.
- [ ] Confirm bus resistance.
- [ ] Determine bitrate.
- [ ] Bring interface up in OS listen-only mode.
- [ ] Record first passive CAN dumps.
- [ ] Map door, D/N/R, brake, lights, speed and fuel one action at a time.
- [ ] Create first `MGO4_CAN.dbc`.

## v0.6 — First real vehicle data
- [ ] AutoPi installed with protected power.
- [ ] Factory CAN connected listen-only.
- [ ] Real speed/gear/body signals normalized.
- [ ] Simulator/real sources selectable on the installed unit.
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
