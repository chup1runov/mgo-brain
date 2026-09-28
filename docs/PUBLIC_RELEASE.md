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


## Repository settings after publication

Recommended GitHub settings:

- description: `Experimental telemetry, diagnostics and CAN research for Microcar M.Go / Progress ACT`;
- topics: `can-bus`, `vehicle-telemetry`, `diagnostics`, `microcar`, `fastapi`, `automotive`;
- enable Issues;
- enable private vulnerability reporting if available;
- protect `main` with required PR/checks and no force-push/deletion.

## Historical note before first public switch

The current private history contains one early commit title using an unrelated internal project name. Current files are clean and the name is not part of MGO Brain, but **history and old Actions titles become public when repository visibility changes**.

Before the first public switch, choose deliberately:

1. accept that harmless historical naming artifact; or
2. recreate/rewrite the public Git history and remove old Actions runs/technical branches.

The current connector cannot delete old Actions runs or Git refs, so option 2 requires GitHub UI/CLI or a fresh public-history rewrite outside this automation.
