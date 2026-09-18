# Engineering Evidence Policy

Every vehicle-specific conclusion should be classified.

## Evidence classes

### DOCUMENTED

Directly supported by manufacturer/service/parts documentation.

Record:

- source title;
- revision/date if known;
- page/section or URL.

### OBSERVED

Directly seen on this vehicle.

Examples:

- connector exists;
- wire pair is twisted;
- component label;
- measured resistance.

### MEASURED

Numerical observation with method.

Examples:

- CAN resistance;
- voltage;
- hose diameter;
- sender thread;
- current.

Record tool/method and conditions when material.

### REPEATED / CONFIRMED

Observed repeatedly with controlled changes.

Required before promoting reverse-engineered CAN signals to confirmed mappings.

### INFERRED / HYPOTHESIS

Plausible interpretation not yet confirmed.

Must not be silently copied into production configuration.

## CAN evidence

A useful signal record should eventually include:

- CAN ID;
- DLC;
- byte/bit layout;
- endian;
- signedness;
- factor;
- offset;
- unit;
- behavior;
- experiment IDs / sessions supporting it;
- confidence/status.

## Corrections

When a hypothesis is disproved, preserve the correction in Git history / ADR / notes rather than rewriting history as if the error never happened.
