# SPDX-License-Identifier: GPL-3.0-only
"""Body-relative resource capacity contracts for distributed Velvet cognition.

This layer does not replace ``DistributedBodyPlanner``. It provides a bounded,
authority-free resource gate so the existing planner can reason over the body
that is actually available now rather than a hard-coded board model.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from enum import Enum
from typing import Dict, Iterable, Mapping, Sequence, Tuple

from .distributed_body import (
    DistributedBodyPlanner,
    NodeAdvertisement,
    WorkPlacementProposal,
    WorkRequirement,
)


class ResourceKind(str, Enum):
    MEMORY = "memory"
    STORAGE = "storage"
    COMPUTE = "compute"
    ACCELERATOR = "accelerator"


class ResourceScope(str, Enum):
    LOCAL = "local"
    ATTACHED = "attached"
    BODY_SHARED = "body_shared"


@dataclass(frozen=True)
class ResourceAdvertisement:
    """One measurable resource exposed by one verified body organ."""

    resource_id: str
    kind: ResourceKind
    scope: ResourceScope
    capacity: float
    available: float
    unit: str
    capabilities: Tuple[str, ...] = ()
    online: bool = True
    authority: str = "none"

    def __post_init__(self) -> None:
        if not isinstance(self.resource_id, str) or not self.resource_id.strip():
            raise ValueError("resource_id is required")
        if not isinstance(self.kind, ResourceKind):
            raise TypeError("kind must be ResourceKind")
        if not isinstance(self.scope, ResourceScope):
            raise TypeError("scope must be ResourceScope")
        for name, value in (("capacity", self.capacity), ("available", self.available)):
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise ValueError("%s must be numeric" % name)
            if not math.isfinite(float(value)):
                raise ValueError("%s must be finite" % name)
        if float(self.capacity) <= 0.0:
            raise ValueError("capacity must be positive")
        if not 0.0 <= float(self.available) <= float(self.capacity):
            raise ValueError("available must fit inside capacity")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("unit is required")
        if any(not isinstance(item, str) or not item.strip() for item in self.capabilities):
            raise ValueError("resource capabilities cannot be blank")
        if not isinstance(self.online, bool):
            raise ValueError("online must be boolean")
        if self.authority != "none":
            raise ValueError("resource advertisements cannot carry authority")


@dataclass(frozen=True)
class NodeResourceAdvertisement:
    """Current resource view for one verified organ."""

    node_id: str
    body_id: str
    observed_at: float
    resources: Tuple[ResourceAdvertisement, ...]
    body_verified: bool = True
    continuity_verified: bool = True
    authority: str = "none"

    def __post_init__(self) -> None:
        if not isinstance(self.node_id, str) or not self.node_id.strip():
            raise ValueError("node_id is required")
        if not isinstance(self.body_id, str) or not self.body_id.strip():
            raise ValueError("body_id is required")
        if isinstance(self.observed_at, bool) or not isinstance(self.observed_at, (int, float)):
            raise ValueError("observed_at must be numeric")
        if float(self.observed_at) < 0.0:
            raise ValueError("observed_at cannot be negative")
        if not isinstance(self.resources, tuple):
            raise ValueError("resources must be a tuple")
        if any(not isinstance(item, ResourceAdvertisement) for item in self.resources):
            raise TypeError("resources must contain ResourceAdvertisement values")
        ids = [item.resource_id for item in self.resources]
        if len(ids) != len(set(ids)):
            raise ValueError("resource ids must be unique per node advertisement")
        if not self.body_verified or not self.continuity_verified:
            # The value may still be carried for diagnostics, but consumers must reject it.
            pass
        if self.authority != "none":
            raise ValueError("node resource advertisements cannot carry authority")


@dataclass(frozen=True)
class ResourceRequirement:
    """Minimum host resource needed by one bounded work item."""

    kind: ResourceKind
    minimum_available: float
    unit: str
    accepted_scopes: Tuple[ResourceScope, ...] = (
        ResourceScope.LOCAL,
        ResourceScope.ATTACHED,
        ResourceScope.BODY_SHARED,
    )
    required_capabilities: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ResourceKind):
            raise TypeError("kind must be ResourceKind")
        if isinstance(self.minimum_available, bool) or not isinstance(
            self.minimum_available, (int, float)
        ):
            raise ValueError("minimum_available must be numeric")
        if not math.isfinite(float(self.minimum_available)) or float(self.minimum_available) < 0.0:
            raise ValueError("minimum_available must be finite and non-negative")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("unit is required")
        if not self.accepted_scopes:
            raise ValueError("at least one accepted resource scope is required")
        if any(not isinstance(scope, ResourceScope) for scope in self.accepted_scopes):
            raise TypeError("accepted_scopes must contain ResourceScope values")
        if any(not isinstance(item, str) or not item.strip() for item in self.required_capabilities):
            raise ValueError("required resource capabilities cannot be blank")


@dataclass(frozen=True)
class BodyCapacityTotal:
    kind: ResourceKind
    unit: str
    capacity: float
    available: float
    resource_count: int


@dataclass(frozen=True)
class BodyCapacitySnapshot:
    """Aggregate read-only capacity across verified current body organs."""

    node_ids: Tuple[str, ...]
    totals: Tuple[BodyCapacityTotal, ...]
    resource_count: int
    canonical: bool = False
    authority: str = "none"

    def __post_init__(self) -> None:
        if self.resource_count < 0:
            raise ValueError("resource_count cannot be negative")
        if self.canonical:
            raise ValueError("body capacity snapshots are observational, not canonical memory")
        if self.authority != "none":
            raise ValueError("body capacity snapshots cannot carry authority")


def build_body_capacity_snapshot(
    advertisements: Sequence[NodeResourceAdvertisement],
) -> BodyCapacitySnapshot:
    """Aggregate the newest verified advertisement for each node."""

    newest = _latest_verified_advertisements(advertisements)
    buckets: Dict[Tuple[ResourceKind, str], list[ResourceAdvertisement]] = {}
    for advertisement in newest.values():
        for resource in advertisement.resources:
            if not resource.online:
                continue
            key = (resource.kind, resource.unit.strip())
            buckets.setdefault(key, []).append(resource)

    totals = []
    count = 0
    for (kind, unit), resources in sorted(
        buckets.items(), key=lambda item: (item[0][0].value, item[0][1])
    ):
        count += len(resources)
        totals.append(
            BodyCapacityTotal(
                kind=kind,
                unit=unit,
                capacity=sum(float(item.capacity) for item in resources),
                available=sum(float(item.available) for item in resources),
                resource_count=len(resources),
            )
        )
    return BodyCapacitySnapshot(
        node_ids=tuple(sorted(newest)),
        totals=tuple(totals),
        resource_count=count,
    )


def node_meets_resource_requirements(
    node_id: str,
    advertisements: Sequence[NodeResourceAdvertisement],
    requirements: Sequence[ResourceRequirement],
) -> bool:
    if not requirements:
        return True
    newest = _latest_verified_advertisements(advertisements)
    advertisement = newest.get(node_id)
    if advertisement is None:
        return False
    return all(_requirement_met(advertisement.resources, requirement) for requirement in requirements)


def filter_nodes_for_resources(
    nodes: Sequence[NodeAdvertisement],
    advertisements: Sequence[NodeResourceAdvertisement],
    requirements: Sequence[ResourceRequirement],
) -> Tuple[NodeAdvertisement, ...]:
    if not requirements:
        return tuple(nodes)
    return tuple(
        node
        for node in nodes
        if node_meets_resource_requirements(node.node_id, advertisements, requirements)
    )


class ResourceAwareDistributedBodyPlanner:
    """Delegate to the existing planner after applying body-resource bounds."""

    def __init__(self, planner: DistributedBodyPlanner | None = None) -> None:
        self._planner = planner or DistributedBodyPlanner()

    def propose(
        self,
        requirement: WorkRequirement,
        nodes: Tuple[NodeAdvertisement, ...],
        *,
        resource_advertisements: Sequence[NodeResourceAdvertisement] = (),
        resource_requirements: Sequence[ResourceRequirement] = (),
    ) -> WorkPlacementProposal:
        if not resource_requirements:
            return self._planner.propose(requirement, nodes)
        eligible = filter_nodes_for_resources(nodes, resource_advertisements, resource_requirements)
        excluded = tuple(sorted(set(node.node_id for node in nodes) - set(node.node_id for node in eligible)))
        proposal = self._planner.propose(requirement, eligible)
        if not excluded:
            return proposal
        return replace(
            proposal,
            reasons=proposal.reasons
            + tuple("%s:resource-requirement-unmet" % node_id for node_id in excluded),
        )


def _latest_verified_advertisements(
    advertisements: Sequence[NodeResourceAdvertisement],
) -> Mapping[str, NodeResourceAdvertisement]:
    newest: Dict[str, NodeResourceAdvertisement] = {}
    for advertisement in advertisements:
        if not isinstance(advertisement, NodeResourceAdvertisement):
            raise TypeError("resource advertisements must be NodeResourceAdvertisement values")
        if not advertisement.body_verified or not advertisement.continuity_verified:
            continue
        current = newest.get(advertisement.node_id)
        if current is None or advertisement.observed_at > current.observed_at:
            newest[advertisement.node_id] = advertisement
    return newest


def _requirement_met(
    resources: Iterable[ResourceAdvertisement],
    requirement: ResourceRequirement,
) -> bool:
    needed_caps = set(requirement.required_capabilities)
    accepted_scopes = set(requirement.accepted_scopes)
    for resource in resources:
        if not resource.online:
            continue
        if resource.kind is not requirement.kind:
            continue
        if resource.unit.strip() != requirement.unit.strip():
            continue
        if resource.scope not in accepted_scopes:
            continue
        if not needed_caps.issubset(set(resource.capabilities)):
            continue
        if float(resource.available) >= float(requirement.minimum_available):
            return True
    return False
