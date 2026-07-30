"""Decision receipt creation for the Native Brain."""

from __future__ import annotations

from uuid import uuid4

from .models import DecisionReceipt, Judgment


class ReceiptWriter:
    """Create an immutable receipt for every completed judgment."""

    def write(self, judgment: Judgment) -> DecisionReceipt:
        return DecisionReceipt(
            judgment=judgment,
            receipt_id=str(uuid4()),
        )
