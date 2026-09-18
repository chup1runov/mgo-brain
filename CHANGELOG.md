# Changelog

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
