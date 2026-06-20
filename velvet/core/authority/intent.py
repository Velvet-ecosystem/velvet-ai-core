"""Structured action intents proposed to Velvet's authority layer."""

from dataclasses import dataclass, field
from typing import Any, Dict


@dataclass(frozen=True)
class Intent:
    """A narrowly scoped action request.

    The language layer may create an Intent, but it may not execute it.
    """

    action: str
    actor: str
    target: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    requires_physical_presence: bool = False
    privilege_elevation: bool = False

    def validate(self) -> None:
        """Raise ValueError when required fields are missing or malformed."""
        for name, value in (
            ("action", self.action),
            ("actor", self.actor),
            ("target", self.target),
        ):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not isinstance(self.parameters, dict):
            raise ValueError("parameters must be a dictionary")
