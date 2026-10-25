"""Retired Core execution API; consequential dispatch belongs to Runtime."""

from .handler import IntentHandler
from .intent import Intent
from .receipt import Receipt


class ConsequentialDispatchRetiredError(RuntimeError):
    """Core receipts cannot authorize registration or invocation of handlers."""


_RETIRED = (
    "Core Dispatcher execution is retired; submit an intent through Velvet Runtime "
    "Court, capability verification, safety, replay protection, and approved execution"
)


class Dispatcher:
    """Import-compatible tombstone that never registers or invokes callbacks.

    Court.evaluate remains available for descriptive/educational decisions.
    Its Receipt is not an execution capability. No simulation flag or supplied
    approval object can re-enable this retired execution path.
    """

    def register(self, target: str, handler: IntentHandler) -> None:
        raise ConsequentialDispatchRetiredError(_RETIRED)

    def dispatch(self, intent: Intent, decision: Receipt) -> Receipt:
        raise ConsequentialDispatchRetiredError(_RETIRED)
