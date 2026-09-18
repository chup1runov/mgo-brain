# First Vehicle Day Runbook

Goal: collect evidence. Do **not** install the full system on day one.

## Bring

- phone/camera;
- good multimeter;
- fine back-probes;
- trim tools;
- labels / tape;
- notebook;
- CAN interface/computer only if the CAN pair can be verified safely.

## 1. Photograph before touching

Capture:

- fuse/BFI area wide shot;
- every accessible BFI connector;
- wire colors entering connectors;
- candidate twisted pairs;
- cluster harness if accessible;
- D/N/R selector harness;
- battery and free mounting space;
- engine bay overview;
- starter / alternator / glow wiring;
- engine switches/sensors;
- gearbox / CVT.

## 2. Do not

- cut wires;
- use Scotchlok;
- probe random connector pins with power applied;
- unplug unknown safety-related connectors;
- add a 120 Ω terminator;
- transmit onto factory CAN;
- infer a wire function from fuse number alone.

## 3. Candidate CAN validation

With vehicle safely powered down:

- identify twisted pair candidate;
- measure H↔L resistance;
- record result;
- do not treat ~60 Ω as guaranteed—record the actual topology.

Then determine bus activity/bitrate with a passive interface.

## 4. First captures

Create separate captures with exactly one intentional change per experiment:

- ignition off / on;
- driver door closed / open;
- passenger door closed / open;
- left indicator;
- right indicator;
- low beam;
- high beam;
- handbrake;
- brake switch;
- D;
- N;
- R.

Later, safely:

- 0 / 10 / 20 / 30 / 40 km/h;
- refuel / fuel-level change.

## 5. Naming

Use stable filenames:

```text
2026-xx-xx_01_ign_on_baseline.log
2026-xx-xx_02_driver_door_closed.log
2026-xx-xx_03_driver_door_open.log
```

Immediately archive useful pairs with MGO Brain Survey Sessions.

## Exit criteria

Day 1 is successful if we leave with:

- clear photos;
- measured CAN candidate;
- bitrate;
- passive logs;
- no damage / no altered factory behavior.

Decoding can continue later at home through replay.
