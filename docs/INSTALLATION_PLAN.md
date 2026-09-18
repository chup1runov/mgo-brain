# Installation Plan

## Phase 0 — no vehicle modifications

- software, simulator, UI, analytics, survey tools;
- bench-test Linux deployment;
- test phone/PWA;
- test kiosk on generic display.

Status: software complete.

## Phase 1 — physical survey

- photograph BFI/fuse box and harnesses;
- find candidate CAN twisted pair;
- identify battery / mounting space;
- map cable-routing possibilities;
- identify accessible engine/CVT sensor locations.

No permanent connections yet.

## Phase 2 — passive factory CAN

- verify vehicle power off;
- measure CAN-H ↔ CAN-L resistance;
- determine bitrate;
- configure Linux interface listen-only;
- connect short high-impedance stub;
- capture passive logs;
- confirm no transmit path.

## Phase 3 — main computer power

Target topology:

```text
Battery +
   |
 fuse close to battery
   |
 MGO Brain branch
   |
 automotive computer
```

Requirements:

- independent fuse;
- automotive-rated power path;
- sleep / low-voltage behavior;
- removable connector;
- no dependency of vehicle operation on Brain.

## Phase 4 — first real dashboard

Normalize confirmed factory signals, likely beginning with whatever can be proved from:

- speed;
- D/N/R;
- doors;
- lighting;
- handbrake/brake state;
- fuel level;
- outside temperature;
- BFI status.

Unavailable signals remain UNKNOWN.

## Phase 5 — added engine/power sensors

Only after physical interfaces are confirmed:

- RPM;
- coolant temperature;
- oil pressure/temp;
- battery current/SoC;
- glow/starter observations;
- alternator characterization.

## Phase 6 — CVT / condition monitoring

- CVT fixed-housing temperatures;
- gearbox temperature;
- RPM/speed relationship;
- vibration.

## Phase 7 — peripherals

- TPMS;
- brake thermal comparison;
- cabin environment;
- water ingress;
- camera event linking.

## Phase 8 — dedicated screen

Install only after phone/tablet evaluation confirms:

- viewing position;
- screen size;
- brightness;
- distraction risk;
- mounting clearances.
