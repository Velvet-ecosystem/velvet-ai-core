# SPDX-License-Identifier: GPL-3.0-only
"""Belief and execution-placement scaffolds for Velvet AI Core.

These helpers keep uncertainty, model capability, and execution location
separate from physical authority. They do not call models, dispatch hardware,
or bypass Runtime/Court.
"""

from __future__ import annotations

from dataclasses import dataclass


VALID_EXECUTION_POLICIES = {
    "local-required",
    "local-preferred",
    "handmaiden-eligible",
    "movable",
    "cloud-optional",
    "cloud-forbidden",
}

VALID_AUTHORITY_LEVELS = {"none", "classify", "advise", "propose"}
VALID_PROCESSOR_CLASSES = {"cpu", "gpu", "npu", "dsp", "fpga", "memory_side", "unknown"}


@dataclass(frozen=True)
class CandidateInterpretation:
    label: str
    confidence: float
    supporting_evidence: tuple[str, ...] = ()
    contradicting_evidence: tuple[str, ...] = ()

    def validate(self) -> None:
        _validate_non_empty("label", self.label)
        _validate_confidence("confidence", self.confidence)
        _validate_string_tuple("supporting_evidence", self.supporting_evidence)
        _validate_string_tuple("contradicting_evidence", self.contradicting_evidence)


@dataclass(frozen=True)
class BeliefState:
    belief_id: str
    source_observation_ids: tuple[str, ...]
    candidate_interpretations: tuple[CandidateInterpretation, ...]
    commit_threshold: float
    committed: bool = False
    commit_reason: str | None = None
    requires_corroboration: bool = True
    expiry_time: float | None = None

    def validate(self) -> None:
        _validate_non_empty("belief_id", self.belief_id)
        _validate_string_tuple("source_observation_ids", self.source_observation_ids)
        if not self.candidate_interpretations:
            raise ValueError("candidate_interpretations cannot be empty")
        for candidate in self.candidate_interpretations:
            candidate.validate()
        _validate_confidence("commit_threshold", self.commit_threshold)
        if self.commit_reason is not None:
            _validate_non_empty("commit_reason", self.commit_reason)
        if self.expiry_time is not None:
            _validate_non_negative_number("expiry_time", self.expiry_time)


def strongest_candidate(belief: BeliefState) -> CandidateInterpretation:
    belief.validate()
    return max(belief.candidate_interpretations, key=lambda candidate: candidate.confidence)


def can_commit_belief(belief: BeliefState) -> bool:
    """Return whether the belief is strong enough to commit.

    Corroboration is approximated here as at least two source observations when
    required. Real implementations can plug in richer evidence logic later.
    """

    belief.validate()
    best = strongest_candidate(belief)
    if best.confidence < belief.commit_threshold:
        return False
    if belief.requires_corroboration and len(belief.source_observation_ids) < 2:
        return False
    return True


@dataclass(frozen=True)
class ModelCapability:
    capability_name: str
    preferred_provider: str
    offline_available: bool
    cloud_permission_required: bool
    max_authority_level: str
    fallback_provider: str | None = None
    data_retention_rule: str = "local-first"
    receipt_required: bool = True
    refusal_behavior: str = "fail-closed"

    def validate(self) -> None:
        _validate_non_empty("capability_name", self.capability_name)
        _validate_non_empty("preferred_provider", self.preferred_provider)
        if self.fallback_provider is not None:
            _validate_non_empty("fallback_provider", self.fallback_provider)
        if self.max_authority_level not in VALID_AUTHORITY_LEVELS:
            raise ValueError("max_authority_level cannot grant physical authority")
        _validate_non_empty("data_retention_rule", self.data_retention_rule)
        _validate_non_empty("refusal_behavior", self.refusal_behavior)


