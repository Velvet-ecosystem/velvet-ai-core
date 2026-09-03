# Body-State Conversation Resolver

Status: first grounded body-fact resolver

## Purpose

`BodySnapshotConversationResolver` turns a bounded Runtime body-state snapshot into structured Native Brain conversation meaning. It is the first production-facing bridge that lets the shared written/speech conversation path answer from current Velvet body evidence rather than a deterministic fallback.

The resolver does **not** open Runtime files itself. A caller supplies the current `velvet.runtime.body_state_snapshot.v1` mapping through an injected provider.

```text
Runtime body-state snapshot provider
        |
        v
BodySnapshotConversationResolver
        |
        v
GroundedConversationMeaning
        |
        v
velvet-language realization
```

## First grounded facts

The initial bounded fact set is intentionally small:

- `cabin.temperature` from `environmental_conditions.cabin_temperature_c`
- `outside.temperature` from `environmental_conditions.outside_temperature_c`
- `cabin.humidity` from `environmental_conditions.relative_humidity_percent`
- `cabin.ambient_light` from `environmental_conditions.ambient_light_lux`
- `ignition.state` from `vehicle_power_state.ignition_state`
- `vehicle.voltage` from `vehicle_power_state.voltage_v`
- `vehicle.speed` from a valid `gnss_fix.speed_kmh`

Additional facts should be added only when their evidence source and truth semantics are explicit.

## Truth boundaries

Ignition state is not engine-running state. Charging voltage is not engine-running proof. A question such as `Is the engine running?` remains unavailable until a verified engine signal such as RPM is connected.

GNSS speed is only returned when the current GNSS record declares `has_fix=true`.

A reading older than its declared `stale_after_ms` remains available only as stale evidence. Language is expected to render the `stale` qualifier as last-known wording.

## Authority

Action-like turns are detected before snapshot access and return `authority_required`. The resolver never grants Runtime, Court, execution, or actuation authority.

The supplied Runtime snapshot must declare:

```text
schema: velvet.runtime.body_state_snapshot.v1
read_only: true
authority: none
actuation_granted: false
actuation_performed: false
```

Anything else fails closed.

## Ownership

- Runtime owns current body-state publication and local storage.
- Core owns grounded fact selection and truth semantics.
- Language owns final human wording.
- Runtime/Court own authorization and execution.

This keeps the written UI, future Founder interface, and Vosk transcripts on one conversation path without creating a second chat or command brain.
