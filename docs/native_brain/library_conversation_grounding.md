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
       -> one bounded passage or bounded multi-source comparison
  -> Core EVIDENCE / SYNTHESIS meaning
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

Language may word the evidence naturally, but the Library source remains attached separately from the display sentence.

## Contiguous evidence windows

Velour may expand a ranked search snippet into a short contiguous evidence window when it can prove the additional text comes from the same local item and canonical SHA-256. Runtime carries the window metadata through without opening the Library catalog itself.

Core accepts at most three deterministic chunk identities for one evidence window. A valid window therefore preserves:

```text
library:item:<item_id>
library:sha256:<canonical source hash>
library:chunk:<first chunk id>
library:chunk:<next chunk id>
...
```

The seed `chunk_id` must remain among the returned `chunk_ids`. Core rejects oversized, malformed, or internally inconsistent window metadata rather than quietly dropping provenance.

A contiguous window receives the qualifier:

```text
evidence-window:contiguous
```

If Velour reached its configured context bound before the source context ended, Core also carries:

```text
evidence-window:truncated
```

That qualifier is disclosure, not permission to infer the missing continuation.

## Retrieval score and trust

A retrieval score is never copied into truth confidence. It only determined which passage the Library returned first. Window expansion likewise does not alter trust class, lifecycle state, source freshness, or truth status.

## Failure posture

If the Library service is absent, unreachable, malformed, or returns no full-text passage, Core returns `UNAVAILABLE`. The shared conversation path continues running and body questions remain independent.

Malformed window metadata also fails closed at the Library resolver. A larger context request can never erase the requirement for canonical item/hash/chunk provenance.

## Authority

Library retrieval cannot grant Runtime, Court, executor, network, CAN, relay, shell, or physical-control authority. Action-like turns hit the existing authority fence before Library retrieval is attempted.

## Multi-source synthesis

Core may compare a bounded set of distinct Library items while retaining every source reference. Agreement, conflict, or unresolved evidence remains explicit. Contiguous windowing only expands context within one item; it never stitches different sources together and never converts retrieval into canonical truth automatically.
