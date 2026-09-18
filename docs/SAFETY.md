# Safety Case

## Top-level invariant

Failure, crash, power loss, removal or software corruption of MGO Brain must not prevent normal factory vehicle operation.

## Prohibited control dependencies

MGO Brain must not become required for:

- engine start;
- braking;
- steering;
- D/N/R selection;
- OEM low-oil-pressure warning;
- OEM over-temperature warning;
- speed-limiter compliance;
- throttle/governor function.

## Factory CAN

Discovery phase:

- receive only;
- OS-level listen-only;
- no transmit API in MGO Brain factory-CAN path;
- no guessed bitrate;
- no guessed termination;
- no active requests to unknown ECUs.

## Added sensors

Prefer parallel observation that leaves OEM sensing intact.

Examples:

- oil pressure: retain OEM warning switch if adding an independent pressure sensor;
- coolant: retain OEM overheat warning independently;
- battery: measurement failure must not interrupt starter/vehicle current path.

## Alarm architecture

Critical alarms are deterministic and local.

AI may:

- explain;
- correlate;
- summarize;
- suggest inspection.

AI may not be the sole mechanism deciding whether a critical warning exists.

## Quality / stale behavior

A stale value is not a current measurement.

State-machine and health decisions must not silently use STALE/MISSING/INVALID readings as live evidence.

## Human factors

The moving-vehicle HOME screen should remain concise. LAB, raw CAN, reverse engineering and detailed history are not intended for interaction while driving.
