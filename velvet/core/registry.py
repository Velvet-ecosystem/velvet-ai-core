# velvet/core/registry.py
from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Type, TypeVar

log = logging.getLogger("velvet.registry")

T = TypeVar("T")


class Registry:
    """
    Very small capability registry.
    Store objects by interface/type key.
    """

    def __init__(self) -> None:
        self._items: Dict[Type[Any], Any] = {}

    def provide(self, key: Type[T], impl: T) -> None:
        self._items[key] = impl
        log.info("Provided capability: %s", getattr(key, "__name__", str(key)))

    def get(self, key: Type[T]) -> Optional[T]:
        obj = self._items.get(key)
        return obj  # type: ignore[return-value]
