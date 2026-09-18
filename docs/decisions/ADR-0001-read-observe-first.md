# ADR-0001: Read/observe-first vehicle boundary

Status: Accepted.

## Decision

MGO Brain observes, records and analyzes. Factory safety-critical vehicle operation must not depend on it.

## Consequences

- no throttle/brake/steering/gear/start/glow control;
- factory CAN discovery is receive-only;
- OEM critical warnings remain independent;
- unplugging MGO Brain must not disable normal operation.

## Reason

The project seeks observability and condition monitoring, not replacement vehicle control. This sharply reduces integration and failure risk.
