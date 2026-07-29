# SPDX-License-Identifier: GPL-3.0-only
"""Authority-free distributed-body workload planning contracts.

Native Brain may describe bounded work and understand which verified organs
appear suitable. Runtime owns placement, leases, handoff, and live execution.
Court remains the only authorization path for consequential work.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class NodeTier(str, Enum):
    MICROCONTROLLER = "microcontroller"
    SPECIALIST_LINUX = "specialist_linux"
    HEAVY_LINUX = "heavy_linux"
    QUEEN = "queen"


class NodeAvailability(str, Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    SATURATED = "saturated"
    DEGRADED = "degraded"
    DRAINING = "draining"
    OFFLINE = "offline"
    QUARANTINED = "quarantined"


class CandidateMode(str, Enum):
    PRIMARY = "primary"
    OVERFLOW = "overflow"
    TEMPORARY_ABSORPTION = "temporary_absorption"
    QUEEN_FALLBACK = "queen_fallback"
    PARTIAL = "partial"
    OBSERVE_ONLY = "observe_only"


class PlacementDisposition(str, Enum):
    PLACE_CANDIDATE = "place_candidate"
    DEGRADED_CANDIDATE = "degraded_candidate"
    UNAVAILABLE = "unavailable"


class DegradationMode(str, Enum):
    NONE = "none"
    FULL_REPLACEMENT = "full_replacement"
    PARTIAL_REPLACEMENT = "partial_replacement"
    OBSERVE_ONLY = "observe_only"
    CAPABILITY_UNAVAILABLE = "capability_unavailable"


@dataclass(frozen=True)
class NodeAdvertisement:
    """Verified body-organ capability and live-condition advertisement."""

    node_id: str
    organ: str
    tier: NodeTier
    capabilities: Tuple[str, ...]
    current_load: float
    health: float
    availability: NodeAvailability
    accepted_work_classes: Tuple[str, ...] = ()
    refused_work_classes: Tuple[str, ...] = ()
    max_concurrent_tasks: int = 1
    current_tasks: int = 0
    overflow_capable: bool = False
    fallback_capabilities: Tuple[str, ...] = ()
    temporary_absorption_capabilities: Tuple[str, ...] = ()
    body_verified: bool = True
    continuity_verified: bool = True
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.node_id.strip() or not self.organ.strip():
            raise ValueError("node_id and organ are required")
        if not 0.0 <= self.current_load <= 1.0 or not 0.0 <= self.health <= 1.0:
            raise ValueError("load and health must be between 0 and 1")
        if self.max_concurrent_tasks < 1:
            raise ValueError("max_concurrent_tasks must be at least one")
        if not 0 <= self.current_tasks <= self.max_concurrent_tasks:
            raise ValueError("current_tasks must fit the declared task limit")
        for values in (
            self.capabilities,
            self.accepted_work_classes,
            self.refused_work_classes,
            self.fallback_capabilities,
            self.temporary_absorption_capabilities,
        ):
            if any(not item.strip() for item in values):
                raise ValueError("advertised values cannot be blank")
        if self.authority != "none":
            raise ValueError("node advertisements cannot carry authority")

    @property
    def available_capacity(self) -> float:
        if self.current_tasks >= self.max_concurrent_tasks:
            return 0.0
        return round(max(0.0, 1.0 - self.current_load), 4)


@dataclass(frozen=True)
class WorkRequirement:
    """Bounded description of needed work, not an execution request."""

    work_id: str
    work_class: str
    required_capabilities: Tuple[str, ...]
    preferred_capabilities: Tuple[str, ...] = ()
    min_health: float = 0.5
    max_load: float = 0.85
    allow_overflow: bool = True
    allow_temporary_absorption: bool = True
    allow_partial: bool = False
    allow_queen_fallback: bool = True
    observe_only_capability: Optional[str] = None
    whole_system_coordination: bool = False
    safety_relevant: bool = False
    consequential: bool = False
    partial_result_useful: bool = False

    def __post_init__(self) -> None:
        if not self.work_id.strip() or not self.work_class.strip():
            raise ValueError("work_id and work_class are required")
        if not self.required_capabilities:
            raise ValueError("at least one required capability is required")
        if any(not item.strip() for item in self.required_capabilities + self.preferred_capabilities):
            raise ValueError("work capabilities cannot be blank")
        if self.observe_only_capability is not None and not self.observe_only_capability.strip():
            raise ValueError("observe_only_capability cannot be blank")
        if not 0.0 <= self.min_health <= 1.0 or not 0.0 <= self.max_load <= 1.0:
            raise ValueError("work thresholds must be between 0 and 1")


@dataclass(frozen=True)
class WorkCandidate:
    node_id: str
    organ: str
    mode: CandidateMode
    score: float
    matched_capabilities: Tuple[str, ...]
    missing_capabilities: Tuple[str, ...]
    reasons: Tuple[str, ...]
    authority: str = "none"

    def __post_init__(self) -> None:
        if not 0.0 <= self.score <= 1.0:
            raise ValueError("candidate score must be between 0 and 1")
        if self.authority != "none":
            raise ValueError("work candidates cannot carry authority")


@dataclass(frozen=True)
class WorkPlacementProposal:
    work_id: str
    disposition: PlacementDisposition
    candidates: Tuple[WorkCandidate, ...]
    degradation: DegradationMode
    reasons: Tuple[str, ...]
    escalate_results_to_queen: bool = True
    requires_runtime_placement: bool = True
    requires_court_authorization: bool = False
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if not self.work_id.strip() or not self.reasons:
            raise ValueError("placement proposals require work_id and reasons")
        if self.disposition is PlacementDisposition.UNAVAILABLE and self.candidates:
            raise ValueError("unavailable proposals cannot contain candidates")
        if self.disposition is not PlacementDisposition.UNAVAILABLE and not self.candidates:
            raise ValueError("candidate proposals require at least one candidate")
        if not self.requires_runtime_placement:
            raise ValueError("Native Brain cannot bypass Runtime placement")
        if self.canonical:
            raise ValueError("placement proposals are not canonical memory")
        if self.authority != "none":
            raise ValueError("placement proposals cannot carry authority")


class DistributedBodyPlanner:
    """Rank suitable organs without assigning work or transferring authority."""

    def propose(
        self,
        requirement: WorkRequirement,
        nodes: Tuple[NodeAdvertisement, ...],
    ) -> WorkPlacementProposal:
        full = []
        partial = []
        observe_only = []
        exclusions = []
        required = set(requirement.required_capabilities)

        for node in nodes:
            exclusion = self._exclusion_reason(requirement, node)
            if exclusion is not None:
                exclusions.append(f"{node.node_id}:{exclusion}")
                continue

            normal = set(node.capabilities)
            fallback_only = set(node.fallback_capabilities) - normal
            temporary_only = set(node.temporary_absorption_capabilities) - normal
            effective = normal
            mode = CandidateMode.PRIMARY

            if required.issubset(normal):
                if node.tier is NodeTier.QUEEN and not requirement.whole_system_coordination:
                    mode = CandidateMode.QUEEN_FALLBACK
            elif (
                requirement.allow_overflow
                and node.overflow_capable
                and required.issubset(normal | fallback_only)
            ):
                mode = CandidateMode.OVERFLOW
                effective = normal | fallback_only
            elif (
                requirement.allow_temporary_absorption
                and required.issubset(normal | temporary_only)
            ):
                mode = CandidateMode.TEMPORARY_ABSORPTION
                effective = normal | temporary_only
            else:
                all_declared = normal | fallback_only | temporary_only
                matched = tuple(sorted(required & all_declared))
                missing = tuple(sorted(required - all_declared))
                if requirement.allow_partial and requirement.partial_result_useful and matched:
                    partial.append(
                        self._candidate(node, requirement, CandidateMode.PARTIAL, matched, missing)
                    )
                if (
                    requirement.observe_only_capability is not None
                    and requirement.observe_only_capability in all_declared
                ):
                    observe_only.append(
                        self._candidate(
                            node,
                            requirement,
                            CandidateMode.OBSERVE_ONLY,
                            (requirement.observe_only_capability,),
                            tuple(sorted(required)),
                        )
                    )
                continue

            full.append(
                self._candidate(
                    node,
                    requirement,
                    mode,
                    tuple(sorted(required & effective)),
                    (),
                )
            )

        if full:
            ranked = tuple(sorted(full, key=self._sort_key))
            degradation = (
                DegradationMode.FULL_REPLACEMENT
                if ranked[0].mode in {
                    CandidateMode.OVERFLOW,
                    CandidateMode.TEMPORARY_ABSORPTION,
                    CandidateMode.QUEEN_FALLBACK,
                }
                else DegradationMode.NONE
            )
            return WorkPlacementProposal(
                work_id=requirement.work_id,
                disposition=PlacementDisposition.PLACE_CANDIDATE,
                candidates=ranked,
                degradation=degradation,
                reasons=("compatible verified organs found",) + tuple(exclusions),
                requires_court_authorization=requirement.consequential,
            )

        if partial:
            return WorkPlacementProposal(
                work_id=requirement.work_id,
                disposition=PlacementDisposition.DEGRADED_CANDIDATE,
                candidates=tuple(sorted(partial, key=self._sort_key)),
                degradation=DegradationMode.PARTIAL_REPLACEMENT,
                reasons=("only partial replacement is currently possible",) + tuple(exclusions),
                requires_court_authorization=requirement.consequential,
            )

        if observe_only:
            return WorkPlacementProposal(
                work_id=requirement.work_id,
                disposition=PlacementDisposition.DEGRADED_CANDIDATE,
                candidates=tuple(sorted(observe_only, key=self._sort_key)),
                degradation=DegradationMode.OBSERVE_ONLY,
                reasons=("only observe-only fallback is currently possible",) + tuple(exclusions),
                requires_court_authorization=requirement.consequential,
            )

        return WorkPlacementProposal(
            work_id=requirement.work_id,
            disposition=PlacementDisposition.UNAVAILABLE,
            candidates=(),
            degradation=DegradationMode.CAPABILITY_UNAVAILABLE,
            reasons=("no verified healthy organ can satisfy the work",) + tuple(exclusions),
            requires_court_authorization=requirement.consequential,
        )

    @staticmethod
    def _exclusion_reason(
        requirement: WorkRequirement, node: NodeAdvertisement
    ) -> Optional[str]:
        if not node.body_verified:
            return "body-not-verified"
        if not node.continuity_verified:
            return "continuity-not-verified"
        if node.availability in {
            NodeAvailability.SATURATED,
            NodeAvailability.DRAINING,
            NodeAvailability.OFFLINE,
            NodeAvailability.QUARANTINED,
        }:
            return f"availability:{node.availability.value}"
        if node.health < requirement.min_health:
            return "health-below-work-minimum"
        if node.current_load > requirement.max_load or node.available_capacity <= 0.0:
            return "load-or-task-limit-exceeded"
        if requirement.work_class in node.refused_work_classes:
            return "work-class-refused"
        if node.accepted_work_classes and requirement.work_class not in node.accepted_work_classes:
            return "work-class-not-accepted"
        if node.tier is NodeTier.QUEEN and not requirement.allow_queen_fallback:
            return "queen-fallback-disabled"
        if requirement.whole_system_coordination and node.tier is not NodeTier.QUEEN:
            return "whole-system-coordination-requires-queen"
        return None

    @staticmethod
    def _candidate(
        node: NodeAdvertisement,
        requirement: WorkRequirement,
        mode: CandidateMode,
        matched: Tuple[str, ...],
        missing: Tuple[str, ...],
    ) -> WorkCandidate:
        preferred = set(requirement.preferred_capabilities)
        preferred_ratio = (
            len(preferred & set(node.capabilities)) / len(preferred)
            if preferred
            else 1.0
        )
        score = (
            node.health * 0.35
            + node.available_capacity * 0.35
            + preferred_ratio * 0.15
            + (0.10 if node.availability is NodeAvailability.AVAILABLE else 0.05)
        )
        reasons = [f"health:{node.health:.2f}", f"capacity:{node.available_capacity:.2f}"]

        if mode is CandidateMode.TEMPORARY_ABSORPTION:
            score -= 0.05
            reasons.append("temporary-duty-absorption")
        elif mode is CandidateMode.OVERFLOW:
            score -= 0.02
            reasons.append("overflow-fallback-capability")
        elif mode is CandidateMode.QUEEN_FALLBACK:
            score -= 0.12
            reasons.append("queen-reserved-as-fallback")
        elif mode is CandidateMode.PARTIAL:
            score -= 0.20
            reasons.append("partial-capability-only")
        elif mode is CandidateMode.OBSERVE_ONLY:
            score -= 0.25
            reasons.append("observe-only-fallback")

        if requirement.whole_system_coordination and node.tier is NodeTier.QUEEN:
            score += 0.15
            reasons.append("queen-whole-system-role")
        elif node.tier is NodeTier.SPECIALIST_LINUX:
            score += 0.05
            reasons.append("narrow-specialist-fit")

        if node.availability is NodeAvailability.DEGRADED:
            score -= 0.10
            reasons.append("node-degraded")

        return WorkCandidate(
            node_id=node.node_id,
            organ=node.organ,
            mode=mode,
            score=round(max(0.0, min(score, 1.0)), 4),
            matched_capabilities=matched,
            missing_capabilities=missing,
            reasons=tuple(reasons),
        )

    @staticmethod
    def _sort_key(candidate: WorkCandidate) -> Tuple[float, str]:
        return (-candidate.score, candidate.node_id)
