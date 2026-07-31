"""Vehicle interface contract for adapter-bound physical surfaces."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class VehicleInterfaceAuthority(str, Enum):
    OBSERVATION_ONLY = "OBSERVATION_ONLY"
    READ_ONLY = "READ_ONLY"
    GOVERNED_CONTROL = "GOVERNED_CONTROL"
    BENCH_ONLY = "BENCH_ONLY"


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class VehicleInterfaceContract:
    """Vehicle-facing adapter boundary. Authority remains external to the adapter."""

    interface_id: str
    purpose: str
    vehicle_targets: Tuple[str, ...]
    authority_mode: VehicleInterfaceAuthority
    owning_handmaiden: str
    physical_interface: str
    data_format: str
    update_frequency_hz: float
    command_format: Optional[str]
    receipt_type: str
    safe_failure_behavior: str
    adapter_boundary: str
    simulation_adapter_available: bool
    allowed_surfaces: Tuple[str, ...]

    def __post_init__(self) -> None:
        for name in (
            "interface_id",
            "purpose",
            "owning_handmaiden",
            "physical_interface",
            "data_format",
            "receipt_type",
            "safe_failure_behavior",
            "adapter_boundary",
        ):
            _require_text(name, getattr(self, name))

        if not self.vehicle_targets:
            raise ValueError("vehicle_targets must not be empty")
        if not self.allowed_surfaces:
            raise ValueError("allowed_surfaces must not be empty")
        if float(self.update_frequency_hz) < 0:
            raise ValueError("update_frequency_hz must be non-negative")

        if not isinstance(self.authority_mode, VehicleInterfaceAuthority):
            object.__setattr__(
                self,
                "authority_mode",
                VehicleInterfaceAuthority(self.authority_mode),
            )

        if self.authority_mode == VehicleInterfaceAuthority.GOVERNED_CONTROL:
            if self.command_format is None:
                raise ValueError(
                    "governed control interfaces must declare command_format"
                )
            _require_text("command_format", self.command_format)

    def allowed_on(self, surface: str) -> bool:
        _require_text("surface", surface)
        return surface in self.allowed_surfaces

    def to_dict(self) -> Dict[str, Any]:
        return {
            "interface_id": self.interface_id,
            "purpose": self.purpose,
            "vehicle_targets": list(self.vehicle_targets),
            "authority_mode": self.authority_mode.value,
            "owning_handmaiden": self.owning_handmaiden,
            "physical_interface": self.physical_interface,
            "data_format": self.data_format,
            "update_frequency_hz": float(self.update_frequency_hz),
            "command_format": self.command_format,
            "receipt_type": self.receipt_type,
            "safe_failure_behavior": self.safe_failure_behavior,
            "adapter_boundary": self.adapter_boundary,
            "simulation_adapter_available": bool(
                self.simulation_adapter_available
            ),
            "allowed_surfaces": list(self.allowed_surfaces),
        }
