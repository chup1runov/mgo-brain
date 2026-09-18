# Changelog

## [0.5.6] - 2026-09-18

### Added
- TAVRELI repo-first canon policy.
- Documentation index and project-state snapshot.
- Vehicle baseline, hardware BOM and machine-readable hardware plan.
- Installation and first-vehicle-day runbooks.
- Dedicated safety and engineering-evidence policies.
- Signal-catalog semantics and unresolved-question registry.
- Data/privacy, AI gateway, testing, release and backup/recovery documentation.
- External reference index and glossary.
- Architecture Decision Records.
- LICENSE, CONTRIBUTING, SECURITY, CODEOWNERS, PR/issue templates and Dependabot.
- Broader runtime/private-data Git exclusions.
- Machine-readable project metadata and deployment vehicle-profile example.
- CI repository-canon test.

## [0.5.5] - 2026-09-18

### Added
- Numeric CAN field discovery against timestamped reference data.
- u8/s8 and u16 LE/BE signed/unsigned candidate extraction.
- Linear regression, correlation, R² and RMSE ranking.
- Counter-likeness penalty to reduce false positives.
- Synthetic varied-speed test dataset.
- Numeric discovery REST API and LAB UI.
- `mgo-discover-numeric` CLI.
- `docs/NUMERIC_DISCOVERY.md`.

## [0.5.4] - 2026-09-18

### Added
- Dedicated-screen `mgo-kiosk` launcher.
- Backend readiness polling before browser launch.
- Chromium/Chrome discovery and kiosk command profile.
- User-level systemd kiosk service.
- Kiosk environment template.
- PWA `?kiosk=1` mode and Screen Wake Lock request.
- Display/kiosk tests.
- `docs/KIOSK.md`.

## [0.5.3] - 2026-09-18

### Added
- Environment-driven runtime data/config paths.
- systemd vehicle-service template.
- Avahi HTTP service descriptor.
- `mgo-doctor` deployment preflight.
- `mgo-backup` consistent data/config archive.
- SQLite backup via the SQLite backup API.
- Deployment layout and runtime-settings tests.
- `deployment/README.md`.

## [0.5.2] - 2026-09-18

### Added
- Receive-only CAN recorder with standard candump output.
- Offline candump replay transport with timing scaling.
- Persistent survey-session evidence store.
- Saved-session LAB workflow and API.
- `mgo-can-record`, `mgo-can-replay` and `mgo-survey-session` commands.
- Recorder/replay/session round-trip tests.
- `docs/COMMISSIONING.md`.

## [0.5.1] - 2026-09-18

### Added
- CAN/candump parser for hash and bracket formats.
- Baseline-vs-action CAN differential analyzer.
- Ranking of candidate CAN IDs and changed byte positions.
- Noise-aware scoring for stable toggles vs counters.
- Safe message-only DBC draft generation.
- Survey sample dataset for demonstration/testing.
- Survey REST API.
- `mgo-survey` CLI.
- LAB UI for paste/analyze workflow.
- `docs/CAN_SURVEY.md`.

## [0.5.0] - 2026-09-18

### Added
- `SourceAdapter` and partial `SourceUpdate` contract.
- `SourceMux` for concurrent source fan-in.
- `StateAggregator` with signal freshness, quality and preferred-source fallback.
- Receive-only SocketCAN transport wrapper.
- Lazy DBC decoder and canonical signal mapping.
- SensorHub CAN v1 codec and source adapter.
- Modbus digital/analog source adapters plus optional pymodbus transport.
- VE.Direct text parser/adapter plus optional serial transport.
- Generic TPMS source adapter.
- Generic GNSS/IMU source adapter.
- Runtime source configuration and builder registry.
- `GET /api/v1/sources`.
- Optional `hardware` dependency group and dedicated CI job.

### Changed
- Core service now consumes SourceUpdates through StateAggregator instead of directly consuming MGOSimulator VehicleState.
- State machine ignores STALE/MISSING/INVALID signals.
- Health readiness no longer treats stale sensor sets as healthy.
- Setuptools package discovery now includes `mgo_brain*` subpackages.

## [0.4.0] - 2026-09-18
- Seven-view local PWA console and offline shell.

## [0.3.0] - 2026-09-18
- Historical Parquet/DuckDB analytics and baselines.

## [0.2.0] - 2026-09-18
- Fault laboratory, alert lifecycle and subsystem health.

## [0.1.0] - 2026-09-18
- Initial software foundation.