@dataclass(frozen=True)
class ExecutionPlacement:
    capability_name: str
    execution_location_policy: str
    allowed_nodes: tuple[str, ...]
    forbidden_nodes: tuple[str, ...] = ()
    data_may_leave_origin_node: bool = False
    max_latency_ms: int | None = None
    fallback_location: str | None = None
    power_cost_class: str = "unknown"
    thermal_cost_class: str = "unknown"
    authority_changes_if_moved: bool = False

    def validate(self) -> None:
        _validate_non_empty("capability_name", self.capability_name)
        if self.execution_location_policy not in VALID_EXECUTION_POLICIES:
            raise ValueError("unsupported execution_location_policy")
        _validate_string_tuple("allowed_nodes", self.allowed_nodes)
        _validate_string_tuple("forbidden_nodes", self.forbidden_nodes)
        if self.max_latency_ms is not None:
            _validate_non_negative_int("max_latency_ms", self.max_latency_ms)
        if self.fallback_location is not None:
            _validate_non_empty("fallback_location", self.fallback_location)
        _validate_non_empty("power_cost_class", self.power_cost_class)
        _validate_non_empty("thermal_cost_class", self.thermal_cost_class)
        if self.authority_changes_if_moved:
            raise ValueError("execution placement cannot change authority")


def choose_execution_node(placement: ExecutionPlacement, healthy_nodes: tuple[str, ...]) -> str | None:
    """Choose the first allowed healthy node, respecting forbidden nodes.

    Returns None when no safe placement exists. This is selection scaffolding,
    not task dispatch.
    """

    placement.validate()
    _validate_string_tuple("healthy_nodes", healthy_nodes)
    forbidden = set(placement.forbidden_nodes)
    healthy = set(healthy_nodes)
    for node in placement.allowed_nodes:
        if node in healthy and node not in forbidden:
            return node
    return None


@dataclass(frozen=True)
class InferenceCostSketch:
    capability_requested: str
    model_name_or_local_id: str
    execution_location: str
    processor_class: str
    runtime_ms: int
    memory_peak_mb: int
    estimated_energy_j: float | None = None
    fallback_invoked: bool = False
    larger_model_reason: str | None = None

    def validate(self) -> None:
        _validate_non_empty("capability_requested", self.capability_requested)
        _validate_non_empty("model_name_or_local_id", self.model_name_or_local_id)
        _validate_non_empty("execution_location", self.execution_location)
        if self.processor_class not in VALID_PROCESSOR_CLASSES:
            raise ValueError("unsupported processor_class")
        _validate_non_negative_int("runtime_ms", self.runtime_ms)
        _validate_non_negative_int("memory_peak_mb", self.memory_peak_mb)
        if self.estimated_energy_j is not None:
            _validate_non_negative_number("estimated_energy_j", self.estimated_energy_j)
        if self.larger_model_reason is not None:
            _validate_non_empty("larger_model_reason", self.larger_model_reason)


def useful_work_per_watt_gb(*, throughput: float, watts: float, memory_mb: int) -> float:
    _validate_non_negative_number("throughput", throughput)
    _validate_positive_number("watts", watts)
    _validate_positive_int("memory_mb", memory_mb)
    memory_gb = memory_mb / 1024.0
    return float(throughput) / float(watts) / memory_gb


def _validate_non_empty(name: str, value: object) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must be a non-empty string")


def _validate_string_tuple(name: str, value: object) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{name} must be a tuple")
    for item in value:
        _validate_non_empty(f"{name}[]", item)


def _validate_confidence(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{name} must be between 0 and 1")


def _validate_non_negative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} cannot be negative")


def _validate_positive_int(name: str, value: object) -> None:
    _validate_non_negative_int(name, value)
    if int(value) == 0:
        raise ValueError(f"{name} must be positive")


def _validate_non_negative_number(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be numeric")
    if float(value) < 0:
        raise ValueError(f"{name} cannot be negative")


def _validate_positive_number(name: str, value: object) -> None:
    _validate_non_negative_number(name, value)
    if float(value) == 0:
        raise ValueError(f"{name} must be positive")
