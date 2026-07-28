# Native Brain Attention and Observation Maturity

## Purpose

This layer helps Native Brain decide what deserves further thought without adding learning, model dependency, or authority.

The Attention Engine receives a bounded observation and explicit context. It produces a deterministic assessment containing maturity, priority, score, and reasons.

## Observation maturity

Observations may mature through:

```text
new
  -> repeated
  -> confirmed
  -> pattern
  -> expectation
```

Maturity describes evidential history. It does not convert an inference into fact, create canonical memory, or grant authority.

## Attention factors

The first implementation considers:

- observation confidence;
- novelty;
- owner relevance;
- safety relevance;
- repetition;
- corroborating sources;
- historical matches.

The factors are explicit inputs rather than learned weights. This keeps the first version deterministic and auditable.

## Priority

The assessment may be low, normal, high, or critical. Critical priority can result from strong safety relevance, but remains an attention result only.

```text
attention priority != Runtime priority
attention priority != Court authority
authority = none
```

## Silence and patience

A low-priority observation may still be retained in working state, correlated later, or allowed to expire. Native Brain is not required to speak merely because it noticed something.

## Future learning boundary

Later learning may tune bounded attention weights, but it must preserve:

- original observations;
- explicit reasons;
- deterministic fallback values;
- No Drift checks;
- proposal-only authority;
- Runtime and Court ownership.
