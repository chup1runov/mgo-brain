# Security Policy

## Scope and trust model

MGO Brain can expose vehicle telemetry, trip history, GPS-derived data and configuration. Treat a deployed vehicle computer as a private device.

The current web/API service is designed for a **trusted local network**. It does not yet provide authentication suitable for an untrusted LAN or the public Internet.

Therefore:

- do not expose port 8080 directly to the Internet;
- do not port-forward it from a router;
- prefer an isolated vehicle hotspot / trusted LAN;
- use a VPN or authenticated reverse proxy if remote access is added;
- keep runtime telemetry, captures and deployment secrets outside the source repository.

## Secrets and private data

Never commit API keys, Wi-Fi/SIM/VPN credentials, private certificates, access tokens, exact private location history, or raw personal telemetry that is not intentionally sanitized for publication.

Use environment variables or deployment-only files excluded by Git.

## CAN security boundary

Factory CAN discovery is receive-only. Software does not expose a factory-CAN transmit method, and the Linux CAN interface must be independently verified as OS-level LISTEN-ONLY before physical factory-CAN use.

## Reporting a vulnerability

For vulnerabilities that could expose credentials, private telemetry or unsafe vehicle behavior, use GitHub private vulnerability reporting / a Security Advisory when available. Do not publish exploit details or secrets in a normal issue.

If private reporting is unavailable, open a minimal issue asking the maintainer for a private reporting channel without including sensitive details.

## Supported versions

Only the current `main` branch is actively maintained until formal stable releases begin.
