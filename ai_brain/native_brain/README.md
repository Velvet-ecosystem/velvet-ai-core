# Native Brain

> **Generation status:** this `ai_brain/native_brain/` tree is a tested legacy deterministic foundation and recovery source. New production-facing cognition and Learning Mode work belongs in `velvet/core/native_brain/` together with `velvet/core/cognition/`. Do not create new cross-generation imports as a migration shortcut. See `docs/native_brain/native_brain_generation_ownership.md`.

Velvet's Native Brain is a deterministic, local reasoning spine that converts incoming events into explainable recommendations without owning physical authority.

## Core laws

> Events have no meaning until they are placed in context.

> Silence is a decision, not an absence.

Observation records facts. Context gives them meaning. Judgment decides their significance. Attention arbitration decides whether a completed receipt should remain quiet, wait, surface normally, or request interruption.

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

Around that spine, bounded subsystems provide Event Protocol normalization, Unified-Organ reasoning coordination, evidence fusion, evidence freshness, consequence-aware evaluation, the Doctrine of Silence, and a contract-driven simulated body.

## Practice skeleton

Every physical organ can declare one `OrganContract` and use it with both a `HardwareOrganAdapter` and a `FakeOrganAdapter`. The fake twin can inject:

- delay
- bounded numeric noise
- dropout
- impossible values
- stale timestamps

`BodyPracticeSkeleton` accepts either adapter through the same interface. Both successful emissions enter `NativeBrain.process_protocol_event()` and leave through the same receipt callback. Simulation keeps explicit `origin` and `organ_name` provenance inside Event Protocol metadata, but it receives no separate authority, execution, or learning lane.

The result is a practice skeleton: Velvet can exercise timing, evidence quality, dropout, contradiction, and receipt behavior before real hardware is under load.

## Foundation posture

- local and standard-library only
- deterministic recommendation behavior
- explicit context and evidence receipts
- proposal-only learning
- Unified-Organ load sharing without an agent swarm
- confidence decay for aging evidence
- separate costs for false dismissal and false escalation
- silence, defer, present, and interrupt attention dispositions
- hardware-equivalent fake organ contracts
- bounded delay, noise, dropout, impossible-value, and stale-time injection
- one Event Protocol path for simulation and hardware
- one receipt callback path for simulation and hardware
- no direct notification delivery
- no prediction
- no network dependency
- no CAN, Qt, or hardware-library imports
- no autonomous physical control

## Authority boundary

The Native Brain may recommend. Attention arbitration may request silence, waiting, presentation, or interruption. Runtime may coordinate delivery. Court authorizes. Capability-bound organs execute only after authorization.

An event cannot declare its own authority or demand interruption. Agreement, freshness, confidence, owner presence, urgency, severe consequence, an interrupt disposition, or simulated-body provenance may strengthen interpretation, but none unlock execution.

See `ARCHITECTURE.md` for the completed foundation sequence and module responsibilities. See `DOCTRINE_OF_SILENCE.md` for interruption and deferral rules.
