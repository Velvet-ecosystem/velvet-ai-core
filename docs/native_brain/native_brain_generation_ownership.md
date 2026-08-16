# Native Brain Generation Ownership

## Decision

Velvet AI Core currently contains two Native Brain code families. They are not peers and must not be treated as interchangeable runtime owners.

### Canonical active family

`velvet/core/native_brain/`

This is the canonical Native Brain package for new Core work, including Learning Mode integration. New production-facing cognition code should target this family together with `velvet/core/cognition/` where deeper workspace, consolidation, prediction, interruption, and governed-plasticity contracts live.

The installed `velvet-ai-core` package is discovered from `velvet*` packages, so this family is part of the published package surface.

### Legacy foundation and recovery family

`ai_brain/native_brain/`

This tree is retained as a tested historical deterministic foundation and migration/recovery source. It preserves important early architecture including the decision spine, receipt reflection, proposal-only learning, evidence fusion/freshness, Doctrine of Silence, consequence evaluation, distributed reasoning concepts, and the simulated-body practice skeleton.

It is not the target for new Learning Mode orchestration, new runtime-facing integrations, or new production dependencies.

The current package configuration does not install `ai_brain*`; only `velvet*` is included. Source-tree tests may continue to exercise the legacy family so its behavior and lineage remain inspectable.

## Import rule

New Core implementation must not create a dependency from:

- `velvet/core/native_brain/`
- `velvet/core/cognition/`
- Learning Mode contracts
- new Runtime-facing Core adapters

to `ai_brain/native_brain/`.

If a legacy behavior remains valuable, recover the behavior deliberately into the canonical family under current contracts. Do not bridge the namespaces as a shortcut.

## Migration rule

Legacy components are classified one of three ways:

1. **Already superseded or re-expressed**
   - attention and bounded interruption concepts
   - deterministic cognition/judgment concepts
   - distributed-work proposal concepts
   - evidence freshness/confidence concepts
   - simulated-body provenance and authority separation

2. **Valuable recovery sources**
   - receipt reflection semantics
   - proposal-only learning semantics
   - Doctrine of Silence wording and decision distinctions
   - consequence-of-error reasoning
   - recognition/regression fixtures

3. **Do not migrate by import**
   - old aggregate brain orchestration
   - old event-protocol wrappers where current Event Protocol owns the contract
   - old receipt wrappers where Velvet Receipts owns durability
   - old distributed coordination where Runtime now owns placement/lifecycle
   - any legacy field that assumes authority, Runtime state, or world truth without current verified contracts

Migration means extracting the useful rule, writing it against current canonical contracts, and proving it with current tests. It does not mean making the modern package import the legacy tree.

## Learning Mode placement

Learning Mode belongs on the canonical side:

```text
velvet.core.native_brain
        +
velvet.core.cognition
        |
Learning Session / White Room orchestration
        |
Runtime eligibility and placement
        |
Event Protocol / Receipts / memory admission
```

The legacy `LearningProposalBuilder` and receipt-reflection path remain architectural evidence until their useful semantics are intentionally re-expressed in the canonical family. Learning Mode must not hard-wire itself to the legacy namespace merely because those names already exist there.

## Why the legacy tree remains

Removal is not required to establish ownership. Keeping the legacy family provides:

- historical lineage
- regression evidence
- exact behavior recovery when needed
- comparison material during migration
- protection against accidentally forgetting earlier architectural decisions

Its continued presence does not make it a second canonical brain.

## Guardrail

When a feature appears to exist in both families, inspect both before implementing. Prefer the canonical implementation where it exists. If the legacy version contains a missing useful rule, migrate that rule explicitly rather than creating a cross-generation dependency.

**Canonical active Native Brain:** `velvet/core/native_brain/`

**Canonical deeper cognition/workspace:** `velvet/core/cognition/`

**Legacy tested recovery source:** `ai_brain/native_brain/`
