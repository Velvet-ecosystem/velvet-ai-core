# Capability Ownership Map

## Purpose

Every durable capability has one accountable owner, known dependencies, explicit outputs, receipt types, degraded behavior, and forbidden direct callers. Named handmaidens remain specialties in one Velvet body, not independent agents.

Implemented as machine-readable rows with `velvet.core.schemas.CapabilityOwnership`.

## Authority levels

- `OBSERVE`
- `PROPOSE`
- `GOVERNED_CONTROL`
- `GOVERNED_EMERGENCY`

Ownership does not grant execution. Runtime and Court remain below UI, language models, scenes, and organs.

## Initial map

| Capability | Owner | Fallback | Authority | Forbidden direct callers |
|---|---|---|---|---|
| Owner-facing voice and presence | Velvet | silent local UI | PROPOSE | raw model output, remote web client |
| Archive, receipts, history | Velour | Velvet read-only cache | OBSERVE | arbitrary modules, guest tools |
| Minimal-risk driving proposal | Charlotte | stop and notify | GOVERNED_CONTROL | UI, language model, scene |
| Medical watch and emergency assessment | Temperance | Velvet notification posture | GOVERNED_EMERGENCY | entertainment, guest profile |
| Engine and CAN diagnostics | Ruby | read-only raw capture | OBSERVE | UI write controls, model output |
| Cabin, HVAC, comfort, air quality | Jade | safe environmental defaults | GOVERNED_CONTROL | scene objects, unapproved plugins |

## Required fields per capability

- capability name
- owning handmaiden
- inputs and outputs
- dependencies
- fallback owner
- authority level
- receipt types
- degraded behavior
- forbidden direct callers

## Rules

- One primary owner per capability.
- A fallback owner receives responsibility only through governed handoff.
- Multiple organs may contribute evidence without sharing execution authority.
- Direct calls from forbidden layers fail even when the UI displays approval.
- New capabilities require a map row before Module Lab promotion.
