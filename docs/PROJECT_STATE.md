> Актуальная проверенная точка: **v0.5.10**, аудит 19.09.2026. Начните с [русской точки входа](../START_HERE_RU.md). Более ранние отметки «готово» ниже относятся к программным прототипам, не к проверке автомобиля.

# Project State

Last updated: 2026-09-19.

Current release: **v0.5.9 — Bench / Integration Simulation Pack**.

## State

The software, research tooling, deployment tooling, repository canon and read-only AI question layer are prepared for first physical vehicle integration.

## Ready

- live backend / PWA architecture;
- simulator / fault lab;
- diagnostics and quality handling;
- trip/history/baselines;
- hardware abstraction;
- passive CAN recording/replay;
- binary and numeric reverse-engineering tools;
- evidence-session storage;
- deployment / doctor / backup;
- kiosk display launcher;
- repo-first documentation / ADR / safety / BOM / runbooks;
- Ask MGO local evidence gateway;
- optional OpenAI provider boundary with precise-location redaction by default;
- Russian-first driver-facing UI with English fallback;
- complete multi-source integration bench covering ingestion → health/rules → history → Ask MGO.

## AI safety boundary

- AI is read-only.
- Default provider is local.
- External AI is opt-in.
- No vehicle-control tools exist.
- Deterministic local CRITICAL/ATTENTION logic remains independent.
- Raw high-volume CAN/audio/video is excluded from normal AI context.
- Precise latitude/longitude is redacted before external AI by default.

## Not yet evidenced on the actual vehicle

- CAN pair location;
- connector pins / wire colors;
- CAN bitrate;
- CAN IDs/signals;
- actual stock CAN coverage;
- physical sensor threads/dimensions;
- permanent mounting / cable routing;
- final dedicated display geometry.

## Current blocker

Access to the physical vehicle for the first controlled electrical/CAN survey.

## Next success criterion

Leave the first survey with:

- photographs;
- measured CAN topology;
- bitrate;
- passive logs;
- at least one repeatable candidate signal;
- unchanged factory vehicle behavior.
