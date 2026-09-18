# TAVRELI Repository Canon

This repository is the canonical engineering record for the TAVRELI vehicle project currently implemented as **MGO Brain** for the 2017 Microcar M.Go / Progress ACT platform.

## Repo-first rule

Material project knowledge belongs in GitHub, not only in chat.

Commit it when it affects any of the following:

- product / system intent;
- architecture or interfaces;
- safety boundaries;
- vehicle integration;
- CAN reverse engineering;
- hardware selection or BOM;
- installation / wiring plans;
- source and signal definitions;
- service / maintenance logic;
- data storage / retention;
- AI integration;
- deployment / recovery;
- testing / release criteria;
- assumptions, uncertainties, unresolved questions;
- important decisions and the reasons behind them.

Chat may be used to reason and iterate, but GitHub is the durable source of truth.

## Evidence rule

Facts learned from the actual vehicle must be recorded with provenance:

- observed / measured;
- derived from manufacturer documentation;
- inferred / hypothesis;
- confirmed by repeated experiment.

Never promote an unverified wire color, connector pin, CAN ID, scale, endian choice, sensor thread, or vehicle behavior into the confirmed configuration.

## Current repository subsystem

The concrete subsystem implemented here is **MGO Brain**:

> read/observe-first telemetry, diagnostics, history, condition monitoring and AI-assisted analysis for the Microcar M.Go without replacing factory safety-critical functions.

If TAVRELI later grows beyond this vehicle subsystem, its broader scope should be documented explicitly rather than inferred.
