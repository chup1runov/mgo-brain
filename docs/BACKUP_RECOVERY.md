# Backup & Recovery

## Backup

Use:

```bash
mgo-backup --output mgo-brain-backup.tar.gz
```

The backup includes reviewed configuration and runtime data. SQLite is copied with SQLite's backup API.

## What matters most

Priority order:

1. confirmed configuration / DBC mappings;
2. survey evidence sessions;
3. service / component history;
4. SQLite events/trips/starts/reports;
5. Parquet trip history;
6. optional raw captures.

## Recovery workflow

1. install a known-good MGO Brain commit;
2. stop the service;
3. restore configuration to the configured config directory;
4. restore runtime data to the configured data directory;
5. verify file ownership/permissions;
6. run `mgo-doctor`;
7. start the service;
8. check `/health`;
9. open UI;
10. verify signal quality/source status before vehicle operation.

## Corrupted analytics

DuckDB/Parquet history is not in the real-time critical path.

If analytics data becomes unusable:

- preserve a copy for diagnosis;
- keep deterministic live rules running;
- rebuild history where possible from surviving trip files/summaries.

## Broken configuration

If hardware configuration prevents startup:

- revert `sources.json` to simulator-only;
- run doctor;
- recover one hardware source at a time.

## Disaster rule

Never troubleshoot a software recovery by changing unknown factory vehicle wiring.
