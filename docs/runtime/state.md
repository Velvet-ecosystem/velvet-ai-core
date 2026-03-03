# Velvet Core State (Derived)

Velvet does not keep “truth” in RAM.

Velvet keeps:
- **commands** (what was asked)
- **events** (what happened)
- **memory** (what Velvet remembers)
- **snapshots** (what is true *right now*)

**State is derived.**
If Velvet crashes, state is reconstructed by replaying files.

---

## Files

Velvet Core uses these local files (relative to `/var/lib/velvet`):

- `velvet_config.json`  
  Static configuration inputs.

- `events.jsonl`  
  Append-only event stream (one JSON object per line).

- `commands.jsonl`  
  Append-only command stream (one JSON object per line).

- `memory_events.jsonl`  
  Append-only memory log (one JSON object per line).

- `health.json`  
  Latest health snapshot (overwritten).

- `wallet.json`  
  Latest wallet snapshot (overwritten).

---

## State vs Events

**Events are history.**  
**State is now.**

Events are immutable append-only receipts.  
State is a **computed view** built from events + snapshots.

---

## Rebuild Order (Boot Replay)

On boot, Velvet reconstructs state in this order:

1. Load `velvet_config.json`
2. Initialize registry (capabilities map)
3. Replay `events.jsonl` from oldest → newest
4. Replay `memory_events.jsonl` from oldest → newest (optional, depending on UI needs)
5. Load snapshots:
   - `wallet.json`
   - `health.json`

This yields the current derived state, even after crashes.

---

## Snapshot Rules

Some modules produce “latest view” files:

### `health.json`
- overwritten each interval
- represents current system health

### `wallet.json`
- overwritten after wallet changes
- represents current wallet state (balance + metadata)

Snapshots are **not authoritative history**.
They are fast access points.
If they are missing, state must still be reconstructible via replay.

---

## Determinism Contract

Velvet Core must remain:
- **deterministic**
- **replayable**
- **human-debuggable**

This means:
- no hidden network state required to boot
- no internal RPC required for truth
- state can always be reconstructed from files

---

## UI Contract

The UI does not ask Velvet “what happened.”

The UI reads:
- `events.jsonl` (history)
- `health.json` (now)
- `wallet.json` (now)
- `registry` events (capabilities)
- optional `memory_events.jsonl` (memory thread)

The UI may replay events to rebuild its own model.

---

## Future (Planned)

Likely additions to state reconstruction:

- `registry.json` snapshot  
  cached capability map for fast boot

- `state.json` snapshot  
  a single merged derived state for UI

- a “replay cursor” file  
  to avoid replaying the full history on every boot

But the rule stays the same:

**Velvet can always boot from receipts.**
