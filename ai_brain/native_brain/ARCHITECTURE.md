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
```

Reflection is append-only review. It may flag incomplete reasoning or weak confidence, but it does not rewrite the receipt, change the past, authorize action, or modify learning state.

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

## Authority boundary

The Native Brain may recommend.

Reflection may review and flag.

Runtime and Court authorize.

Capability-bound organs execute only after authorization.

## Sprint roadmap

1. Package skeleton and architecture
2. Shared data models
3. Deterministic pipeline
4. Event Protocol integration
5. Reflection and receipt review
6. Learning integration
7. Distributed reasoning across Velvet's organs

## Current non-goals

- no autonomous physical control
- no learning or weight changes
- no prediction
- no receipt mutation or historical rewriting
- no network dependency
- no CAN, Qt, or hardware imports
- no authority bypass
