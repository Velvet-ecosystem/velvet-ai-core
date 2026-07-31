"""Module Lab promotion evidence and deterministic gate checks."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Tuple


class PromotionGate(str, Enum):
    LIFECYCLE = "lifecycle"
    HEALTH_EVENT = "health_event"
    RECEIPT_EMISSION = "receipt_emission"
    MALFORMED_INPUT = "malformed_input"
    AUTHORITY_BYPASS = "authority_bypass"
    DEPENDENCY_FAILURE = "dependency_failure"
    STALE_TIMESTAMP = "stale_timestamp"
    SIMULATED_ADAPTER = "simulated_adapter"
    DEGRADED_MODE = "degraded_mode"
    SHUTDOWN = "shutdown"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class ModulePromotionEvidence:
    """Append-only promotion evidence. Passing gates does not self-promote code."""

    module_id: str
    gate_results: Mapping[PromotionGate, bool]
    evidence_receipts: Mapping[PromotionGate, str]
    fuzz_targets: Tuple[str, ...] = ()
    notes: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _require_text("module_id", self.module_id)
        missing_results = set(PromotionGate).difference(self.gate_results)
        if missing_results:
            raise ValueError(
                "missing promotion gate results: %s"
                % ", ".join(sorted(gate.value for gate in missing_results))
            )
        missing_receipts = set(PromotionGate).difference(self.evidence_receipts)
        if missing_receipts:
            raise ValueError(
                "missing promotion evidence receipts: %s"
                % ", ".join(sorted(gate.value for gate in missing_receipts))
            )
        for gate in PromotionGate:
            _require_text(
                "evidence receipt for %s" % gate.value,
                self.evidence_receipts[gate],
            )

    @property
    def failed_gates(self) -> Tuple[PromotionGate, ...]:
        return tuple(
            gate for gate in PromotionGate if not bool(self.gate_results[gate])
        )

    @property
    def ready_for_human_promotion_review(self) -> bool:
        return not self.failed_gates

    def assert_ready_for_human_promotion_review(self) -> None:
        if self.failed_gates:
            raise ValueError(
                "module promotion gates failed: %s"
                % ", ".join(gate.value for gate in self.failed_gates)
            )
