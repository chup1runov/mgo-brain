# Security Policy

## Scope

MGO Brain can expose vehicle telemetry, trip history, GPS-derived data and configuration over a local network. Treat the vehicle computer as a private device.

## Current trust model

The current web/API service is designed for a trusted local network. It does **not** yet provide user authentication suitable for an untrusted LAN or the public Internet.

Therefore:

- do not expose port 8080 directly to the Internet;
- do not port-forward it from a router;
- prefer an isolated vehicle hotspot / trusted LAN;
- use a VPN or authenticated reverse proxy if remote access is added later;
- keep the repository private while it contains vehicle-specific engineering data.

## Secrets

Never commit:

- OpenAI/API keys;
- Wi-Fi passwords;
- SIM credentials;
- VPN keys;
- private certificates;
- personal access tokens;
- exact private location history intended to remain private.

Use environment variables or deployment-only secret files excluded from Git.

## CAN security boundary

Factory CAN discovery is receive-only. Software does not provide a factory-CAN transmit method. The OS CAN interface must also be configured listen-only during discovery.

## Reporting a vulnerability

For this private repository, report vulnerabilities directly to the repository owner rather than publishing them in a public issue.

## Supported versions

Only the current `main` branch is actively maintained until formal releases begin.
