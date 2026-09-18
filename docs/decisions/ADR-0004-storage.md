# ADR-0004: Local-first storage split

Status: Accepted.

## Decision

Use different storage for different workloads:

- SQLite: metadata, starts, trips, events, reports;
- streaming JSONL: temporary active-trip telemetry;
- Parquet/ZSTD: finalized historical telemetry;
- DuckDB: local analytics;
- bounded/event-based storage later for high-rate audio/vibration.

## Reason

This avoids treating SQLite as a large time-series database and limits unnecessary flash writes.
