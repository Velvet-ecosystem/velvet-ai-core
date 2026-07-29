# Native Brain Bounded Pattern Formation

## Purpose

Pattern Formation gives Velvet a deterministic way to recognise when repeated supported observations justify a testable hypothesis.

It answers a narrow question:

> Has this relationship appeared with enough independent support to retain as a pattern candidate?

A pattern candidate is not a fact, expectation, canonical memory, operational proposal, or authority object.

## Why this layer exists

Attention identifies observations worth considering. Curiosity keeps uncertainty open. Explainable Judgment distinguishes suspicion from supported evidence.

Pattern Formation comes after those layers because repetition alone is cheap. Sensor noise, duplicated events, one faulty source, and one unusual context can all repeat. Velvet therefore requires both recurrence and independence before a candidate matures.

## Pattern states

A bounded assessment produces one of six states:

- `none`: recurrence is not demonstrated or upstream judgment is not ready
- `emerging`: a supported relationship has repeated but lacks broad independence
- `testable`: recurrence spans independent contexts and has corroborating evidence
- `stable`: strong judgment, broad recurrence, independent contexts, multiple sources, and no contradiction
- `rejected`: contradictory evidence outweighs the proposed relationship
- `blocked`: identity, continuity, Runtime context, or safety prevents normal formation

Even a `stable` pattern remains:

```text
fact: false
expectation: false
canonical: false
authority: none
```

Stable means suitable for a later expectation review. It does not mean the future has been predicted.

## Inputs

The first Pattern Engine evaluates only bounded, supplied evidence:

- a domain-provided candidate statement
- an observation key and scope
- Attention maturity and score
- Explainable Judgment confidence and disposition
- supporting occurrence count
- independent context count
- corroborating source count
- contradiction count
- No Drift integrity state
- verified Riven continuity
- verified Runtime context

Pattern Formation does not invent semantic relationships from raw sensor values. Ruby, Jade, Temperance, another handmaiden stem, or a future domain reasoner must supply the candidate statement.

## Independence before maturity

The initial deterministic thresholds are deliberately conservative:

- one occurrence forms no pattern
- two supported occurrences may form an emerging candidate
- three occurrences across at least two contexts with corroboration may become testable
- five occurrences across at least three contexts and two corroborating sources may become stable when upstream Judgment is strong and contradictions are absent

These values are transparent fallbacks, not learned weights.

## Contradiction

Contradiction is first-class evidence. When contradictory observations equal or outweigh support, the candidate is rejected rather than quietly preserved.

Rejection is not deletion of canonical truth because the candidate was never canonical. It is an explainable working-state outcome that allows future evidence to begin a new candidate cleanly.

## Simulation boundary

Ghost and simulated observations may test Pattern Engine behaviour, but they cannot form a real-world pattern candidate.

This prevents a convincing simulation from being mistaken for lived vehicle, home, forge, or body experience.

## Safety and authority

Safety-relevant or critical observations bypass normal Pattern Formation. The safety path owns the next judgment.

Pattern Formation cannot:

- speak or interrupt
- call tools or networks
- poll hardware
- write canonical memory
- create Runtime priority
- grant Court capability
- execute proposals
- change Self, personality, or preferences

Every assessment and candidate reports `authority: none`.

## Cognitive relationship

```text
Observation
    ↓
Attention and Maturity
    ↓
Bounded Curiosity
    ↓
Explainable Judgment
    ↓
Bounded Pattern Formation
    ├─ Observe
    ├─ Emerging Candidate
    ├─ Testable Candidate
    ├─ Stable Candidate
    ├─ Reject Candidate
    └─ Defer to Safety
    ↓
Rest
```

A later Expectation layer may review stable candidates. It must not treat stability as certainty, and it must preserve contradiction, scope, confidence, and non-authority.

## Doctrine

> Repetition may suggest a shape. Independence and contradiction decide whether the shape deserves a name.
