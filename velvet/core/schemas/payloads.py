# velvet/core/schemas/payloads.py
from __future__ import annotations

from typing import Any, Dict


def command_ok(cmd: str, **extra: Any) -> Dict[str, Any]:
    out: Dict[str, Any] = {"cmd": cmd, "ok": True}
    out.update(extra)
    return out


def command_error(cmd: str | None, where: str, error: str) -> Dict[str, Any]:
    return {
        "cmd": cmd,
        "ok": False,
        "where": where,
        "error": error,
    }


def wallet_mint(amount: float, reason: str, balance: float, ts: float) -> Dict[str, Any]:
    return {
        "ts": ts,
        "amount": float(amount),
        "reason": str(reason),
        "balance": float(balance),
    }


def wallet_balance(balance: float) -> Dict[str, Any]:
    return {"balance": float(balance)}
