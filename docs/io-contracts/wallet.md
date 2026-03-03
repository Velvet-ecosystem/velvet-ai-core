# Velvet Wallet — IO Contract

The Velvet wallet is not a blockchain.
It is a deterministic value ledger.

It exists to record, verify, and replay economic state inside Velvet.

All wallet state is derived from receipts.
There is no hidden balance.


## Core Principles

• Wallet state must be replayable  
• Wallet operations must emit receipts  
• Wallet balance must be reconstructible from history  
• Wallet must never mutate state without a record  


## Ledger Model

The wallet is an append-only journal.

Each entry is a receipt with:

- timestamp
- amount
- reason
- resulting balance


## Wallet Actions

The wallet supports the following actions:


### Mint

Adds value to the wallet.

Mint must provide:
- amount
- reason

Mint produces:
- wallet.minted event
- receipt entry
- updated balance


### Spend

Removes value from the wallet.

Spend must provide:
- amount
- reason

Spend is rejected if balance would go negative.

Spend produces:
- wallet.spent event
- receipt entry
- updated balance


### Balance

Returns the current wallet balance.

Balance is not stored.
It is calculated by replaying receipts.


## Required Receipts

Every wallet action must write a receipt.

Receipts are the source of truth.
The wallet may be rebuilt from receipts at any time.


## Events

Wallet must emit:

- wallet.minted
- wallet.spent
- wallet.balance


## Failure Recovery

On crash or restart:
- wallet replays receipts
- recalculates balance
- resumes from last valid state

No balance is ever lost.
Only replayed.
