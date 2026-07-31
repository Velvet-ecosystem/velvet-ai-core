# Velvet Engineering Heuristics

These are starting rules of thumb, not substitutes for measurements, safety analysis, or receipts.

- Prefer deterministic interfaces over clever ones.
- Sensors should degrade gracefully.
- Every hardware module earns trust through tests.
- One primary responsibility per handmaiden.
- Calibration is a feature, not an afterthought.
- Approval screens are not security boundaries.
- Receipts are part of behavior, not decoration.
- Simulated hardware exercises the same path as real hardware.
- Local identity survives network failure.
- Compute priority follows consequence, not excitement.
- Serviceability matters before elegance.
- A clean adapter beats a heroic one-off fix.
- Benchmark the whole body under pressure.
- Watch slow degradation, not only hard failure.
- Hardware capacity describes possibility, not permission.
- Confidence strengthens evidence, never authority.
- Bench success is not vehicle approval.
- Recovery creates new evidence; it does not rewrite the failure.
- Missing capability is denied capability.
- Protected workloads shed convenience before sacrificing receipts or safety.
- A dependency is executable trust and must explain why it exists.

## Use

Architecture reviews, Module Lab promotion, hardware selection, failure analysis, and pull-request review should cite the relevant heuristic and then provide concrete evidence. A heuristic may identify where to look; the test receipt decides what actually happened.

When evidence repeatedly contradicts a heuristic, update the heuristic openly and preserve the history of why it changed.
