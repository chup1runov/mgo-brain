# Testing Strategy

## CI matrix

Core tests run on supported Python versions.

Hardware-optional CI additionally installs:

- python-can;
- cantools;
- pymodbus;
- pyserial.

## Test layers

### Unit

Pure algorithms:

- state machine;
- rules;
- baselines;
- CAN parsing;
- survey ranking;
- numeric discovery;
- sensor codecs.

### Integration

- API routes;
- SQLite persistence;
- Parquet/DuckDB round trip;
- SourceAdapter aggregation;
- recorder/replay;
- survey session persistence;
- deployment templates.

### Simulator fault tests

Every supported simulated fault should create the expected deterministic evidence/alert.

### Replay regression tests

Once real PKB839 logs exist, sanitized replay fixtures should be added where privacy permits.

A confirmed decoding bug should ideally become a regression fixture.

### Bench hardware

Before vehicle install:

- CAN loopback/private Sensor CAN;
- Modbus fake/bench device;
- sleep/wake;
- power interruption;
- filesystem recovery.

### Vehicle validation

After integration:

- compare dashboard against independent measurements;
- deliberately disconnect noncritical sensors and confirm STALE/UNKNOWN behavior;
- verify MGO Brain removal does not affect factory operation.

## Release gate

A release should not be called complete until:

- compile passes;
- tests pass;
- hardware optional job passes when affected;
- docs/roadmap/handoff are synchronized;
- safety boundary is unchanged or explicitly reviewed.
