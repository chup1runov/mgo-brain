# Commissioning & Replay Toolkit

v0.5.2 prepares MGO Brain for the first real CAN survey day without requiring the vehicle during development.

## Receive-only recording

Record a fixed time window:

```bash
mgo-can-record --channel can0 --seconds 10 --output door_closed.log
```

Or a fixed number of frames:

```bash
mgo-can-record --channel can0 --frames 1000 --output baseline.log
```

The recorder only calls the receive side of the SocketCAN abstraction.

**Important:** the Linux CAN interface itself must be configured in listen-only mode before connecting to the factory MGO bus.

## Offline replay

A saved recording can be replayed without any CAN hardware:

```bash
mgo-can-replay door_closed.log --speed 0
```

Use `--speed 1` to preserve recorded timing or a larger value to accelerate replay.

Replay implements the same raw CAN receive boundary, so future decoders can be tested against recorded PKB839 data at home.

## Persistent survey sessions

A survey experiment can be archived as evidence:

```bash
mgo-survey-session door_closed.log door_open.log \
  --label driver_door_open \
  --notes "IGN ON, stationary, opened driver door once"
```

Each session stores:

- `baseline.log`
- `action.log`
- `analysis.json`
- `draft.dbc`
- `manifest.json`

Default storage is `data/surveys/<session-id>/`.

The LAB UI exposes the same workflow with **Save survey session**.

## API

- `GET /api/v1/survey/sessions`
- `POST /api/v1/survey/sessions`
- `GET /api/v1/survey/sessions/{id}`
- `GET /api/v1/survey/sessions/{id}/files/{kind}`

This preserves the raw evidence behind every reverse-engineering conclusion.
