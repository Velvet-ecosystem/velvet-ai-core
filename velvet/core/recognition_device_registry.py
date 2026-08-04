"""Explicit device binding registry for recognition adapters.

Runtime supplies approved bindings. Devices cannot scan themselves into the
system, select an adapter, choose a candidate identity, or claim authority.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Mapping, Optional, Tuple, Type

from .recognition_adapters import (
    CameraRecognitionAdapter,
    NfcRecognitionAdapter,
    RecognitionAdapter,
    SeatPresenceRecognitionAdapter,
    VoiceRecognitionAdapter,
)
from .recognition_evidence import RecognitionModality


class DeviceBindingState(str, Enum):
    DECLARED = "DECLARED"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    RETIRED = "RETIRED"


class DeviceTransport(str, Enum):
    USB = "USB"
    UART = "UART"
    I2C = "I2C"
    SPI = "SPI"
    GPIO = "GPIO"
    NETWORK = "NETWORK"
    VIRTUAL = "VIRTUAL"
    UNKNOWN = "UNKNOWN"


_ADAPTER_TYPES: Mapping[str, Type[RecognitionAdapter]] = {
    "camera": CameraRecognitionAdapter,
    "voice": VoiceRecognitionAdapter,
    "nfc": NfcRecognitionAdapter,
    "seat_presence": SeatPresenceRecognitionAdapter,
}


def _require_text(name: str, value: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("%s must be a non-empty string" % name)


@dataclass(frozen=True)
class RecognitionDeviceBinding:
    binding_id: str
    device_id: str
    module_id: str
    node_id: str
    adapter_kind: str
    transport: DeviceTransport
    endpoint: str
    owning_handmaiden: str
    approved_by: str
    approval_receipt_id: str
    state: DeviceBindingState = DeviceBindingState.DECLARED
    configuration: Mapping[str, object] = field(default_factory=dict)
    simulated: bool = False
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        for name in (
            "binding_id",
            "device_id",
            "module_id",
            "node_id",
            "adapter_kind",
            "endpoint",
            "owning_handmaiden",
            "approved_by",
            "approval_receipt_id",
        ):
            _require_text(name, getattr(self, name))
        if self.adapter_kind not in _ADAPTER_TYPES:
            raise ValueError("unsupported adapter_kind: %s" % self.adapter_kind)
        if not isinstance(self.transport, DeviceTransport):
            object.__setattr__(self, "transport", DeviceTransport(self.transport))
        if not isinstance(self.state, DeviceBindingState):
            object.__setattr__(self, "state", DeviceBindingState(self.state))
        if not isinstance(self.configuration, Mapping):
            raise ValueError("configuration must be a mapping")
        if self.authority_granted or self.execution_performed:
            raise ValueError("device bindings cannot claim authority or execution")

    @property
    def modality(self) -> RecognitionModality:
        return _ADAPTER_TYPES[self.adapter_kind].modality

    def create_adapter(self) -> RecognitionAdapter:
        if self.state != DeviceBindingState.ACTIVE:
            raise RuntimeError("only active bindings can create adapters")
        adapter_type = _ADAPTER_TYPES[self.adapter_kind]
        return adapter_type(self.module_id, self.node_id)

    def with_state(
        self,
        state: DeviceBindingState,
        approval_receipt_id: Optional[str] = None,
    ) -> "RecognitionDeviceBinding":
        if self.state == DeviceBindingState.RETIRED and state != DeviceBindingState.RETIRED:
            raise ValueError("retired bindings cannot be reactivated")
        receipt_id = approval_receipt_id or self.approval_receipt_id
        _require_text("approval_receipt_id", receipt_id)
        return RecognitionDeviceBinding(
            binding_id=self.binding_id,
            device_id=self.device_id,
            module_id=self.module_id,
            node_id=self.node_id,
            adapter_kind=self.adapter_kind,
            transport=self.transport,
            endpoint=self.endpoint,
            owning_handmaiden=self.owning_handmaiden,
            approved_by=self.approved_by,
            approval_receipt_id=receipt_id,
            state=state,
            configuration=dict(self.configuration),
            simulated=self.simulated,
        )


@dataclass(frozen=True)
class RegistryChange:
    binding_id: str
    previous_state: Optional[DeviceBindingState]
    new_state: DeviceBindingState
    approval_receipt_id: str
    reason: str
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if self.authority_granted or self.execution_performed:
            raise ValueError("registry changes cannot claim authority or execution")


class RecognitionDeviceRegistry:
    """In-memory registry populated only through explicit approved bindings."""

    def __init__(self) -> None:
        self._bindings: Dict[str, RecognitionDeviceBinding] = {}
        self._device_index: Dict[str, str] = {}
        self._module_index: Dict[str, str] = {}
        self._history: list[RegistryChange] = []

    def register(self, binding: RecognitionDeviceBinding) -> RegistryChange:
        if binding.binding_id in self._bindings:
            raise ValueError("binding_id already registered")
        if binding.device_id in self._device_index:
            raise ValueError("device_id already bound")
        if binding.module_id in self._module_index:
            raise ValueError("module_id already bound")
        self._bindings[binding.binding_id] = binding
        self._device_index[binding.device_id] = binding.binding_id
        self._module_index[binding.module_id] = binding.binding_id
        change = RegistryChange(
            binding_id=binding.binding_id,
            previous_state=None,
            new_state=binding.state,
            approval_receipt_id=binding.approval_receipt_id,
            reason="explicit approved device binding registered",
        )
        self._history.append(change)
        return change

    def activate(self, binding_id: str, approval_receipt_id: str) -> RegistryChange:
        return self._transition(
            binding_id,
            DeviceBindingState.ACTIVE,
            approval_receipt_id,
            "binding activated by explicit Runtime approval",
        )

    def suspend(self, binding_id: str, approval_receipt_id: str) -> RegistryChange:
        return self._transition(
            binding_id,
            DeviceBindingState.SUSPENDED,
            approval_receipt_id,
            "binding suspended by explicit Runtime approval",
        )

    def retire(self, binding_id: str, approval_receipt_id: str) -> RegistryChange:
        return self._transition(
            binding_id,
            DeviceBindingState.RETIRED,
            approval_receipt_id,
            "binding retired by explicit Runtime approval",
        )

    def get(self, binding_id: str) -> RecognitionDeviceBinding:
        try:
            return self._bindings[binding_id]
        except KeyError as exc:
            raise KeyError("unknown binding_id: %s" % binding_id) from exc

    def by_device(self, device_id: str) -> RecognitionDeviceBinding:
        binding_id = self._device_index.get(device_id)
        if binding_id is None:
            raise KeyError("device is not explicitly bound")
        return self.get(binding_id)

    def active_adapters(self) -> Tuple[RecognitionAdapter, ...]:
        return tuple(
            binding.create_adapter()
            for binding in self._bindings.values()
            if binding.state == DeviceBindingState.ACTIVE
        )

    def active_bindings(
        self,
        modality: Optional[RecognitionModality] = None,
    ) -> Tuple[RecognitionDeviceBinding, ...]:
        bindings = tuple(
            item
            for item in self._bindings.values()
            if item.state == DeviceBindingState.ACTIVE
        )
        if modality is None:
            return bindings
        return tuple(item for item in bindings if item.modality == modality)

    def history(self) -> Tuple[RegistryChange, ...]:
        return tuple(self._history)

    def discover(self, *_args, **_kwargs):
        raise RuntimeError("device discovery and storage scanning are forbidden")

    def self_register(self, *_args, **_kwargs):
        raise RuntimeError("devices cannot self-register")

    def _transition(
        self,
        binding_id: str,
        state: DeviceBindingState,
        approval_receipt_id: str,
        reason: str,
    ) -> RegistryChange:
        _require_text("approval_receipt_id", approval_receipt_id)
        current = self.get(binding_id)
        updated = current.with_state(state, approval_receipt_id)
        self._bindings[binding_id] = updated
        change = RegistryChange(
            binding_id=binding_id,
            previous_state=current.state,
            new_state=state,
            approval_receipt_id=approval_receipt_id,
            reason=reason,
        )
        self._history.append(change)
        return change
