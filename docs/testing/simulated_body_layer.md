# Simulated Body Layer

## Purpose

Velvet receives a practice skeleton before physical organs carry real load. Every physical organ and its fake twin share one `OrganContract`, Event Protocol entry point, receipt path, and authority boundary.

Implemented by `ai_brain.native_brain.simulated_body`.

## Supported faults

- deterministic delay
- probabilistic packet dropout
- additive numeric noise
- impossible values
- stale timestamps
- malformed payloads
- sudden disconnect
- scheduled recovery
- low-voltage values
- degraded sensor confidence

Dotted paths may target nested values such as `power.voltage` or `sensor.confidence`.

## Path equality rule

```text
hardware adapter ─┐
                  ├─> same OrganContract
fake adapter ─────┘
                       -> same Event Protocol
                       -> same Native Brain processor
                       -> same receipt callback
                       -> same Runtime / Court boundary
```

A dropped or disconnected sample creates no reasoning receipt because no event entered the body path. Disconnect and recovery attempts remain visible in the returned emission reasons so the harness can create health evidence separately.

Malformed packets are not sanitized by a special simulation lane. They are submitted to the ordinary Event Protocol and must be rejected there.

## Safety rules

- simulation origin stays explicit
- fake confidence never becomes authority
- impossible-value injection may test authority fields, but Event Protocol must reject them
- simulation may not register or select a physical executor
- bench adapters remain surface-restricted
- recovery is a new observation, not a rewrite of the outage

## Adapter backlog

Concrete fake adapters should next be bound for CAN, GNSS, microphones, seat sensors, LD2410, ignition and voltage state, cameras, actuator feedback, network nodes, and receipt storage. Each binding must use the standard sensor packet, health event, lifecycle, and node-manifest contracts.
