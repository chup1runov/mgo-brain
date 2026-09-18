# MGO Brain Fault Laboratory

The v0.2 simulator can deliberately inject faults so the diagnostic pipeline can be tested before any real vehicle wiring is connected.

## Scenarios

| Scenario | Simulated effect | Expected diagnostic response |
|---|---|---|
| `weak_battery` | Low resting voltage and deep crank sag | `BATTERY_LOW_REST`, `CRANK_VOLTAGE_LOW` |
| `starter_degradation` | Longer crank, lower cranking RPM, higher starter current | `STARTER_SLOW_CRANK`, possibly `CRANK_VOLTAGE_LOW` |
| `glow_fault` | Low glow-plug current during PREHEAT | `GLOW_CURRENT_LOW` |
| `alternator_undercharge` | Running voltage around 12 V | `CHARGING_LOW` |
| `alternator_overvoltage` | Running voltage above 15.2 V | `CHARGING_OVERVOLTAGE` |
| `low_oil_pressure` | Running oil pressure below 0.8 bar | `LOW_OIL_PRESSURE` and simulated OEM oil warning |
| `overheating` | Coolant rises above prototype thresholds | `HIGH_COOLANT_TEMP` / OEM overheat warning |
| `cvt_slip` | Engine RPM rises ~20% at the same road speed | `CVT_RATIO_DRIFT` |
| `cvt_overheat` | CVT temperatures exceed 100 °C | `CVT_OVERHEAT` |

These values are simulator test thresholds, not a replacement for the manufacturer's real service limits.

## API

List scenarios:

```bash
curl http://localhost:8080/api/v1/simulator/faults
```

Enable one:

```bash
curl -X POST http://localhost:8080/api/v1/simulator/faults/weak_battery/enable
```

Disable one:

```bash
curl -X POST http://localhost:8080/api/v1/simulator/faults/weak_battery/disable
```

Clear all:

```bash
curl -X POST http://localhost:8080/api/v1/simulator/faults/clear
```

## Alert lifecycle

Rules emit current fault conditions. `AlertManager` converts them into lifecycle records:

```text
condition appears  -> ACTIVE
condition persists -> ACTIVE, occurrences increase
condition absent   -> waits clear-after interval
interval expires   -> CLEARED and moved to history
```

The dashboard and health engine consume only currently active alerts; history remains available through `/api/v1/alerts`.

## Health model

The following subsystems are evaluated independently:

- ENGINE
- CVT
- ELECTRICAL
- TYRES
- BRAKES

A subsystem without its required sensor set is `UNKNOWN`, not `NORMAL`. This is intentional: the software must not claim health when it has no evidence.
