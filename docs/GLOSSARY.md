# Glossary

**BFI** — integrated body/fuse electronics used in the MGO4/P98 context.

**CAN** — Controller Area Network.

**CAN0** — project name for the factory MGO CAN interface; discovery is listen-only.

**CAN1 / Sensor CAN** — separate private CAN network for added MGO Brain sensors.

**DBC** — CAN database describing messages/signals, scaling and units.

**Progress ACT** — engine configuration used in this project, based on Lombardini LDW502.

**DCI** — different Microcar diesel/engine-management configuration; do not transfer DCI OBD assumptions to Progress ACT.

**CVT** — continuously variable transmission / belt variator.

**VehicleState** — canonical current state consumed by diagnostics/UI regardless of physical source.

**SourceAdapter** — hardware/simulator adapter emitting partial canonical updates.

**SourceMux** — fan-in for multiple adapters.

**StateAggregator** — merges source updates, applies source priority/freshness and produces VehicleState.

**STALE** — signal value exists but is too old to be considered a current measurement.

**Reference baseline** — intentionally slow/healthy historical reference.

**Rolling baseline** — recent behavior window.

**Survey session** — archived baseline/action CAN experiment with source logs and derived analysis.

**LAB** — engineering/debug section of the UI; not intended for use while driving.

**PWA** — progressive web app used for phone/tablet UI.

**Kiosk** — dedicated fullscreen display mode.

**MGO Brain** — the read/observe-first vehicle telemetry/diagnostics project in this repository.
