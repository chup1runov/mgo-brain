# MGO Brain Roadmap

## Completed

### v0.1.0 — Software foundation
- [x] Canonical signal model, simulator, state machine, persistence, REST/WebSocket, Docker/CI.

### v0.2.0 — Fault and health simulator
- [x] Nine fault scenarios, deterministic rules, alert lifecycle and subsystem health.

### v0.3.0 — Historical analytics
- [x] Parquet/DuckDB, reference/rolling baselines, anomaly scoring, reports and comparison.

### v0.4.0 — Complete local UI
- [x] HOME / ENGINE / CVT / POWER / TRIPS / SERVICE / LAB PWA.

### v0.5.0 — Hardware abstraction
- [x] SourceAdapter / SourceUpdate / SourceMux / StateAggregator.
- [x] STALE-aware priority/failover.
- [x] Receive-only SocketCAN API.
- [x] DBC / SensorHub CAN / Modbus / VE.Direct / TPMS / GNSS boundaries.
- [x] Config-driven sources and hardware CI.

### v0.5.1 — CAN Survey Toolkit
- [x] Baseline/action candump differential analysis.
- [x] Candidate CAN ID/byte ranking.
- [x] Noise penalty and safe DBC message draft.
- [x] LAB + CLI workflow.

### v0.5.2 — Commissioning & Replay
- [x] CAN recorder.
- [x] Offline replay.
- [x] Persistent survey sessions and evidence files.
- [x] Browser/API/CLI workflows.

### v0.5.3 — Deployment Pack
- [x] Runtime config/data directories.
- [x] systemd / mDNS templates.
- [x] doctor and backup tooling.

### v0.5.4 — Display / Kiosk Pack
- [x] Kiosk launcher.
- [x] Backend readiness wait.
- [x] Browser auto-discovery/restart.
- [x] PWA kiosk + Screen Wake Lock.

### v0.5.5 — Numeric Signal Discovery
- [x] Timestamp/reference alignment.
- [x] u8/s8/u16 LE/BE hypotheses.
- [x] Linear fit / R² / RMSE.
- [x] Counter penalty.
- [x] LAB/API/CLI.

### v0.5.6 — Repository Canon & Engineering Pack
- [x] MGO Brain repo-first project policy.
- [x] Standard repository files and templates.
- [x] Documentation index / project state / open questions.
- [x] Safety and evidence policies.
- [x] Vehicle baseline / BOM / hardware plan.
- [x] Installation and first-vehicle-day runbooks.
- [x] Signal catalog semantics.
- [x] Data/privacy + AI design.
- [x] Testing / release / backup-recovery docs.
- [x] References / glossary / ADRs.
- [x] Runtime/private-data Git exclusions.
- [x] CI repository-canon test.

### v0.5.7 — Ask MGO / AI Gateway
- [x] Read-only AI toolbox.
- [x] Deterministic question→evidence router.
- [x] Local no-cloud fallback provider.
- [x] Optional OpenAI Responses API provider.
- [x] Evidence size bounding / raw high-volume exclusion.
- [x] Precise location redaction for external AI by default.
- [x] AI status/tools/evidence/ask REST API.
- [x] HOME “Спросить MGO” UI.
- [x] `mgo-ask` CLI.
- [x] Optional AI dependency CI job.
- [x] AI safety/privacy regression tests.

### v0.5.8 — Russian Driver UI & Localization
- [x] Russian default PWA language.
- [x] English fallback via `?lang=en`.
- [x] RU/EN header toggle.
- [x] Localized subsystem/status/mode labels.
- [x] Localized maintenance labels.
- [x] Localized driver-facing trip/start strings.
- [x] Ask MGO language follows UI language.
- [x] Russian PWA manifest metadata.
- [x] Localization regression tests.
- [x] Canonical API/signal identifiers remain unchanged.

### v0.5.9 — Bench / Integration Simulation Pack
- [x] Multi-source bench controller.
- [x] Independent CAN / SensorHub / SmartShunt / Modbus / TPMS / GNSS channels.
- [x] SourceMux + StateAggregator end-to-end path.
- [x] Full start → trip → stop virtual cycle.
- [x] Normal / weak battery / undercharge / low-oil / overheat / CVT-overheat scenarios.
- [x] SensorHub-dropout STALE/UNKNOWN validation.
- [x] Bench source configuration selectable by environment.
- [x] Bench scenario REST API + LAB controls.
- [x] Headless `mgo-bench-smoke`.
- [x] Start/trip/health/alert/Ask MGO integration tests.

## Next physical milestone — Hardware Survey

- [ ] Photograph BFI/fuse-box wiring.
- [ ] Identify factory CAN twisted pair.
- [ ] Confirm bus resistance/topology.
- [ ] Determine bitrate.
- [ ] Bring CAN interface up OS-level listen-only.
- [ ] Record first passive CAN dumps.
- [ ] Map one-variable binary states.
- [ ] Record varied drive + independent speed reference.
- [ ] Create first evidence-backed `MGO4_CAN.dbc`.

## v0.6 — First real vehicle data

- [ ] Install main computer with protected power.
- [ ] Factory CAN listen-only connection.
- [ ] Real speed/gear/body signals normalized.
- [ ] Real/simulator/replay source switching.
- [ ] Multiple-trip logging validation.

## v0.7 — Engine and power instrumentation

- [ ] Battery current/SoC monitor.
- [ ] RPM source.
- [ ] Independent coolant temperature.
- [ ] Oil pressure + temperature.
- [ ] Glow current.
- [ ] Starter-current/high-rate voltage.
- [ ] Alternator characterization.

## v0.8 — CVT / condition monitoring

- [ ] Primary/secondary CVT temperature.
- [ ] Gearbox temperature.
- [ ] RPM-speed CVT model.
- [ ] CVT drift detection.
- [ ] Engine vibration node.
- [ ] Body-vs-engine vibration separation.

## v0.9 — Peripheral monitoring

- [ ] TPMS ×4.
- [ ] Brake thermal comparison.
- [ ] Cabin environment.
- [ ] Water ingress.
- [ ] Camera/event links.

## v1.0 — Operational MGO Brain

- [ ] automatic startup/shutdown;
- [ ] Brain failure cannot prevent normal vehicle operation;
- [ ] factory CAN passively read;
- [ ] Sensor CAN operational;
- [ ] robust trip/start/service history;
- [ ] RPM/speed/coolant/oil/electrical/CVT observability;
- [ ] local critical alarms;
- [ ] learned baselines;
- [ ] Russian driver-facing UI;
- [ ] structured AI analysis;
- [ ] useful operation without Internet.
