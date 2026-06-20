"""Receipts for Velvet authority decisions and executor outcomes."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4


@dataclass(frozen=True)
class Receipt:
    """Immutable record of an authority decision or completed action."""

    receipt_id: str
    intent_action: str
    actor: str
    target: str
    authorized: bool
    reason: str
    executor: Optional[str]
    outcome: Optional[str]
    created_at: str

    @classmethod
    def create(
        cls,
        *,
        intent_action: str,
        actor: str,
        target: str,
        authorized: bool,
        reason: str,
        executor: Optional[str] = None,
        outcome: Optional[str] = None,
    ) -> "Receipt":
        """Create a receipt with a unique identifier and UTC timestamp."""
        return cls(
            receipt_id=str(uuid4()),
            intent_action=intent_action,
            actor=actor,
            target=target,
            authorized=authorized,
            reason=reason,
            executor=executor,
            outcome=outcome,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
