# Ask MGO / AI Gateway

Status: implemented in v0.5.7.

## Purpose

Ask MGO explains vehicle evidence without becoming part of the vehicle control or critical-warning path.

Example questions:

- Почему сегодня дольше заводился?
- Что изменилось по вариатору?
- Что сейчас с аккумулятором?
- Были ли новые предупреждения?
- Что скоро обслуживать?

## Architecture

```text
question
   ↓
local deterministic router
   ↓
selected read-only evidence tools
   ↓
compact EvidencePacket
   ↓
provider
   ├─ local fallback (default)
   └─ OpenAI Responses API (optional)
   ↓
answer
```

## Default behavior

Default:

```text
MGO_AI_PROVIDER=local
```

No external AI, Internet connection or API key is required.

The local provider is intentionally limited: it summarizes available measurements, quality, health status and recent start/CVT/battery evidence.

## Read-only tools

Implemented:

- `get_live_state()`
- `get_engine_health()`
- `get_cvt_health()`
- `get_battery_health()`
- `get_start_history()`
- `get_recent_trips()`
- `compare_trips()`
- `get_fault_events()`
- `get_service_plan()`
- `get_baselines()`
- `get_source_status()`

There are deliberately no tools for CAN transmit, starter control, D/N/R, throttle, braking, steering, glow control or speed-limiter changes.

## Context compression

The gateway selects at most a small tool set per question.

It removes known high-volume raw fields such as:

- raw CAN;
- raw audio;
- raw video;
- raw sample arrays.

Lists are bounded before an external model receives them.

## Signal quality

AI is instructed that:

- `STALE`
- `MISSING`
- `INVALID`

are not current measurements.

It must distinguish observation from hypothesis and must not downgrade deterministic local CRITICAL/ATTENTION states.

## Privacy

For an external provider, precise:

- `position.latitude`
- `position.longitude`

are redacted by default.

Explicit opt-in:

```text
MGO_AI_ALLOW_LOCATION=1
```

Do not enable this without a concrete reason.

## OpenAI provider

Optional deployment:

```text
MGO_AI_PROVIDER=openai
MGO_AI_MODEL=gpt-5.6-terra
MGO_AI_REASONING=low
OPENAI_API_KEY=<deployment secret>
```

The API key must be supplied through environment/secret management and never committed to Git.

The provider uses the OpenAI Responses API through the Python SDK.

Official references:

- Responses/text guide: https://developers.openai.com/api/docs/guides/text
- API key safety: https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety

## REST API

- `GET /api/v1/ai/status`
- `GET /api/v1/ai/tools`
- `POST /api/v1/ai/evidence`
- `POST /api/v1/ai/ask`

Normal `/ask` responses do not include the whole evidence packet unless `include_evidence=true` is explicitly requested.

## CLI

Against the running MGO Brain service:

```bash
mgo-ask Почему сегодня дольше заводился?
```

Engineering debug:

```bash
mgo-ask --evidence Что с вариатором?
```

## Voice

Voice remains a UI layer. The same `/api/v1/ai/ask` contract can later be driven by speech-to-text without changing the diagnostic/evidence architecture.
