# velvet/core/command_router.py
from __future__ import annotations

import logging
from typing import Any, Dict

from velvet.core.context import get_event_bus, get_registry
from velvet.core.interfaces.wallet import WalletInterface
from velvet.core.interfaces.memory import MemoryInterface
from velvet.core.schemas.topics import Topics
from velvet.core.schemas.payloads import command_ok, command_error, wallet_balance

log = logging.getLogger("velvet.command_router")


class CommandRouter:
    """
    Safe command routing for core.
    Hardware/vehicle-control commands live elsewhere.
    """

    def __init__(self) -> None:
        self._handlers = {
            "ping": self._ping,
            "wallet.balance": self._wallet_balance,
            "wallet.mint": self._wallet_mint,     # local-only stub
            "memory.write": self._memory_write,
        }

    def handle(self, cmd: Dict[str, Any]) -> None:
        name = str(cmd.get("cmd", ""))
        handler = self._handlers.get(name, self._unknown)
        handler(cmd)

    # ---- helpers ----

    def _emit(self, topic: str, data: Dict[str, Any]) -> None:
        bus = get_event_bus()
        if bus:
            bus.emit(topic, data)

    def _err(self, where: str, msg: str, cmd: Dict[str, Any]) -> None:
        self._emit(Topics.COMMAND_ERROR, command_error(cmd.get("cmd"), where, msg))

    def _get_wallet(self) -> WalletInterface | None:
        reg = get_registry()
        if not reg:
            return None
        return reg.get(WalletInterface)

    def _get_memory(self) -> MemoryInterface | None:
        reg = get_registry()
        if not reg:
            return None
        return reg.get(MemoryInterface)

    # ---- handlers ----

    def _ping(self, cmd: Dict[str, Any]) -> None:
        log.info("ping")
        self._emit(Topics.COMMAND_PONG, {"ok": True})

    def _wallet_balance(self, cmd: Dict[str, Any]) -> None:
        w = self._get_wallet()
        if not w:
            self._err("wallet.balance", "WalletInterface not available", cmd)
            return

        bal = float(w.get_balance())
        self._emit(Topics.WALLET_BALANCE, wallet_balance(bal))
        self._emit(Topics.COMMAND_OK, command_ok("wallet.balance", balance=bal))

    def _wallet_mint(self, cmd: Dict[str, Any]) -> None:
        """
        Local-only mint for plumbing/UI.
        Expected:
          {"cmd":"wallet.mint","amount":1.0,"reason":"sim"}
        """
        w = self._get_wallet()
        if not w:
            self._err("wallet.mint", "WalletInterface not available", cmd)
            return

        try:
            amount = float(cmd.get("amount", 0))
        except Exception:
            self._err("wallet.mint", "amount must be a number", cmd)
            return

        reason = str(cmd.get("reason", "sim"))

        if amount <= 0:
            self._err("wallet.mint", "amount must be > 0", cmd)
            return

        # WalletModule emits the real wallet.mint event (with new balance).
        w.mint(amount=amount, reason=reason)
        self._emit(Topics.COMMAND_OK, command_ok("wallet.mint", amount=amount, reason=reason))

    def _memory_write(self, cmd: Dict[str, Any]) -> None:
        """
        Expected:
          {"cmd":"memory.write","kind":"note","payload":{"text":"hi"}}
        """
        m = self._get_memory()
        if not m:
            self._err("memory.write", "MemoryInterface not available", cmd)
            return

        kind = str(cmd.get("kind", "note"))
        payload = cmd.get("payload", {})

        if not isinstance(payload, dict):
            self._err("memory.write", "payload must be an object/dict", cmd)
            return

        m.write(kind=kind, payload=payload)
        self._emit(Topics.COMMAND_OK, command_ok("memory.write", kind=kind))

    def _unknown(self, cmd: Dict[str, Any]) -> None:
        name = str(cmd.get("cmd"))
        log.info("unknown command: %s", name)
        self._emit(Topics.COMMAND_UNKNOWN, {"cmd": name})
