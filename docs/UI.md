# MGO Brain Local UI

v0.4 defines the phone/browser interface as a local PWA. The phone is a terminal, not the vehicle computer.

## Views

- **HOME**: live speed/RPM, mode, overall/subsystem health, active alerts and latest trip.
- **ENGINE**: RPM, coolant, oil, glow/starter current, start history and engine baselines.
- **CVT**: ratio, drift, primary/secondary temperatures and CVT baselines.
- **POWER**: battery voltage/current/SoC, alternator and electrical baselines.
- **TRIPS**: trip history, report viewer and two-trip comparison.
- **SERVICE**: documented maintenance registry.
- **LAB**: simulator fault injection, analytics status, baselines and raw normalized state.

## Offline policy

The service worker caches only the application shell. Requests under `/api/` and WebSocket traffic remain network/live data. Offline mode must never make an old vehicle value appear current.

## Driver-distraction boundary

HOME is intentionally concise. Raw state, fault injection and historical detail live in secondary screens and are not intended for interaction while driving.
