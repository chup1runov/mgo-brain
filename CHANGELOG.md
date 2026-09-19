# Changelog

## [0.5.10] — 2026-09-19 — Audit and chat-independent handoff

### Added
- Russian entry point, complete material chat handoff, corrections register, explicit engineering backlog and recovery/new-chat instructions.
- Whole-repository inventory with content hashes, Python/JSON/JavaScript syntax checks and local Markdown-link checks.
- Real Chromium desktop/mobile smoke checks, RU/EN, local AI language and stale-value behavior.
- Regression coverage for unusable/non-finite data, source fallback/failure, alert lifecycle, storage failure, namespace separation, protocol validation and bounded requests.
- Persistent audit evidence under docs/audit/2026-09-19, separate from expiring Actions artifacts.
- Actual non-root Docker build/start smoke workflow.
- Original chat asset checksum manifest; original PNG bytes remain in the explicitly supplied separate backup archive.

### Fixed
- Unverified/stale/invalid values no longer act as current numeric evidence.
- A sensor failure supersedes its older GOOD reading; source fallback candidates are retained.
- No-source and all-unknown states no longer silently report a healthy running vehicle.
- Heartbeat ages values when all sources go silent; source EOF/failure is visible.
- Local alerts run before optional history work; history/Parquet failures are surfaced without suppressing current alerts.
- Missing evidence does not clear an active critical alert; severity escalation is a transition.
- Simulated/bench/vehicle storage is separated; no automatic import of old simulated history into a real baseline.
- Empty Modbus replies are INVALID rather than invented zero/False.
- VE.Direct byte framing/checksum validation; legacy text-only results remain UNVERIFIED.
- Factory CAN checks Linux listen-only mode before physical opening.
- Replay EOF and observed-DLC DBC draft handling.
- Request-body cap, browser Origin checks, default localhost bind and Docker-context exclusions.
- Explicit cloud-model configuration, bounded AI timeout/output, language propagation and local fallback on external failure.
- Backup output/symlink restrictions and Chromium update suppression removed.

### Still not claimed
- No real vehicle hardware qualification, confirmed MGO DBC, validated manufacturer thresholds, certified safety or universal diagnostic accuracy.
- See docs/REMAINING_WORK_RU.md for packaging, protocol-level bench, crash recovery, baseline, time-integration, security and hardware work.

## Historical milestones

The original changes and documents are preserved in Git history and docs/ROADMAP.md.

- 0.5.9: multi-source software integration bench, not a physical protocol bench.
- 0.5.8: Russian-first driver UI.
- 0.5.7: Ask MGO read-only gateway and optional cloud provider.
- 0.5.6: project repository canon and engineering documents.
- 0.5.5: numeric CAN candidate discovery.
- 0.5.4: dedicated-display/kiosk scaffolding.
- 0.5.3: deployment, doctor and backup scaffolding.
- 0.5.2: recording/replay and survey sessions.
- 0.5.1: differential CAN survey toolkit.
- 0.5.0: hardware source abstraction.
- 0.4.0: local web console.
- 0.3.0: historical analytics and simple baselines.
- 0.2.0: fault scenarios and health/alert model.
- 0.1.0: simulator, canonical state, storage and API foundation.
