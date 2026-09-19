# Instructions for the next engineering agent

Read START_HERE_RU.md, docs/CHAT_HANDOFF_RU.md, docs/AUDIT_2026-09-19_RU.md and docs/REMAINING_WORK_RU.md before changing this project.

Scope: MGO Brain / Microcar M.Go only. The owner's other projects are unrelated.

## Evidence and safety

- Read the actual repository and its current SHA before asserting implementation status.
- Preserve the owner's software-first preference; hardware survey has been postponed, not completed.
- Never invent manufacturer limits, stock CAN mappings, wire colors, connector pins, sensor threads or vehicle measurements.
- Hardware candidates are not purchase orders or proof of compatibility.
- Factory CAN is receive-only during commissioning, with driver/controller listen-only verified separately.
- Critical vehicle operation and OEM warnings must not depend on this prototype.
- UNKNOWN/STALE/INVALID are not healthy measurements. Do not clear a critical alert merely because its sensor stopped reporting.
- Bench inputs are synthetic SourceUpdates, not verified physical protocol/device tests.
- Do not mix simulator/bench history with real-vehicle training data.

## Development

- Branch, test, inspect the actual diff, then integrate without force-pushing over unrelated work.
- Run pytest, tools/repository_audit.py and the real-browser audit for UI changes. Preserve failed-test evidence and fix the cause, not just the assertion.
- A static string test, passing import or simulated demo is not a hardware integration test.
- Record what was not tested. Do not announce 100% readiness or a validated diagnosis based on synthetic values.
- Keep meaningful documentation, source provenance, regressions and handoff synchronized with code.
- Do not publish private telemetry, credentials, deployment .env files or access tokens.
- Do not create background tasks or cloud/API expenses unless requested; local Ask MGO is a deterministic fallback, not a local LLM.

## Architecture

Canonical signals -> source aggregation -> local rules/alerts -> UI and separately persisted history/analytics. Preserve fail-visible behavior and the read/observe-only boundary. Request sizes are bounded; current networking is trusted-local, not authenticated public hosting.
