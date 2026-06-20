"""Dispatch Court-approved intents to named handlers."""

from typing import Dict

from .handler import IntentHandler
from .intent import Intent
from .receipt import Receipt


class Dispatcher:
    """Routes only authorized receipts to registered handlers."""

    def __init__(self) -> None:
        self._handlers: Dict[str, IntentHandler] = {}

    def register(self, target: str, handler: IntentHandler) -> None:
        if not target.strip():
            raise ValueError("target must be a non-empty string")
        self._handlers[target] = handler

    def dispatch(self, intent: Intent, decision: Receipt) -> Receipt:
        if not decision.authorized:
            return Receipt.create(
                intent_action=intent.action,
                actor=intent.actor,
                target=intent.target,
                authorized=False,
                reason="dispatch denied: Court did not authorize intent",
            )

        handler = self._handlers.get(intent.target)
        if handler is None:
            return Receipt.create(
                intent_action=intent.action,
                actor=intent.actor,
                target=intent.target,
                authorized=False,
                reason="dispatch denied: no handler registered",
            )

        outcome = handler.handle(intent)
        return Receipt.create(
            intent_action=intent.action,
            actor=intent.actor,
            target=intent.target,
            authorized=True,
            reason="handled after Court authorization",
            executor=handler.name,
            outcome=str(outcome),
        )
