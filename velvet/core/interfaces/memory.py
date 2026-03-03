# velvet/core/interfaces/memory.py
from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Any, Dict, Iterable


class MemoryInterface(ABC):
    """
    Abstract interface for Velvet's long-term memory.
    """

    @abstractmethod
    def write(self, kind: str, payload: Dict[str, Any]) -> None:
        raise NotImplementedError

    @abstractmethod
    def read(self, kind: str | None = None) -> Iterable[Dict[str, Any]]:
        raise NotImplementedError
