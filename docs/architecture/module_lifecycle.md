# Module Lifecycle Standard

## Purpose

All modules use the same lifecycle vocabulary so initialization, readiness, degradation, recovery, shutdown, receipts, and test automation are predictable.

Implemented by `velvet.core.module_lifecycle`.

## States

`DISCOVERED -> CONFIGURED -> INITIALIZING -> READY -> ACTIVE`

Failure and shutdown branches use:

- `DEGRADED`
- `FAILED`
- `RECOVERING`
- `SHUTTING_DOWN`
- `OFFLINE`

The contract contains a policy for every state and an explicit allowed-transition map. Illegal jumps are rejected.

## Every state policy records

- entry condition
- exit condition
- timeout behavior
- receipt type
- health event type
- owning handmaiden
- fallback behavior
- whether lifecycle posture permits authority

Lifecycle authority is necessary but never sufficient. The conservative standard contract permits authority only in `ACTIVE`; Runtime identity, Court authorization, capability tokens, execution contracts, safety gates, resource coordination, and replay protection still apply.

## Required behavior

- `DISCOVERED`: identity known; no operational authority.
- `CONFIGURED`: validated configuration loaded; no operational authority.
- `INITIALIZING`: dependencies and hardware checks in progress.
- `READY`: prepared but not yet active.
- `ACTIVE`: performing its declared role through governed paths.
- `DEGRADED`: bounded service only; unsafe capabilities removed.
- `FAILED`: no operational authority.
- `RECOVERING`: recovery attempt is observable and receipt-linked.
- `SHUTTING_DOWN`: new work refused; resources released.
- `OFFLINE`: no heartbeat or capability advertisement.

Promotion through Module Lab must test every reachable failure and recovery branch.
