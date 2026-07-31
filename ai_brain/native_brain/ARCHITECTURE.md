# Native Brain Architecture

## Purpose

The Native Brain is Velvet's local reasoning spine. It converts incoming events into explainable recommendations while preserving the authority boundaries of Runtime, Court, and physical-control systems.

The Native Brain does not directly actuate hardware, bypass Court, or become an alternate authority path.

## Core laws

> Events have no meaning until they are placed in context.

> Silence is a decision, not an absence.

Observation records facts. Context gives them meaning. Judgment decides their significance. Attention arbitration decides whether a completed receipt deserves silence, waiting, ordinary presentation, or interruption.

## Decision spine

```text
Event
  ↓
Observe
  ↓
Context
  ↓
Understand
  ↓
Evaluate
  ↓
Judge
  ↓
Receipt
  ├──→ Attention Decision
  └──→ Reflect
          ↓
      Learning Proposal
```

Reflection is append-only review. It may flag incomplete reasoning or weak confidence, but it does not rewrite the receipt, change the past, authorize action, or modify learning state.

A learning proposal is also append-only evidence. It identifies a candidate worth reviewing, but it applies no change by itself.

An attention decision is append-only. It does not deliver a message or grant permission.

## Responsibilities

### Observation

Records what was reported without adding interpretation.

### Context

Supplies the working world-state for the moment, including:

- runtime mode
- Court permissions
- owner, guest, or unknown presence
- active scene
- recent event history
- other organ activity
- relevant world-state values

### Understanding

Combines observation and context into a plain-language interpretation of what is happening.

### Evaluation

Assesses importance, urgency, confidence, potential consequence, cost of dismissing a real condition, and cost of unnecessary escalation.

Consequence inputs arrive through a separate explicit evaluation profile. Arbitrary event payloads cannot silently grade themselves as urgent, severe, trusted, or authorized.

### Judgment

Produces a recommendation such as ignore, observe, notify, or escalate. It never performs the action itself.

Judgment compares the cost of false dismissal with the cost of false escalation. Serious uncertainty may justify notification, but no consequence score grants authority.

### Receipt

Records the reasoning path, including decisions to take no action.

### Doctrine of Silence

Consumes a completed receipt and an explicit attention profile. It records one of four dispositions:

- silent
- defer
- present
- interrupt

Routine observation remains quiet. Ordinary notifications may wait during quiet mode, protected focus, repetition, or temporary audience absence. Critical importance, immediate urgency, or governed escalation may request interruption despite ordinary silence preferences.

This layer is distinct from observation-maturity or priority scoring. A high attention score can strengthen reasoning, but it does not prove delivery, grant authority, or bypass this arbitration boundary.

### Reflection

Reviews a completed receipt for bounded internal quality signals such as confidence range, evidence reasons, and rationale completeness.

Reflection produces a new linked review record. The original receipt remains immutable. A flagged review is evidence for later human inspection or future approved learning work, not permission to alter behavior.

### Learning proposal

Collects flagged reflection records into an immutable candidate for later governed review. It records its evidence links, subject, disposition, and rationale.

A proposal cannot alter weights, prompts, policy, thresholds, memory, Runtime state, Court permissions, event subscriptions, or physical behavior. Promotion into an actual change requires a separate explicit approval and implementation path.

### Unified-Organ coordination

Organs advertise capability, load, health, availability, limits, and fallback posture. The coordinator may offer, refuse, hand off, or escalate bounded reasoning work.

A handoff is coordination, not authorization. It never creates independent agent identity, private goals, or a direct organ-to-organ authority lane.

### Cross-organ evidence fusion

Named organs may contribute findings about one shared subject. Fusion preserves source links, agreement, conflict, uncertainty, and confidence without turning consensus into permission.

Conflicting findings remain visible. A coherent fusion is stronger evidence only.

### Evidence freshness

Every evidence contribution carries an observation time. A separate append-only freshness review records its age and effective confidence.

Fresh evidence keeps its confidence. Aging evidence decays deterministically. Stale or invalid evidence remains visible in provenance but contributes no active confidence to fusion.

### Consequence-aware evaluation

An explicit immutable profile records urgency, consequence, confidence, cost of dismissal, and cost of escalation. Importance is derived deterministically from urgency and consequence.

The default profile remains routine and observational. Higher recommendations require explicit bounded inputs and produce rationale in the decision receipt.

### Simulated-body practice skeleton

Each physical organ declares a stable `OrganContract` containing its organ name, Event Protocol event type, source, family, and schema version.

A `HardwareOrganAdapter` and its mirrored `FakeOrganAdapter` share that exact contract. The fake adapter may inject bounded delay, numeric noise, dropout, impossible values, and stale timestamps. Nested payload fields use dotted paths so the fault target is explicit and reviewable.

Both adapter kinds produce the same Event Protocol record shape. `BodyPracticeSkeleton` accepts either adapter and sends successful emissions through the same `process_protocol_event()` method and the same receipt callback. A dropped sample produces no event and no receipt.

Simulation provenance is preserved as `origin` and `organ_name` metadata. Provenance may inform interpretation and test assertions, but it does not grant authority, skip validation, create a separate receipt lane, or allow simulated evidence to masquerade as physical evidence.

Impossible values remain subject to ordinary Event Protocol rules. A fake payload that attempts to inject authority-bearing fields is rejected by the same boundary as hardware input.

## Authority boundary

The Native Brain may recommend.

Attention arbitration may remain silent, defer, present, or request interruption.

Reflection may review and flag.

Learning may propose.

Organs may contribute and coordinate reasoning.

Fusion and freshness may improve evidence quality.

Consequence evaluation may raise recommendation severity.

The practice skeleton may inject faults and record outcomes.

Runtime may coordinate delivery. Court authorizes. Capability-bound organs execute only after authorization.

## Delivered foundation sequence

1. Decision-spine foundation
2. Event Protocol boundary
3. Reflection and receipt review
4. Proposal-only learning
5. Unified-Organ distributed reasoning
6. Cross-organ evidence fusion
7. Evidence freshness and uncertainty decay
8. Consequence-aware evaluation and cost of being wrong
9. Doctrine of Silence and attention arbitration
10. Simulated-body practice skeleton and hardware-equivalent fault injection

## Current non-goals

- no autonomous physical control
- no automatic weight, prompt, policy, or threshold changes
- no self-promotion of learning proposals
- no direct notification delivery
- no prediction
- no receipt mutation or historical rewriting
- no network dependency
- no CAN, Qt, or hardware-library imports
- no authority bypass
- no simulation-only authority, event, or receipt lane
