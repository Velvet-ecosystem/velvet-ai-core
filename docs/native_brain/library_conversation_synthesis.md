# Multi-source Library conversation synthesis

## Purpose

Velvet may answer an owner question from more than one published Velour Library passage without turning retrieval into canonical truth.

The conversation path remains:

```text
owner question
  -> body resolver first
  -> read-only Velour Library evidence
  -> bounded Core comparison
  -> structured synthesis meaning
  -> Language realization
```

Runtime still owns transport and configuration. Velour's Library still owns retrieval, provenance, source lifecycle, and indexing. AI Core owns the bounded comparison. Language owns final human wording.

## Three outcomes

Core emits one of three explicit evidence dispositions when at least two independent Library items contain answerable passages:

- `corroborated`: the bounded comparison can justify that the passages point to the same result or guidance;
- `conflicted`: comparable measurements disagree beyond the configured tolerance;
- `mixed`: several passages are relevant but Core cannot safely collapse them into one answer.

A second chunk from the same Library item does not create source diversity. At most three distinct Library items participate in one conversation synthesis.

## Measurement comparison

For common workshop-style measurements, Core may normalize compatible units before comparison. Initial families are torque, pressure, temperature, voltage, current, RPM, speed, length, and percentage.

Example:

```text
170 N·m
125 ft-lb
```

These may be classified as corroborating torque after deterministic unit normalization. The original displayed values and stable Library references remain attached to the synthesis.

If comparable values disagree beyond the bounded tolerance, Core returns `conflicted`. It never averages them into a synthetic answer.

## Non-numeric comparison

When no comparable measurement is available, Core performs a conservative lexical-overlap check on the bounded retrieved passages. Strong overlap may produce extractive corroboration. Otherwise the result is `mixed`.

This is intentionally not semantic free-form summarization. It cannot infer unstated relationships, merge unrelated instructions, or manufacture a conclusion from low-overlap passages.

A future local model may assist semantic interpretation only behind the existing optional-model boundary. Model output would remain candidate reasoning tied to the same Library evidence references.

## Relationship to Judgment and the cognitive workspace

This resolver does not replace the Native Brain `JudgmentEngine` and does not create a second general-purpose judgment system. The existing Judgment Engine remains responsible for broader candidate-claim confidence, contradiction, evidence completeness, and presentation readiness.

Likewise, unresolved Library disagreement remains compatible with the cognitive event workspace doctrine: contradictions are preserved rather than absorbed into a convenient story.

Conversation synthesis is a narrow owner-facing evidence comparison whose output remains non-canonical and authority-free.

## Truth and authority fence

All synthesis outputs remain:

```text
reference_only: true
canonical: false
authority: none
grants_authority: false
grants_execution: false
grants_actuation: false
```

Retrieval score is never copied into truth confidence. Library trust class is retained as provenance metadata, not treated as automatic correctness. Stale or superseded source posture remains visible to Language.

The synthesis path cannot stage, publish, refresh, remove, adopt, or otherwise mutate Library material. It also cannot call Court, an executor, CAN, relays, shell commands, or physical-control APIs.
