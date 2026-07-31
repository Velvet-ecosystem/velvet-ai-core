"""Whole-body saturation measurements and deterministic threshold review."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple


@dataclass(frozen=True)
class SaturationThresholds:
    max_cpu_percent: float = 95.0
    max_memory_percent: float = 90.0
    max_receipt_delay_ms: float = 250.0
    max_disk_latency_ms: float = 100.0
    max_temperature_c: float = 85.0
    max_dropped_events: int = 0
    max_stale_packets: int = 0


@dataclass(frozen=True)
class SaturationSample:
    timestamp: float
    cpu_percent: float
    memory_percent: float
    receipt_delay_ms: float
    disk_latency_ms: float
    temperature_c: float
    dropped_events: int = 0
    stale_packets: int = 0
    throttled: bool = False
    degraded_services: Tuple[str, ...] = ()
    recovery_observed: bool = False

    def __post_init__(self) -> None:
        for name in ("cpu_percent", "memory_percent"):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 100.0:
                raise ValueError("%s must be between 0 and 100" % name)
        for name in (
            "timestamp",
            "receipt_delay_ms",
            "disk_latency_ms",
            "temperature_c",
        ):
            if float(getattr(self, name)) < 0:
                raise ValueError("%s must be non-negative" % name)
        if self.dropped_events < 0 or self.stale_packets < 0:
            raise ValueError("event and stale packet counts must be non-negative")


@dataclass(frozen=True)
class SaturationReport:
    sample_count: int
    passed: bool
    breaches: Tuple[str, ...]
    recovery_observed: bool


def evaluate_saturation(
    samples: Iterable[SaturationSample],
    thresholds: SaturationThresholds = SaturationThresholds(),
) -> SaturationReport:
    sample_list = tuple(samples)
    if not sample_list:
        raise ValueError("at least one saturation sample is required")

    breaches = []
    recovery_observed = any(sample.recovery_observed for sample in sample_list)

    for index, sample in enumerate(sample_list):
        prefix = "sample %d" % index
        if sample.cpu_percent > thresholds.max_cpu_percent:
            breaches.append("%s cpu" % prefix)
        if sample.memory_percent > thresholds.max_memory_percent:
            breaches.append("%s memory" % prefix)
        if sample.receipt_delay_ms > thresholds.max_receipt_delay_ms:
            breaches.append("%s receipt delay" % prefix)
        if sample.disk_latency_ms > thresholds.max_disk_latency_ms:
            breaches.append("%s disk latency" % prefix)
        if sample.temperature_c > thresholds.max_temperature_c:
            breaches.append("%s temperature" % prefix)
        if sample.dropped_events > thresholds.max_dropped_events:
            breaches.append("%s dropped events" % prefix)
        if sample.stale_packets > thresholds.max_stale_packets:
            breaches.append("%s stale packets" % prefix)
        if sample.throttled:
            breaches.append("%s throttling" % prefix)
        if sample.degraded_services:
            breaches.append("%s degraded services" % prefix)

    return SaturationReport(
        sample_count=len(sample_list),
        passed=not breaches,
        breaches=tuple(breaches),
        recovery_observed=recovery_observed,
    )
