"""Contract-driven hardware and simulated-body adapters for Native Brain.

Both adapter kinds emit the same Velvet Event Protocol record shape. The body
practice loop sends those records through the same processor method and receipt
callback, so simulation cannot become a parallel authority or telemetry lane.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from random import Random
from time import sleep
from typing import (
    Any,
    Callable,
    Mapping,
    MutableMapping,
    Optional,
    Protocol,
    Tuple,
)
from uuid import uuid4

from .models import DecisionReceipt, EvaluationProfile


PayloadReader = Callable[[], Optional[Mapping[str, Any]]]
Clock = Callable[[], datetime]
Sleeper = Callable[[float], None]
ReceiptPath = Callable[["BodyReceiptEnvelope"], None]


class FaultInjectionError(ValueError):
    """Raised when a requested fake-organ fault cannot be applied safely."""


@dataclass(frozen=True)
class OrganContract:
    """Stable event identity shared by one physical organ and its fake twin."""

    organ_name: str
    event_type: str
    source: str
    family: str = "body.observation"
    schema_version: str = "1.0"

    def __post_init__(self) -> None:
        for field_name in (
            "organ_name",
            "event_type",
            "source",
            "family",
            "schema_version",
        ):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError("%s must be a non-empty string" % field_name)

    def event_record(
        self,
        payload: Mapping[str, Any],
        observed_at: datetime,
        origin: str,
    ) -> Mapping[str, Any]:
        """Build one transport record without granting authority."""

        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        else:
            observed_at = observed_at.astimezone(timezone.utc)

        return {
            "event_id": str(uuid4()),
            "event_type": self.event_type,
            "source": self.source,
            "family": self.family,
            "schema_version": self.schema_version,
            "timestamp": observed_at.isoformat(),
            "origin": origin,
            "organ_name": self.organ_name,
            "payload": dict(payload),
        }


@dataclass(frozen=True)
class FaultProfile:
    """Deterministic fault controls for a fake organ.

    Dotted field paths may target nested payload mappings. Noise is additive and
    bounded by the configured amplitude. Impossible values are applied last so
    they remain deliberately impossible.
    """

    delay_seconds: float = 0.0
    dropout_rate: float = 0.0
    stale_by_seconds: float = 0.0
    noise: Mapping[str, float] = field(default_factory=dict)
    impossible_values: Mapping[str, Any] = field(default_factory=dict)
    seed: Optional[int] = None

    def __post_init__(self) -> None:
        if self.delay_seconds < 0:
            raise ValueError("delay_seconds cannot be negative")
        if not 0.0 <= self.dropout_rate <= 1.0:
            raise ValueError("dropout_rate must be between 0.0 and 1.0")
        if self.stale_by_seconds < 0:
            raise ValueError("stale_by_seconds cannot be negative")
        for path, amplitude in self.noise.items():
            if not isinstance(path, str) or not path.strip():
                raise ValueError("noise paths must be non-empty strings")
            if isinstance(amplitude, bool) or not isinstance(amplitude, (int, float)):
                raise ValueError("noise amplitudes must be numeric")
            if amplitude < 0:
                raise ValueError("noise amplitudes cannot be negative")


@dataclass(frozen=True)
class OrganEmission:
    """One adapter attempt, including deliberate or natural dropout."""

    contract: OrganContract
    origin: str
    record: Optional[Mapping[str, Any]]
    reasons: Tuple[str, ...] = ()

    @property
    def dropped(self) -> bool:
        return self.record is None


class OrganAdapter(Protocol):
    """Interchangeable hardware or simulated organ source."""

    contract: OrganContract

    def emit(self) -> OrganEmission:
        ...


class ProtocolEventProcessor(Protocol):
    """The existing Native Brain Event Protocol entry point."""

    def process_protocol_event(
        self,
        record: Mapping[str, Any],
        state: Optional[Mapping[str, Any]] = None,
        evaluation_profile: Optional[EvaluationProfile] = None,
    ) -> DecisionReceipt:
        ...


class HardwareOrganAdapter:
    """Read a physical organ and emit its declared Event Protocol contract."""

    def __init__(
        self,
        contract: OrganContract,
        reader: PayloadReader,
        clock: Optional[Clock] = None,
    ) -> None:
        self.contract = contract
        self._reader = reader
        self._clock = clock or _utc_now

    def emit(self) -> OrganEmission:
        payload = self._reader()
        if payload is None:
            return OrganEmission(
                contract=self.contract,
                origin="hardware",
                record=None,
                reasons=("reader returned no sample",),
            )
        if not isinstance(payload, Mapping):
            raise TypeError("organ reader must return a mapping or None")
        return OrganEmission(
            contract=self.contract,
            origin="hardware",
            record=self.contract.event_record(payload, self._clock(), "hardware"),
        )


class FakeOrganAdapter:
    """Practice twin for a physical organ contract with bounded fault injection."""

    def __init__(
        self,
        contract: OrganContract,
        reader: PayloadReader,
        faults: Optional[FaultProfile] = None,
        clock: Optional[Clock] = None,
        sleeper: Optional[Sleeper] = None,
        rng: Optional[Random] = None,
    ) -> None:
        self.contract = contract
        self._reader = reader
        self._faults = faults or FaultProfile()
        self._clock = clock or _utc_now
        self._sleeper = sleeper or sleep
        self._rng = rng or Random(self._faults.seed)

    @classmethod
    def mirror(
        cls,
        hardware: HardwareOrganAdapter,
        reader: PayloadReader,
        faults: Optional[FaultProfile] = None,
        clock: Optional[Clock] = None,
        sleeper: Optional[Sleeper] = None,
        rng: Optional[Random] = None,
    ) -> "FakeOrganAdapter":
        """Create the fake twin of an existing physical adapter contract."""

        return cls(
            contract=hardware.contract,
            reader=reader,
            faults=faults,
            clock=clock,
            sleeper=sleeper,
            rng=rng,
        )

    def emit(self) -> OrganEmission:
        if self._faults.delay_seconds:
            self._sleeper(self._faults.delay_seconds)

        payload = self._reader()
        if payload is None:
            return OrganEmission(
                contract=self.contract,
                origin="simulation",
                record=None,
                reasons=("fake reader returned no sample",),
            )
        if not isinstance(payload, Mapping):
            raise TypeError("fake organ reader must return a mapping or None")

        if self._rng.random() < self._faults.dropout_rate:
            return OrganEmission(
                contract=self.contract,
                origin="simulation",
                record=None,
                reasons=("fault injection: dropout",),
            )

        mutated = _deep_copy_mapping(payload)
        reasons = []

        for path, amplitude in self._faults.noise.items():
            value = _get_path(mutated, path)
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise FaultInjectionError(
                    "noise target %r must contain a numeric value" % path
                )
            delta = self._rng.uniform(-float(amplitude), float(amplitude))
            _set_path(mutated, path, value + delta)
            reasons.append("fault injection: noise:%s" % path)

        for path, value in self._faults.impossible_values.items():
            _set_path(mutated, path, value)
            reasons.append("fault injection: impossible:%s" % path)

        observed_at = self._clock() - timedelta(
            seconds=self._faults.stale_by_seconds
        )
        if self._faults.stale_by_seconds:
            reasons.append("fault injection: stale timestamp")
        if self._faults.delay_seconds:
            reasons.append("fault injection: delay")

        return OrganEmission(
            contract=self.contract,
            origin="simulation",
            record=self.contract.event_record(mutated, observed_at, "simulation"),
            reasons=tuple(reasons),
        )


@dataclass(frozen=True)
class BodyReceiptEnvelope:
    """Receipt plus the exact body event that produced it."""

    event_record: Mapping[str, Any]
    receipt: DecisionReceipt


@dataclass(frozen=True)
class BodyCycle:
    """Result of one hardware or simulated body pass."""

    emission: OrganEmission
    receipt: Optional[DecisionReceipt] = None
    receipt_recorded: bool = False

    @property
    def dropped(self) -> bool:
        return self.emission.dropped


class BodyPracticeSkeleton:
    """Run hardware and fake organs through one event and receipt path."""

    def __init__(
        self,
        processor: ProtocolEventProcessor,
        receipt_path: Optional[ReceiptPath] = None,
    ) -> None:
        self._processor = processor
        self._receipt_path = receipt_path

    def run(
        self,
        adapter: OrganAdapter,
        state: Optional[Mapping[str, Any]] = None,
        evaluation_profile: Optional[EvaluationProfile] = None,
    ) -> BodyCycle:
        emission = adapter.emit()
        if emission.record is None:
            return BodyCycle(emission=emission)

        receipt = self._processor.process_protocol_event(
            emission.record,
            state,
            evaluation_profile,
        )
        recorded = False
        if self._receipt_path is not None:
            self._receipt_path(
                BodyReceiptEnvelope(
                    event_record=emission.record,
                    receipt=receipt,
                )
            )
            recorded = True

        return BodyCycle(
            emission=emission,
            receipt=receipt,
            receipt_recorded=recorded,
        )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _deep_copy_mapping(value: Mapping[str, Any]) -> MutableMapping[str, Any]:
    copied = {}  # type: MutableMapping[str, Any]
    for key, item in value.items():
        if isinstance(item, Mapping):
            copied[str(key)] = _deep_copy_mapping(item)
        else:
            copied[str(key)] = item
    return copied


def _split_path(path: str) -> Tuple[str, ...]:
    parts = tuple(part for part in path.split(".") if part)
    if not parts:
        raise FaultInjectionError("fault path must be a non-empty dotted path")
    return parts


def _get_path(payload: Mapping[str, Any], path: str) -> Any:
    current = payload  # type: Any
    for part in _split_path(path):
        if not isinstance(current, Mapping) or part not in current:
            raise FaultInjectionError("fault path %r does not exist" % path)
        current = current[part]
    return current


def _set_path(payload: MutableMapping[str, Any], path: str, value: Any) -> None:
    parts = _split_path(path)
    current = payload
    for part in parts[:-1]:
        child = current.get(part)
        if child is None:
            child = {}
            current[part] = child
        if not isinstance(child, MutableMapping):
            raise FaultInjectionError(
                "fault path %r crosses a non-mapping value" % path
            )
        current = child
    current[parts[-1]] = value
