# AI Gateway Design

Status: planned interface; deterministic diagnostics already exist independently.

## Purpose

The AI layer should answer questions such as:

- Why did the vehicle start slower today?
- What changed in CVT behavior over the last month?
- Did charging behavior degrade?
- What should be inspected next?
- Which manual/service information is relevant to the observed event?

## Non-goals

AI must not:

- control brakes/steering/throttle/gear/start/glow;
- replace local CRITICAL rules;
- invent unavailable telemetry;
- treat STALE data as current;
- silently infer unconfirmed CAN mappings.

## Tool boundary

Planned functions:

- `get_live_state()`
- `get_engine_health()`
- `get_cvt_health()`
- `get_battery_health()`
- `get_start_history()`
- `get_trip(id)`
- `compare_trips(a,b)`
- `get_fault_events()`
- `get_service_history()`
- `search_vehicle_manual(query)`

## Context compression

Raw CAN/audio/vibration should be processed locally.

AI receives a compact evidence package:

```json
{
  "current_state": {},
  "signal_quality": {},
  "active_alerts": [],
  "baseline_deviations": [],
  "recent_trip": {},
  "maintenance_due": [],
  "relevant_manual_sections": []
}
```

## API / secrets

ChatGPT subscription and OpenAI API billing are separate concerns.

If automatic API use is enabled later:

- API key stays in deployment secrets;
- never commit it;
- log request metadata carefully;
- provide a local/no-AI fallback.

## Voice

Voice is a UI layer. The backend/tool contract should work identically for text and voice.
