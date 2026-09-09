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
Tighten the crank pulley bolt to 170 N·m after seating the pulley.
Tighten the crank pulley bolt to 125 ft-lb after seating the pulley.
```

These may be classified as corroborating torque after deterministic unit normalization. Each passage must contain one unambiguous scalar measurement, with identical surrounding text after whitespace normalization. This binds the comparison to the expressed subject, predicate and conditions, instead of just the number and unit. Bare quantities, different components, different conditions and multiple quantities cannot establish a scalar comparison. The original displayed values and stable Library references remain attached to the synthesis.

Negated quantities, bounds, ranges and approximations are conservatively excluded from scalar comparison. Identical complete passages can still be compared as text, preserving their qualifications. The exclusion is bounded and deterministic; it is not a general semantic or grammatical parser.

If comparable values disagree beyond the bounded tolerance, Core returns `conflicted`. It never averages them into a synthetic answer.

## Non-numeric comparison

When no comparable measurement is available, lexical overlap alone never establishes agreement. Extractive corroboration additionally requires the full received passages to match after whitespace normalization. Word order, case, punctuation, subjects, predicates, negation and conditions remain significant. Paraphrases that this bounded check cannot establish remain `mixed`, even if a human could recognize their agreement. The existing `comparison:lexical-overlap` qualifier is retained for compatibility, but can only accompany corroboration after this stronger check.

Direct negation, different predicates, subjects or conditions remain `mixed` unless the existing comparable-measurement rule establishes `conflicted`. Core does not infer a semantic contradiction classification. A truncated evidence window cannot establish corroboration. Comparison happens before display truncation; the existing bounded excerpts and complete stable item/hash/chunk references are retained, including when the distinguishing text lies outside a displayed excerpt.

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

## Reproducing the conversation acceptance

`acceptance/test_library_evidence_acceptance.py` supplies synthetic read-only retrieval responses to the real Runtime provider and conversation composition, Core ingress/resolvers, and Language gateway/realizer. Only retrieval data is synthetic. The suite covers genuine agreement, negation, changed conditions, different subjects/predicates, measurement binding, unresolved/insufficient evidence, reversed ranks and a disagreeing third source. It checks both Core dispositions and final Language wording, provenance and authority fences.

The dedicated `Library evidence acceptance` workflow runs the complete Core pytest suite plus these acceptance tests on Python 3.8, 3.10 and 3.12. It pins:

- Language: `e3f4a65ee83aa30cd1f2081c24b251760b76f007`
- Runtime: `32117e7e6f58c2b5a8c01d952a4cbcd9f43877ec`

With those repositories checked out at `.acceptance-deps/velvet-language` and `.acceptance-deps/velvet-runtime` under Core, run:

```sh
python -m pip install -e . -e .acceptance-deps/velvet-language 'pytest>=7.4,<8.4'
PYTHONPATH="$PWD/.acceptance-deps/velvet-runtime" python -m pytest tests acceptance -q -ra --junitxml=library-evidence-results.xml
```

The workflow retains JUnit executed counts and the exact tested Core, Language and Runtime commits. It requires no production identity, keys or Library service. This proves the software comparison/composition boundary, not live retrieval, LAN or hardware acceptance. No persisted state, API, receipt or configuration migration is required. Revisit the dependency pins when deliberately testing a new combination; these pins do not constitute the ecosystem compatibility ledger.
