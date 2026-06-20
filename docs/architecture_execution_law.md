# Velvet Architecture Execution Law

Velvet is local-first, offline-capable, and built around narrow authority boundaries.

The language model may interpret, propose, explain, and request. It must not directly control the shell, files, relays, CAN bus, actuators, or vehicle hardware.

## Core Execution Path

Every meaningful action must pass through the following sequence:

```text
input
  -> identity and context check
  -> strict intent schema
  -> authority and policy check
  -> safety check
  -> approved executor
  -> receipt
```

The execution path is deliberately narrow. Interfaces, voice systems, mobile clients, sensors, handmaidens, and language models are clients of the local gateway. They do not bypass it.

## Roles

### Brain

The brain interprets context and proposes an action.

It may:

- understand natural language
- ask questions
- produce a structured intent
- explain why an action is being proposed

It may not actuate hardware directly.

### Court

The Court evaluates whether the proposed action is allowed.

It checks:

- identity
- local context
- physical presence
- capability and permission
- current safety state
- policy constraints

### Executors

Executors perform approved, tightly scoped actions.

Each executor must:

- accept only validated intent schemas
- enforce its own final safety limits
- reject malformed or unauthorized requests
- return a result suitable for a receipt

### Receipts

Receipts record what was requested, what was authorized, what acted, and what happened.

Receipts provide continuity, reviewability, and a basis for denial when authorization cannot be proven.

## Enforcement Laws

1. **No valid receipt path means deny actuation.**
2. **No verified physical presence means deny privilege elevation.**
3. **No trusted signature means reject the update.**

## Remote Access Boundary

Remote access may observe, request, and receive status.

Remote access must never be treated as equivalent to verified local physical presence. Deep authority requires an in-vehicle physical ceremony and cannot be granted solely through a network session.

## Design Rule

Security checks belong at a few narrow choke points rather than being scattered across every interface.

The governing sentence is:

> Brain proposes. Court authorizes. Executors act. Receipts remember.
