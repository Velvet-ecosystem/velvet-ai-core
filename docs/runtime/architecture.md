# Velvet Core — Architecture

Velvet is not an app.  
It is a resident system.

Everything inside Velvet is designed to be:

- local  
- deterministic  
- replayable  
- inspectable  

No sockets.  
No HTTP.  
No RPC.  
No hidden state.

Only files, events, and receipts.

---

## Core Components

Velvet is made of a small number of cooperating systems.

They do not talk over networks.  
They communicate by writing and reading files.

### Runtime

The runtime is the spine.

It:
- starts all modules  
- stops all modules  
- installs signal handlers  
- keeps the system alive  

The runtime does not contain logic.  
It only holds the system together.

---

### Module Loader

The module loader is Velvet’s lifecycle manager.

Every module must provide:
- start()  
- stop()  

The loader:
- starts modules in registration order  
- stops them in reverse order  

This guarantees clean startup and clean shutdown every time.

---

### Event Bus

The event bus is Velvet’s nervous system.

Modules write events to:

events.jsonl

One JSON object per line.

The UI, dashboards, and tools do not query Velvet.  
They read the event log.

This means:
- no race conditions  
- no hidden state  
- full replay of history  

Velvet never forgets what she did.

---

### Command Bus

The command bus is Velvet’s mouth.

External tools write commands to:

commands.jsonl

Each line is a JSON object:

{ "cmd": "ping" }

The command bus reads this file, parses commands, and emits them into the system as events.

No ports.  
No APIs.  
Only receipts.

---

### Registry

The registry tracks what Velvet knows how to do.

Modules announce themselves with:
- a name  
- a set of capabilities  

The registry emits:
- registry.registered  
- registry.removed  

This allows the UI to discover Velvet’s abilities by reading the event log.

---

### Memory

Memory is not a database.  
It is a receipt book.

Every important event is appended to:

memory_events.jsonl

This allows:
- full audit  
- full replay  
- forensic debugging  
- future learning  

Velvet remembers because she keeps receipts.

---

### State

Velvet does not store mutable state in RAM.

State is reconstructed from:
- memory logs  
- events  
- module receipts  

This means Velvet can always recover after:
- crashes  
- power loss  
- upgrades  

Velvet can always boot from receipts.

---

## UI Model

The UI does not “ask” Velvet anything.

It:
- tails events.jsonl  
- tails memory_events.jsonl  
- reads state files  

The UI is a witness, not a controller.

Velvet speaks by writing.  
The UI listens by reading.

---

## Design Principles

Velvet is built so that:
- everything is human-readable  
- everything is inspectable  
- everything is replayable  
- nothing is hidden  

This makes:
- crashes survivable  
- bugs debuggable  
- systems forkable  
- users sovereign  

Velvet is not a black box.  
She is a ledgered mind.
