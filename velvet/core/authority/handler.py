"""Legacy handler interface; Core Dispatcher no longer registers or calls it."""

from abc import ABC, abstractmethod
from typing import Any

from .intent import Intent


class IntentHandler(ABC):
    """Legacy callback shape, not a Runtime executor or authority capability."""

    name: str

    @abstractmethod
    def handle(self, intent: Intent) -> Any:
        """Legacy callback contract. Invoking it directly grants no authority."""
        raise NotImplementedError
