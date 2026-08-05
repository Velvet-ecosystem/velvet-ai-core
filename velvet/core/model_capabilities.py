"""Vendor-neutral model capability selection for local-first cognition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple


KNOWN_CAPABILITIES = (
    "reasoning-small",
    "reasoning-large",
    "vision-local",
    "code-review",
    "speech-transcription",
    "speech-synthesis",
    "memory-summarizer",
    "safety-classifier",
    "document-parser",
    "local-embedding",
)


@dataclass(frozen=True)
class ModelCapabilitySpec:
    capability_name: str
    preferred_local_engine: Optional[str]
    fallback_engine: Optional[str]
    offline_available: bool
    cloud_permission_required: bool
    max_authority_level: int
    data_retention_rule: str
    receipt_required: bool
    refusal_behavior: str

    def __post_init__(self) -> None:
        if self.capability_name not in KNOWN_CAPABILITIES:
            raise ValueError("unknown model capability: %s" % self.capability_name)
        if self.max_authority_level < 0:
            raise ValueError("max_authority_level must be non-negative")
        for name in ("data_retention_rule", "refusal_behavior"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class ModelSelection:
    capability_name: str
    engine: Optional[str]
    available: bool
    used_fallback: bool
    refusal_reason: Optional[str]
    authority_granted: bool = False


class ModelCapabilityRegistry:
    def __init__(self) -> None:
        self._specs: Dict[str, ModelCapabilitySpec] = {}

    def register(self, spec: ModelCapabilitySpec) -> None:
        if spec.capability_name in self._specs:
            raise ValueError("model capability is already registered")
        self._specs[spec.capability_name] = spec

    def select(
        self,
        capability_name: str,
        *,
        local_engine_available: bool,
        fallback_engine_available: bool,
        cloud_permission: bool,
    ) -> ModelSelection:
        spec = self._specs.get(capability_name)
        if spec is None:
            return ModelSelection(
                capability_name=capability_name,
                engine=None,
                available=False,
                used_fallback=False,
                refusal_reason="capability_unavailable",
            )
        if spec.preferred_local_engine and local_engine_available:
            return ModelSelection(
                capability_name=capability_name,
                engine=spec.preferred_local_engine,
                available=True,
                used_fallback=False,
                refusal_reason=None,
            )
        if not spec.fallback_engine or not fallback_engine_available:
            return ModelSelection(
                capability_name=capability_name,
                engine=None,
                available=False,
                used_fallback=False,
                refusal_reason=spec.refusal_behavior,
            )
        if spec.cloud_permission_required and not cloud_permission:
            return ModelSelection(
                capability_name=capability_name,
                engine=None,
                available=False,
                used_fallback=False,
                refusal_reason="cloud_permission_required",
            )
        return ModelSelection(
            capability_name=capability_name,
            engine=spec.fallback_engine,
            available=True,
            used_fallback=True,
            refusal_reason=None,
        )

    def names(self) -> Tuple[str, ...]:
        return tuple(sorted(self._specs))
