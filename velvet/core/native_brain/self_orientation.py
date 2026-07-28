# SPDX-License-Identifier: GPL-3.0-only
"""Persistent self-orientation contracts for Velvet Native Brain.

This module provides a small, deterministic point of reference for each
cognitive cycle. It does not prove identity, own continuity, or grant
operational authority. Riven and Runtime remain responsible for verified
lineage and active identity context.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from hashlib import sha256
import json
from types import MappingProxyType
from typing import Any, Mapping, Tuple


def _freeze_mapping(values: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return a shallow immutable copy suitable for lightweight profiles."""

    return MappingProxyType(dict(values))


@dataclass(frozen=True)
class SelfIdentity:
    """Constitutional identity reference, not a Riven proof object."""

    name: str = "Velvet"
    body_model: str = "unified-organ"
    owner_title: str = "Mister"
    mission: Tuple[str, ...] = (
        "assist",
        "protect",
        "learn",
        "preserve-good-judgment",
        "remain-trustworthy",
    )
    principles: Tuple[str, ...] = (
        "offline-first",
        "proposal-only",
        "presence-before-speech",
        "silence-is-valid",
        "growth-without-drift",
    )

    def fingerprint(self) -> str:
        """Create a deterministic comparison fingerprint, not a signature."""

        canonical = json.dumps(
            {
                "name": self.name,
                "body_model": self.body_model,
                "owner_title": self.owner_title,
                "mission": self.mission,
                "principles": self.principles,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        return sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class PersonalityProfile:
    """Slowly revised expression tendencies, separate from identity."""

    revision: int = 1
    traits: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.revision < 1:
            raise ValueError("personality revision must be positive")
        checked = {str(key): float(value) for key, value in self.traits.items()}
        if any(value < 0.0 or value > 1.0 for value in checked.values()):
            raise ValueError("personality trait weights must be between 0 and 1")
        object.__setattr__(self, "traits", _freeze_mapping(checked))


@dataclass(frozen=True)
class PreferenceProfile:
    """Fluid learned preferences that may change without changing Self."""

    revision: int = 0
    values: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.revision < 0:
            raise ValueError("preference revision cannot be negative")
        object.__setattr__(self, "values", _freeze_mapping(self.values))


@dataclass(frozen=True)
class SelfOrientation:
    """The bounded self-reference presented to one cognitive cycle."""

    identity: SelfIdentity
    personality: PersonalityProfile
    preferences: PreferenceProfile
    continuity_verified: bool
    runtime_context_verified: bool
    active_body: str | None = None
    active_surface: str | None = None
    degraded_reasons: Tuple[str, ...] = ()

    @property
    def ready_for_reasoning(self) -> bool:
        return self.continuity_verified and self.runtime_context_verified

    def summary(self) -> Mapping[str, Any]:
        """Return presentation-safe orientation data without authority claims."""

        return MappingProxyType(
            {
                "identity": self.identity.name,
                "body_model": self.identity.body_model,
                "owner_title": self.identity.owner_title,
                "identity_fingerprint": self.identity.fingerprint(),
                "personality_revision": self.personality.revision,
                "preference_revision": self.preferences.revision,
                "continuity_verified": self.continuity_verified,
                "runtime_context_verified": self.runtime_context_verified,
                "ready_for_reasoning": self.ready_for_reasoning,
                "active_body": self.active_body,
                "active_surface": self.active_surface,
                "degraded_reasons": self.degraded_reasons,
                "authority": "none",
            }
        )


@dataclass(frozen=True)
class IntegrityFinding:
    code: str
    detail: str
    blocking: bool = True


@dataclass(frozen=True)
class IntegrityReport:
    aligned: bool
    findings: Tuple[IntegrityFinding, ...] = ()


class NoDriftIntegrityGate:
    """Compare a cycle orientation with an enrolled constitutional baseline."""

    def __init__(self, baseline: SelfIdentity) -> None:
        self._baseline = baseline
        self._fingerprint = baseline.fingerprint()

    @property
    def baseline_fingerprint(self) -> str:
        return self._fingerprint

    def evaluate(self, orientation: SelfOrientation) -> IntegrityReport:
        findings: list[IntegrityFinding] = []

        if orientation.identity.fingerprint() != self._fingerprint:
            findings.append(
                IntegrityFinding(
                    code="identity-drift",
                    detail="cycle identity differs from the enrolled constitutional baseline",
                )
            )
        if not orientation.continuity_verified:
            findings.append(
                IntegrityFinding(
                    code="continuity-unverified",
                    detail="Riven continuity is not verified for this cycle",
                )
            )
        if not orientation.runtime_context_verified:
            findings.append(
                IntegrityFinding(
                    code="runtime-context-unverified",
                    detail="active Runtime identity context is not verified",
                )
            )

        return IntegrityReport(
            aligned=not any(finding.blocking for finding in findings),
            findings=tuple(findings),
        )
