# Data & Privacy

MGO Brain can become a highly sensitive personal dataset even though the core software is vehicle-focused.

## Potentially sensitive data

- trip timestamps;
- GPS tracks;
- home/work locations inferred from parking;
- driving patterns;
- audio snippets;
- camera/event clips;
- vehicle identifiers;
- service history;
- network identifiers.

## Repository policy

Do not commit personal runtime telemetry to Git.

Runtime data belongs under deployment data storage such as:

`/var/lib/mgo-brain`

and should be ignored by Git.

## Default retention philosophy

Prefer compact derived history over indefinite raw capture.

- ordinary normalized trip telemetry → Parquet/history;
- raw CAN → commissioning/research or anomaly-triggered retention;
- vibration/audio high-rate raw data → bounded ring buffer;
- audio/video → event-linked and limited, not continuous archival by default.

## Location

GPS is useful for:

- speed validation;
- slope/context;
- trip analysis.

But precise long-term GPS history should be treated as private data.

## AI

Do not send raw high-frequency history to an AI service.

Prepare a compact context containing only relevant:

- current state;
- alerts;
- derived metrics;
- recent comparisons;
- maintenance context;
- selected manual references.

## Backups

Backups may contain sensitive runtime data. Store them privately and consider encryption before off-device/cloud storage.

## Future work

Before enabling Internet-facing remote access, add authenticated transport and update the threat model.
