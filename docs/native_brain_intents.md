# Native Brain Bounded Intent Formation

Intent Formation is the proposal boundary between cognition and downstream review.
It allows Velvet to describe a bounded next step without turning thought into
permission.

## Core law

> Native Brain may propose. Presence decides conversational timing. Runtime
> chooses and leases an organ. Court authorizes consequential work. Executors
> perform bounded contracts.

## Accepted upstream support

An intent candidate requires either:

- a supported or strong ready Judgment; or
- an active Expectation that is explicitly eligible for intent review.

The candidate also requires a non-empty objective, evidence references, a finite
lifetime, and a named intent kind.

## Intent kinds

- `watch`: continue bounded observation;
- `inform`: prepare information for Presence review;
- `ask`: prepare a question for Presence review;
- `suggest`: prepare a non-command suggestion;
- `propose_work`: describe work that Runtime may later place.

## Candidate states

- `draft`: coherent but not strong enough for downstream review;
- `ready_for_review`: eligible for the appropriate downstream gate;
- `deferred`: one contradiction requires more observation;
- `withdrawn`: repeated contradiction defeats the proposal;
- `expired`: the original finite lifetime ended;
- `blocked`: integrity, continuity, Runtime context, or safety failed closed.

No candidate renews itself. A later candidate must be earned from newly assessed
evidence.

## Authority boundary

Every intent candidate remains:

```text
candidate: true
proposal_only: true
command: false
canonical: false
speaking_authorized: false
memory_write_authorized: false
runtime_placement_authorized: false
court_authorized: false
execution_authorized: false
actuation_authorized: false
authority: none
```

An intent may report which reviews remain necessary. Reporting a review
requirement does not satisfy it.

## Distributed-body boundary

A `propose_work` intent describes an objective and constraints. It does not name
or reserve a node. Runtime independently evaluates verified advertisements,
health, load, task limits, locality, fallback options, and workload leases.

The Queen retains whole-system awareness and final coordination, but specialist
work should still be placed on suitable organs whenever possible.

## Presence boundary

`inform`, `ask`, and `suggest` candidates require Presence review. Intent
Formation cannot interrupt, speak, or manufacture conversational permission.

## Court boundary

Consequential proposals always report `requires_court_review: true`. Intent
Formation cannot create a Court decision, transfer a prior authorization, or
smuggle authority through a handoff.

## Current limits

This layer adds deterministic local contracts only. It adds no model call,
canonical memory write, Event Protocol message, scheduler, workload lease,
Court decision, executor, network access, CAN transmission, actuator path, or
physical authority. Current physical authority remains none.
