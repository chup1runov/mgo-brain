# ADR-0002: Canonical signals and SourceAdapter isolation

Status: Accepted.

## Decision

Dashboard, history, rules and AI consume canonical signal names, not CAN frames, Modbus registers or vendor-specific APIs.

Physical sources enter through SourceAdapter / SourceUpdate.

## Consequences

A signal such as `engine.rpm` may later switch from CAN to tach/Hall acquisition without rewriting consumers.

Hardware-specific decoding remains isolated at the edges.
