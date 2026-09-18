# ADR-0006: Evidence-first CAN reverse engineering

Status: Accepted.

## Decision

Do not invent DBC signals from resemblance, another Microcar model, or one ambiguous capture.

Binary states use controlled baseline/action experiments. Numeric fields use reference-series discovery only as a hypothesis generator.

## Confirmation

A production mapping requires repeated evidence for:

- ID;
- bit/byte layout;
- endian;
- signedness;
- scaling;
- offset;
- unit;
- expected behavior.

Survey evidence is retained so every conclusion can be audited.
