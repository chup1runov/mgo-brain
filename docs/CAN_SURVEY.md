# CAN Survey Toolkit

Survey Toolkit is the bridge between a physically connected listen-only CAN interface and the first trustworthy `MGO4_CAN.dbc`.

## Workflow

1. Record a baseline with exactly one condition inactive, e.g. driver door closed.
2. Record the same time window with exactly that condition active, e.g. driver door open.
3. Compare the logs with the LAB UI or the `mgo-survey` CLI.
4. Review ranked CAN IDs and changed byte positions.
5. Repeat the experiment several times before naming a signal.
6. Add confirmed mappings to the real DBC only after repeatability is established.

## Supported candump input

Hash format:

```text
(123.456) can0 310#00010203
```

Bracket format:

```text
can0 310 [4] 00 01 02 03
```

Malformed/unrecognized lines are reported rather than silently interpreted.

## Ranking

For every CAN ID and byte index the toolkit compares value distributions between baseline and action.

Strong evidence:
- byte is stable before and stable after;
- modal value changes between recordings;
- the same change dominates most frames.

Lower-confidence evidence:
- noisy counters;
- bytes that vary heavily in both recordings;
- very unbalanced sample counts.

IDs that appear only in one condition are also surfaced.

## DBC draft safety

The generated draft contains `BO_` message declarations and comments only. It deliberately emits no `SG_` signal definitions because a two-state log comparison cannot safely determine bit offset, endian, scaling, signedness or units.

## Browser API

- `GET /api/v1/survey/sample`
- `POST /api/v1/survey/parse`
- `POST /api/v1/survey/analyze`

## CLI

```bash
mgo-survey closed.log open.log --label driver_door_open \
  --json-out door-analysis.json \
  --dbc-out mgo4-survey-draft.dbc
```

## Physical safety rule

Survey Toolkit analyzes received logs only. It does not transmit CAN frames. The Linux CAN interface connected to the factory MGO bus must still be configured in listen-only mode.
