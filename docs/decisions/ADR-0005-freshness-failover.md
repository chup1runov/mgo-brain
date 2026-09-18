# ADR-0005: Freshness and source failover

Status: Accepted.

## Decision

Preferred source priority applies only while the source remains fresh/usable.

STALE/MISSING/INVALID readings cannot silently behave like current measurements.

A live lower-priority fallback may replace a stale primary.

## Example

Factory CAN speed can be preferred while fresh; GNSS can remain an independent fallback/validator.
