# Contributing

MGO Brain is currently a private engineering project. Contributions should preserve the project's safety and evidence rules.

## Before changing code

Read:

1. `PROJECT.md`
2. `docs/SAFETY.md`
3. `docs/ARCHITECTURE.md`
4. relevant ADRs under `docs/decisions/`
5. `docs/TESTING.md`

## Rules

- Do not add vehicle-control features to the read/observe source layer.
- Do not guess factory CAN mappings, connector pins or wire colors.
- Do not weaken STALE / quality handling.
- Do not put AI in the sole path for a critical alert.
- Do not commit credentials, API keys, precise private location history or raw private media.
- Mark unverified hardware and CAN discoveries explicitly.
- Add/update tests for behavioral changes.
- Update documentation, roadmap, changelog and handoff when a material project decision changes.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev,analytics,hardware]'
python -m compileall -q mgo_brain tests
pytest -q
```

## Commit style

Prefer small descriptive commits: `Add`, `Fix`, `Document`, `Refactor`.
