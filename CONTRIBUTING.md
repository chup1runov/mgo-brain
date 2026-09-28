# Contributing

By participating, follow [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

Contributions to MGO Brain are welcome. Safety-impacting vehicle claims require stronger evidence than ordinary application changes.

## Before changing code

Read `PROJECT.md`, `docs/SAFETY.md`, `docs/ARCHITECTURE.md`, relevant ADRs under `docs/decisions/`, and `docs/TESTING.md`.

## Rules

- Do not add vehicle-control features to the read/observe factory-source layer.
- Do not guess factory CAN mappings, connector pins or wire colors.
- Do not weaken STALE / quality handling.
- Do not put AI in the sole path for a critical alert.
- Do not commit credentials, API keys, precise private location history or raw private media.
- Mark unverified hardware and CAN discoveries explicitly.
- Add or update tests for behavioral changes.
- Update documentation, roadmap and changelog when a material project decision changes.

## Development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev,analytics,hardware]'
python -m compileall -q mgo_brain tests
pytest -q
python tools/repository_audit.py
```

For UI changes, also run the browser audit. For packaging changes, build a wheel and test it from outside the repository.

## Pull requests

Keep PRs focused. Explain what changed, why, safety/vehicle impact, evidence/tests, and what remains untested.

Prefer small descriptive commits: `Add`, `Fix`, `Document`, `Refactor`.
