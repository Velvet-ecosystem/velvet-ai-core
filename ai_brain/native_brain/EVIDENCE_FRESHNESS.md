# Native Brain Evidence Freshness

Cross-organ evidence is only useful while its time context remains honest.

A contribution now carries an observation timestamp. The freshness evaluator creates a separate append-only review that records age, base confidence, effective confidence, and one of four dispositions:

- `fresh`
- `aging`
- `stale`
- `invalid`

Fresh evidence keeps its original confidence. Aging evidence loses confidence deterministically. Stale or invalid evidence contributes no active confidence to fusion, but its record and provenance remain visible.

## Allowed

- evaluate age using timezone-aware timestamps
- preserve the original contribution unchanged
- decay confidence through a configured aging window
- exclude stale and invalid findings from active fusion
- retain stale and invalid contribution IDs in the fusion record
- expose the evaluation time and effective confidence

## Forbidden

- silently refreshing an old timestamp
- treating stale agreement as current certainty
- deleting inconvenient or conflicting history
- inventing confidence for invalid evidence
- granting authority because evidence is fresh
- claiming execution because confidence is high

## Authority boundary

Freshness changes evidence quality, not permission.

Every freshness and fusion record begins with `authority_granted=False` and `execution_performed=False`. Runtime and Court remain the only authority path.

> Confidence must age with the evidence that carries it.
