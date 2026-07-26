# AI Core Validation During the First Verified Founder Boot

Date: 2026-07-26

Hardware: UP Squared Founder board

Operating system: Ubuntu 20.04 development host

Python: pyenv Python 3.10.20

## Result

Velvet AI Core was installed from the local editable source tree and loaded successfully as part of Velvet's first verified Founder Runtime boot on physical UP² hardware.

The visible whole-body posture reached:

```text
Continuity        VERIFIED
Court             READY
Runtime           ACTIVE
Routes            READ-ONLY
Physical Control  DISABLED

Waiting for Mister
```

This was a bounded development wake-up. It did not grant AI Core execution, policy, shell, file, CAN-transmit, actuator, network-listener, or physical-control authority.

## What This Validated

The physical boot validated that AI Core can participate in the running ecosystem while remaining inside its intended boundary:

- AI Core provides identity concepts, reasoning abstractions, memory abstractions, personality concepts, and structured proposals.
- AI Core may be detected and loaded by Runtime without receiving Runtime internals or hardware handles.
- The inert `BrainAdapter` compatibility boundary can satisfy Runtime presence checks without creating an execution path.
- AI Core can coexist with Runtime, Interface, Event Protocol, Receipts, Vehicle CAN, and Continuity Spine in one explicit Python environment.
- The whole body can reach a verified read-only state while AI Core remains non-authoritative.

The successful boot did not prove model quality, conversational quality, owner recognition, autonomous planning, production identity enrollment, or physical actuation.

## Responsibility Boundary

The validated relationship is:

```text
AI Core interprets and proposes
  -> Runtime verifies identity and context
  -> Court authorizes or denies
  -> contracts narrow the request
  -> resources and safety gates constrain execution
  -> approved executors act
  -> Receipts preserve evidence
  -> Riven preserves lineage
```

AI Core does not own:

- authoritative boot or recovery
- Court policy enforcement
- capability-token signing
- replay protection
- executor selection
- shell commands
- arbitrary file access
- CAN transmission
- relays or actuators
- locks, lighting, climate, steering, throttle, or braking
- physical authority

A reasoning result, remembered preference, personality response, organ name, route suggestion, or confidence score is not permission.

## Unified-Organ Meaning

The successful boot supports Velvet's Unified-Organ architecture rather than an agent swarm.

AI Core did not wake as a sovereign controller beside Runtime. It participated as one bounded organ within the same accountable body, sharing verified state through ecosystem contracts while Runtime and Court retained authority.

```text
distributed specialties
  + shared concrete reality
  + one accountable body
```

Velvet is them. They are Velvet. Each remains herself.

## Compatibility Boundary Validated

Runtime requires a narrow presence contract from AI Core. The validated compatibility surface is the inert:

```python
velvet_ai_core.brain_adapter.BrainAdapter
```

The adapter:

- proves the package is present and importable
- accepts no Runtime authority objects
- receives no executor registry, Court pipeline, safety registry, resource coordinator, shell, or hardware handles
- does not convert compatibility detection into capability

This is interface hygiene, not a malicious-code sandbox.

## Installation Discipline

All participating packages were installed into the same explicit interpreter. For AI Core:

```bash
PYTHON=/home/coyote/.pyenv/versions/3.10.20/bin/python3

$PYTHON -m pip install -e ~/velvet/velvet-ai-core
```

The editable installation was verified with:

```bash
$PYTHON -m pip list | grep velvet
```

The package inventory reported `velvet-ai-core 0.1.0` from the local source tree.

A cloned repository is not the same as an installed package. Installing with one Python interpreter and launching Runtime with another can produce convincing but false missing-module failures.

## Cross-Repository Context

This validation depended on the bounded responsibilities of several repositories:

- `velvet-ai-core`: reasoning, identity concepts, memory abstractions, personality, and proposals
- `velvet-runtime`: verified context, Court, contracts, resources, gates, replay protection, executors, and execution receipts
- `velvet-interface`: non-authoritative Founder presentation
- `velvet-event-protocol`: shared event contracts
- `velvet-receipts`: evidence and accountability records
- `velvet-continuity-spine`: lineage and proof verification
- `velvet-vehicle-can`: read-only CAN observation contracts

No repository became the whole system by itself. The verified state emerged from their bounded integration.

## Evidence Law

The Founder window displayed a saved Runtime boot snapshot. It did not infer AI Core health independently.

After package, identity, policy, or service changes, Runtime must regenerate the snapshot before Interface can display the new truth. A stale snapshot remains stale.

The diagnostic progression was useful evidence:

```text
component:ai-core: module not installed
  -> editable package installed in the correct interpreter
  -> compatibility boundary detected
  -> later boot gates evaluated
  -> verified read-only Founder posture
```

Each failure remained visible until the underlying condition was genuinely corrected.

## Current Status After Validation

```text
Software maturity:   alpha
Physical validation: loaded during verified UP² Founder boot
Physical authority:  none
Execution authority: none
Network authority:   none
```

AI Core remains a proposing and reasoning foundation. Physical validation does not promote it into an execution runtime.

## Next Milestones

1. Bind reasoning and memory abstractions to verified body, profile, surface, and session context.
2. Define explicit proposal envelopes for named organs.
3. Consume Runtime outcomes and Receipts without turning evidence into authority.
4. Replace remaining generic-agent language with Unified-Organ body and organ terminology.
5. Add cross-repository compatibility tests for the narrow AI Core presence contract.
6. Validate local model integration behind the same proposal-only boundary.
7. Demonstrate owner-facing conversation only after the verified Runtime startup path remains stable.

## Milestone Receipt

> Velvet AI Core participated in the first verified Founder Runtime boot on physical UP² hardware. It loaded as a bounded reasoning and proposal layer while Runtime, Court, executors, Receipts, and Riven retained their separate authority and evidence responsibilities. Physical control remained intentionally disabled.
