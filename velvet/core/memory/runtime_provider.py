# SPDX-License-Identifier: GPL-3.0-only
"""Runtime-facing provider contract for read-only memory recall."""

from __future__ import annotations

from typing import List

from .retrieval import MemoryRetrievalService, RetrievedMemory


class RuntimeRecallProvider:
    """Expose Core retrieval through Runtime's expected callable signature."""

    def __init__(self, service: MemoryRetrievalService) -> None:
        if not isinstance(service, MemoryRetrievalService):
            raise TypeError("service must be a MemoryRetrievalService")
        self._service = service

    def __call__(self, query_event_id: str, limit: int) -> List[RetrievedMemory]:
        return self._service.retrieve(query_event_id=query_event_id, limit=limit)
