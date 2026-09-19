# ADR-0007: Ask MGO is a read-only explanatory layer

Status: Accepted.

## Decision

Ask MGO may read normalized vehicle evidence and historical summaries, but it does not control the vehicle and is not the sole mechanism for critical alarms.

## Provider boundary

The default provider is local.

External AI is opt-in and receives only a bounded evidence packet.

## Privacy

Precise latitude/longitude is redacted before external-provider use unless explicitly enabled.

## Safety consequences

The AI tool registry contains no:

- CAN transmit;
- starter;
- D/N/R;
- throttle;
- brake;
- steering;
- glow-control;
- speed-limiter

actions.

Deterministic local rules remain authoritative for current critical warnings.

## Rationale

Natural-language reasoning is useful for correlation and explanation, but model availability, latency and uncertainty make it unsuitable as the sole real-time safety path.
