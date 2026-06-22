# Core and Runtime Responsibility Boundary

Velvet AI Core and Velvet Runtime serve different layers of the ecosystem.

## Core

Core defines doctrine, identity concepts, proposal models, conversational and memory abstractions, module base classes, and descriptive schemas.

Core may:

- interpret context
- maintain memory
- produce proposals
- describe desired outcomes
- route requests toward Runtime

Core may not:

- authorize physical action
- sign capability tokens
- select or invoke approved executors
- bypass safety gates
- consume replay tokens
- control shell, files, relays, CAN writers, or actuators directly

## Runtime

Runtime owns secure boot, continuity, identity binding, capability policy, Court authorization, safety gates, executor registration, replay protection, and execution receipts.

The sole approved action path is:

```text
proposal
  -> narrow Runtime request boundary
  -> strict intent
  -> Court
  -> signed token
  -> safety gate
  -> approved executor
  -> receipts
```

## Legacy Runtime Language

Some early Core classes and documentation use “runtime” to describe local lifecycle orchestration. That wording does not grant authority and does not replace `velvet-runtime`.

Legacy command ingestion must be treated as developmental input only. It may be adapted into route requests, but it must never directly execute commands or touch hardware.

## Shared Rule

```text
Core proposes.
Runtime authorizes.
Executors act.
Receipts remember.
```
