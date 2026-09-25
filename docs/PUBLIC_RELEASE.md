# Public release / publication policy

MGO Brain is intended to be publishable as an experimental open-source engineering project under Apache-2.0.

## Appropriate public content

- source code and tests;
- synthetic simulator/bench data;
- documentation and architecture decisions;
- sanitized, reproducible CAN research results;
- generic hardware integration code;
- UI assets and non-private screenshots.

## Do not commit

- exact private GPS tracks;
- credentials or network secrets;
- private deployment configuration;
- raw personal telemetry unless deliberately sanitized;
- registration/VIN documents;
- unrelated project material.

Public source code does **not** make a deployed MGO Brain instance safe to expose to the Internet. The API currently assumes a trusted local network.

## Before changing repository visibility

1. CI, Repository audit, Docker smoke and wheel-install smoke are green.
2. LICENSE is Apache-2.0.
3. SECURITY.md describes public reporting and local-network constraints.
4. After visibility change, protect `main`: require PR/checks, block force-push and branch deletion.
5. Review history/Actions logs for accidental secrets or private telemetry.
6. Enable GitHub private vulnerability reporting if available.

Opaque historical ZIP archives are better kept as release assets or private backups rather than normal source-tree files.
