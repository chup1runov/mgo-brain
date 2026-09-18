# Changelog

All notable changes to MGO Brain are tracked here.

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

### Changed
- Service pipeline now processes rule results through `AlertManager` before health evaluation.
- Simulator drive-cycle timing can adapt to fault scenarios such as slow cranking.
- Project package version advanced to 0.2.0.

## [0.1.0] - 2026-09-18

### Added
- Canonical vehicle signal model with source and quality metadata.
- Registry of 80 planned/simulated signals.
- Progress ACT / MGO maintenance registry.
- Synthetic M.Go drive-cycle simulator.
- Vehicle mode inference.
- Start and trip detection.
- SQLite metadata store and JSONL trip telemetry.
- Deterministic safety-rule engine.
- Initial adaptive start/battery baselines.
- FastAPI REST API and WebSocket live stream.
- Mobile-friendly local dashboard.
- AI-context endpoint.
- GitHub Actions CI and Docker packaging.
