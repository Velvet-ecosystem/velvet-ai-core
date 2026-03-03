# Velvet Core Events (JSONL)

Velvet Core writes all system events to:

- `events.jsonl` (one JSON object per line)

This file is append-only and acts as the system’s nervous system.
UI, telemetry, and analytics systems should tail this file.

Location (systemd):
/var/lib/velvet/events.jsonl

---

## Event envelope

Every event is a JSON object with:

{
  "topic": "string",
  "ts": number,
  "data": object
}

Fields:
- topic: namespaced event name
- ts: unix timestamp (float)
- data: event payload

---

## Core lifecycle

### velvet.started
Emitted when Velvet Core finishes booting.

### velvet.stopping
Emitted when Velvet is shutting down.

---

## Command bus

### command_bus.started
{ path }

### command_bus.stopped
{ path }

### command.received
{ cmd, ... }

### command.ok
{ cmd }

### command.error
{ cmd, where, error }

### command.unknown
{ cmd }

---

## Heartbeat

### heartbeat.tick
{ ts }

Emitted every heartbeat interval.

---

## Health

### health.update
{
  ts,
  status
}

Status is currently:
- "ok"
- later: degraded, fault, etc

---

## Memory

### memory.started
{ path }

### memory.stopping
{ path }

### memory.stopped
{ path }

### memory.event
{
  kind,
  payload
}

---

## Wallet

### wallet.balance
{ balance }

### wallet.mint
{
  ts,
  amount,
  reason,
  balance
}

---

## Registry

### registry.registered
{ name, capabilities }

### registry.removed
{ name }

---

## Design notes

Velvet does not use sockets, HTTP, or RPC internally.

Everything is:
- files
- events
- deterministic
- replayable

This means:
- UI can replay history
- crashes are survivable
- state can be reconstructed
- debugging is human-readable
