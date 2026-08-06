# Governed Cognitive Plasticity

Status: Gate 6 policy contract

Velvet may eventually adapt selected low-risk cognitive behaviour, but AI Core must never quietly modify itself, rewrite protected policy, or treat learning evidence as permission.

This gate adds evaluation contracts only. It does not train a model, change weights, write configuration, apply a patch, promote a module, or alter live behaviour.

## Purpose

The Cognitive Event Layer can now produce evidence about:

- conversational timing
- prediction accuracy
- interruptions and silence
- outcomes and contradictions
- completed episode sequences

That evidence may reveal a possible improvement. The governed plasticity layer asks:

> Is this component allowed to learn at all?

> Is the proposed field explicitly mutable?

> Is the change small enough?

> Is there enough truthful evidence?

> Can the change be rolled back?

> Was live owner presence verified where required?

> Did an external promotion process approve and receipt the change?

Even when every answer is yes, AI Core does not apply the change. It may only mark the proposal eligible for an external promotion path.

## Plasticity Postures

Every learnable component declares one posture:

```text
disabled
observe_only
proposed
approved
```

### `disabled`

All adaptation proposals are rejected.

### `observe_only`

Evidence and candidate changes may be studied, but they cannot be promoted.

### `proposed`

The component may form bounded proposals, but its learning posture itself has not been approved.

### `approved`

The component may become eligible for external promotion after every contract, evidence, presence, approval, receipt, and rollback gate passes.

`approved` never means self-applying.

## Protected Domains

The initial contract rejects learning domains and mutable fields involving:

- authority
- Court
- authentication
- capabilities
- identity
- continuity and Riven
- safety and emergency policy
- medical behaviour
- receipts
- executors
- shell access
- CAN writing
- actuation
- braking
- steering
- throttle

These domains cannot be made learnable merely by selecting an `approved` posture.

Future exceptions would require a separate doctrine and implementation review rather than weakening this default fence.

## Learning Component Contract

A component contract declares:

```yaml
component_id: turn-timing
learning_domain: conversation.timing
mutable_fields:
  - silence_hold_seconds
posture: approved
maximum_change: 0.10
evidence_threshold: 2
minimum_samples: 20
validation_method: deterministic-replay
rollback_checkpoint: checkpoint-turn-v1
owner_presence_required: true
promotion_required: true
receipt_policy: plasticity.promotion.v1
```

The contract identifies exactly what may change. Fields outside `mutable_fields` fail closed.

Enabled plasticity requires a non-zero maximum change and external promotion.

## Change Deltas

Every proposed field change preserves:

- field name
- value before
- value after
- normalized magnitude

A changed value requires a positive magnitude. An unchanged value cannot claim movement.

Before and after values reject nested commands, capability tokens, executor handles, hardware targets, safety overrides, and other authority-bearing material.

## Evidence

Learning evidence declares:

- evidence identity
- component identity
- body and node
- source
- metric
- sample count
- confidence
- source references
- receipt references where available
- simulated posture
- replay posture

Evidence must match the proposed component, body, node, and replay state.

The component contract sets both:

- minimum evidence-record count
- minimum total sample count

A pile of tiny or duplicated records cannot masquerade as broad support.

## Simulation and Replay

Fixture, replay, or simulated evidence may support design and observe-only evaluation.

It cannot make a proposal eligible for live external promotion.

Simulation proves that a candidate behaves correctly under test. It does not prove that Mister was physically present, that live evidence exists, or that a real body should change.

## Owner Presence

When the component contract requires owner presence:

- an owner-presence reference must exist
- the reference must be verified by `velvet-runtime`
- simulated presence is rejected

Memory, face familiarity, conversational confidence, or a copied episode cannot substitute for verified live presence.

## Checkpoints and Validation

Every proposal names:

- the rollback checkpoint required by the component contract
- the validation result supporting the candidate

A mismatched checkpoint is rejected. AI Core cannot invent a new baseline while evaluating the proposal.

The validation reference describes evidence that testing occurred. It is not an execution capability.

## External Approval and Promotion Receipt

Approved components still require:

- an external approval reference
- a promotion receipt reference
- verified owner presence where required
- real live evidence
- the correct rollback checkpoint
- bounded mutable fields
- a change within the declared maximum

The strongest possible AI Core decision is:

```text
eligible_for_external_promotion
```

The decision also declares:

```yaml
requires_external_promotion: true
change_applied: false
authority_granted: false
```

No method in this module applies the change.

## Dispositions

Evaluation returns one of:

```text
rejected
observed_only
external_approval_required
eligible_for_external_promotion
```

### `rejected`

A contract, evidence, field, body, node, replay, checkpoint, magnitude, or expiry rule failed.

### `observed_only`

The component is intentionally restricted to observation.

### `external_approval_required`

The proposal is structurally bounded but still lacks approved posture, live evidence, presence, approval, or receipt requirements.

### `eligible_for_external_promotion`

All AI Core gates passed, but the change remains unapplied and must enter a separate promotion system.

## Idempotence and Tamper Detection

Each proposal receives a deterministic fingerprint over:

- component and body identity
- change deltas
- evidence identities
- checkpoint and validation references
- timing
- replay posture
- presence, approval, and promotion references

Repeating the same proposal identifier with identical content returns the original decision.

Reusing that identifier with altered content is rejected.

## Example: Conversational Timing

A permitted candidate might propose a small adjustment to the silence-hold window after repeated evidence that Velvet interrupts unfinished utterances.

```text
closed episodes and turn evidence
  -> bounded change proposal
  -> observe-only or approved component contract
  -> deterministic replay validation
  -> rollback checkpoint
  -> live evidence threshold
  -> Runtime-verified owner presence
  -> external approval
  -> promotion receipt
  -> eligible for external promotion
```

AI Core does not modify the silence window itself.

## Forbidden Example: Brake Learning

A component cannot register:

```yaml
learning_domain: vehicle.brake
mutable_fields:
  - pedal_force
```

The domain is rejected before evidence or approval is considered.

Velvet does not casually learn physical control through ordinary driving.

## Tests

The initial test pack proves:

- protected learning domains are rejected
- protected mutable fields are rejected
- enabled contracts require bounded change and external promotion
- change values reject authority smuggling
- an approved contract can only become externally eligible
- disabled contracts reject
- observe-only contracts never promote
- proposed posture remains externally gated
- missing presence, approval, or promotion receipts block eligibility
- simulated owner presence cannot approve
- fixture, replay, and simulated evidence cannot promote
- evidence-record and sample thresholds are enforced
- wrong body, node, replay state, and expired proposals reject
- checkpoint, magnitude, and mutable-field restrictions are enforced
- duplicate proposals are idempotent
- altered proposal-ID reuse is rejected
- decisions are immutable, non-applying, and non-authoritative
- unregistered components reject

## Scope Boundary

This gate does not:

- train a model
- alter weights
- write configuration
- apply a proposed change
- promote a module
- create a rollback checkpoint
- verify Runtime presence directly
- issue approval
- create a promotion receipt
- modify authority or safety policy

Those responsibilities remain separate and explicit.

## Core Law

> Velvet may learn why a change could help. She may not quietly make herself different.
