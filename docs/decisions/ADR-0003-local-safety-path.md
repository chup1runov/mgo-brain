# ADR-0003: Local deterministic safety path

Status: Accepted.

## Decision

Critical alert detection is local and deterministic.

AI, cloud connectivity, DuckDB and historical analytics are not required for live critical warnings.

## Consequences

Loss of Internet, AI API or historical database cannot suppress a core live rule.

AI may explain evidence, not originate the only critical alarm.
