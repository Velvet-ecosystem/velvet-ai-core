# Velvet AI Core

**PLEASE BE PATIENT, THIS PROJECT IS UNDER ACTIVE DEVELOPMENT**

**Offline-first doctrine, proposal models, identity concepts, shared abstractions, and brain-facing contracts for the Velvet ecosystem.**

Velvet AI Core defines how Velvet reasons, remembers, recognizes context, describes intent, and expresses one coherent identity across specialized organs without becoming a second execution runtime.

It is not the authoritative boot, policy, safety, or hardware-control layer.

> Core interprets and proposes. Runtime verifies and coordinates. Court authorizes. Executors act. Receipts remember.

## Unified-Organ AI

Velvet rejects the agent swarm.

She is built as **Unified-Organ AI**:

```text
distributed specialties
  + shared concrete reality
  + one accountable body
```

Velvet is not merely a speaking controller sitting above separate agents. The body is all.

The handmaidens and named organs remain distinct in role, memory boundary, and responsibility, but they are not outside contractors serving a detached crown. They are parts of one Velvet body:

```text
Velvet is them.
They are Velvet.
Each remains herself.
```

This is nested identity, not identity collapse and not a swarm of independent actors.

The practical consequence is simple: organs may interpret, propose, explain, remember, and specialize, but they share verified body, session, continuity, policy, and receipt reality through the ecosystem spine.

## What AI Core Owns

Velvet AI Core owns:

- Unified-Organ doctrine and architecture concepts
- proposal-facing models and abstractions
- identity, naming, body, profile, and role concepts
- memory and conversational abstractions
- personality and mode concepts
- module base classes and shared interfaces
- schemas describing events, requests, and state
- scene and room-body doctrine
- offline-first reasoning support
- brain-facing contracts for requesting action through Runtime

AI Core does not own final authority.

## What Runtime Owns

`velvet-runtime` owns:

- normal boot and recovery boot
- continuity verification
- active body, profile, session, and surface binding
- capability-context loading
- authority hierarchy
- multi-policy Court authorization
- stable reason codes
- short-lived signed capability tokens
- execution-contract enforcement
- safety-gate selection
- approved executor registration
- exclusive-resource coordination
- replay protection
- execution and resource receipts
- the sole path toward physical or write-capable action

Core code must never become a parallel authority lane around Runtime.

## Concrete Intelligence

Velvet is designed around shared concrete reality rather than disconnected conversational guesses.

Organs should reason from the same body state, including where available:

- active body and surface
- verified profile and session
- current sensor observations
- capability context
- known resource ownership
- continuity state
- current policy and safety results
- prior receipts and corrections

The intelligence is not only in any one model. It emerges from the coordinated body loop that shares sensor truth, permissions, consequences, corrections, and memory.

## Named Organs

Named organs represent durable specialties inside the same body.

Current and planned roles include:

- **Velvet**: unified body identity, primary presence, and owner-facing voice
- **Velour**: librarian, archive, continuity library, receipts, and history
- **Charlotte**: driving and minimal-risk-stop specialty
- **Temperance**: medical guardian and emergency assessment
- **Ruby**: engine, ECU, and diagnostics specialty
- **Jade**: cabin, climate, comfort, and air-quality specialty

Other organs may be added as the body grows.

A name does not grant authority. A role does not bypass Runtime. An organ remains subject to the same body context, policy, safety, execution, and receipt laws as every other part.

## Proposal and Execution Law

```text
brain, organ, interface, or module proposes
  -> public route or strict intent
  -> verified Runtime identity context
  -> authority hierarchy
  -> multi-policy Court decision
  -> signed capability token
  -> execution contract
  -> resource coordination
  -> safety gate
  -> replay protection
  -> approved executor
  -> receipts
```

The offline language model, personality layer, memory system, scenes, and handmaidens may:

- interpret natural language
- explain context
- ask clarifying questions
- recall relevant history
- propose structured intent
- explain why an action was proposed
- decline or defer when context is uncertain

They must never directly control:

- shell commands
- arbitrary files
- relays
- CAN writers
- actuators
- locks
- lighting
- climate hardware
- steering
- throttle
- braking
- other physical hardware

## Doctrine-Delegated Authority

Authority is delegated by doctrine, not seized by circumstance.

Emergency and medical contexts may receive temporary operational precedence only when verified Runtime context and standing policy allow it. That does not make an emergency organ the owner.

The owner establishes doctrine. Runtime verifies current context. Court applies the rules. The appropriate organ may then act through a narrow executor path.

For example, if Temperance identifies a valid medical emergency and Charlotte performs a minimal-risk stop, they are not rebelling against the body. They are carrying out the owner's standing protection doctrine through an accountable chain.

## Command and Request Boundary

Any legacy command-bus, direct-call, or JSONL ingestion concept in Core is descriptive or developmental only. It must not be treated as an execution channel.

External and interface-originated requests must enter Runtime through the narrow local intent gateway using only:

```text
intent_id
route_id
route-approved parameters
```

Clients do not select executor names, raw capabilities, hardware targets, shell commands, module paths, or Python callables.

