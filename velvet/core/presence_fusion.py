"""Purpose-specific presence evidence fusion without granting authority."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Dict, Iterable, Optional, Tuple


class PresencePurpose(str, Enum):
    ACCESS = "access"
    SAFETY = "safety"
    PERSONALIZATION = "personalization"
    MEDICAL_ESCALATION = "medical_escalation"


@dataclass(frozen=True)
class PresenceObservation:
    presence_source: str
    spatial_presence_source: str
    zone: str
    timestamp: float
    fresh_until: float
    confidence: float
    range_confidence: float
    living_motion_detected: bool
    identity_claim: Optional[str] = None
    owner_match_confidence: float = 0.0
    failure_mode: Optional[str] = None
    spoofing_risk: float = 0.0
    permitted_purposes: Tuple[PresencePurpose, ...] = ()

    def __post_init__(self) -> None:
        for name in ("presence_source", "spatial_presence_source", "zone"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("%s must be a non-empty string" % name)
        for name in (
            "confidence",
            "range_confidence",
            "owner_match_confidence",
            "spoofing_risk",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError("%s must be between 0 and 1" % name)

    def is_fresh(self, now: float) -> bool:
        return self.timestamp <= now <= self.fresh_until


@dataclass(frozen=True)
class PresenceFusionResult:
    purpose: PresencePurpose
    zone: str
    confidence: float
    contributing_sources: Tuple[str, ...]
    rejected_sources: Tuple[Tuple[str, str], ...]
    source_diversity_met: bool
    contradiction_count: int
    authority_granted: bool = False


DEFAULT_MINIMUM_SOURCES: Dict[PresencePurpose, int] = {
    PresencePurpose.ACCESS: 2,
    PresencePurpose.SAFETY: 2,
    PresencePurpose.PERSONALIZATION: 1,
    PresencePurpose.MEDICAL_ESCALATION: 2,
}


def fuse_presence(
    observations: Iterable[PresenceObservation],
    *,
    purpose: PresencePurpose,
    zone: str,
    now: float,
    minimum_sources: Optional[int] = None,
) -> PresenceFusionResult:
    accepted = []
    rejected = []
    positive = 0
    negative = 0

    for observation in observations:
        if observation.zone != zone:
            rejected.append((observation.presence_source, "zone_mismatch"))
            continue
        if purpose not in observation.permitted_purposes:
            rejected.append((observation.presence_source, "purpose_not_permitted"))
            continue
        if not observation.is_fresh(now):
            rejected.append((observation.presence_source, "stale"))
            continue
        if observation.failure_mode:
            rejected.append((observation.presence_source, "source_failure"))
            continue

        evidence = (
            observation.confidence
            * max(observation.range_confidence, 0.25)
            * (1.0 - observation.spoofing_risk)
        )
        if purpose == PresencePurpose.ACCESS:
            evidence *= max(observation.owner_match_confidence, 0.1)
        accepted.append((observation.presence_source, evidence))
        if observation.living_motion_detected or evidence >= 0.5:
            positive += 1
        else:
            negative += 1

    unique_sources = tuple(sorted({name for name, _ in accepted}))
    required = (
        DEFAULT_MINIMUM_SOURCES[purpose]
        if minimum_sources is None
        else int(minimum_sources)
    )
    if required < 1:
        raise ValueError("minimum_sources must be positive")

    diversity_met = len(unique_sources) >= required
    confidence = 0.0
    if accepted:
        confidence = sum(value for _, value in accepted) / len(accepted)
    if not diversity_met:
        confidence = 0.0

    contradictions = min(positive, negative)
    if contradictions:
        confidence *= max(0.0, 1.0 - 0.25 * contradictions)

    return PresenceFusionResult(
        purpose=purpose,
        zone=zone,
        confidence=round(confidence, 6),
        contributing_sources=unique_sources,
        rejected_sources=tuple(rejected),
        source_diversity_met=diversity_met,
        contradiction_count=contradictions,
    )
