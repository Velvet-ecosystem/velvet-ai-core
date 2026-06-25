# SPDX-License-Identifier: GPL-3.0-only
"""Apply already-approved memory transitions through a narrow writer bridge."""

from __future__ import annotations

from typing import Any, Dict

from velvet.core.memory.lifecycle import MemoryTransition


class MemoryTransitionBridge:
    """Append reviewed transitions without granting or evaluating authority."""

    def __init__(self, writer: Any) -> None:
        self._writer = writer

    def append(self, transition: MemoryTransition, approved: bool) -> Dict[str, Any]:
        if not isinstance(transition, MemoryTransition):
            raise TypeError("transition must be a MemoryTransition")
        if approved is not True:
            raise PermissionError("memory transition requires prior approval")
        return self._writer.write_event(**transition.to_write_args())
