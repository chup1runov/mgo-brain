# Vehicle Baseline

This file records only project-relevant, non-secret vehicle facts that are sufficiently established for engineering work.

## Platform

- Vehicle family: Microcar M.Go / F8 0.5.
- Model year: 2017.
- Category: L6e moped car.
- Engine: Progress ACT / Lombardini LDW502.
- Displacement: 505 cm³.
- Architecture: two-cylinder, four-stroke indirect-injection diesel.
- Rated output: approximately 4 kW at 3200 rpm.
- Drivetrain: front-wheel drive.
- Transmission: CVT plus D/N/R reduction gearbox.
- Nominal road-speed class limit: 45 km/h.
- Battery class: approximately 12 V / 42 Ah.
- Generator documentation: approximately 55 A / 480 W.
- Starter documentation: approximately 1.1 kW.

## Service baseline used by software

Machine-readable intervals live in `config/maintenance-plan.json`.

Current baseline:

- engine oil + filter: 5,000 km / 12 months;
- air filter: 5,000 km / 12 months;
- CVT belt inspection: 5,000 km;
- CVT belt replacement: 10,000 km / 24 months;
- gearbox oil: 10,000 km / 24 months;
- brake fluid: 24 months;
- coolant: 24 months.

## Diagnostic architecture distinction

The Progress ACT configuration must not be treated like the DCI version. Rich modern engine-ECU OBD-II PID/DTC access is not assumed.

The project instead combines:

- factory body/CAN signals where available;
- OEM discrete states;
- independent sensors;
- derived condition metrics.

## Identity data policy

Registration/VIN and other vehicle-identifying data are intentionally not required by the source repository. If needed for a deployed unit, keep them in private deployment configuration rather than project-wide documentation.
