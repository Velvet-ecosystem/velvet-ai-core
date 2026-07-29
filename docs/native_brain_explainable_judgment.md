# Native Brain Explainable Judgment

## Purpose

Attention decides what deserves thought. Curiosity decides whether uncertainty should remain open. Explainable Judgment decides whether the current evidence is strong enough to support a bounded candidate claim.

It answers three questions:

1. How confident is Velvet in the available evidence?
2. Why is that confidence justified or limited?
3. Is the claim ready for Presence to consider presenting, or should Velvet observe, correlate, or ask instead?

Judgment is not speech, authority, memory, or execution.

## Confidence bands

Every assessment receives one explicit band:

- `blocked`: integrity, continuity, Runtime context, or safety ownership prevents normal judgment
- `insufficient`: evidence cannot yet support a claim
- `tentative`: a possible interpretation exists, but more evidence is needed
- `supported`: the evidence is adequate for a bounded presentation candidate
- `strong`: mature, reliable, complete, and corroborated evidence strongly supports the candidate claim

Confidence is not certainty. A strong assessment remains revisable when new evidence appears.

## Dispositions

Judgment returns one bounded disposition:

- `blocked`: do not continue normal judgment
- `observe`: retain the observation without making a claim
- `question`: missing or conflicting evidence is best reduced through a bounded question candidate
- `correlate`: compare future evidence before presenting a claim
- `ready`: the candidate claim is supported enough for Presence to evaluate
- `defer_to_safety`: the safety path owns the next decision

`ready` does not mean “speak now.” Presence still decides whether the moment is appropriate.

## Evidence factors

The first deterministic engine considers:

- observation confidence
- Attention score and maturity
- source reliability
- evidence completeness
- freshness
- corroborating sources
- contradictory evidence
- explicitly missing evidence
- integrity alignment
- Riven continuity verification
- Runtime context verification

Every assessment preserves explicit reason codes and the list of missing evidence.

## Candidate claims

Judgment never invents a semantic claim from raw sensor data. A bounded candidate claim must be supplied by an earlier understanding layer or a deterministic domain stem.

Without a candidate claim, even excellent evidence remains an observation.

This keeps evidence calibration separate from interpretation.

## Simulated evidence

Ghost, test, and simulated observations are useful for exercising cognition, but they cannot independently support a real-world claim.

Simulated evidence is capped at tentative confidence and remains in correlation. A verified real observation must support any real-world presentation candidate.

## Safety precedence

Critical or safety-relevant attention bypasses normal explainable judgment. The assessment returns `defer_to_safety`, carries no operational authority, and leaves the established Runtime, Court, and executor path unchanged.

## Authority boundary

Every assessment reports:

```text
canonical: false
authority: none
```

Judgment cannot:

- speak or interrupt
- grant capability
- authorize a proposal
- execute a command
- access hardware or networks
- write canonical memory
- alter Self, personality, or preferences
- replace Runtime, Court, Receipts, or Riven

## Cognitive relationship

```text
Observation
    ↓
Attention and Maturity
    ↓
Bounded Curiosity
    ↓
Explainable Judgment
    ├─ Blocked
    ├─ Observe
    ├─ Question
    ├─ Correlate
    ├─ Ready Candidate
    └─ Defer to Safety
    ↓
Presence decides whether a supported claim enters the moment
    ↓
Rest
```

The doctrine is simple:

> Velvet should know the difference between evidence, suspicion, and support.
