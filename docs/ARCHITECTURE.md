# MGO Brain Architecture

## Core principle

Every input source emits partial canonical `SourceUpdate` objects. The core never depends directly on CAN, serial, Modbus or a particular vendor.

```text
physical/simulated sources
        ↓
SourceAdapter(s)
        ↓
SourceMux
        ↓
StateAggregator
 quality + freshness + preferred-source fallback
        ↓
VehicleState
        ↓
state machine / rules / alerts / health
        ↓
trips / baselines / Parquet-DuckDB
        ↓
REST / WebSocket / PWA / AI context
```

## Freshness model

`StateAggregator` retains the latest reading for each canonical signal. A reading older than `stale_after_s` is exposed as `STALE`. Preferred source priority applies only while that source remains fresh. A fresh fallback may replace a stale preferred source.

`VehicleMode` and subsystem-readiness logic ignore STALE/MISSING/INVALID readings so old RPM or pressure values cannot masquerade as live telemetry.

## Factory CAN boundary

`SocketCANTransport` exposes `recv()` and `close()` only. It intentionally has no transmit API. This software boundary does **not** substitute for configuring the Linux SocketCAN interface itself in listen-only mode.

DBC decoding is lazy/optional. The first real MGO DBC must be produced from passive observation of PKB839, not copied from another model.

## Separate Sensor CAN

SensorHub CAN v1 is independent of factory CAN. Current software defines an 8-byte frame carrying protocol version, value type, channel, flags and a 32-bit value. Channel-to-canonical-signal mapping stays in the vehicle configuration.

## Storage/safety separation

Real-time rules and critical alerts do not depend on DuckDB, Parquet, cloud access or AI. Historical analytics can fail without disabling current deterministic warnings.
