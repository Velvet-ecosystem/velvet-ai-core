# Native Brain Architecture

## Purpose

The Native Brain is Velvet's local reasoning spine. It converts incoming events into explainable recommendations while preserving the authority boundaries of Runtime, Court, and physical-control systems.

The Native Brain does not directly actuate hardware, bypass Court, or become an alternate authority path.

## Core law

> Events have no meaning until they are placed in context.

Observation records facts. Context gives them meaning. Judgment decides their significance.

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
  ↓
Reflect
  ↓
Learning Proposal
```

Reflection is append-only review. It may flag incomplete reasoning or weak confidence, but it does not rewrite the receipt, change the past, authorize action, or modify learning state.

A learning proposal is also append-only evidence. It identifies a candidate worth reviewing, but it applies no change by itself.

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

Assesses importance, urgency, confidence, and potential consequence.

### Judgment

Produces a recommendation such as ignore, observe, notify, or escalate. It never performs the action itself.

### Receipt

Records the reasoning path, including decisions to take no action.

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

## Authority boundary

The Native Brain may recommend.

Reflection may review and flag.

Learning may propose.

Organs may contribute and coordinate reasoning.

Fusion and freshness may improve evidence quality.

Runtime and Court authorize.

Capability-bound organs execute only after authorization.

## Delivered sprint sequence

1. Decision-spine foundation
2. Event Protocol boundary
3. Reflection and receipt review
4. Proposal-only learning
5. Unified-Organ distributed reasoning
6. Cross-organ evidence fusion
7. Evidence freshness and uncertainty decay

## Current non-goals

- no autonomous physical control
- no automatic weight, prompt, policy, or threshold changes
- no self-promotion of learning proposals
- no prediction
- no receipt mutation or historical rewriting
- no network dependency
- no CAN, Qt, or hardware imports
- no authority bypass
