"""Minimal decision gate for Velvet action intents."""

from dataclasses import dataclass, field
from typing import FrozenSet

from .intent import Intent
from .receipt import Receipt


@dataclass(frozen=True)
class AuthorityContext:
    """Trusted local context presented to the decision gate."""

    presence_verified: bool = False
    allowed_actions: FrozenSet[str] = field(default_factory=frozenset)
    allowed_targets: FrozenSet[str] = field(default_factory=frozenset)


class Court:
    """Return an allow or deny receipt without performing the action."""

    def evaluate(self, intent: Intent, context: AuthorityContext) -> Receipt:
        try:
            intent.validate()
        except ValueError as exc:
            return self._deny(intent, "invalid intent: %s" % exc)

        if intent.action not in context.allowed_actions:
            return self._deny(intent, "action is not allowed")

        if intent.target not in context.allowed_targets:
            return self._deny(intent, "target is not allowed")

        needs_presence = (
            intent.requires_physical_presence or intent.privilege_elevation
        )
        if needs_presence and not context.presence_verified:
            return self._deny(intent, "verified physical presence is required")

        return Receipt.create(
            intent_action=intent.action,
            actor=intent.actor,
            target=intent.target,
            authorized=True,
            reason="authorized by Court",
        )

    @staticmethod
    def _deny(intent: Intent, reason: str) -> Receipt:
        return Receipt.create(
            intent_action=intent.action,
            actor=intent.actor,
            target=intent.target,
            authorized=False,
            reason=reason,
        )
