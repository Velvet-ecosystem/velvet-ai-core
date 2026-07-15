# Public Ghost AI Core Patch Notes

This patch adds the Core-side proposal and memory layer for the public jarred-car demo.

## Added

- `velvet/core/ghost_can.py`
- `docs/ghost_can_core_contract.md`
- `examples/ghost_can_core_proposal.py`
- `examples/fixtures/ghost_can_core_observation.json`
- `tests/test_ghost_can_core.py`

## Updated

- `velvet/core/__init__.py`
- `velvet/core/schemas/topics.py`
- `pyproject.toml`

The Ghost Core path is descriptive only. It requires the synthetic, read-only safety flags and rejects executor names, route IDs, shell commands, hardware targets, capability tokens, transmit/write/inject verbs, actuator fields, and relay fields. Core still does not grant physical authority or execute hardware actions.
