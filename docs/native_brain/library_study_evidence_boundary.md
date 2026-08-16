# Library-backed Learning Mode evidence boundary

## Decision

Learning Mode does not need a new knowledge-retrieval subsystem.

Velour's Library already owns guarded ingestion, provenance, source lifecycle, deterministic indexing, retrieval, and reference-only evidence bundles. AI Core should consume that existing evidence contract rather than duplicating Library behavior or turning Velour into a learner.

## Ownership

`velours_library` owns:

- source acquisition and preservation
- catalog identity and source provenance
- trust-class metadata
- source lifecycle and freshness warnings
- deterministic chunk identity
- retrieval scoring
- source location
- reference-only evidence bundles

AI Core owns:

- why a Learning Session is studying something
- which retrieved evidence is relevant to the current bounded cognitive workspace
- comparison, contradiction handling, hypothesis formation, and candidate understanding
- keeping retrieval evidence non-authoritative

Runtime owns:

- whether Learning Mode may run
- where bounded study work is placed
- resource and interruption posture
- separately authorized network access when live external retrieval is ever requested

Memory admission and governed promotion remain outside Library retrieval.

## Existing Library contract

The Library already returns provenance-rich evidence records carrying fields equivalent to:

```text
item_id
chunk_id
title
source
source_uri
trust_class
sha256
score
snippet
retrieval_method
location
reference_only = true
canonical_receipt = false
version / lifecycle / staleness metadata
warnings
```

Learning Mode should use these results as evidence, not convert them into a second memory store.

## Study flow

```text
Learning Session objective
        |
read-only Library query
        |
Library EvidenceResult / evidence bundle
        |
ephemeral White Room / cognitive workspace material
        |
stable Library evidence references retained by the session
        |
candidate understanding
        |
existing review / memory-admission / promotion paths
```

The full retrieved passage may be available to an active bounded workspace while the session is running. Long-lived Learning Session state should retain stable evidence references and provenance rather than silently copying Library text into canonical memory.

## Stable evidence reference

A Learning Session reference should be reconstructable from Library provenance. The exact serialization may evolve, but it must preserve at least:

- Library item identity
- deterministic chunk identity where one exists
- canonical source hash
- source location or metadata-only indication

A random retrieval result ID or query ID is not sufficient as the only durable reference because a later reindex of unchanged material should still allow the original evidence to be located.

## Retrieval score is not truth confidence

Library retrieval score answers whether material matched a query. It does not answer whether the material is correct.

Likewise:

- `primary` does not mean infallible
- `community` does not mean false
- a fresh source does not automatically defeat older evidence
- a superseded source may still matter historically
- repeated matching sources do not grant authority

Learning confidence must be formed by the reasoning/evidence policy, not copied from retrieval ranking or Library trust class.

## Conflicts

When Library results disagree, Learning Mode should preserve the disagreement and pass both evidence paths into Reflection / White Room analysis. It must not average conflicting claims into a synthetic certainty.

A Learning Session may end with:

- a candidate explanation
- reduced confidence
- an unresolved contradiction
- a revalidation request
- insufficient evidence
- no change

All are valid outcomes.

## Read-only study boundary

The first Library-backed Learning Mode integration is read-only.

A study worker may request evidence from already-published Library material. It must not gain permission to:

- stage new Library sources
- publish candidates
- alter trust classes
- mark sources stale or refreshed
- adopt packs
- activate pack revisions
- remove Library material
- rewrite provenance

Those remain Library lifecycle operations with their own policy.

## Ghost boundary

Ghost is not used for this path.

Ghost remains fake-car / simulated-vehicle evidence and fixtures. Library-backed study is real knowledge retrieval from the curated offline archive. A Library study worker must receive its own reviewed read-only contract rather than being disguised as a Ghost handler or weakening Ghost's synthetic-only rules.

## Local models

A local model may later assist interpretation of Library evidence, but it is optional and downstream of retrieval. Model output remains candidate reasoning and must point back to the Library evidence that supported it.

A model cannot upgrade `reference_only` evidence into canonical truth, doctrine, authority, or an applied behavior change.

## Web relationship

Captured web material admitted into the Library is ordinary Library evidence with provenance.

Live web retrieval remains a separate Web Leash / Runtime network-policy concern. A Learning Session must remain useful when that path is unavailable.

## Implementation consequence

No new learner code belongs in `velours_library` for Learning Mode v1.

The eventual integration should be a narrow read-only consumer/worker seam that calls the existing Library evidence API and hands bounded results into the current cognition workspace. If a runtime worker is introduced, it should expose only query constraints and evidence results, not the Library's mutation surface.
