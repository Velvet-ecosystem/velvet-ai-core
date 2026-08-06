# Read-Only Cognitive Event Workspace

Status: Gate 2 implementation contract

## Purpose

The current-event workspace gives AI Core a bounded, temporary representation of what appears to be happening now. It associates explicit observation references, preserves contradictions and interruptions, tracks cognitive mode, proposes evidence-backed boundaries, and emits Cognitive Event Protocol-compatible documents.

It is not memory, Court, Runtime, an executor, or identity continuity.

## Deterministic Association

An observation may join the current event only when one of these is true:

- it explicitly names the current `cognitive_event_id`
- it shares a correlation identifier with the current event
- the caller deliberately permits an uncorrelated association

The workspace does not absorb every nearby packet into a convenient story.

Stale, duplicate, wrong-body, unrelated, closed-event, and over-capacity observations receive distinct dispositions. Rejected observations do not silently mutate the event.

## Read-Only Surface

Language and interface consumers receive a deeply immutable view. The workspace output carries:

```text
interpretation_only: true
canonical_evidence: false
authority: none
grants_authority: false
grants_execution: false
grants_actuation: false
```

Nested authority claims, capability tokens, executor handles, commands, hardware targets, policy overrides, retry authorization, and actuation claims are rejected at the observation boundary.

## Modes

```text
OBSERVE
PROPOSE_ACTION
TRACK_ACTION
```

`PROPOSE_ACTION` requires a proposal reference. `TRACK_ACTION` requires references to externally owned Court and execution lifecycle records. These references remain descriptive and cannot be used as capabilities.

## Boundaries

Closing an event requires a previously recorded boundary proposal. Boundary evidence must already belong to the workspace. The close operation preserves the boundary ID and emission chain.

This prevents an event from quietly declaring itself complete without named evidence.

## Capacity and Degradation

The workspace has a fixed observation capacity. It does not evict old evidence to make room for new evidence. When full, it reports `observation-capacity-reached`, emits a degraded workspace update, and preserves the existing event.

## Scope

Gate 2 includes:

- current-event opening and updating
- explicit deterministic association
- immutable snapshots
- contradiction and interruption references
- proposal and action-tracking postures
- evidence-backed boundary proposals
- terminal closure and reset
- Cognitive Event Protocol-compatible event documents

Gate 2 does not include:

- learned event segmentation
- prediction models
- salience scoring
- automatic interruption policy
- episode consolidation
- long-term memory
- learning or plasticity
- physical execution

Those remain later promotion gates.
