# Numeric Signal Discovery

v0.5.5 is for continuous/numeric CAN signals such as vehicle speed, fuel level, outside temperature or an odometer-like value.

## Input

1. A timestamped candump log.
2. A timestamped CSV reference series:

```text
timestamp,value
2000.000,0
2000.200,5
2000.400,12
```

For speed discovery, the reference can later come from GNSS.

## Candidate fields

For every CAN ID the workbench tests:

- unsigned/signed 8-bit fields;
- unsigned/signed 16-bit little-endian fields;
- unsigned/signed 16-bit big-endian fields.

Frames are aligned with the closest reference sample inside a configurable time window.

## Ranking

Each candidate gets:

- Pearson correlation `r`;
- `R²`;
- fitted `slope` and `intercept`;
- RMSE;
- sample coverage;
- counter-likeness penalty;
- combined score.

Example hypothesis:

```text
vehicle_speed_gps ≈ 0.05 * raw + 0
```

## Counter protection

Simple monotonically incrementing byte fields can correlate with time and accidentally look useful. The workbench measures counter-like successive increments and reduces their score.

This is only a heuristic. Use a varied reference profile (accelerate, slow down, accelerate again) rather than a single monotonic ramp.

## Safety / evidence rule

Results are **statistical hypotheses**, not confirmed DBC signals.

A candidate must be reproduced in multiple experiments and checked for bit layout, signedness, scaling and behavior before it becomes a real `SG_` definition.

## API

- `GET /api/v1/survey/numeric/sample`
- `POST /api/v1/survey/numeric`

## CLI

```bash
mgo-discover-numeric drive.log gps_speed.csv \
  --label vehicle_speed_gps \
  --json-out speed-candidates.json
```