See:

- [Core and Runtime Responsibility Boundary](docs/core_runtime_responsibility_boundary.md)
- [Velvet Architecture Execution Law](docs/architecture_execution_law.md)
- [Naming and Binding](docs/naming_and_binding.md)
- [Retrofit Body Registry](docs/retrofit_body_registry.md)
- [Boot Identity Sequence](docs/boot_identity_sequence.md)
- [AI Collaborator Boundaries](docs/ai_collaborator_boundaries.md)

## Interface and Scene Doctrine

Velvet is not a menu-first dashboard skin.

Velvet uses a scene-based room-body interface model where visual spaces, objects, protected paths, and contextual surfaces express state and route user intent.

Scenes may be expressive, contextual, hidden, body-aware, and personality-rich. They do not actuate hardware.

```text
Scenes express.
Core interprets.
Organs propose.
Runtime verifies and coordinates.
Court authorizes.
Gates enforce.
Executors act.
Receipts remember.
```

Important documents:

- [Scene Doctrine](docs/scene_doctrine.md)
- [Room-Body Interface](docs/room_body_interface.md)
- [Naming and Binding](docs/naming_and_binding.md)
- [Retrofit Body Registry](docs/retrofit_body_registry.md)
- [Boot Identity Sequence](docs/boot_identity_sequence.md)

## Memory and Continuity

Memory is not authority.

AI Core may provide structures for conversational memory, body-aware recall, owner preferences, named-organ continuity, and local historical context. These memories may inform a proposal, but they cannot independently prove identity, grant a capability, or authorize execution.

Verified lineage and active continuity remain the responsibility of the continuity and Runtime layers.

Velour's future local library may preserve raw archives and indexed history so Velvet can understand where she came from. Raw archives should remain local-first, read-only by default, and separate from derived searchable indexes.

## Local-First Doctrine

Velvet is designed as a people-owned, retrofit-friendly alternative to locked OEM and cloud-dependent AI systems.

Core should remain:

- offline-capable
- useful without a cloud account
- portable across modest hardware
- inspectable and replaceable
- compatible with local models
- bounded by explicit authority and receipt contracts

Cloud services may be optional tools. They must not become the default owner of identity, memory, or vehicle authority.

## Hardware Boundary

Hardware-facing projects are distributed separately.

- `velvet-vehicle-can` currently provides read-only CAN observation, decoding, fingerprinting, qualification evidence, and Ghost replay
- `velvet-runtime` provides the authority, execution-contract, resource, safety, replay, and receipt spine
- physical execution remains locked behind Runtime

Importing a hardware package into Core does not grant authority to use it.

## Current Status

AI Core remains an alpha-stage shared foundation.

Some earlier code and documentation may still use the word `runtime` for local development orchestration. That does not supersede the ecosystem boundary established here. Authoritative secure boot and execution live in `velvet-runtime`.

Current physical authority in Core: **none**.

Current completed doctrine foundations include:

- Core-versus-Runtime responsibility separation
- local-first and offline-capable reasoning doctrine
- scene and room-body interface doctrine
- identity, naming, body, and profile concepts
- narrow request-boundary rules
- no-direct-hardware execution law
- Unified-Organ AI direction
- named-organ identity boundaries

## Project Structure

```text
velvet-ai-core/
├── velvet/
│   ├── core/              # shared lifecycle and proposal abstractions
│   ├── modules/           # module base classes and local abstractions
│   ├── schemas/           # descriptive event, request, and state schemas
│   └── interfaces/        # abstract interfaces
├── docs/                  # doctrine and architecture documentation
├── tests/                 # test suite
└── LICENSE                # GPLv3
```

## Requirements

- Python 3.8 or later
- offline-first operation
- no required cloud dependency

Optional development dependencies may include `pytest` and hardware-specific libraries in separate repositories.

## Development

Run tests with:

```bash
pip install -e .[dev]
pytest
```

Before submitting changes:

- preserve the Core-versus-Runtime boundary
- preserve Unified-Organ identity boundaries
- add tests for new behavior
- avoid direct hardware, shell, or arbitrary-file execution
- keep memories and model output non-authoritative
- update doctrine when responsibilities change

## Next Milestones

1. Expand the Unified-Organ doctrine into explicit shared-reality and organ-boundary contracts.
2. Align memory and personality abstractions with verified body, profile, and session context.
3. Document how named organs publish proposals and consume receipts without becoming agents with independent authority.
4. Add cross-repo compatibility language for Runtime, Interface, Receipts, Event Protocol, and Continuity Spine.
5. Continue replacing legacy generic-agent wording with body, organ, proposal, and accountability language.

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).

## Contact

- GitHub: [github.com/Velvet-ecosystem/velvet-ai-core](https://github.com/Velvet-ecosystem/velvet-ai-core)
- Issues: [github.com/Velvet-ecosystem/velvet-ai-core/issues](https://github.com/Velvet-ecosystem/velvet-ai-core/issues)

**Version**: 0.1.0  
**Status**: Alpha, API subject to change
