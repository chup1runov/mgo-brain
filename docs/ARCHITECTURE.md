# MGO Brain Architecture

MGO Brain is a read/observe-first telemetry and condition-monitoring platform for a 2017 Microcar M.Go / F8 0.5 with Progress ACT / Lombardini LDW502.

## Safety boundary

MGO Brain is not a replacement ECU and must not become a single point of failure. The vehicle must remain operable if MGO Brain is unplugged or failed.

- factory CAN discovery is listen-only;
- OEM digital signals are sensed in isolation when needed;
- added sensors supplement rather than replace OEM warnings;
- deterministic critical alerts work without cloud/AI;
- historical analytics are outside the real-time safety path.

## Logical architecture

```text
Physical/simulated sources
        ↓
SourceAdapter layer
        ↓
Canonical signals + quality/source metadata
        ↓
VehicleState + state machine
        ↓
Start / Trip detectors
        ↓
Deterministic rules → Alert lifecycle → Subsystem health
        ↓
Healthy reference baseline + rolling baseline
        ↓
SQLite metadata/reports + Parquet/ZSTD telemetry
        ↓
DuckDB historical analytics
        ↓
REST / WebSocket / AI context
        ↓
Local PWA console
HOME | ENGINE | CVT | POWER | TRIPS | SERVICE | LAB
```

## Historical learning policy

The healthy reference baseline excludes starts/trips associated with ATTENTION or CRITICAL diagnostic conditions. Those observations may still enter the rolling window, which makes gradual drift visible against the healthier reference.

Reference baselines require 20 eligible samples before anomaly classification becomes qualified. Before then the result is `UNQUALIFIED`.

The anomaly score is a project heuristic, not a manufacturer service limit.

## Storage

- SQLite: events, starts, trip summaries and post-trip reports.
- Flat JSONL: streaming temporary telemetry while a trip is active.
- Parquet/ZSTD: finalized trip telemetry.
- DuckDB: local historical queries.
- Future high-rate vibration/audio: bounded ring buffers plus event-triggered retention.

## PWA policy

The application shell may be cached offline. Dynamic `/api/` and WebSocket vehicle data are not served from stale caches. A disconnected UI must show loss/reconnection rather than present old measurements as current.

## Planned hardware topology

```text
phone/browser
     |
 Wi-Fi/4G
     |
AutoPi TMU CM4
 |           |
CAN0        CAN1
 |           |
MGO BFI    Sensor CAN
             |
       ESP32 SensorHub
             |
      sensors / RS485
```

Exact MGO4 CAN pins, wire colors and signal IDs remain intentionally undefined until measured on the vehicle.
