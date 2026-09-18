# MGO Brain Architecture

MGO Brain is a read/observe-first telemetry and condition-monitoring platform for a 2017 Microcar M.Go / F8 0.5 with the Progress ACT / Lombardini LDW502 engine.

## Safety boundary

MGO Brain is not a replacement ECU and must not become a single point of failure for vehicle-critical functions. Vehicle operation must remain possible if the entire MGO Brain system is unplugged or failed.

Initial hardware integrations are therefore read-only:

- listen-only access to the factory BFI/CAN bus;
- isolated sensing of OEM digital signals when CAN data is unavailable;
- independent add-on sensors for temperatures, pressures, vibration and power telemetry;
- local deterministic critical alarms independent of cloud/AI availability.

AI is explanatory/analytical, not the sole safety mechanism. Historical analytics are also isolated from the real-time alert path.

## Logical layers

```text
Physical sources
  simulator / MGO CAN / SensorHub / GNSS / SmartShunt / TPMS / added sensors
        |
        v
Source adapters
        |
        v
Canonical signals + quality metadata
        |
        v
VehicleState + state machine
        |
        +--> Start detector --> StartEvent
        +--> Trip detector  --> TripSummary + telemetry
        |
        v
Deterministic rules --> Alert lifecycle --> Subsystem health
        |
        +------------------------ real-time safety/diagnostic path
        |
        v
Healthy reference baseline + rolling baseline
        |
        v
SQLite summaries/reports + Parquet/ZSTD telemetry
        |
        v
DuckDB historical analytics
        |
        +--> REST API
        +--> WebSocket live state
        +--> Dashboard
        +--> AI context gateway
```

## Canonical signal contract

Consumers do not depend on the physical source. A signal is normalized before diagnostics or UI use.

```json
{
  "value": 82.4,
  "unit": "°C",
  "quality": "GOOD",
  "source": "sensorhub.coolant",
  "timestamp": "2026-09-18T10:00:00Z"
}
```

A future CAN decoder can replace the simulated source without changing dashboard, rules, history or AI interfaces.

## Historical learning policy

The reference baseline is intended to represent healthy behavior. Samples associated with ATTENTION or CRITICAL diagnostic conditions are excluded from reference learning. They still enter the rolling window, allowing current behavior to drift away from the frozen healthy reference.

The reference baseline requires 20 eligible samples before anomaly status becomes qualified. Before that, comparisons are marked `UNQUALIFIED`.

Anomaly score is a project heuristic, not a manufacturer service limit.

## Storage strategy

v0.3 uses:

- SQLite for events, starts, trip summaries and post-trip reports;
- flat JSONL streamed while a trip is active;
- Parquet/ZSTD finalization when DuckDB is installed;
- DuckDB for local historical queries;
- baseline rebuild from persisted start/trip summaries after restart.

Future high-frequency vibration/audio will use bounded ring buffers and event-triggered retention.

## Planned hardware topology

```text
                    phone / browser
                          |
                       Wi-Fi/4G
                          |
                    AutoPi TMU CM4
                 Linux / API / storage
                    |             |
             CAN0 listen-only     CAN1
                    |             |
              MGO4 BFI/CAN    Sensor CAN
                                  |
                           ESP32 SensorHub
                                  |
                  sensors / isolated inputs / RS485
```

Exact MGO4 CAN pins, wire colors and signal IDs are intentionally not hard-coded until confirmed on the specific vehicle.
