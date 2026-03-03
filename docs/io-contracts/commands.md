# Velvet Core Commands (JSONL)

Velvet Core reads commands from:

- `commands.jsonl` (one JSON object per line)

Each command must include a `"cmd"` string field.

Example line format:
{"cmd":"ping"}

---

## Where commands go

Your systemd service uses:

WorkingDirectory = %S/velvet

So `commands.jsonl` lives in the Velvet state directory, typically:

/var/lib/velvet/commands.jsonl

---

## Command envelope

Minimum:
- cmd (string)

Optional:
- any additional fields required by that command

---

## Commands

### ping
Sanity check that the command plane is alive.

Write:
{"cmd":"ping"}

Emits:
- command.pong
- command.ok

---

### wallet.balance
Query the local Velvet wallet.

Write:
{"cmd":"wallet.balance"}

Emits:
- wallet.balance { balance }
- command.ok

---

### wallet.mint
Local-only mint (simulation / Drive-Fi accounting).

Write:
{"cmd":"wallet.mint","amount":1.25,"reason":"drive"}

Fields:
- amount (number > 0)
- reason (string, optional)

Emits:
- wallet.mint
- command.ok

---

### memory.write
Write a memory event into the local Memory Core.

Write:
{"cmd":"memory.write","kind":"note","payload":{"text":"hello velvet"}}

Fields:
- kind (string, optional, default "note")
- payload (object)

Emits:
- memory.event
- command.ok

---

## Errors

If something fails, Velvet emits:

command.error {
  cmd,
  where,
  error
}
