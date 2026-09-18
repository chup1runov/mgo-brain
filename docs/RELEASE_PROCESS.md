# Release Process

Until formal tags/releases are introduced, `main` is the canonical integration branch.

## Versioning

Use semantic intent:

- patch: fixes, documentation, tooling that does not materially change architecture;
- minor: new subsystem capability or integration layer;
- major: incompatible architecture / data contract / safety boundary.

## Before merging/releasing

1. compile;
2. full pytest;
3. hardware-optional CI where applicable;
4. verify `/health` version;
5. update README current version;
6. update CHANGELOG;
7. update ROADMAP;
8. update PROJECT_HANDOFF;
9. update PROJECT_STATE if milestone changes;
10. update ADRs for architecture decisions.

## Vehicle-specific gate

A CAN mapping may enter a production DBC only when evidence is repeatable and traceable.

## Rollback

Deployment should always retain:

- previous known-good Git commit/tag;
- backup of data/config;
- ability to disable hardware adapters and fall back to simulator/replay.

## Future

When deployment begins on real hardware, introduce Git tags such as `v0.6.0` and GitHub Releases with release notes and installation checksum/artifacts.
