# velvet/core/modules/wallet.py
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Optional

from velvet.core.context import get_event_bus, get_registry
from velvet.core.interfaces.wallet import WalletInterface

log = logging.getLogger("velvet.module.wallet")


class _LocalWalletAdapter(WalletInterface):
    """
    Local stub wallet:
    - stores a numeric balance locally
    - emits events when balance changes
    No keys, no signing, no chain. Yet.
    """

    def __init__(self, module: "WalletModule") -> None:
        self._m = module

    def get_balance(self) -> float:
        return float(self._m.balance)

    def mint(self, amount: float, reason: str) -> None:
        self._m.mint(amount=float(amount), reason=str(reason))


class WalletModule:
    name = "wallet"

    def __init__(self, path: str = "wallet.json") -> None:
        # relative to WorkingDirectory (/var/lib/velvet)
        self.path = Path(path)
        self.balance: float = 0.0
        self._running = False
        self.adapter = _LocalWalletAdapter(self)

    def start(self) -> None:
        self._running = True
        self._load()

        # Provide wallet capability
        reg = get_registry()
        if reg:
            reg.provide(WalletInterface, self.adapter)

        bus = get_event_bus()
        if bus:
            bus.emit("wallet.started", {"path": str(self.path), "balance": self.balance})
            bus.emit("wallet.provided", {"interface": "WalletInterface"})

        log.info("Wallet module started (balance=%s).", self.balance)

    def stop(self) -> None:
        self._running = False
        self._save()

        bus = get_event_bus()
        if bus:
            bus.emit("wallet.stopped", {"balance": self.balance})

        log.info("Wallet module stopped.")

    def mint(self, amount: float, reason: str) -> None:
        if amount <= 0:
            log.info("Ignored mint: amount <= 0 (%s)", amount)
            return

        self.balance = float(self.balance) + float(amount)
        self._save()

        event = {
            "ts": time.time(),
            "amount": float(amount),
            "reason": reason,
            "balance": self.balance,
        }

        bus = get_event_bus()
        if bus:
            bus.emit("wallet.mint", event)

        log.info("Minted %s (%s). New balance=%s", amount, reason, self.balance)

    def _load(self) -> None:
        try:
            if self.path.exists():
                obj = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(obj, dict):
                    self.balance = float(obj.get("balance", 0.0))
        except Exception:
            log.exception("Failed to load wallet file; starting with 0.0")
            self.balance = 0.0

    def _save(self) -> None:
        try:
            obj = {"balance": self.balance}
            self.path.write_text(json.dumps(obj, indent=2), encoding="utf-8")
        except Exception:
            log.exception("Failed to save wallet file")
