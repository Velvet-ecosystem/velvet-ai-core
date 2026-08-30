"""Runtime handoff for approved recognition device bindings.

Runtime supplies concrete adapter instances for explicit active bindings. The
handoff collects bounded observations, records health outcomes, and forwards only
valid evidence. It does not discover devices, choose identities, grant authority,
or execute physical action.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable, Dict, Mapping, Optional, Tuple
from uuid import uuid4

from .recognition_adapters import AdapterContext, RecognitionAdapter
from .recognition_device_registry import (
    DeviceBindingState,
    RecognitionDeviceBinding,
    RecognitionDeviceRegistry,
)
from .recognition_evidence import RecognitionObservation


class HandoffHealth(str, Enum):
    OBSERVATION_ACCEPTED = "OBSERVATION_ACCEPTED"
    ADAPTER_UNAVAILABLE = "ADAPTER_UNAVAILABLE"
    ADAPTER_FAILED = "ADAPTER_FAILED"
    BINDING_INACTIVE = "BINDING_INACTIVE"
    BINDING_MISMATCH = "BINDING_MISMATCH"


@dataclass(frozen=True)
class RecognitionHealthEvent:
    event_id: str
    binding_id: str
    device_id: str
    module_id: str
    node_id: str
    health: HandoffHealth
    observed_at: float
    receipt_ids: Tuple[str, ...]
    reason: str
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if self.observed_at < 0:
            raise ValueError("observed_at must be non-negative")
        if self.authority_granted or self.execution_performed:
            raise ValueError("recognition health events cannot claim authority")


@dataclass(frozen=True)
class RecognitionCollectionResult:
    observations: Tuple[RecognitionObservation, ...]
    health_events: Tuple[RecognitionHealthEvent, ...]
    authority_granted: bool = False
    execution_performed: bool = False

    def __post_init__(self) -> None:
        if self.authority_granted or self.execution_performed:
            raise ValueError("recognition collection cannot claim authority")


AdapterProvider = Callable[[RecognitionDeviceBinding], RecognitionAdapter]


class RecognitionRuntimeHandoff:
    """Collect observations from explicitly bound Runtime-provided adapters."""

    def __init__(
        self,
        registry: RecognitionDeviceRegistry,
        adapter_provider: AdapterProvider,
    ) -> None:
        self._registry = registry
        self._adapter_provider = adapter_provider
        self._adapters: Dict[str, RecognitionAdapter] = {}

    def bind_active(self) -> Tuple[RecognitionHealthEvent, ...]:
        events = []
        for binding in self._registry.active_bindings():
            try:
                adapter = self._adapter_provider(binding)
                self._validate_adapter(binding, adapter)
                self._adapters[binding.binding_id] = adapter
            except Exception as exc:
                self._adapters.pop(binding.binding_id, None)
                events.append(
                    self._health(
                        binding,
                        HandoffHealth.ADAPTER_UNAVAILABLE,
                        0.0,
                        (binding.approval_receipt_id,),
                        "adapter provider could not bind device: %s" % exc,
                    )
                )
        return tuple(events)

    def collect(
        self,
        contexts: Mapping[str, AdapterContext],
    ) -> RecognitionCollectionResult:
        observations = []
        health_events = []
        for binding_id, context in contexts.items():
            binding = self._registry.get(binding_id)
            if binding.state != DeviceBindingState.ACTIVE:
                health_events.append(
                    self._health(
                        binding,
                        HandoffHealth.BINDING_INACTIVE,
                        context.observed_at,
                        (binding.approval_receipt_id,),
                        "binding is not active",
                    )
                )
                continue

            adapter = self._adapters.get(binding_id)
            if adapter is None:
                health_events.append(
                    self._health(
                        binding,
                        HandoffHealth.ADAPTER_UNAVAILABLE,
                        context.observed_at,
                        (binding.approval_receipt_id,),
                        "no Runtime-provided adapter is bound",
                    )
                )
                continue

            try:
                self._validate_adapter(binding, adapter)
                observation = adapter.observe(context)
            except Exception as exc:
                health_events.append(
                    self._health(
                        binding,
                        HandoffHealth.ADAPTER_FAILED,
                        context.observed_at,
                        (binding.approval_receipt_id,),
                        "adapter observation failed: %s" % exc,
                    )
                )
                continue

            observations.append(observation)
            health_events.append(
                self._health(
                    binding,
                    HandoffHealth.OBSERVATION_ACCEPTED,
                    context.observed_at,
                    (binding.approval_receipt_id, observation.receipt_id),
                    "bounded recognition observation accepted",
                )
            )

        return RecognitionCollectionResult(
            observations=tuple(observations),
            health_events=tuple(health_events),
        )

    def unbind(self, binding_id: str) -> None:
        self._adapters.pop(binding_id, None)

    def discover(self, *_args, **_kwargs):
        raise RuntimeError("Runtime handoff cannot discover devices")

    @staticmethod
    def _validate_adapter(
        binding: RecognitionDeviceBinding,
        adapter: RecognitionAdapter,
    ) -> None:
        if not isinstance(adapter, binding.adapter_type):
            raise ValueError("adapter type does not match approved binding")
        if adapter.module_id != binding.module_id or adapter.node_id != binding.node_id:
            raise ValueError("adapter identity does not match approved binding")
        if adapter.modality != binding.modality:
            raise ValueError("adapter modality does not match approved binding")

    @staticmethod
    def _health(
        binding: RecognitionDeviceBinding,
        health: HandoffHealth,
        observed_at: float,
        receipt_ids: Tuple[str, ...],
        reason: str,
    ) -> RecognitionHealthEvent:
        return RecognitionHealthEvent(
            event_id=str(uuid4()),
            binding_id=binding.binding_id,
            device_id=binding.device_id,
            module_id=binding.module_id,
            node_id=binding.node_id,
            health=health,
            observed_at=float(observed_at),
            receipt_ids=tuple(dict.fromkeys(receipt_ids)),
            reason=reason,
        )
