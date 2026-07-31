"""Bounded adapter from Velvet Event Protocol records into Native Brain input.

The adapter normalizes information only. It does not authorize, publish, execute,
or treat a valid event shape as permission.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


_FORBIDDEN_AUTHORITY_FIELDS = frozenset(
    {
        "authorized_by",
        "capability",
        "capability_token",
        "command",
        "executor",
        "executor_name",
        "hardware_target",
        "route",
        "shell",
    }
)


class EventProtocolError(ValueError):
    """Raised when an event cannot be safely normalized."""


@dataclass(frozen=True)
class EventProtocolAdapter:
    """Normalize one validated bus record into the brain's factual event shape."""

    reject_authority_fields: bool = True

    def normalize(self, record: Mapping[str, Any]) -> dict[str, Any]:
        event_type = record.get("event_type", record.get("type"))
        source = record.get("source")
        payload = record.get("payload", {})

        if not isinstance(event_type, str) or not event_type.strip():
            raise EventProtocolError("event_type must be a non-empty string")
        if not isinstance(source, str) or not source.strip():
            raise EventProtocolError("source must be a non-empty string")
        if not isinstance(payload, Mapping):
            raise EventProtocolError("payload must be a mapping")

        if self.reject_authority_fields:
            forbidden = sorted(_FORBIDDEN_AUTHORITY_FIELDS.intersection(payload))
            if forbidden:
                joined = ", ".join(forbidden)
                raise EventProtocolError(
                    f"observation payload contains authority-bearing fields: {joined}"
                )

        metadata = {
            key: record[key]
            for key in (
                "event_id",
                "family",
                "schema_version",
                "timestamp",
                "origin",
                "organ_name",
            )
            if key in record
        }

        normalized_payload = dict(payload)
        if metadata:
            normalized_payload["_event_protocol"] = metadata

        return {
            "type": event_type,
            "source": source,
            "payload": normalized_payload,
        }
