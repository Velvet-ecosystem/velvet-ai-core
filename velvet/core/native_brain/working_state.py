# SPDX-License-Identifier: GPL-3.0-only
"""Ephemeral Native Brain working state, separate from canonical memory."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from uuid import uuid4


class ThreadStatus(str, Enum):
    OPEN = "open"
    RESOLVED = "resolved"
    EXPIRED = "expired"


@dataclass
class OpenThread:
    subject: str
    reason: str
    expires_after: timedelta = timedelta(hours=1)
    thread_id: str = field(default_factory=lambda: f"thread_{uuid4().hex}")
    opened_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: ThreadStatus = ThreadStatus.OPEN

    @property
    def canonical(self) -> bool:
        return False

    def expire_if_stale(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        if self.status is ThreadStatus.OPEN and current - self.opened_at >= self.expires_after:
            self.status = ThreadStatus.EXPIRED
            return True
        return False

    def resolve(self) -> None:
        self.status = ThreadStatus.RESOLVED


@dataclass
class DeferredThought:
    content: str
    defer_reason: str
    expires_after: timedelta = timedelta(minutes=15)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def canonical(self) -> bool:
        return False

    def is_stale(self, now: datetime | None = None) -> bool:
        current = now or datetime.now(timezone.utc)
        return current - self.created_at >= self.expires_after
