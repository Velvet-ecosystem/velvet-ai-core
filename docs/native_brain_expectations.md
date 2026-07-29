# Native Brain Bounded Expectations

## Purpose

Expectation Formation gives Velvet a deterministic way to review one stable,
supported pattern and describe what **may** happen again under named conditions
and within a finite time horizon.

It does not predict destiny. It creates an expiring candidate for later bounded
intent review.

> A pattern says what has repeatedly happened. An expectation says what may
> happen again if the relevant conditions return.

## Upstream requirement

Expectation Formation accepts only a `PatternAssessment` that is:

- `stable`;
- backed by a `PatternCandidate`;
- explicitly eligible for expectation review;
- aligned with integrity, continuity, and verified Runtime context;
- outside an active safety-priority path.

Emerging and testable patterns remain observations. Repetition alone cannot
produce an expectation.

## Domain framing

A domain stem must supply:

- a bounded expectation statement;
- explicit triggering conditions;
- stable evidence references;
- the evaluation time;
- a finite horizon;
- a review interval;
- contradiction and missed-occurrence counts;
- existing candidate timing when reviewing an earlier expectation.

Native Brain does not invent a domain claim from raw sensor values.

Example:

```text
Pattern:
Battery voltage tends to fall during prolonged parked audio load.

Triggering conditions:
- vehicle parked
- audio amplifiers remain active

Expectation candidate:
If the parked audio load continues, battery voltage may fall again.

Horizon:
300 seconds

Review:
120 seconds
```

## States

- `provisional`: the stable pattern supports a candidate, but confidence remains
  below the active threshold;
- `active`: the candidate is sufficiently supported for later intent review;
- `weakened`: one contradiction or missed occurrence reduced support;
- `expired`: the original finite lifetime ended;
- `retired`: repeated contradiction or missed outcomes no longer support it;
- `blocked`: integrity, continuity, Runtime context, or safety owns the path;
- `none`: the inputs do not justify an expectation candidate.

## No automatic renewal

An existing expectation keeps its original `formed_at` and `expires_at` values.
Review does not slide the expiry window forward. When review is due, the
assessment reports:

```text
review-due-no-auto-renewal
```

A future layer may propose a new candidate from newly assessed evidence, but
this layer cannot silently extend the old one.

## Contradiction and expiry

One contradiction or missed occurrence weakens a candidate. Repeated
contradiction or repeated misses retire it. Reaching the expiry boundary expires
it even if no contradiction appeared.

This prevents expectations from fossilizing into background assumptions.

## Candidate boundary

Every `ExpectationCandidate` fixes the following posture:

```text
candidate: true
expectation: true
fact: false
prediction: false
canonical: false
speaking_authorized: false
memory_write_authorized: false
execution_authorized: false
authority: none
```

An active expectation is only eligible for a later **intent review**. It cannot:

- speak or interrupt;
- create an operational proposal;
- select a node or executor;
- write canonical memory;
- access tools or hardware;
- authorize Runtime placement;
- authorize Court or actuation;
- renew itself;
- claim certainty.

## Distributed-body boundary

Expectation Formation describes a bounded cognitive result. It does not decide
where later work runs.

The continuing body law remains:

> Native Brain describes the work. Runtime chooses and leases the organ. Court
> authorizes consequential work. The selected organ performs its bounded
> contract. The Queen retains whole-system awareness and final coordination.

## Determinism

Identical pattern and expectation context inputs produce identical assessments.
Time enters only as an explicit input. The engine does not read a clock, network,
model, memory store, or sensor directly.

## Next layer

A later Bounded Intent Formation layer may review active expectations alongside
Presence, Attention, Curiosity, Judgment, and safety context. Eligibility for
that review is not permission to act.
