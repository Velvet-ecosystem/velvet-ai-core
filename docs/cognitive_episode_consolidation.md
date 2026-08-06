# Cognitive Episode Consolidation

Status: Gate 5 implementation contract

A closed cognitive event may be transformed into an evidence-linked episode proposal for memory navigation.

An episode is not raw evidence, a receipt, an authority decision, an execution record, canonical memory, or identity proof.

## Purpose

The current-event workspace holds what appears to be happening now. Prediction records expectations. Action tracking records returned outcomes. Interruption records preserve changes in attention and unfinished effects.

Episode consolidation connects those finished pieces into one navigational object:

```text
cognitive.event.opened
  -> observations and correlations
  -> proposals and external authority references
  -> predictions and outcomes
  -> interruptions and contradictions
  -> evidence-backed boundary
  -> cognitive.event.closed
  -> cognitive.episode.proposed
```

The episode helps Velvet find and explain the sequence later. The underlying sources remain canonical.

## Required Source Pair

Consolidation requires both the original opened-event document and the final closed-event document.

The pair must agree on:

- cognitive event identity
- body
- node
- replay posture

The closed event must use a terminal lifecycle state and may not end before the opened event.

This preserves:

- start time
- end time
- event kind
- completion state
- completion reason
- closing boundary
- source evidence
- correlation identifiers

A free-floating summary cannot create an episode by itself.

## Related Record Validation

Prediction, action-tracking, and interruption views must belong to the same:

- cognitive event
- body
- node
- replay posture

The consolidator refuses:

- pending predictions
- active action tracking
- unaccepted interruption candidates
- mismatched bodies or nodes
- replay/live confusion
- nested commands, capability tokens, executor handles, hardware targets, safeing claims, or authority fields

## Episode Contents

An episode proposal may include:

```yaml
episode_id: episode-entry-1
source_event_id: cog-entry
opened_event_ref: opened-1
closed_event_ref: closed-1
summary: Mister entered the vehicle and the driver door unlocked.
start_time: 100.0
end_time: 101.0
event_kind: vehicle_entry
completion_state: COMPLETED
completion_reason: lock-state-confirmed
actors:
  - Mister
locations:
  - tiburon.driver-door
what_changed:
  - driver door lock changed to unlocked
observation_refs: []
proposal_refs: []
authorization_refs: []
execution_refs: []
outcome_refs: []
prediction_refs: []
prediction_error_refs: []
interruption_refs: []
contradiction_refs: []
boundary_refs: []
action_tracking_refs: []
outstanding_effect_refs: []
receipt_refs: []
```

The proposal explicitly declares:

```yaml
memory_navigation_only: true
canonical_memory: false
identity_proof: false
grants_authority: false
grants_execution: false
grants_actuation: false
```

## Interrupted Episodes

An interrupted event remains a valid episode candidate.

The episode preserves:

- accepted interruption references
- unfinished action-tracking records
- outstanding physical-effect references
- the interruption boundary
- unknown safe-state posture where unresolved

Changing attention does not erase loose physical ends.

## Retention Classes

### `transient`

Short-lived navigational context. It cannot request a continuity anchor.

### `operational`

Ordinary useful event history. This is the default proposal class.

### `significant`

Longer-lived event history requiring:

- an explicit retention-policy reference
- at least one receipt reference

### `protected`

Sensitive or high-consequence history requiring:

- an explicit retention-policy reference
- at least one receipt reference
- a protected-retention reason

A protected proposal may reference an existing Riven continuity anchor when policy permits. It does not create the anchor and does not become identity proof.

## Receipt Boundary

Episode summaries may organize receipt references. They do not replace receipt payloads.

Changing an interpretation later must not rewrite the decision, execution, or outcome receipts that supported the original episode.

Removing episode memory must not remove receipts.

## Riven Boundary

Riven owns:

- identity lineage
- installation and body continuity
- successor relationships
- continuity anchors
- verified gaps and recovery

Episode consolidation may reference a policy-approved continuity anchor. A copied episode cannot create a new identity, verify a successor, or grant privilege.

## Replay

Opened event, closed event, related records, and consolidator must share one replay posture:

- `live`
- `fixture`
- `replay`

A replayed episode remains replayed interpretation. It cannot become a fresh live experience or physical command.

## Capacity and Idempotence

The consolidator has bounded proposal capacity and rejects duplicate episode identifiers.

It does not silently evict older proposals to make a new episode appear successful.

## Tests

The initial test pack proves:

- opened and closed events form a bounded context
- non-terminal closure is rejected
- body, timing, and identity mismatches are rejected
- source-event authority smuggling is rejected
- episodes preserve evidence and receipt references
- protocol envelopes remain non-authoritative
- pending predictions are rejected
- active actions are rejected
- unaccepted interrupts are rejected
- interrupted episodes retain outstanding effects
- significant retention requires policy and receipts
- protected retention requires policy, receipts, and reason
- transient episodes cannot claim continuity anchors
- related views must match body, node, event, and replay posture
- read-only proposals are immutable
- duplicate identifiers and capacity overflow fail closed

## Scope Boundary

This gate does not:

- persist episodes into a memory database
- promote episodes into canonical memory
- create Riven anchors
- rewrite receipts
- learn retention policy
- authorize actions
- invoke executors
- prove consciousness

Memory services and continuity services decide separately whether and how a proposal is retained.

## Core Law

> An episode may tell Velvet where to look. Evidence tells her what happened. Receipts tell her what was authorized and done. Riven tells her who remained continuous.
