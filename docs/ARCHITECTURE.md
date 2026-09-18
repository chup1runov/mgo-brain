# MGO Brain Architecture

MGO Brain is a read/observe-first telemetry and condition-monitoring platform for a 2017 Microcar M.Go / F8 0.5 with the Progress ACT / Lombardini LDW502 engine.

## Safety boundary

MGO Brain is not a replacement ECU and must not become a single point of failure for vehicle-critical functions. Vehicle operation must remain possible if the entire MGO Brain system is unplugged or failed.

Initial hardware integrations are therefore read-only:

- listen-only access to the factory BFI/CAN bus;
- isolated sensing of OEM digital signals when CAN data is unavailable;
- independent add-on sensors for temperatures, pressures, vibration and power telemetry;
- local deterministic critical alarms independent of cloud/AI availability.

AI is an explanatory and analytical layer, not the sole safety mechanism.

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
Rules + baseline/anomaly engine
        |
        v
SQLite metadata + Parquet/DuckDB history
        |
        +--> REST API
        +--> WebSocket live state
        +--> Dashboard
        +--> AI context gateway
```

## Canonical signal contract

Consumers do not depend on the physical source. A signal is normalized before diagnostics or UI use.

Example:

```json
{
  "value": 82.4,
  "unit": "°C",
  "quality": "GOOD",
  "source": "sensorhub.coolant",
  "timestamp": "2026-09-18T10:00:00Z"
}
```

A future CAN decoder can replace a simulated source without changing the dashboard, rule engine, trip detector or AI interface.

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

The exact MGO4 CAN pins, wire colors and signal IDs are intentionally not hard-coded until they are confirmed on the specific vehicle.

## Storage strategy

v0.1 uses:

- SQLite for events, starts and trip metadata;
- JSONL for raw per-trip normalized state.

Planned:

- Parquet for compact historical telemetry;
- DuckDB for local analytics;
- bounded ring buffers for high-rate vibration/audio;
- event-triggered retention of raw high-frequency data.
