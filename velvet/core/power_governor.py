"""Recommendation-only power-aware workload scheduling for Velvet."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Tuple


class WorkloadClass(str, Enum):
    PROTECTED = "PROTECTED"
    DEGRADABLE = "DEGRADABLE"
    YIELD_FIRST = "YIELD_FIRST"


class PowerDisposition(str, Enum):
    RUN = "RUN"
    DEGRADE = "DEGRADE"
    PAUSE = "PAUSE"
    REFUSE = "REFUSE"


@dataclass(frozen=True)
class PowerPolicy:
    low_voltage_threshold: float = 11.8
    critical_voltage_threshold: float = 11.0
    hot_temperature_c: float = 80.0
    critical_temperature_c: float = 90.0

    def __post_init__(self) -> None:
        if self.critical_voltage_threshold >= self.low_voltage_threshold:
            raise ValueError(
                "critical voltage threshold must be below low voltage threshold"
            )
        if self.critical_temperature_c <= self.hot_temperature_c:
            raise ValueError(
                "critical temperature must be above hot temperature"
            )


@dataclass(frozen=True)
class PowerState:
    ignition_on: bool
    battery_voltage: float
    charging: bool
    temperature_c: float
    node_healthy: bool
    owner_present: bool
    runtime_mode: str

    def __post_init__(self) -> None:
        if not isinstance(self.runtime_mode, str) or not self.runtime_mode.strip():
            raise ValueError("runtime_mode must be a non-empty string")


@dataclass(frozen=True)
class WorkloadRequest:
    workload_id: str
    workload_class: WorkloadClass
    allow_while_driving: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.workload_id, str) or not self.workload_id.strip():
            raise ValueError("workload_id must be a non-empty string")
        if not isinstance(self.workload_class, WorkloadClass):
            object.__setattr__(
                self,
                "workload_class",
                WorkloadClass(self.workload_class),
            )


@dataclass(frozen=True)
class PowerDecision:
    workload_id: str
    disposition: PowerDisposition
    reasons: Tuple[str, ...]
    authority_granted: bool = False
    execution_performed: bool = False


class PowerGovernor:
    """Produce deterministic workload advice without stopping processes itself."""

    def __init__(self, policy: PowerPolicy = PowerPolicy()) -> None:
        self._policy = policy

    def decide(
        self,
        request: WorkloadRequest,
        state: PowerState,
    ) -> PowerDecision:
        reasons = []

        if not state.node_healthy:
            return PowerDecision(
                workload_id=request.workload_id,
                disposition=PowerDisposition.REFUSE,
                reasons=("node health unavailable",),
            )

        driving = state.runtime_mode.lower() in {
            "drive",
            "driving",
            "moving",
            "route",
            "pullover",
        }
        if driving and not request.allow_while_driving:
            return PowerDecision(
                workload_id=request.workload_id,
                disposition=PowerDisposition.PAUSE,
                reasons=("workload not permitted while driving",),
            )

        critical_power = (
            state.battery_voltage <= self._policy.critical_voltage_threshold
        )
        low_power = state.battery_voltage <= self._policy.low_voltage_threshold
        critical_heat = (
            state.temperature_c >= self._policy.critical_temperature_c
        )
        hot = state.temperature_c >= self._policy.hot_temperature_c
        parked_unpowered = (
            not state.ignition_on
            and not state.charging
            and state.runtime_mode.lower() in {"parked", "sleep", "standby"}
        )

        if critical_power:
            reasons.append("critical battery voltage")
        elif low_power:
            reasons.append("low battery voltage")

        if critical_heat:
            reasons.append("critical temperature")
        elif hot:
            reasons.append("high temperature")

        if parked_unpowered:
            reasons.append("parked without charging")

        constrained = bool(reasons)

        if request.workload_class == WorkloadClass.PROTECTED:
            return PowerDecision(
                workload_id=request.workload_id,
                disposition=PowerDisposition.RUN,
                reasons=tuple(reasons) or ("protected workload",),
            )

        if request.workload_class == WorkloadClass.YIELD_FIRST:
            return PowerDecision(
                workload_id=request.workload_id,
                disposition=(
                    PowerDisposition.PAUSE
                    if constrained
                    else PowerDisposition.RUN
                ),
                reasons=tuple(reasons) or ("power posture acceptable",),
            )

        return PowerDecision(
            workload_id=request.workload_id,
            disposition=(
                PowerDisposition.DEGRADE
                if constrained
                else PowerDisposition.RUN
            ),
            reasons=tuple(reasons) or ("power posture acceptable",),
        )
