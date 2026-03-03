# Velvet AI Core

**PLEASE BE PATIENT, THIS PROJECT IS UNDER ACTIVE DEVELOPMENT**

**Offline-first, modular AI runtime for automotive and embedded systems.**

Velvet AI Core is a lightweight, event-driven runtime designed for resource-constrained environments where cloud connectivity cannot be assumed. It provides a pluggable module system, structured logging, and configurable persistence—all with zero external dependencies.

---

## Features

- **Offline-First Architecture**: No cloud dependency; all operations local
- **Event-Driven**: Pub/sub event bus for inter-module communication
- **Hot-Swappable Modules**: Dynamic loading and unloading of feature modules
- **Health Monitoring**: Built-in heartbeat and health status tracking
- **Failure Recovery**: Automatic rollback on module initialization failures
- **Automotive Grade Linux (AGL) Ready**: Designed for Yocto/AGL integration
- **Zero External Dependencies**: Pure Python 3.8+ with stdlib only

---

## Architecture

Velvet Core is built on four key primitives:

1. **Runtime** — Lifecycle orchestrator (boot, run, shutdown)
2. **Module Loader** — Dynamic module registration and management
3. **Event Bus** — Asynchronous event pub/sub for module communication
4. **Command Bus** — JSONL-based command ingestion for external control

All modules extend the `VelvetModule` base class and implement standard lifecycle hooks (`start()`, `stop()`).

---

## Quick Start

### Installation

```bash
pip install velvet-ai-core
```

### Basic Usage

```python
from velvet.core import VelvetRuntime

# Create and start the runtime
runtime = VelvetRuntime()
runtime.start()

# Runtime will run until stopped
# Ctrl+C or SIGTERM will trigger graceful shutdown
```

### Creating a Custom Module

```python
from velvet.core.velvet_module import VelvetModule

class MyModule(VelvetModule):
    def __init__(self):
        super().__init__(name="my_module")
    
    def start(self):
        self.log("MyModule started")
    
    def stop(self):
        self.log("MyModule stopped")
```

See `docs/` for full module development guide.

---

## Project Structure

```
velvet-ai-core/
├── velvet/
│   ├── core/              # Core runtime components
│   │   ├── runtime.py     # Main runtime orchestrator
│   │   ├── module_loader.py
│   │   ├── modules/       # Built-in modules
│   │   ├── schemas/       # Event/command schemas
│   │   └── interfaces/    # Abstract interfaces
│   └── modules/           # Base for pluggable modules
├── docs/                  # Architecture documentation
├── tests/                 # Test suite
└── LICENSE                # GPLv3
```

---

## Documentation

- [Architecture Overview](docs/runtime/architecture.md)
- [Boot Sequence](docs/runtime/boot.md)
- [Event Contracts](docs/io-contracts/events.md)
- [Command Contracts](docs/io-contracts/commands.md)
- [Failure Recovery](docs/failure-recovery/failure.md)

Full documentation available in the `docs/` directory.

---

## Hardware Modules

Velvet Core supports pluggable hardware modules for vehicle integration:

- **velvet-vehicle-can** — CAN bus learning and fingerprinting (read-only)
- More modules coming soon

Hardware modules are distributed separately and installed as optional dependencies.

---

## Requirements

- Python 3.8 or later
- No external dependencies (stdlib only)

**Optional:**
- `python-can` — Required for CAN hardware modules
- `pytest` — For running tests

---

## Development

### Running Tests

```bash
pip install -e .[dev]
pytest
```

### Code Style

This project follows PEP 8 conventions and uses type hints where applicable.

---

## License

This project is licensed under the **GNU General Public License v3.0** (GPLv3).

See [LICENSE](LICENSE) for full terms.

**TL;DR:** You are free to use, modify, and distribute this software, but any modifications or network-accessible services using this code must also be open-sourced under GPLv3.

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Before submitting:**
- Ensure all tests pass (`pytest`)
- Follow existing code style
- Add tests for new features
- Update documentation as needed

---

## Contact

- **GitHub**: [github.com/Velvet-ecosystem/velvet-ai-core](https://github.com/Velvet-ecosystem/velvet-ai-core)
- **Issues**: [github.com/Velvet-ecosystem/velvet-ai-core/issues](https://github.com/Velvet-ecosystem/velvet-ai-core/issues)
- **Discussions**: [github.com/Velvet-ecosystem/velvet-ai-core/discussions](https://github.com/Velvet-ecosystem/velvet-ai-core/discussions)

---

## Acknowledgments

Velvet AI Core is designed for automotive-grade embedded systems and builds on principles from:

- Automotive Grade Linux (AGL)
- Event-driven architecture patterns
- Offline-first design principles

---

**Version**: 0.1.0  
**Status**: Alpha — API subject to change
