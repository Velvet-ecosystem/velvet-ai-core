# Library-backed conversation grounding

## Purpose

Velvet may answer informational questions from Velour's curated offline Library without treating retrieval as body truth, canonical memory, doctrine, or execution authority.

## Flow

```text
human question
  -> velvet-language ConversationGateway
  -> Runtime conversation composition
  -> body resolver
       -> verified body fact when applicable
       -> otherwise UNAVAILABLE
  -> Library evidence resolver
       -> Runtime-normalized read-only evidence bundle
       -> one bounded provenance-backed passage
  -> Core EVIDENCE meaning
  -> velvet-language wording
```

Body grounding is attempted first. This keeps questions such as cabin temperature on live body state even if similar words also exist in manuals or notes.

## FACT versus EVIDENCE

`FACT` is reserved for grounded scalar facts such as a current sensor value.

`EVIDENCE` is reference-only material retrieved from Velour's Library. An evidence response must carry:

- a bounded text passage
- a human source label
- stable Library references
- the `reference-only` qualifier
- lifecycle warnings when the source is stale or superseded

Language should therefore say that Velour *found* the passage rather than silently stating the passage as verified body truth.

## Stable references

The first conversation integration preserves references equivalent to:

```text
library:item:<item_id>
library:sha256:<canonical source hash>
library:chunk:<deterministic chunk id>
```

A retrieval score is never copied into truth confidence. It only determined which passage the Library returned first.

## Failure posture

If the Library service is absent, unreachable, malformed, or returns no full-text passage, Core returns `UNAVAILABLE`. The shared conversation path continues running and body questions remain independent.

## Authority

Library retrieval cannot grant Runtime, Court, executor, network, CAN, relay, shell, or physical-control authority. Action-like turns hit the existing authority fence before Library retrieval is attempted.

## Future synthesis

This v1 connection deliberately returns one bounded passage. A later evidence reasoning layer may compare multiple Library passages, contradictions, or local-model interpretations, but its conclusions must retain the stable evidence references and must not convert retrieval into canonical truth automatically.
