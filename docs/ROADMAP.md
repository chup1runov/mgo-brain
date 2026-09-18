# MGO Brain Roadmap

## v0.1.0 — Software foundation

- [x] Canonical signal model.
- [x] 80-signal registry.
- [x] Vehicle state machine.
- [x] Synthetic M.Go simulator.
- [x] Start and trip detection.
- [x] Deterministic safety rules.
- [x] SQLite event/start/trip metadata.
- [x] Live REST/WebSocket API.
- [x] Initial dashboard.
- [x] AI-context endpoint.
- [x] CI and Docker packaging.

## v0.2.0 — Fault and health simulator

- [x] Fault injection framework.
- [x] Weak-battery scenario.
- [x] Starter degradation scenario.
- [x] Glow-plug / preheat anomaly scenario.
- [x] Alternator under/over-voltage scenarios.
- [x] Oil-pressure failure scenarios.
- [x] Cooling over-temperature scenarios.
- [x] CVT drift/over-temperature scenarios.
- [x] Subsystem health model: ENGINE / CVT / ELECTRICAL / TYRES / BRAKES.
- [x] Explicit ACTIVE → CLEARED alert lifecycle.
- [x] Fault-laboratory API and dashboard controls.
- [x] Automated fault-scenario tests.

## v0.3.0 — Historical analytics (current)

- [x] Streaming flat trip telemetry with JSONL fallback.
- [x] Parquet/ZSTD trip finalization.
- [x] DuckDB analytics layer.
- [x] Reference and rolling baselines.
- [x] 20-sample baseline qualification period.
- [x] Exclude unhealthy starts/trips from reference learning.
- [x] Trend/anomaly score.
- [x] Baseline rebuild after restart.
- [x] Compare-trip API.
- [x] Stored post-trip report.
- [x] Running-only trip aggregation for oil pressure and related metrics.

## v0.4 — Complete local UI

- [ ] HOME screen.
- [ ] ENGINE screen.
- [ ] CVT screen.
- [ ] ELECTRICAL screen.
- [ ] TRIPS screen.
- [ ] SERVICE screen.
- [ ] LAB/debug screen.
- [ ] PWA/offline shell.

## v0.5 — Hardware abstraction

- [ ] Generic SourceAdapter protocol.
- [ ] SocketCAN adapter.
- [ ] CAN DBC decoder support.
- [ ] SensorHub CAN protocol.
- [ ] Modbus/RS485 input adapter.
- [ ] Battery-monitor adapter.
- [ ] TPMS adapter.
- [ ] GNSS/IMU adapter.

## Hardware survey milestone

Before any factory-wire integration:

- [ ] Photograph BFI/fuse-box wiring.
- [ ] Identify factory CAN twisted pair.
- [ ] Confirm CAN bus resistance and bitrate.
- [ ] Record first listen-only CAN dumps.
- [ ] Map one action at a time: door, D/N/R, brake, lights, speed, fuel.
- [ ] Create first `MGO4_CAN.dbc`.

## v0.6 — First real vehicle data

- [ ] AutoPi installed with protected power.
- [ ] Factory CAN connected listen-only.
- [ ] Simulator and real source switchable by configuration.
- [ ] Real speed/gear/body signals normalized.
- [ ] Logging verified over multiple trips.

## v0.7 — Engine and power instrumentation

Only after physical dimensions/threads/signals are confirmed:

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

## v1.0 — MGO Brain operational

Definition of done:

- [ ] automatic startup/shutdown;
- [ ] failure of MGO Brain cannot prevent normal vehicle operation;
- [ ] factory CAN read passively;
- [ ] Sensor CAN operational;
- [ ] trip/start/service history retained;
- [ ] RPM, speed, coolant, oil pressure/temp, electrical power and CVT observability;
- [ ] deterministic local critical alarms;
- [ ] learned reference/rolling baselines;
- [ ] mobile local dashboard;
- [ ] AI analysis uses structured data + documentation + service history;
- [ ] core operation remains useful without Internet access.
