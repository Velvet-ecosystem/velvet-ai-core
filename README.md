# Velvet AI Core

**PLEASE BE PATIENT, THIS PROJECT IS UNDER ACTIVE DEVELOPMENT**

**Offline-first doctrine, proposal models, identity concepts, and shared abstractions for the Velvet ecosystem.**

Velvet AI Core defines the concepts and brain-facing structures that let Velvet reason, remember, recognize context, describe intent, and participate in the wider ecosystem without directly controlling hardware.

It is not the authoritative boot or execution runtime.

> Core proposes and models. Runtime verifies and authorizes. Executors act. Receipts remember.

## Responsibility Boundary

Velvet AI Core owns:

- doctrine and architecture concepts
- proposal-facing models
- identity, naming, body, and profile concepts
- memory and conversational abstractions
- module base classes and shared interfaces
- schemas that describe events, requests, and state
- offline-first reasoning support

`velvet-runtime` owns:

- normal boot and recovery boot
- continuity verification
- active body, profile, and session binding
- capability-context loading
- Court authorization
- signed capability tokens
- safety-gate selection
- approved executor registration
- replay protection
- execution receipts
- the sole path to physical or write-capable action

Core code must never become a second authority lane around Runtime.

## Execution Doctrine

```text
brain or module proposes
  -> public route or strict intent
  -> verified Runtime identity context
  -> capability policy
  -> Court authorization
  -> signed capability token
  -> matching safety gate
  -> approved executor
  -> receipts
```

The offline language model, personality layer, memory system, and handmaidens may propose, explain, converse, and remember. They must never directly control:

- shell commands
- arbitrary files
- relays
- CAN writers
- actuators
- steering
- throttle
- braking
- other hardware

## Command and Request Boundary

Any legacy command-bus or JSONL ingestion concept in Core is descriptive or developmental only. It must not be treated as an execution channel.

External and interface-originated requests must enter Runtime through the narrow local intent gateway using only:

```text
intent_id
route_id
route-approved parameters
```

Clients do not select executor names, raw capabilities, hardware targets, shell commands, module paths, or Python callables.

See:

- [Core and Runtime Responsibility Boundary](docs/core_runtime_responsibility_boundary.md)
- [Naming and Binding](docs/naming_and_binding.md)
- [Retrofit Body Registry](docs/retrofit_body_registry.md)
- [Boot Identity Sequence](docs/boot_identity_sequence.md)
- [AI Collaborator Boundaries](docs/ai_collaborator_boundaries.md)

## Interface and Scene Doctrine

Velvet is not a menu-first dashboard skin.

Velvet uses a scene-based room-body interface model where visual spaces, objects, and protected paths express context and route user intent. Scenes may be expressive, contextual, hidden, and body-aware, but they do not actuate hardware.

```text
Scenes express.
Core proposes.
Runtime authorizes.
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

## Current Status

Core remains an alpha-stage shared foundation.

Some earlier code and documentation may still use the word “runtime” for local development orchestration. That does not supersede the ecosystem boundary established here. Authoritative secure boot and execution live in `velvet-runtime`.

Current physical authority in Core: **none**.

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

## Hardware Modules

Hardware-facing projects are distributed separately.

- `velvet-vehicle-can` currently focuses on read-only CAN learning and fingerprinting
- physical execution remains locked behind `velvet-runtime`

Importing a hardware package into Core does not grant authority to use it.

## Requirements

- Python 3.8 or later
- offline-first operation
- no required cloud dependency

Optional development dependencies may include `pytest` and hardware-specific libraries in separate repos.

## Development

Run tests with:

```bash
pip install -e .[dev]
pytest
```

Before submitting changes:

- preserve the Core versus Runtime boundary
- add tests for new behavior
- avoid direct hardware or shell execution
- update doctrine when responsibilities change

## License

GNU General Public License v3.0. See [LICENSE](LICENSE).

## Contact

- GitHub: [github.com/Velvet-ecosystem/velvet-ai-core](https://github.com/Velvet-ecosystem/velvet-ai-core)
- Issues: [github.com/Velvet-ecosystem/velvet-ai-core/issues](https://github.com/Velvet-ecosystem/velvet-ai-core/issues)

**Version**: 0.1.0  
**Status**: Alpha, API subject to change
