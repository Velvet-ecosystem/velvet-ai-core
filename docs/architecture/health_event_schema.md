# Standard Health Event Schema

## Purpose

Every module and node reports health in one language so Runtime, watchdogs, receipts, diagnostics, UI surfaces, and recovery logic do not maintain incompatible state machines.

Implemented by `velvet.core.schemas.HealthEvent`.

## Event types

- `ONLINE`
- `READY`
- `DEGRADED`
- `FAILED`
- `RECOVERING`
- `RECOVERED`
- `OFFLINE`
- `STALE`
- `CALIBRATION_REQUIRED`

Severity is separately recorded as `INFO`, `NOTICE`, `WARNING`, `ERROR`, or `CRITICAL`. A health state does not grade its own authority or automatically demand interruption.

## Required fields

- `event_id`
- `event_type`
- `module_id`
- `node_id`
- `owning_handmaiden`
- `timestamp`
- `severity`
- `state_before`
- `state_after`
- `confidence`
- `diagnostic_payload`
- `receipt_id`

Optional fields:

- `recovery_action`
- `fallback_owner`

## Transition law

A health event records a transition; it does not mutate history. Recovery creates a new event and receipt. Diagnostic payloads should contain bounded, machine-readable evidence such as packet error counts, voltage sag, thermal throttling, frame loss, noise-floor shift, or timeout details.

`HealthEvent.to_event_protocol()` emits a `HEALTH_<TYPE>` record through the ordinary Event Protocol path.

## Safety rules

- `FAILED` and `STALE` remove any assumption of current evidence.
- Recovery actions are descriptions or proposals, not permission to execute.
- Fallback ownership does not transfer capability by itself.
- Repeated transient failures should be rate-limited by Runtime policy rather than hidden.
- UI status is a projection of health receipts, not the source of health truth.
