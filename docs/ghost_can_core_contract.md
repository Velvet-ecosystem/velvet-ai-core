# Ghost CAN Core Contract

Velvet AI Core may describe, summarize, and remember a public Ghost CAN observation. It must not execute it.

The public chain is:

```text
velvet-vehicle-can -> velvet-event-protocol -> velvet-ai-core -> velvet-runtime -> velvet-receipts -> velvet-interface
```

Core requires the synthetic, read-only safety flags and rejects executor names, routes, hardware targets, shell commands, capability tokens, CAN write/inject verbs, actuators, and relays.

Core may create a `GhostCanProposal`, a narrow description-only `Intent`, a Court decision for that descriptive intent, a human-readable summary, and an observation memory record with `authority_status="observation_only"`.

Core must not create physical authority, hardware bus access, CAN writers, actuator commands, relay commands, shell execution, executor selection, or capability tokens.

## Demo

```bash
python examples/ghost_can_core_proposal.py
```
