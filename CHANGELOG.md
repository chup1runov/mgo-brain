# Changelog

All notable changes to MGO Brain are tracked here.

## [0.3.0] - 2026-09-18

### Added
- Streaming flat trip telemetry designed for Parquet conversion.
- DuckDB-backed Parquet/ZSTD historical analytics.
- Persistent reference and rolling baselines for start and trip metrics.
- 20-sample baseline qualification period with explicit UNQUALIFIED state.
- Healthy-reference protection: diagnostic ATTENTION/CRITICAL starts and trips are excluded from reference learning.
- Heuristic historical anomaly score with NORMAL / WATCH / ATTENTION states.
- Baseline rebuild from persisted starts/trips after restart.
- Stored post-trip reports.
- Trip comparison API.
- Historical analytics and baseline API endpoints.
- DuckDB/Parquet CI round-trip test.

### Fixed
- Stopped-engine zero oil pressure no longer contaminates the minimum running oil-pressure metric.
- Python package discovery for editable CI installs.
- Docker runtime path behavior by using editable project installation.

## [0.2.0] - 2026-09-18

### Added
- Fault-injection controller with nine diagnostic scenarios.
- Weak-battery, starter, glow, alternator, oil-pressure, overheating and CVT fault simulations.
- Simulated glow current, starter current, alternator voltage, CVT temperatures and CVT ratio deviation.
- Deterministic rules for the new fault channels.
- Explicit alert lifecycle with ACTIVE and CLEARED states plus history.
- Subsystem health engine for ENGINE, CVT, ELECTRICAL, TYRES and BRAKES.
- Honest `UNKNOWN` health state for subsystems that are not yet instrumented.
- Fault-laboratory REST controls.
- Dashboard subsystem-health, active-alert and fault-injection panels.
- Automated tests for all v0.2 fault classes and health/alert behavior.
- `docs/FAULT_LAB.md`.

## [0.1.0] - 2026-09-18

### Added
- Canonical vehicle signal model with source and quality metadata.
- Registry of 80 planned/simulated signals.
- Progress ACT / MGO maintenance registry.
- Synthetic M.Go drive-cycle simulator.
- Vehicle mode inference.
- Start and trip detection.
- SQLite metadata store.
- Deterministic safety-rule engine.
- Initial adaptive start/battery baselines.
- FastAPI REST API and WebSocket live stream.
- Mobile-friendly local dashboard.
- AI-context endpoint.
- GitHub Actions CI and Docker packaging.
