"""Handler interface for Court-approved intents."""

from abc import ABC, abstractmethod
from typing import Any

from .intent import Intent


class IntentHandler(ABC):
    """Named component that processes one approved intent."""

    name: str

    @abstractmethod
    def handle(self, intent: Intent) -> Any:
        """Process an approved intent and return an outcome."""
        raise NotImplementedError
