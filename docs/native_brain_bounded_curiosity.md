# Native Brain Bounded Curiosity

## Purpose

Curiosity gives Velvet a lightweight way to keep an unfinished question alive without pretending to know, speaking too soon, or starting an unbounded reasoning loop.

It answers a narrow question:

> Does this observation justify quiet watching, correlation, a future question candidate, or no further thought?

Curiosity is not autonomous research. It does not search networks, poll sensors, open files, call tools, write canonical memory, or execute proposals.

## Dispositions

A curiosity assessment resolves to one of six bounded dispositions:

- `none`: the observation does not justify an unfinished thought
- `watch`: retain a non-canonical working-state candidate and wait for more evidence
- `correlate`: compare conflicting or mature evidence with future observations
- `question_candidate`: prepare a bounded question for Presence to evaluate later
- `resolved`: a mature observation has a sufficient explanation
- `defer_to_safety`: safety handling outranks curiosity

A question candidate is not speech. Curiosity always reports:

```text
speak_now: false
interrupt: false
authority: none
canonical: false
```

Presence still decides whether the moment is appropriate. Runtime and Court retain their existing authority boundaries.

## Quiet watching

Repeated, corroborated, novel, contradictory, or unexplained observations may produce a `CuriosityThreadCandidate`.

The candidate is intentionally not an `OpenThread` yet. It contains only:

- a subject
- a reason
- a bounded expiry
- `canonical: false`
- `authority: none`

The working-state owner may later accept it as an ephemeral Open Thread. Curiosity cannot create canonical memory or preserve the candidate indefinitely.

## Duplicate restraint

When an existing Open Thread already covers the same uncertainty, Curiosity does not create another candidate. It continues watching quietly.

This prevents repeated observations from filling working state with copies of the same unfinished thought.

## Safety precedence

Critical or safety-relevant attention never becomes a curiosity exercise. Curiosity returns `defer_to_safety` and creates no question or thread candidate.

Safety escalation remains data only and follows the established Runtime and Court paths.

## Determinism

The first Curiosity Engine is deterministic and model-free. Identical observation, attention, and context inputs produce identical assessments.

No learned weights are present. Later tuning may change bounded thresholds only if deterministic fallbacks, explicit reasons, No Drift checks, non-authority, and the original observation remain intact.

## Cognitive relationship

```text
Observation
    ↓
Attention and Maturity
    ↓
Bounded Curiosity
    ├─ None
    ├─ Watch
    ├─ Correlate
    ├─ Question Candidate
    ├─ Resolved
    └─ Defer to Safety
    ↓
Presence decides whether any question enters the moment
    ↓
Rest
```

Curiosity exists to support the doctrine:

> I do not know yet, but I am paying attention.
