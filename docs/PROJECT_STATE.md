# Project State

Last updated: 2026-09-18.

Current release: **v0.5.6 — Repository Canon & Engineering Pack**.

## State

The software, research tooling, deployment tooling and repository canon are prepared for first physical vehicle integration.

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
- repo-first documentation / ADR / safety / BOM / runbooks.

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
