# MGO Brain Project Canon

This repository is the canonical engineering record for **MGO Brain**: read/observe-first telemetry, diagnostics, history, condition monitoring and AI-assisted analysis for the 2017 Microcar M.Go / Progress ACT platform.

## Repo-first rule

Material project knowledge belongs in GitHub, not only in chat.

Commit it when it affects:

- system intent;
- architecture or interfaces;
- safety boundaries;
- vehicle integration;
- CAN reverse engineering;
- hardware selection / BOM;
- installation / wiring plans;
- signal definitions;
- service / maintenance logic;
- data storage / retention;
- AI integration;
- deployment / recovery;
- testing / release criteria;
- assumptions, uncertainties and unresolved questions;
- important engineering decisions and their rationale.

Chat is a working environment; GitHub is the durable source of truth for MGO Brain.

## Evidence rule

Facts learned from the actual vehicle must be classified as:

- documented;
- observed;
- measured;
- repeated / confirmed;
- inferred / hypothesis.

Never promote an unverified wire color, connector pin, CAN ID, scale, endian choice, sensor thread or vehicle behavior into confirmed configuration.

## Scope

This repository covers only MGO Brain and the Microcar M.Go work described in this project. Unrelated projects, names and context do not belong here.
