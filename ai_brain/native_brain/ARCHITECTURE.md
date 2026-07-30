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
```

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

## Authority boundary

The Native Brain may recommend.

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

## Non-goals for Sprint 1

- no autonomous physical control
- no learning
- no prediction
- no network dependency
- no CAN, Qt, or hardware imports
- no authority bypass
