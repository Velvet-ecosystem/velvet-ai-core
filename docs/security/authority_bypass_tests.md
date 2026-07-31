# Authority-Bypass Tests

## Core rule

Approval is not authority. UI state, language-model output, simulation mode, bench mode, confidence, ownership, and lifecycle readiness may describe context, but none may create a capability the caller does not already possess through Runtime and Court.

## Required proofs

Tests must demonstrate that:

- an approval screen cannot select or create an executor capability
- direct module calls cannot bypass the governed Runtime path
- AI suggestions cannot carry shell, route, executor, capability-token, or hardware-target authority
- write-capable paths remain gated
- read-only vehicle routes cannot become write routes
- simulation mode cannot unlock real actuators
- bench permission cannot become vehicle permission
- lifecycle `READY` is not operational authority
- capability ownership does not replace authorization

## Current contract coverage

`tests/security/test_authority_bypass_contracts.py` proves:

- Event Protocol rejects authority-bearing UI payloads
- simulated organs cannot smuggle capability tokens through impossible-value injection
- bench-only vehicle interfaces remain surface-restricted
- only `ACTIVE` lifecycle posture may qualify for authority, while Runtime and Court remain required
- forbidden direct callers remain explicit in capability ownership records

## Layering law

```text
UI / scene / model / simulation / bench tool
  -> request or observation only
  -> Runtime identity and route validation
  -> Court authorization
  -> signed capability token
  -> execution contract and safety gate
  -> approved executor
  -> receipt
```

Tests should fail closed when any lower layer is unavailable. A visually approved action with no valid capability must remain unexecuted.
