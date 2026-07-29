# Native Brain: Bounded Intent Formation

Intent is a proposal about what Velvet may wish to do next. It is not permission, speech, memory, placement, execution, or actuation.

## Core law

> Judgment says what the evidence supports. Expectation says what may happen. Intent proposes what may be worth doing next. Authority remains elsewhere.

## Intent kinds

- `watch`: continue bounded observation without interrupting the owner.
- `ask`: prepare a question for a valid Presence window.
- `suggest`: prepare advice for Presence review.
- `request_authorized_action`: request independent Runtime placement and Court review for consequential work.

There is deliberately no direct `execute` intent.

## Candidate boundary

Every candidate remains:

```text
candidate: true
proposal_only: true
canonical: false
speaking_authorized: false
interruption_authorized: false
memory_write_authorized: false
runtime_placement_authorized: false
court_authorized: false
execution_authorized: false
actuation_authorized: false
authority: none
```

A request may state that Runtime placement and Court authorization are required. It cannot claim either has occurred.

## Presence boundary

Quiet `watch` proposals may become ready for internal review without owner presence. `ask`, `suggest`, and `request_authorized_action` wait for a valid Presence and interruption window. Readiness still does not authorize speech.

## Evidence boundary

`watch` and `ask` may arise from a ready Judgment or an active Expectation. `suggest` and `request_authorized_action` require both a ready Judgment and an active Expectation. Every candidate carries stable evidence references.

## Safety boundary

Safety always outranks ordinary intent formation. Integrity, continuity, and Runtime-context failures block the layer. Superseded proposals retire rather than linger.

## Distributed-body boundary

Native Brain describes the proposal. Runtime chooses and leases a suitable organ. Court independently authorizes consequential work. The executor performs only its bounded contract. The Queen retains whole-body awareness and final coordination.

## Current physical authority

None. This layer adds deterministic local cognition only. It adds no Event Protocol message, memory write, scheduler, node lease, Court decision, tool call, CAN transmission, actuator path, or hardware authority.
