# SPDX-License-Identifier: GPL-3.0-only

from __future__ import annotations

from typing import Any, Dict


class MemoryLifecycle:
    def __init__(self, writer: Any) -> None:
        self._writer = writer

    def propose(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._writer.write_event(
            "candidate", payload, authority_status="candidate"
        )
