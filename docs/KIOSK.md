# Dedicated Display / Kiosk

v0.5.4 prepares a dedicated 7–10 inch Linux display to behave like an automotive instrument screen.

## Startup sequence

```text
Linux graphical session
        ↓
mgo-kiosk starts
        ↓
poll /health
        ↓
MGO Brain ready
        ↓
Chromium --kiosk http://127.0.0.1:8080/?kiosk=1
        ↓
full-screen MGO dashboard
```

The launcher waits for the backend instead of racing it during boot.

## Files

- `deployment/systemd-user/mgo-brain-kiosk.service`
- `deployment/kiosk.env.example`
- `mgo-kiosk` CLI

The user-level systemd unit is intended for the graphical desktop user. The backend itself remains a system service.

## Browser discovery

The launcher searches:

1. `chromium-browser`
2. `chromium`
3. `google-chrome`
4. `google-chrome-stable`

Or set `MGO_KIOSK_BROWSER`.

## Phone mode

None of this is required for the first installation. A phone can simply open the MGO Brain PWA over the local network.

## Dedicated-screen recommendation

Do not purchase a final screen before testing the real UI on a phone/tablet in the car. Once viewing distance and mounting position are known, choose the permanent 7–10 inch display.

## Safety

A dedicated display is a client only. Failure of the browser/display must not affect vehicle telemetry acquisition, warnings, logging or normal vehicle operation.
