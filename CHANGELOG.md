# Changelog

All notable changes to MGO Brain are tracked here.

## [0.4.0] - 2026-09-18

### Added
- Seven-view local console: HOME, ENGINE, CVT, POWER, TRIPS, SERVICE and LAB.
- Live WebSocket telemetry across the console.
- Subsystem-health and active-alert presentation.
- Start-history and baseline views.
- Trip report viewer and two-trip comparison UI.
- Maintenance-plan view.
- Fault laboratory and raw-state inspector.
- PWA manifest, SVG icon and service worker.
- Offline application shell while dynamic API/WebSocket data remains live-only.
- `GET /api/v1/reports`.
- Static UI/PWA automated tests.
- `docs/UI.md`.

## [0.3.0] - 2026-09-18

### Added
- Streaming flat trip telemetry and Parquet/ZSTD finalization.
- DuckDB historical analytics.
- Persistent healthy reference and rolling baselines.
- 20-sample baseline qualification.
- Exclusion of ATTENTION/CRITICAL samples from reference learning.
- Historical anomaly score.
- Baseline rebuild after restart.
- Stored post-trip reports and trip comparison API.
- Parquet/DuckDB CI round-trip test.

### Fixed
- Stopped-engine zero oil pressure no longer contaminates running trip minimums.
- Python package discovery and Docker editable-install paths.

## [0.2.0] - 2026-09-18

### Added
- Nine diagnostic fault simulations.
- Expanded deterministic rules.
- ACTIVE/CLEARED alert lifecycle.
- Subsystem health engine.
- Fault-laboratory REST controls and UI.
- Automated v0.2 tests.

## [0.1.0] - 2026-09-18

### Added
- Canonical signal model and registry.
- Simulator, state machine, start/trip detection.
- SQLite persistence and telemetry logging.
- FastAPI/REST/WebSocket.
- Initial dashboard and AI-context endpoint.
- Docker and GitHub Actions CI.
