# Signal Catalog

Machine-readable signal definitions live in:

`config/signals-v1.json`

This document defines how to interpret that registry.

## Status meanings

- `simulated_v0.x`: implemented in the software simulator, not proof that the real vehicle exposes it.
- `planned`: intended measurement, source not yet integrated/confirmed.
- future `observed`: physical source observed but decoding may be incomplete.
- future `confirmed`: source/mapping verified by repeatable evidence.

## Source vocabulary

Examples:

- `can.bfi` — factory body/BFI CAN candidate;
- `digital.oem` — isolated read of an OEM discrete signal;
- `sensor.coolant` — independent added coolant sensor;
- `sensor.oil` — independent oil pressure/temp sensor;
- `smartshunt` — battery monitor;
- `gnss` — GNSS measurements;
- `autopi.imu` — main-computer IMU;
- `tpms` — tyre sensor system;
- `derived` — calculated value.

## Priority rule

Preferred sources are ordered, but priority applies only while the preferred reading is fresh and usable.

Example:

```text
vehicle.speed
  primary:   can.bfi
  secondary: speed.pulse
  validation: gnss
```

If factory CAN becomes stale, a fresh fallback may take over.

## Canonical-name rule

Consumers use canonical names, never hardware-specific register or CAN names.

Dashboard, AI, history and diagnostics should not care whether `engine.rpm` came from CAN, a tach lead or a Hall sensor.
