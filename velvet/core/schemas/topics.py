# velvet/core/schemas/topics.py
from __future__ import annotations


class Topics:
    # System / lifecycle
    COMMAND_OK = "command.ok"
    COMMAND_ERROR = "command.error"
    COMMAND_UNKNOWN = "command.unknown"
    COMMAND_RECEIVED = "command.received"
    COMMAND_PONG = "command.pong"

    # Memory
    MEMORY_STARTED = "memory.started"
    MEMORY_STOPPING = "memory.stopping"
    MEMORY_STOPPED = "memory.stopped"
    MEMORY_EVENT = "memory.event"
    MEMORY_PROVIDED = "memory.provided"

    # Wallet
    WALLET_STARTED = "wallet.started"
    WALLET_STOPPED = "wallet.stopped"
    WALLET_PROVIDED = "wallet.provided"
    WALLET_MINT = "wallet.mint"
    WALLET_BALANCE = "wallet.balance"

    # Health
    HEALTH_UPDATE = "health.update"

    # Heartbeat
    HEARTBEAT = "heartbeat.tick"
