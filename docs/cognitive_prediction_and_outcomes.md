# Cognitive Prediction and Outcome Tracking

Status: Gate 3 implementation contract

Velvet can now attach explicit expectations to a bounded current cognitive event and compare those expectations with returned evidence.

This layer is interpretation-only. It does not authorize, execute, retry, perform safeing, create receipts, or replace source observations.

## Purpose

The read-only Cognitive Event workspace answers:

> What appears to be happening now?

Prediction and outcome tracking add two narrower questions:

> What observable state does the body expect next?

> What evidence returned after an externally authorized action or unfolding event?

The resulting loop is:

```text
read-only current-event context
  -> explicit prediction
  -> bounded proposal
  -> external Runtime and Court decision
  -> external execution contract
  -> read-only action tracking
  -> observed outcome and receipt references
  -> explicit prediction resolution
```

A prediction is not an instruction. An action-tracking record is not an executor.

## Workspace Binding

`CognitiveWorkspaceContext` accepts only a validated, open, non-authoritative workspace view.

It preserves:

- cognitive event identity
- body and node identity
- lifecycle state and cognitive mode
- source and correlation references
- proposal references
- external authorization and execution references
- replay state

It rejects:

- closed events
- another body or node
- mismatched replay state
- capability tokens
- executor or hardware handles
- commands
- policy or safety overrides
- nested authority claims

Prediction and action tracking cannot invent a workspace identity independently when using the workspace-bound entry points.

## Explicit Predictions

A prediction declares:

```yaml
prediction_id: prediction-unlock
cognitive_event_id: cog-entry
subject: driver_door_lock
expected_state:
  locked: false
expected_by: 101.0
tolerance: {}
confidence: 0.95
source_model: door-state-model
source_version: "1.0"
source_refs:
  - obs-presence
  - obs-auth
status: pending
```

Every prediction is:

- bounded to one cognitive event
- attached to one body and node
- versioned by source model
- assigned an explicit deadline
- falsifiable through observable state
- replay-aware
- non-canonical
- non-authoritative

Expected state and tolerance values are immutable after creation.

## Prediction Outcomes

A pending prediction may resolve as:

- `confirmed`
- `contradicted`
- `expired`
- `unknown`

Prediction errors remain distinct:

- `mismatch`: returned state conflicts with expectation
- `partial`: only part of the expected state was observable
- `timeout`: the deadline passed without confirmation
- `impossible`: the requested comparison cannot be made truthfully
- `unobservable`: no usable state was available

A mismatch or timeout may inform diagnostics or a future proposal. It never requests an automatic retry.

```yaml
automatic_retry_requested: false
```

A new physical attempt requires a new bounded request and a new external authority path.

## Numeric Tolerance

Predictions may declare a non-negative numeric tolerance for numeric expected fields.

```yaml
expected_state:
  voltage: 12.0
tolerance:
  voltage: 0.25
```

An observation of `12.2` confirms that prediction. An observation of `11.5` contradicts it.

Tolerance keys must correspond to expected fields. Nested expected mappings require matching nested tolerance mappings.

## Externally Owned Action Tracking

`ActionOutcomeTracker` observes the lifecycle of work that was authorized and initiated elsewhere.

Tracking may begin only with:

- an open workspace in `TRACK_ACTION` mode
- an authorization reference already present in that workspace
- an execution reference already present in that workspace

The tracker does not validate the authority itself and does not receive tokens, executor handles, commands, or hardware targets. It merely preserves references to externally owned records.

Tracking states are:

- `started`
- `completed`
- `failed`
- `unknown`
- `interrupted`

`completed` and `failed` require returned observation or receipt evidence.

`interrupted` requires outstanding-effect references so unfinished physical consequences cannot disappear from the story.

## Explicit False Claims

Action-tracking emissions explicitly state:

```yaml
tracking_only: true
execution_performed: false
actuation_performed: false
automatic_retry_requested: false
```

These fields describe what the cognitive tracker did, not what the external executor did.

Only top-level false declarations are allowed. True values or nested execution and actuation claims are rejected.

## Evidence Relationship

Predictions and tracking records preserve references to:

- source observations
- workspace correlations
- external Court decisions
- external execution contracts
- returned outcome observations
- receipts
- outstanding effects

They never rewrite those sources.

A fluent explanation cannot convert an unknown outcome into a completed action. A receipt reference cannot become a replayable command.

## Full Vehicle-Entry Example

```text
presence observations join vehicle-entry event
  -> unlock outcome predicted
  -> unlock intent proposed
  -> Runtime and Court evaluate request
  -> approved executor receives execution contract
  -> workspace enters TRACK_ACTION
  -> action tracker watches external references
  -> lock-state sensor reports unlocked
  -> execution receipt is referenced
  -> action tracking closes completed
  -> prediction resolves confirmed
```

Alternate truthful endings include:

- actuator reports failure
- lock sensor contradicts a success report
- outcome remains unobservable
- deadline expires
- emergency interruption leaves motor state unknown

None of these endings triggers an automatic retry.

## Prediction Stability

The tracker exposes a bounded descriptive ratio of confirmed predictions among resolved predictions.

This can later contribute to the operational `prediction_stability` modulator. It cannot lower authentication, bypass Court, select an executor, suppress a receipt, or alter safety policy.

## Replay

Workspace, prediction, and action tracking must use the same replay posture:

- `live`
- `fixture`
- `replay`

Fixture and replay records are safe to reconstruct because they carry no physical authority and cannot invoke executors.

## Failure and Abuse Tests

The implementation tests that:

- deadlines cannot precede prediction creation
- nested authority fields are rejected
- resolution requires returned evidence
- predictions cannot resolve twice
- tracking cannot finish twice
- completed and failed actions require evidence
- interrupted actions preserve outstanding effects
- closed or forged workspace contexts are rejected
- action tracking requires `TRACK_ACTION`
- authorization and execution references must already exist in the workspace
- prediction errors never request retries
- emission chains preserve creation, resolution, and error order
- read-only views are deeply immutable

## Scope Boundary

This gate does not add:

- learned prediction models
- automatic event segmentation
- salience accumulation
- automatic interruption selection
- episode consolidation
- memory promotion
- plasticity or online learning
- Court logic
- executor selection
- physical authority

Those remain separate gates.

## Core Law

> Velvet may expect an outcome and notice when reality disagrees. Disagreement creates evidence, not permission.
