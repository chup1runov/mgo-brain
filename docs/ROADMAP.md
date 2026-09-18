# MGO Brain Roadmap

## v0.1.0 — Software foundation (current)

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

## v0.2 — Fault and health simulator

- [ ] Fault injection framework.
- [ ] Weak-battery scenario.
- [ ] Starter degradation scenario.
- [ ] Glow-plug / preheat anomaly scenario.
- [ ] Alternator under/over-voltage scenarios.
- [ ] Oil-pressure failure scenarios.
- [ ] Cooling over-temperature scenarios.
- [ ] CVT drift/over-temperature scenarios.
- [ ] Subsystem health model: ENGINE / CVT / ELECTRICAL / TYRES / BRAKES.
- [ ] Rule persistence/clear logic rather than only event de-duplication.

## v0.3 — Historical analytics

- [ ] Parquet trip telemetry.
- [ ] DuckDB analytics layer.
- [ ] Reference and rolling baselines.
- [ ] Baseline qualification period.
- [ ] Trend and anomaly scoring.
- [ ] Compare-trip API.
- [ ] Post-trip report.

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
